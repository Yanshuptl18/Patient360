"""Unit tests for clinical event extractor and temporal date resolution."""

from datetime import date

from backend.timeline.extractor import ClinicalEventExtractor, parse_text_date


def test_parse_text_date_formats() -> None:
    fallback = date(2024, 1, 1)

    # ISO Format
    d1, p1 = parse_text_date("Patient evaluated on 2021-04-12 for symptoms.", fallback)
    assert d1 == date(2021, 4, 12)
    assert p1 == "day"

    # US Format
    d2, p2 = parse_text_date("Visit note dated 04/14/2021 in clinic.", fallback)
    assert d2 == date(2021, 4, 14)
    assert p2 == "day"

    # Named month day year
    d3, p3 = parse_text_date("Discharge on April 14, 2021 after stabilization.", fallback)
    assert d3 == date(2021, 4, 14)
    assert p3 == "day"

    # Named day month year
    d4, p4 = parse_text_date("Consultation performed 12 Apr 2021 in outpatient suite.", fallback)
    assert d4 == date(2021, 4, 12)
    assert p4 == "day"

    # Month and year only
    d5, p5 = parse_text_date("Symptoms commenced in April 2021.", fallback)
    assert d5 == date(2021, 4, 1)
    assert p5 == "month"

    # Year only
    d6, p6 = parse_text_date("Underwent surgical intervention in 2018.", fallback)
    assert d6 == date(2018, 1, 1)
    assert p6 == "year"

    # Fallback to document date when no date in text
    d7, p7 = parse_text_date("Patient has ongoing fatigue without specific timeline.", fallback)
    assert d7 == fallback
    assert p7 == "approximate"


def test_extract_allergies() -> None:
    extractor = ClinicalEventExtractor()
    doc_date = date(2021, 4, 14)

    # Test NKDA
    text_nkda = "Allergies: No known drug allergies (NKDA)."
    events = extractor.extract_from_chunk(text_nkda, document_id="doc-1", chunk_id="chk-1", doc_date=doc_date)
    assert len(events) == 1
    assert events[0].event_type == "allergy"
    assert "NKDA" in events[0].description
    assert events[0].clinical_status == "active"

    # Test Specific Allergy with reaction
    text_specific = "Allergies: Lisinopril, reaction: severe facial angioedema observed on 2021-04-12."
    events2 = extractor.extract_from_chunk(text_specific, document_id="doc-2", chunk_id="chk-2", doc_date=doc_date)
    assert len(events2) >= 1
    allergy_ev = [e for e in events2 if e.event_type == "allergy"][0]
    assert "Lisinopril" in allergy_ev.description
    assert allergy_ev.event_date == date(2021, 4, 12)
    assert allergy_ev.document_date == doc_date
    assert allergy_ev.event_date != allergy_ev.document_date  # Explicit separation
    assert "angioedema" in (allergy_ev.value_or_dosage or "").lower()


def test_extract_medications() -> None:
    extractor = ClinicalEventExtractor()
    doc_date = date(2023, 1, 15)

    text = "Active Medications: Lisinopril 10mg daily, Metformin 500mg BID, and Atorvastatin 40mg."
    events = extractor.extract_from_chunk(text, document_id="doc-1", chunk_id="chk-1", doc_date=doc_date)

    meds = [e for e in events if e.event_type == "medication"]
    assert len(meds) >= 3
    med_names = [m.description for m in meds]
    assert any("Lisinopril" in name for name in med_names)
    assert any("Metformin" in name for name in med_names)
    assert any("Atorvastatin" in name for name in med_names)


def test_extract_diagnoses_and_procedures() -> None:
    extractor = ClinicalEventExtractor()
    doc_date = date(2024, 2, 1)

    text = (
        "Assessment: Type 2 Diabetes Mellitus and Essential Hypertension.\n"
        "Past Surgical History: Underwent Appendectomy in 2018."
    )
    events = extractor.extract_from_chunk(text, document_id="doc-1", chunk_id="chk-1", doc_date=doc_date)

    diagnoses = [e for e in events if e.event_type == "diagnosis"]
    procedures = [e for e in events if e.event_type == "procedure"]

    assert len(diagnoses) >= 1
    assert len(procedures) >= 1
    proc = procedures[0]
    assert "Appendectomy" in proc.description
    assert proc.event_date.year == 2018
    assert proc.event_date_precision == "year"


def test_extract_labs_and_encounters() -> None:
    extractor = ClinicalEventExtractor()
    doc_date = date(2024, 3, 10)

    text = (
        "Encounter: Emergency Department Visit on 2024-03-09.\n"
        "Diagnostics: NT-proBNP at 6200 pg/mL, eGFR: 42 mL/min/1.73m2, and HbA1c: 6.2%."
    )
    events = extractor.extract_from_chunk(text, document_id="doc-1", chunk_id="chk-1", doc_date=doc_date)

    labs = [e for e in events if e.event_type == "lab_result"]
    encounters = [e for e in events if e.event_type == "encounter"]

    assert len(encounters) >= 1
    assert len(labs) >= 2
    lab_names = [lb.description for lb in labs]
    assert any("NT-PROBNP" in name.upper() for name in lab_names)
    assert any("EGFR" in name.upper() for name in lab_names)
