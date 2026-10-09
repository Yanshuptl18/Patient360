"""Audit Log Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogCreate(BaseModel):
    user_id: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    patient_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    status: str = "SUCCESS"
    details_json: str | None = "{}"


class AuditLogResponse(BaseModel):
    id: str
    user_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    patient_id: str | None
    ip_address: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
