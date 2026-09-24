from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.core.security import get_current_user
from app.db.database import get_db
from app.models import AuditLog, Case, ChatMessage, Document, Service, User
from app.services.knowledge_base import answer_with_metadata, normalize_service_id
from app.services.case_lifecycle import canonical_status, next_status, tracking_code, validate_transition
from app.services.case_notifications import notification_draft
from app.services.mock_citizens import verify_mock_profile

router = APIRouter(prefix="/api", tags=["cases"])


class CreateCaseRequest(BaseModel):
    service_id: str = Field(..., examples=["residence_certificate"])
    submit: bool = True


class ChatRequest(BaseModel):
    case_id: str | None = None
    service_id: str | None = None
    message: str
    language: str = "darija"


class RejectRequest(BaseModel):
    reason: str


class UpdateCaseStatusRequest(BaseModel):
    status: str


class VerifyRequest(BaseModel):
    value: str


def ensure_case_access(case: Case | None, current_user: User) -> Case:
    """Checks case existence and verifies citizen ownership."""
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if case.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return case


def log_case_action(
    db: Session,
    case_id: str,
    action: str,
    actor_id: str | None,
    details: dict
) -> None:
    db.add(AuditLog(case_id=case_id, action=action, actor_id=actor_id, details=details))


@router.get("/services")
async def list_services(db: Session = Depends(get_db)) -> dict:
    """Get all available public services."""
    services = db.query(Service).all()
    return {
        "status": "success",
        "data": [
            {
                "id": s.id,
                "name_ar": s.name_ar,
                "name_fr": s.name_fr,
                "name_darija": s.name_darija,
                "description_ar": s.description_ar,
                "description_fr": s.description_fr,
                "icon": s.icon,
                "avg_days": s.avg_processing_days,
                "required_docs": s.required_documents
            }
            for s in services
        ]
    }


@router.get("/services/{service_id}")
async def get_service_details(service_id: str, db: Session = Depends(get_db)) -> dict:
    """Get details for one service."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return {
        "status": "success",
        "data": {
            "id": service.id,
            "name_ar": service.name_ar,
            "name_fr": service.name_fr,
            "name_darija": service.name_darija,
            "description_ar": service.description_ar,
            "description_fr": service.description_fr,
            "required_docs": service.required_documents,
            "avg_days": service.avg_processing_days
        }
    }


@router.post("/cases")
async def create_case(
    request: CreateCaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Create a new citizen case."""
    service = db.query(Service).filter(Service.id == request.service_id).first()
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    public_id = (db.query(func.max(Case.public_id)).scalar() or 0) + 1
    created_at = datetime.utcnow()
    new_case = Case(
        public_id=public_id,
        reference_number=tracking_code(public_id, created_at),
        user_id=current_user.id,
        service_id=request.service_id,
        status="DRAFT",
        created_at=created_at,
    )
    db.add(new_case)
    db.flush()
    log_case_action(
        db=db,
        case_id=new_case.id,
        action="created",
        actor_id=current_user.id,
        details={"service_id": request.service_id, "status": "DRAFT"}
    )
    if request.submit:
        new_case.status = validate_transition(new_case.status, "SUBMITTED", is_admin=False)
        log_case_action(db, new_case.id, "status_changed", current_user.id, {
            "status": new_case.status,
            "notification": notification_draft(new_case.status, new_case.reference_number),
        })
    db.commit()
    db.refresh(new_case)
    return {
        "status": "success",
        "data": {
            "id": new_case.id,
            "service_id": new_case.service_id,
            "status": new_case.status,
            "created_at": new_case.created_at
        }
    }


@router.get("/cases/{case_id}")
async def get_case_details(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Get one case with document summary."""
    case = ensure_case_access(db.query(Case).filter(Case.id == case_id).first(), current_user=current_user)
    return {
        "status": "success",
        "data": {
            "id": case.id,
            "service": case.service.name_ar,
            "status": case.status,
            "created_at": case.created_at,
            "updated_at": case.updated_at,
            "documents": [
                {
                    "id": d.id,
                    "type": d.doc_type,
                    "name": d.file_name,
                    "uploaded_at": d.uploaded_at,
                    "validation_status": d.validation_status
                }
                for d in case.documents
            ]
        }
    }


@router.get("/cases")
async def list_user_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """List all cases for logged-in citizen."""
    cases = db.query(Case).filter(Case.user_id == current_user.id).all()
    return {
        "status": "success",
        "data": [
            {
                "id": c.id,
                "service_id": c.service_id,
                "service": c.service.name_ar,
                "status": c.status,
                "created_at": c.created_at,
                "updated_at": c.updated_at
            }
            for c in cases
        ]
    }


@router.post("/cases/{case_id}/upload")
async def upload_document(
    case_id: str,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Upload one case document and persist metadata."""
    case = ensure_case_access(db.query(Case).filter(Case.id == case_id).first(), current_user=current_user)

    upload_dir = Path(settings.upload_root) / case.id
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_bytes = await file.read()
    file_path = upload_dir / file.filename
    file_path.write_bytes(file_bytes)

    document = Document(
        case_id=case.id,
        doc_type=doc_type,
        file_name=file.filename,
        file_path=str(file_path),
        file_size=len(file_bytes),
        mime_type=file.content_type or "application/octet-stream",
        validation_status="pending"
    )
    db.add(document)
    log_case_action(
        db=db,
        case_id=case.id,
        action="uploaded",
        actor_id=current_user.id,
        details={"doc_type": doc_type, "file_name": file.filename}
    )
    db.commit()
    db.refresh(document)

    return {
        "status": "success",
        "data": {
            "id": document.id,
            "file_name": document.file_name,
            "validation_status": document.validation_status
        }
    }


@router.post("/chat")
async def send_chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Send chat message and return answer from service knowledge base."""
    case: Case | None = None
    service_id = normalize_service_id(request.service_id)

    if request.case_id:
        loaded_case = db.query(Case).filter(Case.id == request.case_id).first()
        if loaded_case is not None:
            case = ensure_case_access(loaded_case, current_user=current_user)
            service_id = normalize_service_id(case.service_id)

    if not service_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="service_id or valid case_id is required"
        )

    knowledge_answer = answer_with_metadata(service_id=service_id, user_message=request.message)
    ai_response = knowledge_answer.answer

    message_id = "standalone"
    if case:
        user_message = ChatMessage(
            case_id=case.id,
            sender="user",
            message=request.message,
            language=request.language
        )
        assistant_message = ChatMessage(
            case_id=case.id,
            sender="assistant",
            message=ai_response,
            language=request.language
        )
        db.add(user_message)
        db.add(assistant_message)
        log_case_action(
            db=db,
            case_id=case.id,
            action="chat_message",
            actor_id=current_user.id,
            details={"language": request.language}
        )
        db.commit()
        db.refresh(assistant_message)
        message_id = assistant_message.id

    return {
        "status": "success",
        "data": {
            "response": ai_response,
            "confidence": knowledge_answer.confidence,
            "sources": knowledge_answer.sources,
            "language": request.language,
            "message_id": message_id,
            "service_id": service_id
        }
    }


@router.get("/cases/{case_id}/chat")
async def get_case_chat_history(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Get chat history for one case."""
    case = ensure_case_access(db.query(Case).filter(Case.id == case_id).first(), current_user=current_user)
    messages = db.query(ChatMessage).filter(ChatMessage.case_id == case.id).all()
    return {
        "status": "success",
        "data": [
            {
                "id": m.id,
                "sender": m.sender,
                "message": m.message,
                "language": m.language,
                "created_at": m.created_at
            }
            for m in messages
        ]
    }


@router.get("/admin/cases")
async def get_all_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Get all cases for admins."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    cases = db.query(Case).all()
    return {
        "status": "success",
        "data": [
            {
                "id": c.id,
                "user_id": c.user_id,
                "service": c.service.name_ar,
                "status": c.status,
                "created_at": c.created_at,
                "updated_at": c.updated_at
            }
            for c in cases
        ]
    }


@router.patch("/admin/cases/{case_id}/status")
async def update_case_status(
    case_id: str,
    request: UpdateCaseStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Advance a case by exactly one canonical lifecycle step."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    previous = canonical_status(case.status)
    try:
        case.status = validate_transition(case.status, request.status, is_admin=True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    case.updated_at = datetime.utcnow()
    log_case_action(db, case.id, "status_changed", current_user.id, {
        "fromStatus": previous,
        "status": case.status,
        "notification": notification_draft(case.status, case.reference_number),
    })
    db.commit()
    return {"status": "success", "data": {"case_id": case.id, "status": case.status}}


@router.post("/admin/approve/{case_id}")
async def approve_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Approve case (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    target = next_status(case.status)
    if target is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Case is already at its final state")
    try:
        case.status = validate_transition(case.status, target, is_admin=True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    case.updated_at = datetime.utcnow()
    log_case_action(db=db, case_id=case.id, action="approved", actor_id=current_user.id, details={})
    db.commit()
    return {"status": "success", "data": {"case_id": case.id, "status": case.status}}


@router.post("/admin/reject/{case_id}")
async def reject_case(
    case_id: str,
    request: RejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Reject case (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    if canonical_status(case.status) != "UNDER_REVIEW":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Documents can only be requested during review")
    case.updated_at = datetime.utcnow()
    log_case_action(
        db=db,
        case_id=case.id,
        action="action_required",
        actor_id=current_user.id,
        details={
            "nextAction": request.reason,
            "notification": notification_draft(case.status, case.reference_number, missing_document=request.reason),
        }
    )
    db.commit()
    return {
        "status": "success",
        "data": {"case_id": case.id, "status": case.status, "reason": request.reason}
    }


@router.post("/verify/cin")
async def verify_cin(request: VerifyRequest) -> dict:
    """Mock CIN verification endpoint."""
    return {"status": "success", "data": {"cin": request.value, **verify_mock_profile("cin", request.value)}}


@router.post("/verify/cnss")
async def verify_cnss(request: VerifyRequest) -> dict:
    """Mock CNSS verification endpoint."""
    return {
        "status": "success",
        "data": {"cnss": request.value, **verify_mock_profile("cnss_number", request.value)}
    }


@router.get("/cases/{case_id}/audit")
async def get_case_audit_log(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Get full audit trail for one case."""
    case = ensure_case_access(db.query(Case).filter(Case.id == case_id).first(), current_user=current_user)
    logs = db.query(AuditLog).filter(AuditLog.case_id == case.id).all()
    return {
        "status": "success",
        "data": [
            {
                "id": log.id,
                "action": log.action,
                "actor": log.actor_id or "system",
                "created_at": log.created_at,
                "details": log.details
            }
            for log in logs
        ]
    }
