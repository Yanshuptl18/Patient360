"""Longitudinal patient timeline and clinical contradiction API endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user, get_db
from backend.audit.service import log_audit_event
from backend.core.exceptions import AuthorizationError
from backend.models.user import User
from backend.patients.service import check_user_patient_access
from backend.schemas.timeline import (
    ContradictionItem,
    PatientTimelineResponse,
    TimelineExtractRequest,
    TimelineExtractResponse,
)
from backend.timeline.service import TimelineService, get_timeline_service

router = APIRouter()


@router.get(
    "/patients/{patient_id}",
    response_model=PatientTimelineResponse,
    status_code=status.HTTP_200_OK,
)
def get_patient_timeline(
    patient_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TimelineService, Depends(get_timeline_service)],
    event_types: Annotated[list[str] | None, Query()] = None,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    order: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
) -> PatientTimelineResponse:
    """
    Retrieves the chronological clinical timeline for an authorized patient.
    Enforces server-side RBAC and patient dossier access boundaries.
    Automatically surfaces cross-document clinical contradictions.
    """
    if not check_user_patient_access(db, user=current_user, patient_id=patient_id, min_permission="read"):
        raise AuthorizationError(
            f"User lacks read permission for patient dossier '{patient_id}'."
        )

    return service.get_patient_timeline(
        db=db,
        patient_id=patient_id,
        event_types=event_types,
        start_date=start_date,
        end_date=end_date,
        order=order,
    )


@router.post(
    "/patients/{patient_id}/extract",
    response_model=TimelineExtractResponse,
    status_code=status.HTTP_200_OK,
)
def extract_timeline_events(
    patient_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TimelineService, Depends(get_timeline_service)],
    request_body: TimelineExtractRequest | None = None,
) -> TimelineExtractResponse:
    """
    Triggers rule-based and NLP event extraction across patient document chunks.
    Re-evaluates cross-document contradictions and updates the longitudinal trajectory.
    """
    if not check_user_patient_access(db, user=current_user, patient_id=patient_id, min_permission="write"):
        raise AuthorizationError(
            f"User lacks write permission for patient dossier '{patient_id}'."
        )

    doc_ids = request_body.document_ids if request_body else None
    force = request_body.force_reextract if request_body else False

    result = service.extract_events_for_patient(
        db=db,
        patient_id=patient_id,
        document_ids=doc_ids,
        force_reextract=force,
    )

    log_audit_event(
        db=db,
        action="TIMELINE_EVENTS_EXTRACTED",
        resource_type="patient_timeline",
        user_id=current_user.id,
        resource_id=patient_id,
        patient_id=patient_id,
        status="SUCCESS",
        details={
            "events_extracted": result.events_extracted_count,
            "contradictions_detected": result.contradictions_detected_count,
            "documents_processed": result.documents_processed_count,
        },
    )

    return result


@router.get(
    "/patients/{patient_id}/contradictions",
    response_model=list[ContradictionItem],
    status_code=status.HTTP_200_OK,
)
def get_patient_contradictions(
    patient_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TimelineService, Depends(get_timeline_service)],
) -> list[ContradictionItem]:
    """
    Retrieves all surfaced clinical contradictions across patient documentation.
    """
    if not check_user_patient_access(db, user=current_user, patient_id=patient_id, min_permission="read"):
        raise AuthorizationError(
            f"User lacks read permission for patient dossier '{patient_id}'."
        )

    return service.get_patient_contradictions(db=db, patient_id=patient_id)
