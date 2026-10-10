"""SQLAlchemy model for longitudinal clinical events and contradictions."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class ClinicalEvent(Base):
    """
    Represents an extracted, dated clinical event from patient documentation.
    Enforces explicit distinction between the clinical event occurrence date
    and the document creation/upload date.
    """

    __tablename__ = "clinical_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Event classification
    # 'diagnosis', 'medication', 'procedure', 'encounter', 'lab_result', 'allergy'
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Temporal tracking
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    # 'day', 'month', 'year', 'approximate'
    event_date_precision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="day",
    )
    document_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Clinical payload
    description: Mapped[str] = mapped_column(Text, nullable=False)
    value_or_dosage: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 'active', 'historical', 'resolved', 'disputed'
    clinical_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # Contradiction and ambiguity tracking
    contradiction_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    contradiction_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationships
    patient = relationship("Patient", backref="clinical_events")
    document = relationship("Document", backref="clinical_events")
    chunk = relationship("DocumentChunk", backref="clinical_events")

    __table_args__ = (
        Index("idx_events_patient_date", "patient_id", "event_date"),
        Index("idx_events_contradiction", "patient_id", "contradiction_flag"),
    )
