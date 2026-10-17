"""Authentication business logic, user management, and credential verification."""

import logging

from sqlalchemy.orm import Session

from backend.core.exceptions import AuthenticationError, Patient360Exception
from backend.core.security import get_password_hash, verify_password
from backend.models.user import User
from backend.schemas.auth import RoleEnum, UserCreate

logger = logging.getLogger(__name__)


def get_user_by_email(db: Session, email: str) -> User | None:
    """Retrieves a user by email address."""
    return db.query(User).filter(User.email == email.lower()).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """Retrieves a user by primary key UUID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    """Registers a new platform user."""
    existing = get_user_by_email(db, user_in.email)
    if existing:
        raise Patient360Exception(
            message=f"User with email '{user_in.email}' already exists.",
            code="USER_ALREADY_EXISTS",
            status_code=409,
        )

    db_user = User(
        email=user_in.email.lower(),
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role.value if isinstance(user_in.role, RoleEnum) else str(user_in.role),
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"Created user {db_user.email} with role {db_user.role}")
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Authenticates credentials against stored password hash."""
    user = get_user_by_email(db, email)
    if not user:
        raise AuthenticationError("Invalid email or password.")
    if not user.is_active:
        raise AuthenticationError("User account is inactive. Please contact administrator.")
    if not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid email or password.")
    return user


DEMO_PERSONAS: dict[str, dict[str, str]] = {
    "doctor": {
        "email": "doctor@patient360.org",
        "full_name": "Dr. Evelyn Reed, MD",
        "role": "doctor",
        "title": "Attending Physician / Clinical Reviewer",
        "department": "Cardio-Oncology & Internal Medicine",
        "description": "Access clinical dossiers, review longitudinal patient trajectories, execute evidence-grounded inquiries with source citations, and certify clinical agent reasoning.",
        "avatar_initials": "ER",
    },
    "nurse": {
        "email": "nurse@patient360.org",
        "full_name": "Sarah Jenkins, RN",
        "role": "nurse",
        "title": "Care Coordinator / Clinical Nurse",
        "department": "Inpatient Care Coordination & Triage",
        "description": "Review patient care trajectories, monitor longitudinal medication timelines, inspect clinical contradiction flags, and examine physical document notes.",
        "avatar_initials": "SJ",
    },
    "hospital_admin": {
        "email": "hospital_admin@patient360.org",
        "full_name": "Marcus Vance, MHA",
        "role": "hospital_admin",
        "title": "Chief Hospital Administrator",
        "department": "Clinical Operations & Governance",
        "description": "Hospital-wide operational overview, patient cohort distributions, document ingestion volume, compliance audit logs, and operational telemetry.",
        "avatar_initials": "MV",
    },
    "patient": {
        "email": "patient@patient360.org",
        "full_name": "Eleanor Vance",
        "role": "patient",
        "title": "Patient (Eleanor Vance - MRN: SYNTH-10001)",
        "department": "Patient Health Record Portal",
        "description": "View personal medical dossier (MRN: SYNTH-10001), clinical care timeline, plain-language diagnostic summaries, visit records, and documented allergies.",
        "avatar_initials": "EV",
    },
    "system_admin": {
        "email": "admin@patient360.org",
        "full_name": "Alex Chen",
        "role": "admin",
        "title": "System & Infrastructure Administrator",
        "department": "IT & Clinical Informatics",
        "description": "Full system administration, database & vector store health metrics, automated 50-item quality evaluation laboratory benchmarks, and security audit trail.",
        "avatar_initials": "AC",
    },
}


def seed_default_users(db: Session) -> dict[str, User]:
    """
    Seeds default synthetic persona accounts if they do not already exist.
    Password for all demo accounts: 'Patient360Secure!'
    """
    default_accounts = [
        ("admin@patient360.org", "Sarah Jenkins", RoleEnum.ADMIN),
        ("reviewer@patient360.org", "Dr. Evelyn Reed", RoleEnum.REVIEWER),
        ("researcher@patient360.org", "Dr. Marcus Vance", RoleEnum.RESEARCHER),
        ("demo@patient360.org", "Alex Chen", RoleEnum.DEMO),
        ("doctor@patient360.org", "Dr. Evelyn Reed, MD", RoleEnum.DOCTOR),
        ("nurse@patient360.org", "Sarah Jenkins, RN", RoleEnum.NURSE),
        ("hospital_admin@patient360.org", "Marcus Vance, MHA", RoleEnum.HOSPITAL_ADMIN),
        ("patient@patient360.org", "Eleanor Vance", RoleEnum.PATIENT),
    ]

    seeded: dict[str, User] = {}
    for email, name, role in default_accounts:
        user = get_user_by_email(db, email)
        if not user:
            user = create_user(
                db,
                UserCreate(
                    email=email,
                    full_name=name,
                    role=role,
                    password="Patient360Secure!",
                ),
            )
        seeded[role.value] = user
    return seeded


def ensure_demo_user_and_permissions(db: Session, role_key: str) -> User:
    """
    Retrieves or provisions the designated demo user account and configures
    their role-specific patient authorization boundary.
    """
    if role_key not in DEMO_PERSONAS:
        raise Patient360Exception(
            message=f"Invalid demo role key '{role_key}'.",
            code="INVALID_DEMO_ROLE",
            status_code=400,
        )

    info = DEMO_PERSONAS[role_key]
    user = get_user_by_email(db, info["email"])
    if user:
        if user.full_name != info["full_name"] or user.role != info["role"]:
            user.full_name = info["full_name"]
            user.role = info["role"]
            db.commit()
            db.refresh(user)
    else:
        user = create_user(
            db,
            UserCreate(
                email=info["email"],
                full_name=info["full_name"],
                role=RoleEnum(info["role"]),
                password="Patient360Secure!",
            ),
        )

    # Lazily import patient models to prevent circular dependency
    from backend.models.patient import Patient, UserPatientPermission

    patients = db.query(Patient).filter(Patient.is_deleted.is_(False)).all()
    if patients:
        eleanor = next((p for p in patients if p.mrn_synthetic == "SYNTH-10001"), None)
        if role_key == "patient" and eleanor:
            # Patient role is strictly isolated to their own record (Eleanor Vance)
            perm = (
                db.query(UserPatientPermission)
                .filter_by(user_id=user.id, patient_id=eleanor.id)
                .first()
            )
            if not perm:
                db.add(
                    UserPatientPermission(
                        user_id=user.id, patient_id=eleanor.id, permission_level="read"
                    )
                )
                db.commit()
        elif role_key in ("doctor", "nurse"):
            # Doctors and Nurses have access to all patient cohort dossiers
            for p in patients:
                perm = (
                    db.query(UserPatientPermission)
                    .filter_by(user_id=user.id, patient_id=p.id)
                    .first()
                )
                if not perm:
                    db.add(
                        UserPatientPermission(
                            user_id=user.id, patient_id=p.id, permission_level="write"
                        )
                    )
            db.commit()

    return user

