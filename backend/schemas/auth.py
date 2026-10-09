"""Authentication and User Pydantic v2 schemas."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RoleEnum(StrEnum):
    """Platform RBAC user roles."""

    ADMIN = "admin"
    REVIEWER = "reviewer"
    RESEARCHER = "researcher"
    DEMO = "demo"


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    role: RoleEnum = RoleEnum.REVIEWER


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    role: str
    type: str  # "access" or "refresh"
    exp: int
