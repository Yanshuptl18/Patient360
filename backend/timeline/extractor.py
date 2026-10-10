"""Clinical event extraction engine for longitudinal patient timelines.

Extracts dated clinical events (Diagnoses, Medications, Encounters, Labs, Procedures, Allergies)
from document chunks with explicit temporal precision and document date distinction.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Regular expressions for clinical date formats
DATE_PATTERNS = [
    # ISO YYYY-MM-DD
    (re.compile(r"\b(19\d\d|20\d\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b"), "day", "%Y-%m-%d"),
    # US MM/DD/YYYY or M/D/YYYY
    (re.compile(r"\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(19\d\d|20\d\d)\b"), "day", "%m/%d/%Y"),
    # Month DD, YYYY (e.g. April 14, 2021; Apr 14, 2021)
    (
        re.compile(
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.,]?\s+(0?[1-9]|[12]\d|3[01]),?\s+(19\d\d|20\d\d)\b",
            re.IGNORECASE,
        ),
        "day",
        "custom_named",
    ),
    # DD Month YYYY (e.g. 14 April 2021; 12 Apr 2021)
    (
        re.compile(
            r"\b(0?[1-9]|[12]\d|3[01])\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.,]?\s+(19\d\d|20\d\d)\b",
            re.IGNORECASE,
        ),
        "day",
        "custom_named_day_first",
    ),
    # Month YYYY (e.g. April 2021, Apr 2021)
    (
        re.compile(
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.,]?\s+(19\d\d|20\d\d)\b",
            re.IGNORECASE,
        ),
        "month",
        "custom_named_month_only",
    ),
    # Year only (e.g. "in 2018", "year 2021", "since 2019")
    (re.compile(r"\b(?:in|year|since|circa|during)?\s*(19\d\d|20\d\d)\b", re.IGNORECASE), "year", "year_only"),
]

MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


@dataclass
class ExtractedEventData:
    """Internal representation of a clinically extracted event."""

    event_type: str
    event_date: date
    event_date_precision: str
    document_date: date | None
    description: str
    value_or_dosage: str | None
    clinical_status: str
    confidence_score: float
    document_id: str
    chunk_id: str | None
    exact_quote: str | None = None


def parse_text_date(text_snippet: str, fallback_doc_date: date | None) -> tuple[date, str]:
    """
    Finds the first explicit date mentioned in the snippet.
    Returns (parsed_date, precision). If no date found, returns (fallback_doc_date, 'approximate').
    """
    for regex, precision, fmt in DATE_PATTERNS:
        match = regex.search(text_snippet)
        if not match:
            continue

        raw = match.group(0).strip()
        try:
            if fmt == "%Y-%m-%d":
                return datetime.strptime(raw, "%Y-%m-%d").date(), precision
            if fmt == "%m/%d/%Y":
                # Normalize two-digit or single-digit numbers
                parts = raw.split("/")
                m, d, y = int(parts[0]), int(parts[1]), int(parts[2])
                return date(y, m, d), precision
            if fmt == "custom_named":
                m_str, d_str, y_str = match.group(1), match.group(2), match.group(3)
                month_num = MONTH_MAP[m_str.lower()[:3]]
                return date(int(y_str), month_num, int(d_str)), precision
            if fmt == "custom_named_day_first":
                d_str, m_str, y_str = match.group(1), match.group(2), match.group(3)
                month_num = MONTH_MAP[m_str.lower()[:3]]
                return date(int(y_str), month_num, int(d_str)), precision
            if fmt == "custom_named_month_only":
                m_str, y_str = match.group(1), match.group(2)
                month_num = MONTH_MAP[m_str.lower()[:3]]
                return date(int(y_str), month_num, 1), precision
            if fmt == "year_only":
                # Extract digits
                year_match = re.search(r"(19\d\d|20\d\d)", raw)
                if year_match:
                    y = int(year_match.group(1))
                    return date(y, 1, 1), precision
        except Exception:
            continue

    # Fallback to document date or today
    if fallback_doc_date:
        return fallback_doc_date, "approximate"
    return date.today(), "approximate"


class ClinicalEventExtractor:
    """
    Rule-based and heuristic clinical event extractor.
    Identifies clinical statements in raw document chunk text.
    """

    def extract_from_chunk(
        self,
        chunk_text: str,
        document_id: str,
        chunk_id: str | None,
        doc_date: date | None = None,
        doc_type: str = "patient_record",
    ) -> list[ExtractedEventData]:
        """Extracts all clinical events from a single chunk's text."""
        events: list[ExtractedEventData] = []
        lines = [line.strip() for line in chunk_text.split("\n") if line.strip()]

        for i, line in enumerate(lines):
            # Context window for date lookup: current line or nearby lines
            context_window = " ".join(lines[max(0, i - 1) : min(len(lines), i + 2)])

            # 1. Allergies
            allergy_events = self._extract_allergies(line, context_window, document_id, chunk_id, doc_date)
            events.extend(allergy_events)

            # 2. Medications
            med_events = self._extract_medications(line, context_window, document_id, chunk_id, doc_date)
            events.extend(med_events)

            # 3. Diagnoses / Assessment
            diag_events = self._extract_diagnoses(line, context_window, document_id, chunk_id, doc_date)
            events.extend(diag_events)

            # 4. Procedures / Surgeries
            proc_events = self._extract_procedures(line, context_window, document_id, chunk_id, doc_date)
            events.extend(proc_events)

            # 5. Lab Results
            lab_events = self._extract_labs(line, context_window, document_id, chunk_id, doc_date)
            events.extend(lab_events)

            # 6. Encounters
            enc_events = self._extract_encounters(line, context_window, document_id, chunk_id, doc_date, doc_type)
            events.extend(enc_events)

        return events

    def _extract_allergies(
        self,
        line: str,
        context: str,
        doc_id: str,
        chunk_id: str | None,
        doc_date: date | None,
    ) -> list[ExtractedEventData]:
        results: list[ExtractedEventData] = []
        lower = line.lower()

        # Check for NKDA / No known allergies
        if "no known drug allergies" in lower or "nkda" in lower or "no known allergies" in lower:
            ev_date, prec = parse_text_date(context, doc_date)
            results.append(
                ExtractedEventData(
                    event_type="allergy",
                    event_date=ev_date,
                    event_date_precision=prec,
                    document_date=doc_date,
                    description="No known drug allergies (NKDA)",
                    value_or_dosage=None,
                    clinical_status="active",
                    confidence_score=0.98,
                    document_id=doc_id,
                    chunk_id=chunk_id,
                    exact_quote=line,
                )
            )
            return results

        # Specific documented allergy
        allergy_patterns = [
            re.compile(r"allerg(?:y|ies):\s*([^,;\n]+)(?:[;,]|\s*reaction:\s*([^,;\n]+))?", re.IGNORECASE),
            re.compile(r"allergic\s+to\s+([^,;\n]+?)(?:\s*resulting in\s+([^,;\n]+))?[\.\n]", re.IGNORECASE),
            re.compile(r"(?:severe\s+)?(?:anaphylaxis|angioedema|rash|hives)\s+(?:to|following)\s+([^,;\n]+)", re.IGNORECASE),
        ]

        for pat in allergy_patterns:
            m = pat.search(line)
            if m:
                agent = m.group(1).strip()
                reaction = m.group(2).strip() if (m.lastindex and m.lastindex >= 2 and m.group(2)) else None
                if not reaction and "angioedema" in lower:
                    reaction = "Facial angioedema"
                elif not reaction and "anaphylaxis" in lower:
                    reaction = "Severe anaphylaxis"

                # Filter out false positives
                if agent.lower() in ["none", "denies", "no", "nkda", "nil"]:
                    continue

                ev_date, prec = parse_text_date(context, doc_date)
                results.append(
                    ExtractedEventData(
                        event_type="allergy",
                        event_date=ev_date,
                        event_date_precision=prec,
                        document_date=doc_date,
                        description=f"{agent.title()} Allergy",
                        value_or_dosage=reaction,
                        clinical_status="active",
                        confidence_score=0.95,
                        document_id=doc_id,
                        chunk_id=chunk_id,
                        exact_quote=line,
                    )
                )
                break

        return results

    def _extract_medications(
        self,
        line: str,
        context: str,
        doc_id: str,
        chunk_id: str | None,
        doc_date: date | None,
    ) -> list[ExtractedEventData]:
        results: list[ExtractedEventData] = []
        lower = line.lower()

        # Common clinical medications pattern: Drug Name + Dosage + Route/Frequency
        med_regex = re.compile(
            r"\b(lisinopril|metformin|osimertinib|atorvastatin|furosemide|amlodipine|levothyroxine|"
            r"apixaban|empagliflozin|losartan|metoprolol|aspirin|carvedilol|albuterol|omeprazole|"
            r"gabapentin|amoxicillin|ciprofloxacin|prednisone|hydrochlorothiazide)\b"
            r"(?:\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?)))?"
            r"(?:\s+(daily|bid|tid|qid|prn|po|iv|twice daily|once daily))?",
            re.IGNORECASE,
        )

        matches = med_regex.finditer(line)
        for m in matches:
            drug = m.group(1).title()
            dosage = m.group(2) if m.group(2) else ""
            freq = m.group(3) if m.group(3) else ""
            val = f"{dosage} {freq}".strip() or None

            # Detect status
            status = "active"
            if "discontinue" in lower or "stopped" in lower or "d/c" in lower:
                status = "resolved"
            elif "prior" in lower or "historical" in lower:
                status = "historical"

            ev_date, prec = parse_text_date(context, doc_date)
            results.append(
                ExtractedEventData(
                    event_type="medication",
                    event_date=ev_date,
                    event_date_precision=prec,
                    document_date=doc_date,
                    description=f"{drug} Therapy",
                    value_or_dosage=val,
                    clinical_status=status,
                    confidence_score=0.92,
                    document_id=doc_id,
                    chunk_id=chunk_id,
                    exact_quote=line,
                )
            )

        return results

    def _extract_diagnoses(
        self,
        line: str,
        context: str,
        doc_id: str,
        chunk_id: str | None,
        doc_date: date | None,
    ) -> list[ExtractedEventData]:
        results: list[ExtractedEventData] = []
        lower = line.lower()

        diagnosis_patterns = [
            (r"(?:assessment|impression|diagnosis|diagnoses|history of):\s*([^\.\n;]+)", 0.95),
            (r"\b(acute decompensated heart failure|congestive heart failure|heart failure)\b", 0.92),
            (r"\b(type 2 diabetes mellitus|type 2 diabetes|diabetes mellitus)\b", 0.92),
            (r"\b(chronic kidney disease(?: stage \d)?|ckd(?: stage \d)?)\b", 0.92),
            (r"\b(non-small cell lung cancer|nsclc|adenocarcinoma)\b", 0.92),
            (r"\b(essential hypertension|hypertension|htn)\b", 0.90),
            (r"\b(atrial fibrillation|afib)\b", 0.90),
            (r"\b(major depressive disorder|depression)\b", 0.90),
        ]

        for pat_str, conf in diagnosis_patterns:
            m = re.search(pat_str, line, re.IGNORECASE)
            if m:
                diag = m.group(1).strip() if m.lastindex and m.group(1) else m.group(0).strip()
                diag = diag.capitalize()

                # Status inference
                status = "active"
                if "resolved" in lower or "cured" in lower or "in remission" in lower:
                    status = "resolved"
                elif "history of" in lower or "past" in lower:
                    status = "historical"
                elif "disputed" in lower or "unconfirmed" in lower:
                    status = "disputed"

                ev_date, prec = parse_text_date(context, doc_date)
                results.append(
                    ExtractedEventData(
                        event_type="diagnosis",
                        event_date=ev_date,
                        event_date_precision=prec,
                        document_date=doc_date,
                        description=diag,
                        value_or_dosage=None,
                        clinical_status=status,
                        confidence_score=conf,
                        document_id=doc_id,
                        chunk_id=chunk_id,
                        exact_quote=line,
                    )
                )
                break

        return results

    def _extract_procedures(
        self,
        line: str,
        context: str,
        doc_id: str,
        chunk_id: str | None,
        doc_date: date | None,
    ) -> list[ExtractedEventData]:
        results: list[ExtractedEventData] = []

        proc_regex = re.compile(
            r"\b(status post|s/p|underwent|performed)?\s*"
            r"(appendectomy|cholecystectomy|coronary artery bypass graft|cabg|"
            r"knee arthroscopy|hip replacement|percutaneous coronary intervention|pci|"
            r"bronchoscopy|colonoscopy|lumbar puncture|biopsy|echocardiogram)\b",
            re.IGNORECASE,
        )

        m = proc_regex.search(line)
        if m:
            proc_name = m.group(2).title()
            ev_date, prec = parse_text_date(context, doc_date)

            results.append(
                ExtractedEventData(
                    event_type="procedure",
                    event_date=ev_date,
                    event_date_precision=prec,
                    document_date=doc_date,
                    description=proc_name,
                    value_or_dosage=None,
                    clinical_status="historical",
                    confidence_score=0.90,
                    document_id=doc_id,
                    chunk_id=chunk_id,
                    exact_quote=line,
                )
            )

        return results

    def _extract_labs(
        self,
        line: str,
        context: str,
        doc_id: str,
        chunk_id: str | None,
        doc_date: date | None,
    ) -> list[ExtractedEventData]:
        results: list[ExtractedEventData] = []

        lab_regex = re.compile(
            r"\b(nt-probnp|bnp|egfr|serum creatinine|creatinine|hba1c|potassium|hemoglobin|troponin i|troponin)\b"
            r"(?:\s*[:=]\s*|\s+(?:at|is|of|level|was)\s*)?(\d+(?:\.\d+)?|\<\s*\d+(?:\.\d+)?)"
            r"\s*(pg/ml|ml/min/1\.73m2|mg/dl|%|meq/l|g/dl|ng/ml)?",
            re.IGNORECASE,
        )

        matches = lab_regex.finditer(line)
        for m in matches:
            test_name = m.group(1).upper() if m.group(1).lower() in ["bnp", "nt-probnp", "egfr", "hba1c"] else m.group(1).title()
            val = m.group(2)
            unit = m.group(3) if m.group(3) else ""
            dosage_val = f"{val} {unit}".strip()

            ev_date, prec = parse_text_date(context, doc_date)
            results.append(
                ExtractedEventData(
                    event_type="lab_result",
                    event_date=ev_date,
                    event_date_precision=prec,
                    document_date=doc_date,
                    description=f"Lab: {test_name}",
                    value_or_dosage=dosage_val,
                    clinical_status="active",
                    confidence_score=0.94,
                    document_id=doc_id,
                    chunk_id=chunk_id,
                    exact_quote=line,
                )
            )

        return results

    def _extract_encounters(
        self,
        line: str,
        context: str,
        doc_id: str,
        chunk_id: str | None,
        doc_date: date | None,
        doc_type: str,
    ) -> list[ExtractedEventData]:
        results: list[ExtractedEventData] = []
        enc_regex = re.compile(
            r"\b(discharge summary|inpatient admission|emergency department visit|"
            r"cardiology consult|cardiology follow-up|oncology consultation|"
            r"annual wellness exam|outpatient clinic note|telehealth encounter)\b",
            re.IGNORECASE,
        )

        m = enc_regex.search(line)
        if m:
            enc_name = m.group(1).title()
            ev_date, prec = parse_text_date(context, doc_date)
            results.append(
                ExtractedEventData(
                    event_type="encounter",
                    event_date=ev_date,
                    event_date_precision=prec,
                    document_date=doc_date,
                    description=enc_name,
                    value_or_dosage=None,
                    clinical_status="historical",
                    confidence_score=0.88,
                    document_id=doc_id,
                    chunk_id=chunk_id,
                    exact_quote=line,
                )
            )

        return results
