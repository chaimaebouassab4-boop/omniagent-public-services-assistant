from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import Service, User


def seed_admin(db: Session) -> None:
    """Create the default admin account if it does not exist."""
    existing = db.query(User).filter(User.email == settings.admin_email).first()
    if existing is None:
        db.add(
            User(
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                is_admin=True
            )
        )
        db.commit()
    elif not existing.password_hash:
        existing.password_hash = hash_password(settings.admin_password)
        existing.is_admin = True
        db.commit()


def seed_services(db: Session) -> None:
    """Insert the 10 public services if they are missing."""
    services = [
        Service(
            id="residence_certificate",
            name_ar="شهادة السكنى",
            name_fr="Certificat de Résidence",
            name_darija="شهادة السكنى",
            description_ar="وثيقة تثبت إقامتك في عنوان معين",
            description_fr="Document prouvant votre résidence",
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
        ),
        Service(
            id="death_certificate",
            name_ar="مستخرج شهادة الوفاة",
            name_fr="Extrait de certificat de décès",
            name_darija="شهادة الوفاة",
            description_ar="وثيقة رسمية من الحالة المدنية تثبت وفاة الشخص",
            description_fr="Document officiel attestant le décès d'une personne",
            icon="🕊️",
            avg_processing_days=2,
            required_documents=["declarant_id", "medical_death_notice", "family_book"]
        ),
        Service(
            id="life_certificate",
            name_ar="شهادة الحياة",
            name_fr="Certificat de vie",
            name_darija="شهادة الحياة",
            description_ar="وثيقة إدارية تثبت أن الشخص لا يزال على قيد الحياة",
            description_fr="Document attestant que la personne est en vie",
            icon="❤️",
            avg_processing_days=1,
            required_documents=["national_id", "residence_proof"]
        ),
        Service(
            id="single_status_certificate",
            name_ar="شهادة العزوبة",
            name_fr="Certificat de célibat",
            name_darija="شهادة العزوبة",
            description_ar="وثيقة إدارية تثبت أن الشخص غير متزوج",
            description_fr="Document attestant que la personne n'est pas mariée",
            icon="🧍",
            avg_processing_days=3,
            required_documents=["national_id", "birth_certificate", "witness_declaration"]
        ),
        Service(
            id="non_property_certificate",
            name_ar="شهادة عدم الملكية",
            name_fr="Certificat de non-propriété",
            name_darija="شهادة عدم الملكية",
            description_ar="وثيقة تثبت أن الشخص لا يملك أي عقار محفظ",
            description_fr="Document attestant l'absence de propriété immobilière",
            icon="🏘️",
            avg_processing_days=4,
            required_documents=["national_id", "request_form"]
        ),
        Service(
            id="administrative_certificate",
            name_ar="الشهادة الإدارية",
            name_fr="Attestation administrative",
            name_darija="الشهادة الإدارية",
            description_ar="وثيقة إدارية عامة تسلمها السلطة المحلية لإثبات حالة معينة",
            description_fr="Attestation générale délivrée par l'autorité locale",
            icon="📄",
            avg_processing_days=3,
            required_documents=["national_id", "supporting_documents"]
        ),
        Service(
            id="good_conduct_certificate",
            name_ar="شهادة حسن السيرة",
            name_fr="Fiche anthropométrique",
            name_darija="شهادة حسن السيرة",
            description_ar="وثيقة من الأمن الوطني تثبت خلو السوابق",
            description_fr="Document de la police attestant l'absence d'antécédents",
            icon="🛡️",
            avg_processing_days=5,
            required_documents=["national_id", "photos", "residence_proof"]
        ),
        Service(
            id="criminal_record",
            name_ar="السجل العدلي",
            name_fr="Extrait du casier judiciaire",
            name_darija="السجل العدلي",
            description_ar="وثيقة من المحكمة تتضمن جردا للأحكام الجنائية",
            description_fr="Extrait du casier judiciaire délivré par le tribunal",
            icon="⚖️",
            avg_processing_days=7,
            required_documents=["national_id", "birth_certificate", "request_form"]
        )
    ]

    for service in services:
        existing = db.query(Service).filter(Service.id == service.id).first()
        if existing is None:
            db.add(service)
    db.commit()
