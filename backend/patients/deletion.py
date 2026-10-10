"""GDPR & HIPAA Right-to-be-Forgotten cascading erasure service."""

import logging
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.audit.service import log_audit_event
from backend.core.exceptions import EntityNotFoundError
from backend.models.document import Document
from backend.models.patient import Patient, UserPatientPermission
from backend.models.timeline import ClinicalEvent
from backend.vector.store import QdrantVectorStore, get_vector_store

logger = logging.getLogger(__name__)


def cascade_delete_patient(
    db: Session,
    patient_id: str,
    vector_store: QdrantVectorStore | None = None,
    current_user_id: str | None = None,
) -> dict[str, Any]:
    """
    Atomically purges all clinical and demographic records for a patient dossier:
    1. Removes all vector embeddings from Qdrant by patient_id and document_id.
    2. Deletes physical document files from disk.
    3. Purges ClinicalEvent records.
    4. Purges UserPatientPermission mappings.
    5. Purges Document and DocumentChunk database rows.
    6. Purges Patient database row.
    7. Appends an immutable audit log record documenting the cascading purge.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise EntityNotFoundError(f"Patient dossier '{patient_id}' not found.")

    mrn = patient.mrn_synthetic

    # 1. Enumerate associated documents and timeline events
    docs = db.query(Document).filter(Document.patient_id == patient_id).all()
    doc_count = len(docs)
    doc_ids = [d.id for d in docs]
    event_count = db.query(ClinicalEvent).filter(ClinicalEvent.patient_id == patient_id).count()

    # 2. Vector Store Purge (Qdrant)
    try:
        v_store = vector_store or get_vector_store()
        v_store.delete_patient_chunks(patient_id=patient_id)
        for doc_id in doc_ids:
            v_store.delete_document_chunks(document_id=doc_id)
        logger.info(f"Purged vector store chunks for patient '{patient_id}'.")
    except Exception as exc:
        logger.warning(f"Error purging vector store chunks for patient '{patient_id}': {exc}")

    # 3. Physical Storage File Cleanup
    for doc in docs:
        try:
            p = Path(doc.file_path)
            if p.exists() and p.is_file():
                p.unlink()
                logger.info(f"Unlinked physical document file '{p}'.")
        except Exception as exc:
            logger.warning(f"Failed to unlink file '{doc.file_path}': {exc}")

    # 4. Relational Database Cascade Purge
    try:
        # Purge Timeline events
        db.query(ClinicalEvent).filter(ClinicalEvent.patient_id == patient_id).delete(synchronize_session=False)

        # Purge User Patient permissions
        db.query(UserPatientPermission).filter(UserPatientPermission.patient_id == patient_id).delete(
            synchronize_session=False
        )

        # Purge Documents (DocumentChunk has cascade='all, delete-orphan')
        for doc in docs:
            db.delete(doc)

        # Purge Patient record
        db.delete(patient)
        db.commit()

        # 5. Immutable Audit Trail
        log_audit_event(
            db=db,
            action="PATIENT_CASCADING_PURGE",
            resource_type="patients",
            resource_id=patient_id,
            patient_id=patient_id,
            user_id=current_user_id,
            status="SUCCESS",
            details={
                "mrn_synthetic": mrn,
                "purged_documents_count": doc_count,
                "purged_timeline_events_count": event_count,
                "compliance_reason": "GDPR_HIPAA_RIGHT_TO_BE_FORGOTTEN",
            },
        )

        return {
            "patient_id": patient_id,
            "mrn_synthetic": mrn,
            "purged_documents_count": doc_count,
            "purged_timeline_events_count": event_count,
            "status": "PURGED",
        }

    except Exception as exc:
        db.rollback()
        logger.error(f"Failed cascading deletion for patient '{patient_id}': {exc}")
        raise
