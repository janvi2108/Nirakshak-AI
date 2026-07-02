from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.schemas.rag import RAGQuery, RAGResponse, RAGSource
from app.services.rag_service import rag_service
from app.api.deps import get_current_user
import uuid

router = APIRouter()


@router.post("/query", response_model=RAGResponse)
async def query_rag(data: RAGQuery, current_user: dict = Depends(get_current_user)):
    if not data.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    result = rag_service.answer_query(query=data.query, language=data.language)
    return RAGResponse(
        answer=result["answer"],
        sources=[RAGSource(source_doc=s["source_doc"], chunk_text=s["chunk_text"], score=s["score"]) for s in result.get("sources", [])],
        session_id=data.session_id or str(uuid.uuid4()),
        language=result["language"],
    )


@router.post("/ingest")
async def ingest_document(
    source_name: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") not in ["admin", "officer"]:
        raise HTTPException(status_code=403, detail="Admin/Officer access required")
    content = await file.read()
    if file.filename.endswith(".pdf"):
        from app.services.preprocessing import pdf_to_images
        import pytesseract
        pages = pdf_to_images(content)
        texts = [pytesseract.image_to_string(page) for page in pages]
        text = " ".join(texts)
    else:
        text = content.decode("utf-8", errors="ignore")
    chunks = [text[i:i+512] for i in range(0, len(text), 400)]
    count = rag_service.add_documents(chunks, source_name)
    return {"message": f"Ingested {count} chunks from {source_name}", "source": source_name}


@router.get("/stats")
async def get_index_stats(current_user: dict = Depends(get_current_user)):
    return {"total_chunks": len(rag_service.chunks), "index_ready": rag_service.index is not None,
            "sources": list({c.get("source", "unknown") for c in rag_service.chunks})}
