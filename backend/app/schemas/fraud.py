from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FraudFeature(BaseModel):
    feature: str
    contribution: float
    value: Optional[float] = None


class FraudScoreResponse(BaseModel):
    application_id: str
    fraud_probability: float
    anomaly_score: float
    recommendation: str
    top_features: List[FraudFeature]
    model_version: str


class FraudScoreDB(BaseModel):
    id: str
    application_id: str
    fraud_probability: float
    anomaly_score: Optional[float] = None
    top_features: Optional[list] = None
    recommendation: str
    created_at: datetime

    class Config:
        from_attributes = True
