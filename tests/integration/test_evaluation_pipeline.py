"""Integration tests for the Evaluation Laboratory runner and REST API endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.evaluation.runner import BenchmarkRunner
from backend.schemas.evaluation import EvaluationRunRequest


def test_benchmark_runner_full_suite() -> None:
    """Verifies that the BenchmarkRunner completes all 50 items and meets all core quality targets."""
    runner = BenchmarkRunner()
    run_record = runner.run(request=EvaluationRunRequest(name="Full Test Suite"))

    assert run_record.total_items == 50
    assert run_record.passed_items == 50

    # Assert primary target criteria from docs/EVALUATION_PLAN.md
    assert run_record.recall_at_5 >= 0.85
    assert run_record.mrr >= 0.75
    assert run_record.faithfulness >= 0.85
    assert run_record.citation_precision >= 0.90
    assert run_record.abstention_accuracy == 1.0
    assert run_record.p95_retrieval_latency_ms <= 1500.0
    assert run_record.p95_e2e_latency_ms <= 4000.0

    targets = run_record.summary_metrics.get("targets", {})
    assert targets["recall_at_5"]["met"] is True
    assert targets["mrr"]["met"] is True
    assert targets["faithfulness"]["met"] is True
    assert targets["citation_precision"]["met"] is True
    assert targets["abstention_accuracy"]["met"] is True

    categories = run_record.summary_metrics.get("categories", {})
    assert len(categories) == 6
    assert categories["single_doc_factual"]["total_items"] == 12
    assert categories["multi_doc_longitudinal"]["total_items"] == 10
    assert categories["contradictory_records"]["total_items"] == 8
    assert categories["unanswerable_abstention"]["total_items"] == 8
    assert categories["adversarial_injection"]["total_items"] == 6
    assert categories["research_matrix"]["total_items"] == 6


def test_evaluation_api_endpoints(
    client: TestClient,
    reviewer_headers: dict[str, str],
    db: Session,
) -> None:
    """Tests the /api/v1/evaluation API lifecycle including dataset inspection, run triggering, and history."""
    # 1. Unauthenticated requests are rejected with 401
    unauth_resp = client.get("/api/v1/evaluation/benchmark-dataset")
    assert unauth_resp.status_code == 401

    # 2. Inspect benchmark dataset
    ds_resp = client.get(
        "/api/v1/evaluation/benchmark-dataset",
        headers=reviewer_headers,
    )
    assert ds_resp.status_code == 200
    dataset = ds_resp.json()
    assert len(dataset) == 50
    assert dataset[0]["id"] == "BENCH-FACT-01"

    # 3. Trigger evaluation run via API
    run_payload = {
        "name": "Integration Test Run",
        "mode": "hybrid",
        "limit": 10,
    }
    create_resp = client.post(
        "/api/v1/evaluation/runs",
        json=run_payload,
        headers=reviewer_headers,
    )
    assert create_resp.status_code == 201
    run_data = create_resp.json()
    run_id = run_data["id"]
    assert run_data["total_items"] == 10
    assert run_data["passed_items"] == 10
    assert run_data["faithfulness"] >= 0.85
    assert len(run_data["item_results"]) == 10

    # 4. List runs
    list_resp = client.get(
        "/api/v1/evaluation/runs",
        headers=reviewer_headers,
    )
    assert list_resp.status_code == 200
    runs_list = list_resp.json()
    assert len(runs_list) >= 1
    assert any(r["id"] == run_id for r in runs_list)

    # 5. Get detailed run report
    detail_resp = client.get(
        f"/api/v1/evaluation/runs/{run_id}",
        headers=reviewer_headers,
    )
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["id"] == run_id
    assert "summary_metrics" in detail_data
    assert len(detail_data["item_results"]) == 10

    # 6. Non-existent run returns 404
    not_found_resp = client.get(
        "/api/v1/evaluation/runs/non-existent-uuid",
        headers=reviewer_headers,
    )
    assert not_found_resp.status_code == 404
