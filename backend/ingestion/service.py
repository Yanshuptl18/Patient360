"""Document ingestion service coordinating extraction, normalization, and semantic chunking."""

import logging

from sqlalchemy.orm import Session

from backend.audit.service import log_audit_event
from backend.core.exceptions import Patient360Exception
from backend.documents.service import get_document
from backend.documents.storage import DocumentStorage
from backend.ingestion.chunker import SemanticChunker
from backend.ingestion.extractor import extract_pages_from_pdf
from backend.ingestion.normalizer import normalize_clinical_text
from backend.models.chunk import DocumentChunk
from backend.models.user import User
from backend.schemas.chunk import IngestionResponse

logger = logging.getLogger(__name__)


def ingest_document(
    db: Session,
    storage: DocumentStorage,
    document_id: str,
    current_user: User,
) -> IngestionResponse:
    """
    Executes the ingestion pipeline for a stored PDF document:
    1. Verifies authorization and updates status to 'processing'.
    2. Reads binary file from storage.
    3. Extracts pages using PyMuPDF.
    4. Normalizes clinical text preserving decimals and units.
    5. Chunks text with exact physical page provenance and context headers.
    6. Idempotently replaces existing chunks in the database.
    7. Updates status to 'completed' and writes audit log.
    """
    doc = get_document(db, document_id=document_id, current_user=current_user)

    # 1. Update status to 'processing'
    doc.ingestion_status = "processing"
    doc.error_message = None
    db.commit()
    db.refresh(doc)

    try:
        # 2. Read physical PDF binary
        pdf_bytes = storage.read_file(doc.file_path)

        # 3. Extract pages with PyMuPDF
        pages = extract_pages_from_pdf(pdf_bytes)

        # 4. Normalize clinical text for each page
        for page in pages:
            page.text = normalize_clinical_text(page.text)

        # 5. Chunk pages with SemanticChunker
        chunker = SemanticChunker(chunk_size=512, chunk_overlap=64)
        doc_date_str = doc.doc_date.isoformat() if doc.doc_date else None
        generated_chunks = chunker.chunk_pages(
            pages=pages,
            doc_title=doc.title,
            doc_date=doc_date_str,
            doc_type=doc.doc_type,
            patient_id=doc.patient_id,
        )

        # 6. Idempotently clear existing chunks for this document
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()

        # 7. Insert new chunks
        total_tokens = 0
        for gen in generated_chunks:
            chunk_rec = DocumentChunk(
                document_id=doc.id,
                chunk_index=gen.chunk_index,
                page_number=gen.page_number,
                content=gen.content,
                raw_content=gen.raw_content,
                token_count=gen.token_count,
                metadata_json=gen.metadata,
            )
            db.add(chunk_rec)
            total_tokens += gen.token_count

        # 8. Mark document completed
        doc.ingestion_status = "completed"
        doc.error_message = None
        db.commit()
        db.refresh(doc)

        # 9. Audit event
        log_audit_event(
            db,
            action="DOCUMENT_INGESTED",
            resource_type="documents",
            user_id=current_user.id,
            resource_id=doc.id,
            patient_id=doc.patient_id,
            status="SUCCESS",
            details={
                "chunk_count": len(generated_chunks),
                "total_tokens": total_tokens,
                "pages_processed": len(pages),
            },
        )

        logger.info(
            f"Document '{doc.title}' ({doc.id}) ingested: {len(generated_chunks)} chunks, "
            f"{total_tokens} tokens across {len(pages)} pages."
        )

        return IngestionResponse(
            document_id=doc.id,
            status="completed",
            chunk_count=len(generated_chunks),
            total_tokens=total_tokens,
            pages_processed=len(pages),
            message=f"Successfully extracted {len(generated_chunks)} semantic chunks across {len(pages)} pages.",
        )

    except Exception as err:
        logger.error(f"Failed to ingest document '{doc.title}' ({doc.id}): {err}", exc_info=True)
        doc.ingestion_status = "failed"
        doc.error_message = str(err)
        db.commit()

        log_audit_event(
            db,
            action="DOCUMENT_INGESTED",
            resource_type="documents",
            user_id=current_user.id,
            resource_id=doc.id,
            patient_id=doc.patient_id,
            status="FAILURE",
            details={"error": str(err)},
        )

        raise Patient360Exception(
            message=f"Document ingestion failed: {err}",
            code="INGESTION_FAILED",
            status_code=500,
        ) from err
