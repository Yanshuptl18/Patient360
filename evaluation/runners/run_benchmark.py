"""CLI runner for executing the 50-item synthetic clinical evaluation benchmark."""

import argparse
import sys
from typing import Any

from backend.core.database import SessionLocal
from backend.evaluation.runner import BenchmarkRunner
from backend.evaluation.service import get_evaluation_service
from backend.schemas.evaluation import EvaluationRunRequest


def print_scorecard(run_data: Any) -> None:
    """Prints an ASCII performance scorecard formatted for terminal inspection."""
    metrics = run_data.summary_metrics or {}
    categories = metrics.get("categories", {})

    print("\n" + "=" * 78)
    print("           PATIENT360 RAG EVALUATION LABORATORY — BENCHMARK RESULTS")
    print("=" * 78)
    print(f"Run Name:      {run_data.name}")
    print(f"Retrieval Mode:{run_data.mode.upper()}")
    print(f"Git Commit:    {run_data.git_commit}")
    print(f"Total Items:   {run_data.total_items} | Passed: {run_data.passed_items} ({run_data.passed_items / run_data.total_items * 100:.1f}%)")
    print("-" * 78)
    print(f"{'Target Metric':<28} | {'Target':<10} | {'Achieved':<12} | {'Status':<10}")
    print("-" * 78)

    metric_rows = [
        ("Retrieval Recall@5", ">= 0.85", f"{run_data.recall_at_5:.4f}", run_data.recall_at_5 >= 0.85),
        ("Mean Reciprocal Rank (MRR)", ">= 0.75", f"{run_data.mrr:.4f}", run_data.mrr >= 0.75),
        ("Generation Faithfulness", ">= 0.85", f"{run_data.faithfulness:.4f}", run_data.faithfulness >= 0.85),
        ("Citation Precision", ">= 0.90", f"{run_data.citation_precision:.4f}", run_data.citation_precision >= 0.90),
        ("Abstention Accuracy", "100%", f"{run_data.abstention_accuracy * 100:.1f}%", run_data.abstention_accuracy >= 0.99),
        ("Retrieval P95 Latency", "<= 1500ms", f"{run_data.p95_retrieval_latency_ms:.1f}ms", run_data.p95_retrieval_latency_ms <= 1500),
        ("End-to-End P95 Latency", "<= 4000ms", f"{run_data.p95_e2e_latency_ms:.1f}ms", run_data.p95_e2e_latency_ms <= 4000),
    ]

    for label, target, achieved, status in metric_rows:
        status_str = "[ PASS ]" if status else "[ FAIL ]"
        print(f"{label:<28} | {target:<10} | {achieved:<12} | {status_str:<10}")

    print("-" * 78)
    print(f"{'Category Breakdown':<32} | {'Items':<7} | {'Passed':<8} | {'Pass Rate':<10} | {'Avg Faith':<10}")
    print("-" * 78)

    for cat_key, cat_data in categories.items():
        label = cat_data.get("category_label", cat_key)
        tot = cat_data.get("total_items", 0)
        pas = cat_data.get("passed_items", 0)
        rate = f"{cat_data.get('pass_rate', 0.0) * 100:.1f}%"
        faith = f"{cat_data.get('avg_faithfulness', 0.0):.2f}"
        print(f"{label:<32} | {tot:<7} | {pas:<8} | {rate:<10} | {faith:<10}")

    print("=" * 78 + "\n")


def main() -> None:
    """CLI entry point for running the evaluation benchmark suite."""
    parser = argparse.ArgumentParser(description="Patient360 Synthetic Clinical Benchmark Runner")
    parser.add_argument(
        "--mode",
        choices=["hybrid", "dense_only", "sparse_only"],
        default="hybrid",
        help="Retrieval mode: hybrid (default), dense_only, or sparse_only",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of benchmark items to execute (default: all 50)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="Synthetic Clinical Benchmark (50 items)",
        help="Custom name for this evaluation run",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not persist run results to database",
    )

    args = parser.parse_args()

    request = EvaluationRunRequest(
        name=args.name,
        mode=args.mode,
        limit=args.limit,
    )

    if args.no_save:
        runner = BenchmarkRunner()
        run_record = runner.run(request=request)
    else:
        try:
            db = SessionLocal()
            service = get_evaluation_service()
            run_record = service.run_benchmark(db=db, request=request)
            db.close()
        except Exception as err:
            print(f"Notice: Database persistence unavailable ({err}). Executing benchmark in standalone mode.")
            runner = BenchmarkRunner()
            run_record = runner.run(request=request)

    print_scorecard(run_record)

    # Return non-zero exit code if primary quality targets are breached
    if run_record.faithfulness < 0.85 or run_record.citation_precision < 0.90:
        print("ERROR: Benchmark failed primary quality gates (Faithfulness >= 0.85, Precision >= 0.90).")
        sys.exit(1)


if __name__ == "__main__":
    main()
