from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.document import Document
from app.models.application import Application
from app.models.audit_log import AuditLog
from app.schemas.document import DocumentResponse, ExtractionResult
from app.services.storage_service import storage_service
from app.services.ocr_service import process_document
from app.services.rag_service import rag_service
from app.api.deps import get_current_user
import logging
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter()
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/jpg", "application/pdf"}


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    application_id: str = Form(...), doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Use JPEG, PNG, or PDF.")
    file_bytes = await file.read()
    if len(file_bytes) / (1024 * 1024) > 10:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")
    result = await db.execute(select(Application).where(Application.id == application_id, Application.citizen_id == current_user["user_id"]))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Application not found")
    upload_result = storage_service.upload_file(file_bytes, file.filename, file.content_type)
    document = Document(application_id=application_id, file_key=upload_result["file_key"], doc_type=doc_type)
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


@router.post("/{document_id}/extract", response_model=ExtractionResult)
async def extract_document(document_id: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    app_result = await db.execute(select(Application).where(Application.id == doc.application_id, Application.citizen_id == current_user["user_id"]))
    if not app_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        file_bytes = storage_service.download_file(doc.file_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not retrieve file: {str(e)}")
    filename = doc.file_key.split("/")[-1]
    ocr_result = process_document(file_bytes, filename, doc.doc_type)
    doc.extracted_json = {"fields": ocr_result["extracted_fields"], "raw_text_preview": ocr_result["raw_text"][:500],
                           "file_hash": ocr_result["file_hash"], "tamper_details": ocr_result.get("tamper_result", {})}
    doc.ocr_confidence = ocr_result["ocr_confidence"]
    doc.tamper_flag = ocr_result.get("tamper_detected", False)
    doc.doc_type = ocr_result["doc_type"]
    db.add(AuditLog(entity_type="document", entity_id=document_id, action="extracted",
                    actor=current_user["user_id"], detail=f"ocr_confidence={ocr_result['ocr_confidence']},tamper={doc.tamper_flag}"))
    await db.commit()

    source_name = f"document_{document_id}_{filename}"
    try:
        rag_service.add_documents([ocr_result["raw_text"]], source_name=source_name)
    except Exception as e:
        logger.warning(f"Failed to ingest extracted document into RAG index: {e}")

    return ExtractionResult(document_id=document_id, extracted_fields=ocr_result["extracted_fields"],
                            confidence_score=ocr_result["ocr_confidence"], tamper_detected=doc.tamper_flag,
                            raw_text=ocr_result["raw_text"][:1000])


@router.get("/{document_id}/url")
async def get_document_url(document_id: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"url": storage_service.get_presigned_url(doc.file_key), "expires_in": 3600}


@router.get("/application/{application_id}", response_model=List[DocumentResponse])
async def list_application_documents(application_id: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Document).where(Document.application_id == application_id))
    return result.scalars().all()
