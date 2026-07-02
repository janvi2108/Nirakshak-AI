"""Celery async tasks for heavy ML jobs."""
from celery import Celery
from app.config import settings

celery_app = Celery("nirakshak", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_expires = 3600


@celery_app.task(bind=True, max_retries=3)
def process_application_task(self, app_id: str, cert_type: str, district: str, doc_result: dict = None):
    try:
        from app.services.orchestrator import run_orchestrator
        return run_orchestrator(app_id, cert_type, district, doc_result)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=2)
def extract_document_task(self, document_id: str, file_key: str, doc_type: str):
    try:
        from app.services.storage_service import storage_service
        from app.services.ocr_service import process_document
        file_bytes = storage_service.download_file(file_key)
        filename = file_key.split("/")[-1]
        return process_document(file_bytes, filename, doc_type)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


@celery_app.task
def ingest_document_task(texts: list, source_name: str):
    from app.services.rag_service import rag_service
    return rag_service.add_documents(texts, source_name)
