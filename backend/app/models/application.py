import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    citizen_id: Mapped[str] = mapped_column(ForeignKey("citizens.id"), nullable=False)
    cert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="submitted")
    fraud_recommendation: Mapped[str] = mapped_column(String(50), nullable=True)
    predicted_days: Mapped[float] = mapped_column(Float, nullable=True)
    assigned_officer_id: Mapped[str] = mapped_column(String, nullable=True)
    officer_brief: Mapped[str] = mapped_column(String(2000), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    citizen: Mapped["Citizen"] = relationship(back_populates="applications")
    documents: Mapped[list["Document"]] = relationship(back_populates="application")
    fraud_score: Mapped["FraudScore"] = relationship(back_populates="application", uselist=False)
