"""Grounded RAG question-answering and clinician feedback API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user, get_db
from backend.audit.service import log_audit_event
from backend.core.exceptions import AuthorizationError
from backend.models.user import User
from backend.patients.service import check_user_patient_access
from backend.rag.service import get_rag_service
from backend.schemas.rag import (
    RAGFeedbackRequest,
    RAGFeedbackResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)

router = APIRouter()


@router.post("/query", response_model=RAGQueryResponse, status_code=status.HTTP_200_OK)
def query_grounded_rag(
    request_body: RAGQueryRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RAGQueryResponse:
    """
    Executes an evidence-grounded clinical query over a specific patient dossier.
    Enforces server-side patient isolation and logs audit telemetry.
    """
    # 1. Enforce server-side tenant / patient-level authorization
    if not check_user_patient_access(
        db, user=current_user, patient_id=request_body.patient_id, min_permission="read"
    ):
        raise AuthorizationError(
            f"User '{current_user.email}' is not authorized to access patient dossier '{request_body.patient_id}'."
        )

    # 2. Execute RAG retrieval and synthesis
    rag_service = get_rag_service()
    response = rag_service.query(
        query=request_body.query,
        patient_id=request_body.patient_id,
        top_k=request_body.top_k,
        db=db,
    )

    # 3. Log immutable audit trail
    log_audit_event(
        db=db,
        action="RAG_QUERY_EXECUTED",
        resource_type="patient_dossier",
        user_id=current_user.id,
        resource_id=request_body.patient_id,
        patient_id=request_body.patient_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        status="SUCCESS",
        details={
            "query_length": len(request_body.query),
            "citations_count": len(response.citations),
            "is_abstention": response.retrieval_metadata.is_abstention,
            "confidence_score": response.confidence_score,
            "total_latency_ms": response.retrieval_metadata.total_latency_ms,
        },
    )

    return response


@router.post("/feedback", response_model=RAGFeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_rag_feedback(
    request_body: RAGFeedbackRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RAGFeedbackResponse:
    """
    Records clinician or researcher feedback and quality ratings on synthesized answers.
    """
    # Verify patient access
    if not check_user_patient_access(
        db, user=current_user, patient_id=request_body.patient_id, min_permission="read"
    ):
        raise AuthorizationError(
            f"User '{current_user.email}' is not authorized to submit feedback for patient '{request_body.patient_id}'."
        )

    log_audit_event(
        db=db,
        action="RAG_FEEDBACK_SUBMITTED",
        resource_type="rag_response",
        user_id=current_user.id,
        resource_id=request_body.patient_id,
        patient_id=request_body.patient_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        status="SUCCESS",
        details={
            "rating": request_body.rating,
            "issue_type": request_body.issue_type,
            "comment": request_body.comment,
            "query_snippet": request_body.query[:100],
        },
    )

    return RAGFeedbackResponse(
        status="FEEDBACK_LOGGED",
        message="Clinician feedback successfully recorded in audit log.",
    )
