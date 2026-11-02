"""Asynchronous document ingestion job orchestration with persistent state and retry handling."""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.audit.service import log_audit_event
from backend.core.database import SessionLocal
from backend.core.exceptions import EntityNotFoundError
from backend.documents.service import get_document
from backend.documents.storage import DocumentStorage, get_storage
from backend.ingestion.service import ingest_document
from backend.models.job import IngestionJob
from backend.models.user import User

logger = logging.getLogger(__name__)

# Bounded thread pool for asynchronous background ingestion workers
_job_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ingestion-worker")


def enqueue_ingestion_job(
    db: Session,
    storage: DocumentStorage,
    document_id: str,
    current_user: User,
) -> IngestionJob:
    """
    Idempotently enqueues an asynchronous document ingestion job:
    1. Verifies authorization for the target document.
    2. Checks for existing queued or running jobs to prevent duplicates.
    3. Persists IngestionJob record with status 'queued'.
    4. Dispatches background execution to the worker pool.
    """
    doc = get_document(db, document_id=document_id, current_user=current_user)

    # Prevent duplicate active jobs
    existing_active = (
        db.query(IngestionJob)
        .filter(
            IngestionJob.document_id == doc.id,
            IngestionJob.status.in_(["queued", "processing"]),
        )
        .first()
    )
    if existing_active:
        logger.info(f"Returning existing active ingestion job {existing_active.id} for doc {doc.id}")
        return existing_active

    job = IngestionJob(
        document_id=doc.id,
        patient_id=doc.patient_id,
        status="queued",
        attempts=0,
        max_attempts=3,
        error_message=None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch to background thread pool
    _job_executor.submit(_execute_background_job, job.id, doc.id, current_user.id)

    log_audit_event(
        db,
        action="DOCUMENT_INGESTION_QUEUED",
        resource_type="documents",
        user_id=current_user.id,
        resource_id=doc.id,
        patient_id=doc.patient_id,
        status="SUCCESS",
        details={"job_id": job.id},
    )

    return job


def _execute_background_job(job_id: str, document_id: str, user_id: str) -> None:
    """Worker task executed in background thread with an isolated database session."""
    worker_db: Session = SessionLocal()
    try:
        job = worker_db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        user = worker_db.query(User).filter(User.id == user_id).first()
        if not job or not user:
            return

        job.status = "processing"
        job.attempts += 1
        job.updated_at = datetime.now(UTC)
        worker_db.commit()

        storage = get_storage()
        ingest_document(
            db=worker_db,
            storage=storage,
            document_id=document_id,
            current_user=user,
        )

        job.status = "completed"
        job.error_message = None
        job.updated_at = datetime.now(UTC)
        worker_db.commit()
        logger.info(f"Asynchronous ingestion job {job_id} for doc {document_id} completed successfully.")

    except Exception as exc:
        logger.error(f"Asynchronous ingestion job {job_id} failed: {exc}", exc_info=True)
        try:
            worker_db.rollback()
            job = worker_db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
            if job:
                job.error_message = str(exc)
                if job.attempts >= job.max_attempts:
                    job.status = "dead_letter"
                else:
                    job.status = "failed"
                job.updated_at = datetime.now(UTC)
                worker_db.commit()
        except Exception as update_err:
            logger.error(f"Could not update failed job status for {job_id}: {update_err}")
    finally:
        worker_db.close()


def get_ingestion_job(db: Session, job_id: str, current_user: User) -> IngestionJob:
    """Retrieves status and metadata of an ingestion job, enforcing document authorization."""
    job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    if not job:
        raise EntityNotFoundError(f"Ingestion job '{job_id}' not found.")
    # Check document authorization
    get_document(db, document_id=job.document_id, current_user=current_user)
    return job


def retry_ingestion_job(
    db: Session,
    storage: DocumentStorage,
    job_id: str,
    current_user: User,
) -> IngestionJob:
    """Idempotently resets and retries a failed or dead-letter job."""
    job = get_ingestion_job(db, job_id=job_id, current_user=current_user)

    if job.status in ("queued", "processing"):
        return job

    job.status = "queued"
    job.error_message = None
    job.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(job)

    _job_executor.submit(_execute_background_job, job.id, job.document_id, current_user.id)

    log_audit_event(
        db,
        action="DOCUMENT_INGESTION_RETRIED",
        resource_type="documents",
        user_id=current_user.id,
        resource_id=job.document_id,
        patient_id=job.patient_id,
        status="SUCCESS",
        details={"job_id": job.id, "attempt": job.attempts},
    )

    return job
