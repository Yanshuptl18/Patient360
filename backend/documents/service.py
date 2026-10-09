"""Document upload, metadata persistence, and access management service."""

import logging
from datetime import date

from sqlalchemy.orm import Session

from backend.audit.service import log_audit_event
from backend.core.exceptions import AuthorizationError, EntityNotFoundError, Patient360Exception
from backend.documents.storage import DocumentStorage
from backend.documents.validator import validate_pdf_file
from backend.models.document import Document
from backend.models.user import User
from backend.patients.service import check_user_patient_access, get_patient

logger = logging.getLogger(__name__)


def upload_document(
    db: Session,
    storage: DocumentStorage,
    file_bytes: bytes,
    title: str,
    doc_type: str = "patient_record",
    doc_date: date | None = None,
    patient_id: str | None = None,
    current_user: User | None = None,
) -> tuple[Document, bool]:
    """
    Validates, deduplicates, stores, and registers a PDF document.
    Returns: (document_record, is_duplicate)
    """
    # 1. Validate PDF format and compute SHA-256
    is_valid, file_hash, err_msg = validate_pdf_file(file_bytes, filename=title)
    if not is_valid:
        raise Patient360Exception(
            message=err_msg,
            code="INVALID_DOCUMENT",
            status_code=400,
        )

    # 2. Enforce patient write permission if patient-linked
    if patient_id:
        get_patient(db, patient_id)  # verify existence
        if current_user and not check_user_patient_access(db, current_user, patient_id, min_permission="write"):
            raise AuthorizationError(f"User is not authorized to upload documents for patient '{patient_id}'.")

    # 3. Check for existing document with identical SHA-256 hash for this patient (Idempotency)
    existing = (
        db.query(Document)
        .filter(
            Document.file_hash_sha256 == file_hash,
            Document.patient_id == patient_id,
            Document.is_deleted.is_(False),
        )
        .first()
    )
    if existing:
        logger.info(f"Duplicate document detected (Hash: {file_hash[:8]}). Returning existing ID: {existing.id}")
        return existing, True

    # 4. Save physical file to storage
    rel_path = storage.save_file(file_bytes, file_hash)

    # 5. Insert document metadata record
    doc = Document(
        patient_id=patient_id,
        title=title,
        file_path=rel_path,
        file_hash_sha256=file_hash,
        file_size_bytes=len(file_bytes),
        mime_type="application/pdf",
        doc_type=doc_type,
        doc_date=doc_date,
        ingestion_status="pending",
        version=1,
        is_deleted=False,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 6. Audit log
    if current_user:
        log_audit_event(
            db,
            action="DOCUMENT_UPLOAD",
            resource_type="documents",
            user_id=current_user.id,
            resource_id=doc.id,
            patient_id=patient_id,
            status="SUCCESS",
            details={"title": title, "file_hash": file_hash, "size": len(file_bytes)},
        )

    logger.info(f"Registered document '{title}' (ID: {doc.id}, Hash: {file_hash[:8]})")
    return doc, False


def get_document(db: Session, document_id: str, current_user: User | None = None) -> Document:
    """Retrieves document record after verifying authorization."""
    doc = db.query(Document).filter(Document.id == document_id, Document.is_deleted.is_(False)).first()
    if not doc:
        raise EntityNotFoundError(f"Document with ID '{document_id}' not found.")

    # Enforce patient read permission if document is linked to a patient
    if doc.patient_id and current_user:
        if not check_user_patient_access(db, current_user, doc.patient_id, min_permission="read"):
            raise AuthorizationError(f"User is not authorized to access documents for patient '{doc.patient_id}'.")

    return doc


def list_documents_for_patient(
    db: Session,
    patient_id: str,
    current_user: User | None = None,
    doc_type: str | None = None,
) -> list[Document]:
    """Lists all active documents for a patient after verifying read permission."""
    get_patient(db, patient_id)

    if current_user and not check_user_patient_access(db, current_user, patient_id, min_permission="read"):
        raise AuthorizationError(f"User is not authorized to access documents for patient '{patient_id}'.")

    query = db.query(Document).filter(Document.patient_id == patient_id, Document.is_deleted.is_(False))
    if doc_type:
        query = query.filter(Document.doc_type == doc_type)

    return query.order_by(Document.created_at.desc()).all()


def delete_document(
    db: Session,
    storage: DocumentStorage,
    document_id: str,
    current_user: User,
) -> bool:
    """Soft deletes document record and removes physical file."""
    doc = get_document(db, document_id, current_user)

    if doc.patient_id and not check_user_patient_access(db, current_user, doc.patient_id, min_permission="write"):
        raise AuthorizationError("Write permission required to delete documents.")

    doc.is_deleted = True
    db.commit()

    # Unlink file from storage
    storage.delete_file(doc.file_path)

    log_audit_event(
        db,
        action="DOCUMENT_DELETED",
        resource_type="documents",
        user_id=current_user.id,
        resource_id=doc.id,
        patient_id=doc.patient_id,
        status="SUCCESS",
        details={"title": doc.title},
    )

    logger.info(f"Deleted document '{doc.title}' (ID: {doc.id})")
    return True
