from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class CertType(str, Enum):
    caste = "caste_certificate"
    birth = "birth_certificate"
    income = "income_certificate"
    domicile = "domicile_certificate"
    death = "death_certificate"


class ApplicationCreate(BaseModel):
    cert_type: CertType
    citizen_name: str = Field(..., min_length=2, max_length=255)
    citizen_phone: str = Field(..., min_length=10, max_length=15)
    citizen_email: Optional[str] = None
    district: str = Field(..., min_length=2, max_length=100)
    aadhaar_last4: str = Field(..., min_length=4, max_length=4)


class ApplicationResponse(BaseModel):
    id: str
    cert_type: str
    status: str
    predicted_days: Optional[float] = None
    submitted_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationDetail(ApplicationResponse):
    citizen_id: str
    fraud_recommendation: Optional[str] = None
    assigned_officer_id: Optional[str] = None
    officer_brief: Optional[str] = None
