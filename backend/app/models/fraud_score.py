import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class FraudScore(Base):
    __tablename__ = "fraud_scores"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), unique=True, nullable=False)
    fraud_probability: Mapped[float] = mapped_column(Float, nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=True)
    top_features: Mapped[list] = mapped_column(JSON, nullable=True)
    recommendation: Mapped[str] = mapped_column(String(50), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    application: Mapped["Application"] = relationship(back_populates="fraud_score")
