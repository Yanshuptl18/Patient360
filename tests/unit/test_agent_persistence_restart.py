"""Tests for durable agent workflow persistence across restarts and RBAC approval barriers."""

from datetime import date

import pytest
from sqlalchemy.orm import Session

from backend.agents.service import AgentWorkflowService
from backend.auth.service import get_user_by_email
from backend.core.exceptions import AuthorizationError
from backend.models.patient import Patient, UserPatientPermission


def create_test_patient(db: Session, mrn: str, owner_id: str) -> Patient:
    patient = Patient(
        mrn_synthetic=mrn,
        first_name="Arthur",
        last_name="Pendleton",
        date_of_birth=date(1975, 4, 12),
        gender="male",
        primary_condition="Ischemic Cardiomyopathy",
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


def test_agent_workflow_survives_restart(db: Session) -> None:
    """Verifies workflow persisted to DB is retrievable by a brand-new service instance."""
    reviewer = get_user_by_email(db, "reviewer@patient360.org")
    assert reviewer is not None
    patient = create_test_patient(db, "MRN-RESTART-001", reviewer.id)

    # Instance 1: start workflow
    service1 = AgentWorkflowService()
    snapshot = service1.start_run(
        db=db,
        user=reviewer,
        patient_id=patient.id,
        query="Analyze ejection fraction timeline and heart failure markers",
    )
    run_id = snapshot.run_id
    assert snapshot.status == "awaiting_approval"

    # Simulate server restart by creating completely new service instance
    service2 = AgentWorkflowService()
    restored = service2.get_run(db=db, user=reviewer, run_id=run_id)

    assert restored.run_id == run_id
    assert restored.patient_id == patient.id
    assert restored.status == "awaiting_approval"
    assert restored.approval_status == "pending"
    assert restored.draft_synthesis is not None
    assert len(restored.steps) >= 3


def test_patient_role_cannot_approve_clinical_reports(db: Session) -> None:
    """Verifies patients cannot approve or certify research reports even for their own dossier."""
    reviewer = get_user_by_email(db, "reviewer@patient360.org")
    patient_user = get_user_by_email(db, "patient@patient360.org")
    assert reviewer is not None and patient_user is not None

    patient = create_test_patient(db, "MRN-RESTART-002", reviewer.id)

    # Grant patient write permission to test strict role enforcement
    perm = UserPatientPermission(
        user_id=patient_user.id,
        patient_id=patient.id,
        permission_level="admin",
    )
    db.add(perm)
    db.commit()

    service = AgentWorkflowService()
    snapshot = service.start_run(
        db=db,
        user=reviewer,
        patient_id=patient.id,
        query="Synthesize cardiac history",
    )

    # Attempt approval with patient role must be rejected
    with pytest.raises(AuthorizationError) as exc_info:
        service.review_run(
            db=db,
            user=patient_user,
            run_id=snapshot.run_id,
            approved=True,
            feedback="Patient self-approval attempt",
        )
    assert "Patients are strictly prohibited" in str(exc_info.value)
