"""Clinical contradiction detection engine for longitudinal patient dossiers.

Surfaces contradictory statements across multiple documents, such as:
1. Conflicting allergy declarations (NKDA vs specific drug allergy).
2. Active medication prescription of an allergic/contraindicated agent.
3. Divergent surgical or procedure dates (e.g. Appendectomy in 2018 vs 2021).
4. Status discrepancies (resolved condition reported as active without interval progression).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.schemas.timeline import (
    ContradictionItem,
)

if TYPE_CHECKING:
    from backend.models.timeline import ClinicalEvent

logger = logging.getLogger(__name__)


class ContradictionDetector:
    """Analyzes a collection of patient clinical events to surface contradictions."""

    def detect_contradictions(
        self,
        events: list[ClinicalEvent],
    ) -> list[ContradictionItem]:
        """
        Inspects all events and identifies cross-document clinical contradictions.
        Modifies events in-place setting contradiction_flag=True and contradiction_details.
        Returns a list of structured ContradictionItem objects.
        """
        contradictions: list[ContradictionItem] = []

        # 1. Check for Allergy vs NKDA conflicts
        allergy_conflicts = self._check_allergy_vs_nkda(events)
        contradictions.extend(allergy_conflicts)

        # 2. Check for Allergy vs Active Medication prescription
        med_allergy_conflicts = self._check_allergy_vs_active_med(events)
        contradictions.extend(med_allergy_conflicts)

        # 3. Check for Divergent Surgical / Procedure dates
        proc_date_conflicts = self._check_procedure_date_discrepancies(events)
        contradictions.extend(proc_date_conflicts)

        # 4. Check for Diagnosis Status conflicts
        diag_status_conflicts = self._check_diagnosis_status_conflicts(events)
        contradictions.extend(diag_status_conflicts)

        return contradictions

    def _check_allergy_vs_nkda(self, events: list[ClinicalEvent]) -> list[ContradictionItem]:
        items: list[ContradictionItem] = []
        nkda_events = [e for e in events if e.event_type == "allergy" and "nkda" in e.description.lower()]
        specific_allergies = [
            e for e in events if e.event_type == "allergy" and "nkda" not in e.description.lower()
        ]

        for nkda in nkda_events:
            for spec in specific_allergies:
                if nkda.document_id == spec.document_id:
                    continue  # Only flag cross-document conflicts

                explanation = (
                    f"Conflicting allergy declarations: Document '{nkda.document.title if nkda.document else 'Doc A'}' "
                    f"declares No Known Drug Allergies (NKDA), whereas Document "
                    f"'{spec.document.title if spec.document else 'Doc B'}' records '{spec.description}' "
                    f"with reaction '{spec.value_or_dosage or 'unspecified'}'. "
                    f"Risk of inadvertent drug administration."
                )

                # Mark events
                nkda.contradiction_flag = True
                spec.contradiction_flag = True
                nkda.contradiction_details = explanation
                spec.contradiction_details = explanation

                items.append(
                    ContradictionItem(
                        event_id_1=nkda.id,
                        event_id_2=spec.id,
                        event_1_summary=f"{nkda.description} ({nkda.event_date})",
                        event_2_summary=f"{spec.description} ({spec.value_or_dosage or 'unspecified'})",
                        document_title_1=nkda.document.title if nkda.document else "Document 1",
                        document_title_2=spec.document.title if spec.document else "Document 2",
                        page_number_1=nkda.chunk.page_number if nkda.chunk else None,
                        page_number_2=spec.chunk.page_number if spec.chunk else None,
                        conflict_type="allergy_conflict",
                        severity="critical",
                        explanation=explanation,
                        suggested_resolution="Reconcile allergy profile with patient directly; verify prior hypersensitivity reaction.",
                    )
                )

        return items

    def _check_allergy_vs_active_med(self, events: list[ClinicalEvent]) -> list[ContradictionItem]:
        items: list[ContradictionItem] = []
        allergy_events = [
            e for e in events if e.event_type == "allergy" and "nkda" not in e.description.lower()
        ]
        med_events = [e for e in events if e.event_type == "medication"]

        for allg in allergy_events:
            allg_lower = allg.description.lower()
            for med in med_events:
                med_lower = med.description.lower()
                # Extract base drug name (e.g. "Lisinopril Allergy" vs "Lisinopril Therapy")
                drug_term = allg_lower.replace("allergy", "").strip()
                if drug_term and drug_term in med_lower and allg.document_id != med.document_id:
                    explanation = (
                        f"Contra-indicated medication prescription: Document '{med.document.title if med.document else 'Doc A'}' "
                        f"lists active therapy '{med.description}' ({med.value_or_dosage or ''}), while Document "
                        f"'{allg.document.title if allg.document else 'Doc B'}' documents '{allg.description}' "
                        f"({allg.value_or_dosage or 'reaction'})."
                    )

                    allg.contradiction_flag = True
                    med.contradiction_flag = True
                    allg.contradiction_details = explanation
                    med.contradiction_details = explanation

                    items.append(
                        ContradictionItem(
                            event_id_1=allg.id,
                            event_id_2=med.id,
                            event_1_summary=f"{allg.description} ({allg.value_or_dosage or 'reaction'})",
                            event_2_summary=f"{med.description} ({med.value_or_dosage or ''})",
                            document_title_1=allg.document.title if allg.document else "Allergy Record",
                            document_title_2=med.document.title if med.document else "Medication Record",
                            page_number_1=allg.chunk.page_number if allg.chunk else None,
                            page_number_2=med.chunk.page_number if med.chunk else None,
                            conflict_type="allergy_conflict",
                            severity="critical",
                            explanation=explanation,
                            suggested_resolution="Suspend active medication order pending allergy confirmation.",
                        )
                    )

        return items

    def _check_procedure_date_discrepancies(self, events: list[ClinicalEvent]) -> list[ContradictionItem]:
        items: list[ContradictionItem] = []
        procedures = [e for e in events if e.event_type == "procedure"]

        for i, p1 in enumerate(procedures):
            for p2 in procedures[i + 1 :]:
                if p1.description.lower() == p2.description.lower() and p1.document_id != p2.document_id:
                    # Check for year discrepancy
                    if abs(p1.event_date.year - p2.event_date.year) >= 1:
                        explanation = (
                            f"Divergent surgical history date: Document '{p1.document.title if p1.document else 'Doc A'}' "
                            f"dates '{p1.description}' to {p1.event_date.year}, whereas Document "
                            f"'{p2.document.title if p2.document else 'Doc B'}' records it in {p2.event_date.year}."
                        )

                        p1.contradiction_flag = True
                        p2.contradiction_flag = True
                        p1.contradiction_details = explanation
                        p2.contradiction_details = explanation

                        items.append(
                            ContradictionItem(
                                event_id_1=p1.id,
                                event_id_2=p2.id,
                                event_1_summary=f"{p1.description} ({p1.event_date})",
                                event_2_summary=f"{p2.description} ({p2.event_date})",
                                document_title_1=p1.document.title if p1.document else "Doc 1",
                                document_title_2=p2.document.title if p2.document else "Doc 2",
                                page_number_1=p1.chunk.page_number if p1.chunk else None,
                                page_number_2=p2.chunk.page_number if p2.chunk else None,
                                conflict_type="date_conflict",
                                severity="moderate",
                                explanation=explanation,
                                suggested_resolution="Verify operative note or pathology report for authoritative surgical date.",
                            )
                        )

        return items

    def _check_diagnosis_status_conflicts(self, events: list[ClinicalEvent]) -> list[ContradictionItem]:
        items: list[ContradictionItem] = []
        diagnoses = [e for e in events if e.event_type == "diagnosis"]

        for i, d1 in enumerate(diagnoses):
            for d2 in diagnoses[i + 1 :]:
                if d1.description.lower() == d2.description.lower() and d1.document_id != d2.document_id:
                    # If one is resolved and the other is active at the same time or earlier date
                    if (
                        (d1.clinical_status == "resolved" and d2.clinical_status == "active" and d2.event_date <= d1.event_date)
                        or (d2.clinical_status == "resolved" and d1.clinical_status == "active" and d1.event_date <= d2.event_date)
                    ):
                        explanation = (
                            f"Clinical status discrepancy: Condition '{d1.description}' is marked '{d1.clinical_status}' "
                            f"in Document '{d1.document.title if d1.document else 'Doc 1'}' ({d1.event_date}) but listed as "
                            f"'{d2.clinical_status}' in Document '{d2.document.title if d2.document else 'Doc 2'}' ({d2.event_date})."
                        )

                        d1.contradiction_flag = True
                        d2.contradiction_flag = True
                        d1.contradiction_details = explanation
                        d2.contradiction_details = explanation

                        items.append(
                            ContradictionItem(
                                event_id_1=d1.id,
                                event_id_2=d2.id,
                                event_1_summary=f"{d1.description} [{d1.clinical_status}] ({d1.event_date})",
                                event_2_summary=f"{d2.description} [{d2.clinical_status}] ({d2.event_date})",
                                document_title_1=d1.document.title if d1.document else "Doc 1",
                                document_title_2=d2.document.title if d2.document else "Doc 2",
                                page_number_1=d1.chunk.page_number if d1.chunk else None,
                                page_number_2=d2.chunk.page_number if d2.chunk else None,
                                conflict_type="status_conflict",
                                severity="moderate",
                                explanation=explanation,
                                suggested_resolution="Assess whether diagnosis represents disease recurrence or clinical documentation error.",
                            )
                        )

        return items
