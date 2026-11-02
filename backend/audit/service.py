"""Append-only audit service for logging security and clinical access events."""

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.audit.sanitizer import sanitize_audit_details
from backend.models.audit import AuditLog

logger = logging.getLogger(__name__)


def log_audit_event(
    db: Session,
    action: str,
    resource_type: str,
    user_id: str | None = None,
    resource_id: str | None = None,
    patient_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    status: str = "SUCCESS",
    details: dict[str, Any] | None = None,
) -> AuditLog:
    """
    Appends an immutable audit log record to PostgreSQL.
    Guarantees no raw API keys, tokens, or PHI are placed in the log.
    """
    sanitized_details = sanitize_audit_details(details)
    details_str = json.dumps(sanitized_details)
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        patient_id=patient_id,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        details_json=details_str,
    )
    try:
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to record audit log: {exc}")
        raise


def get_audit_logs(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    action: str | None = None,
    user_id: str | None = None,
    patient_id: str | None = None,
) -> list[AuditLog]:
    """Retrieve immutable audit logs ordered chronologically descending."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if patient_id:
        query = query.filter(AuditLog.patient_id == patient_id)
    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
