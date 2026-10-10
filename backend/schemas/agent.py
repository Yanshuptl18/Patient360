"""Pydantic schemas for bounded agentic workflows and human-in-the-loop review gates."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

WorkflowStatus = Literal[
    "planning",
    "executing",
    "awaiting_approval",
    "completed",
    "iteration_limit_reached",
    "timeout_exceeded",
    "rejected",
    "failed",
]

ApprovalStatus = Literal["pending", "approved", "rejected"]


class AgentRunRequest(BaseModel):
    """Payload to initiate a bounded agentic research workflow."""

    patient_id: str
    query: str = Field(..., min_length=3, max_length=2000)
    max_iterations: int = Field(default=5, ge=1, le=5)  # Enforce hard ceiling of 5


class WorkflowStepLog(BaseModel):
    """Execution telemetry for a single discrete step/tool execution."""

    step_index: int
    node_name: str
    thought: str
    action_tool: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: Any | None = None
    timestamp_iso: str


class AgentRunSnapshot(BaseModel):
    """Full observable state snapshot of an agentic workflow run."""

    run_id: str
    patient_id: str
    patient_name: str | None = None
    query: str
    status: WorkflowStatus
    iteration_count: int
    max_iterations: int
    elapsed_seconds: float
    plan: list[str]
    steps: list[WorkflowStepLog]
    retrieved_evidence_count: int
    contradictions_found: list[dict[str, Any]]
    draft_synthesis: str | None = None
    final_report: str | None = None
    approval_status: ApprovalStatus
    clinician_feedback: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentApprovalRequest(BaseModel):
    """Clinician review decision payload for Human-in-the-Loop approval gate."""

    approved: bool
    feedback: str | None = Field(default=None, max_length=1000)


class AgentApprovalResponse(BaseModel):
    """Response returned upon clinician review submission."""

    run_id: str
    status: WorkflowStatus
    approval_status: ApprovalStatus
    message: str
    final_report: str | None = None
