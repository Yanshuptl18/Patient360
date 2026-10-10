"""Unit tests for hard bounded iteration ceiling (max 5) and execution timeout guards."""

from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.agents.graph import build_clinical_agent_graph
from backend.agents.service import AgentWorkflowService
from backend.agents.state import AgentWorkflowState
from backend.auth.service import get_user_by_email
from backend.models.patient import Patient, UserPatientPermission
from backend.schemas.agent import AgentRunRequest


def create_mock_patient_for_limits(db: Session, mrn: str, owner_id: str) -> Patient:
    patient = Patient(
        mrn_synthetic=mrn,
        first_name="Beatrice",
        last_name="Webb",
        date_of_birth=date(1975, 8, 20),
        gender="female",
        primary_condition="Hypertension",
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


def test_agent_run_request_schema_hard_ceiling() -> None:
    """Verifies Pydantic enforces max_iterations <= 5."""
    # Valid ceiling of 5
    valid_req = AgentRunRequest(patient_id="pat_123", query="Inquire clinical history", max_iterations=5)
    assert valid_req.max_iterations == 5

    # Exceeding 5 must raise ValidationError
    with pytest.raises(ValidationError):
        AgentRunRequest(patient_id="pat_123", query="Inquire clinical history", max_iterations=6)

    # Below 1 must raise ValidationError
    with pytest.raises(ValidationError):
        AgentRunRequest(patient_id="pat_123", query="Inquire clinical history", max_iterations=0)


def test_state_machine_halts_at_iteration_ceiling(db: Session) -> None:
    """Verifies state machine transitions to iteration_limit_reached when ceiling is hit."""
    reviewer = get_user_by_email(db, "reviewer@patient360.org")
    assert reviewer is not None
    patient = create_mock_patient_for_limits(db, "MRN-LIMIT-001", reviewer.id)

    graph = build_clinical_agent_graph(db, reviewer)

    # Simulate state already at or exceeding ceiling (e.g. max_iterations=1, iteration_count=1)
    import time
    state: AgentWorkflowState = {
        "run_id": "test_run_limit",
        "patient_id": patient.id,
        "user_id": reviewer.id,
        "query": "Assess medical conditions",
        "status": "planning",
        "approval_status": "pending",
        "iteration_count": 1,
        "max_iterations": 1,  # Ceiling is 1, already hit
        "start_time_seconds": time.time(),  # Current time so no timeout
        "timeout_seconds": 30.0,
        "elapsed_seconds": 0.0,
        "plan": [],
        "steps_executed": [],
        "patient_dossier": None,
        "retrieved_evidence": [],
        "contradictions_found": [],
        "draft_synthesis": None,
        "final_report": None,
        "clinician_feedback": None,
        "error_message": None,
    }

    result = graph.invoke(state)
    assert result["status"] == "iteration_limit_reached"
    assert "bounded iteration ceiling" in (result.get("error_message") or "").lower()



def test_state_machine_halts_on_timeout(db: Session) -> None:
    """Verifies state machine terminates when execution time exceeds timeout budget."""
    reviewer = get_user_by_email(db, "reviewer@patient360.org")
    assert reviewer is not None
    patient = create_mock_patient_for_limits(db, "MRN-TIMEOUT-001", reviewer.id)

    graph = build_clinical_agent_graph(db, reviewer)

    # State with start time 60 seconds in the past
    state: AgentWorkflowState = {
        "run_id": "test_run_timeout",
        "patient_id": patient.id,
        "user_id": reviewer.id,
        "query": "Assess medical conditions",
        "status": "planning",
        "approval_status": "pending",
        "iteration_count": 0,
        "max_iterations": 5,
        "start_time_seconds": 0.0,  # Far past -> timeout
        "timeout_seconds": 30.0,
        "elapsed_seconds": 0.0,
        "plan": [],
        "steps_executed": [],
        "patient_dossier": None,
        "retrieved_evidence": [],
        "contradictions_found": [],
        "draft_synthesis": None,
        "final_report": None,
        "clinician_feedback": None,
        "error_message": None,
    }

    result = graph.invoke(state)
    assert result["status"] == "timeout_exceeded"
    assert "Time budget" in (result.get("error_message") or "")



def test_service_clamps_max_iterations(db: Session) -> None:
    """Verifies AgentWorkflowService enforces bounds between 1 and 5."""
    reviewer = get_user_by_email(db, "reviewer@patient360.org")
    assert reviewer is not None
    patient = create_mock_patient_for_limits(db, "MRN-CLAMP-001", reviewer.id)

    service = AgentWorkflowService()
    snapshot = service.start_run(
        db=db,
        user=reviewer,
        patient_id=patient.id,
        query="Examine hypertension status",
        max_iterations=10,  # Clamped to 5
    )

    assert snapshot.max_iterations == 5
