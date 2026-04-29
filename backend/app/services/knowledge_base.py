import json
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
KB_ROOT = PROJECT_ROOT / "tests" / "knowledge_base"

SERVICE_KB_PATHS = {
    "birth_certificate": KB_ROOT / "birth" / "birth_certificate.json",
    "residence_certificate": KB_ROOT / "residence" / "residence_certificate.json",
    "marriage_contract": KB_ROOT / "common" / "faq.json"
}

COMMON_KB_PATH = KB_ROOT / "common" / "faq.json"

SERVICE_ALIASES = {
    "birth": "birth_certificate",
    "naissance": "birth_certificate",
    "residence": "residence_certificate",
    "certificat_residence": "residence_certificate",
    "marriage": "marriage_contract",
    "mariage": "marriage_contract"
}


def normalize_service_id(service_id: str | None) -> str | None:
    """Normalizes route aliases to canonical service ids."""
    if not service_id:
        return None
    lower = service_id.strip().lower()
    return SERVICE_ALIASES.get(lower, lower)


@lru_cache(maxsize=8)
def load_service_knowledge(service_id: str) -> dict[str, Any]:
    """Loads JSON knowledge for one service."""
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
    """Loads shared FAQ fallback knowledge."""
    if not COMMON_KB_PATH.exists():
        return {}
    try:
        with COMMON_KB_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _score_match(query: str, question: str) -> int:
    query_tokens = {token for token in query.lower().split() if len(token) > 1}
    question_tokens = {token for token in question.lower().split() if len(token) > 1}
    return len(query_tokens.intersection(question_tokens))


def answer_from_knowledge(service_id: str, user_message: str) -> str:
    """Returns best answer from FAQ, then summary fallback."""
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

    required = knowledge.get("required_documents")
    if isinstance(required, dict):
        common_docs = required.get("common_to_all", [])
        if common_docs:
            docs_preview = "\n".join(f"- {doc}" for doc in common_docs[:4])
            return f"Hadi awel watha2iq lli khassek غالبا:\n{docs_preview}"
    if isinstance(required, list) and required:
        docs_preview = "\n".join(f"- {doc}" for doc in required[:4])
        return f"Hadi awel watha2iq lli khassek غالبا:\n{docs_preview}"

    description = knowledge.get("description_ar") or knowledge.get("description") or ""
    if description:
        return str(description)
    return "Twasalna b su2alek. Ghadi n3tiwk jawab mofdhal mlli tkoun ma3loumat akthar."
