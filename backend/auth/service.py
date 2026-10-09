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
