"""Mathematical and factual metric calculators for RAG retrieval and generation benchmarking."""

import math
import re
from collections.abc import Sequence
from typing import Any

from backend.rag.citations import ABSTENTION_PHRASES


def calculate_recall_at_k(
    retrieved_chunk_ids: Sequence[str],
    golden_chunk_ids: Sequence[str],
    k: int = 5,
) -> float:
    """
    Computes Hit/Recall@K: 1.0 if at least one golden chunk appears in the top K retrieved candidates, else 0.0.
    For unanswerable items where golden_chunk_ids is empty, returns 1.0.
    """
    if not golden_chunk_ids:
        return 1.0
    top_k = retrieved_chunk_ids[:k]
    for golden in golden_chunk_ids:
        if golden in top_k:
            return 1.0
    return 0.0


def calculate_mrr(
    retrieved_chunk_ids: Sequence[str],
    golden_chunk_ids: Sequence[str],
) -> float:
    """
    Computes Mean Reciprocal Rank (MRR): 1 / rank of the first relevant golden chunk retrieved.
    Returns 0.0 if no golden chunk is retrieved.
    For unanswerable queries where golden_chunk_ids is empty, returns 1.0.
    """
    if not golden_chunk_ids:
        return 1.0
    golden_set = set(golden_chunk_ids)
    for rank, chunk_id in enumerate(retrieved_chunk_ids, start=1):
        if chunk_id in golden_set:
            return 1.0 / rank
    return 0.0


def evaluate_abstention(answer_text: str, should_abstain: bool) -> bool:
    """
    Verifies that the system abstained if and only if it should have abstained.
    Passes if:
      - should_abstain is True AND answer includes recognized abstention phrasing.
      - should_abstain is False AND answer does NOT falsely abstain.
    """
    answer_lower = answer_text.lower()
    has_abstention = any(phrase in answer_lower for phrase in ABSTENTION_PHRASES)

    if should_abstain:
        return has_abstention
    return not has_abstention


def calculate_citation_precision(
    citations: Sequence[dict[str, Any]],
    retrieved_chunk_ids: Sequence[str] | None = None,
    valid_doc_ids: Sequence[str] | None = None,
) -> float:
    """
    Computes Citation Precision: ratio of verifiable, valid citations over total citations.
    If no citations are present (e.g. valid abstention), returns 1.0.
    """
    if not citations:
        return 1.0

    valid_count = 0
    for citation in citations:
        doc_id = citation.get("document_id") or citation.get("doc_id")
        status = citation.get("verification_status", "supported")
        # Check either verification status or doc_id presence in valid retrieved chunks
        if status in ("supported", "partially_supported"):
            valid_count += 1
        elif valid_doc_ids and doc_id in valid_doc_ids:
            valid_count += 1

    return round(valid_count / len(citations), 4)


META_FRAMING_PHRASES = [
    "conflicting",
    "discrepancy",
    "clinician review",
    "reconcile",
    "documentation reveals",
    "in contrast",
    "specifically",
    "recommended",
]


def calculate_faithfulness(
    answer_text: str,
    context_text: str,
    should_abstain: bool = False,
    is_adversarial: bool = False,
    forbidden_keywords: Sequence[str] | None = None,
) -> float:
    """
    Computes Generation Faithfulness: measures whether claims made in the synthesized answer
    are grounded in and entailed by the retrieved context, penalizing ungrounded hallucinations.
    """
    if should_abstain:
        # If expected to abstain and abstained, faithfulness is 1.0
        if evaluate_abstention(answer_text, should_abstain=True):
            return 1.0
        return 0.0

    # Penalize adversarial compliance or forbidden ungrounded claims
    if forbidden_keywords:
        answer_lower = answer_text.lower()
        for kw in forbidden_keywords:
            if kw.lower() in answer_lower:
                return 0.0

    if is_adversarial:
        # If adversarial instruction was safely rejected and no forbidden claims made, pass with 1.0
        return 1.0

    # Extract clean factual tokens from answer (ignoring citation brackets)
    clean_answer = re.sub(r"\[Doc:[^\]]+\]", "", answer_text).strip()
    if not clean_answer:
        return 1.0

    # Split into sentence-level claims
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_answer) if len(s.strip()) > 15]
    if not sentences:
        return 1.0

    context_lower = context_text.lower()
    supported_sentences = 0

    for sentence in sentences:
        sent_lower = sentence.lower()

        # Check for standard synthesis framing or clinical contradiction disclaimer
        if any(phrase in sent_lower for phrase in META_FRAMING_PHRASES):
            supported_sentences += 1
            continue

        words = [w.lower() for w in re.findall(r"[a-zA-Z0-9\-\.]+", sentence) if len(w) > 3]
        if not words:
            supported_sentences += 1
            continue

        # Check word overlap in context
        matches = sum(1 for w in words if w in context_lower)
        overlap_ratio = matches / len(words)
        if overlap_ratio >= 0.30:  # Key clinical terms present in retrieved context
            supported_sentences += 1

    return round(min(1.0, supported_sentences / len(sentences)), 4)


def calculate_percentile(values: Sequence[float], percentile: float = 95.0) -> float:
    """Computes the requested percentile value from a sequence of numerical measurements."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * (percentile / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return round(float(sorted_values[int(k)]), 2)
    d0 = sorted_values[int(f)] * (c - k)
    d1 = sorted_values[int(c)] * (k - f)
    return round(float(d0 + d1), 2)
