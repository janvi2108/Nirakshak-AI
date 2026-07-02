from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ComplaintCreate(BaseModel):
    text: str = Field(..., min_length=10, max_length=2000)
    application_id: Optional[str] = None


class ComplaintClassifyResult(BaseModel):
    category: str
    department: str
    urgency_score: float
    sla_risk: str
    language: str
    confidence: Optional[float] = None
    method: str


class ComplaintResponse(BaseModel):
    id: str
    citizen_id: str
    raw_text: str
    category: Optional[str] = None
    department: Optional[str] = None
    urgency_score: Optional[float] = None
    sla_risk: Optional[str] = None
    draft_response: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ComplaintDetail(ComplaintResponse):
    classification: Optional[ComplaintClassifyResult] = None
