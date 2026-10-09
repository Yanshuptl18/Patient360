"""Authentication, token exchange, and user management API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user, get_db, require_role
from backend.audit.service import log_audit_event
from backend.auth.service import (
    authenticate_user,
    create_user,
    get_user_by_id,
    seed_default_users,
)
from backend.core.config import settings
from backend.core.exceptions import AuthenticationError
from backend.core.security import create_access_token, create_refresh_token, decode_token
from backend.models.user import User
from backend.schemas.auth import (
    LoginRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(
    login_in: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """
    Authenticates user credentials and issues JWT access and refresh tokens.
    Records audit log entries for both successful and failed attempts.
    """
    ip_addr = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    try:
        user = authenticate_user(db, email=login_in.email, password=login_in.password)
    except AuthenticationError as exc:
        log_audit_event(
            db,
            action="LOGIN_ATTEMPT",
            resource_type="auth",
            ip_address=ip_addr,
            user_agent=user_agent,
            status="FAILURE",
            details={"email": login_in.email, "reason": str(exc)},
        )
        raise

    access_token = create_access_token(subject=user.id, role=user.role)
    refresh_token = create_refresh_token(subject=user.id, role=user.role)

    log_audit_event(
        db,
        action="LOGIN_SUCCESS",
        resource_type="auth",
        user_id=user.id,
        ip_address=ip_addr,
        user_agent=user_agent,
        status="SUCCESS",
        details={"email": user.email, "role": user.role},
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_in: TokenRefreshRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Issues a fresh access token using a valid JWT refresh token."""
    payload = decode_token(refresh_in.refresh_token, expected_type="refresh")
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid refresh token payload.")

    user = get_user_by_id(db, user_id=user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User is no longer active.")

    new_access_token = create_access_token(subject=user.id, role=user.role)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=refresh_in.refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Returns the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_role("admin"))],
) -> list[UserResponse]:
    """Admin-only endpoint listing all platform users."""
    users = db.query(User).all()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    user_in: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_role("admin"))],
) -> UserResponse:
    """Admin-only endpoint to provision a new user account."""
    new_user = create_user(db, user_in=user_in)
    log_audit_event(
        db,
        action="USER_PROVISIONED",
        resource_type="users",
        user_id=admin_user.id,
        resource_id=new_user.id,
        status="SUCCESS",
        details={"created_email": new_user.email, "assigned_role": new_user.role},
    )
    return UserResponse.model_validate(new_user)


@router.post("/seed-demo-users", response_model=list[UserResponse])
def seed_demo_accounts(
    db: Annotated[Session, Depends(get_db)],
) -> list[UserResponse]:
    """
    Public utility endpoint in development mode to seed demo persona accounts:
    - Sarah Jenkins (admin@patient360.org)
    - Dr. Evelyn Reed (reviewer@patient360.org)
    - Dr. Marcus Vance (researcher@patient360.org)
    - Alex Chen (demo@patient360.org)
    All default passwords: 'Patient360Secure!'
    """
    seeded = seed_default_users(db)
    return [UserResponse.model_validate(u) for u in seeded.values()]
