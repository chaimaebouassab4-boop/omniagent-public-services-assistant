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
import io
from dataclasses import dataclass
from typing import Optional


# ─── Moroccan Document Analysis Prompts (3 languages) ────────────────────────

_DOCUMENT_PROMPTS: dict[str, dict[str, str]] = {
    "darija": {
        "system": (
            "أنت محلل وثائق إداري متخصص في الوثائق الرسمية المغربية. "
            "مهمتك هي تحليل الوثيقة وإعطاء معلومات واضحة ومفيدة للمواطن باللغة الدارجة المغربية."
        ),
        "analyze": (
            "حلل هاد الوثيقة وعطيني:\n"
            "1. **نوع الوثيقة**: شنو هاد الوثيقة بالضبط؟\n"
            "2. **المعلومات المستخرجة**: الاسم، التاريخ، العنوان، رقم البطاقة الوطنية، الرقم الضريبي... إلخ\n"
            "3. **صلاحية الوثيقة**: واش لا تزال صالحة؟ (الوثائق الإدارية خاص ما يتجاوزش 3 أشهر)\n"
            "4. **الخاتم والتوقيع**: واش عندها ختم رسمي وتوقيع؟\n"
            "5. **اللغة**: بأي لغة محررة؟ (العربية / الفرنسية / ثنائية اللغة)\n"
            "6. **الصلاحية للإجراءات الإدارية**: واش تصلح هاد الوثيقة للإجراءات الإدارية المغربية؟ "
            "وشنو ممكن يكون ناقص؟\n\n"
            "جاوب بالدارجة المغربية بطريقة واضحة ومنظمة.\n\n"
            "محتوى الوثيقة:\n{text}"
        ),
        "no_text": (
            "⚠️ **ما قدرتش نقرا الوثيقة بوضوح**\n\n"
            "الوثيقة ديالك وصلت، ولكن ما قدرتش نستخرج النص منها. "
            "ممكن تكون:\n"
            "- الصورة غير واضحة أو ماشي بزاف الضوء\n"
            "- الوثيقة مشفرة أو محمية\n\n"
            "جرب تعاود ترفع صورة أوضح، أو وصف ليا محتوى الوثيقة ونعاونك."
        ),
        "error": (
            "❌ **وقع مشكل في التحليل**\n\n"
            "ما قدرتش نحلل الوثيقة دابا. "
            "تقدر تسولني مباشرة على ما تحتاجو."
        ),
    },
    "fr": {
        "system": (
            "Vous êtes un expert en analyse de documents administratifs marocains. "
            "Votre rôle est d'analyser le document soumis et de fournir une réponse claire et utile au citoyen en français."
        ),
        "analyze": (
            "Analysez ce document et indiquez-moi :\n"
            "1. **Type de document** : De quel document s'agit-il précisément ?\n"
            "2. **Informations extraites** : Nom, date, adresse, numéro CIN, numéro fiscal… etc.\n"
            "3. **Validité du document** : Est-il encore valide ? (Les documents administratifs ne doivent pas dépasser 3 mois)\n"
            "4. **Cachet et signature** : Y a-t-il un cachet officiel et une signature ?\n"
            "5. **Langue** : En quelle(s) langue(s) est-il rédigé ? (Arabe / Français / Bilingue)\n"
            "6. **Conformité administrative** : Ce document est-il valide pour les démarches administratives marocaines ? "
            "Qu'est-ce qui pourrait manquer ?\n\n"
            "Répondez en français de manière claire et structurée.\n\n"
            "Contenu du document :\n{text}"
        ),
        "no_text": (
            "⚠️ **Impossible de lire le document clairement**\n\n"
            "Votre document a bien été reçu, mais le texte n'a pas pu être extrait. "
            "Cela peut être dû à :\n"
            "- Une image floue ou mal éclairée\n"
            "- Un document chiffré ou protégé\n\n"
            "Essayez de renvoyer une image plus nette, ou décrivez-moi le contenu du document."
        ),
        "error": (
            "❌ **Erreur d'analyse**\n\n"
            "L'analyse du document a échoué. "
            "Vous pouvez me poser directement vos questions."
        ),
    },
    "arabic": {
        "system": (
            "أنت محلل وثائق إداري متخصص في الوثائق الرسمية المغربية. "
            "مهمتك تحليل الوثيقة وتقديم معلومات واضحة ومفيدة للمواطن باللغة العربية الفصحى."
        ),
        "analyze": (
            "يرجى تحليل هذه الوثيقة وتزويدي بما يلي:\n"
            "1. **نوع الوثيقة**: ما هذه الوثيقة بالتحديد؟\n"
            "2. **المعلومات المستخرجة**: الاسم، التاريخ، العنوان، رقم بطاقة التعريف الوطنية، الرقم الضريبي...\n"
            "3. **صلاحية الوثيقة**: هل لا تزال سارية المفعول؟ (يجب ألا تتجاوز الوثائق الإدارية 3 أشهر)\n"
            "4. **الختم والتوقيع**: هل تحمل ختماً رسمياً وتوقيعاً؟\n"
            "5. **اللغة**: بأي لغة محررة؟ (العربية / الفرنسية / ثنائية اللغة)\n"
            "6. **الصلاحية للإجراءات الإدارية**: هل تصلح هذه الوثيقة للإجراءات الإدارية المغربية؟ "
            "وما الذي قد يكون مفقوداً؟\n\n"
            "أجب باللغة العربية الفصحى بأسلوب واضح ومنظم.\n\n"
            "محتوى الوثيقة:\n{text}"
        ),
        "no_text": (
            "⚠️ **تعذر قراءة الوثيقة بوضوح**\n\n"
            "تم استلام وثيقتك، غير أنه تعذر استخراج النص منها. "
            "قد يكون ذلك بسبب:\n"
            "- صورة غير واضحة أو سيئة الإضاءة\n"
            "- وثيقة مشفرة أو محمية\n\n"
            "يُرجى إعادة إرسال صورة أوضح، أو وصف محتوى الوثيقة وسأساعدك."
        ),
        "error": (
            "❌ **حدث خطأ في التحليل**\n\n"
            "تعذر تحليل الوثيقة في الوقت الحالي. "
            "يمكنك طرح أسئلتك مباشرةً."
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

@dataclass
class DocumentAnalysis:
    doc_type: str = "unknown"
    extracted_text: str = ""
    page_count: int = 0
    ocr_used: bool = False
    llm_analysis: str = ""
    is_image: bool = False
    error: Optional[str] = None


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
    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=api_key)
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        prompt = (
            "Extract ALL text from this document image exactly as it appears. "
            "Preserve Arabic, French, numbers, dates, and any special characters. "
            "Do NOT translate, summarise, or add commentary — output raw text only."
        )
        m = genai.GenerativeModel(model)
        response = m.generate_content([{"mime_type": mime, "data": encoded}, prompt])
        return (response.text or "").strip()
    except Exception as exc:
        print(f"[WARN] Gemini Vision OCR failed: {exc}")
        return ""


# ─── Step 3: LLM Document Analysis ───────────────────────────────────────────

def _analyze_with_gemini_sdk(text: str, lang: str, api_key: str, model: str) -> str:
    """Use direct Gemini SDK for rich document analysis with system instructions."""
    prompts = _DOCUMENT_PROMPTS[lang]
    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(model, system_instruction=prompts["system"])
        response = m.generate_content(prompts["analyze"].format(text=text[:6000]))
        return (response.text or "").strip()
    except Exception as exc:
        print(f"[WARN] Gemini analysis failed: {exc}")
        return ""


def _analyze_with_llamaindex_llm(text: str, lang: str) -> str:
    """Fallback: use the LlamaIndex global LLM (Ollama / OpenAI / Gemini via LI)."""
    prompts = _DOCUMENT_PROMPTS[lang]
    try:
        from llama_index.core import Settings as LISettings  # type: ignore

        llm = LISettings.llm
        if llm is None:
            return ""
        full_prompt = prompts["system"] + "\n\n" + prompts["analyze"].format(text=text[:4000])
        response = llm.complete(full_prompt)
        return (str(response) or "").strip()
    except Exception as exc:
        print(f"[WARN] LlamaIndex LLM analysis failed: {exc}")
        return ""


# ─── Public Entry Point ───────────────────────────────────────────────────────

def analyze_document(
    file_bytes: bytes,
    content_type: str,
    filename: str,
    language: str = "darija",
    google_api_key: str = "",
    gemini_model_name: str = "gemini-1.5-flash",
) -> DocumentAnalysis:
    """Run the full OCR → LLM analysis pipeline on an uploaded document.

    Args:
        file_bytes:        Raw bytes of the uploaded file.
        content_type:      MIME type (application/pdf, image/jpeg, image/png, image/webp).
        filename:          Original filename (for logging / display).
        language:          Chat language key ('darija', 'fr', 'arabic').
        google_api_key:    Google Gemini API key; if empty, Vision OCR is skipped.
        gemini_model_name: Gemini model to use for both OCR and analysis.

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
            result.llm_analysis = _analyze_with_gemini_sdk(extracted_text, lang, google_api_key, gemini_model_name)
        if not result.llm_analysis:
            result.llm_analysis = _analyze_with_llamaindex_llm(extracted_text, lang)

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

    if analysis.error:
        return prompts["error"]

    if not analysis.llm_analysis:
        return prompts["no_text"]

    # OCR badge
    ocr_badge = ""
    if analysis.ocr_used:
        ocr_badge_map = {
            "fr": "🔬 *Reconnaissance optique de caractères (OCR) utilisée*\n\n",
            "arabic": "🔬 *تم استخدام تقنية التعرف الضوئي على الحروف (OCR)*\n\n",
            "darija": "🔬 *خدمنا تقنية OCR باش نقراو الصورة*\n\n",
        }
        ocr_badge = ocr_badge_map.get(lang, "")

    # Header
    page_info = f"PDF · {analysis.page_count} صفحة" if not analysis.is_image else "صورة"
    if lang == "fr":
        page_info = f"PDF · {analysis.page_count} page(s)" if not analysis.is_image else "Image"
        header = f"📄 **Analyse — {filename}** *({page_info})*\n\n"
    elif lang == "arabic":
        header = f"📄 **تحليل الوثيقة — {filename}** *({page_info})*\n\n"
    else:
        header = f"📄 **تحليل الوثيقة — {filename}** *({page_info})*\n\n"

    # Footer call-to-action
    footer_map = {
        "fr": (
            "\n\n---\n"
            "💬 *Des questions sur ce document ou sur une démarche administrative marocaine ? "
            "Je suis là pour vous aider !*"
        ),
        "arabic": (
            "\n\n---\n"
            "💬 *هل لديك أسئلة أخرى حول هذه الوثيقة أو حول إجراء إداري؟ أنا هنا لمساعدتك!*"
        ),
        "darija": (
            "\n\n---\n"
            "💬 *عندك أسئلة أخرى على هاد الوثيقة أو على إجراء إداري؟ سول بلا حشوما، أنا هنا!*"
        ),
    }
    footer = footer_map.get(lang, "")

    return header + ocr_badge + analysis.llm_analysis + footer
