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
    """Fallback: use the LlamaIndex global LLM (Ollama / OpenAI / Gemini via LI)."""
    prompts = _DOCUMENT_PROMPTS[lang]
    user_query_instruction = ""
    if user_query and user_query.strip():
        if lang == "fr":
            user_query_instruction = f"👉 **Question du citoyen** : \"{user_query.strip()}\"\nRépondez à cette question.\n\n"
        else:
            user_query_instruction = f"👉 **سؤال المواطن** : \"{user_query.strip()}\"\n\n"

    try:
        from llama_index.core import Settings as LISettings  # type: ignore

        llm = LISettings.llm
        if llm is None:
            return ""
        prompt_text = prompts["analyze"].format(
            text=text[:4000],
            user_query_instruction=user_query_instruction,
        )
        full_prompt = prompts["system"] + "\n\n" + prompt_text
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
