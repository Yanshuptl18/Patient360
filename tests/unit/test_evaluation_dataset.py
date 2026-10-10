"""Unit tests validating the 50-item synthetic benchmark dataset integrity and category distribution."""

from backend.evaluation.dataset import BENCHMARK_ITEMS_RAW, get_benchmark_dataset
from backend.schemas.evaluation import BenchmarkCategory


def test_benchmark_dataset_distribution() -> None:
    items = get_benchmark_dataset()

    # Total item count must be exactly 50
    assert len(items) == 50
    assert len(BENCHMARK_ITEMS_RAW) == 50

    # Category counts must match Evaluation Plan Section 2
    category_counts: dict[str, int] = {}
    for item in items:
        category_counts[item.category.value] = category_counts.get(item.category.value, 0) + 1

    assert category_counts[BenchmarkCategory.SINGLE_DOC_FACTUAL.value] == 12
    assert category_counts[BenchmarkCategory.MULTI_DOC_LONGITUDINAL.value] == 10
    assert category_counts[BenchmarkCategory.CONTRADICTORY_RECORDS.value] == 8
    assert category_counts[BenchmarkCategory.UNANSWERABLE_ABSTENTION.value] == 8
    assert category_counts[BenchmarkCategory.ADVERSARIAL_INJECTION.value] == 6
    assert category_counts[BenchmarkCategory.RESEARCH_MATRIX.value] == 6


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
        if item.category == BenchmarkCategory.UNANSWERABLE_ABSTENTION:
            assert item.should_abstain is True
            assert len(item.expected_golden_chunk_ids) == 0

        # Contradictory items must have has_contradiction=True and at least 2 golden chunks
        if item.category == BenchmarkCategory.CONTRADICTORY_RECORDS:
            assert item.has_contradiction is True
            assert len(item.expected_golden_chunk_ids) >= 2

        # Adversarial items must have is_adversarial=True and forbidden keywords
        if item.category == BenchmarkCategory.ADVERSARIAL_INJECTION:
            assert item.is_adversarial is True
            assert len(item.forbidden_keywords) >= 1
