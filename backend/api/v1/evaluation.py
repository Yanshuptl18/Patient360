"""API endpoints for triggering RAG evaluation runs and inspecting historical benchmarks."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user, get_db
from backend.evaluation.service import EvaluationService, get_evaluation_service
from backend.models.user import User
from backend.schemas.evaluation import (
    EvaluationBenchmarkItem,
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationRunSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/runs",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger an automated RAG evaluation benchmark run",
)
def trigger_evaluation_run(
    payload: EvaluationRunRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EvaluationService, Depends(get_evaluation_service)],
) -> EvaluationRunResponse:
    """
    Executes the 50-item synthetic benchmark suite in the specified retrieval mode
    (hybrid RRF, dense-only, sparse-only), persists metrics to the database, and creates an audit record.
    """
    run_record = service.run_benchmark(
        db=db,
        request=payload,
        user_id=current_user.id,
    )
    return EvaluationRunResponse.model_validate(run_record)


@router.get(
    "/runs",
    response_model=list[EvaluationRunSummary],
    summary="List historical evaluation benchmark runs",
)
def list_evaluation_runs(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EvaluationService, Depends(get_evaluation_service)],
    limit: int = Query(default=50, ge=1, le=100),
) -> list[EvaluationRunSummary]:
    """Retrieves historical benchmark runs ordered by most recent execution."""
    runs = service.list_runs(db=db, limit=limit)
    return [EvaluationRunSummary.model_validate(r) for r in runs]


@router.get(
    "/runs/{run_id}",
    response_model=EvaluationRunResponse,
    summary="Get detailed evaluation run metrics and item results",
)
def get_evaluation_run(
    run_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EvaluationService, Depends(get_evaluation_service)],
) -> EvaluationRunResponse:
    """Returns comprehensive evaluation results including 50 individual item evaluations and category breakdowns."""
    run = service.get_run(db=db, run_id=run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Evaluation run '{run_id}' not found.",
            },
        )
    return EvaluationRunResponse.model_validate(run)


@router.get(
    "/benchmark-dataset",
    response_model=list[EvaluationBenchmarkItem],
    summary="Inspect frozen 50-item synthetic clinical benchmark dataset",
)
def get_benchmark_dataset(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EvaluationService, Depends(get_evaluation_service)],
) -> list[EvaluationBenchmarkItem]:
    """Inspects the 50 curated synthetic test items distributed across the 6 clinical evaluation categories."""
    return service.get_dataset()
