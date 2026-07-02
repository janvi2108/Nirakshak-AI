from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.application import Application
from app.models.citizen import Citizen
from app.models.audit_log import AuditLog
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationDetail
from app.schemas.auth import CitizenRegister, TokenResponse, LoginRequest
from app.services.auth_service import get_or_create_citizen, create_access_token, login_citizen
from app.api.deps import get_current_user
from typing import List

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register_citizen(data: CitizenRegister, db: AsyncSession = Depends(get_db)):
    citizen = await get_or_create_citizen(db, data.name, data.phone, data.district, data.aadhaar_last4, data.email)
    token = create_access_token(citizen.id, role="citizen")
    return {"access_token": token, "token_type": "bearer", "user_id": citizen.id, "role": "citizen"}


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await login_citizen(db, data.phone, data.aadhaar_last4)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Citizen not found. Please register first.")
    return result


@router.post("/", response_model=ApplicationDetail, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Citizen).where(Citizen.id == current_user["user_id"]))
    citizen = result.scalar_one_or_none()
    if not citizen:
        raise HTTPException(status_code=404, detail="Citizen not found")
    application = Application(citizen_id=citizen.id, cert_type=data.cert_type.value, status="submitted")
    db.add(application)
    await db.flush()
    audit = AuditLog(entity_type="application", entity_id=application.id, action="created",
                     actor=citizen.id, detail=f"cert_type={data.cert_type.value}")
    db.add(audit)
    await db.commit()
    await db.refresh(application)
    return application


@router.post("/{application_id}/process")
async def process_application(
    application_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Trigger full ML pipeline: fraud + delay + brief."""
    result = await db.execute(select(Application).where(
        Application.id == application_id, Application.citizen_id == current_user["user_id"]))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    from app.services.orchestrator import run_orchestrator
    state = run_orchestrator(application.id, application.cert_type,
                              getattr(application, "district", "unknown"))
    application.status = state["decision"].replace("auto_", "") if "auto_" in state.get("decision", "") else state.get("decision", "submitted")
    if state.get("decision") == "auto_approve":
        application.status = "approved"
    elif state.get("decision") == "auto_reject":
        application.status = "rejected"
    else:
        application.status = "officer_review"
    if state.get("delay_result"):
        application.predicted_days = state["delay_result"].get("predicted_days")
    if state.get("fraud_result"):
        application.fraud_recommendation = state["fraud_result"].get("recommendation")
    if state.get("officer_brief"):
        application.officer_brief = state["officer_brief"]
    from app.models.fraud_score import FraudScore
    if state.get("fraud_result"):
        fr = state["fraud_result"]
        fraud_score = FraudScore(
            application_id=application.id,
            fraud_probability=fr.get("fraud_probability", 0),
            anomaly_score=fr.get("anomaly_score", 0),
            top_features=fr.get("top_features", []),
            recommendation=fr.get("recommendation", "pass"),
            model_version=fr.get("model_version", "v1.0"),
        )
        db.add(fraud_score)
    audit = AuditLog(entity_type="application", entity_id=application.id, action="processed",
                     actor=current_user["user_id"], detail=f"decision={state.get('decision')}")
    db.add(audit)
    await db.commit()
    return {"application_id": application_id, "decision": state.get("decision"),
            "fraud_probability": state.get("fraud_result", {}).get("fraud_probability"),
            "predicted_days": state.get("delay_result", {}).get("predicted_days"),
            "officer_brief": state.get("officer_brief")}


@router.get("/", response_model=List[ApplicationResponse])
async def list_my_applications(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Application).where(Application.citizen_id == current_user["user_id"]).order_by(desc(Application.submitted_at)))
    return result.scalars().all()


@router.get("/{application_id}", response_model=ApplicationDetail)
async def get_application(application_id: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Application).where(Application.id == application_id, Application.citizen_id == current_user["user_id"]))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app
