"""Notification drafts for status changes; no SMS or WhatsApp is sent here."""

from app.services.case_lifecycle import canonical_status

NOTIFICATION_PROMPT = """You write Moroccan public-service case notifications.
Input: tracking code, new case status, optional missing document, and channel (SMS or WhatsApp).
Produce JSON with exactly two fields: fr and darija. Each text must mention the tracking code,
state what happened, and give one concrete next action. Use natural Moroccan Darija in Arabic
script, concise French, no invented dates, fees, approval promises, links, or personal identifiers.
Keep SMS under 160 characters per language. Never claim the message was sent.
"""

_STATUS_TEXT = {
    "SUBMITTED": (
        "Votre demande {code} a été reçue. Suivez son évolution dans OmniAgent.",
        "توصلنا بالطلب ديالك {code}. تابع الحالة ديالو فـ OmniAgent.",
    ),
    "UNDER_REVIEW": (
        "Votre demande {code} est en cours d'examen. Consultez votre dossier.",
        "الطلب ديالك {code} دابا كيتراجع. شوف الملف ديالك.",
    ),
    "DOCS_APPROVED": (
        "Les pièces de votre demande {code} sont validées. Attendez la convocation.",
        "الوثائق ديال الطلب {code} تصادقو. تسنى الاستدعاء.",
    ),
    "READY_FOR_PICKUP": (
        "Votre document {code} est prêt. Présentez votre reçu et votre CIN au guichet.",
        "الوثيقة ديالك {code} واجدة. جيب الوصل ولاكارط ناسيونال للشباك.",
    ),
}


def notification_draft(status: str, code: str, *, missing_document: str | None = None) -> dict[str, str]:
    """Deterministic, reviewable copy suitable for SMS or WhatsApp previews."""
    document = (missing_document or "").strip()[:40]
    if document:
        return {
            "fr": f"Dossier {code} : pièce manquante ({document}). Ajoutez-la dans OmniAgent.",
            "darija": f"الملف {code}: خاص وثيقة ({document}). زيدها فـ OmniAgent.",
        }
    fr, darija = _STATUS_TEXT.get(canonical_status(status), (
        "Consultez la mise à jour de votre dossier {code} dans OmniAgent.",
        "شوف الجديد ديال الملف {code} فـ OmniAgent.",
    ))
    return {"fr": fr.format(code=code), "darija": darija.format(code=code)}
