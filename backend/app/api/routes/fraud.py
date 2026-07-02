from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.fraud_score import FraudScore
from app.models.application import Application
from app.schemas.fraud import FraudScoreResponse, FraudScoreDB
from app.services.fraud_service import fraud_detector
from app.api.deps import get_current_user
from typing import List

router = APIRouter()


@router.post("/score/{application_id}", response_model=FraudScoreResponse)
async def score_application(application_id: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    fraud_result = fraud_detector.score({"doc_hash_reuse": 0, "submission_speed_seconds": 300,
                                          "ip_reuse_count": 1, "field_mismatch_score": 0.0,
                                          "time_since_last_app_days": 30, "district_anomaly_score": 0.0})
    existing = await db.execute(select(FraudScore).where(FraudScore.application_id == application_id))
    fs = existing.scalar_one_or_none()
    if fs:
        fs.fraud_probability = fraud_result["fraud_probability"]
        fs.anomaly_score = fraud_result["anomaly_score"]
        fs.top_features = fraud_result["top_features"]
        fs.recommendation = fraud_result["recommendation"]
    else:
        fs = FraudScore(application_id=application_id, fraud_probability=fraud_result["fraud_probability"],
                        anomaly_score=fraud_result["anomaly_score"], top_features=fraud_result["top_features"],
                        recommendation=fraud_result["recommendation"], model_version=fraud_result["model_version"])
        db.add(fs)
    application.fraud_recommendation = fraud_result["recommendation"]
    await db.commit()
    return FraudScoreResponse(application_id=application_id, fraud_probability=fraud_result["fraud_probability"],
        anomaly_score=fraud_result["anomaly_score"], recommendation=fraud_result["recommendation"],
        top_features=fraud_result["top_features"], model_version=fraud_result["model_version"])


@router.get("/{application_id}", response_model=FraudScoreDB)
async def get_fraud_score(application_id: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(FraudScore).where(FraudScore.application_id == application_id))
    fs = result.scalar_one_or_none()
    if not fs:
        raise HTTPException(status_code=404, detail="Fraud score not found. Run /score first.")
    return fs
