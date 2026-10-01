"""Validated conversation snapshots derived only from user turns."""
import re
import unicodedata
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ConversationState(BaseModel):
    session_id: str = Field(min_length=1)
    current_procedure_id: str | None = None
    current_procedure_title: str | None = None
    user_type: str | None = None
    stage: Literal["exploring", "procedure_identified", "collecting_info", "ready"] = "exploring"
    last_user_intent: str | None = None
    mentioned_documents: list[str] = Field(default_factory=list)
    special_case: str | None = None
    language: Literal["fr", "ar", "darija"] = "fr"
    turn_count: int = Field(default=0, ge=0)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def consistent(self):
        if self.stage != "exploring" and not self.current_procedure_id:
            raise ValueError("An identified procedure is required for this stage")
        if bool(self.current_procedure_title) != bool(self.current_procedure_id):
            raise ValueError("Procedure id and title must be set together")
        if self.last_updated.tzinfo is None:
            raise ValueError("last_updated must include a timezone")
        return self


def normalized(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold())
                   if not unicodedata.combining(c)).replace("’", "'")


def advance(state: ConversationState, message: str, language: str) -> ConversationState:
    from app.rag_service import _detect_service_from_query
    from app.services.knowledge_base import load_service_knowledge

    data = state.model_dump()
    text = normalized(message)
    detected = _detect_service_from_query(message)
    if detected is None:
        # The corpus labels retain accents; accept common unaccented input too.
        from app.rag_service import _SERVICE_KEYWORDS
        detected = next((key for key, words in _SERVICE_KEYWORDS.items()
            if any(re.search(r"(?<!\w)" + re.escape(normalized(word)) + r"(?!\w)", text)
                   for word in words)), None)
    # Mentioning a supporting ID is not automatically a switch to the ID procedure.
    possession = bool(re.search(r"\b(j'ai|je possede|j'apporte|avec ma|avec une)\b|عندي|معايا", text))
    if detected == "identity_card" and possession and not re.search(r"renouvel|refaire|demande|تجديد|نجدد", text):
        detected = None
    reset = text.strip(" .!؟?") in {"nouveau sujet", "autre sujet", "recommencer", "موضوع جديد"}
    if reset or (detected and detected != state.current_procedure_id):
        data.update(current_procedure_id=None, current_procedure_title=None,
                    stage="exploring", mentioned_documents=[], special_case=None, last_user_intent=None)
    if detected and not reset:
        kb = load_service_knowledge(detected)
        data.update(current_procedure_id=detected,
                    current_procedure_title=kb.get("service_name_fr", detected))
        if data["stage"] == "exploring":
            data["stage"] = "procedure_identified"
    intent = "other"
    for name, pattern in [
        ("documents", r"documents?|pieces|وثائق|وراق|لوازم"),
        ("timing", r"delai|duree|temps|مدة|وقت"),
        ("fees", r"prix|cout|combien|tarif|frais|ثمن|رسوم|شحال"),
        ("location", r"\bou\b|adresse|فين|اين"),
        ("steps", r"comment|etapes|renouvel|كيف|نجدد"),
    ]:
        if re.search(pattern, text):
            intent = name
            break
    # Capture only explicit self-descriptions; questions about minors are not a profile.
    for user_type, pattern in [
        ("student", r"je suis (?:un[e]? )?etudiant[e]?|انا طالب|انا طالبة"),
        ("minor", r"je suis (?:un[e]? )?mineur[e]?|انا قاصر"),
        ("foreigner", r"je suis (?:un[e]? )?etranger[e]?|انا اجنبي"),
        ("adult", r"je suis majeur[e]?|انا راشد"),
    ]:
        if re.search(pattern, text):
            data["user_type"] = user_type
            intent = "provide_info"
    for name, pattern in [("lost_id", r"j'ai perdu|بطاقتي ضاعت|ضاعت ليا"),
                          ("stolen_id", r"on m'a vole|تسرقات ليا"),
                          ("address_change", r"j'ai demenage|بدلت السكن")]:
        if re.search(pattern, text):
            data["special_case"] = name
            intent = "provide_info"
    for document, pattern in [("identity_card", r"\b(cnie?|cin)\b|بطاقة التعريف|البطاقة الوطنية"),
                              ("birth_certificate", r"acte de naissance|عقد الازدياد"),
                              ("residence_certificate", r"certificat de residence|شهادة السكنى")]:
        if re.search(pattern, text) and document not in data["mentioned_documents"]:
            data["mentioned_documents"].append(document)
    # Mentioned documents are never treated as verified or a complete dossier.
    if data["current_procedure_id"] and intent in {"documents", "provide_info"}:
        data["stage"] = "collecting_info"
    data.update(last_user_intent=intent, language=language if language in {"fr", "ar", "darija"} else "fr",
                turn_count=state.turn_count + 1, last_updated=datetime.now(timezone.utc))
    return ConversationState.model_validate(data)


def load_state(db, user_id: str, session_id: str) -> ConversationState:
    from app.models import ChatMessage
    rows = db.query(ChatMessage).filter(ChatMessage.user_id == user_id,
        ChatMessage.case_id.is_(None), ChatMessage.sender == "user")
    rows = rows.filter(ChatMessage.session_id.is_(None) if session_id == "legacy"
                       else ChatMessage.session_id == session_id)
    rows = rows.order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc()).all()
    state = ConversationState(session_id=session_id)
    # Replay is also the integrity check and migration for legacy/corrupt snapshots.
    for row in rows:
        state = advance(state, row.message, row.language)
        state.last_updated = row.created_at.replace(tzinfo=timezone.utc)
    return ConversationState.model_validate(state.model_dump())
