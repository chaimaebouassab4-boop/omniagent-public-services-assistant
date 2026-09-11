"""Compatibility API matching the omniagent frontend's generated client.

The generated client (orval) expects raw (un-enveloped) JSON payloads with
camelCase fields and numeric ids. This router serves that exact contract on the
`/api/*` paths the frontend calls, backed by the existing SQLAlchemy models and
the knowledge-base answer engine.
"""
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.db.database import get_db
from app.models import AuditLog, Case, ChatMessage, Document, Service, User, VisitEvent
from app.services.knowledge_base import answer_with_metadata, normalize_service_id

router = APIRouter(prefix="/api", tags=["omni"])

# Canonical service ids in a fixed order → numeric id = index + 1.
SERVICE_ORDER = [
    "residence_certificate",
    "birth_certificate",
    "marriage_contract",
    "death_certificate",
    "life_certificate",
    "single_status_certificate",
    "non_property_certificate",
    "administrative_certificate",
    "good_conduct_certificate",
    "criminal_record",
]

SERVICE_CATEGORY = {
    "residence_certificate": "civil_status",
    "birth_certificate": "civil_status",
    "marriage_contract": "family",
    "death_certificate": "civil_status",
    "life_certificate": "civil_status",
    "single_status_certificate": "family",
    "non_property_certificate": "property",
    "administrative_certificate": "administrative",
    "good_conduct_certificate": "justice",
    "criminal_record": "justice",
}

_STRING_TO_NUM = {sid: idx + 1 for idx, sid in enumerate(SERVICE_ORDER)}
_NUM_TO_STRING = {idx + 1: sid for idx, sid in enumerate(SERVICE_ORDER)}

MESSAGE_LANGUAGES = {"ar", "fr", "darija"}

# Upload constraints for citizen documents.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_UPLOAD_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}


# --------------------------------------------------------------------------- #
# Request bodies
# --------------------------------------------------------------------------- #
class CreateCaseBody(BaseModel):
    serviceId: int
    applicantName: str
    applicantEmail: str
    applicantPhone: str | None = None
    notes: str | None = None


class UpdateCaseBody(BaseModel):
    status: str | None = None
    notes: str | None = None


class SendMessageBody(BaseModel):
    content: str
    language: str = "darija"
    sessionId: str | None = None


class VisitEventBody(BaseModel):
    sessionId: str = Field(min_length=1, max_length=100)
    page: str = Field(min_length=1, max_length=200)
    pageLabel: str = Field(min_length=1, max_length=100)
    language: str = Field(default="fr", max_length=20)
    device: str = Field(default="Desktop", max_length=30)


# --------------------------------------------------------------------------- #
# Serializers (camelCase, numeric ids, raw payloads)
# --------------------------------------------------------------------------- #
def service_num_id(service_id: str) -> int:
    return _STRING_TO_NUM.get(service_id, 0)


def serialize_service(service: Service) -> dict:
    return {
        "id": service_num_id(service.id),
        "nameAr": service.name_ar,
        "nameFr": service.name_fr,
        "descriptionAr": service.description_ar,
        "descriptionFr": service.description_fr,
        "icon": service.icon,
        "category": SERVICE_CATEGORY.get(service.id, "general"),
        "processingDays": service.avg_processing_days,
        "requiredDocuments": service.required_documents or [],
        "isActive": True,
        "createdAt": datetime.utcnow().isoformat(),
    }


def serialize_case(case: Case, include_service: bool = True) -> dict:
    estimated = None
    if case.service is not None:
        estimated = (
            case.created_at + timedelta(days=case.service.avg_processing_days)
        ).isoformat()
    payload = {
        "id": case.public_id,
        "referenceNumber": case.reference_number or f"OMN-{case.public_id:05d}",
        "serviceId": service_num_id(case.service_id),
        "applicantName": case.applicant_name or "",
        "applicantEmail": case.applicant_email or "",
        "applicantPhone": case.applicant_phone,
        "status": case.status,
        "notes": case.notes,
        "submittedAt": case.created_at.isoformat(),
        "updatedAt": case.updated_at.isoformat(),
        "estimatedCompletionDate": estimated,
    }
    if include_service and case.service is not None:
        payload["service"] = serialize_service(case.service)
    return payload


def serialize_message(message: ChatMessage, index: int) -> dict:
    role = "user" if message.sender == "user" else "assistant"
    language = message.language if message.language in MESSAGE_LANGUAGES else "darija"
    return {
        "id": index,
        "caseId": message.case.public_id if message.case is not None else None,
        "role": role,
        "content": message.message,
        "language": language,
        "createdAt": message.created_at.isoformat(),
    }


def serialize_document(document: Document, index: int, case_public_id: int) -> dict:
    status_map = {"pending": "pending", "verified": "verified", "rejected": "rejected"}
    return {
        "id": index,
        "caseId": case_public_id,
        "name": document.file_name,
        "fileType": document.mime_type,
        "fileSize": document.file_size,
        "status": status_map.get(document.validation_status, "pending"),
        "uploadedAt": document.uploaded_at.isoformat(),
    }


TIMELINE_LABELS = {
    "created": ("تم إنشاء الطلب", "Demande créée"),
    "uploaded": ("تم رفع وثيقة", "Document téléversé"),
    "chat_message": ("رسالة في المحادثة", "Message de discussion"),
    "status_changed": ("تغيّرت حالة الطلب", "Statut mis à jour"),
    "approved": ("تمت الموافقة على الطلب", "Demande approuvée"),
    "rejected": ("تم رفض الطلب", "Demande rejetée"),
}


def serialize_timeline_event(log: AuditLog, case_public_id: int, index: int) -> dict:
    ar, fr = TIMELINE_LABELS.get(log.action, (log.action, log.action))
    return {
        "id": index,
        "caseId": case_public_id,
        "event": log.action,
        "descriptionAr": ar,
        "descriptionFr": fr,
        "status": (log.details or {}).get("status"),
        "occurredAt": log.created_at.isoformat(),
    }


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def get_case_or_404(db: Session, public_id: int) -> Case:
    case = db.query(Case).filter(Case.public_id == public_id).first()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


def next_public_id(db: Session) -> int:
    return (db.query(func.max(Case.public_id)).scalar() or 0) + 1


def log_action(db: Session, case_id: str, action: str, actor_id: str | None, details: dict) -> None:
    db.add(AuditLog(case_id=case_id, action=action, actor_id=actor_id, details=details))


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #
@router.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


# --------------------------------------------------------------------------- #
# Services
# --------------------------------------------------------------------------- #
@router.get("/services")
async def list_services(db: Session = Depends(get_db)) -> list[dict]:
    services = db.query(Service).all()
    ordered = sorted(services, key=lambda s: _STRING_TO_NUM.get(s.id, 999))
    return [serialize_service(s) for s in ordered]


@router.get("/services/{service_id}")
async def get_service(service_id: int, db: Session = Depends(get_db)) -> dict:
    string_id = _NUM_TO_STRING.get(service_id)
    service = db.query(Service).filter(Service.id == string_id).first() if string_id else None
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return serialize_service(service)


# --------------------------------------------------------------------------- #
# Cases
# --------------------------------------------------------------------------- #
@router.get("/cases")
async def list_cases(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    query = db.query(Case).filter(Case.user_id == current_user.id)
    if status_filter:
        query = query.filter(Case.status == status_filter)
    cases = query.order_by(Case.created_at.desc()).all()
    return [serialize_case(c) for c in cases]


@router.post("/cases", status_code=status.HTTP_201_CREATED)
async def create_case(
    body: CreateCaseBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    string_id = _NUM_TO_STRING.get(body.serviceId)
    service = db.query(Service).filter(Service.id == string_id).first() if string_id else None
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    public_id = next_public_id(db)
    case = Case(
        public_id=public_id,
        reference_number=f"OMN-{public_id:05d}",
        user_id=current_user.id,
        service_id=service.id,
        applicant_name=body.applicantName,
        applicant_email=body.applicantEmail,
        applicant_phone=body.applicantPhone,
        notes=body.notes,
        status="submitted",
    )
    db.add(case)
    db.flush()
    log_action(db, case.id, "created", current_user.id, {"service_id": service.id})
    db.commit()
    db.refresh(case)
    return serialize_case(case)


@router.get("/cases/{case_id}")
async def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return serialize_case(get_case_or_404(db, case_id))


@router.patch("/cases/{case_id}")
async def update_case(
    case_id: int,
    body: UpdateCaseBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    case = get_case_or_404(db, case_id)
    if body.status is not None and body.status != case.status:
        case.status = body.status
        log_action(db, case.id, "status_changed", current_user.id, {"status": body.status})
    if body.notes is not None:
        case.notes = body.notes
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(case)
    return serialize_case(case)


@router.get("/cases/{case_id}/timeline")
async def get_case_timeline(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    case = get_case_or_404(db, case_id)
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.case_id == case.id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )
    return [serialize_timeline_event(log, case.public_id, i + 1) for i, log in enumerate(logs)]


@router.get("/cases/{case_id}/documents")
async def list_case_documents(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    case = get_case_or_404(db, case_id)
    docs = (
        db.query(Document)
        .filter(Document.case_id == case.id)
        .order_by(Document.uploaded_at.asc())
        .all()
    )
    return [serialize_document(d, i + 1, case.public_id) for i, d in enumerate(docs)]


def _sanitize_filename(raw_name: str | None) -> str:
    """Keep only the basename with safe characters; never trust client paths."""
    base = Path(raw_name or "document").name
    cleaned = re.sub(r"[^\w.\- ]", "_", base).strip() or "document"
    return cleaned[:120]


@router.post("/cases/{case_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_case_document(
    case_id: int,
    file: UploadFile = File(...),
    docType: str = Form(default="other"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Upload one citizen document for a case (PDF or image, max 10 MB)."""
    case = get_case_or_404(db, case_id)

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_UPLOAD_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF, JPEG, PNG or WebP files are accepted",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 10 MB limit",
        )
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    safe_name = _sanitize_filename(file.filename)
    upload_dir = Path(settings.upload_root) / case.id
    upload_dir.mkdir(parents=True, exist_ok=True)
    # Unique on-disk name to avoid collisions; original name kept in DB.
    stored_path = upload_dir / f"{uuid.uuid4().hex}_{safe_name}"
    stored_path.write_bytes(file_bytes)

    document = Document(
        case_id=case.id,
        doc_type=docType.strip()[:64] or "other",
        file_name=safe_name,
        file_path=str(stored_path),
        file_size=len(file_bytes),
        mime_type=content_type,
        validation_status="pending",
    )
    db.add(document)
    log_action(
        db,
        case.id,
        "uploaded",
        current_user.id,
        {"doc_type": document.doc_type, "file_name": safe_name},
    )
    db.commit()
    db.refresh(document)

    count = db.query(Document).filter(Document.case_id == case.id).count()
    return serialize_document(document, count, case.public_id)


@router.get("/cases/{case_id}/documents/{doc_id}/view")
async def view_case_document(
    case_id: int,
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Serve uploaded case document for inline preview or download (for citizen & admin)."""
    case = get_case_or_404(db, case_id)
    if not current_user.is_admin and case.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    doc = (
        db.query(Document)
        .filter(Document.case_id == case.id, (Document.id == doc_id) | (Document.file_name == doc_id))
        .first()
    )

    if not doc and doc_id.isdigit():
        docs = db.query(Document).filter(Document.case_id == case.id).order_by(Document.uploaded_at.asc()).all()
        idx = int(doc_id) - 1
        if 0 <= idx < len(docs):
            doc = docs[idx]

    if not doc or not Path(doc.file_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found")

    return FileResponse(
        path=doc.file_path,
        media_type=doc.mime_type or "application/octet-stream",
        filename=doc.file_name,
        headers={"Content-Disposition": f'inline; filename="{doc.file_name}"'},
    )


@router.delete("/cases/{case_id}/documents/{doc_id}")
async def delete_case_document(
    case_id: int,
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete an uploaded case document (by citizen owner or admin)."""
    case = get_case_or_404(db, case_id)
    if not current_user.is_admin and case.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    doc = (
        db.query(Document)
        .filter(Document.case_id == case.id, (Document.id == doc_id) | (Document.file_name == doc_id))
        .first()
    )

    if not doc and doc_id.isdigit():
        docs = db.query(Document).filter(Document.case_id == case.id).order_by(Document.uploaded_at.asc()).all()
        idx = int(doc_id) - 1
        if 0 <= idx < len(docs):
            doc = docs[idx]

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    file_path = Path(doc.file_path) if doc.file_path else None
    if file_path and file_path.exists():
        file_path.unlink(missing_ok=True)

    db.delete(doc)
    log_action(
        db,
        case.id,
        "document_deleted",
        current_user.id,
        {"file_name": doc.file_name},
    )
    db.commit()
    return {"status": "success", "message": "Document deleted successfully"}


@router.get("/cases/{case_id}/messages")
async def list_case_messages(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    case = get_case_or_404(db, case_id)
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.case_id == case.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [serialize_message(m, i + 1) for i, m in enumerate(messages)]


@router.post("/cases/{case_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_case_message(
    case_id: int,
    body: SendMessageBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    case = get_case_or_404(db, case_id)
    language = body.language if body.language in MESSAGE_LANGUAGES else "darija"

    conversation_history = _recent_chat_history(
        db.query(ChatMessage)
        .filter(ChatMessage.case_id == case.id)
        .filter(ChatMessage.sender.in_(("user", "assistant")))
    )

    user_msg = ChatMessage(case_id=case.id, sender="user", message=body.content, language=language)
    db.add(user_msg)

    answer = answer_with_metadata(
        service_id=case.service_id,
        user_message=body.content,
        conversation_history=conversation_history,
    )
    assistant_msg = ChatMessage(
        case_id=case.id, sender="assistant", message=answer.answer, language=language
    )
    db.add(assistant_msg)
    log_action(db, case.id, "chat_message", current_user.id, {"language": language})
    db.commit()
    db.refresh(assistant_msg)

    count = db.query(ChatMessage).filter(ChatMessage.case_id == case.id).count()
    return serialize_message(assistant_msg, count)


# --------------------------------------------------------------------------- #
# Standalone chat (not tied to a case)
# --------------------------------------------------------------------------- #
def _recent_chat_history(query, max_exchanges: int = 5) -> list[dict[str, str]]:
    """Return the last complete conversation window in chronological order."""
    rows = query.order_by(ChatMessage.created_at.desc()).limit(max_exchanges * 2).all()
    return [
        {"role": row.sender, "content": row.message}
        for row in reversed(rows)
    ]


def detect_service_id(message: str) -> str | None:
    """Best-effort service detection using the unified 50+ keyword dictionary."""
    try:
        from app.rag_service import _detect_service_from_query
        detected = _detect_service_from_query(message)
        if detected:
            return detected
    except Exception:
        pass
    lowered = message.lower()
    keyword_map = {
        # ----- civil status -----
        "residence_certificate": [
            "سكن", "سكنى", "شهادة السكنى", "résidence", "residence",
        ],
        "birth_certificate": [
            "ازدياد", "عقد الازدياد", "رسم الولادة", "ولادة",
            "naissance", "birth",
        ],
        "death_certificate": [
            "وفاة", "رسم الوفاة", "شهادة الوفاة",
            "décès", "deces", "death",
        ],
        "life_certificate": [
            "شهادة الحياة", "حياة", "certificat de vie", "vie", "life",
        ],
        # ----- family -----
        "marriage_contract": [
            "زواج", "عقد الزواج", "تعدد الزوجات", "الزوجة", "الزوج",
            "الخطوبة", "خطيب", "mariage", "marriage",
        ],
        "single_status_certificate": [
            "عزوبة", "شهادة العزوبة", "عازب", "célibat", "celibat", "single",
        ],
        # ----- property / admin -----
        "non_property_certificate": [
            "ملكية", "عدم الملكية", "شهادة عدم الملكية",
            "propriété", "propriete", "property",
        ],
        "administrative_certificate": [
            "شهادة إدارية", "الشهادة الإدارية", "إدارية", "administrative",
        ],
        # ----- justice -----
        "good_conduct_certificate": [
            "حسن السيرة", "شهادة حسن السيرة", "bonne conduite", "conduite", "conduct",
        ],
        "criminal_record": [
            "السجل العدلي", "سجل عدلي", "الكازي", "casier judiciaire", "casier", "criminal",
        ],
        # ----- identity / misc (no dedicated KB folder yet) -----
        "residence_certificate": [
            "بطاقة التعريف", "cnie", "cin", "carte nationale",
            "رخصة القيادة", "جواز السفر",
        ],
    }
    for service_id, keywords in keyword_map.items():
        if any(kw in message or kw in lowered for kw in keywords):
            return service_id
    # No keyword matched → return None so the caller does a global search
    return None


@router.get("/chat/messages")
async def list_chat_messages(
    sessionId: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    query = (
        db.query(ChatMessage)
        .filter(ChatMessage.case_id.is_(None))
        .filter(ChatMessage.user_id == current_user.id)
        .filter(ChatMessage.sender != "document_context")
    )
    if sessionId == "legacy":
        query = query.filter(ChatMessage.session_id.is_(None))
    elif sessionId:
        query = query.filter(ChatMessage.session_id == sessionId)
    messages = query.order_by(ChatMessage.created_at.asc()).all()
    return [serialize_message(m, i + 1) for i, m in enumerate(messages)]


@router.get("/chat/sessions")
async def list_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """List the user's conversations, newest first, without exposing other users' data."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.case_id.is_(None))
        .filter(ChatMessage.user_id == current_user.id)
        .filter(ChatMessage.sender != "document_context")
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    grouped: dict[str, list[ChatMessage]] = {}
    for message in messages:
        grouped.setdefault(message.session_id or "legacy", []).append(message)

    sessions = []
    for session_id, rows in grouped.items():
        first_user = next((row for row in rows if row.sender == "user"), rows[0])
        title = first_user.message.removeprefix("[Document] ").strip()
        sessions.append(
            {
                "id": session_id,
                "title": title[:70] or "Conversation",
                "preview": rows[-1].message[:100],
                "messageCount": len(rows),
                "createdAt": rows[0].created_at.isoformat(),
                "updatedAt": rows[-1].created_at.isoformat(),
            }
        )
    return sorted(sessions, key=lambda item: item["updatedAt"], reverse=True)


def _standalone_count(db: Session, user_id: str, session_id: str | None = None) -> int:
    query = (
        db.query(ChatMessage)
        .filter(ChatMessage.case_id.is_(None))
        .filter(ChatMessage.user_id == user_id)
        .filter(ChatMessage.sender != "document_context")
    )
    if session_id:
        query = query.filter(ChatMessage.session_id == session_id)
    return query.count()


@router.delete("/chat/messages")
async def clear_chat_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete the current user's standalone chat history (incl. document context)."""
    deleted = (
        db.query(ChatMessage)
        .filter(ChatMessage.case_id.is_(None))
        .filter(ChatMessage.user_id == current_user.id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"deleted": deleted}


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    deleted = (
        db.query(ChatMessage)
        .filter(ChatMessage.case_id.is_(None))
        .filter(ChatMessage.user_id == current_user.id)
        .filter(ChatMessage.session_id == session_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"deleted": deleted}


@router.post("/chat/messages", status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    body: SendMessageBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    language = body.language if body.language in MESSAGE_LANGUAGES else "darija"
    session_id = body.sessionId or uuid.uuid4().hex

    conversation_history = _recent_chat_history(
        db.query(ChatMessage)
        .filter(ChatMessage.case_id.is_(None))
        .filter(ChatMessage.user_id == current_user.id)
        .filter(ChatMessage.session_id == session_id)
        .filter(ChatMessage.sender.in_(("user", "assistant")))
    )

    user_msg = ChatMessage(
        case_id=None, user_id=current_user.id, session_id=session_id,
        sender="user", message=body.content, language=language
    )
    db.add(user_msg)

    # Detect service if keyword matches, else None (searches all services)
    detected_service = detect_service_id(body.content)

    # ── Guardrail: detect clearly out-of-scope or gibberish input ────────────
    _MEANINGFUL_MIN_CHARS = 3
    _has_arabic = bool(re.search(r'[\u0600-\u06FF]', body.content))
    _has_french = bool(re.search(r'[a-zA-Z]{2,}', body.content))
    _is_too_short = len(body.content.strip()) < _MEANINGFUL_MIN_CHARS
    # Gibberish: long Latin string with no real words (no spaces AND no Arabic)
    _is_gibberish = (
        not _has_arabic
        and len(body.content.strip()) > 6
        and " " not in body.content.strip()
        and not any(word in body.content.lower() for word in [
            "hello", "bonjour", "salam", "merhba", "salut",
            "merci", "chokran", "help", "aide", "assistance",
            "cin", "cni", "carte", "document", "pdf", "upload",
        ])
    )

    if _is_too_short or _is_gibberish:
        _out_of_scope_msg = {
            "darija": (
                "👋 **أهلاً بيك في OmniAgent!**\n\n"
                "ما فهمتش سؤالك مزيان. تقدر تسألني بالدارجة، الفرنسية، أو العربية على:\n\n"
                "• 📋 **شهادة السكنى** — الوثائق، الرسوم، المكان\n"
                "• 🪪 **CIN / الهوية الوطنية** — التجديد، الفقدان\n"
                "• 📄 **عقد الازدياد** — الاستخراج، التصحيح\n"
                "• 💍 **عقد الزواج** — الوثائق، الإجراءات\n"
                "• ⚖️ **السجل العدلي** — الطلب، المدة\n\n"
                "كيفاش نعاونك؟"
            ),
            "fr": (
                "👋 **Bienvenue sur OmniAgent !**\n\n"
                "Je n'ai pas compris votre question. Posez-moi vos questions en darija, français ou arabe sur:\n\n"
                "• 📋 Certificat de résidence\n"
                "• 🪪 Carte Nationale d'Identité (CIN)\n"
                "• 📄 Acte de naissance\n"
                "• 💍 Acte de mariage\n"
                "• ⚖️ Casier judiciaire\n\n"
                "Comment puis-je vous aider ?"
            ),
            "arabic": (
                "👋 **أهلاً بك في OmniAgent!**\n\n"
                "لم أفهم سؤالك. يمكنك سؤالي بالدارجة أو الفرنسية أو العربية الفصحى حول:\n\n"
                "• 📋 شهادة الإقامة\n"
                "• 🪪 بطاقة التعريف الوطنية\n"
                "• 📄 عقد الازدياد\n"
                "• 💍 عقد الزواج\n"
                "• ⚖️ السجل العدلي\n\n"
                "كيف يمكنني مساعدتك؟"
            ),
        }
        answer_text = _out_of_scope_msg.get(language, _out_of_scope_msg["darija"])
        assistant_msg = ChatMessage(
            case_id=None,
            user_id=current_user.id,
            session_id=session_id,
            sender="assistant",
            message=answer_text,
            language=language,
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)
        return serialize_message(assistant_msg, _standalone_count(db, current_user.id, session_id))

    try:
        from app.rag_service import query_rag
        rag_res = query_rag(
            user_query=body.content,
            service_type=detected_service,
            conversation_history=conversation_history
        )
        answer_text = rag_res.get("answer", "").strip()
        # Only fall back if RAG is explicitly offline (fallback_reason), NOT for every answer
        if not answer_text:
            if detected_service:
                answer = answer_with_metadata(
                    service_id=detected_service,
                    user_message=body.content,
                    use_rag=False,
                    conversation_history=conversation_history,
                )
                answer_text = answer.answer
            else:
                # No service detected and RAG returned empty — ask for clarification
                answer_text = (
                    "ما فهمتش تماماً شنو بغيت. تقدر تعطيني مزيد من التفاصيل على الخدمة الإدارية لي محتاجها؟\n\n"
                    "مثلاً: شهادة السكنى، عقد الازدياد، السجل العدلي، CIN..."
                )
    except Exception as e:
        print(f"[WARN] RAG query failed: {e}")
        if detected_service:
            answer = answer_with_metadata(
                service_id=detected_service,
                user_message=body.content,
                use_rag=False,
                conversation_history=conversation_history,
            )
            answer_text = answer.answer
        else:
            answer_text = (
                "وقع مشكل تقني مؤقت. تقدر تسولني مباشرة على أي إجراء إداري وغادي نعاونك."
            )


    assistant_msg = ChatMessage(
        case_id=None,
        user_id=current_user.id,
        session_id=session_id,
        sender="assistant",
        message=answer_text,
        language=language,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return serialize_message(assistant_msg, _standalone_count(db, current_user.id, session_id))


from app.services.document_analyzer import (  # noqa: E402
    analyze_document,
    format_analysis_chat_message,
)


@router.post("/chat/documents", status_code=status.HTTP_201_CREATED)
async def upload_chat_document(
    file: UploadFile = File(...),
    language: str = Form(default="darija"),
    sessionId: str | None = Form(default=None),
    message: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Upload a document into the standalone chat.

    Pipeline:
    1. Validate MIME type and size.
    2. Save file to disk.
    3. Extract text (pypdf fast path for selectable PDFs).
    4. OCR fallback via Gemini Vision for scanned PDFs and images.
    5. LLM analysis: doc type, entities, validity, conformity verdict, answering user prompt if provided.
    6. Store extracted text as a hidden context row for follow-up RAG queries.
    7. Return formatted analysis as the assistant's reply.
    """
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_UPLOAD_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF, JPEG, PNG or WebP files are accepted",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 10 MB limit",
        )

    safe_name = _sanitize_filename(file.filename)
    upload_dir = Path(settings.upload_root) / "chat" / current_user.id
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / f"{uuid.uuid4().hex}_{safe_name}").write_bytes(file_bytes)

    lang = language if language in MESSAGE_LANGUAGES else "darija"
    session_id = sessionId or uuid.uuid4().hex
    trimmed_msg = (message or "").strip()

    # ── Run Smart Document Analysis (OCR + LLM) ───────────────────────────────
    analysis = analyze_document(
        file_bytes=file_bytes,
        content_type=content_type,
        filename=safe_name,
        language=lang,
        google_api_key=settings.google_api_key,
        gemini_model_name=settings.gemini_model,
        user_query=trimmed_msg,
    )

    # ── Visible user message (attachment bubble with optional message) ────────
    user_msg_content = f"[Document] {safe_name}\n\n{trimmed_msg}" if trimmed_msg else f"[Document] {safe_name}"
    db.add(
        ChatMessage(
            case_id=None,
            user_id=current_user.id,
            session_id=session_id,
            sender="user",
            message=user_msg_content,
            language=lang,
        )
    )

    # ── Hidden context row — stores extracted OCR text for follow-up RAG use ──
    if analysis.extracted_text:
        db.add(
            ChatMessage(
                case_id=None,
                user_id=current_user.id,
                session_id=session_id,
                sender="document_context",
                message=analysis.extracted_text[:20000],
                language=lang,
            )
        )

    # ── Assistant reply with full structured analysis ─────────────────────────
    assistant_msg = ChatMessage(
        case_id=None,
        user_id=current_user.id,
        session_id=session_id,
        sender="assistant",
        message=format_analysis_chat_message(analysis, safe_name, lang),
        language=lang,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return serialize_message(assistant_msg, _standalone_count(db, current_user.id, session_id))


# --------------------------------------------------------------------------- #
# Dashboard & Admin
# --------------------------------------------------------------------------- #
@router.post("/analytics/visits", status_code=status.HTTP_201_CREATED)
async def record_visit(body: VisitEventBody, db: Session = Depends(get_db)) -> dict:
    event = VisitEvent(
        session_id=body.sessionId,
        page=body.page,
        page_label=body.pageLabel,
        language=body.language if body.language in MESSAGE_LANGUAGES else "fr",
        device=body.device if body.device in {"Mobile", "Desktop", "Tablette"} else "Desktop",
    )
    db.add(event)
    db.commit()
    return {"recorded": True}


@router.get("/admin/analytics/visits")
async def admin_visit_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    cutoff = datetime.utcnow() - timedelta(days=7)
    events = (
        db.query(VisitEvent)
        .filter(VisitEvent.created_at >= cutoff)
        .order_by(VisitEvent.created_at.desc())
        .limit(2000)
        .all()
    )
    return [
        {
            "id": event.id,
            "sessionId": event.session_id,
            "page": event.page,
            "pageLabel": event.page_label,
            "timestamp": int(event.created_at.timestamp() * 1000),
            "device": event.device,
            "city": "Non renseignée",
            "lang": event.language,
        }
        for event in events
    ]


def status_counts(db: Session, base_query) -> list[dict]:
    rows = base_query.with_entities(Case.status, func.count(Case.id)).group_by(Case.status).all()
    return [{"status": s, "count": c} for s, c in rows]


@router.get("/dashboard/summary")
async def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    base = db.query(Case).filter(Case.user_id == current_user.id)
    total = base.count()
    approved = base.filter(Case.status == "approved").count()
    pending_docs = base.filter(Case.status == "pending_documents").count()
    active = base.filter(Case.status.in_(["submitted", "in_review"])).count()
    recent = base.order_by(Case.created_at.desc()).limit(5).all()

    avg_days = (
        db.query(func.avg(Service.avg_processing_days)).scalar() or 0
    )
    return {
        "totalCases": total,
        "activeCases": active,
        "pendingDocuments": pending_docs,
        "approvedCases": approved,
        "avgProcessingDays": round(float(avg_days), 1),
        "recentCases": [serialize_case(c) for c in recent],
        "casesByStatus": status_counts(db, base),
    }


@router.get("/admin/stats")
async def admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    total_cases = db.query(Case).count()
    total_services = db.query(Service).count()
    total_documents = db.query(Document).count()
    avg_days = db.query(func.avg(Service.avg_processing_days)).scalar() or 0

    by_service_rows = (
        db.query(Service.name_fr, func.count(Case.id))
        .join(Case, Case.service_id == Service.id)
        .group_by(Service.name_fr)
        .all()
    )
    return {
        "totalCases": total_cases,
        "totalServices": total_services,
        "casesByStatus": status_counts(db, db.query(Case)),
        "casesByService": [
            {"serviceNameFr": name, "count": count} for name, count in by_service_rows
        ],
        "avgProcessingDays": round(float(avg_days), 1),
        "totalDocuments": total_documents,
    }


@router.get("/admin/cases")
async def admin_list_cases(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    query = db.query(Case)
    if status_filter:
        query = query.filter(Case.status == status_filter)
    cases = query.order_by(Case.created_at.desc()).all()
    return [serialize_case(c) for c in cases]


@router.patch("/admin/cases/{case_id}")
async def admin_update_case(
    case_id: int,
    body: UpdateCaseBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    case = get_case_or_404(db, case_id)
    if body.status is not None and body.status != case.status:
        case.status = body.status
        log_action(db, case.id, "status_changed", current_user.id, {"status": body.status})
    if body.notes is not None:
        case.notes = body.notes
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(case)
    return serialize_case(case)


@router.get("/admin/notifications")
async def admin_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Fetch pending case alerts and recent citizen submissions for admin."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    pending_count = (
        db.query(func.count(Case.id))
        .filter(Case.status.in_(("submitted", "in_review")))
        .scalar()
        or 0
    )

    recent_cases = (
        db.query(Case)
        .order_by(Case.created_at.desc())
        .limit(20)
        .all()
    )

    notifications = []
    for c in recent_cases:
        service_name_fr = c.service.name_fr if c.service else "Service administratif"
        service_name_ar = c.service.name_ar if c.service else "خدمة إدارية"
        notifications.append({
            "id": f"notif-case-{c.id}",
            "caseId": c.public_id,
            "type": "new_request",
            "referenceNumber": c.reference_number,
            "applicantName": c.applicant_name or "المواطن",
            "serviceNameFr": service_name_fr,
            "serviceNameAr": service_name_ar,
            "status": c.status,
            "createdAt": c.created_at.isoformat() if c.created_at else None,
            "messageFr": f"Nouvelle demande : {service_name_fr} ({c.reference_number}) déposée par {c.applicant_name or 'un citoyen'}",
            "messageAr": f"طلب جديد : {service_name_ar} ({c.reference_number}) مقدم من {c.applicant_name or 'مواطن'}",
        })

    return {
        "pendingCount": pending_count,
        "notifications": notifications,
    }
