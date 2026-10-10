"""State definition for bounded LangGraph clinical agent workflows."""

from typing import Any, TypedDict

from backend.schemas.agent import ApprovalStatus, WorkflowStatus


class AgentWorkflowState(TypedDict, total=False):
    """Observable state machine data structure for LangGraph workflow execution."""

    run_id: str
    patient_id: str
    user_id: str
    query: str
    status: WorkflowStatus
    approval_status: ApprovalStatus
    iteration_count: int
    max_iterations: int
    start_time_seconds: float
    timeout_seconds: float
    elapsed_seconds: float
    plan: list[str]
    steps_executed: list[dict[str, Any]]
    patient_dossier: dict[str, Any] | None
    retrieved_evidence: list[dict[str, Any]]
    contradictions_found: list[dict[str, Any]]
    draft_synthesis: str | None
    final_report: str | None
    clinician_feedback: str | None
    error_message: str | None
