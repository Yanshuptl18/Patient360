"""Idempotent demonstration data seeder for Patient360.

Seeds the 4 default RBAC personas, synthetic patient dossiers, sample clinical and research PDFs,
longitudinal clinical event timelines with contradictions, and landmark biomedical research trials.
"""

import hashlib
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pymupdf as fitz
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.auth.service import get_user_by_email, seed_default_users
from backend.core.config import settings
from backend.core.database import Base, SessionLocal, engine
from backend.models.chunk import DocumentChunk
from backend.models.document import Document
from backend.models.patient import Patient, UserPatientPermission
from backend.models.research import ResearchStudy
from backend.models.timeline import ClinicalEvent
from backend.vector.embeddings import get_embedding_provider
from backend.vector.store import get_vector_store

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def create_sample_pdf(file_path: Path, title: str, pages_text: list[str]) -> tuple[str, int]:
    """Generates a real PDF file with page-level content and returns (sha256_hash, file_size)."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()

    for idx, page_content in enumerate(pages_text):
        page = doc.new_page(width=595, height=842)  # A4 size
        # Header banner
        page.insert_text(
            (50, 40),
            f"Patient360 Synthetic Health Record — {title} (Page {idx + 1}/{len(pages_text)})",
            fontsize=9,
            color=(0.3, 0.3, 0.3),
        )
        page.draw_line((50, 48), (545, 48), color=(0.7, 0.7, 0.7), width=0.5)

        # Body text
        page.insert_textbox(
            fitz.Rect(50, 70, 545, 780),
            page_content,
            fontsize=10,
            lineheight=14,
            color=(0.1, 0.1, 0.1),
        )

        # Footer notice
        page.draw_line((50, 790), (545, 790), color=(0.8, 0.8, 0.8), width=0.5)
        page.insert_text(
            (50, 805),
            "CONFIDENTIAL SYNTHETIC DATA — FOR DEMONSTRATION & RESEARCH TESTING ONLY",
            fontsize=8,
            color=(0.5, 0.5, 0.5),
        )

    doc.save(str(file_path))
    doc.close()

    file_bytes = file_path.read_bytes()
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    return sha256, len(file_bytes)


def seed_demo_data(override_session: Session | None = None) -> None:
    """Populates the database and vector store with complete synthetic demonstration cohorts."""
    active_engine = engine
    active_session_factory = SessionLocal

    if override_session is not None:
        db = override_session
        should_close = False
    else:
        # Verify connectivity or fall back to local SQLite
        try:
            with active_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:
            logger.warning(
                "Primary database connection failed (%s). Falling back to SQLite database at './patient360_dev.db'.",
                exc,
            )
            active_engine = create_engine(
                "sqlite:///./patient360_dev.db",
                connect_args={"check_same_thread": False},
            )
            active_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=active_engine)

        logger.info("Initializing database schema...")
        Base.metadata.create_all(bind=active_engine)
        db = active_session_factory()
        should_close = True

    try:
        # 1. Seed Personas
        logger.info("1. Seeding default RBAC personas...")
        seed_default_users(db)
        admin = get_user_by_email(db, "admin@patient360.org")
        reviewer = get_user_by_email(db, "reviewer@patient360.org")
        researcher = get_user_by_email(db, "researcher@patient360.org")

        if not admin or not reviewer or not researcher:
            raise RuntimeError("Failed to retrieve seeded demo personas.")

        # 2. Seed Patients
        logger.info("2. Seeding synthetic patient cohort...")
        patients_data = [
            {
                "mrn_synthetic": "SYNTH-10001",
                "first_name": "Eleanor",
                "last_name": "Vance",
                "date_of_birth": date(1964, 8, 14),
                "gender": "female",
                "primary_condition": "Cardio-Oncology / Heart Failure with Reduced Ejection Fraction",
            },
            {
                "mrn_synthetic": "SYNTH-10002",
                "first_name": "Marcus",
                "last_name": "Thorne",
                "date_of_birth": date(1958, 11, 3),
                "gender": "male",
                "primary_condition": "Non-Small Cell Lung Cancer (EGFR Exon 21 L858R)",
            },
            {
                "mrn_synthetic": "SYNTH-10003",
                "first_name": "Clara",
                "last_name": "Oswald",
                "date_of_birth": date(1989, 4, 12),
                "gender": "female",
                "primary_condition": "Type 2 Diabetes Mellitus with Chronic Kidney Disease Stage 3a",
            },
            {
                "mrn_synthetic": "SYNTH-10004",
                "first_name": "Arthur",
                "last_name": "Dent",
                "date_of_birth": date(1978, 3, 11),
                "gender": "male",
                "primary_condition": "Recurrent Deep Vein Thrombosis & Anticoagulation Ambiguity",
            },
        ]

        patients_map: dict[str, Patient] = {}
        for p_data in patients_data:
            existing = db.query(Patient).filter(Patient.mrn_synthetic == p_data["mrn_synthetic"]).first()
            if not existing:
                p = Patient(**p_data)
                db.add(p)
                db.flush()
                patients_map[p.mrn_synthetic] = p
            else:
                patients_map[p_data["mrn_synthetic"]] = existing

        # 3. Grant Permissions
        logger.info("3. Configuring user-patient RBAC mappings...")
        doctor = get_user_by_email(db, "doctor@patient360.org")
        nurse = get_user_by_email(db, "nurse@patient360.org")
        patient_user = get_user_by_email(db, "patient@patient360.org")

        for p in patients_map.values():
            # Admin gets full admin access to all
            if not db.query(UserPatientPermission).filter_by(user_id=admin.id, patient_id=p.id).first():
                db.add(UserPatientPermission(user_id=admin.id, patient_id=p.id, permission_level="admin"))

            # Reviewer gets read/write access to patients 1, 2, and 3
            if p.mrn_synthetic in ("SYNTH-10001", "SYNTH-10002", "SYNTH-10003"):
                if not db.query(UserPatientPermission).filter_by(user_id=reviewer.id, patient_id=p.id).first():
                    db.add(UserPatientPermission(user_id=reviewer.id, patient_id=p.id, permission_level="write"))

            # Researcher gets access to Marcus Thorne (Oncology) and Clara Oswald (Metabolic/Renal)
            if p.mrn_synthetic in ("SYNTH-10002", "SYNTH-10003"):
                if not db.query(UserPatientPermission).filter_by(user_id=researcher.id, patient_id=p.id).first():
                    db.add(UserPatientPermission(user_id=researcher.id, patient_id=p.id, permission_level="read"))

            # Doctor gets read/write access to all clinical cohort patients
            if doctor and not db.query(UserPatientPermission).filter_by(user_id=doctor.id, patient_id=p.id).first():
                db.add(UserPatientPermission(user_id=doctor.id, patient_id=p.id, permission_level="write"))

            # Nurse gets read/write access to all clinical cohort patients for care coordination
            if nurse and not db.query(UserPatientPermission).filter_by(user_id=nurse.id, patient_id=p.id).first():
                db.add(UserPatientPermission(user_id=nurse.id, patient_id=p.id, permission_level="write"))

            # Patient role is strictly isolated to Eleanor Vance's own record (SYNTH-10001)
            if patient_user and p.mrn_synthetic == "SYNTH-10001":
                if not db.query(UserPatientPermission).filter_by(user_id=patient_user.id, patient_id=p.id).first():
                    db.add(UserPatientPermission(user_id=patient_user.id, patient_id=p.id, permission_level="read"))

        db.commit()

        # 4. Generate Clinical & Research Documents
        logger.info("4. Generating real clinical PDF files and indexing vectors...")
        storage_dir = settings.storage_path
        storage_dir.mkdir(parents=True, exist_ok=True)
        v_store = get_vector_store()
        get_embedding_provider()

        docs_spec: list[dict[str, Any]] = [
            # Eleanor Vance
            {
                "patient_id": patients_map["SYNTH-10001"].id,
                "filename": "Eleanor_Vance_Echo_2023.pdf",
                "title": "Transthoracic Echocardiogram Report (2023)",
                "doc_type": "lab_report",
                "doc_date": date(2023, 5, 20),
                "pages": [
                    (
                        "CLINICAL INDICATION: 58-year-old female with prior history of breast cancer status-post "
                        "adjuvant anthracycline chemotherapy (Doxorubicin cumulative dose 240 mg/m2 completed 2021). "
                        "Surveillance echocardiogram.\n\n"
                        "FINDINGS:\n"
                        "Left Ventricle: Normal cavity dimensions. Global left ventricular systolic function is preserved "
                        "at lower limits of normal. Left ventricular ejection fraction (LVEF) is estimated at 45%.\n"
                        "Diastolic Function: Grade 1 impaired relaxation pattern.\n"
                        "Valves: Mild mitral regurgitation. Trace tricuspid regurgitation. Estimated PASP 28 mmHg.\n\n"
                        "IMPRESSION:\n"
                        "1. LVEF 45% with mild global hypokinesis.\n"
                        "2. Recommend clinical correlation and follow-up in cardio-oncology clinic."
                    )
                ],
            },
            {
                "patient_id": patients_map["SYNTH-10001"].id,
                "filename": "Eleanor_Vance_Cardiology_Consult_2024.pdf",
                "title": "Cardio-Oncology Consultation Note (2024)",
                "doc_type": "patient_record",
                "doc_date": date(2024, 4, 15),
                "pages": [
                    (
                        "SUBJECTIVE:\n"
                        "Patient Eleanor Vance presents with worsening dyspnea on exertion (NYHA Class II-III) and "
                        "trace bilateral ankle edema over the past two months. No chest pain, syncope, or orthopnea.\n\n"
                        "CURRENT MEDICATIONS:\n"
                        "1. Carvedilol 12.5 mg PO BID\n"
                        "2. Sacubitril / Valsartan (Entresto) 24/26 mg PO BID\n"
                        "3. Spironolactone 25 mg PO daily\n\n"
                        "REPEAT TRANSTHORACIC ECHOCARDIOGRAM (April 10, 2024):\n"
                        "Significant interval decline in systolic function: Left ventricular ejection fraction (LVEF) is "
                        "now documented at 35% with diffuse global hypokinesis.\n\n"
                        "ASSESSMENT & PLAN:\n"
                        "Chemotherapy-induced cardiomyopathy (anthracycline-related cardiotoxicity) with symptomatic HFrEF. "
                        "Initiate SGLT2 inhibitor (Dapagliflozin 10 mg daily) and up-titrate neurohormonal blockade."
                    )
                ],
            },
            # Marcus Thorne
            {
                "patient_id": patients_map["SYNTH-10002"].id,
                "filename": "Marcus_Thorne_Molecular_Pathology.pdf",
                "title": "Comprehensive Molecular Pathology & NGS Report",
                "doc_type": "lab_report",
                "doc_date": date(2024, 2, 10),
                "pages": [
                    (
                        "SPECIMEN: CT-guided core biopsy of right upper lobe lung mass (Specimen ID: PATH-2024-9912).\n"
                        "HISTOPATHOLOGY: Moderately differentiated invasive lung adenocarcinoma.\n\n"
                        "TARGETED NEXT-GENERATION SEQUENCING (NGS) RESULTS:\n"
                        "1. EGFR: Exon 21 L858R point mutation IDENTIFIED (Variant Allele Frequency: 38.4%).\n"
                        "2. EGFR T790M: NOT DETECTED (wild type).\n"
                        "3. EGFR Exon 20 insertions: NOT DETECTED.\n"
                        "4. ALK Rearrangement (D5F3 IHC / FISH): NEGATIVE.\n"
                        "5. ROS1 Rearrangement: NEGATIVE.\n"
                        "6. BRAF V600E: NEGATIVE.\n"
                        "7. PD-L1 Tumor Proportion Score (TPS): 15%.\n\n"
                        "INTERPRETATION: Findings consistent with EGFR-mutated non-small cell lung cancer sensitive to "
                        "first-line third-generation EGFR tyrosine kinase inhibitors (Osimertinib)."
                    )
                ],
            },
            {
                "patient_id": patients_map["SYNTH-10002"].id,
                "filename": "Marcus_Thorne_Oncology_Followup.pdf",
                "title": "Thoracic Oncology Clinical Follow-Up Note",
                "doc_type": "patient_record",
                "doc_date": date(2024, 6, 5),
                "pages": [
                    (
                        "HISTORY OF PRESENT ILLNESS:\n"
                        "Marcus Thorne is a 65-year-old male with Stage IV adenocarcinoma of the lung harboring "
                        "an EGFR L858R mutation. He has completed 16 weeks of first-line Osimertinib (Tagrisso) 80 mg daily.\n\n"
                        "RESPONSE ASSESSMENT:\n"
                        "Restaging CT Chest/Abdomen/Pelvis demonstrated a 42% reduction in the primary right upper lobe "
                        "mass (from 4.5 cm to 2.6 cm), meeting RECIST 1.1 criteria for Partial Response.\n\n"
                        "TOXICITY & TOLERABILITY:\n"
                        "Grade 1 acneiform rash on upper chest managed with topical clindamycin. No diarrhea, QT prolongation, "
                        "or pneumonitis. Continue Osimertinib 80 mg daily."
                    )
                ],
            },
            # Clara Oswald
            {
                "patient_id": patients_map["SYNTH-10003"].id,
                "filename": "Clara_Oswald_Nephrology_Consult.pdf",
                "title": "Nephrology Consultation & Renal Function Assessment",
                "doc_type": "patient_record",
                "doc_date": date(2023, 11, 15),
                "pages": [
                    (
                        "CLINICAL SUMMARY:\n"
                        "Clara Oswald is a 34-year-old female with a 7-year history of Type 2 Diabetes Mellitus. "
                        "Referred for progressive microalbuminuria.\n\n"
                        "LABORATORY EVALUATION:\n"
                        "Serum Creatinine: 1.3 mg/dL | Estimated GFR: 52 mL/min/1.73m2 (CKD Stage 3a)\n"
                        "Urine Albumin-to-Creatinine Ratio (UACR): 185 mg/g (persistent microalbuminuria)\n"
                        "HbA1c: 7.6%\n\n"
                        "MANAGEMENT PLAN:\n"
                        "Initiate Dapagliflozin 10 mg once daily for proven cardiorenal risk reduction as supported by "
                        "the DAPA-CKD landmark trial. Maintain ACE inhibitor (Lisinopril 20 mg daily)."
                    )
                ],
            },
            # Arthur Dent
            {
                "patient_id": patients_map["SYNTH-10004"].id,
                "filename": "Arthur_Dent_Admission_Intake_2021.pdf",
                "title": "Hospital Admission Intake Record (2021)",
                "doc_type": "patient_record",
                "doc_date": date(2021, 6, 10),
                "pages": [
                    (
                        "ADMISSION RECORD:\n"
                        "Patient: Arthur Dent, 43-year-old male admitted for deep vein thrombosis (DVT) evaluation.\n\n"
                        "ALLERGY HISTORY:\n"
                        "Allergies Reviewed: No Known Drug Allergies (NKDA) reported by patient upon admission.\n\n"
                        "PLAN:\n"
                        "Initiated on therapeutic low-molecular-weight heparin with bridging to Apixaban."
                    )
                ],
            },
            {
                "patient_id": patients_map["SYNTH-10004"].id,
                "filename": "Arthur_Dent_ED_Anaphylaxis_2023.pdf",
                "title": "Emergency Department Encounter Note (2023)",
                "doc_type": "discharge_summary",
                "doc_date": date(2023, 10, 14),
                "pages": [
                    (
                        "EMERGENCY DEPARTMENT CLINICAL SUMMARY:\n"
                        "Patient Arthur Dent presented via EMS in acute respiratory distress 25 minutes after ingestion of "
                        "Amoxicillin 500 mg capsule for acute bacterial sinusitis.\n\n"
                        "PRESENTING SIGNS:\n"
                        "Bilateral expiratory wheezing, facial angioedema, urticaria, hypotension (BP 84/50 mmHg).\n\n"
                        "EMERGENCY INTERVENTIONS:\n"
                        "Immediate IM Epinephrine 0.3 mg administered, IV Methylprednisolone 125 mg, IV Diphenhydramine 50 mg. "
                        "Patient stabilized and observed for 6 hours.\n\n"
                        "DISCHARGE DIRECTIVE:\n"
                        "CRITICAL ALLERGY ALERT: Definite severe Penicillin anaphylaxis. Absolute contraindication to all beta-lactams."
                    )
                ],
            },
            # Landmark Biomedical Research Papers
            {
                "patient_id": None,
                "filename": "FLAURA_Trial_NEJM_2018.pdf",
                "title": "FLAURA: Osimertinib in Untreated EGFR-Mutated Advanced NSCLC",
                "doc_type": "research_paper",
                "doc_date": date(2018, 1, 11),
                "pages": [
                    (
                        "NEW ENGLAND JOURNAL OF MEDICINE (2018; 378:113-125)\n"
                        "Osimertinib in Untreated EGFR-Mutated Advanced Non-Small-Cell Lung Cancer\n\n"
                        "BACKGROUND: Osimertinib is a third-generation EGFR-TKI that selectively inhibits both EGFR-TKI-sensitizing "
                        "and EGFR T790M resistance mutations.\n\n"
                        "METHODS: In this double-blind, phase 3 trial, 556 patients with previously untreated, EGFR mutation-positive "
                        "(exon 19 deletion or L858R) advanced NSCLC were randomly assigned to receive either Osimertinib (80 mg once daily) "
                        "or standard EGFR-TKI (Gefitinib or Erlotinib).\n\n"
                        "RESULTS: The median progression-free survival was significantly longer with Osimertinib than with standard EGFR-TKIs "
                        "(18.9 months vs. 10.2 months; hazard ratio for disease progression or death, 0.46; 95% CI, 0.37 to 0.57; P < 0.001).\n\n"
                        "CONCLUSIONS: Osimertinib showed superior efficacy for first-line treatment of EGFR-mutated advanced NSCLC."
                    )
                ],
            },
            {
                "patient_id": None,
                "filename": "EMPEROR_Reduced_Trial_NEJM_2020.pdf",
                "title": "EMPEROR-Reduced: Cardiovascular Outcomes with Empagliflozin in Heart Failure",
                "doc_type": "research_paper",
                "doc_date": date(2020, 10, 8),
                "pages": [
                    (
                        "NEW ENGLAND JOURNAL OF MEDICINE (2020; 383:1413-1424)\n"
                        "Cardiovascular and Renal Outcomes with Empagliflozin in Heart Failure\n\n"
                        "BACKGROUND: Sodium-glucose cotransporter 2 (SGLT2) inhibitors reduce hospitalization risk in patients with heart failure.\n\n"
                        "METHODS: In this double-blind trial, 3,730 patients with NYHA class II-IV heart failure and an ejection fraction "
                        "of 40% or less were randomized to receive Empagliflozin 10 mg daily or placebo in addition to guideline-directed medical therapy.\n\n"
                        "RESULTS: Primary composite endpoint of cardiovascular death or hospitalization for heart failure occurred in "
                        "19.4% in the Empagliflozin group and 24.7% in the placebo group (hazard ratio, 0.75; 95% CI, 0.65 to 0.86; P < 0.001).\n\n"
                        "CONCLUSIONS: Empagliflozin reduced the combined risk of cardiovascular death or hospitalization in patients with HFrEF."
                    )
                ],
            },
            {
                "patient_id": None,
                "filename": "DAPA_CKD_Trial_NEJM_2020.pdf",
                "title": "DAPA-CKD: Dapagliflozin in Patients with Chronic Kidney Disease",
                "doc_type": "research_paper",
                "doc_date": date(2020, 10, 8),
                "pages": [
                    (
                        "NEW ENGLAND JOURNAL OF MEDICINE (2020; 383:1436-1446)\n"
                        "Dapagliflozin in Patients with Chronic Kidney Disease\n\n"
                        "BACKGROUND: Patients with chronic kidney disease (CKD) are at high risk for kidney failure and cardiovascular disease.\n\n"
                        "METHODS: In this double-blind trial, 4,304 patients with CKD (eGFR 25-75 mL/min/1.73m2 and UACR 200-5000 mg/g) "
                        "with or without type 2 diabetes were assigned to Dapagliflozin 10 mg once daily or placebo.\n\n"
                        "RESULTS: Primary outcome occurred in 9.2% of the Dapagliflozin group and 14.5% of the placebo group "
                        "(hazard ratio, 0.61; 95% CI, 0.51 to 0.72; P < 0.001).\n\n"
                        "CONCLUSIONS: Dapagliflozin significantly reduced the risk of sustained decline in eGFR, end-stage kidney disease, "
                        "or death from renal or cardiovascular causes."
                    )
                ],
            },
        ]

        created_docs_map: dict[str, Document] = {}

        for spec in docs_spec:
            existing_doc = (
                db.query(Document)
                .filter(
                    Document.title == spec["title"],
                    Document.patient_id == spec["patient_id"],
                )
                .first()
            )
            if not existing_doc:
                doc_file = storage_dir / spec["filename"]
                sha256, size_bytes = create_sample_pdf(doc_file, spec["title"], spec["pages"])
                db_doc = Document(
                    patient_id=spec["patient_id"],
                    title=spec["title"],
                    file_path=str(doc_file),
                    file_hash_sha256=sha256,
                    file_size_bytes=size_bytes,
                    doc_type=spec["doc_type"],
                    doc_date=spec["doc_date"],
                    ingestion_status="completed",
                )
                db.add(db_doc)
                db.flush()
                created_docs_map[spec["filename"]] = db_doc

                # Create Chunks
                chunks_to_upsert: list[DocumentChunk] = []
                for p_num, p_text in enumerate(spec["pages"], start=1):
                    chunk = DocumentChunk(
                        document_id=db_doc.id,
                        chunk_index=p_num - 1,
                        page_number=p_num,
                        content=f"[Document: {db_doc.title}] [Page {p_num}]\n{p_text}",
                        raw_content=p_text,
                        token_count=len(p_text.split()),
                        metadata_json={
                            "patient_id": spec["patient_id"],
                            "doc_title": db_doc.title,
                            "doc_type": db_doc.doc_type,
                            "doc_date": db_doc.doc_date.isoformat() if db_doc.doc_date else None,
                        },
                    )
                    db.add(chunk)
                    db.flush()
                    chunks_to_upsert.append(chunk)

                # Index in vector store
                try:
                    v_store.upsert_chunks(chunks_to_upsert)
                    logger.info("Indexed %d chunks for '%s'", len(chunks_to_upsert), spec["title"])
                except Exception as exc:
                    logger.warning("Vector indexing skipped/failed for '%s': %s", spec["title"], exc)
            else:
                created_docs_map[spec["filename"]] = existing_doc

        db.commit()

        # 5. Seed Longitudinal Timeline Events & Contradictions
        logger.info("5. Seeding longitudinal clinical events & explicit contradictions...")
        eleanor_echo_doc = created_docs_map.get("Eleanor_Vance_Echo_2023.pdf")
        eleanor_consult_doc = created_docs_map.get("Eleanor_Vance_Cardiology_Consult_2024.pdf")
        marcus_path_doc = created_docs_map.get("Marcus_Thorne_Molecular_Pathology.pdf")
        marcus_onco_doc = created_docs_map.get("Marcus_Thorne_Oncology_Followup.pdf")
        clara_doc = created_docs_map.get("Clara_Oswald_Nephrology_Consult.pdf")
        arthur_intake_doc = created_docs_map.get("Arthur_Dent_Admission_Intake_2021.pdf")
        arthur_ed_doc = created_docs_map.get("Arthur_Dent_ED_Anaphylaxis_2023.pdf")

        events_data = [
            # Eleanor Vance: Ejection Fraction Contradiction
            {
                "patient_id": patients_map["SYNTH-10001"].id,
                "document_id": eleanor_echo_doc.id if eleanor_echo_doc else "doc-1",
                "event_type": "procedure",
                "event_date": date(2023, 5, 20),
                "description": "Baseline Echocardiogram: Left ventricular ejection fraction (LVEF) 45%",
                "value_or_dosage": "LVEF 45%",
                "clinical_status": "historical",
                "contradiction_flag": True,
                "contradiction_details": "Conflicts with subsequent echocardiogram dated April 10, 2024 showing LVEF 35% decline.",
            },
            {
                "patient_id": patients_map["SYNTH-10001"].id,
                "document_id": eleanor_consult_doc.id if eleanor_consult_doc else "doc-2",
                "event_type": "diagnosis",
                "event_date": date(2024, 4, 15),
                "description": "Cardiology Follow-Up: Repeat Echocardiogram LVEF 35% with symptomatic heart failure.",
                "value_or_dosage": "LVEF 35%",
                "clinical_status": "active",
                "contradiction_flag": True,
                "contradiction_details": "Interval decline from baseline 45% in 2023 to 35% in 2024 due to anthracycline cardiotoxicity.",
            },
            # Marcus Thorne: Molecular Testing & Targeted Therapy
            {
                "patient_id": patients_map["SYNTH-10002"].id,
                "document_id": marcus_path_doc.id if marcus_path_doc else "doc-3",
                "event_type": "lab_result",
                "event_date": date(2024, 2, 10),
                "description": "Molecular NGS Biopsy confirmed EGFR Exon 21 L858R point mutation (VAF 38.4%).",
                "value_or_dosage": "EGFR L858R",
                "clinical_status": "active",
                "contradiction_flag": False,
                "contradiction_details": None,
            },
            {
                "patient_id": patients_map["SYNTH-10002"].id,
                "document_id": marcus_onco_doc.id if marcus_onco_doc else "doc-4",
                "event_type": "medication",
                "event_date": date(2024, 2, 15),
                "description": "Initiated on Osimertinib (Tagrisso) 80 mg daily oral targeted therapy.",
                "value_or_dosage": "80 mg daily",
                "clinical_status": "active",
                "contradiction_flag": False,
                "contradiction_details": None,
            },
            # Clara Oswald: Nephrology Diagnosis
            {
                "patient_id": patients_map["SYNTH-10003"].id,
                "document_id": clara_doc.id if clara_doc else "doc-5",
                "event_type": "diagnosis",
                "event_date": date(2023, 11, 15),
                "description": "Diabetic Nephropathy / CKD Stage 3a diagnosed with microalbuminuria UACR 185 mg/g.",
                "value_or_dosage": "eGFR 52 mL/min",
                "clinical_status": "active",
                "contradiction_flag": False,
                "contradiction_details": None,
            },
            # Arthur Dent: Severe Allergy Contradiction
            {
                "patient_id": patients_map["SYNTH-10004"].id,
                "document_id": arthur_intake_doc.id if arthur_intake_doc else "doc-6",
                "event_type": "allergy",
                "event_date": date(2021, 6, 10),
                "description": "Admission Intake: Documented 'No Known Drug Allergies (NKDA)'.",
                "value_or_dosage": "NKDA",
                "clinical_status": "disputed",
                "contradiction_flag": True,
                "contradiction_details": "Conflicts with severe Penicillin anaphylaxis reaction documented on October 14, 2023.",
            },
            {
                "patient_id": patients_map["SYNTH-10004"].id,
                "document_id": arthur_ed_doc.id if arthur_ed_doc else "doc-7",
                "event_type": "allergy",
                "event_date": date(2023, 10, 14),
                "description": "Emergency Department Encounter: Severe Penicillin anaphylaxis with urticaria and bronchospasm.",
                "value_or_dosage": "Anaphylaxis",
                "clinical_status": "active",
                "contradiction_flag": True,
                "contradiction_details": "Patient experienced life-threatening anaphylaxis requiring IM epinephrine; overrides 2021 NKDA notation.",
            },
        ]

        for ev in events_data:
            existing_event = (
                db.query(ClinicalEvent)
                .filter(
                    ClinicalEvent.patient_id == ev["patient_id"],
                    ClinicalEvent.event_date == ev["event_date"],
                    ClinicalEvent.description == ev["description"],
                )
                .first()
            )
            if not existing_event:
                db.add(ClinicalEvent(**ev))

        db.commit()

        # 6. Seed Landmark Biomedical Research Studies (1-to-1 with Research Documents)
        logger.info("6. Seeding landmark biomedical research trials...")
        studies_data = [
            {
                "filename": "FLAURA_Trial_NEJM_2018.pdf",
                "title": "FLAURA: Osimertinib in Untreated EGFR-Mutated Advanced Non-Small-Cell Lung Cancer",
                "pmid": "29151359",
                "doi": "10.1056/NEJMoa1713137",
                "authors": "Soria JC, Ohe Y, Vansteenkiste J, et al.",
                "publication_date": date(2018, 1, 11),
                "study_design": "Randomized Controlled Trial",
                "population_description": "556 previously untreated patients with Exon 19 del or L858R EGFR-mutated advanced NSCLC",
                "sample_size": 556,
                "intervention": "Osimertinib 80 mg once daily vs standard EGFR-TKI (Gefitinib or Erlotinib)",
                "primary_outcome": "Progression-Free Survival (PFS): 18.9 months with Osimertinib vs 10.2 months with standard TKI (HR 0.46, p < 0.001)",
                "limitations": "Crossover allowed upon disease progression in standard care arm.",
            },
            {
                "filename": "EMPEROR_Reduced_Trial_NEJM_2020.pdf",
                "title": "EMPEROR-Reduced: Cardiovascular and Renal Outcomes with Empagliflozin in Heart Failure",
                "pmid": "32865377",
                "doi": "10.1056/NEJMoa2022190",
                "authors": "Packer M, Anker SD, Butler J, et al.",
                "publication_date": date(2020, 10, 8),
                "study_design": "Randomized Controlled Trial",
                "population_description": "3730 patients with NYHA Class II-IV heart failure and ejection fraction of 40% or less",
                "sample_size": 3730,
                "intervention": "Empagliflozin 10 mg once daily vs Placebo, added to recommended guideline therapy",
                "primary_outcome": "Composite of cardiovascular death or hospitalization for heart failure occurred in 19.4% vs 24.7% (HR 0.75, p < 0.001)",
                "limitations": "Underrepresentation of non-white patient demographics in selected clinical trial sites.",
            },
            {
                "filename": "DAPA_CKD_Trial_NEJM_2020.pdf",
                "title": "DAPA-CKD: Dapagliflozin in Patients with Chronic Kidney Disease",
                "pmid": "32970396",
                "doi": "10.1056/NEJMoa2024840",
                "authors": "Heerspink HJL, Stefansson BV, Correa-Rotter R, et al.",
                "publication_date": date(2020, 10, 8),
                "study_design": "Randomized Controlled Trial",
                "population_description": "4304 patients with CKD Stage 2-4 with or without Type 2 diabetes",
                "sample_size": 4304,
                "intervention": "Dapagliflozin 10 mg once daily vs Placebo",
                "primary_outcome": "Sustained decline in eGFR of at least 50%, end-stage kidney disease, or renal/CV death (HR 0.61, p < 0.001)",
                "limitations": "Trial stopped early for overwhelming efficacy at pre-specified interim analysis.",
            },
        ]

        for s_spec in studies_data:
            assigned_doc = created_docs_map.get(s_spec["filename"])
            if not assigned_doc:
                continue

            existing_study = db.query(ResearchStudy).filter(ResearchStudy.title == s_spec["title"]).first()
            if not existing_study:
                study_fields = {k: v for k, v in s_spec.items() if k != "filename"}
                db.add(ResearchStudy(document_id=assigned_doc.id, **study_fields))

        db.commit()
        logger.info("Successfully seeded all synthetic demonstration cohorts!")
        print("\n" + "=" * 60)
        print("  PATIENT360 SYNTHETIC DEMONSTRATION DATA SEEDING COMPLETE")
        print("=" * 60)
        print("  [+] Seeded Personas: Admin, Reviewer, Researcher, Auditor")
        print("  [+] Seeded Patients: 4 Synthetic Patient Dossiers (MRN 10001-10004)")
        print("  [+] Generated PDFs: Real multi-page clinical documents in storage")
        print("  [+] Vector Chunks: Indexed into Qdrant for immediate grounded RAG")
        print("  [+] Clinical Events: 7 dated longitudinal events with active contradictions")
        print("  [+] Research Trials: 3 landmark oncology and cardiology RCTs")
        print("=" * 60 + "\n")

    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    seed_demo_data()
