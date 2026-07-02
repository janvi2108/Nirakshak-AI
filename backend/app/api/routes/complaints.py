from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.complaint import Complaint
from app.models.audit_log import AuditLog
from app.schemas.complaint import ComplaintCreate, ComplaintResponse, ComplaintDetail, ComplaintClassifyResult
from app.services.complaint_service import complaint_classifier
from app.api.deps import get_current_user
from typing import List

router = APIRouter()


@router.post("/", response_model=ComplaintDetail, status_code=status.HTTP_201_CREATED)
async def submit_complaint(data: ComplaintCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    classification = complaint_classifier.classify(data.text)
    language = complaint_classifier.detect_language(data.text)
    complaint = Complaint(citizen_id=current_user["user_id"], raw_text=data.text,
                          category=classification["category"], department=classification["department"],
                          urgency_score=classification["urgency_score"], sla_risk=classification["sla_risk"])
    db.add(complaint)
    await db.flush()
    db.add(AuditLog(entity_type="complaint", entity_id=complaint.id, action="submitted",
                    actor=current_user["user_id"], detail=f"category={classification['category']},urgency={classification['urgency_score']}"))
    await db.commit()
    await db.refresh(complaint)
    return ComplaintDetail(
        id=complaint.id, citizen_id=complaint.citizen_id, raw_text=complaint.raw_text,
        category=complaint.category, department=complaint.department, urgency_score=complaint.urgency_score,
        sla_risk=complaint.sla_risk, draft_response=complaint.draft_response,
        resolved_at=complaint.resolved_at, created_at=complaint.created_at,
        classification=ComplaintClassifyResult(category=classification["category"], department=classification["department"],
            urgency_score=classification["urgency_score"], sla_risk=classification["sla_risk"], language=language,
            confidence=classification.get("confidence"), method=classification.get("method", "rule_based")),
    )


@router.get("/", response_model=List[ComplaintResponse])
async def list_my_complaints(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Complaint).where(Complaint.citizen_id == current_user["user_id"]).order_by(desc(Complaint.created_at)))
    return result.scalars().all()


@router.get("/{complaint_id}", response_model=ComplaintDetail)
async def get_complaint(complaint_id: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id, Complaint.citizen_id == current_user["user_id"]))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return ComplaintDetail(id=complaint.id, citizen_id=complaint.citizen_id, raw_text=complaint.raw_text,
        category=complaint.category, department=complaint.department, urgency_score=complaint.urgency_score,
        sla_risk=complaint.sla_risk, draft_response=complaint.draft_response,
        resolved_at=complaint.resolved_at, created_at=complaint.created_at)
