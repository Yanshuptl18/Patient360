"""Unit tests for StudyParameterExtractor analyzing biomedical papers and guidelines."""

import datetime

from backend.research.extractor import StudyParameterExtractor


def test_study_parameter_extractor_doi_and_pmid() -> None:
    """Verifies DOI and PMID extraction from publication text."""
    extractor = StudyParameterExtractor()
    sample_text = (
        "New England Journal of Medicine. Published online May 15, 2023.\n"
        "DOI: 10.1056/NEJMoa2214903\n"
        "PMID: 37195978\n"
        "Osimertinib in Resected EGFR-Mutated Non-Small-Cell Lung Cancer."
    )

    doi = extractor.extract_doi(sample_text)
    pmid = extractor.extract_pmid(sample_text)

    assert doi == "10.1056/NEJMoa2214903"
    assert pmid == "37195978"


def test_study_design_classification() -> None:
    """Verifies study design taxonomy identification across evidence types."""
    extractor = StudyParameterExtractor()

    assert (
        extractor.extract_study_design(
            "In this double-blind, randomized controlled trial, patients were assigned to..."
        )
        == "Randomized Controlled Trial"
    )

    assert (
        extractor.extract_study_design(
            "A systematic review and meta-analysis of 24 observational studies was conducted..."
        )
        == "Systematic Review & Meta-Analysis"
    )

    assert (
        extractor.extract_study_design(
            "This prospective cohort study followed 1,200 participants over 5 years..."
        )
        == "Prospective Cohort Study"
    )

    assert (
        extractor.extract_study_design(
            "We performed a retrospective chart review of cases presenting with acute coronary syndrome..."
        )
        == "Retrospective Cohort Study"
    )

    assert (
        extractor.extract_study_design(
            "American College of Cardiology / AHA Clinical Practice Guideline on the Management of Heart Failure..."
        )
        == "Clinical Practice Guideline"
    )


def test_sample_size_extraction() -> None:
    """Verifies extraction of cohort sizes across distinct phrasing patterns."""
    extractor = StudyParameterExtractor()

    # Pattern: n = X
    assert extractor.extract_sample_size("Baseline characteristics of the study cohort (n = 682).") == 682

    # Pattern: A total of X patients were enrolled
    assert (
        extractor.extract_sample_size(
            "A total of 1,166 patients were enrolled across 132 international clinical centers."
        )
        == 1166
    )

    # Pattern: enrolled X participants
    assert extractor.extract_sample_size("The trial enrolled 450 participants randomized 1:1.") == 450


def test_comprehensive_parameter_extraction() -> None:
    """Verifies full parameter extraction dictionary output."""
    extractor = StudyParameterExtractor()
    text = (
        "ADA Clinical Compendium 2024.\n"
        "Authors: Sarah Jenkins MD, Marcus Vance PhD, et al.\n"
        "DOI: 10.2337/dc23-s001\n"
        "PMID: 38118000\n"
        "Methods: A randomized controlled trial of 740 patients aged 18 to 75 diagnosed with type 2 diabetes.\n"
        "Interventions: Patients received empagliflozin 10mg daily versus matching placebo.\n"
        "Results: Primary outcome of HbA1c reduction demonstrated a statistically significant difference of -0.8%.\n"
        "Limitations: Study limitations include the 24-week follow-up period without long-term cardiovascular outcomes.\n"
    )

    params = extractor.extract_parameters(
        full_text=text,
        document_title="ADA_Diabetes_Trial_2024.pdf",
        doc_date=datetime.date(2024, 1, 1),
    )

    assert params["doi"] == "10.2337/dc23-s001"
    assert params["pmid"] == "38118000"
    assert params["study_design"] == "Randomized Controlled Trial"
    assert params["sample_size"] == 740
    assert "Jenkins" in (params["authors"] or "")
    assert "empagliflozin" in (params["intervention"] or "").lower()
    assert "hba1c" in (params["primary_outcome"] or "").lower()
    assert "follow-up period" in (params["limitations"] or "").lower()
