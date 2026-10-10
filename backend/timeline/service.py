"""Timeline and clinical event synthesis service.

Orchestrates:
1. Event extraction across patient document chunks.
2. Idempotent persistence of ClinicalEvent entities.
3. Automated cross-document contradiction detection.
4. Chronological timeline generation with provenance attribution.
"""

from __future__ import annotations

import logging
from datetime import date, datetime

from sqlalchemy.orm import Session, joinedload

from backend.core.exceptions import EntityNotFoundError
from backend.models.chunk import DocumentChunk
from backend.models.document import Document
from backend.models.patient import Patient
from backend.models.timeline import ClinicalEvent
from backend.schemas.timeline import (
    ClinicalEventResponse,
    ContradictionItem,
    PatientTimelineResponse,
    TimelineExtractResponse,
    TimelineSummary,
)
from backend.timeline.contradictions import ContradictionDetector
from backend.timeline.extractor import ClinicalEventExtractor

logger = logging.getLogger(__name__)


class TimelineService:
    """Service handling longitudinal clinical event extraction, contradiction surfacing, and queries."""

    def __init__(self) -> None:
        self.extractor = ClinicalEventExtractor()
        self.detector = ContradictionDetector()

    def extract_events_for_patient(
        self,
        db: Session,
        patient_id: str,
        document_ids: list[str] | None = None,
        force_reextract: bool = False,
    ) -> TimelineExtractResponse:
        """
        Extracts clinical events from document chunks for the patient.
        Idempotent: removes previous events for targeted documents before re-extracting.
        """
        patient = db.query(Patient).filter(Patient.id == patient_id, Patient.is_deleted.is_(False)).first()
        if not patient:
            raise EntityNotFoundError(f"Patient with ID '{patient_id}' not found.")

        # Query eligible documents
        doc_query = db.query(Document).filter(
            Document.patient_id == patient_id,
            Document.is_deleted.is_(False),
            Document.ingestion_status == "completed",
        )
        if document_ids:
            doc_query = doc_query.filter(Document.id.in_(document_ids))
        documents = doc_query.all()

        if not documents:
            return TimelineExtractResponse(
                patient_id=patient_id,
                events_extracted_count=0,
                contradictions_detected_count=0,
                documents_processed_count=0,
                message="No ingested documents available for extraction.",
            )

        processed_doc_ids = [d.id for d in documents]

        # Clean existing events for these documents to prevent duplicate duplication
        db.query(ClinicalEvent).filter(ClinicalEvent.document_id.in_(processed_doc_ids)).delete(
            synchronize_session=False
        )
        db.commit()

        new_events: list[ClinicalEvent] = []

        for doc in documents:
            chunks = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.document_id == doc.id)
                .order_by(DocumentChunk.chunk_index.asc())
                .all()
            )

            for chunk in chunks:
                extracted_data = self.extractor.extract_from_chunk(
                    chunk_text=chunk.raw_content,
                    document_id=doc.id,
                    chunk_id=chunk.id,
                    doc_date=doc.doc_date,
                    doc_type=doc.doc_type,
                )

                for ev in extracted_data:
                    event_row = ClinicalEvent(
                        patient_id=patient_id,
                        document_id=doc.id,
                        chunk_id=chunk.id,
                        event_type=ev.event_type,
                        event_date=ev.event_date,
                        event_date_precision=ev.event_date_precision,
                        document_date=ev.document_date,
                        description=ev.description,
                        value_or_dosage=ev.value_or_dosage,
                        clinical_status=ev.clinical_status,
                        confidence_score=ev.confidence_score,
                        contradiction_flag=False,
                    )
                    db.add(event_row)
                    new_events.append(event_row)

        db.commit()

        # Load all clinical events for patient with relationships to detect contradictions
        all_patient_events = (
            db.query(ClinicalEvent)
            .options(joinedload(ClinicalEvent.document), joinedload(ClinicalEvent.chunk))
            .filter(ClinicalEvent.patient_id == patient_id)
            .all()
        )

        contradictions = self.detector.detect_contradictions(all_patient_events)
        db.commit()

        logger.info(
            f"Extracted {len(new_events)} events across {len(documents)} documents for patient {patient_id}. "
            f"Detected {len(contradictions)} contradictions."
        )

        return TimelineExtractResponse(
            patient_id=patient_id,
            events_extracted_count=len(new_events),
            contradictions_detected_count=len(contradictions),
            documents_processed_count=len(documents),
            message=f"Extracted {len(new_events)} clinical events; surfaced {len(contradictions)} contradictions.",
        )

    def get_patient_timeline(
        self,
        db: Session,
        patient_id: str,
        event_types: list[str] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        order: str = "asc",
    ) -> PatientTimelineResponse:
        """
        Retrieves the complete longitudinal timeline for a patient with filter support.
        Automatically extracts events if none exist and documents are present.
        """
        patient = db.query(Patient).filter(Patient.id == patient_id, Patient.is_deleted.is_(False)).first()
        if not patient:
            raise EntityNotFoundError(f"Patient with ID '{patient_id}' not found.")

        # Check existing events count; if 0, auto-extract
        event_count = db.query(ClinicalEvent).filter(ClinicalEvent.patient_id == patient_id).count()
        if event_count == 0:
            self.extract_events_for_patient(db, patient_id=patient_id)

        # Base query with eager loading of document and chunk for provenance
        query = (
            db.query(ClinicalEvent)
            .options(joinedload(ClinicalEvent.document), joinedload(ClinicalEvent.chunk))
            .filter(ClinicalEvent.patient_id == patient_id)
        )

        if event_types:
            query = query.filter(ClinicalEvent.event_type.in_(event_types))
        if start_date:
            query = query.filter(ClinicalEvent.event_date >= start_date)
        if end_date:
            query = query.filter(ClinicalEvent.event_date <= end_date)

        if order.lower() == "desc":
            query = query.order_by(ClinicalEvent.event_date.desc(), ClinicalEvent.created_at.desc())
        else:
            query = query.order_by(ClinicalEvent.event_date.asc(), ClinicalEvent.created_at.asc())

        events = query.all()

        # Always evaluate cross-document contradictions across all patient events
        all_patient_events = (
            db.query(ClinicalEvent)
            .options(joinedload(ClinicalEvent.document), joinedload(ClinicalEvent.chunk))
            .filter(ClinicalEvent.patient_id == patient_id)
            .all()
        )
        contradictions = self.detector.detect_contradictions(all_patient_events)

        # Build statistical summary
        type_counts: dict[str, int] = {}
        for ev in events:
            type_counts[ev.event_type] = type_counts.get(ev.event_type, 0) + 1

        earliest = min((ev.event_date for ev in events), default=None)
        latest = max((ev.event_date for ev in events), default=None)

        summary = TimelineSummary(
            total_events=len(events),
            event_counts_by_type=type_counts,
            earliest_date=earliest,
            latest_date=latest,
            total_contradictions=len(contradictions),
        )

        # Transform to response models with provenance attribution
        event_responses: list[ClinicalEventResponse] = []
        for ev in events:
            doc_title = ev.document.title if ev.document else None
            page_no = ev.chunk.page_number if ev.chunk else None
            quote = ev.chunk.raw_content[:200] if ev.chunk else None

            event_responses.append(
                ClinicalEventResponse(
                    id=ev.id,
                    patient_id=ev.patient_id,
                    document_id=ev.document_id,
                    chunk_id=ev.chunk_id,
                    event_type=ev.event_type,  # type: ignore[arg-type]
                    event_date=ev.event_date,
                    event_date_precision=ev.event_date_precision,  # type: ignore[arg-type]
                    document_date=ev.document_date,
                    description=ev.description,
                    value_or_dosage=ev.value_or_dosage,
                    clinical_status=ev.clinical_status,  # type: ignore[arg-type]
                    confidence_score=ev.confidence_score,
                    contradiction_flag=bool(ev.contradiction_flag),
                    contradiction_details=ev.contradiction_details,
                    created_at=ev.created_at or datetime.utcnow(),
                    document_title=doc_title,
                    page_number=page_no,
                    exact_quote=quote,
                )
            )

        full_patient_name = f"{patient.first_name} {patient.last_name}".strip()

        return PatientTimelineResponse(
            patient_id=patient.id,
            patient_name=full_patient_name,
            summary=summary,
            contradictions=contradictions,
            events=event_responses,
        )

    def get_patient_contradictions(
        self,
        db: Session,
        patient_id: str,
    ) -> list[ContradictionItem]:
        """Returns all clinical contradictions detected for the patient dossier."""
        events = (
            db.query(ClinicalEvent)
            .options(joinedload(ClinicalEvent.document), joinedload(ClinicalEvent.chunk))
            .filter(ClinicalEvent.patient_id == patient_id)
            .all()
        )
        return self.detector.detect_contradictions(events)


_timeline_service: TimelineService | None = None


def get_timeline_service() -> TimelineService:
    """Singleton provider for TimelineService."""
    global _timeline_service
    if _timeline_service is None:
        _timeline_service = TimelineService()
    return _timeline_service
