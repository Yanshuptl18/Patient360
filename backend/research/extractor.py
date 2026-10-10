"""Heuristic and layout-aware parameter extractor for biomedical publications."""

import datetime
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

DOI_PATTERN = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b")
PMID_PATTERN = re.compile(r"\b(?:PMID|PubMed\s*(?:ID)?):\s*(\d{6,10})\b", re.IGNORECASE)

SAMPLE_SIZE_PATTERNS = [
    re.compile(
        r"(?:sample\s+size|total\s+of|enrolled|randomized|included|cohort\s+of|trial\s+of|study\s+of|involving)\s*(?:of\s*)?([1-9]\d{0,2}(?:,\d{3})*|[1-9]\d{1,6})\s*(?:eligible\s+)?(?:patients|participants|subjects|individuals|cases)?",
        re.IGNORECASE,
    ),
    re.compile(r"\bn\s*=\s*([1-9]\d{0,2}(?:,\d{3})*|[1-9]\d{1,6})\b", re.IGNORECASE),
    re.compile(
        r"([1-9]\d{0,2}(?:,\d{3})*|[1-9]\d{1,6})\s+(?:patients|participants|subjects|individuals|cases)\s+(?:were\s+)?(?:enrolled|randomized|included|evaluated|analyzed|aged|with|diagnosed)",
        re.IGNORECASE,
    ),
]


STUDY_DESIGN_PATTERNS = [
    ("Systematic Review & Meta-Analysis", re.compile(r"\b(?:systematic\s+review|meta-analysis)\b", re.IGNORECASE)),
    ("Clinical Practice Guideline", re.compile(r"\b(?:clinical\s+practice\s+guideline|consensus\s+statement|expert\s+consensus)\b", re.IGNORECASE)),
    ("Randomized Controlled Trial", re.compile(r"\b(?:randomized(?:\s+controlled)?\s+trial|double-blind|placebo-controlled|phase\s+[1-4]\s+(?:trial|study))\b", re.IGNORECASE)),
    ("Prospective Cohort Study", re.compile(r"\b(?:prospective\s+cohort|prospective\s+observational|prospective\s+multicenter)\b", re.IGNORECASE)),
    ("Retrospective Cohort Study", re.compile(r"\b(?:retrospective\s+cohort|retrospective\s+analysis|retrospective\s+chart\s+review)\b", re.IGNORECASE)),
    ("Case-Control Study", re.compile(r"\bcase-control\b", re.IGNORECASE)),
    ("Cross-Sectional Study", re.compile(r"\bcross-sectional\b", re.IGNORECASE)),
    ("Case Series / Report", re.compile(r"\b(?:case\s+series|case\s+report)\b", re.IGNORECASE)),
]

SECTION_PATTERNS = {
    "population": [
        re.compile(r"(?:patients\s+and\s+methods|eligibility\s+criteria|inclusion\s+criteria|study\s+population|participants)[\s:]+([^\n\.]+(?:\.[^\n\.]+){0,3})", re.IGNORECASE),
        re.compile(r"(?:enrolled|included)\s+(patients\s+(?:with|aged|diagnosed)[^\n\.]+(?:\.[^\n\.]+){0,2})", re.IGNORECASE),
    ],
    "intervention": [
        re.compile(r"(?:interventions?|treatment|therapy)[\s:]+([^\n\.]+(?:\.[^\n\.]+){0,3})", re.IGNORECASE),
        re.compile(r"(?:randomly\s+assigned\s+to|treated\s+with|received)\s+([^\n\.]+(?:\.[^\n\.]+){0,2})", re.IGNORECASE),
    ],
    "primary_outcome": [
        re.compile(r"(?:primary\s+(?:endpoint|outcome|efficacy\s+variable)|results)[\s:]+([^\n\.]+(?:\.[^\n\.]+){0,3})", re.IGNORECASE),
        re.compile(r"(?:overall\s+survival|progression-free\s+survival|hazard\s+ratio|primary\s+objective)[^\n\.]*?([^\n\.]+(?:\.[^\n\.]+){0,2})", re.IGNORECASE),
    ],
    "limitations": [
        re.compile(r"(?:limitations?|study\s+limitations?)[\s:]+([^\n\.]+(?:\.[^\n\.]+){0,3})", re.IGNORECASE),
        re.compile(r"(?:potential\s+confounders?|lack\s+of\s+blinding|single-center\s+nature)[^\n\.]*?([^\n\.]+(?:\.[^\n\.]+){0,2})", re.IGNORECASE),
    ],
}



class StudyParameterExtractor:
    """Extracts study parameters and methodology metadata from biomedical text chunks."""

    def extract_doi(self, text: str) -> str | None:
        """Extracts Digital Object Identifier (DOI)."""
        match = DOI_PATTERN.search(text)
        if match:
            doi = match.group(1).rstrip(".,;)")
            return doi
        return None

    def extract_pmid(self, text: str) -> str | None:
        """Extracts PubMed Identifier (PMID)."""
        match = PMID_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        return None

    def extract_study_design(self, text: str) -> str:
        """Identifies methodological study design based on clinical evidence taxonomy."""
        for design_name, pattern in STUDY_DESIGN_PATTERNS:
            if pattern.search(text):
                return design_name
        return "Observational Clinical Study"

    def extract_sample_size(self, text: str) -> int | None:
        """Extracts patient enrollment cohort size (N)."""
        for pattern in SAMPLE_SIZE_PATTERNS:
            match = pattern.search(text)
            if match:
                raw_num = match.group(1).replace(",", "")
                try:
                    val = int(raw_num)
                    if 1 <= val <= 2000000:
                        return val
                except ValueError:
                    continue
        return None

    def extract_section_text(self, text: str, section_key: str) -> str | None:
        """Extracts concise contextual narrative for population, intervention, outcome, or limitations."""
        patterns = SECTION_PATTERNS.get(section_key, [])
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                snippet = match.group(1).strip()
                # Clean multiple spaces and linebreaks
                cleaned = re.sub(r"\s+", " ", snippet)
                if len(cleaned) > 15:
                    return cleaned[:600]
        return None

    def extract_authors(self, text: str) -> str | None:
        """Extracts author list or primary investigator attribution."""
        m = re.search(r"(?:authors?|by|investigators?)[\s:]+([A-Z][a-zA-Z\s,\.\-]+(?:et\s+al\.)?)", text, re.IGNORECASE)
        if m:
            authors = re.sub(r"\s+", " ", m.group(1).strip())
            return authors[:300]
        return None

    def extract_publication_date(self, text: str, fallback_date: datetime.date | None = None) -> datetime.date | None:
        """Extracts year/date of publication or falls back to document date."""
        # Check explicit year pattern in first 1000 characters
        year_match = re.search(r"\b(?:published|copyright|accepted|©)?\s*(19\d\d|20\d\d)\b", text[:1500], re.IGNORECASE)
        if year_match:
            try:
                year = int(year_match.group(1))
                return datetime.date(year, 1, 1)
            except ValueError:
                pass
        return fallback_date

    def extract_parameters(
        self,
        full_text: str,
        document_title: str,
        doc_date: datetime.date | None = None,
    ) -> dict[str, Any]:
        """
        Executes unified parameter extraction across document text.
        """
        doi = self.extract_doi(full_text)
        pmid = self.extract_pmid(full_text)
        study_design = self.extract_study_design(full_text)
        sample_size = self.extract_sample_size(full_text)
        authors = self.extract_authors(full_text)
        pub_date = self.extract_publication_date(full_text, fallback_date=doc_date)

        population = self.extract_section_text(full_text, "population") or "Broad clinical cohort meeting study inclusion criteria."
        intervention = self.extract_section_text(full_text, "intervention") or "Standard clinical regimen / protocol specified in study documentation."
        primary_outcome = self.extract_section_text(full_text, "primary_outcome") or "Efficacy, safety, and clinical endpoint markers."
        limitations = self.extract_section_text(full_text, "limitations") or "Standard observational or sample size constraints reported in discussion."

        # Title: use document_title, or check text
        title = document_title.strip()
        if title.lower().endswith(".pdf"):
            title = title[:-4].replace("_", " ").title()

        return {
            "title": title,
            "doi": doi,
            "pmid": pmid,
            "authors": authors,
            "publication_date": pub_date,
            "study_design": study_design,
            "sample_size": sample_size,
            "population_description": population,
            "intervention": intervention,
            "primary_outcome": primary_outcome,
            "limitations": limitations,
        }
