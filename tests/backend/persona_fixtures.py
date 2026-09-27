"""Repeatable, synthetic presentation scenarios for the admin demo toolbar."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AuditLog, Case, Document, Service, User
from app.services.case_lifecycle import tracking_code


DEMO_PERSONAS = {
    "amine": {
        "label": "Amine",
        "language": "darija",
        "service_id": "residence_certificate",
        "full_name": "Amine El Mansouri",
        "email": "demo.amine@omniagent.local",
        "phone": "+212612345601",
        "address": "18 Rue Al Massira, Maarif, Casablanca",
        "documents": (
            ("national_id", "CIN-Amine.pdf", "verified", "CIN: BK654321\nAdresse: 18 Rue Al Massira, Maarif, Casablanca"),
            ("proof_of_residence", "Facture-electricite-Amine.pdf", "verified", "Adresse: 18 Rue Al Massira, Maarif, Casablanca\nDate: 10/09/2026"),
            ("address_confirmation", "Attestation-adresse-Amine.pdf", "verified", "Adresse: 18 Rue Al Massira, Maarif, Casablanca"),
        ),
    },
    "fatima": {
        "label": "Fatima",
        "language": "fr",
        "service_id": "birth_certificate",
        "full_name": "Fatima Zahra Alaoui",
        "email": "demo.fatima@omniagent.local",
        "phone": "+212612345602",
        "address": "32 Avenue Fal Ould Oumeir, Agdal, Rabat",
        "documents": (
            ("parent_id", "CIN-parent-Fatima.pdf", "verified", "Nom: Fatima Zahra Alaoui\nAdresse: 32 Avenue Fal Ould Oumeir, Agdal, Rabat"),
            ("marriage_certificate", "Acte-mariage-parents.pdf", "verified", "Acte de mariage vérifié"),
            ("hospital_record", "Declaration-naissance.pdf", "verified", "Déclaration de naissance - Hôpital Ibn Sina"),
        ),
    },
    "youssef": {
        "label": "Youssef",
        "language": "fr",
        "service_id": "residence_certificate",
        "full_name": "Youssef Berrada",
        "email": "demo.youssef@omniagent.local",
        "phone": "+212612345603",
        "address": "7 Boulevard Zerktouni, Casablanca",
        "documents": (
            ("national_id", "CIN-Youssef-illisible.pdf", "rejected", "Document illisible - unreadable"),
            ("proof_of_residence", "Facture-Youssef.pdf", "verified", "Adresse: 7 Boulevard Zerktouni, Casablanca"),
            ("address_confirmation", "Attestation-Youssef.pdf", "verified", "Adresse: 7 Boulevard Zerktouni, Casablanca"),
        ),
    },
}


def _write_demo_pdf(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(path), pagesize=A4)
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawString(54, 780, "OmniAgent - Document de démonstration")
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(54, 745, title[:80])
    canvas.setFont("Helvetica", 10)
    y = 715
    for line in body.splitlines():
        canvas.drawString(54, y, line[:90])
        y -= 17
    canvas.setFont("Helvetica-Oblique", 9)
    canvas.drawString(54, 70, "Données entièrement synthétiques - aucune valeur officielle")
    canvas.save()


def prepare_demo_persona(db: Session, key: str, actor_id: str) -> tuple[Case, dict]:
    config = DEMO_PERSONAS.get(key)
    if config is None:
        raise KeyError(key)
    user = db.query(User).filter(User.email == config["email"]).first()
    if user is None:
        user = User(
            email=config["email"],
            full_name=config["full_name"],
            phone=config["phone"],
            password_hash="",
        )
        db.add(user)
        db.flush()
    service = db.query(Service).filter(Service.id == config["service_id"]).first()
    if service is None:
        raise LookupError(config["service_id"])
    marker = f"[demo:{key}]"
    case = db.query(Case).filter(Case.notes == marker).first()
    if case is None:
        max_id = db.query(func.max(Case.public_id)).scalar() or 0
        created_at = datetime.utcnow()
        case = Case(
            public_id=max_id + 1,
            reference_number=tracking_code(max_id + 1, created_at),
            user_id=user.id,
            service_id=service.id,
            applicant_name=config["full_name"],
            applicant_email=config["email"],
            applicant_phone=config["phone"],
            notes=marker,
            status="UNDER_REVIEW",
            created_at=created_at,
            updated_at=created_at,
        )
        db.add(case)
        db.flush()
        db.add(AuditLog(case_id=case.id, action="created", actor_id=actor_id, details={"status": "DRAFT", "demo": key}))
        db.add(AuditLog(case_id=case.id, action="status_changed", actor_id=actor_id, details={"status": "SUBMITTED", "demo": key}))
        db.add(AuditLog(case_id=case.id, action="status_changed", actor_id=actor_id, details={"status": "UNDER_REVIEW", "demo": key}))
    else:
        case.status = "UNDER_REVIEW"
        case.updated_at = datetime.utcnow()

    existing_by_type = {document.doc_type: document for document in case.documents}
    for doc_type, filename, validation_status, ocr_text in config["documents"]:
        storage = Path(settings.upload_root) / "demo" / key / filename
        if not storage.exists():
            _write_demo_pdf(storage, filename, ocr_text)
        document = existing_by_type.get(doc_type)
        if document is None:
            document = Document(
                case_id=case.id,
                doc_type=doc_type,
                file_name=filename,
                file_path=str(storage),
                file_size=storage.stat().st_size,
                mime_type="application/pdf",
            )
            db.add(document)
        document.file_name = filename
        document.file_path = str(storage)
        document.file_size = storage.stat().st_size
        document.mime_type = "application/pdf"
        document.validation_status = validation_status
        document.ocr_text = ocr_text
    db.commit()
    db.refresh(case)
    return case, {"key": key, "label": config["label"], "language": config["language"]}
