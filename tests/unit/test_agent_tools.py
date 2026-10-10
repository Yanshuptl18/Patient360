"""Unit tests for read-only clinical agent tools and patient security boundaries."""

from datetime import date

import pytest
from sqlalchemy.orm import Session

from backend.agents.tools import (
    get_patient_dossier,
    inspect_clinical_contradictions,
    query_longitudinal_timeline,
    search_clinical_evidence,
)
from backend.auth.service import get_user_by_email
from backend.core.exceptions import AuthorizationError
from backend.models.patient import Patient, UserPatientPermission


def create_mock_patient(db: Session, mrn: str, owner_id: str) -> Patient:
    """Helper to create an active test patient with owner permissions."""
    patient = Patient(
        mrn_synthetic=mrn,
        first_name="Arthur",
        last_name="Pendelton",
        date_of_birth=date(1960, 5, 14),
        gender="male",
        primary_condition="Coronary Artery Disease",
        is_deleted=False,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    perm = UserPatientPermission(
        user_id=owner_id,
        patient_id=patient.id,
        permission_level="admin",
    )
    db.add(perm)
    db.commit()
    return patient


def test_get_patient_dossier_authorized_and_unauthorized(db: Session) -> None:
    """Verifies get_patient_dossier returns profile when authorized and raises AuthorizationError when not."""
    reviewer = get_user_by_email(db, "reviewer@patient360.org")
    researcher = get_user_by_email(db, "researcher@patient360.org")
    assert reviewer is not None and researcher is not None

    patient = create_mock_patient(db, "MRN-AGT-001", reviewer.id)

    # 1. Authorized read
    dossier = get_patient_dossier(db, reviewer, patient.id)
    assert dossier["patient_id"] == patient.id
    assert dossier["mrn_synthetic"] == "MRN-AGT-001"
    assert dossier["full_name"] == "Arthur Pendelton"
    assert dossier["primary_condition"] == "Coronary Artery Disease"
    assert isinstance(dossier["document_count"], int)

    # 2. Unauthorized read (researcher lacks access to reviewer's patient)
    with pytest.raises(AuthorizationError):
        get_patient_dossier(db, researcher, patient.id)


def test_search_clinical_evidence_access_boundary(db: Session) -> None:
    """Verifies search_clinical_evidence enforces server-side patient access control."""
    reviewer = get_user_by_email(db, "reviewer@patient360.org")
    researcher = get_user_by_email(db, "researcher@patient360.org")
    assert reviewer is not None and researcher is not None

    patient = create_mock_patient(db, "MRN-AGT-002", reviewer.id)

    # Authorized search (returns list, possibly empty if no chunks yet)
    results = search_clinical_evidence(db, reviewer, patient.id, query="chest pain", top_k=5)
    assert isinstance(results, list)

    # Unauthorized search raises AuthorizationError
    with pytest.raises(AuthorizationError):
        search_clinical_evidence(db, researcher, patient.id, query="chest pain", top_k=5)


def test_query_timeline_and_contradictions_access_boundary(db: Session) -> None:
    """Verifies timeline and contradiction tools enforce patient access boundary."""
    reviewer = get_user_by_email(db, "reviewer@patient360.org")
    researcher = get_user_by_email(db, "researcher@patient360.org")
    assert reviewer is not None and researcher is not None

    patient = create_mock_patient(db, "MRN-AGT-003", reviewer.id)

    # Authorized timeline query
    timeline_events = query_longitudinal_timeline(db, reviewer, patient.id)
    assert isinstance(timeline_events, list)

    # Authorized contradictions inspection
    contradictions = inspect_clinical_contradictions(db, reviewer, patient.id)
    assert isinstance(contradictions, list)

    # Unauthorized attempts raise AuthorizationError
    with pytest.raises(AuthorizationError):
        query_longitudinal_timeline(db, researcher, patient.id)

    with pytest.raises(AuthorizationError):
        inspect_clinical_contradictions(db, researcher, patient.id)
