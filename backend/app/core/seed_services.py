from sqlalchemy.orm import Session

from app.models import Service


def seed_services(db: Session) -> None:
    """Insert the 3 public services if they are missing."""
    services = [
        Service(
            id="residence_certificate",
            name_ar="شهادة السكنى",
            name_fr="Certificat de Residence",
            name_darija="شهادة السكنى",
            description_ar="وثيقة تثبت إقامتك في عنوان معين",
            description_fr="Document prouvant votre residence",
            icon="🏠",
            avg_processing_days=3,
            required_documents=["national_id", "proof_of_residence", "address_confirmation"]
        ),
        Service(
            id="birth_certificate",
            name_ar="عقد الازدياد",
            name_fr="Acte de Naissance",
            name_darija="عقد الازدياد",
            description_ar="الشهادة الرسمية للولادة",
            description_fr="Certificat officiel de naissance",
            icon="👶",
            avg_processing_days=2,
            required_documents=["parent_id", "marriage_certificate", "hospital_record"]
        ),
        Service(
            id="marriage_contract",
            name_ar="عقد الزواج",
            name_fr="Acte de Mariage",
            name_darija="عقد الزواج",
            description_ar="الشهادة الرسمية للزواج",
            description_fr="Certificat officiel de mariage",
            icon="💍",
            avg_processing_days=5,
            required_documents=["both_ids", "birth_certificates", "witness_documents"]
        )
    ]

    for service in services:
        existing = db.query(Service).filter(Service.id == service.id).first()
        if existing is None:
            db.add(service)
    db.commit()
