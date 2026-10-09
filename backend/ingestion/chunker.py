"""Context-aware semantic chunker with physical page provenance and header injection."""

import re
from dataclasses import dataclass
from typing import Any

from backend.ingestion.extractor import ExtractedPage

# Set of lowercase abbreviations that end with a dot and should not cause sentence splitting
CLINICAL_ABBREVIATIONS = {
    "dr.", "mr.", "ms.", "mrs.", "prof.", "vs.", "eg.", "ie.", "e.g.", "i.e.",
    "approx.", "tab.", "cap.", "mg.", "mcg.", "ml.", "b.i.d.", "t.i.d.",
    "q.i.d.", "p.r.n.", "q.h.s.", "p.o.", "no.", "vol.", "fig.",
}

# Token estimation regex matching words and punctuation tokens
RE_TOKENS = re.compile(r"\w+|[^\w\s]")


def split_into_clinical_sentences(text: str) -> list[str]:
    """
    Splits text into clinical sentences while preserving decimals (e.g. '0.5 mg')
    and medical/Latin abbreviations (e.g. 'b.i.d.', 'p.r.n.', 'Dr.').
    """
    if not text.strip():
        return []

    # First break along explicit paragraph boundaries
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    sentences: list[str] = []

    for para in paragraphs:
        # Split on period followed by whitespace and uppercase/digit
        parts = re.split(r"(\.\s+(?=[A-Z0-9]))", para)
        buffer = ""
        for i in range(0, len(parts), 2):
            piece = parts[i]
            delimiter = parts[i + 1] if i + 1 < len(parts) else ""
            candidate = buffer + piece

            # Inspect trailing word of candidate
            words = candidate.strip().split()
            last_word = words[-1].lower() if words else ""

            # Check if this period is part of a decimal number (e.g. '0.') or known abbreviation
            if (
                last_word in CLINICAL_ABBREVIATIONS
                or last_word.rstrip(".") + "." in CLINICAL_ABBREVIATIONS
                or re.search(r"\d+\.$", candidate.strip())
            ):
                # Don't split; keep accumulating in buffer
                buffer = candidate + delimiter
            else:
                final_sentence = candidate.strip()
                if delimiter and not final_sentence.endswith((".", "!", "?", ":", ";")):
                    final_sentence += "."
                if final_sentence:
                    sentences.append(final_sentence)
                buffer = ""

        if buffer.strip():
            sentences.append(buffer.strip())

    return sentences


def estimate_token_count(text: str) -> int:
    """Estimates subword token count using word/punctuation tokenization."""
    if not text:
        return 0
    tokens = RE_TOKENS.findall(text)
    return max(1, len(tokens))


@dataclass
class GeneratedChunk:
    """Represents a generated semantic chunk ready for database insertion."""

    chunk_index: int
    page_number: int
    content: str
    raw_content: str
    token_count: int
    metadata: dict[str, Any]


class SemanticChunker:
    """
    Context-aware sliding-window chunker operating with physical page provenance.
    Prepends context headers to every chunk:
      [Document: {doc_title} | Page: {page_no} | Date: {doc_date}]
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(
        self,
        pages: list[ExtractedPage],
        doc_title: str,
        doc_date: str | None = None,
        doc_type: str = "patient_record",
        patient_id: str | None = None,
    ) -> list[GeneratedChunk]:
        """
        Chunks extracted document pages while guaranteeing 100% page-number retention.
        """
        chunks: list[GeneratedChunk] = []
        global_chunk_index = 0
        date_str = doc_date or "Undated"

        for page in pages:
            if page.is_blank or not page.text.strip():
                continue

            page_number = page.page_number
            page_text = page.text.strip()
            sentences = split_into_clinical_sentences(page_text)

            if not sentences:
                sentences = [page_text]

            # Build sliding windows of sentences
            current_window: list[str] = []
            current_tokens = 0

            for sentence in sentences:
                sent_tokens = estimate_token_count(sentence)

                if current_tokens + sent_tokens > self.chunk_size and current_window:
                    # Flush current window as a chunk
                    raw_content = " ".join(current_window).strip()
                    header = (
                        f"[Document: {doc_title} | Page: {page_number} | Date: {date_str}]\n"
                    )
                    full_content = f"{header}{raw_content}"
                    token_count = estimate_token_count(full_content)

                    chunks.append(
                        GeneratedChunk(
                            chunk_index=global_chunk_index,
                            page_number=page_number,
                            content=full_content,
                            raw_content=raw_content,
                            token_count=token_count,
                            metadata={
                                "doc_title": doc_title,
                                "doc_type": doc_type,
                                "doc_date": doc_date,
                                "page_number": page_number,
                                "chunk_index": global_chunk_index,
                                "patient_id": patient_id,
                            },
                        )
                    )
                    global_chunk_index += 1

                    # Retain overlap sentences for sliding window
                    overlap_window: list[str] = []
                    overlap_tokens = 0
                    for prev_sent in reversed(current_window):
                        prev_tokens = estimate_token_count(prev_sent)
                        if overlap_tokens + prev_tokens <= self.chunk_overlap:
                            overlap_window.insert(0, prev_sent)
                            overlap_tokens += prev_tokens
                        else:
                            break

                    current_window = overlap_window + [sentence]
                    current_tokens = overlap_tokens + sent_tokens
                else:
                    current_window.append(sentence)
                    current_tokens += sent_tokens

            # Flush remaining window for this page
            if current_window:
                raw_content = " ".join(current_window).strip()
                header = (
                    f"[Document: {doc_title} | Page: {page_number} | Date: {date_str}]\n"
                )
                full_content = f"{header}{raw_content}"
                token_count = estimate_token_count(full_content)

                chunks.append(
                    GeneratedChunk(
                        chunk_index=global_chunk_index,
                        page_number=page_number,
                        content=full_content,
                        raw_content=raw_content,
                        token_count=token_count,
                        metadata={
                            "doc_title": doc_title,
                            "doc_type": doc_type,
                            "doc_date": doc_date,
                            "page_number": page_number,
                            "chunk_index": global_chunk_index,
                            "patient_id": patient_id,
                        },
                    )
                )
                global_chunk_index += 1

        return chunks
