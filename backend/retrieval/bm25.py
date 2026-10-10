"""In-memory per-patient BM25 sparse keyword retriever for clinical terminology."""

import math
import re
from collections import Counter
from dataclasses import dataclass


@dataclass
class BM25Document:
    """Document chunk representation indexed by BM25."""

    chunk_id: str
    document_id: str
    patient_id: str | None
    page_number: int
    chunk_index: int
    content: str
    raw_content: str
    doc_title: str
    doc_type: str
    doc_date: str | None


@dataclass
class BM25SearchResult:
    """Ranked search result produced by BM25 search."""

    chunk_id: str
    document_id: str
    patient_id: str | None
    page_number: int
    chunk_index: int
    content: str
    raw_content: str
    score: float
    doc_title: str
    doc_type: str
    doc_date: str | None


# Clinical token pattern that preserves hyphens in medical terms (e.g., NT-proBNP, EGFR-mutated, L858R, COVID-19)
CLINICAL_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+(?:[-/][a-zA-Z0-9]+)*")


def tokenize_clinical_text(text: str) -> list[str]:
    """Tokenizes text while preserving clinical acronyms, hyphens, and alphanumeric codes."""
    return [match.group(0).lower() for match in CLINICAL_TOKEN_PATTERN.finditer(text)]


class BM25Index:
    """
    In-memory Okapi BM25 index with clinical tokenization.
    Parameters:
        k1: Term frequency saturation parameter (default: 1.5)
        b: Document length normalization parameter (default: 0.75)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.documents: list[BM25Document] = []
        self.doc_lengths: list[int] = []
        self.avg_doc_length: float = 0.0
        self.term_doc_frequencies: dict[str, int] = {}
        self.doc_term_frequencies: list[Counter[str]] = []
        self.total_docs: int = 0

    def index_documents(self, documents: list[BM25Document]) -> None:
        """Indexes or replaces documents in this patient's BM25 index."""
        self.documents = list(documents)
        self.total_docs = len(self.documents)
        self.doc_lengths = []
        self.doc_term_frequencies = []
        self.term_doc_frequencies = {}

        if self.total_docs == 0:
            self.avg_doc_length = 0.0
            return

        total_length = 0
        for doc in self.documents:
            tokens = tokenize_clinical_text(doc.content)
            tf = Counter(tokens)
            doc_len = len(tokens)

            self.doc_lengths.append(doc_len)
            self.doc_term_frequencies.append(tf)
            total_length += doc_len

            # Update document frequencies (DF) for each unique term
            for term in tf:
                self.term_doc_frequencies[term] = self.term_doc_frequencies.get(term, 0) + 1

        self.avg_doc_length = total_length / self.total_docs

    def add_documents(self, documents: list[BM25Document]) -> None:
        """Appends new documents and updates the index."""
        existing_docs = {doc.chunk_id: doc for doc in self.documents}
        for doc in documents:
            existing_docs[doc.chunk_id] = doc
        self.index_documents(list(existing_docs.values()))

    def delete_document_chunks(self, document_id: str) -> None:
        """Removes all chunks belonging to a document and rebuilds the index."""
        remaining = [d for d in self.documents if d.document_id != document_id]
        self.index_documents(remaining)

    def search(self, query: str, top_k: int = 20) -> list[BM25SearchResult]:
        """
        Calculates Okapi BM25 score for the query across indexed chunks.
        Returns top-k documents sorted by score descending.
        """
        if self.total_docs == 0:
            return []

        query_tokens = tokenize_clinical_text(query)
        if not query_tokens:
            return []

        scores: list[float] = [0.0] * self.total_docs

        for token in query_tokens:
            df = self.term_doc_frequencies.get(token, 0)
            if df == 0:
                continue

            # Standard Okapi BM25 IDF formulation: ln((N - df + 0.5) / (df + 0.5) + 1)
            idf = math.log(((self.total_docs - df + 0.5) / (df + 0.5)) + 1.0)

            for i in range(self.total_docs):
                tf = self.doc_term_frequencies[i].get(token, 0)
                if tf == 0:
                    continue

                doc_len = self.doc_lengths[i]
                # BM25 term weight
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1.0, self.avg_doc_length)))
                scores[i] += idf * (numerator / denominator)

        # Pair indices with positive scores
        scored_pairs = [
            (i, scores[i]) for i in range(self.total_docs) if scores[i] > 0.0
        ]
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        results: list[BM25SearchResult] = []
        for idx, score in scored_pairs[:top_k]:
            doc = self.documents[idx]
            results.append(
                BM25SearchResult(
                    chunk_id=doc.chunk_id,
                    document_id=doc.document_id,
                    patient_id=doc.patient_id,
                    page_number=doc.page_number,
                    chunk_index=doc.chunk_index,
                    content=doc.content,
                    raw_content=doc.raw_content,
                    score=round(score, 4),
                    doc_title=doc.doc_title,
                    doc_type=doc.doc_type,
                    doc_date=doc.doc_date,
                )
            )

        return results


class PatientBM25Registry:
    """Singleton per-patient in-memory index partition registry."""

    def __init__(self) -> None:
        self._indexes: dict[str, BM25Index] = {}

    def get_index_for_patient(self, patient_id: str) -> BM25Index:
        """Returns the in-memory BM25 index for the specified patient dossier."""
        if patient_id not in self._indexes:
            self._indexes[patient_id] = BM25Index()
        return self._indexes[patient_id]

    def index_chunks(self, patient_id: str, chunks: list[BM25Document]) -> None:
        """Updates the patient's BM25 index with fresh chunks."""
        index = self.get_index_for_patient(patient_id)
        index.add_documents(chunks)

    def delete_document_chunks(self, patient_id: str, document_id: str) -> None:
        """Purges document chunks from the patient's BM25 index."""
        if patient_id in self._indexes:
            self._indexes[patient_id].delete_document_chunks(document_id)

    def clear(self) -> None:
        """Clears all in-memory indexes (useful for test isolation)."""
        self._indexes.clear()


_bm25_registry: PatientBM25Registry | None = None


def get_bm25_registry() -> PatientBM25Registry:
    """Returns the singleton per-patient BM25 registry."""
    global _bm25_registry
    if _bm25_registry is None:
        _bm25_registry = PatientBM25Registry()
    return _bm25_registry
