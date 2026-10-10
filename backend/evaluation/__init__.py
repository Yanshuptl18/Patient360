"""Evaluation package for RAG and research benchmarking."""

from backend.evaluation.dataset import get_benchmark_dataset
from backend.evaluation.metrics import (
    calculate_citation_precision,
    calculate_faithfulness,
    calculate_mrr,
    calculate_percentile,
    calculate_recall_at_k,
    evaluate_abstention,
)
from backend.evaluation.runner import BenchmarkRunner
from backend.evaluation.service import EvaluationService, get_evaluation_service

__all__ = [
    "get_benchmark_dataset",
    "calculate_recall_at_k",
    "calculate_mrr",
    "evaluate_abstention",
    "calculate_citation_precision",
    "calculate_faithfulness",
    "calculate_percentile",
    "BenchmarkRunner",
    "EvaluationService",
    "get_evaluation_service",
]
