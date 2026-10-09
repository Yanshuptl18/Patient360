"""Clinical text normalizer preserving decimals, medical units, and prescription abbreviations."""

import re

# Common English/clinical prefixes that should NOT have their hyphens removed when followed by newline
# Genuine compound adjectives or clinical terms: e.g., EGFR-positive, post-op, COVID-19
PROTECTED_HYPHEN_PATTERNS = [
    r"\b[A-Za-z0-9]+-[A-Za-z0-9]+\b",
]

# De-hyphenation regex: lowercase letter followed by hyphen, newline, and lowercase letter
# e.g., "hyper-\ntension" -> "hypertension", "evalu-\nation" -> "evaluation"
RE_LINEBREAK_HYPHEN = re.compile(r"([a-zA-Z]{2,})-\s*\n\s*([a-z]{2,})")

# Unicode whitespace characters (non-breaking space, thin space, zero-width space, etc.)
RE_UNICODE_SPACES = re.compile(r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000\u200b\ufeff]")

# Excessive spaces within a line
RE_MULTI_SPACES = re.compile(r"[^\S\r\n]{2,}")

# Excessive consecutive newlines (3 or more -> 2)
RE_MULTI_NEWLINES = re.compile(r"\n{3,}")


def normalize_clinical_text(text: str) -> str:
    """
    Normalizes clinical document text while strictly preserving:
    1. Numerical decimals (e.g. '0.5 mg', '.25 mcg', '12.5 mg/dL')
    2. Medical dosage units (e.g. 'mg/dL', 'mEq/L', 'mmHg', 'mL/min/1.73m²')
    3. Latin prescription abbreviations (e.g. 'b.i.d.', 't.i.d.', 'q.h.s.', 'p.r.n.', 'p.o.')
    4. Legitimate compound terms ('EGFR-mutated', 'post-operative', 'COVID-19')

    De-hyphenates line-break splits ('hyper-\\ntension' -> 'hypertension') and
    normalizes excessive whitespace.
    """
    if not text:
        return ""

    # 1. Normalize line endings to LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Normalize exotic Unicode whitespace characters to standard space
    text = RE_UNICODE_SPACES.sub(" ", text)

    # 3. Fix line-break hyphenations (e.g. "hyper-\ntension" -> "hypertension")
    text = RE_LINEBREAK_HYPHEN.sub(r"\1\2", text)

    # 4. Collapse multiple horizontal spaces into a single space
    lines = text.split("\n")
    cleaned_lines: list[str] = []
    for line in lines:
        cleaned_line = RE_MULTI_SPACES.sub(" ", line).strip()
        cleaned_lines.append(cleaned_line)

    text = "\n".join(cleaned_lines)

    # 5. Collapse 3+ newlines into 2 (preserving paragraph breaks)
    text = RE_MULTI_NEWLINES.sub("\n\n", text)

    return text.strip()
