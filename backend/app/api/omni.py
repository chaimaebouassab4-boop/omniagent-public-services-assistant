"""Compatibility API matching the omniagent frontend's generated client.

The generated client (orval) expects raw (un-enveloped) JSON payloads with
camelCase fields and numeric ids. This router serves that exact contract on the
`/api/*` paths the frontend calls, backed by the existing SQLAlchemy models and
the knowledge-base answer engine.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models import AuditLog, Case, ChatMessage, Document, Service, User
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

    user_msg = ChatMessage(case_id=case.id, sender="user", message=body.content, language=language)
    db.add(user_msg)

    answer = answer_with_metadata(service_id=case.service_id, user_message=body.content)
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
def detect_service_id(message: str) -> str:
    """Best-effort service detection from keywords for standalone chat."""
    lowered = message.lower()
    keyword_map = {
        "residence_certificate": ["سكن", "résidence", "residence", "سكنى"],
        "birth_certificate": ["ازدياد", "ولادة", "naissance", "birth"],
        "marriage_contract": ["زواج", "mariage", "marriage"],
        "death_certificate": ["وفاة", "décès", "deces", "death"],
        "life_certificate": ["حياة", "vie", "life"],
        "single_status_certificate": ["عزوبة", "célibat", "celibat", "single"],
        "non_property_certificate": ["ملكية", "propriété", "propriete", "property"],
        "good_conduct_certificate": ["حسن السيرة", "conduite", "conduct"],
        "criminal_record": ["سجل العدلي", "casier", "criminal"],
        "administrative_certificate": ["إدارية", "administrative"],
    }
    for service_id, keywords in keyword_map.items():
        if any(keyword in message or keyword in lowered for keyword in keywords):
            return service_id
    return "residence_certificate"


@router.get("/chat/messages")
async def list_chat_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.case_id.is_(None))
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [serialize_message(m, i + 1) for i, m in enumerate(messages)]


@router.post("/chat/messages", status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    body: SendMessageBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    language = body.language if body.language in MESSAGE_LANGUAGES else "darija"

    user_msg = ChatMessage(case_id=None, sender="user", message=body.content, language=language)
    db.add(user_msg)

    service_id = detect_service_id(body.content)
    answer = answer_with_metadata(service_id=service_id, user_message=body.content)
    assistant_msg = ChatMessage(
        case_id=None, sender="assistant", message=answer.answer, language=language
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    count = db.query(ChatMessage).filter(ChatMessage.case_id.is_(None)).count()
    return serialize_message(assistant_msg, count)


# --------------------------------------------------------------------------- #
# Dashboard & Admin
# --------------------------------------------------------------------------- #
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
