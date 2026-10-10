"""SQLAlchemy model for evaluation benchmark execution runs and metrics."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class EvaluationRun(Base):
    """Persisted record of an automated or triggered RAG benchmark evaluation run."""

    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Benchmark Run")
    git_commit: Mapped[str] = mapped_column(String(64), nullable=False, default="HEAD")
    mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default="hybrid", index=True
    )  # "hybrid", "dense_only", "sparse_only"
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    passed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Core Target Quantitative Metrics
    recall_at_5: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mrr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    faithfulness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    citation_precision: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    abstention_accuracy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Latency Telemetry (ms)
    p95_retrieval_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    p95_e2e_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Category breakdown & detailed item results
    summary_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    item_results: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    created_by_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<EvaluationRun {self.name} [{self.mode}] - "
            f"Faithfulness={self.faithfulness:.2f}, CitationPrec={self.citation_precision:.2f}>"
        )
