from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentResponse(BaseModel):
    id: str
    application_id: str
    file_key: str
    doc_type: Optional[str] = None
    ocr_confidence: Optional[float] = None
    extracted_json: Optional[dict] = None
    tamper_flag: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ExtractionResult(BaseModel):
    document_id: str
    extracted_fields: dict
    confidence_score: float
    tamper_detected: bool
    raw_text: Optional[str] = None
