import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
KB_ROOT = PROJECT_ROOT / "tests" / "knowledge_base"

SERVICE_KB_PATHS = {
    "birth_certificate": KB_ROOT / "birth" / "birth_certificate.json",
    "residence_certificate": KB_ROOT / "residence" / "residence_certificate.json",
    "marriage_contract": KB_ROOT / "marriage" / "marriage_certificate.json",
}

COMMON_KB_PATH = KB_ROOT / "common" / "faq.json"

SERVICE_ALIASES = {
    "birth": "birth_certificate",
    "birth_certificate": "birth_certificate",
    "naissance": "birth_certificate",
    "residence": "residence_certificate",
    "residence_certificate": "residence_certificate",
    "certificat_residence": "residence_certificate",
    "marriage": "marriage_contract",
    "marriage_certificate": "marriage_contract",
    "marriage_contract": "marriage_contract",
    "mariage": "marriage_contract",
}


def normalize_service_id(service_id: str | None) -> str | None:
    """Normalize route aliases to canonical service ids."""
    if not service_id:
        return None
    lower = service_id.strip().lower()
    return SERVICE_ALIASES.get(lower, lower)


@lru_cache(maxsize=8)
def load_service_knowledge(service_id: str) -> dict[str, Any]:
    """Load JSON knowledge for one service."""
    canonical = normalize_service_id(service_id)
    if not canonical:
        return {}
    path = SERVICE_KB_PATHS.get(canonical)
    if not path or not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


@lru_cache(maxsize=2)
def load_common_knowledge() -> dict[str, Any]:
    """Load shared FAQ fallback knowledge when available."""
    if not COMMON_KB_PATH.exists():
        return {}
    try:
        with COMMON_KB_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _tokenize(text: str) -> set[str]:
    """Extract lowercase word tokens while ignoring punctuation and quotes."""
    return {
        token
        for token in re.findall(r"\w+", text.lower(), flags=re.UNICODE)
        if len(token) > 1
    }


def _score_match(query: str, question: str) -> int:
    return len(_tokenize(query).intersection(_tokenize(question)))


def _answer_marriage_fallback(user_message: str, knowledge: dict[str, Any]) -> str | None:
    """Handle common marriage questions even when FAQ text quality is poor."""
    lowered_message = user_message.lower()

    if "سن" in user_message or "age" in lowered_message:
        return "Ssen l9anouni lizzwaj f lmaghrib howa 18 3am ljouj. Ila kan chi wa7ed asghar, kaykhas idn istithna2i mn qadi l2osra."

    if any(term in user_message for term in ["رسوم", "ثمن"]) or any(
        term in lowered_message for term in ["prix", "fee", "fees", "cost"]
    ):
        return "Rsom 3a9d zwaj kaykouno ghaliban bin 200 w 500 dirham, 7asab l3doul w tomboilat w masarif idariya. F بعض l7alat momkin ytl3 aktar."

    if "online" in lowered_message or "أونلاين" in user_message or "اونلاين" in user_message:
        return "La, 3a9d zwaj ma kaytddarsh kamel online. Lmassar kaykoun 7odori 3بر l3doul w qadi l2osra."

    if any(term in user_message for term in ["وثائق", "الوثائق", "مدارك", "watha2iq", "documents"]):
        required = knowledge.get("required_documents")
        if isinstance(required, dict):
            docs = required.get("common_to_both", [])
            if docs:
                docs_preview = "\n".join(f"- {doc}" for doc in docs[:4])
                return f"Hadi awel watha2iq lli khassek ghaliban:\n{docs_preview}"

    return None


def answer_from_knowledge(service_id: str, user_message: str) -> str:
    """Return best answer from FAQ, then structured fallbacks."""
    canonical_service_id = normalize_service_id(service_id)
    knowledge = load_service_knowledge(service_id)
    if not knowledge:
        knowledge = load_common_knowledge()
    if not knowledge:
        return "Ma lqit-sh ma3loumat kfaya daba. 3tini details akthar bach n3awnek."

    faq_entries = knowledge.get("faq", [])
    best_entry: dict[str, Any] | None = None
    best_score = 0
    for entry in faq_entries:
        question = str(entry.get("question", ""))
        score = _score_match(user_message, question)
        if score > best_score:
            best_score = score
            best_entry = entry

    if best_entry and best_score > 0:
        answer = str(best_entry.get("answer", "")).strip()
        if answer:
            return answer

    if canonical_service_id == "marriage_contract":
        marriage_fallback = _answer_marriage_fallback(user_message, knowledge)
        if marriage_fallback:
            return marriage_fallback

    lowered_message = user_message.lower()
    fees = knowledge.get("fees")
    if isinstance(fees, str) and any(
        term in lowered_message for term in ["رسوم", "ثمن", "prix", "fee", "fees", "cost"]
    ):
        return fees

    required = knowledge.get("required_documents")
    if isinstance(required, dict):
        for key in ("common_to_both", "common_to_all"):
            docs = required.get(key, [])
            if docs:
                docs_preview = "\n".join(f"- {doc}" for doc in docs[:4])
                return f"Hadi awel watha2iq lli khassek ghaliban:\n{docs_preview}"
    if isinstance(required, list) and required:
        docs_preview = "\n".join(f"- {doc}" for doc in required[:4])
        return f"Hadi awel watha2iq lli khassek ghaliban:\n{docs_preview}"

    description = knowledge.get("description_ar") or knowledge.get("description") or ""
    if description:
        return str(description)
    return "Twasalna b su2alek. Ghadi n3tiwk jawab mofdhal mlli tkoun ma3loumat akthar."
