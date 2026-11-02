"""Clinical Agent Workflow orchestration service with durable database persistence."""

import datetime
import json
import logging
import time
import uuid
from typing import Any, cast

from sqlalchemy.orm import Session

from backend.agents.graph import build_clinical_agent_graph
from backend.agents.state import AgentWorkflowState
from backend.audit.service import log_audit_event
from backend.core.exceptions import (
    AuthorizationError,
    EntityNotFoundError,
    Patient360Exception,
)
from backend.models.agent import AgentWorkflowRun
from backend.models.user import User
from backend.patients.service import check_user_patient_access
from backend.schemas.agent import (
    AgentApprovalResponse,
    AgentRunSnapshot,
    WorkflowStepLog,
)

logger = logging.getLogger(__name__)


class AgentWorkflowService:
    """Manages bounded clinical inquiry workflow runs with durable database persistence and human review gates."""

    def _state_to_db_model(
        self,
        state: AgentWorkflowState,
        db_run: AgentWorkflowRun | None = None,
    ) -> AgentWorkflowRun:
        plan = state.get("plan") or []
        steps = state.get("steps_executed") or []
        evidence = state.get("retrieved_evidence") or []
        contradictions = state.get("contradictions_found") or []

        if db_run is None:
            db_run = AgentWorkflowRun(
                id=state["run_id"],
                patient_id=state["patient_id"],
                user_id=state["user_id"],
                query=state["query"],
                status=state.get("status", "planning"),
                approval_status=state.get("approval_status", "pending"),
                iteration_count=state.get("iteration_count", 0),
                max_iterations=state.get("max_iterations", 5),
                elapsed_seconds=state.get("elapsed_seconds", 0.0),
                plan_json=json.dumps(plan),
                steps_json=json.dumps(steps),
                retrieved_evidence_json=json.dumps(evidence),
                contradictions_json=json.dumps(contradictions),
                draft_synthesis=state.get("draft_synthesis"),
                final_report=state.get("final_report"),
                report_version=1,
                error_message=state.get("error_message"),
            )
        else:
            db_run.status = state.get("status", db_run.status)
            db_run.approval_status = state.get("approval_status", db_run.approval_status)
            db_run.iteration_count = state.get("iteration_count", db_run.iteration_count)
            db_run.elapsed_seconds = state.get("elapsed_seconds", db_run.elapsed_seconds)
            db_run.plan_json = json.dumps(plan)
            db_run.steps_json = json.dumps(steps)
            db_run.retrieved_evidence_json = json.dumps(evidence)
            db_run.contradictions_json = json.dumps(contradictions)
            db_run.draft_synthesis = state.get("draft_synthesis", db_run.draft_synthesis)
            db_run.final_report = state.get("final_report", db_run.final_report)
            db_run.error_message = state.get("error_message", db_run.error_message)

        return db_run

    def _db_model_to_snapshot(self, db_run: AgentWorkflowRun) -> AgentRunSnapshot:
        plan = json.loads(db_run.plan_json) if db_run.plan_json else []
        raw_steps = json.loads(db_run.steps_json) if db_run.steps_json else []
        steps = [WorkflowStepLog(**s) for s in raw_steps]
        evidence = json.loads(db_run.retrieved_evidence_json) if db_run.retrieved_evidence_json else []
        contradictions = json.loads(db_run.contradictions_json) if db_run.contradictions_json else []

        patient_name = None
        if db_run.patient:
            patient_name = f"{db_run.patient.first_name} {db_run.patient.last_name}".strip()

        return AgentRunSnapshot(
            run_id=db_run.id,
            patient_id=db_run.patient_id,
            patient_name=patient_name,
            query=db_run.query,
            status=cast(Any, db_run.status),
            iteration_count=db_run.iteration_count,
            max_iterations=db_run.max_iterations,
            elapsed_seconds=db_run.elapsed_seconds,
            plan=plan,
            steps=steps,
            retrieved_evidence_count=len(evidence),
            contradictions_found=contradictions,
            draft_synthesis=db_run.draft_synthesis,
            final_report=db_run.final_report,
            approval_status=cast(Any, db_run.approval_status),
            clinician_feedback=db_run.review_notes,
            error_message=db_run.error_message,
            created_at=db_run.created_at,
            updated_at=db_run.updated_at,
        )

    def _db_model_to_state(self, db_run: AgentWorkflowRun) -> AgentWorkflowState:
        plan = json.loads(db_run.plan_json) if db_run.plan_json else []
        steps = json.loads(db_run.steps_json) if db_run.steps_json else []
        evidence = json.loads(db_run.retrieved_evidence_json) if db_run.retrieved_evidence_json else []
        contradictions = json.loads(db_run.contradictions_json) if db_run.contradictions_json else []

        return {
            "run_id": db_run.id,
            "patient_id": db_run.patient_id,
            "user_id": db_run.user_id,
            "query": db_run.query,
            "status": cast(Any, db_run.status),
            "approval_status": cast(Any, db_run.approval_status),
            "iteration_count": db_run.iteration_count,
            "max_iterations": db_run.max_iterations,
            "start_time_seconds": time.time(),
            "timeout_seconds": 30.0,
            "elapsed_seconds": db_run.elapsed_seconds,
            "plan": plan,
            "steps_executed": steps,
            "patient_dossier": None,
            "retrieved_evidence": evidence,
            "contradictions_found": contradictions,
            "draft_synthesis": db_run.draft_synthesis,
            "final_report": db_run.final_report,
            "clinician_feedback": db_run.review_notes,
            "error_message": db_run.error_message,
        }

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
        Initiates a bounded clinical inquiry workflow and persists run state to the database.
        Guarded by read-access authorization check.
        """
        if not check_user_patient_access(db, user=user, patient_id=patient_id, min_permission="read"):
            raise AuthorizationError(f"Access denied: user '{user.id}' lacks permission for patient '{patient_id}'.")

        run_id = f"run_{uuid.uuid4().hex[:12]}"
        bounded_max_iterations = min(max(1, max_iterations), 5)  # Enforce hard ceiling of 5

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

        # Persist durable state in relational database
        db_run = self._state_to_db_model(executed_state)
        db.add(db_run)
        db.commit()
        db.refresh(db_run)

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

        return self._db_model_to_snapshot(db_run)

    def get_run(
        self,
        db: Session,
        user: User,
        run_id: str,
    ) -> AgentRunSnapshot:
        """Retrieves snapshot of a specific workflow run from persistent database."""
        db_run = db.query(AgentWorkflowRun).filter(AgentWorkflowRun.id == run_id).first()
        if not db_run:
            raise EntityNotFoundError(f"Agent run '{run_id}' not found.")

        if not check_user_patient_access(db, user=user, patient_id=db_run.patient_id, min_permission="read"):
            raise AuthorizationError(f"Access denied: user '{user.id}' lacks permission for patient '{db_run.patient_id}'.")

        return self._db_model_to_snapshot(db_run)

    def list_runs_for_patient(
        self,
        db: Session,
        user: User,
        patient_id: str,
    ) -> list[AgentRunSnapshot]:
        """Lists all agent runs executed for the specified patient from persistent database."""
        if not check_user_patient_access(db, user=user, patient_id=patient_id, min_permission="read"):
            raise AuthorizationError(f"Access denied: user '{user.id}' lacks permission for patient '{patient_id}'.")

        runs = (
            db.query(AgentWorkflowRun)
            .filter(AgentWorkflowRun.patient_id == patient_id)
            .order_by(AgentWorkflowRun.created_at.desc())
            .all()
        )
        return [self._db_model_to_snapshot(r) for r in runs]

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
        Enforces strict role boundaries and ensures approved reports are immutable.
        """
        if user.role == "patient":
            raise AuthorizationError("Patients are strictly prohibited from approving clinical research reports.")

        db_run = db.query(AgentWorkflowRun).filter(AgentWorkflowRun.id == run_id).first()
        if not db_run:
            raise EntityNotFoundError(f"Agent run '{run_id}' not found.")

        if not check_user_patient_access(db, user=user, patient_id=db_run.patient_id, min_permission="write"):
            raise AuthorizationError(
                f"Access denied: reviewing clinical reports requires write access for patient '{db_run.patient_id}'."
            )

        if db_run.status != "awaiting_approval":
            raise Patient360Exception(
                f"Run '{run_id}' cannot be reviewed because it is in '{db_run.status}' status, not 'awaiting_approval'.",
                code="INVALID_STATE",
                status_code=400,
            )

        # Reconstruct state from database record
        state = self._db_model_to_state(db_run)
        state["approval_status"] = "approved" if approved else "rejected"
        state["clinician_feedback"] = feedback

        # Resume through LangGraph gate
        graph = build_clinical_agent_graph(db, user)
        resumed_state: AgentWorkflowState = cast(AgentWorkflowState, graph.invoke(state))

        # Update database entity
        self._state_to_db_model(resumed_state, db_run=db_run)
        decision_str = "APPROVED" if approved else "REJECTED"
        db_run.reviewer_id = user.id
        db_run.reviewer_email = user.email
        db_run.reviewer_role = user.role
        db_run.review_decision = decision_str
        db_run.review_notes = feedback
        db_run.reviewed_at = datetime.datetime.now(datetime.UTC)

        db.commit()
        db.refresh(db_run)

        log_audit_event(
            db=db,
            action="AGENT_RUN_REVIEWED",
            resource_type="agent_run",
            user_id=user.id,
            resource_id=run_id,
            patient_id=db_run.patient_id,
            details={"decision": decision_str, "feedback": feedback},
        )

        msg = (
            "Clinical report approved and certified successfully."
            if approved
            else "Clinical report rejected by clinician."
        )

        return AgentApprovalResponse(
            run_id=run_id,
            status=cast(Any, db_run.status),
            approval_status=cast(Any, db_run.approval_status),
            message=msg,
            final_report=db_run.final_report,
        )


_agent_service: AgentWorkflowService | None = None


def get_agent_service() -> AgentWorkflowService:
    """Singleton accessor for AgentWorkflowService."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentWorkflowService()
    return _agent_service

