"""SQLAlchemy model for extracted biomedical research studies and clinical guidelines."""

import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

if TYPE_CHECKING:
    from backend.models.document import Document


class ResearchStudy(Base):
    """Structured extraction of biomedical research publication parameters and trial methodologies."""

    __tablename__ = "research_studies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    pmid: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    doi: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[str | None] = mapped_column(Text, nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    study_design: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )  # e.g. Randomized Controlled Trial, Systematic Review, Cohort Study, Meta-Analysis
    population_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    intervention: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="research_study")

    def __repr__(self) -> str:
        return f"<ResearchStudy {self.title[:40]} (Design: {self.study_design}, N={self.sample_size})>"
