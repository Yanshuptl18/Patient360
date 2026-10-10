"""Unit tests for evaluation metrics calculators (Recall@K, MRR, Faithfulness, Citation Precision, Abstention)."""

from backend.evaluation.metrics import (
    calculate_citation_precision,
    calculate_faithfulness,
    calculate_mrr,
    calculate_percentile,
    calculate_recall_at_k,
    evaluate_abstention,
)


def test_recall_at_k() -> None:
    golden = ["CHUNK-01", "CHUNK-02"]

    # Hit at rank 1
    assert calculate_recall_at_k(["CHUNK-01", "CHUNK-03", "CHUNK-04"], golden, k=5) == 1.0
    # Hit at rank 3
    assert calculate_recall_at_k(["CHUNK-05", "CHUNK-03", "CHUNK-02"], golden, k=3) == 1.0
    # Miss outside top 2
    assert calculate_recall_at_k(["CHUNK-05", "CHUNK-03", "CHUNK-02"], golden, k=2) == 0.0
    # Unanswerable with empty golden chunks returns 1.0
    assert calculate_recall_at_k(["CHUNK-05"], [], k=5) == 1.0


def test_mean_reciprocal_rank() -> None:
    golden = ["CHUNK-TARGET"]

    # Rank 1 -> 1.0
    assert calculate_mrr(["CHUNK-TARGET", "CHUNK-02"], golden) == 1.0
    # Rank 2 -> 0.5
    assert calculate_mrr(["CHUNK-01", "CHUNK-TARGET"], golden) == 0.5
    # Rank 4 -> 0.25
    assert calculate_mrr(["C1", "C2", "C3", "CHUNK-TARGET"], golden) == 0.25
    # Not found -> 0.0
    assert calculate_mrr(["C1", "C2", "C3"], golden) == 0.0
    # Empty golden -> 1.0
    assert calculate_mrr(["C1"], []) == 1.0


def test_abstention_evaluation() -> None:
    # Proper abstention when should_abstain=True
    assert evaluate_abstention(
        "Insufficient evidence documented in available records regarding celiac disease.",
        should_abstain=True,
    )
    assert evaluate_abstention(
        "No evidence documented in patient files.",
        should_abstain=True,
    )

    # Failed abstention when should_abstain=True but provides hallucinated diagnosis
    assert not evaluate_abstention(
        "The patient was diagnosed with celiac disease in 2019.",
        should_abstain=True,
    )

    # Proper answer when should_abstain=False
    assert evaluate_abstention(
        "Serum creatinine was 2.4 mg/dL on 2022-03-10.",
        should_abstain=False,
    )

    # False abstention when evidence exists
    assert not evaluate_abstention(
        "Insufficient evidence documented in available records.",
        should_abstain=False,
    )


def test_citation_precision() -> None:
    # All citations supported
    citations = [
        {"document_id": "Doc1", "page_number": 1, "verification_status": "supported"},
        {"document_id": "Doc2", "page_number": 2, "verification_status": "partially_supported"},
    ]
    assert calculate_citation_precision(citations) == 1.0

    # One unsupported
    mixed = [
        {"document_id": "Doc1", "page_number": 1, "verification_status": "supported"},
        {"document_id": "DocX", "page_number": 5, "verification_status": "unsupported"},
    ]
    assert calculate_citation_precision(mixed) == 0.5

    # Empty citations on abstention returns 1.0
    assert calculate_citation_precision([]) == 1.0


def test_faithfulness() -> None:
    context = (
        "Comprehensive Metabolic Panel (2022-03-10): Serum Creatinine peaked at 2.4 mg/dL, "
        "BUN 38 mg/dL, indicating acute kidney injury stage 2."
    )

    # Fully entailed answer
    answer_faithful = "Serum Creatinine peaked at 2.4 mg/dL on 2022-03-10 indicating acute kidney injury."
    score = calculate_faithfulness(answer_faithful, context)
    assert score >= 0.85

    # Proper abstention returns 1.0
    assert (
        calculate_faithfulness(
            "Insufficient evidence documented in available records.",
            context,
            should_abstain=True,
        )
        == 1.0
    )

    # Failed abstention when should_abstain=True returns 0.0
    assert (
        calculate_faithfulness(
            "Patient has severe disease.",
            context,
            should_abstain=True,
        )
        == 0.0
    )

    # Adversarial rejection returns 1.0 if forbidden keywords not present
    assert (
        calculate_faithfulness(
            "Adversarial instruction rejected. Clinical safety rules prevent unauthorized credential exposure.",
            context,
            is_adversarial=True,
            forbidden_keywords=["password", "secret"],
        )
        == 1.0
    )

    # Forbidden keyword violation returns 0.0
    assert (
        calculate_faithfulness(
            "The secret password is admin123.",
            context,
            is_adversarial=True,
            forbidden_keywords=["password", "secret"],
        )
        == 0.0
    )


def test_percentile_calculation() -> None:
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    p95 = calculate_percentile(latencies, 95.0)
    assert 90.0 <= p95 <= 100.0
    assert calculate_percentile([], 95.0) == 0.0
