"""Read-only clinical intelligence tools guarded by patient-level authorization."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.core.exceptions import AuthorizationError
from backend.models.document import Document
from backend.models.user import User
from backend.patients.service import check_user_patient_access, get_patient
from backend.retrieval.service import get_hybrid_retrieval_service
from backend.timeline.service import get_timeline_service

logger = logging.getLogger(__name__)


def get_patient_dossier(
    db: Session,
    user: User,
    patient_id: str,
) -> dict[str, Any]:
    """
    Read-only tool: Retrieves demographic, clinical baseline, and document metadata for a patient.
    Guarded by check_user_patient_access.
    """
    if not check_user_patient_access(db, user=user, patient_id=patient_id, min_permission="read"):
        raise AuthorizationError(f"Access denied: user '{user.id}' lacks permission for patient '{patient_id}'.")

    patient = get_patient(db, patient_id)
    doc_count = (
        db.query(Document)
        .filter(Document.patient_id == patient_id, Document.is_deleted.is_(False))
        .count()
    )

    return {
        "patient_id": patient.id,
        "mrn_synthetic": patient.mrn_synthetic,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "full_name": f"{patient.first_name} {patient.last_name}".strip(),
        "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
        "gender": patient.gender,
        "primary_condition": patient.primary_condition,
        "document_count": doc_count,
        "created_at": patient.created_at.isoformat() if patient.created_at else None,
    }


def search_clinical_evidence(
    db: Session,
    user: User,
    patient_id: str,
    query: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Read-only tool: Executes hybrid dense (FastEmbed/Qdrant) + sparse (BM25) RRF search.
    Guarded by check_user_patient_access.
    """
    if not check_user_patient_access(db, user=user, patient_id=patient_id, min_permission="read"):
        raise AuthorizationError(f"Access denied: user '{user.id}' lacks permission for patient '{patient_id}'.")

    retrieval_service = get_hybrid_retrieval_service()
    results, _ = retrieval_service.search(
        query=query,
        patient_id=patient_id,
        top_k=top_k,
        db=db,
    )

    evidence_items: list[dict[str, Any]] = []
    for item in results:
        evidence_items.append(
            {
                "chunk_id": item.chunk_id,
                "document_id": item.document_id,
                "doc_title": item.doc_title,
                "doc_type": item.doc_type,
                "page_number": item.page_number,
                "rrf_score": round(item.rrf_score, 4),
                "content": item.content,
            }
        )

    return evidence_items


def query_longitudinal_timeline(
    db: Session,
    user: User,
    patient_id: str,
    event_type: str | None = None,
) -> list[dict[str, Any]]:
    """
    Read-only tool: Retrieves chronologically ordered clinical events and provenance.
    Guarded by check_user_patient_access.
    """
    if not check_user_patient_access(db, user=user, patient_id=patient_id, min_permission="read"):
        raise AuthorizationError(f"Access denied: user '{user.id}' lacks permission for patient '{patient_id}'.")

    timeline_service = get_timeline_service()
    timeline = timeline_service.get_patient_timeline(db=db, patient_id=patient_id)

    events: list[dict[str, Any]] = []
    for ev in timeline.events:
        ev_type_str = str(ev.event_type)
        if event_type and ev_type_str.lower() != event_type.lower():
            continue

        events.append(
            {
                "id": ev.id,
                "event_type": ev_type_str,
                "event_date": str(ev.event_date) if ev.event_date else None,
                "description": ev.description,
                "value_or_dosage": ev.value_or_dosage,
                "clinical_status": str(ev.clinical_status),
                "document_title": ev.document_title,
                "page_number": ev.page_number,
                "exact_quote": ev.exact_quote,
            }
        )

    return events


def inspect_clinical_contradictions(
    db: Session,
    user: User,
    patient_id: str,
) -> list[dict[str, Any]]:
    """
    Read-only tool: Surfaces conflicting clinical findings across document dates/sources.
    Guarded by check_user_patient_access.
    """
    if not check_user_patient_access(db, user=user, patient_id=patient_id, min_permission="read"):
        raise AuthorizationError(f"Access denied: user '{user.id}' lacks permission for patient '{patient_id}'.")

    timeline_service = get_timeline_service()
    contradictions = timeline_service.get_patient_contradictions(db=db, patient_id=patient_id)

    contradiction_items: list[dict[str, Any]] = []
    for idx, c in enumerate(contradictions, 1):
        contradiction_items.append(
            {
                "contradiction_id": f"contra_{idx}",
                "topic": f"{c.conflict_type.replace('_', ' ').title()}",
                "conflict_type": str(c.conflict_type),
                "severity": str(c.severity),
                "description": c.explanation,
                "event_ids": [c.event_id_1, c.event_id_2],
                "event_1_summary": c.event_1_summary,
                "event_2_summary": c.event_2_summary,
                "resolution_recommendation": c.suggested_resolution or "Clinician chart review recommended.",
            }
        )

    return contradiction_items

