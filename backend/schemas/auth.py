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
    DOCTOR = "doctor"
    CLINICIAN = "clinician"
    NURSE = "nurse"
    HOSPITAL_ADMIN = "hospital_admin"
    PATIENT = "patient"


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


class OtpRequest(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: RoleEnum = RoleEnum.REVIEWER


class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    full_name: str | None = None
    role: RoleEnum = RoleEnum.REVIEWER


class OtpResponse(BaseModel):
    status: str = "success"
    message: str
    email: str
    dev_otp: str | None = None


class DemoLoginRequest(BaseModel):
    role_key: str = Field(description="Role key: doctor, nurse, hospital_admin, patient, system_admin")


class DemoRoleItem(BaseModel):
    key: str
    name: str
    title: str
    email: str
    role: str
    department: str
    description: str
    avatar_initials: str


class DemoRolesResponse(BaseModel):
    demo_mode: bool
    roles: list[DemoRoleItem]
