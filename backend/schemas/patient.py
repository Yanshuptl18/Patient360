"""Pydantic schemas for Patient management."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PatientBase(BaseModel):
    mrn_synthetic: str = Field(min_length=3, max_length=64, description="Synthetic Medical Record Number")
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    gender: str = Field(min_length=1, max_length=20)
    primary_condition: str | None = Field(default=None, max_length=255)


class PatientCreate(PatientBase):
    pass


class PatientResponse(PatientBase):
    id: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class PermissionGrantRequest(BaseModel):
    user_id: str
    permission_level: str = Field(default="read", pattern="^(read|write|admin)$")
