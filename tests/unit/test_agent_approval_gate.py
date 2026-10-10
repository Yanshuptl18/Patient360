"""Unit tests for Human-in-the-Loop clinician review gate and report certification."""

from datetime import date

import pytest
from sqlalchemy.orm import Session

from backend.agents.service import AgentWorkflowService
from backend.auth.service import get_user_by_email
from backend.core.exceptions import AuthorizationError, Patient360Exception
from backend.models.patient import Patient, UserPatientPermission


def create_mock_patient_for_approval(db: Session, mrn: str, owner_id: str) -> Patient:
    patient = Patient(
        mrn_synthetic=mrn,
        first_name="Clara",
        last_name="Oswald",
        date_of_birth=date(1989, 11, 23),
        gender="female",
        primary_condition="Chronic Kidney Disease",
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


def test_workflow_pauses_at_approval_gate(db: Session) -> None:
    """Verifies workflow stops at 'awaiting_approval' with draft synthesis and no final report."""
    reviewer = get_user_by_email(db, "reviewer@patient360.org")
    assert reviewer is not None
    patient = create_mock_patient_for_approval(db, "MRN-GATE-001", reviewer.id)

    service = AgentWorkflowService()
    snapshot = service.start_run(
        db=db,
        user=reviewer,
        patient_id=patient.id,
        query="Summarize renal function and nephrology findings",
    )

    assert snapshot.status == "awaiting_approval"
    assert snapshot.approval_status == "pending"
    assert snapshot.draft_synthesis is not None
    assert "Clinical Inquiry Draft Synthesis" in snapshot.draft_synthesis
    assert snapshot.final_report is None
    assert snapshot.iteration_count > 0


def test_clinician_approval_certifies_report(db: Session) -> None:
    """Verifies clinician approval transitions status to completed and produces certified final report."""
    reviewer = get_user_by_email(db, "reviewer@patient360.org")
    assert reviewer is not None
    patient = create_mock_patient_for_approval(db, "MRN-GATE-002", reviewer.id)

    service = AgentWorkflowService()
    snapshot = service.start_run(
        db=db,
        user=reviewer,
        patient_id=patient.id,
        query="Verify lab trends and clinical recommendations",
    )
    assert snapshot.status == "awaiting_approval"

    # Submit clinician approval
    response = service.review_run(
        db=db,
        user=reviewer,
        run_id=snapshot.run_id,
        approved=True,
        feedback="Verified against EHR source documents.",
    )

    assert response.status == "completed"
    assert response.approval_status == "approved"
    assert response.final_report is not None
    assert "Certified Clinical Intelligence Report" in response.final_report
    assert "Verified against EHR source documents." in response.final_report

    # Inspect updated snapshot
    updated_snapshot = service.get_run(db, reviewer, snapshot.run_id)
    assert updated_snapshot.status == "completed"
    assert updated_snapshot.approval_status == "approved"


def test_clinician_rejection_halts_workflow(db: Session) -> None:
    """Verifies clinician rejection transitions status to rejected and records reason."""
    reviewer = get_user_by_email(db, "reviewer@patient360.org")
    assert reviewer is not None
    patient = create_mock_patient_for_approval(db, "MRN-GATE-003", reviewer.id)

    service = AgentWorkflowService()
    snapshot = service.start_run(
        db=db,
        user=reviewer,
        patient_id=patient.id,
        query="Check contradictions in medication dosages",
    )
    assert snapshot.status == "awaiting_approval"

    # Submit rejection
    response = service.review_run(
        db=db,
        user=reviewer,
        run_id=snapshot.run_id,
        approved=False,
        feedback="Insufficient evidence excerpts provided for review.",
    )

    assert response.status == "rejected"
    assert response.approval_status == "rejected"
    assert response.final_report is None

    updated_snapshot = service.get_run(db, reviewer, snapshot.run_id)
    assert updated_snapshot.status == "rejected"
    assert updated_snapshot.approval_status == "rejected"


def test_cannot_review_non_awaiting_run(db: Session) -> None:
    """Verifies submitting a review for an already completed run raises 400 error."""
    reviewer = get_user_by_email(db, "reviewer@patient360.org")
    assert reviewer is not None
    patient = create_mock_patient_for_approval(db, "MRN-GATE-004", reviewer.id)

    service = AgentWorkflowService()
    snapshot = service.start_run(
        db=db,
        user=reviewer,
        patient_id=patient.id,
        query="Assess timeline",
    )

    # First review: approve
    service.review_run(db, reviewer, snapshot.run_id, approved=True)

    # Second review attempt must raise Patient360Exception
    with pytest.raises(Patient360Exception) as exc_info:
        service.review_run(db, reviewer, snapshot.run_id, approved=True)
    assert exc_info.value.status_code == 400
    assert "cannot be reviewed" in exc_info.value.message


def test_unauthorized_user_cannot_review_run(db: Session) -> None:
    """Verifies user without patient write permission cannot approve or reject runs."""
    reviewer = get_user_by_email(db, "reviewer@patient360.org")
    researcher = get_user_by_email(db, "researcher@patient360.org")
    assert reviewer is not None and researcher is not None
    patient = create_mock_patient_for_approval(db, "MRN-GATE-005", reviewer.id)

    service = AgentWorkflowService()
    snapshot = service.start_run(
        db=db,
        user=reviewer,
        patient_id=patient.id,
        query="Assess timeline",
    )

    with pytest.raises(AuthorizationError):
        service.review_run(db, researcher, snapshot.run_id, approved=True)
