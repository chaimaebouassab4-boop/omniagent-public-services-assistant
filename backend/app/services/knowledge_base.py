import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
KB_ROOT = PROJECT_ROOT / "tests" / "knowledge_base"

# Canonical service id -> knowledge base folder name.
SERVICE_DIRS = {
    "residence_certificate": "residence",
    "birth_certificate": "birth",
    "marriage_contract": "marriage",
    "death_certificate": "death",
    "life_certificate": "life",
    "single_status_certificate": "single_status",
    "non_property_certificate": "non_property",
    "administrative_certificate": "administrative",
    "good_conduct_certificate": "good_conduct",
    "criminal_record": "criminal_record",
}

COMMON_KB_PATH = KB_ROOT / "common" / "faq.json"

SERVICE_ALIASES = {
    "birth": "birth_certificate",
    "naissance": "birth_certificate",
    "residence": "residence_certificate",
    "certificat_residence": "residence_certificate",
    "marriage": "marriage_contract",
    "marriage_certificate": "marriage_contract",
    "mariage": "marriage_contract",
    "death": "death_certificate",
    "deces": "death_certificate",
    "life": "life_certificate",
    "vie": "life_certificate",
    "single_status": "single_status_certificate",
    "celibat": "single_status_certificate",
    "non_property": "non_property_certificate",
    "administrative": "administrative_certificate",
    "good_conduct": "good_conduct_certificate",
    "bonne_conduite": "good_conduct_certificate",
    "criminal_record": "criminal_record",
    "casier_judiciaire": "criminal_record",
}
# Canonical ids map to themselves.
SERVICE_ALIASES.update({service_id: service_id for service_id in SERVICE_DIRS})

# FAQ matches below this confidence trigger the clarification fallback.
LOW_CONFIDENCE_THRESHOLD = 0.30

FALLBACK_ANSWER = "Ma lqit-sh ma3loumat kfaya daba. 3tini details akthar bach n3awnek."


@dataclass
class KnowledgeAnswer:
    """Structured chat answer with retrieval metadata."""

    answer: str
    confidence: float
    sources: list[str] = field(default_factory=list)
    matched_question: str | None = None


def normalize_service_id(service_id: str | None) -> str | None:
    """Normalize route aliases to canonical service ids."""
    if not service_id:
        return None
    lower = service_id.strip().lower()
    return SERVICE_ALIASES.get(lower, lower)


def _service_kb_path(canonical_id: str) -> Path | None:
    """Locate the knowledge JSON file for a canonical service id."""
    folder = SERVICE_DIRS.get(canonical_id)
    if not folder:
        return None
    service_dir = KB_ROOT / folder
    if not service_dir.is_dir():
        return None
    for path in sorted(service_dir.glob("*.json")):
        if "test_cases" not in path.name:
            return path
    return None


@lru_cache(maxsize=16)
def load_service_knowledge(service_id: str) -> dict[str, Any]:
    """Load JSON knowledge for one service."""
    canonical = normalize_service_id(service_id)
    if not canonical:
        return {}
    path = _service_kb_path(canonical)
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


def _source_label(service_id: str | None) -> list[str]:
    canonical = normalize_service_id(service_id)
    if not canonical:
        return []
    path = _service_kb_path(canonical)
    if path is None:
        return []
    return [str(path.relative_to(KB_ROOT)).replace("\\", "/")]


def _tokenize(text: str) -> set[str]:
    """Extract lowercase word tokens while ignoring punctuation and quotes."""
    return {
        token
        for token in re.findall(r"\w+", text.lower(), flags=re.UNICODE)
        if len(token) > 1
    }


def _score_match(query_tokens: set[str], question: str) -> tuple[int, float]:
    """Return raw overlap count and overlap coefficient against a FAQ question."""
    question_tokens = _tokenize(question)
    if not query_tokens or not question_tokens:
        return 0, 0.0
    overlap = len(query_tokens.intersection(question_tokens))
    coefficient = overlap / min(len(query_tokens), len(question_tokens))
    return overlap, coefficient


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


def _structured_fallback(user_message: str, knowledge: dict[str, Any]) -> str | None:
    """Answer from structured KB fields (fees, documents, description)."""
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
    return None


def answer_with_metadata(service_id: str, user_message: str, use_rag: bool = True) -> KnowledgeAnswer:
    """Return the best KB answer with confidence score and source files."""
    canonical_service_id = normalize_service_id(service_id)

    # Try querying the RAG pipeline first if available
    if use_rag:
        try:
            from app.rag_service import get_rag_engine
            engine = get_rag_engine()
            if engine.initialized:
                rag_res = engine.query(user_query=user_message, service_type=canonical_service_id)
                if rag_res.get("confidence", 0.0) >= LOW_CONFIDENCE_THRESHOLD and not rag_res.get("fallback_reason"):
                    return KnowledgeAnswer(
                        answer=rag_res.get("answer", ""),
                        confidence=rag_res.get("confidence", 0.85),
                        sources=rag_res.get("sources", []),
                        matched_question=None
                    )
        except Exception as e:
            pass

    sources = _source_label(canonical_service_id)
    knowledge = load_service_knowledge(service_id)
    if not knowledge:
        knowledge = load_common_knowledge()
        sources = ["common/faq.json"] if knowledge else []
    if not knowledge:
        return KnowledgeAnswer(answer=FALLBACK_ANSWER, confidence=0.0)

    query_tokens = _tokenize(user_message)
    best_entry: dict[str, Any] | None = None
    best_overlap = 0
    best_coefficient = 0.0
    for entry in knowledge.get("faq", []):
        question = str(entry.get("question", ""))
        overlap, coefficient = _score_match(query_tokens, question)
        if (overlap, coefficient) > (best_overlap, best_coefficient):
            best_overlap = overlap
            best_coefficient = coefficient
            best_entry = entry

    if best_entry and best_overlap > 0:
        answer = str(best_entry.get("answer", "")).strip()
        confidence = round(min(0.95, 0.30 + 0.65 * best_coefficient), 2)
        if answer and confidence >= LOW_CONFIDENCE_THRESHOLD and best_overlap >= 2:
            return KnowledgeAnswer(
                answer=answer,
                confidence=confidence,
                sources=sources,
                matched_question=str(best_entry.get("question", ""))
            )

    if canonical_service_id == "marriage_contract":
        marriage_fallback = _answer_marriage_fallback(user_message, knowledge)
        if marriage_fallback:
            return KnowledgeAnswer(answer=marriage_fallback, confidence=0.60, sources=sources)

    structured = _structured_fallback(user_message, knowledge)
    if structured:
        return KnowledgeAnswer(answer=structured, confidence=0.50, sources=sources)

    return KnowledgeAnswer(
        answer="Twasalna b su2alek. Ghadi n3tiwk jawab mofdhal mlli tkoun ma3loumat akthar.",
        confidence=0.20,
        sources=sources
    )


def answer_from_knowledge(service_id: str, user_message: str) -> str:
    """Backward-compatible helper returning only the answer text."""
    return answer_with_metadata(service_id, user_message).answer
