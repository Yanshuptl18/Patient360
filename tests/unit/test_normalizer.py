"""Unit tests for clinical text normalizer."""

from backend.ingestion.normalizer import normalize_clinical_text


def test_preserves_decimals_and_dosages() -> None:
    """Verifies that decimal dosages and laboratory values are never stripped or altered."""
    raw = "Prescribed 0.5 mg oral tablet, .25 mcg levothyroxine, and 12.5 mg/dL creatinine."
    normalized = normalize_clinical_text(raw)

    assert "0.5 mg" in normalized
    assert ".25 mcg" in normalized
    assert "12.5 mg/dL" in normalized


def test_preserves_medical_units() -> None:
    """Verifies that complex clinical units are preserved intact."""
    raw = "eGFR 45 mL/min/1.73m², BP 130/80 mmHg, Sodium 138 mEq/L, Troponin 0.04 ng/mL."
    normalized = normalize_clinical_text(raw)

    assert "45 mL/min/1.73m²" in normalized
    assert "130/80 mmHg" in normalized
    assert "138 mEq/L" in normalized
    assert "0.04 ng/mL" in normalized


def test_preserves_latin_prescription_abbreviations() -> None:
    """Verifies Latin abbreviations with periods are not corrupted."""
    raw = "Take 1 tab p.o. b.i.d. and 2 tabs p.r.n. pain at bedtime q.h.s."
    normalized = normalize_clinical_text(raw)

    assert "p.o." in normalized
    assert "b.i.d." in normalized
    assert "p.r.n." in normalized
    assert "q.h.s." in normalized


def test_dehyphenates_linebreaks() -> None:
    """Verifies words split across line breaks with hyphens are joined cleanly."""
    raw = "Patient has severe hyper-\ntension and was admitted for evalu-\nation."
    normalized = normalize_clinical_text(raw)

    assert "hypertension" in normalized
    assert "evaluation" in normalized
    assert "hyper-" not in normalized


def test_preserves_legitimate_clinical_hyphens() -> None:
    """Verifies compound adjectives and biological designations retain hyphens."""
    raw = "Patient is EGFR-mutated, post-operative, and receiving beta-blocker therapy after COVID-19."
    normalized = normalize_clinical_text(raw)

    assert "EGFR-mutated" in normalized
    assert "post-operative" in normalized
    assert "beta-blocker" in normalized
    assert "COVID-19" in normalized


def test_normalizes_unicode_whitespace_and_newlines() -> None:
    """Verifies non-breaking spaces and excessive newlines are normalized."""
    raw = "Line 1\u00a0with\u200bspaces.\n\n\n\nLine 2 after multi-newlines."
    normalized = normalize_clinical_text(raw)

    assert "Line 1 with spaces." in normalized
    assert "\n\n\n" not in normalized
    assert "Line 1 with spaces.\n\nLine 2 after multi-newlines." == normalized
