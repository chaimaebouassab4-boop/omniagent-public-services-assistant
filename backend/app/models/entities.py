import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, default="")
    full_name: Mapped[str] = mapped_column(String, default="")
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    cases: Mapped[list["Case"]] = relationship(back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="actor")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name_ar: Mapped[str] = mapped_column(String)
    name_fr: Mapped[str] = mapped_column(String)
    name_darija: Mapped[str] = mapped_column(String)
    description_ar: Mapped[str] = mapped_column(String)
    description_fr: Mapped[str] = mapped_column(String)
    icon: Mapped[str] = mapped_column(String)
    avg_processing_days: Mapped[int] = mapped_column(Integer)
    required_documents: Mapped[list[str]] = mapped_column(JSON)

    cases: Mapped[list["Case"]] = relationship(back_populates="service")


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Stable numeric id exposed to the frontend (used in URLs).
    public_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, autoincrement=True)
    reference_number: Mapped[str] = mapped_column(String, default="")
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    service_id: Mapped[str] = mapped_column(String, ForeignKey("services.id"), index=True)
    applicant_name: Mapped[str] = mapped_column(String, default="")
    applicant_email: Mapped[str] = mapped_column(String, default="")
    applicant_phone: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="submitted")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(back_populates="case")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="case")
    service: Mapped[Service] = relationship(back_populates="cases")
    user: Mapped[User] = relationship(back_populates="cases")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id"), index=True)
    doc_type: Mapped[str] = mapped_column(String)
    file_name: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    file_size: Mapped[int] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_status: Mapped[str] = mapped_column(String, default="pending")

    case: Mapped[Case] = relationship(back_populates="documents")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Nullable so standalone chat messages (not tied to a case) can be stored.
    case_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("cases.id"), index=True, nullable=True
    )
    sender: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String, default="darija")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped[Case | None] = relationship(back_populates="chat_messages")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id"), index=True)
    action: Mapped[str] = mapped_column(String)
    actor_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped[Case] = relationship(back_populates="audit_logs")
    actor: Mapped[User | None] = relationship(back_populates="audit_logs")
