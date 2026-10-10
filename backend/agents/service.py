"""Clinical Agent Workflow orchestration service."""

import datetime
import logging
import time
import uuid
from typing import TypedDict, cast

from sqlalchemy.orm import Session

from backend.agents.graph import build_clinical_agent_graph
from backend.agents.state import AgentWorkflowState
from backend.audit.service import log_audit_event
from backend.core.exceptions import (
    AuthorizationError,
    EntityNotFoundError,
    Patient360Exception,
)
from backend.models.user import User
from backend.patients.service import check_user_patient_access
from backend.schemas.agent import (
    AgentApprovalResponse,
    AgentRunSnapshot,
    WorkflowStepLog,
)

logger = logging.getLogger(__name__)


class AgentRunRecord(TypedDict):
    """Storage record for in-memory and persistent workflow cache."""

    state: AgentWorkflowState
    created_at: datetime.datetime
    updated_at: datetime.datetime


class AgentWorkflowService:
    """Manages bounded clinical inquiry workflow runs and human review checkpoints."""

    def __init__(self) -> None:
        self._runs: dict[str, AgentRunRecord] = {}


    def _state_to_snapshot(
        self,
        state: AgentWorkflowState,
        created_at: datetime.datetime,
        updated_at: datetime.datetime,
    ) -> AgentRunSnapshot:
        dossier = state.get("patient_dossier") or {}
        patient_name = dossier.get("full_name")
        steps = [WorkflowStepLog(**s) for s in state.get("steps_executed", [])]
        evidence = state.get("retrieved_evidence", [])
        contradictions = state.get("contradictions_found", [])

        return AgentRunSnapshot(
            run_id=state["run_id"],
            patient_id=state["patient_id"],
            patient_name=patient_name,
            query=state["query"],
            status=state.get("status", "planning"),
            iteration_count=state.get("iteration_count", 0),
            max_iterations=state.get("max_iterations", 5),
            elapsed_seconds=state.get("elapsed_seconds", 0.0),
            plan=state.get("plan", []),
            steps=steps,
            retrieved_evidence_count=len(evidence),
            contradictions_found=contradictions,
            draft_synthesis=state.get("draft_synthesis"),
            final_report=state.get("final_report"),
            approval_status=state.get("approval_status", "pending"),
            clinician_feedback=state.get("clinician_feedback"),
            error_message=state.get("error_message"),
            created_at=created_at,
            updated_at=updated_at,
        )

    def start_run(
        self,
        db: Session,
        user: User,
        patient_id: str,
        query: str,
        max_iterations: int = 5,
        timeout_seconds: float = 30.0,
    ) -> AgentRunSnapshot:
        """
        Initiates a bounded clinical inquiry workflow.
        Guarded by read-access authorization check.
        """
        if not check_user_patient_access(db, user=user, patient_id=patient_id, min_permission="read"):
            raise AuthorizationError(f"Access denied: user '{user.id}' lacks permission for patient '{patient_id}'.")

        run_id = f"run_{uuid.uuid4().hex[:12]}"
        bounded_max_iterations = min(max(1, max_iterations), 5)  # Enforce hard ceiling of 5
        now = datetime.datetime.now(datetime.UTC)

        initial_state: AgentWorkflowState = {
            "run_id": run_id,
            "patient_id": patient_id,
            "user_id": user.id,
            "query": query,
            "status": "planning",
            "approval_status": "pending",
            "iteration_count": 0,
            "max_iterations": bounded_max_iterations,
            "start_time_seconds": time.time(),
            "timeout_seconds": timeout_seconds,
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

        # Build and invoke graph
        graph = build_clinical_agent_graph(db, user)
        executed_state: AgentWorkflowState = cast(AgentWorkflowState, graph.invoke(initial_state))

        record: AgentRunRecord = {
            "state": executed_state,
            "created_at": now,
            "updated_at": datetime.datetime.now(datetime.UTC),
        }
        self._runs[run_id] = record


        log_audit_event(
            db=db,
            action="AGENT_RUN_INITIATED",
            resource_type="agent_run",
            user_id=user.id,
            resource_id=run_id,
            patient_id=patient_id,
            details={
                "query": query,
                "status": executed_state.get("status"),
                "iterations": executed_state.get("iteration_count"),
            },
        )

        return self._state_to_snapshot(
            executed_state,
            record["created_at"],
            record["updated_at"],
        )

    def get_run(
        self,
        db: Session,
        user: User,
        run_id: str,
    ) -> AgentRunSnapshot:
        """Retrieves snapshot of a specific workflow run."""
        record = self._runs.get(run_id)
        if not record:
            raise EntityNotFoundError(f"Agent run '{run_id}' not found.")

        state: AgentWorkflowState = record["state"]
        if not check_user_patient_access(db, user=user, patient_id=state["patient_id"], min_permission="read"):
            raise AuthorizationError(f"Access denied: user '{user.id}' lacks permission for patient '{state['patient_id']}'.")

        return self._state_to_snapshot(state, record["created_at"], record["updated_at"])

    def list_runs_for_patient(
        self,
        db: Session,
        user: User,
        patient_id: str,
    ) -> list[AgentRunSnapshot]:
        """Lists all agent runs executed for the specified patient."""
        if not check_user_patient_access(db, user=user, patient_id=patient_id, min_permission="read"):
            raise AuthorizationError(f"Access denied: user '{user.id}' lacks permission for patient '{patient_id}'.")

        patient_runs = [
            self._state_to_snapshot(rec["state"], rec["created_at"], rec["updated_at"])
            for rec in self._runs.values()
            if rec["state"]["patient_id"] == patient_id
        ]
        # Return newest first
        patient_runs.sort(key=lambda r: r.created_at, reverse=True)
        return patient_runs

    def review_run(
        self,
        db: Session,
        user: User,
        run_id: str,
        approved: bool,
        feedback: str | None = None,
    ) -> AgentApprovalResponse:
        """
        Clinician review decision gate.
        Advances workflow from awaiting_approval to either completed or rejected.
        Requires write permission.
        """
        record = self._runs.get(run_id)
        if not record:
            raise EntityNotFoundError(f"Agent run '{run_id}' not found.")

        state: AgentWorkflowState = record["state"]
        if not check_user_patient_access(db, user=user, patient_id=state["patient_id"], min_permission="write"):
            raise AuthorizationError(f"Access denied: reviewing clinical reports requires write access for patient '{state['patient_id']}'.")

        current_status = state.get("status")
        if current_status != "awaiting_approval":
            raise Patient360Exception(
                f"Run '{run_id}' cannot be reviewed because it is in '{current_status}' status, not 'awaiting_approval'.",
                code="INVALID_STATE",
                status_code=400,
            )

        # Update decision in state
        updated_input_state = dict(state)
        updated_input_state["approval_status"] = "approved" if approved else "rejected"
        updated_input_state["clinician_feedback"] = feedback

        # Resume through LangGraph gate
        graph = build_clinical_agent_graph(db, user)
        resumed_state: AgentWorkflowState = cast(AgentWorkflowState, graph.invoke(updated_input_state))

        record["state"] = resumed_state
        record["updated_at"] = datetime.datetime.now(datetime.UTC)


        decision_str = "APPROVED" if approved else "REJECTED"
        log_audit_event(
            db=db,
            action="AGENT_RUN_REVIEWED",
            resource_type="agent_run",
            user_id=user.id,
            resource_id=run_id,
            patient_id=state["patient_id"],
            details={"decision": decision_str, "feedback": feedback},
        )

        msg = (
            "Clinical report approved and certified successfully."
            if approved
            else "Clinical report rejected by clinician."
        )

        return AgentApprovalResponse(
            run_id=run_id,
            status=resumed_state.get("status", "completed" if approved else "rejected"),
            approval_status=resumed_state.get("approval_status", "approved" if approved else "rejected"),
            message=msg,
            final_report=resumed_state.get("final_report"),
        )


_agent_service: AgentWorkflowService | None = None


def get_agent_service() -> AgentWorkflowService:
    """Singleton accessor for AgentWorkflowService."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentWorkflowService()
    return _agent_service
