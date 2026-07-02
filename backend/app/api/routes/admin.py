from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models.application import Application
from app.models.fraud_score import FraudScore
from app.models.complaint import Complaint
from app.services.delay_service import delay_predictor
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    total_apps = await db.execute(select(func.count(Application.id)))
    status_counts = await db.execute(select(Application.status, func.count(Application.id)).group_by(Application.status))
    fraud_flags = await db.execute(select(func.count(FraudScore.id)).where(FraudScore.fraud_probability > 0.4))
    total_complaints = await db.execute(select(func.count(Complaint.id)))
    return {
        "total_applications": total_apps.scalar(),
        "status_breakdown": dict(status_counts.all()),
        "fraud_flagged": fraud_flags.scalar(),
        "total_complaints": total_complaints.scalar(),
    }


@router.get("/forecast")
async def get_forecast(days: int = 30, current_user: dict = Depends(get_current_user)):
    forecast = delay_predictor.forecast_volume(days=days)
    return {"forecast": forecast, "days": days}


@router.get("/fraud-alerts")
async def get_fraud_alerts(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(
        select(FraudScore, Application).join(Application, FraudScore.application_id == Application.id)
        .where(FraudScore.fraud_probability > 0.4).order_by(desc(FraudScore.fraud_probability)).limit(20)
    )
    alerts = []
    for fs, app in result.all():
        alerts.append({"application_id": app.id, "cert_type": app.cert_type, "fraud_probability": fs.fraud_probability,
                       "recommendation": fs.recommendation, "top_features": fs.top_features, "submitted_at": str(app.submitted_at)})
    return {"alerts": alerts}


@router.get("/sla-breaches")
async def get_sla_breaches(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(
        select(Application).where(Application.status.in_(["submitted", "processing", "officer_review"]),
                                  Application.predicted_days.isnot(None)).order_by(desc(Application.predicted_days)).limit(20)
    )
    return {"breaches": [{"id": a.id, "cert_type": a.cert_type, "status": a.status,
                           "predicted_days": a.predicted_days, "submitted_at": str(a.submitted_at)}
                          for a in result.scalars().all()]}
