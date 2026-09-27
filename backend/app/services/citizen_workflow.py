"""Profile document reuse and immutable case submission snapshots."""
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException
from app.models import Document, AuditLog
from app.core.config import settings
from app.services.document_analyzer import extract_structured_metadata


def analyze_file(data, mime, name, language="fr"):
    result = extract_structured_metadata(data, mime, name, language,
                                        settings.google_api_key, settings.gemini_model).to_dict()
    return {**result, "processedAt": datetime.utcnow().isoformat(),
            "engine": settings.gemini_model if result.get("ocr_used") else "local",
            "extractionStatus": "extracted" if result.get("raw_extracted_text") else "needs_review"}


def profile_documents(user):
    entries = list(user.personal_documents or [])
    if user.cin_file_path and not any(d.get("path") == user.cin_file_path for d in entries):
        path = Path(user.cin_file_path)
        entries.append({"id": "cin", "name": path.name.split("_", 1)[-1],
                        "path": str(path), "documentType": "national_id",
                        "size": path.stat().st_size if path.exists() else 0,
                        "mimeType": "application/pdf" if path.suffix == ".pdf" else "image/png"})
    return entries


def public_documents(user):
    return [{k: v for k, v in entry.items() if k != "path"} for entry in profile_documents(user)]


def snapshot(case, user):
    workflow = dict(case.workflow_data or {})
    if not workflow.get("profileSnapshot"):
        workflow["profileSnapshot"] = {
            "citizenId": user.id, "fullName": case.applicant_name,
            "email": case.applicant_email, "phone": case.applicant_phone,
            "address": (user.profile_data or {}).get("address", ""),
            "snapshotCreatedAt": datetime.utcnow().isoformat(),
        }
        workflow["submittedAt"] = datetime.utcnow().isoformat()
        case.workflow_data = workflow


def attach_profile_document(db, case, user, document_id, requirement):
    if requirement not in (case.service.required_documents or []):
        raise HTTPException(400, "Unknown document requirement")
    entry = next((d for d in profile_documents(user) if d["id"] == document_id), None)
    if not entry or not Path(entry.get("path", "")).is_file():
        raise HTTPException(404, "Profile document not found")
    analysis = entry.get("analysis") or {}
    document = Document(case_id=case.id, doc_type=requirement, file_name=entry["name"],
                        file_path=entry["path"], file_size=entry["size"], mime_type=entry["mimeType"],
                        source_profile_document_id=document_id, analysis=analysis,
                        ocr_text=analysis.get("raw_extracted_text", ""), validation_status="pending")
    db.add(document)
    db.add(AuditLog(case_id=case.id, actor_id=user.id, action="document_attached",
                    details={"requirement": requirement, "sourceDocumentId": document_id}))
    return document
