"""Smart Document Analyzer — OCR + LLM Analysis Module
=======================================================

Pipeline:
    1. MIME detection (PDF / Image)
    2. Text extraction:
        a) PDF with selectable text  → pypdf (fast path)
        b) Scanned PDF / image        → Gemini Vision multimodal (OCR path)
        c) Fallback                   → "Could not extract text" message
    3. LLM analysis prompt →
        • Detected document type (CIN, birth certificate, electricity bill…)
        • Key entities extracted (name, date, address, CIN number…)
        • Validity check (< 3 months old?  Stamp present?  Arabic/French?)
        • Conformity verdict for common Moroccan administrative procedures
    4. Returns a structured analysis object used by the chat endpoint.

Supported languages for the response: darija · arabic · fr
"""

from __future__ import annotations

import base64
from datetime import datetime
import io
import json
import re
from dataclasses import dataclass
from typing import Optional, Any


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
    confidence_score: float = 0.85
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


# ─── Step 2: Gemini Vision OCR ────────────────────────────────────────────────

def _ocr_with_gemini(image_bytes: bytes, mime: str, api_key: str, model: str) -> str:
    """Call Gemini Vision multimodal API to extract raw text from an image/PDF."""
    if not api_key:
        print("[WARN] Gemini Vision OCR skipped: GOOGLE_API_KEY is not set.")
        return ""
    try:
        import google.generativeai as genai  # type: ignore
        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        genai.configure(api_key=api_key)
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        prompt_text = (
            "Extract ALL text from this document exactly as it appears. "
            "Preserve Arabic (Darija and MSA), French, numbers, dates, stamps, "
            "and any special characters. "
            "Do NOT translate, summarise, or add commentary — output raw text only."
        )
        # Build structured parts
        parts = [
            {"inline_data": {"mime_type": mime, "data": encoded}},
            prompt_text,
        ]
        m = genai.GenerativeModel(
            model,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )
        response = m.generate_content(parts)
        try:
            text = (response.text or "").strip()
            if text:
                print(f"[OK] Gemini Vision OCR: extracted {len(text)} chars.")
            return text
        except (AttributeError, ValueError) as ve:
            # Response blocked or no parts — log and return empty
            print(f"[WARN] Gemini Vision: no text in response ({ve})")
            return ""
    except Exception as exc:
        print(f"[WARN] Gemini Vision OCR failed: {exc}")
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
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(model, system_instruction=prompts["system"])
        prompt_text = prompts["analyze"].format(
            text=text[:6000],
            user_query_instruction=user_query_instruction,
        )
        response = m.generate_content(prompt_text)
        try:
            return (response.text or "").strip()
        except (AttributeError, ValueError):
            return ""
    except Exception as exc:
        print(f"[WARN] Gemini analysis failed: {exc}")
        return ""


def _analyze_with_llamaindex_llm(
    text: str,
    lang: str,
    user_query: str = "",
) -> str:
    """Fallback: use google-generativeai directly (no LlamaIndex)."""
    prompts = _DOCUMENT_PROMPTS[lang]
    user_query_instruction = ""
    if user_query and user_query.strip():
        if lang == "fr":
            user_query_instruction = f"Question du citoyen : \"{user_query.strip()}\"\nRepondez a cette question.\n\n"
        else:
            user_query_instruction = f"سؤال المواطن : \"{user_query.strip()}\"\n\n"

    try:
        import google.generativeai as genai
        import os

        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
        if not api_key:
            return ""

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        prompt_text = prompts["analyze"].format(
            text=text[:4000],
            user_query_instruction=user_query_instruction,
        )
        full_prompt = prompts["system"] + "\n\n" + prompt_text
        response = model.generate_content(full_prompt)
        return (response.text or "").strip()
    except Exception as exc:
        print(f"[WARN] Gemini fallback analysis failed: {exc}")
        return ""


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

    extracted_text = ""
    page_count = 0

    # ── 1. Text extraction ────────────────────────────────────────────────────
    if content_type == "application/pdf":
        extracted_text, page_count = _extract_pdf_text_pypdf(file_bytes)
        result.page_count = page_count

        # Scanned PDF threshold: fewer than 80 meaningful chars → trigger OCR
        if len(extracted_text.strip()) < 80 and google_api_key:
            print(f"[INFO] Scanned PDF detected for '{filename}'. Running Vision OCR.")
            img_bytes = _pdf_first_page_as_png(file_bytes)
            if img_bytes:
                ocr_text = _ocr_with_gemini(img_bytes, "image/png", google_api_key, gemini_model_name)
            else:
                # PyMuPDF not available — send PDF bytes directly (Gemini supports it)
                ocr_text = _ocr_with_gemini(file_bytes, "application/pdf", google_api_key, gemini_model_name)
            if ocr_text:
                extracted_text = ocr_text
                result.ocr_used = True
                print(f"[OK] OCR: {len(extracted_text)} chars extracted from '{filename}'.")

    elif content_type.startswith("image/"):
        page_count = 1
        result.page_count = 1
        if google_api_key:
            extracted_text = _ocr_with_gemini(file_bytes, content_type, google_api_key, gemini_model_name)
            if extracted_text:
                result.ocr_used = True
                print(f"[OK] Vision OCR: {len(extracted_text)} chars from image '{filename}'.")

    result.extracted_text = extracted_text

    # ── 2. LLM Analysis ───────────────────────────────────────────────────────
    if len(extracted_text.strip()) >= 30:
        if google_api_key:
            result.llm_analysis = _analyze_with_gemini_sdk(
                extracted_text, lang, google_api_key, gemini_model_name, user_query=user_query
            )
        if not result.llm_analysis:
            result.llm_analysis = _analyze_with_llamaindex_llm(
                extracted_text, lang, user_query=user_query
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


def _heuristic_structured_extract(
    text: str,
    filename: str,
    lang: str = "darija",
    ocr_used: bool = False,
    page_count: int = 1,
) -> ExtractedDocumentMetadata:
    """Resilient fallback extractor for Moroccan administrative documents using heuristics and regex."""
    upper = text.upper()
    cin_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    birth_date: Optional[str] = None
    expiry_date: Optional[str] = None
    address: Optional[str] = None
    issuing_authority: Optional[str] = None
    doc_type = "other"
    is_valid = True
    is_expired = False
    is_blurry = len(text.strip()) < 20 and not text.strip()
    is_relevant = len(text.strip()) >= 10
    confidence = 0.75
    anomalies: list[str] = []

    # 1. Moroccan CIN detection
    cin_match = re.search(r'\b([A-Z]{1,2})\s*([0-9]{4,7})\b', text)
    if cin_match:
        cin_number = f"{cin_match.group(1)}{cin_match.group(2)}"
        confidence += 0.15

    # 2. Document type detection (combining filename and extracted text)
    combined = f"{filename} {text}".upper()
    if any(k in combined for k in ["CARTE NATIONALE", "CARTE_NATIONALE", "CIN", "IDENTITE", "DGSN"]) or "بطاقة التعريف" in text or cin_match:
        doc_type = "cin"
        issuing_authority = "DGSN (Direction Générale de la Sûreté Nationale)"
        confidence = max(confidence, 0.90)
        is_relevant = True
    elif any(k in combined for k in ["RESIDENCE", "HABITATION", "LOGEMENT"]) or "السكنى" in text or "سكنى" in text:
        doc_type = "residence_certificate"
        issuing_authority = "DGSN / Sûreté Nationale / Caïdat"
        confidence = max(confidence, 0.90)
        is_relevant = True
    elif any(k in combined for k in ["NAISSANCE", "ETAT CIVIL", "ACTE"]) or "عقد الازدياد" in text or "الحالة المدنية" in text or "ازدياد" in text:
        doc_type = "birth_certificate"
        issuing_authority = "Bureau de l'État Civil"
        confidence = max(confidence, 0.90)
        is_relevant = True
    elif any(kw in combined for kw in ["LYDEC", "REDAL", "ONEE", "AMENDIS", "RADEE", "EAU", "ELECTRICITE", "FACTURE"]):
        doc_type = "electricity_bill"
        issuing_authority = "Régie de distribution d'eau et d'électricité"
        confidence = max(confidence, 0.90)
        is_relevant = True
    elif "PASSEPORT" in combined or "جواز" in text:
        doc_type = "passport"
        issuing_authority = "Ministère de l'Intérieur"
        confidence = max(confidence, 0.90)
        is_relevant = True
    elif "PERMIS" in combined or "سياقة" in text:
        doc_type = "driving_license"
        issuing_authority = "NARSA (Agence Nationale de la Sécurité Routière)"
        confidence = max(confidence, 0.90)
        is_relevant = True
    elif not is_relevant:
        doc_type = "irrelevant"
        confidence = 0.2
        is_valid = False

    # 3. Dates extraction
    exp_match = re.search(
        r'(?:valable\s*jusqu[\'\s]*au|expire\s*le|validit[ée]\s*[:=]?|صالح\s*إلى)\s*[:=]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{4})',
        text,
        re.IGNORECASE,
    )
    if exp_match:
        expiry_date = exp_match.group(1)

    birth_match = re.search(
        r'(?:n[ée]\s*le|naissance\s*[:=]?|تاريخ\s*الازدياد)\s*[:=]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{4})',
        text,
        re.IGNORECASE,
    )
    if birth_match:
        birth_date = birth_match.group(1)

    date_matches = re.findall(r'\b(\d{1,2}[./-]\d{1,2}[./-]\d{4})\b', text)
    if date_matches:
        if not birth_date:
            birth_date = date_matches[0]
        if not expiry_date and len(date_matches) > 1:
            expiry_date = date_matches[-1]

    if expiry_date:
        try:
            # Check expiration against current year (2026)
            parts = re.split(r'[./-]', expiry_date)
            year = int(parts[2]) if len(parts) == 3 else 0
            if 2000 <= year < 2026:
                is_expired = True
                is_valid = False
        except Exception:
            pass

    # 4. Address detection
    addr_match = re.search(
        r'(?:adresse|demeurant[a-z\s]*|résidant[a-z\s]*|العنوان|حي|زنقة|شارع)\s*[:=]?\s*([^\n\r]{5,70})',
        text,
        re.IGNORECASE,
    )
    if addr_match:
        raw_addr = addr_match.group(1).strip()
        # Cut off if trailing keywords appear like "Valable jusqu'au" or dates
        raw_addr = re.split(r'(?i)\b(?:valable|date|né|ne le|cin|n°)\b', raw_addr)[0].strip()
        if raw_addr:
            address = raw_addr

    # 5. Name detection heuristics
    nom_match = re.search(r'\bnom\s*[:=]?\s*([A-Za-zÀ-ÿ\-]+)', text, re.IGNORECASE)
    prenom_match = re.search(r'\bpr[ée]nom\s*[:=]?\s*([A-Za-zÀ-ÿ\-]+)', text, re.IGNORECASE)
    if nom_match and prenom_match:
        last_name = nom_match.group(1).strip().capitalize()
        first_name = prenom_match.group(1).strip().capitalize()
        full_name = f"{first_name} {last_name}"
    elif nom_match:
        last_name = nom_match.group(1).strip().capitalize()
    elif prenom_match:
        first_name = prenom_match.group(1).strip().capitalize()
    else:
        name_match = re.search(
            r'(?:nom\s*(?:et\s*prénom)?)\s*[:=]?\s*([A-Za-zÀ-ÿ\s]{3,35})',
            text,
            re.IGNORECASE,
        )
        if name_match:
            full_name = name_match.group(1).strip().title()
            parts = full_name.split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = " ".join(parts[1:])
            else:
                first_name = full_name

    if not text.strip() and doc_type != "irrelevant":
        is_blurry = False
        norm_l = _resolve_lang(lang)
        if norm_l == "fr":
            anomalies.append("Document reconnu. Vous pouvez ajuster vos coordonnées ci-dessous pour pré-remplir votre démarche.")
        elif norm_l == "arabic":
            anomalies.append("تم التعرف على الوثيقة. يرجى إدخال أو مراجعة البيانات في الخانات أسفله.")
        else:
            anomalies.append("تم التعرف على الوثيقة. تقدر تعمر أو تراجع المعلومات ديالك في الخانات أسفله.")

    warnings = _build_warnings(is_expired, is_blurry, is_relevant, anomalies, lang)

    return ExtractedDocumentMetadata(
        document_type=doc_type,
        document_type_label=DOCUMENT_TYPE_LABELS.get(doc_type, DOCUMENT_TYPE_LABELS["other"]),
        cin_number=cin_number,
        first_name=first_name,
        last_name=last_name,
        full_name=full_name or (f"{first_name} {last_name}".strip() if first_name or last_name else None),
        birth_date=birth_date,
        address=address,
        expiry_date=expiry_date,
        issuing_authority=issuing_authority,
        confidence_score=min(confidence, 0.98),
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
    """Run OCR and multimodal LLM to extract structured entities and detect anomalies."""
    lang = _resolve_lang(language)
    ocr_used = False
    page_count = 1
    extracted_text = ""

    # 1. Text extraction / OCR
    if content_type == "application/pdf":
        extracted_text, page_count = _extract_pdf_text_pypdf(file_bytes)
        if len(extracted_text.strip()) < 80 and google_api_key:
            img_bytes = _pdf_first_page_as_png(file_bytes)
            if img_bytes:
                ocr_text = _ocr_with_gemini(img_bytes, "image/png", google_api_key, gemini_model_name)
            else:
                ocr_text = _ocr_with_gemini(file_bytes, "application/pdf", google_api_key, gemini_model_name)
            if ocr_text:
                extracted_text = ocr_text
                ocr_used = True
    elif content_type.startswith("image/"):
        page_count = 1
        if google_api_key:
            extracted_text = _ocr_with_gemini(file_bytes, content_type, google_api_key, gemini_model_name)
            if extracted_text:
                ocr_used = True

    # 2. Try Gemini Multimodal Structured JSON Extraction if API key is present
    if google_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=google_api_key)

            model = genai.GenerativeModel(
                gemini_model_name,
                system_instruction=_STRUCTURED_JSON_SYSTEM_PROMPT,
                generation_config={"response_mime_type": "application/json"},
            )

            # Pass image bytes directly for high-precision vision extraction
            if content_type.startswith("image/"):
                b64 = base64.b64encode(file_bytes).decode("utf-8")
                parts = [
                    {"inline_data": {"mime_type": content_type, "data": b64}},
                    _STRUCTURED_JSON_USER_PROMPT,
                ]
            elif content_type == "application/pdf":
                img_bytes = _pdf_first_page_as_png(file_bytes)
                if img_bytes:
                    b64 = base64.b64encode(img_bytes).decode("utf-8")
                    parts = [
                        {"inline_data": {"mime_type": "image/png", "data": b64}},
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

            response = model.generate_content(parts)
            raw_json = _clean_json_str(response.text or "")
            if raw_json:
                data = json.loads(raw_json)
                doc_type = data.get("document_type") or "other"
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

                return ExtractedDocumentMetadata(
                    document_type=doc_type,
                    document_type_label=DOCUMENT_TYPE_LABELS.get(doc_type, DOCUMENT_TYPE_LABELS["other"]),
                    cin_number=data.get("cin_number"),
                    first_name=first_name,
                    last_name=last_name,
                    full_name=full_name,
                    birth_date=data.get("birth_date"),
                    address=data.get("address"),
                    expiry_date=data.get("expiry_date"),
                    issuing_authority=data.get("issuing_authority"),
                    confidence_score=float(data.get("confidence_score", 0.95)),
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
        except Exception as exc:
            print(f"[WARN] Gemini structured extraction failed, falling back to heuristics: {exc}")

    # 3. Fallback Heuristics
    return _heuristic_structured_extract(
        extracted_text,
        filename,
        lang=lang,
        ocr_used=ocr_used,
        page_count=page_count,
    )
