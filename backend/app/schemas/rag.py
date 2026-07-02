from pydantic import BaseModel
from typing import Optional, List


class RAGQuery(BaseModel):
    query: str
    language: str = "en"
    session_id: Optional[str] = None


class RAGSource(BaseModel):
    source_doc: str
    chunk_text: str
    score: float


class RAGResponse(BaseModel):
    answer: str
    sources: List[RAGSource]
    session_id: Optional[str] = None
    language: str


class IngestRequest(BaseModel):
    source_name: str
