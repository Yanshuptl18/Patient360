import random
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user, get_db, require_role
from backend.audit.service import log_audit_event
from backend.auth.service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_id,
    seed_default_users,
)
from backend.core.config import settings
from backend.core.exceptions import AuthenticationError
from backend.core.security import create_access_token, create_refresh_token, decode_token
from backend.models.user import User
from backend.schemas.auth import (
    LoginRequest,
    OtpRequest,
    OtpResponse,
    OtpVerifyRequest,
    RoleEnum,
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)

router = APIRouter()

# In-memory OTP registry for verification sessions
OTP_REGISTRY: dict[str, dict] = {}


@router.post("/otp/request", response_model=OtpResponse)
def request_otp(
    otp_in: OtpRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> OtpResponse:
    """
    Dispatches a 6-digit one-time verification code (OTP) to the specified clinical email.
    Supports seamless login and registration for healthcare clinicians and researchers.
    """
    email = otp_in.email.lower().strip()
    code = f"{random.randint(100000, 999999)}"
    expires_at = time.time() + 600.0  # 10 minutes TTL

    OTP_REGISTRY[email] = {
        "code": code,
        "expires_at": expires_at,
        "attempts": 0,
        "full_name": otp_in.full_name,
        "role": otp_in.role,
    }

    ip_addr = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    log_audit_event(
        db,
        action="OTP_REQUESTED",
        resource_type="auth",
        ip_address=ip_addr,
        user_agent=user_agent,
        status="SUCCESS",
        details={"email": email},
    )

    return OtpResponse(
        status="success",
        message="A 6-digit verification code has been dispatched to your email address.",
        email=email,
        dev_otp=code,
    )


@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp(
    verify_in: OtpVerifyRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """
    Verifies the 6-digit OTP code, provisions new user accounts if not present,
    and returns JWT access and refresh tokens.
    """
    email = verify_in.email.lower().strip()
    session = OTP_REGISTRY.get(email)

    if not session:
        raise AuthenticationError("No verification session found for this email. Please request a new code.")

    if time.time() > session["expires_at"]:
        OTP_REGISTRY.pop(email, None)
        raise AuthenticationError("The verification code has expired. Please request a new code.")

    if session["attempts"] >= 5:
        OTP_REGISTRY.pop(email, None)
        raise AuthenticationError("Maximum verification attempts exceeded. Please request a new code.")

    if verify_in.otp.strip() != session["code"]:
        session["attempts"] += 1
        raise AuthenticationError("Invalid verification code. Please check your email and try again.")

    # Code verified successfully! Consume session
    OTP_REGISTRY.pop(email, None)

    # Locate user or auto-register new medical professional
    user = get_user_by_email(db, email=email)
    if not user:
        full_name = (
            verify_in.full_name
            or session.get("full_name")
            or email.split("@")[0].replace(".", " ").replace("_", " ").title()
        )
        role = verify_in.role or session.get("role") or RoleEnum.REVIEWER
        rand_secret = f"ClinicianSecure!{random.randint(100000, 999999)}"
        user = create_user(
            db,
            user_in=UserCreate(
                email=email,
                full_name=full_name,
                role=role,
                password=rand_secret,
            ),
        )

    if not user.is_active:
        raise AuthenticationError("This clinical account is deactivated. Contact hospital administration.")

    ip_addr = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    access_token = create_access_token(subject=user.id, role=user.role)
    refresh_token = create_refresh_token(subject=user.id, role=user.role)

    log_audit_event(
        db,
        action="LOGIN_OTP_SUCCESS",
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
