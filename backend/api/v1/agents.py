"""Bounded Agentic Workflows and Human-in-the-Loop review API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.agents.service import AgentWorkflowService, get_agent_service
from backend.api.deps import get_current_user, get_db
from backend.models.user import User
from backend.schemas.agent import (
    AgentApprovalRequest,
    AgentApprovalResponse,
    AgentRunRequest,
    AgentRunSnapshot,
)

router = APIRouter()


@router.post(
    "/runs",
    response_model=AgentRunSnapshot,
    status_code=status.HTTP_201_CREATED,
)
def create_agent_run(
    payload: AgentRunRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentWorkflowService, Depends(get_agent_service)],
) -> AgentRunSnapshot:
    """
    Executes a bounded LangGraph multi-step clinical inquiry state machine.
    Enforces a hard iteration ceiling (max 5 loops) and pauses at Human-in-the-Loop review gate.
    """
    return service.start_run(
        db=db,
        user=current_user,
        patient_id=payload.patient_id,
        query=payload.query,
        max_iterations=payload.max_iterations,
    )


@router.get(
    "/runs/{run_id}",
    response_model=AgentRunSnapshot,
    status_code=status.HTTP_200_OK,
)
def get_agent_run(
    run_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentWorkflowService, Depends(get_agent_service)],
) -> AgentRunSnapshot:
    """Retrieves full observable state machine snapshot and execution telemetry."""
    return service.get_run(db=db, user=current_user, run_id=run_id)


@router.post(
    "/runs/{run_id}/review",
    response_model=AgentApprovalResponse,
    status_code=status.HTTP_200_OK,
)
def review_agent_run(
    run_id: str,
    payload: AgentApprovalRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentWorkflowService, Depends(get_agent_service)],
) -> AgentApprovalResponse:
    """
    Clinician review decision gate for approving or rejecting synthesized clinical reports.
    Advances the state machine from 'awaiting_approval' to 'completed' or 'rejected'.
    """
    return service.review_run(
        db=db,
        user=current_user,
        run_id=run_id,
        approved=payload.approved,
        feedback=payload.feedback,
    )


@router.get(
    "/patients/{patient_id}/runs",
    response_model=list[AgentRunSnapshot],
    status_code=status.HTTP_200_OK,
)
def list_patient_agent_runs(
    patient_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentWorkflowService, Depends(get_agent_service)],
) -> list[AgentRunSnapshot]:
    """Retrieves history of agent workflow runs executed for the specified patient."""
    return service.list_runs_for_patient(db=db, user=current_user, patient_id=patient_id)
