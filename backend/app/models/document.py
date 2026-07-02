import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), nullable=False)
    file_key: Mapped[str] = mapped_column(String(500), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(100), nullable=True)
    ocr_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    extracted_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    tamper_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    application: Mapped["Application"] = relationship(back_populates="documents")
