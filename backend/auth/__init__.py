"""Authentication Service Package."""

from backend.auth.service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_id,
    seed_default_users,
)

__all__ = [
    "authenticate_user",
    "create_user",
    "get_user_by_email",
    "get_user_by_id",
    "seed_default_users",
]
