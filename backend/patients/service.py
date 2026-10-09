"""Patient dossier management and server-side authorization checks."""

import logging

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.core.exceptions import EntityNotFoundError, Patient360Exception
from backend.models.document import Document
from backend.models.patient import Patient, UserPatientPermission
from backend.models.user import User
from backend.schemas.patient import PatientCreate

logger = logging.getLogger(__name__)


def create_patient(db: Session, patient_in: PatientCreate, creator_user: User) -> Patient:
    """Creates a new synthetic patient record and grants admin permission to the creator."""
    existing = db.query(Patient).filter(Patient.mrn_synthetic == patient_in.mrn_synthetic).first()
    if existing:
        raise Patient360Exception(
            message=f"Patient with MRN '{patient_in.mrn_synthetic}' already exists.",
            code="PATIENT_ALREADY_EXISTS",
            status_code=409,
        )

    patient = Patient(
        mrn_synthetic=patient_in.mrn_synthetic,
        first_name=patient_in.first_name,
        last_name=patient_in.last_name,
        date_of_birth=patient_in.date_of_birth,
        gender=patient_in.gender,
        primary_condition=patient_in.primary_condition,
        is_deleted=False,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    # Grant creator access
    permission = UserPatientPermission(
        user_id=creator_user.id,
        patient_id=patient.id,
        permission_level="admin",
    )
    db.add(permission)
    db.commit()
    db.refresh(patient)

    logger.info(f"Created patient {patient.mrn_synthetic} by user {creator_user.id}")
    return patient


def get_patient(db: Session, patient_id: str) -> Patient:
    """Retrieves patient by ID or raises EntityNotFoundError."""
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.is_deleted.is_(False)).first()
    if not patient:
        raise EntityNotFoundError(f"Patient with ID '{patient_id}' not found.")
    return patient


def check_user_patient_access(
    db: Session,
    user: User,
    patient_id: str,
    min_permission: str = "read",
) -> bool:
    """
    Enforces server-side patient-level access boundary:
    - Administrators have platform-wide access.
    - Other users must have a matching record in user_patient_permissions.
    """
    if user.role == "admin":
        return True

    perm = (
        db.query(UserPatientPermission)
        .filter(
            UserPatientPermission.user_id == user.id,
            UserPatientPermission.patient_id == patient_id,
        )
        .first()
    )
    if not perm:
        return False

    if min_permission == "write" and perm.permission_level == "read":
        return False
    if min_permission == "admin" and perm.permission_level != "admin":
        return False

    return True


def list_authorized_patients(
    db: Session,
    user: User,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
) -> list[tuple[Patient, int]]:
    """
    Returns list of patients authorized for the current user alongside attached document counts.
    Enforces server-side isolation.
    """
    query = db.query(Patient).filter(Patient.is_deleted.is_(False))

    # Enforce isolation filter unless user is admin
    if user.role != "admin":
        query = query.join(
            UserPatientPermission,
            UserPatientPermission.patient_id == Patient.id,
        ).filter(UserPatientPermission.user_id == user.id)

    # Optional search query filter
    if search:
        search_filter = f"%{search.lower()}%"
        query = query.filter(
            or_(
                Patient.first_name.ilike(search_filter),
                Patient.last_name.ilike(search_filter),
                Patient.mrn_synthetic.ilike(search_filter),
                Patient.primary_condition.ilike(search_filter),
            )
        )

    patients = query.order_by(Patient.created_at.desc()).offset(skip).limit(limit).all()

    # Calculate document count for each patient
    result: list[tuple[Patient, int]] = []
    for p in patients:
        doc_count = db.query(Document).filter(Document.patient_id == p.id, Document.is_deleted.is_(False)).count()
        result.append((p, doc_count))

    return result


def grant_patient_access(
    db: Session,
    patient_id: str,
    target_user_id: str,
    permission_level: str = "read",
) -> UserPatientPermission:
    """Grants a user access to a specific patient dossier."""
    get_patient(db, patient_id)

    existing = (
        db.query(UserPatientPermission)
        .filter(
            UserPatientPermission.user_id == target_user_id,
            UserPatientPermission.patient_id == patient_id,
        )
        .first()
    )
    if existing:
        existing.permission_level = permission_level
        db.commit()
        db.refresh(existing)
        return existing

    new_perm = UserPatientPermission(
        user_id=target_user_id,
        patient_id=patient_id,
        permission_level=permission_level,
    )
    db.add(new_perm)
    db.commit()
    db.refresh(new_perm)
    return new_perm
