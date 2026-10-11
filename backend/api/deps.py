"""Reusable FastAPI dependency providers for database access and RBAC authorization."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.auth.service import get_user_by_id
from backend.core.config import settings
from backend.core.database import get_db
from backend.core.exceptions import AuthenticationError, AuthorizationError
from backend.core.security import decode_token
from backend.models.user import User

# Optional OAuth2 password bearer scheme for swagger integration
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)


def get_token_from_header(
    authorization: Annotated[str | None, Header()] = None,
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
) -> str:
    """Extracts the bearer token from the Authorization header or oauth2 scheme."""
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    if token:
        return token
    raise AuthenticationError("Authorization header missing or malformed.")


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(get_token_from_header)],
) -> User:
    """
    Validates the JWT access token and returns the authenticated User instance.
    Raises AuthenticationError if token is invalid, expired, or user not found.
    """
    payload = decode_token(token, expected_type="access")
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token payload missing subject identifier.")

    user = get_user_by_id(db, user_id=user_id)
    if not user:
        raise AuthenticationError("User associated with this token no longer exists.")
    if not user.is_active:
        raise AuthenticationError("User account has been deactivated.")

    return user


CLINICAL_REVIEW_ROLES = {"reviewer", "doctor", "clinician"}


def require_role(required_role: str) -> Callable[[User], User]:
    """
    FastAPI dependency factory enforcing a specific RBAC role.
    Admin users automatically pass all role checks.
    """

    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role == "admin" or current_user.role == required_role:
            return current_user
        if required_role == "reviewer" and current_user.role in CLINICAL_REVIEW_ROLES:
            return current_user
        raise AuthorizationError(
            f"Role '{current_user.role}' is not authorized. Requires '{required_role}'."
        )

    return role_checker


def require_roles(allowed_roles: list[str]) -> Callable[[User], User]:
    """
    FastAPI dependency factory enforcing that user has at least one of the allowed roles.
    Admin users automatically pass all role checks.
    """

    def roles_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role == "admin" or current_user.role in allowed_roles:
            return current_user
        if "reviewer" in allowed_roles and current_user.role in CLINICAL_REVIEW_ROLES:
            return current_user
        raise AuthorizationError(
            f"Role '{current_user.role}' is not authorized. Permitted roles: {allowed_roles}."
        )

    return roles_checker
