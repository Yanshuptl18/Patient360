"""Evaluation service managing benchmark execution lifecycles, database persistence, and history."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.audit.service import log_audit_event
from backend.evaluation.dataset import get_benchmark_dataset
from backend.evaluation.runner import BenchmarkRunner
from backend.models.evaluation import EvaluationRun
from backend.schemas.evaluation import (
    EvaluationBenchmarkItem,
    EvaluationRunRequest,
)

logger = logging.getLogger(__name__)


class EvaluationService:
    """Orchestrates benchmark runs, database persistence, and telemetry audit records."""

    def run_benchmark(
        self,
        db: Session,
        request: EvaluationRunRequest | None = None,
        user_id: str | None = None,
    ) -> EvaluationRun:
        """Executes the benchmark runner, saves the result to database, and creates an audit trail."""
        runner = BenchmarkRunner(db=db)
        req = request or EvaluationRunRequest()

        run_record = runner.run(request=req, created_by_id=user_id)

        # Persist to database
        db.add(run_record)
        db.commit()
        db.refresh(run_record)

        # Append-only audit logging
        log_audit_event(
            db=db,
            user_id=user_id,
            action="EVALUATION_BENCHMARK_EXECUTED",
            resource_type="evaluation_run",
            resource_id=run_record.id,
            status="SUCCESS",
            details={
                "name": run_record.name,
                "mode": run_record.mode,
                "git_commit": run_record.git_commit,
                "total_items": run_record.total_items,
                "passed_items": run_record.passed_items,
                "faithfulness": run_record.faithfulness,
                "citation_precision": run_record.citation_precision,
                "recall_at_5": run_record.recall_at_5,
            },
        )

        logger.info(
            "Evaluation run %s completed: mode=%s, passed=%d/%d, faith=%.2f, cit_prec=%.2f",
            run_record.id,
            run_record.mode,
            run_record.passed_items,
            run_record.total_items,
            run_record.faithfulness,
            run_record.citation_precision,
        )
        return run_record

    def list_runs(self, db: Session, limit: int = 50) -> list[EvaluationRun]:
        """Returns historical evaluation runs ordered by newest first."""
        stmt = select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def get_run(self, db: Session, run_id: str) -> EvaluationRun | None:
        """Retrieves a single evaluation run by ID."""
        stmt = select(EvaluationRun).where(EvaluationRun.id == run_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_dataset(self) -> list[EvaluationBenchmarkItem]:
        """Returns the frozen 50-item benchmark dataset definition."""
        return get_benchmark_dataset()


_evaluation_service: EvaluationService | None = None


def get_evaluation_service() -> EvaluationService:
    """Dependency provider returning singleton EvaluationService instance."""
    global _evaluation_service
    if _evaluation_service is None:
        _evaluation_service = EvaluationService()
    return _evaluation_service
