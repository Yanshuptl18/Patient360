"""PostgreSQL database lifecycle, constraint integrity, cascading, and transaction tests."""

import json
import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.audit.service import log_audit_event
from backend.models.audit import AuditLog
from backend.models.chunk import DocumentChunk
from backend.models.document import Document
from backend.models.job import IngestionJob
from backend.models.patient import Patient
from backend.models.user import User


def test_patient_mrn_uniqueness_and_lifecycle(db: Session) -> None:
    """Tests synthetic MRN unique constraint enforcement and rollback on duplicate."""
    mrn = f"SYNTH-TEST-{uuid.uuid4().hex[:6].upper()}"

    p1 = Patient(
        id=str(uuid.uuid4()),
        mrn_synthetic=mrn,
        first_name="Arthur",
        last_name="Pendleton",
        date_of_birth=date(1960, 3, 15),
        gender="Male",
        primary_condition="Essential Hypertension",
    )
    db.add(p1)
    db.commit()
    db.refresh(p1)
    assert p1.id is not None

    # Attempt duplicate MRN
    p2 = Patient(
        id=str(uuid.uuid4()),
        mrn_synthetic=mrn,
        first_name="Dupe",
        last_name="Record",
        date_of_birth=date(1975, 1, 1),
        gender="Female",
    )
    db.add(p2)
    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()

    # Verify original record survived intact
    retrieved = db.query(Patient).filter(Patient.mrn_synthetic == mrn).first()
    assert retrieved is not None
    assert retrieved.first_name == "Arthur"

    # Cleanup
    db.delete(retrieved)
    db.commit()


def test_document_chunk_cascade_deletion(db: Session) -> None:
    """Verifies that deleting a Document cascades to all of its DocumentChunks."""
    patient = Patient(
        id=str(uuid.uuid4()),
        mrn_synthetic=f"SYNTH-CASCADE-{uuid.uuid4().hex[:6].upper()}",
        first_name="Beatrice",
        last_name="Webb",
        date_of_birth=date(1982, 11, 20),
        gender="Female",
    )
    db.add(patient)
    db.commit()

    doc = Document(
        id=str(uuid.uuid4()),
        patient_id=patient.id,
        title="Cascade_Test_Document.pdf",
        file_path="/storage/test/Cascade_Test_Document.pdf",
        file_hash_sha256=f"hash-{uuid.uuid4().hex}",
        file_size_bytes=51200,
        mime_type="application/pdf",
        doc_type="clinical_note",
        ingestion_status="completed",
        version=1,
    )
    db.add(doc)
    db.commit()

    chunk1 = DocumentChunk(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        page_number=1,
        chunk_index=0,
        content="Patient presents with persistent cough.",
        raw_content="Patient presents with persistent cough.",
        token_count=6,
    )
    chunk2 = DocumentChunk(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        page_number=2,
        chunk_index=1,
        content="Chest radiography demonstrates clear lung fields.",
        raw_content="Chest radiography demonstrates clear lung fields.",
        token_count=7,
    )
    db.add_all([chunk1, chunk2])
    db.commit()

    # Verify chunks exist
    chunks_before = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
    assert len(chunks_before) == 2

    # Delete Document and verify chunks are cascade-deleted
    db.delete(doc)
    db.commit()

    chunks_after = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
    assert len(chunks_after) == 0

    # Cleanup patient
    db.delete(patient)
    db.commit()


def test_transaction_rollback_preserves_clean_session(db: Session) -> None:
    """Verifies that an error rolled back inside a transaction does not corrupt subsequent operations."""
    unique_email = f"clean-{uuid.uuid4().hex[:8]}@example.com"

    # Start a block that fails
    try:
        invalid_user = User(
            id=str(uuid.uuid4()),
            email=None,  # Nullable=False violation
            hashed_password="hashed_pw_test",
            full_name="Broken User",
            role="doctor",
        )
        db.add(invalid_user)
        db.commit()
    except IntegrityError:
        db.rollback()

    # Subsequent valid operation in the same session must succeed smoothly
    valid_user = User(
        id=str(uuid.uuid4()),
        email=unique_email,
        hashed_password="hashed_pw_test",
        full_name="Clean User",
        role="doctor",
        is_active=True,
    )
    db.add(valid_user)
    db.commit()
    db.refresh(valid_user)

    assert valid_user.id is not None
    assert valid_user.email == unique_email

    # Cleanup
    db.delete(valid_user)
    db.commit()


def test_ingestion_job_state_transitions(db: Session) -> None:
    """Tests IngestionJob state lifecycle from queued -> processing -> completed."""
    job_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())

    job = IngestionJob(
        id=job_id,
        document_id=doc_id,
        status="queued",
        attempts=0,
        max_attempts=3,
        error_message=None,
    )
    db.add(job)
    db.commit()

    # Transition to processing
    job.status = "processing"
    db.commit()

    retrieved = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    assert retrieved is not None
    assert retrieved.status == "processing"

    # Transition to completed
    retrieved.status = "completed"
    retrieved.attempts = 1
    db.commit()

    final = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    assert final is not None
    assert final.status == "completed"
    assert final.attempts == 1

    # Cleanup
    db.delete(final)
    db.commit()


def test_audit_log_append_only_persistence(db: Session) -> None:
    """Tests that audit log entries are appended and queryable by action and timestamp."""
    action_name = f"TEST_AUDIT_ACTION_{uuid.uuid4().hex[:6]}"

    log_entry = log_audit_event(
        db=db,
        action=action_name,
        user_id="usr-system-admin",
        patient_id="pat-10001",
        resource_type="patient_record",
        resource_id="doc-999",
        details={"status": "verified", "test": True},
        ip_address="127.0.0.1",
    )

    assert log_entry.id is not None

    found = db.query(AuditLog).filter(AuditLog.action == action_name).first()
    assert found is not None
    assert found.resource_type == "patient_record"
    details_parsed = json.loads(found.details_json or "{}")
    assert details_parsed.get("test") is True

    # Cleanup
    db.delete(found)
    db.commit()
