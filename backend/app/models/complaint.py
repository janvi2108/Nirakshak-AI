import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Complaint(Base):
    __tablename__ = "complaints"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    citizen_id: Mapped[str] = mapped_column(ForeignKey("citizens.id"), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    department: Mapped[str] = mapped_column(String(100), nullable=True)
    urgency_score: Mapped[float] = mapped_column(Float, nullable=True)
    sla_risk: Mapped[str] = mapped_column(String(20), nullable=True)
    draft_response: Mapped[str] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    citizen: Mapped["Citizen"] = relationship(back_populates="complaints")
