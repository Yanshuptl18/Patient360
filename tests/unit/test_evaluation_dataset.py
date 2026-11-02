"""Unit tests validating the 150-item synthetic benchmark dataset integrity and category distribution."""

from backend.evaluation.dataset import BENCHMARK_ITEMS_RAW, get_benchmark_dataset
from backend.schemas.evaluation import BenchmarkCategory


def test_benchmark_dataset_distribution() -> None:
    items = get_benchmark_dataset()

    # Total item count must be exactly 150
    assert len(items) == 150
    assert len(BENCHMARK_ITEMS_RAW) == 150

    # Category counts must match 15 benchmark categories
    category_counts: dict[str, int] = {}
    for item in items:
        category_counts[item.category.value] = category_counts.get(item.category.value, 0) + 1

    # Core categories
    assert category_counts[BenchmarkCategory.SINGLE_DOC_FACTUAL.value] == 12
    assert category_counts[BenchmarkCategory.MULTI_DOC_LONGITUDINAL.value] == 10
    assert category_counts[BenchmarkCategory.CONTRADICTORY_RECORDS.value] == 8
    assert category_counts[BenchmarkCategory.UNANSWERABLE_ABSTENTION.value] == 8
    assert category_counts[BenchmarkCategory.ADVERSARIAL_INJECTION.value] == 6
    assert category_counts[BenchmarkCategory.RESEARCH_MATRIX.value] == 6

    # 10 clinical challenge categories (10 items each)
    assert category_counts[BenchmarkCategory.MEDICATION_DOSAGE.value] == 10
    assert category_counts[BenchmarkCategory.MEDICATION_CONTRAINDICATION.value] == 10
    assert category_counts[BenchmarkCategory.SCANNED_OCR_EXTRACTION.value] == 10
    assert category_counts[BenchmarkCategory.LABORATORY_INTERPRETATION.value] == 10
    assert category_counts[BenchmarkCategory.PEDIATRIC_GERIATRIC_CONTEXT.value] == 10
    assert category_counts[BenchmarkCategory.DIAGNOSTIC_CRITERIA.value] == 10
    assert category_counts[BenchmarkCategory.EMERGENCY_TRIAGE.value] == 10
    assert category_counts[BenchmarkCategory.PROCEDURE_HISTORY.value] == 10
    assert category_counts[BenchmarkCategory.ALLERGY_CONFLICT.value] == 10
    assert category_counts[BenchmarkCategory.UNANSWERABLE_MISSING_EVIDENCE.value] == 10


def test_benchmark_item_schema_integrity() -> None:
    items = get_benchmark_dataset()
    ids_seen = set()

    for item in items:
        # All IDs must be unique
        assert item.id not in ids_seen, f"Duplicate item id: {item.id}"
        ids_seen.add(item.id)

        # Basic fields must be populated
        assert len(item.title.strip()) > 5
        assert len(item.query.strip()) > 10

        # Unanswerable items must have should_abstain=True and empty golden chunks
        if item.category in (
            BenchmarkCategory.UNANSWERABLE_ABSTENTION,
            BenchmarkCategory.CLINICAL_ABSTENTION,
            BenchmarkCategory.UNANSWERABLE_MISSING_EVIDENCE,
        ):
            assert item.should_abstain is True
            assert len(item.expected_golden_chunk_ids) == 0

        # Contradictory items must have has_contradiction=True and at least 2 golden chunks
        if item.category in (
            BenchmarkCategory.CONTRADICTORY_RECORDS,
            BenchmarkCategory.CROSS_DOCUMENT_CONTRADICTIONS,
        ):
            assert item.has_contradiction is True
            assert len(item.expected_golden_chunk_ids) >= 2

        # Adversarial items must have is_adversarial=True and forbidden keywords
        if item.category in (
            BenchmarkCategory.ADVERSARIAL_INJECTION,
            BenchmarkCategory.ADVERSARIAL_INJECTIONS,
        ):
            assert item.is_adversarial is True
            assert len(item.forbidden_keywords) >= 1
