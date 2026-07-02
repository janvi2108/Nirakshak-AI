# NIRAKSHAK-AI — Intelligent Multi-Agent e-Governance Platform

A multi-agent AI platform for certificate processing with document intelligence, complaint classification, fraud detection, delay prediction, and a RAG-powered citizen assistant.

## Tech Stack

**Backend:** Python, FastAPI, PostgreSQL, Redis, Celery
**ML:** XGBoost, LightGBM, Prophet, PyTorch, HuggingFace Transformers, SHAP
**GenAI:** LangChain, LangGraph, FAISS, OpenAI
**Frontend:** React, Tailwind CSS
**Infra:** Docker, Docker Compose, MLflow, MinIO

## Architecture

```
Citizen Portal (React) 
        ↓
FastAPI Gateway (Auth, Routing)
        ↓
┌───────────────────────────────────────────┐
│  Multi-Agent AI Core (LangGraph)           │
│  - Document Intelligence (OCR + LayoutLM)  │
│  - Complaint Classifier (mBERT + LightGBM) │
│  - Fraud Detection (XGBoost + SHAP)        │
│  - Delay Predictor (XGBoost + Prophet)     │
│  - RAG Assistant (LangChain + FAISS)       │
└───────────────────────────────────────────┘
        ↓
PostgreSQL + MinIO (S3) + MLflow
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for ML training scripts)
- Node.js 18+ (for frontend dev, optional — runs in Docker too)

### 1. Clone and configure

```bash
cp .env.example .env
```

### 2. Start the stack

```bash
docker-compose up -d --build
```

This starts: PostgreSQL, Redis, MinIO, MLflow, FastAPI, and Celery worker.

Check everything is running:
```bash
docker-compose ps
curl http://localhost:8000/health
```

### 3. Generate training data and train ML models

```bash
pip install -r backend/requirements.txt

# Generate synthetic complaint data
python ml/data/generate_complaints.py

# Train models (each logs to MLflow at http://localhost:5000)
python ml/training/train_complaint.py
python ml/training/train_fraud.py
python ml/training/train_delay.py
```

### 4. Build the RAG index

Add `.txt` or `.pdf` government documents to `ml/data/raw/` (sample docs included), then:

```bash
python ml/pipelines/ingest_docs.py
```

### 5. Restart backend to pick up trained models

```bash
docker-compose restart fastapi
```

### 6. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

## Service URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API Docs (Swagger) | http://localhost:8000/docs |
| MLflow | http://localhost:5000 |
| MinIO Console | http://localhost:9001 (minioadmin / minioadmin123) |

## Project Structure

```
nirakshak-ai/
├── backend/        # FastAPI app, models, services, tests
├── ml/             # Training scripts, notebooks, pipelines, artifacts
├── frontend/       # React + Tailwind portal
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Running Tests

```bash
docker-compose exec fastapi pytest tests/ -v
```

## Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/applications/register` | Register citizen |
| POST | `/api/applications/login` | Login |
| POST | `/api/applications/` | Submit application |
| POST | `/api/applications/{id}/process` | Run full ML pipeline |
| POST | `/api/documents/upload` | Upload document |
| POST | `/api/documents/{id}/extract` | OCR + field extraction |
| POST | `/api/complaints/` | Submit complaint (Hindi/English) |
| POST | `/api/fraud/score/{app_id}` | Run fraud detection |
| POST | `/api/rag/query` | Ask the citizen assistant |
| GET | `/api/admin/dashboard` | Admin stats |
| GET | `/api/admin/forecast` | Volume forecast |

## Environment Variables

See `.env.example` for all required variables: database, Redis, MinIO, JWT secret, MLflow URI, and OpenAI API key (for GenAI features).

## Notes

- All ML services have rule-based fallbacks — the API works immediately even before training models.
- PII (Aadhaar, phone, email) is stripped before any LLM call.
- Fraud explanations use SHAP values for officer-facing transparency.
