from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.api.routes import applications, documents, complaints, fraud, rag, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="NIRAKSHAK-AI", description="Intelligent Multi-Agent e-Governance Platform", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:8080"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(complaints.router, prefix="/api/complaints", tags=["Complaints"])
app.include_router(fraud.router, prefix="/api/fraud", tags=["Fraud"])
app.include_router(rag.router, prefix="/api/rag", tags=["RAG"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "nirakshak-ai"}
