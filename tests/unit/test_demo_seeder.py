"""Unit test for demonstration data seeder idempotency and integrity."""

from sqlalchemy.orm import Session

from backend.models.document import Document
from backend.models.patient import Patient
from backend.models.research import ResearchStudy
from backend.models.timeline import ClinicalEvent
from backend.models.user import User
from scripts.seed_demo_data import seed_demo_data


def test_seed_demo_data_idempotent(db: Session) -> None:
    """Tests that seed_demo_data populates patients, documents, events, and studies idempotently."""
    # Run seeder with existing test session
    seed_demo_data(override_session=db)

    # Validate personas
    users = db.query(User).all()
    assert len(users) >= 4
    emails = [u.email for u in users]
    assert "admin@patient360.org" in emails
    assert "reviewer@patient360.org" in emails
    assert "researcher@patient360.org" in emails

    # Validate synthetic cohort
    patients = db.query(Patient).all()
    assert len(patients) >= 4
    mrns = [p.mrn_synthetic for p in patients]
    assert "SYNTH-10001" in mrns
    assert "SYNTH-10002" in mrns
    assert "SYNTH-10003" in mrns
    assert "SYNTH-10004" in mrns

    # Validate documents
    docs = db.query(Document).all()
    assert len(docs) >= 7

    # Validate clinical events with contradictions
    events = db.query(ClinicalEvent).all()
    assert len(events) >= 7
    contradictions = [e for e in events if e.contradiction_flag]
    assert len(contradictions) >= 4  # Eleanor echo pair + Arthur allergy pair

    # Validate research studies
    studies = db.query(ResearchStudy).all()
    assert len(studies) >= 3
    pmids = [s.pmid for s in studies]
    assert "29151359" in pmids  # FLAURA
    assert "32865377" in pmids  # EMPEROR-Reduced
    assert "32970396" in pmids  # DAPA-CKD

    # Second run to verify idempotency (no duplicate key errors or crashes)
    seed_demo_data(override_session=db)
    assert len(db.query(Patient).all()) == len(patients)
    assert len(db.query(Document).all()) == len(docs)
    assert len(db.query(ClinicalEvent).all()) == len(events)
    assert len(db.query(ResearchStudy).all()) == len(studies)
