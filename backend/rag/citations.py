"""Citation extraction, provenance verification, and claim entailment analysis."""

import re
from collections.abc import Sequence
from typing import Literal

from backend.retrieval.rrf import HybridSearchResult
from backend.schemas.rag import CitationItem
from backend.vector.store import VectorSearchResult

CITATION_REGEX = re.compile(
    r"\[Doc:\s*([a-zA-Z0-9_\-]+),\s*Page:?\s*(\d+)\]",
    re.IGNORECASE,
)

ABSTENTION_PHRASES = [
    "insufficient evidence documented in available records",
    "insufficient evidence",
    "no evidence documented",
    "not documented in available records",
]

NEGATION_PATTERNS = [
    r"\bno\b",
    r"\bnot\b",
    r"\bnever\b",
    r"\bdenies\b",
    r"\bdenied\b",
    r"\bnegative\b",
    r"\bnegative for\b",
    r"\bwithout\b",
    r"\bresolved\b",
    r"\bdiscontinued\b",
    r"\babsent\b",
    r"\brules out\b",
    r"\bruled out\b",
    r"\bfree of\b",
    r"\bunremarkable\b",
]
NEGATION_REGEX = re.compile("|".join(NEGATION_PATTERNS), re.IGNORECASE)

NUMERIC_TOKEN_REGEX = re.compile(r"\d+(?:\.\d+)?")


class CitationVerifier:
    """Parses citation markers and verifies them against retrieved source chunks."""

    def verify(
        self,
        answer: str,
        retrieved_chunks: Sequence[VectorSearchResult | HybridSearchResult],
    ) -> tuple[list[CitationItem], bool]:
        """
        Parses all citations in the synthesized answer and checks provenance against candidate chunks.
        Returns:
            Tuple of (list[CitationItem], is_abstention: bool)
        """
        answer_lower = answer.lower()
        is_abstention = any(phrase in answer_lower for phrase in ABSTENTION_PHRASES)
        if is_abstention:
            return [], True

        # Index retrieved chunks by (document_id, page_number)
        chunk_map: dict[tuple[str, int], list[VectorSearchResult | HybridSearchResult]] = {}
        for chunk in retrieved_chunks:
            key = (chunk.document_id, chunk.page_number)
            chunk_map.setdefault(key, []).append(chunk)

        # Split answer into sentence blocks to associate claims with citations
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]

        citations: list[CitationItem] = []
        seen_citations: set[tuple[str, int, str]] = set()

        for sentence in sentences:
            matches = list(CITATION_REGEX.finditer(sentence))
            if not matches:
                continue

            # Strip citation tags from sentence to derive claim text
            claim_text = CITATION_REGEX.sub("", sentence).strip()

            for match in matches:
                doc_id = match.group(1).strip()
                page_no = int(match.group(2).strip())

                # Find candidate chunks matching this document and page
                matching_chunks = chunk_map.get((doc_id, page_no), [])
                if not matching_chunks:
                    # Also try partial UUID match if model abbreviated doc_id
                    for (c_doc, c_page), ch_list in chunk_map.items():
                        if (doc_id in c_doc or c_doc in doc_id) and page_no == c_page:
                            matching_chunks = ch_list
                            doc_id = c_doc
                            break

                if matching_chunks:
                    best_chunk = matching_chunks[0]
                    doc_title = best_chunk.doc_title
                    # Calculate token overlap between claim and chunk content
                    claim_words = set(re.findall(r"\w+", claim_text.lower()))
                    chunk_words = set(re.findall(r"\w+", best_chunk.content.lower()))
                    overlap = len(claim_words.intersection(chunk_words))
                    overlap_ratio = overlap / max(1, len(claim_words))

                    # Extract representative excerpt as exact quote matching claim tokens
                    raw_content = best_chunk.raw_content.strip()
                    sentences = [
                        s.strip()
                        for s in re.split(r"[\n.]", raw_content)
                        if s.strip() and len(s.strip()) > 8
                    ]
                    best_matching_sentence = ""
                    max_sent_overlap = -1
                    for s in sentences:
                        s_words = set(re.findall(r"\w+", s.lower()))
                        sent_overlap = len(claim_words.intersection(s_words))
                        if sent_overlap > max_sent_overlap:
                            max_sent_overlap = sent_overlap
                            best_matching_sentence = s

                    exact_quote = (
                        best_matching_sentence
                        if best_matching_sentence
                        else (raw_content.split("\n")[0] if raw_content else best_chunk.content)
                    )[:200].strip()

                    # Check polarity / negation conflict
                    claim_has_neg = bool(NEGATION_REGEX.search(claim_text))
                    target_passage = best_matching_sentence if best_matching_sentence else raw_content
                    passage_has_neg = bool(NEGATION_REGEX.search(target_passage))
                    polarity_conflict = (claim_has_neg != passage_has_neg)

                    # Check numeric and dosage consistency
                    claim_numbers = set(NUMERIC_TOKEN_REGEX.findall(claim_text))
                    chunk_numbers = set(NUMERIC_TOKEN_REGEX.findall(raw_content))
                    missing_numbers = claim_numbers - chunk_numbers - {str(page_no)}

                    status: Literal["supported", "partially_supported", "unsupported"]
                    if polarity_conflict:
                        status = "unsupported"
                    elif missing_numbers and overlap_ratio >= 0.35:
                        status = "partially_supported"
                    elif overlap_ratio >= 0.35:
                        status = "supported"
                    elif overlap_ratio >= 0.15:
                        status = "partially_supported"
                    else:
                        status = "unsupported"
                else:
                    doc_title = f"Document {doc_id[:8]}"
                    exact_quote = "Passage not present in active retrieval candidates."
                    status = "unsupported"

                dedup_key = (doc_id, page_no, claim_text)
                if dedup_key not in seen_citations:
                    seen_citations.add(dedup_key)
                    citations.append(
                        CitationItem(
                            document_id=doc_id,
                            document_title=doc_title,
                            page_number=page_no,
                            exact_quote=exact_quote,
                            claim_text=claim_text,
                            verification_status=status,
                        )
                    )

        return citations, False
