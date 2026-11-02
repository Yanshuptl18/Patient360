"""SQLAlchemy model for persistent, durable LangGraph clinical research workflows."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

if TYPE_CHECKING:
    from backend.models.patient import Patient
    from backend.models.user import User


class AgentWorkflowRun(Base):
    """Persistent storage record for bounded clinical research workflow runs."""

    __tablename__ = "agent_workflow_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planning", index=True)
    approval_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", index=True
    )
    iteration_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_iterations: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    elapsed_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Serialized execution telemetry and state payloads
    plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieved_evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    contradictions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_synthesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Human-in-the-Loop audit verification fields
    reviewer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reviewer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewer_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    review_decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient")
    creator: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    reviewer: Mapped["User | None"] = relationship("User", foreign_keys=[reviewer_id])

    def __repr__(self) -> str:
        return f"<AgentWorkflowRun {self.id} (Status: {self.status}, Decision: {self.approval_status})>"

