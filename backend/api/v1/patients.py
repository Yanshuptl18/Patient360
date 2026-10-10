"""Patient dossier management API routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user, get_db, require_roles
from backend.audit.service import log_audit_event
from backend.core.exceptions import AuthorizationError
from backend.models.user import User
from backend.patients.deletion import cascade_delete_patient
from backend.patients.service import (
    check_user_patient_access,
    create_patient,
    get_patient,
    grant_patient_access,
    list_authorized_patients,
)
from backend.schemas.patient import (
    PatientCreate,
    PatientResponse,
    PermissionGrantRequest,
)

router = APIRouter()


@router.get("", response_model=list[PatientResponse])
def get_patients(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: str | None = Query(None, min_length=1),
) -> list[PatientResponse]:
    """
    Returns list of patient records authorized for the authenticated user.
    Enforces server-side isolation: Reviewers only see patients on their panel;
    Admins see all platform patients.
    """
    patients_with_counts = list_authorized_patients(
        db, user=current_user, skip=skip, limit=limit, search=search
    )
    result: list[PatientResponse] = []
    for patient, count in patients_with_counts:
        p_resp = PatientResponse.model_validate(patient)
        p_resp.document_count = count
        result.append(p_resp)
    return result


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def register_patient(
    patient_in: PatientCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(["admin", "reviewer"]))],
) -> PatientResponse:
    """
    Registers a new synthetic patient record.
    Authorized for admin and clinical reviewer roles.
    """
    patient = create_patient(db, patient_in=patient_in, creator_user=current_user)
    log_audit_event(
        db,
        action="PATIENT_CREATED",
        resource_type="patients",
        user_id=current_user.id,
        patient_id=patient.id,
        status="SUCCESS",
        details={"mrn": patient.mrn_synthetic, "name": f"{patient.first_name} {patient.last_name}"},
    )
    return PatientResponse.model_validate(patient)


@router.get("/{id}", response_model=PatientResponse)
def get_patient_by_id(
    id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PatientResponse:
    """
    Retrieves detailed patient demographic record.
    Rejects with 403 Forbidden if user is not authorized for this patient.
    """
    if not check_user_patient_access(db, current_user, patient_id=id, min_permission="read"):
        log_audit_event(
            db,
            action="PATIENT_ACCESS_DENIED",
            resource_type="patients",
            user_id=current_user.id,
            patient_id=id,
            status="DENIED",
        )
        raise AuthorizationError(f"Access to patient dossier '{id}' is denied.")

    patient = get_patient(db, patient_id=id)
    return PatientResponse.model_validate(patient)


@router.post("/{id}/permissions", status_code=status.HTTP_200_OK)
def grant_permission(
    id: str,
    grant_in: PermissionGrantRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Grants a user access to this patient dossier (admin or patient owner only)."""
    if not check_user_patient_access(db, current_user, patient_id=id, min_permission="admin"):
        raise AuthorizationError("Only administrators or patient owners can grant permissions.")

    grant_patient_access(
        db,
        patient_id=id,
        target_user_id=grant_in.user_id,
        permission_level=grant_in.permission_level,
    )
    return {"status": "PERMISSION_GRANTED"}


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_patient_dossier(
    id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(["admin"]))],
) -> dict[str, Any]:
    """
    Cascading patient purge (GDPR / HIPAA Right-to-be-Forgotten).
    Atomically erases patient demographics, documents, chunks, vectors, and timeline events.
    Authorized for admin role only.
    """
    return cascade_delete_patient(db=db, patient_id=id, current_user_id=current_user.id)
