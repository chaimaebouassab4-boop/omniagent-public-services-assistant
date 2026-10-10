"""Smart Document Analyzer — local OCR/rules with optional Gemini assistance.
=======================================================

Pipeline:
    1. MIME detection (PDF / Image)
    2. Local text extraction:
        a) PDF with selectable text  → pypdf (fast path)
        b) Scanned PDF / image       → Tesseract ara+fra+eng when installed
        c) Conservative preprocessing → orientation, resize, contrast, denoise
    3. Deterministic classification and schema-based field extraction
    4. Gemini is used only when local evidence is insufficient
    5. Optional conversational analysis prompt →
        • Detected document type (CIN, birth certificate, electricity bill…)
        • Key entities extracted (name, date, address, CIN number…)
        • Validity check (< 3 months old?  Stamp present?  Arabic/French?)
        • Conformity verdict for common Moroccan administrative procedures
    4. Returns a structured analysis object used by the chat endpoint.

Supported languages for the response: darija · arabic · fr
"""

from __future__ import annotations

from datetime import datetime
import io
import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional, Any

from app.core.config import settings
from app.core.dev_logging import development_trace
from app.services.gemini_client import GeminiRequestError, binary_part, generate_text


# ─── Moroccan Document Analysis Prompts (3 languages) ────────────────────────

_DOCUMENT_PROMPTS: dict[str, dict[str, str]] = {
    "darija": {
        "system": (
            "أنت OmniAgent، المساعد الذكي الرسمي للإجراءات والخدمات الإدارية المغربية. "
            "الأسلوب ديالك واضح، ودود، مهني، ومبسط بالدارجة المغربية المفهومة. "
            "جاوب المواطن بطريقة حوارية ومباشرة بلا تعقيد أو إطالة غير مفيدة."
        ),
        "analyze": (
            "حلل هاد الوثيقة الإدارية بطريقة محادثة واضحة ومختصرة للمواطن بالدارجة المغربية.\n\n"
            "{user_query_instruction}"
            "الهيكل المطلوب (مختصر ومباشر) :\n"
            "1. **خلاصة مباشرة** : قول للمواطن شنو هي هاد الوثيقة، باسم شكون، وواش مقبولة وصالحة للإجراءات الإدارية في المغرب.\n"
            "2. **أهم النقط المستخرجة (في 3 إلى 4 نقط فقط)** :\n"
            "   * **صاحب(ة) الوثيقة** : [الاسم الكامل]\n"
            "   * **رقم التعريف / المرجع** : [رقم CIN أو CNE أو المرجع إن وجد]\n"
            "   * **تاريخ والجهة المصدرة** : [التاريخ والمؤسسة]\n"
            "   * **الصلاحية والخاتم** : [واش صالحة للإدارة المغربية، واش خاصها ترجمة أو تصحيح إمضاء]\n"
            "3. **توجيه عملي** : جملة أو جوج باش توجه المواطن للخطوة الموالية.\n\n"
            "محتوى الوثيقة:\n{text}"
        ),
        "no_text": (
            "⚠️ **ما قدرتش نقرا الوثيقة بوضوح**\n\n"
            "وصلاتني الوثيقة ديالك، ولكن الصورة أو الملف ما كانش واضح كفاية باش نستخرج النص.\n\n"
            "جرب تعاود ترفع صورة أوضح، أو كتب ليا شنو فيها ونعاونك بكل سرور."
        ),
        "error": (
            "❌ **وقع مشكل في التحليل**\n\n"
            "تعذر تحليل الوثيقة حالياً. تقدر تسولني مباشرة على أي إجراء باغي تديرو."
        ),
    },
    "fr": {
        "system": (
            "Vous êtes OmniAgent, l'assistant officiel pour les démarches administratives marocaines. "
            "Votre ton est naturel, professionnel, bienveillant et synthétique. "
            "Vous vous adressez directement au citoyen dans un style fluide et conversationnel, sans lourdeur administrative ni jargon inutile."
        ),
        "analyze": (
            "Analysez ce document de manière concise et conversationnelle en vous adressant directement à l'utilisateur.\n\n"
            "{user_query_instruction}"
            "Structure attendue (courte, claire et aérée) :\n"
            "1. **Synthèse directe** : Indiquez en une phrase de quel document il s'agit, au nom de qui, et s'il est conforme / utilisable pour les démarches au Maroc.\n"
            "2. **L'essentiel en quelques points clés** :\n"
            "   * **Titulaire** : [Nom & Prénom]\n"
            "   * **Identifiant** : [N° CIN, CNE ou référence]\n"
            "   * **Émetteur & Date** : [Organisme émetteur et date]\n"
            "   * **Validité & Statut** : [Conformité, règle des 3 mois, besoin éventuel de traduction assermentée ou légalisation]\n"
            "3. **Conseil pratique** : 1 ou 2 phrases concrètes pour orienter le citoyen sur la suite de sa démarche.\n\n"
            "Contenu du document :\n{text}"
        ),
        "no_text": (
            "⚠️ **Impossible de lire le document clairement**\n\n"
            "Le document a bien été reçu, mais la lisibilité est insuffisante pour extraire les informations avec certitude.\n\n"
            "Essayez d'envoyer une photo plus nette ou un scan plus clair, ou décrivez-moi votre démarche pour que je puisse vous guider."
        ),
        "error": (
            "❌ **Erreur d'analyse**\n\n"
            "L'analyse du document n'a pas pu aboutir. Vous pouvez me poser directement votre question."
        ),
    },
    "arabic": {
        "system": (
            "أنت OmniAgent، المساعد الذكي الرسمي للمساطر والخدمات الإدارية المغربية. "
            "أسلوبك مهني، واضح، ودود ومختصر، يخاطب المواطن بلغة عربية سلسة ومباشرة دون تعقيد أو إطالة."
        ),
        "analyze": (
            "يرجى تقديم ملخص موجز ومباشر لهذه الوثيقة بأسلوب حواري وواضح:\n\n"
            "{user_query_instruction}"
            "الهيكل المطلوب (موجز ومفيد):\n"
            "1. **موجز مباشر**: حدد نوع الوثيقة، صاحبها، ومدى مطابقتها للمساطر الإدارية بالمغرب.\n"
            "2. **البيانات الأساسية**:\n"
            "   * **المعني(ة) بالأمر**: [الاسم والنسب]\n"
            "   * **رقم الهوية / المرجع**: [رقم CIN أو المرجع]\n"
            "   * **تاريخ والجهة المصدرة**: [تاريخ ومصدر الوثيقة]\n"
            "   * **الصلاحية**: [سارية المفعول، تحتاج مصادقة، مترجمة، إلخ]\n"
            "3. **توجيه عملي**: إرشاد مباشر وموجز للمواطن حول الخطوة التالية.\n\n"
            "محتوى الوثيقة:\n{text}"
        ),
        "no_text": (
            "⚠️ **تعذر قراءة الوثيقة بوضوح**\n\n"
            "تم استلام الوثيقة، لكن جودة الصورة أو الملف غير كافية لاستخراج النص بدقة.\n\n"
            "يرجى إعادة إرسال صورة أوضح، أو إخباري بمحتوى الوثيقة وسأساعدك فوراً."
        ),
        "error": (
            "❌ **حدث خطأ في التحليل**\n\n"
            "تعذر تحليل الوثيقة حالياً. يمكنك طرح سؤالك مباشرة وسأجيبك."
        ),
    },
}


def _resolve_lang(lang: str) -> str:
    """Normalise language string to one of: darija | fr | arabic."""
    lang = lang.strip().lower()
    if lang in ("ar", "arabic", "عربية"):
        return "arabic"
    if lang in ("fr", "french", "français"):
        return "fr"
    return "darija"


# ─── Result dataclass ─────────────────────────────────────────────────────────

DOCUMENT_TYPE_LABELS: dict[str, dict[str, str]] = {
    "cin": {
        "fr": "Carte Nationale d'Identité (CIN)",
        "ar": "بطاقة التعريف الوطنية",
        "darija": "لاكارط ناسيونال (CIN)",
    },
    "residence_certificate": {
        "fr": "Certificat de Résidence",
        "ar": "شهادة السكنى",
        "darija": "شهادة السكنى",
    },
    "birth_certificate": {
        "fr": "Extrait d'Acte de Naissance",
        "ar": "عقد الازدياد",
        "darija": "عقد الازدياد",
    },
    "electricity_bill": {
        "fr": "Facture d'eau / électricité",
        "ar": "فاتورة الماء أو الكهرباء",
        "darija": "ورقة الما والضو",
    },
    "passport": {
        "fr": "Passeport Marocain",
        "ar": "جواز السفر المغربي",
        "darija": "باسبور مغربي",
    },
    "driving_license": {
        "fr": "Permis de Conduire",
        "ar": "رخصة السياقة",
        "darija": "بيرمي السياقة",
    },
    "other": {
        "fr": "Document Administratif",
        "ar": "وثيقة إدارية",
        "darija": "وثيقة إدارية",
    },
    "irrelevant": {
        "fr": "Document non reconnu / non administratif",
        "ar": "وثيقة غير إدارية أو غير ملائمة",
        "darija": "الصورة ماشي وثيقة إدارية رسمية",
    },
    "unknown": {
        "fr": "Type de document inconnu",
        "ar": "نوع الوثيقة غير معروف",
        "darija": "نوع الوثيقة ما معروفش",
    },
}


@dataclass
class DocumentAnalysis:
    doc_type: str = "unknown"
    extracted_text: str = ""
    page_count: int = 0
    ocr_used: bool = False
    llm_analysis: str = ""
    is_image: bool = False
    error: Optional[str] = None
    ocr_backend: str = "none"
    ocr_confidence: float = 0.0
    gemini_vision_status: str = "unavailable"
    gemini_structured_status: str = "unavailable"


@dataclass
class LocalOcrResult:
    """PII-free operational result from a local OCR attempt."""

    text: str = ""
    confidence: float = 0.0
    backend: str = "tesseract"
    status: str = "unavailable"
    languages: tuple[str, ...] = ()


@dataclass
class ExtractedDocumentMetadata:
    """Structured entity & anomaly metadata extracted for form auto-fill."""
    document_type: str = "unknown"
    document_type_label: dict[str, str] = None
    cin_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    birth_date: Optional[str] = None
    address: Optional[str] = None
    expiry_date: Optional[str] = None
    issuing_authority: Optional[str] = None
    confidence_score: float = 0.0
    ocr_confidence: float = 0.0
    classification_confidence: float = 0.0
    extraction_confidence: float = 0.0
    classification_source: str = "local_rules"
    ocr_backend: str = "none"
    field_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)
    document_indicators: list[str] = field(default_factory=list)
    is_valid: bool = True
    is_expired: bool = False
    is_blurry: bool = False
    is_relevant: bool = True
    warnings: list[str] = None
    raw_extracted_text: str = ""
    ocr_used: bool = False
    page_count: int = 1
    anomalies: list[str] = None

    def to_dict(self) -> dict[str, Any]:
        labels = self.document_type_label or DOCUMENT_TYPE_LABELS.get(
            self.document_type,
            DOCUMENT_TYPE_LABELS["other"]
        )
        return {
            "document_type": self.document_type,
            "document_type_label": labels,
            "cin_number": self.cin_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "birth_date": self.birth_date,
            "address": self.address,
            "expiry_date": self.expiry_date,
            "issuing_authority": self.issuing_authority,
            "confidence_score": round(self.confidence_score, 2),
            "ocr_confidence": round(self.ocr_confidence, 2),
            "classification_confidence": round(self.classification_confidence, 2),
            "extraction_confidence": round(self.extraction_confidence, 2),
            "classification_source": self.classification_source,
            "ocr_backend": self.ocr_backend,
            "field_metadata": self.field_metadata,
            "document_indicators": self.document_indicators,
            "is_valid": self.is_valid,
            "is_expired": self.is_expired,
            "is_blurry": self.is_blurry,
            "is_relevant": self.is_relevant,
            "warnings": self.warnings or [],
            "anomalies": self.anomalies or [],
            "raw_extracted_text": self.raw_extracted_text,
            "ocr_used": self.ocr_used,
            "page_count": self.page_count,
        }


# ─── Step 1: pypdf fast path ──────────────────────────────────────────────────

def _extract_pdf_text_pypdf(data: bytes) -> tuple[str, int]:
    """Extract selectable text from a PDF using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return "", 0
    try:
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((p.extract_text() or "") for p in reader.pages).strip()
        return text, len(reader.pages)
    except Exception:
        return "", 0


def _pdf_first_page_as_png(data: bytes) -> Optional[bytes]:
    """Render the first PDF page to PNG bytes via PyMuPDF (optional dep)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=data, filetype="pdf")
        page = doc[0]
        mat = fitz.Matrix(2.0, 2.0)  # 2× zoom ≈ 144 DPI
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return pix.tobytes("png")
    except Exception:
        return None


# ─── Step 2: deterministic local OCR, with Gemini as optional fallback ───────

def _normalized_image_variants(image_bytes: bytes) -> list[tuple[str, Any]]:
    """Return deterministic OCR candidates without degrading a good original.

    The first candidate preserves the decoded image (apart from EXIF rotation
    and RGB conversion).  A second grayscale candidate is resized only when
    necessary and receives conservative contrast normalization and denoising.
    """
    try:
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat
    except ImportError:
        return []

    try:
        with Image.open(io.BytesIO(image_bytes)) as opened:
            original = ImageOps.exif_transpose(opened).convert("RGB")
    except Exception:
        return []

    variants: list[tuple[str, Any]] = [("original", original)]
    gray = ImageOps.grayscale(original)
    width, height = gray.size
    shortest = min(width, height)
    if shortest and shortest < 900:
        scale = min(2.5, 900 / shortest)
        gray = gray.resize(
            (max(1, round(width * scale)), max(1, round(height * scale))),
            Image.Resampling.LANCZOS,
        )

    # Only apply stronger enhancement to low-contrast scans.  The untouched
    # original always remains a candidate and wins when its OCR is better.
    contrast = float(ImageStat.Stat(gray).stddev[0])
    if contrast < 48:
        gray = ImageOps.autocontrast(gray, cutoff=1)
        gray = ImageEnhance.Contrast(gray).enhance(1.25)
        gray = gray.filter(ImageFilter.MedianFilter(size=3))
    else:
        gray = ImageOps.autocontrast(gray, cutoff=0.5)
    variants.append(("normalized", gray))
    return variants


def _tesseract_languages(pytesseract_module: Any) -> tuple[str, ...]:
    """Select installed Arabic/French/English Tesseract packs in priority order."""
    try:
        installed = set(pytesseract_module.get_languages(config=""))
    except Exception:
        return ()
    return tuple(code for code in ("ara", "fra", "eng") if code in installed)


def _correct_tesseract_orientation(image: Any, pytesseract_module: Any) -> Any:
    """Apply Tesseract OSD's deterministic rotation when it is confident enough."""
    try:
        osd = pytesseract_module.image_to_osd(image, config="--psm 0")
        rotate_match = re.search(r"Rotate:\s*(0|90|180|270)", osd)
        confidence_match = re.search(r"Orientation confidence:\s*([0-9.]+)", osd)
        rotate = int(rotate_match.group(1)) if rotate_match else 0
        confidence = float(confidence_match.group(1)) if confidence_match else 0.0
        if rotate and confidence >= 2.0:
            return image.rotate(-rotate, expand=True)
    except Exception:
        pass
    return image


def _text_from_tesseract_data(data: dict[str, list[Any]]) -> tuple[str, float]:
    """Rebuild OCR lines and calculate a token-weighted confidence."""
    line_tokens: dict[tuple[int, int, int], list[str]] = {}
    weighted_confidence = 0.0
    total_weight = 0
    texts = data.get("text", [])
    confidences = data.get("conf", [])
    for index, raw_token in enumerate(texts):
        token = str(raw_token or "").strip()
        if not token:
            continue
        try:
            confidence = float(confidences[index])
        except (IndexError, TypeError, ValueError):
            confidence = -1.0
        if confidence >= 0:
            weight = max(1, len(token))
            weighted_confidence += confidence * weight
            total_weight += weight
        key = (
            int(data.get("block_num", [0] * len(texts))[index]),
            int(data.get("par_num", [0] * len(texts))[index]),
            int(data.get("line_num", [0] * len(texts))[index]),
        )
        line_tokens.setdefault(key, []).append(token)
    text = "\n".join(" ".join(tokens) for tokens in line_tokens.values()).strip()
    confidence = (weighted_confidence / total_weight / 100.0) if total_weight else 0.0
    return text, max(0.0, min(confidence, 1.0))


def _ocr_with_tesseract(image_bytes: bytes) -> LocalOcrResult:
    """Run local Tesseract OCR with installed Arabic/French/English packs.

    Import and executable failures are normal operational states.  They are
    returned as ``unavailable`` without leaking image content or filenames.
    """
    try:
        import pytesseract
        from pytesseract import Output
    except ImportError:
        return LocalOcrResult()

    configured_command = settings.tesseract_cmd.strip()
    if configured_command:
        pytesseract.pytesseract.tesseract_cmd = configured_command

    configured_tessdata = settings.tessdata_prefix.strip()
    if configured_tessdata:
        os.environ["TESSDATA_PREFIX"] = configured_tessdata

    variants = _normalized_image_variants(image_bytes)
    languages = _tesseract_languages(pytesseract)
    if not variants or not languages:
        return LocalOcrResult(languages=languages)

    best = LocalOcrResult(status="empty", languages=languages)
    lang_spec = "+".join(languages)
    for variant_name, image in variants:
        oriented = _correct_tesseract_orientation(image, pytesseract)
        try:
            data = pytesseract.image_to_data(
                oriented,
                lang=lang_spec,
                config="--oem 3 --psm 6",
                output_type=Output.DICT,
            )
        except Exception:
            return LocalOcrResult(languages=languages)
        text, confidence = _text_from_tesseract_data(data)
        if confidence > best.confidence or (
            confidence == best.confidence and len(text) > len(best.text)
        ):
            best = LocalOcrResult(
                text=text,
                confidence=confidence,
                backend=f"tesseract_{variant_name}",
                status="success" if text else "empty",
                languages=languages,
            )
    return best


def _local_text_extraction(
    file_bytes: bytes,
    content_type: str,
) -> tuple[str, int, LocalOcrResult]:
    """Extract text locally from a selectable PDF or an OCR-compatible image."""
    if content_type == "application/pdf":
        text, page_count = _extract_pdf_text_pypdf(file_bytes)
        if len(text.strip()) >= 80:
            confidence = 0.98 if len(text.strip()) >= 200 else 0.90
            return text, page_count, LocalOcrResult(
                text=text,
                confidence=confidence,
                backend="pypdf",
                status="success",
            )
        image_bytes = _pdf_first_page_as_png(file_bytes)
        if image_bytes:
            result = _ocr_with_tesseract(image_bytes)
            if result.text:
                return result.text, page_count, result
        if text.strip():
            return text, page_count, LocalOcrResult(
                text=text,
                confidence=min(0.75, 0.30 + len(text.strip()) / 200.0),
                backend="pypdf_partial",
                status="success",
            )
        return "", page_count, LocalOcrResult(status="unavailable")

    if content_type.startswith("image/"):
        result = _ocr_with_tesseract(file_bytes)
        return result.text, 1, result
    return "", 0, LocalOcrResult(status="unavailable")


# ─── Gemini Vision OCR ────────────────────────────────────────────────────────

def _ocr_with_gemini(image_bytes: bytes, mime: str, api_key: str, model: str) -> str:
    """Call Gemini Vision multimodal API to extract raw text from an image/PDF."""
    if not api_key:
        return ""
    try:
        prompt_text = (
            "Extract ALL text from this document exactly as it appears. "
            "Preserve Arabic (Darija and MSA), French, numbers, dates, stamps, "
            "and any special characters. "
            "Do NOT translate, summarise, or add commentary — output raw text only."
        )
        text = generate_text(
            api_key=api_key,
            model=model,
            contents=[binary_part(image_bytes, mime), prompt_text],
            temperature=0.0,
        )
        return text
    except GeminiRequestError:
        return ""



# ─── Step 3: LLM Document Analysis ───────────────────────────────────────────

def _analyze_with_gemini_sdk(
    text: str,
    lang: str,
    api_key: str,
    model: str,
    user_query: str = "",
) -> str:
    """Use direct Gemini SDK for rich document analysis with system instructions."""
    prompts = _DOCUMENT_PROMPTS[lang]
    user_query_instruction = ""
    if user_query and user_query.strip():
        if lang == "fr":
            user_query_instruction = f"👉 **Question / Message du citoyen** : \"{user_query.strip()}\"\nRépondez explicitement et en priorité à cette question dans votre analyse.\n\n"
        elif lang == "arabic":
            user_query_instruction = f"👉 **سؤال / رسالة المواطن** : \"{user_query.strip()}\"\nيرجى الإجابة بدقة وبشكل رئيسي على هذا السؤال في تحليلك.\n\n"
        else:
            user_query_instruction = f"👉 **سؤال / رسالة المواطن** : \"{user_query.strip()}\"\nجاوب على هاد السؤال بالخصوص في التحليل ديالك.\n\n"

    try:
        prompt_text = prompts["analyze"].format(
            text=text[:6000],
            user_query_instruction=user_query_instruction,
        )
        return generate_text(
            api_key=api_key,
            model=model,
            contents=prompt_text,
            system_instruction=prompts["system"],
            temperature=0.1,
        )
    except GeminiRequestError:
        return ""


def _deterministic_document_summary(
    text: str,
    lang: str,
    user_query: str = "",
) -> str:
    """Return a stable local summary when the external model is unavailable."""
    compact_text = " ".join(text.split())[:700]
    if not compact_text:
        return ""
    if lang == "fr":
        prefix = "L’analyse IA est temporairement indisponible. Voici le texte extrait localement :"
    elif lang == "arabic":
        prefix = "التحليل الذكي غير متاح مؤقتاً. هذا هو النص المستخرج محلياً:"
    else:
        prefix = "التحليل الذكي ما متوفرش مؤقتاً. هادا هو النص اللي تخرج محلياً:"
    return f"{prefix}\n\n> {compact_text}"


# ─── Public Entry Point ───────────────────────────────────────────────────────

def analyze_document(
    file_bytes: bytes,
    content_type: str,
    filename: str,
    language: str = "darija",
    google_api_key: str = "",
    gemini_model_name: str = "gemini-1.5-flash",
    user_query: str = "",
) -> DocumentAnalysis:
    """Run the full OCR → LLM analysis pipeline on an uploaded document.

    Args:
        file_bytes:        Raw bytes of the uploaded file.
        content_type:      MIME type (application/pdf, image/jpeg, image/png, image/webp).
        filename:          Original filename (for logging / display).
        language:          Chat language key ('darija', 'fr', 'arabic').
        google_api_key:    Google Gemini API key; if empty, Vision OCR is skipped.
        gemini_model_name: Gemini model to use for both OCR and analysis.
        user_query:        Optional accompanying text message / question from user.

    Returns:
        DocumentAnalysis dataclass with all pipeline results.
    """
    lang = _resolve_lang(language)
    result = DocumentAnalysis()
    result.is_image = content_type.startswith("image/")

    extracted_text, page_count, local_ocr = _local_text_extraction(file_bytes, content_type)
    result.page_count = page_count
    result.ocr_backend = local_ocr.backend
    result.ocr_confidence = local_ocr.confidence
    result.ocr_used = local_ocr.backend not in {"none", "pypdf", "pypdf_partial"} and bool(extracted_text)

    if google_api_key and (len(extracted_text.strip()) < 30 or local_ocr.confidence < 0.30):
        vision_bytes = file_bytes
        vision_mime = content_type
        if content_type == "application/pdf":
            rendered = _pdf_first_page_as_png(file_bytes)
            if rendered:
                vision_bytes, vision_mime = rendered, "image/png"
        vision_text = _ocr_with_gemini(
            vision_bytes,
            vision_mime,
            google_api_key,
            gemini_model_name,
        )
        if vision_text:
            extracted_text = vision_text
            result.ocr_used = True
            result.ocr_backend = "gemini_vision"
            result.ocr_confidence = 0.72
            result.gemini_vision_status = "success"

    result.extracted_text = extracted_text
    development_trace(
        "DOCUMENT OCR",
        backend=result.ocr_backend,
        status="success" if extracted_text else local_ocr.status,
        confidence=f"{result.ocr_confidence:.2f}",
    )

    # ── 2. LLM Analysis ───────────────────────────────────────────────────────
    if len(extracted_text.strip()) >= 30:
        if google_api_key:
            result.llm_analysis = _analyze_with_gemini_sdk(
                extracted_text, lang, google_api_key, gemini_model_name, user_query=user_query
            )
        if not result.llm_analysis:
            result.llm_analysis = _deterministic_document_summary(
                extracted_text, lang, user_query=user_query
            )

    development_trace(
        "DOCUMENT AI",
        gemini_vision=result.gemini_vision_status,
        gemini_structured=result.gemini_structured_status,
    )

    return result


# ─── Chat Message Formatter ───────────────────────────────────────────────────

def format_analysis_chat_message(
    analysis: DocumentAnalysis,
    filename: str,
    language: str = "darija",
) -> str:
    """Convert a DocumentAnalysis into a user-facing markdown chat reply."""
    lang = _resolve_lang(language)
    prompts = _DOCUMENT_PROMPTS[lang]

    # Clean, concise header
    page_info = f"PDF · {analysis.page_count} page(s)" if not analysis.is_image else "Image"
    header = f"📄 **{filename}** *({page_info})*\n\n"

    if analysis.error:
        return header + prompts["error"]

    if not analysis.llm_analysis:
        return header + prompts["no_text"]

    # OCR badge
    ocr_badge = ""
    if analysis.ocr_used:
        ocr_badge_map = {
            "fr": "🔬 *Reconnaissance optique de caractères (OCR) utilisée*\n\n",
            "arabic": "🔬 *تم استخدام تقنية التعرف الضوئي على الحروف (OCR)*\n\n",
            "darija": "🔬 *خدمنا تقنية OCR باش نقراو الصورة*\n\n",
        }
        ocr_badge = ocr_badge_map.get(lang, "")

    footer_map = {
        "fr": "\n\n💬 *N'hésitez pas si vous avez d'autres questions sur ce document ou sur vos démarches !*",
        "arabic": "\n\n💬 *لا تتردد في طرح أي سؤال إضافي حول هذه الوثيقة أو إجراءاتك الإدارية!*",
        "darija": "\n\n💬 *سولني في أي وقت إلا عندك أي سؤال على هاد الوثيقة أو الإجراءات ديالك!*",
    }
    footer = footer_map.get(lang, "")

    return header + ocr_badge + analysis.llm_analysis + footer


# ─── Feature 2: Structured Document Intelligence (OCR + Anomaly Detection) ────

_STRUCTURED_JSON_SYSTEM_PROMPT = (
    "You are an AI Document Intelligence Agent specialized in Moroccan administrative documents "
    "(CIN, residence certificate, birth certificate, utility bills, passport, driving license). "
    "You must return ONLY a raw JSON object with NO markdown code blocks, NO backticks, and NO extra commentary."
)

_STRUCTURED_JSON_USER_PROMPT = """Analyze this document and extract its structured metadata for administrative form auto-fill.
Return ONLY a valid JSON object matching this schema:
{
  "document_type": "cin" | "residence_certificate" | "birth_certificate" | "electricity_bill" | "passport" | "driving_license" | "other" | "irrelevant",
  "cin_number": "string or null",
  "first_name": "string or null",
  "last_name": "string or null",
  "full_name": "string or null",
  "birth_date": "DD/MM/YYYY or YYYY-MM-DD or null",
  "address": "string or null",
  "expiry_date": "DD/MM/YYYY or YYYY-MM-DD or null",
  "issuing_authority": "string or null",
  "confidence_score": 0.0 to 1.0,
  "is_valid": true,
  "is_expired": false,
  "is_blurry": false,
  "is_relevant": true,
  "anomalies": ["short list of detected issues in French or Darija if any"]
}

STRICT RULES:
1. Moroccan CIN (بطاقة التعريف الوطنية):
   - cin_number usually has 1 or 2 uppercase letters followed by 4 to 7 digits (e.g. BK654321, AB123456, A987654).
   - Look for French Latin names (NOM, PRÉNOM) and Arabic names (الاسم العائلي, الاسم الشخصي).
2. Anomaly Detection:
   - Expired: If expiry_date is in the past compared to current date (year 2026), mark is_expired=true and is_valid=false.
   - Blurry: If text is illegible, pixelated or difficult to decipher, mark is_blurry=true.
   - Irrelevant: If image is a selfie, animal, scenery, food, or non-administrative picture, mark is_relevant=false, document_type="irrelevant", and add anomaly.
3. Return raw JSON ONLY.
"""


def _clean_json_str(raw: str) -> str:
    """Strip markdown code fences and whitespace from LLM JSON response."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _build_warnings(
    is_expired: bool,
    is_blurry: bool,
    is_relevant: bool,
    anomalies: list[str],
    lang: str,
) -> list[str]:
    """Generate user-facing localized warnings for the citizen."""
    warnings: list[str] = []
    normalized_lang = _resolve_lang(lang)

    if not is_relevant:
        if normalized_lang == "fr":
            warnings.append("Ce fichier ne semble pas correspondre à une pièce administrative officielle.")
        elif normalized_lang == "arabic":
            warnings.append("الملف المرفق لا يبدو وثيقة إدارية رسمية معترف بها.")
        else:
            warnings.append("هاد الملف ماشي وثيقة إدارية رسمية، تأكد من الصورة اللي رفعتي.")

    if is_expired:
        if normalized_lang == "fr":
            warnings.append("Attention : Ce document semble expiré (date de validité dépassée).")
        elif normalized_lang == "arabic":
            warnings.append("تنبيه: هذه الوثيقة تبدو منتهية الصلاحية، يرجى تجديدها.")
        else:
            warnings.append("رد البال: هاد الوثيقة بانت سالات الصلاحية ديالها، من الأفضل تجددها.")

    if is_blurry:
        if normalized_lang == "fr":
            warnings.append("Qualité d'image floue ou faible résolution : veuillez vérifier les données extraites.")
        elif normalized_lang == "arabic":
            warnings.append("جودة الصورة ضعيفة أو غير واضحة: يرجى مراجعة البيانات المستخرجة.")
        else:
            warnings.append("الصورة شوية مضببة: عفاك تأكد من صحة المعلومات اللي خرجنا منها.")

    # Append any custom model-detected anomalies if not redundant
    for a in anomalies or []:
        if a and a not in warnings:
            warnings.append(a)

    return warnings


_DOCUMENT_TYPE_RULES: dict[str, tuple[tuple[str, float], ...]] = {
    "cin": (
        ("carte nationale d'identite", 0.72),
        ("carte nationale d’identité", 0.72),
        ("بطاقة التعريف الوطنية", 0.75),
        ("البطاقة الوطنية للتعريف", 0.75),
        ("dgsn", 0.28),
        ("cin", 0.18),
    ),
    "residence_certificate": (
        ("certificat de residence", 0.72),
        ("certificat de domicile", 0.68),
        ("شهادة السكنى", 0.75),
        ("شهادة الإقامة", 0.70),
    ),
    "birth_certificate": (
        ("acte de naissance", 0.72),
        ("extrait de naissance", 0.68),
        ("عقد الازدياد", 0.75),
        ("رسم الولادة", 0.75),
        ("الحالة المدنية", 0.34),
    ),
    "electricity_bill": (
        ("facture d'electricite", 0.72),
        ("facture d’eau", 0.70),
        ("facture d'eau", 0.70),
        ("فاتورة الماء", 0.70),
        ("فاتورة الكهرباء", 0.72),
        ("onee", 0.36),
        ("lydec", 0.36),
        ("redal", 0.36),
        ("amendis", 0.36),
    ),
    "passport": (("passeport", 0.72), ("جواز السفر", 0.75)),
    "driving_license": (("permis de conduire", 0.72), ("رخصة السياقة", 0.75)),
}


def _normalized_search_text(text: str) -> str:
    normalized = text.casefold().replace("’", "'")
    normalized = re.sub(r"[éèêë]", "e", normalized)
    normalized = re.sub(r"[àâä]", "a", normalized)
    normalized = re.sub(r"[îï]", "i", normalized)
    normalized = re.sub(r"[ôö]", "o", normalized)
    normalized = re.sub(r"[ùûü]", "u", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _classify_document_locally(text: str) -> tuple[str, float, list[str]]:
    """Conservatively classify from OCR evidence, never from the filename alone."""
    normalized = _normalized_search_text(text)
    if len(normalized) < 10:
        return "unknown", 0.05 if normalized else 0.0, []

    scores: dict[str, float] = {}
    evidence: dict[str, list[str]] = {}
    for document_type, rules in _DOCUMENT_TYPE_RULES.items():
        matches = [(phrase, weight) for phrase, weight in rules if phrase in normalized]
        if matches:
            scores[document_type] = min(0.97, sum(weight for _, weight in matches))
            evidence[document_type] = [phrase for phrase, _ in matches]

    cin_match = re.search(r"(?<![A-Z0-9])([A-Z]{1,2})\s*[- ]?\s*([0-9]{4,7})(?![0-9])", text.upper())
    if cin_match:
        scores["cin"] = min(0.97, scores.get("cin", 0.0) + 0.32)
        evidence.setdefault("cin", []).append("national_id_pattern")
    if re.search(r"\b(?:nom|pr[ée]nom|date de naissance)\b", text, re.IGNORECASE):
        scores["cin"] = min(0.97, scores.get("cin", 0.0) + 0.12)
        evidence.setdefault("cin", []).append("identity_labels")
    if any(label in text for label in ("الاسم العائلي", "الاسم الشخصي", "تاريخ الازدياد")):
        scores["cin"] = min(0.97, scores.get("cin", 0.0) + 0.12)
        evidence.setdefault("cin", []).append("arabic_identity_labels")

    if not scores:
        return "unknown", 0.12, []
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]
    runner_up = max((score for doc_type, score in scores.items() if doc_type != best_type), default=0.0)
    if best_score < 0.60 or best_score - runner_up < 0.12:
        return "unknown", min(best_score, 0.49), evidence.get(best_type, [])
    return best_type, round(best_score, 3), evidence.get(best_type, [])


def _labeled_value(text: str, label_pattern: str, value_pattern: str, max_length: int = 100) -> Optional[str]:
    """Extract a same-line or immediately-following-line label value."""
    match = re.search(
        rf"(?:{label_pattern})\s*[:=\-]?\s*({value_pattern})",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        match = re.search(
            rf"(?:{label_pattern})\s*[:=\-]?\s*\n\s*({value_pattern})",
            text,
            re.IGNORECASE | re.MULTILINE,
        )
    if not match:
        return None
    value = re.sub(r"\s+", " ", match.group(1)).strip(" :-")[:max_length]
    return value or None


def _valid_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            datetime.strptime(value, fmt)
            return value
        except ValueError:
            continue
    return None


def _heuristic_structured_extract(
    text: str,
    filename: str,
    lang: str = "darija",
    ocr_used: bool = False,
    page_count: int = 1,
    ocr_confidence: Optional[float] = None,
    ocr_backend: str = "none",
) -> ExtractedDocumentMetadata:
    """Deterministic, schema-validated local extractor for Moroccan documents."""
    del filename  # Filenames are untrusted and may contain PII or misleading words.
    text = text or ""
    effective_ocr_confidence = (
        max(0.0, min(float(ocr_confidence), 1.0))
        if ocr_confidence is not None
        else (0.90 if text.strip() else 0.0)
    )
    doc_type, classification_confidence, indicators = _classify_document_locally(text)
    field_metadata: dict[str, dict[str, Any]] = {}

    def record(key: str, value: Optional[str], confidence: float, source: str) -> Optional[str]:
        if value:
            field_metadata[key] = {
                "value": value,
                "confidence": round(max(0.0, min(confidence, 1.0)), 2),
                "source": source,
            }
        return value

    upper = text.upper()
    cin_match = re.search(r"(?<![A-Z0-9])([A-Z]{1,2})\s*[- ]?\s*([0-9]{4,7})(?![0-9])", upper)
    cin_number = record(
        "national_id",
        f"{cin_match.group(1)}{cin_match.group(2)}" if cin_match else None,
        0.94 if doc_type == "cin" else 0.78,
        "regex_local",
    )

    latin_word = r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\- ]{1,60}"
    # Deliberately exclude newlines so one label never consumes the next one.
    arabic_word = r"[\u0600-\u06FF][\u0600-\u06FF \u00A0\-]{1,60}"
    last_name = _labeled_value(text, r"(?:\bnom\b(?!\s+et)|الاسم\s+العائلي|النسب)", rf"(?:{latin_word}|{arabic_word})")
    first_name = _labeled_value(text, r"(?:\bpr[ée]nom\b|الاسم\s+الشخصي)", rf"(?:{latin_word}|{arabic_word})")
    full_name = _labeled_value(text, r"(?:\bnom\s+et\s+pr[ée]nom\b|الاسم\s+الكامل)", rf"(?:{latin_word}|{arabic_word})")

    def clean_name(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        value = re.split(
            r"(?i)\b(?:pr[ée]nom|nom|n[ée]\s+le|naissance|adresse|cin|valable)\b|(?:تاريخ|العنوان|رقم)",
            value,
        )[0].strip()
        if not value:
            return None
        return value.title() if re.search(r"[A-Za-zÀ-ÿ]", value) else value

    first_name = clean_name(first_name)
    last_name = clean_name(last_name)
    full_name = clean_name(full_name)
    if not full_name and (first_name or last_name):
        full_name = " ".join(value for value in (first_name, last_name) if value)
    record("first_name", first_name, 0.88, "label_proximity_local")
    record("last_name", last_name, 0.88, "label_proximity_local")
    record("full_name", full_name, 0.86, "label_proximity_local")

    date_pattern = r"(?:\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{4}-\d{1,2}-\d{1,2})"
    birth_date = _valid_date(_labeled_value(
        text,
        r"(?:n[ée]\s+le|date\s+de\s+naissance|naissance|تاريخ\s+الازدياد|تاريخ\s+الميلاد)",
        date_pattern,
        10,
    ))
    expiry_date = _valid_date(_labeled_value(
        text,
        r"(?:valable\s+jusqu['’]?au|expire\s+le|date\s+d['’]expiration|validit[ée]|صالح\s+إلى|تاريخ\s+انتهاء\s+الصلاحية)",
        date_pattern,
        10,
    ))
    record("birth_date", birth_date, 0.92, "label_regex_local")
    record("expiry_date", expiry_date, 0.92, "label_regex_local")

    address = _labeled_value(
        text,
        r"(?:adresse|demeurant(?:e)?|r[ée]sidant(?:e)?|العنوان)",
        r"[^\n\r]{5,120}",
        120,
    )
    if address:
        address = re.split(
            r"(?i)\b(?:valable|date|n[ée]\s+le|cin|n°|nom|pr[ée]nom)\b|(?:تاريخ|الاسم|رقم)",
            address,
        )[0].strip(" ,;:-") or None
    record("address", address, 0.84, "label_proximity_local")

    issuing_authority = _labeled_value(
        text,
        r"(?:d[ée]livr[ée]e?\s+par|autorit[ée]\s+[ée]mettrice|الجهة\s+المصدرة)",
        r"[^\n\r]{2,80}",
        80,
    )
    if not issuing_authority and re.search(r"\bDGSN\b", upper):
        issuing_authority = "DGSN"
    record("issuing_authority", issuing_authority, 0.82, "label_or_vocabulary_local")

    is_expired = False
    if expiry_date:
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d"):
            try:
                is_expired = datetime.strptime(expiry_date, fmt).date() < datetime.now().date()
                break
            except ValueError:
                continue

    is_blurry = not text.strip() or effective_ocr_confidence < 0.30
    is_relevant = doc_type != "unknown"
    is_valid = is_relevant and not is_expired
    anomalies: list[str] = []
    if doc_type == "unknown" and text.strip():
        anomalies.append("Document type could not be identified with sufficient confidence.")

    detected_confidences = [item["confidence"] for item in field_metadata.values()]
    if detected_confidences:
        field_average = sum(detected_confidences) / len(detected_confidences)
        extraction_confidence = (
            0.45 * classification_confidence
            + 0.35 * field_average
            + 0.20 * effective_ocr_confidence
        )
    else:
        extraction_confidence = 0.60 * classification_confidence + 0.20 * effective_ocr_confidence
    extraction_confidence = max(0.0, min(extraction_confidence, 0.97))
    warnings = _build_warnings(is_expired, is_blurry, is_relevant, anomalies, lang)

    return ExtractedDocumentMetadata(
        document_type=doc_type,
        document_type_label=DOCUMENT_TYPE_LABELS.get(doc_type, DOCUMENT_TYPE_LABELS["unknown"]),
        cin_number=cin_number,
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        birth_date=birth_date,
        address=address,
        expiry_date=expiry_date,
        issuing_authority=issuing_authority,
        confidence_score=extraction_confidence,
        ocr_confidence=effective_ocr_confidence,
        classification_confidence=classification_confidence,
        extraction_confidence=extraction_confidence,
        classification_source="local_rules",
        ocr_backend=ocr_backend,
        field_metadata=field_metadata,
        document_indicators=indicators,
        is_valid=is_valid,
        is_expired=is_expired,
        is_blurry=is_blurry,
        is_relevant=is_relevant,
        warnings=warnings,
        anomalies=anomalies,
        raw_extracted_text=text[:3000],
        ocr_used=ocr_used,
        page_count=page_count,
    )


def extract_structured_metadata(
    file_bytes: bytes,
    content_type: str,
    filename: str,
    language: str = "darija",
    google_api_key: str = "",
    gemini_model_name: str = "gemini-2.0-flash",
) -> ExtractedDocumentMetadata:
    """Extract metadata locally first, using Gemini only for ambiguity."""
    lang = _resolve_lang(language)
    extracted_text, page_count, local_ocr = _local_text_extraction(file_bytes, content_type)
    ocr_used = local_ocr.backend not in {"none", "pypdf", "pypdf_partial"} and bool(extracted_text)
    gemini_vision_status = "unavailable"
    gemini_structured_status = "unavailable"

    # Local OCR is the baseline. Gemini Vision is attempted only when local
    # extraction is absent or clearly too weak to support deterministic rules.
    if google_api_key and (len(extracted_text.strip()) < 30 or local_ocr.confidence < 0.30):
        vision_bytes = file_bytes
        vision_mime = content_type
        if content_type == "application/pdf":
            rendered = _pdf_first_page_as_png(file_bytes)
            if rendered:
                vision_bytes, vision_mime = rendered, "image/png"
        gemini_text = _ocr_with_gemini(
            vision_bytes,
            vision_mime,
            google_api_key,
            gemini_model_name,
        )
        if gemini_text:
            extracted_text = gemini_text
            ocr_used = True
            local_ocr = LocalOcrResult(
                text=gemini_text,
                confidence=0.72,
                backend="gemini_vision",
                status="success",
            )
            gemini_vision_status = "success"

    development_trace(
        "DOCUMENT OCR",
        backend=local_ocr.backend,
        status=local_ocr.status,
        confidence=f"{local_ocr.confidence:.2f}",
    )

    local_result = _heuristic_structured_extract(
        extracted_text,
        filename,
        lang=lang,
        ocr_used=ocr_used,
        page_count=page_count,
        ocr_confidence=local_ocr.confidence,
        ocr_backend=local_ocr.backend,
    )

    # Ask Gemini for structured interpretation only when local evidence is
    # ambiguous.  If the preceding Vision request failed, do not immediately
    # issue another provider request that is likely to fail for the same reason.
    needs_interpretation = (
        local_result.document_type == "unknown"
        or local_result.extraction_confidence < 0.62
    )
    may_try_structured = bool(google_api_key) and needs_interpretation and not (
        local_ocr.status != "success" and gemini_vision_status == "unavailable"
    )
    final_result = local_result
    extraction_backend = "local_rules"
    if may_try_structured:
        try:
            if content_type.startswith("image/"):
                parts = [
                    binary_part(file_bytes, content_type),
                    _STRUCTURED_JSON_USER_PROMPT,
                ]
            elif content_type == "application/pdf":
                img_bytes = _pdf_first_page_as_png(file_bytes)
                if img_bytes:
                    parts = [
                        binary_part(img_bytes, "image/png"),
                        _STRUCTURED_JSON_USER_PROMPT,
                    ]
                else:
                    parts = [
                        f"{_STRUCTURED_JSON_USER_PROMPT}\n\nDocument Text Content:\n{extracted_text[:6000]}"
                    ]
            else:
                parts = [
                    f"{_STRUCTURED_JSON_USER_PROMPT}\n\nDocument Text Content:\n{extracted_text[:6000]}"
                ]

            response_text = generate_text(
                api_key=google_api_key,
                model=gemini_model_name,
                contents=parts,
                system_instruction=_STRUCTURED_JSON_SYSTEM_PROMPT,
                temperature=0.0,
                response_mime_type="application/json",
            )
            raw_json = _clean_json_str(response_text)
            if raw_json:
                data = json.loads(raw_json)
                allowed_types = set(DOCUMENT_TYPE_LABELS) - {"unknown"}
                doc_type = data.get("document_type")
                if doc_type not in allowed_types:
                    doc_type = "unknown"
                is_expired = bool(data.get("is_expired", False))
                is_blurry = bool(data.get("is_blurry", False))
                is_relevant = bool(data.get("is_relevant", True))
                is_valid = bool(data.get("is_valid", not is_expired and is_relevant))
                anomalies = data.get("anomalies") or []
                warnings = _build_warnings(is_expired, is_blurry, is_relevant, anomalies, lang)

                first_name = data.get("first_name")
                last_name = data.get("last_name")
                full_name = data.get("full_name") or (
                    f"{first_name} {last_name}".strip() if first_name or last_name else None
                )
                # Provider confidence remains bounded because the response is
                # interpretation, not independently verified evidence.
                model_confidence = max(0.0, min(float(data.get("confidence_score", 0.0)), 0.88))
                values = {
                    "national_id": data.get("cin_number"),
                    "first_name": first_name,
                    "last_name": last_name,
                    "full_name": full_name,
                    "birth_date": data.get("birth_date"),
                    "address": data.get("address"),
                    "expiry_date": data.get("expiry_date"),
                    "issuing_authority": data.get("issuing_authority"),
                }
                field_metadata = {
                    key: {
                        "value": value,
                        "confidence": round(min(model_confidence, 0.85), 2),
                        "source": "gemini_structured",
                    }
                    for key, value in values.items()
                    if value
                }
                final_result = ExtractedDocumentMetadata(
                    document_type=doc_type,
                    document_type_label=DOCUMENT_TYPE_LABELS.get(doc_type, DOCUMENT_TYPE_LABELS["unknown"]),
                    cin_number=data.get("cin_number"),
                    first_name=first_name,
                    last_name=last_name,
                    full_name=full_name,
                    birth_date=data.get("birth_date"),
                    address=data.get("address"),
                    expiry_date=data.get("expiry_date"),
                    issuing_authority=data.get("issuing_authority"),
                    confidence_score=model_confidence,
                    ocr_confidence=local_ocr.confidence,
                    classification_confidence=model_confidence,
                    extraction_confidence=model_confidence,
                    classification_source="gemini_structured",
                    ocr_backend=local_ocr.backend,
                    field_metadata=field_metadata,
                    document_indicators=local_result.document_indicators,
                    is_valid=is_valid,
                    is_expired=is_expired,
                    is_blurry=is_blurry,
                    is_relevant=is_relevant,
                    warnings=warnings,
                    anomalies=anomalies,
                    raw_extracted_text=extracted_text[:3000],
                    ocr_used=ocr_used,
                    page_count=page_count,
                )
                gemini_structured_status = "success"
                extraction_backend = "gemini_structured"
        except (GeminiRequestError, json.JSONDecodeError, TypeError, ValueError):
            # Provider availability and malformed provider output are expected
            # fallback conditions; never print payloads, OCR text, or PII.
            gemini_structured_status = "unavailable"

    development_trace(
        "DOCUMENT CLASSIFIER",
        backend=final_result.classification_source,
        document_type=final_result.document_type,
        confidence=f"{final_result.classification_confidence:.2f}",
    )
    development_trace(
        "FIELD EXTRACTION",
        backend=extraction_backend,
        fields_detected_count=len(final_result.field_metadata),
        overall_confidence=f"{final_result.extraction_confidence:.2f}",
    )
    development_trace(
        "DOCUMENT AI",
        gemini_vision=gemini_vision_status,
        gemini_structured=gemini_structured_status,
    )
    return final_result
