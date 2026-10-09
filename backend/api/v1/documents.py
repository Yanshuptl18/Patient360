"""Document management and file upload API endpoints."""

import io
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user, get_db
from backend.core.exceptions import Patient360Exception
from backend.documents.service import (
    delete_document,
    get_document,
    list_documents_for_patient,
    upload_document,
)
from backend.documents.storage import get_storage
from backend.models.document import Document
from backend.models.user import User
from backend.schemas.document import DocumentResponse, DocumentUploadResponse

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_pdf_document(
    file: Annotated[UploadFile, File(description="Binary PDF file to upload")],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    patient_id: Annotated[str | None, Form()] = None,
    title: Annotated[str | None, Form()] = None,
    doc_type: Annotated[str, Form()] = "patient_record",
    doc_date: Annotated[date | None, Form()] = None,
) -> DocumentUploadResponse:
    """
    Accepts multipart upload of a PDF document:
    1. Validates file size (<= 25 MB).
    2. Validates magic bytes (%PDF-).
    3. Enforces server-side patient access authorization.
    4. Computes SHA-256 and handles idempotent duplicate uploads.
    5. Saves file to partitioned local storage.
    """
    file_bytes = await file.read()
    doc_title = title.strip() if title and title.strip() else (file.filename or "Untitled_Document.pdf")

    storage = get_storage()
    doc_record, is_duplicate = upload_document(
        db=db,
        storage=storage,
        file_bytes=file_bytes,
        title=doc_title,
        doc_type=doc_type,
        doc_date=doc_date,
        patient_id=patient_id,
        current_user=current_user,
    )

    msg = "Duplicate document detected; referenced existing record." if is_duplicate else "Document accepted and stored for indexing."

    return DocumentUploadResponse(
        document_id=doc_record.id,
        status=doc_record.ingestion_status,
        message=msg,
        file_hash_sha256=doc_record.file_hash_sha256,
        file_size_bytes=doc_record.file_size_bytes,
    )


@router.get("", response_model=list[DocumentResponse])
def get_documents(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    patient_id: Annotated[str | None, Query()] = None,
    doc_type: Annotated[str | None, Query()] = None,
) -> list[DocumentResponse]:
    """
    Lists documents authorized for the current user.
    If patient_id is provided, checks authorization for that patient.
    """
    if patient_id:
        docs = list_documents_for_patient(
            db, patient_id=patient_id, current_user=current_user, doc_type=doc_type
        )
    else:
        # If no patient_id specified and admin, return platform docs; otherwise return empty
        if current_user.role == "admin":
            query = db.query(Document).filter(Document.is_deleted.is_(False))
            if doc_type:
                query = query.filter(Document.doc_type == doc_type)
            docs = query.order_by(Document.created_at.desc()).all()
        else:
            docs = []

    return [DocumentResponse.model_validate(d) for d in docs]


@router.get("/{id}", response_model=DocumentResponse)
def get_document_by_id(
    id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentResponse:
    """Retrieves document metadata by ID, enforcing patient authorization."""
    doc = get_document(db, document_id=id, current_user=current_user)
    return DocumentResponse.model_validate(doc)


@router.get("/{id}/download")
def download_document_file(
    id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """
    Streams the original binary PDF file.
    Enforces server-side authorization check before reading disk.
    """
    doc = get_document(db, document_id=id, current_user=current_user)
    storage = get_storage()

    try:
        content = storage.read_file(doc.file_path)
    except FileNotFoundError as err:
        raise Patient360Exception(
            message="Document binary file missing from storage.",
            code="FILE_MISSING",
            status_code=404,
        ) from err

    headers = {
        "Content-Disposition": f'inline; filename="{doc.title}"',
        "Content-Type": doc.mime_type,
    }
    return StreamingResponse(io.BytesIO(content), media_type=doc.mime_type, headers=headers)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def remove_document(
    id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Soft deletes document and unlinks physical file from storage."""
    storage = get_storage()
    delete_document(db, storage=storage, document_id=id, current_user=current_user)
    return {"status": "DOCUMENT_DELETED"}
