"""Responsible AI safety guards, emergency symptom escalation, and prompt injection defense."""

import re

from backend.core.config import settings

# Standard clinical decision support disclaimer required by regulatory guidance
CLINICAL_SAFETY_DISCLAIMER = (
    "\n\n---\n*Clinical Decision Support Notice: Patient360 is an informational clinical retrieval and synthesis "
    "assistant. It does not replace professional medical judgment, diagnosis, or treatment. All findings, citations, "
    "and inferences must be independently verified against original medical records prior to clinical decision-making.*"
)

# Emergency Escalation Notice for acute life-threatening presentations
EMERGENCY_ESCALATION_BANNER = (
    "\n\n[CRITICAL MEDICAL EMERGENCY WARNING]: The inquiry or documented findings describe acute, potentially "
    "life-threatening clinical symptoms. If this involves an active patient in distress, initiate immediate emergency "
    f"medical services ({settings.EMERGENCY_CONTACT_INFO}) without delay. Automated decision support "
    "tools must never delay emergency care."
)

# Regex patterns matching acute red-flag medical presentations
EMERGENCY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\b(crushing\s+(chest\s+pain|retrosternal\s+pain)|radiat(ing|ion)\s+to\s+(left\s+arm|jaw)|acute\s+myocardial\s+infarction|st-elevation|unstable\s+angina)\b",
            re.IGNORECASE,
        ),
        "Acute Coronary Syndrome / Suspected Myocardial Infarction",
    ),
    (
        re.compile(
            r"\b(cardiac\s+arrest|asystole|ventricular\s+fibrillation|pulseless(ness)?|unresponsive\s+patient|cpr\s+in\s+progress)\b",
            re.IGNORECASE,
        ),
        "Cardiopulmonary Arrest / Hemodynamic Collapse",
    ),
    (
        re.compile(
            r"\b(facial\s+droop|arm\s+drift|slurred\s+speech|acute\s+hemiplegia|sudden\s+numbness|aphasia|stroke\s+symptoms|suspected\s+cva)\b",
            re.IGNORECASE,
        ),
        "Suspected Acute Cerebrovascular Accident (Stroke / TIA)",
    ),
    (
        re.compile(
            r"\b(severe\s+respiratory\s+distress|stridor|inability\s+to\s+breathe|cyanosis|gasping\s+for\s+air|acute\s+respiratory\s+failure)\b",
            re.IGNORECASE,
        ),
        "Severe Respiratory Failure / Airway Compromise",
    ),
    (
        re.compile(
            r"\b(anaphylaxis|anaphylactic\s+shock|throat\s+swelling|angioedema|epinephrine\s+auto-injector\s+needed)\b",
            re.IGNORECASE,
        ),
        "Severe Allergic Anaphylaxis / Airway Edema",
    ),
    (
        re.compile(
            r"\b(suicid(al|e)\s+(ideation|intent|attempt|plan)|want\s+to\s+(kill\s+myself|end\s+my\s+life)|severe\s+self-harm)\b",
            re.IGNORECASE,
        ),
        "Acute Psychiatric Crisis / Suicidal Ideation",
    ),
    (
        re.compile(
            r"\b(thunderclap\s+headache|worst\s+headache\s+of\s+(my\s+)?life|sudden\s+loss\s+of\s+consciousness|massive\s+hemorrhage|arterial\s+bleed|hypovolemic\s+shock|severe\s+bleeding)\b",
            re.IGNORECASE,
        ),
        "Acute Neurological or Hemorrhagic Crisis",
    ),
]

# Prompt injection and jailbreak attempt signatures
INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+(developer|dan|jailbreak|unrestricted)\s+mode", re.IGNORECASE),
    re.compile(r"bypass\s+(all\s+)?(safety|security|ethical)\s+guardrails", re.IGNORECASE),
    re.compile(r"system\s+prompt\s*:\s*reveal", re.IGNORECASE),
    re.compile(r"output\s+(your\s+)?initial\s+system\s+instructions", re.IGNORECASE),
]


def check_emergency_symptoms(text: str) -> tuple[bool, str | None]:
    """
    Scans text for acute clinical emergency red-flags (ACS, Stroke, Anaphylaxis, etc.).
    Returns (True, emergency_category) if an acute condition is identified, otherwise (False, None).
    """
    if not text:
        return False, None

    for pattern, category in EMERGENCY_PATTERNS:
        if pattern.search(text):
            return True, category

    return False, None


def detect_prompt_injection(text: str) -> tuple[bool, str | None]:
    """
    Inspects user input or document content for adversarial prompt injection attempts.
    Returns (True, pattern_match) if an injection pattern is detected, otherwise (False, None).
    """
    if not text:
        return False, None

    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, match.group(0)

    return False, None


def sanitize_prompt_input(text: str) -> str:
    """
    Neutralizes adversarial delimiters or injection phrasing from user clinical query.
    """
    if not text:
        return ""
    # Strip dangerous markers that try to break out of untrusted delimiters
    sanitized = re.sub(r"<{3,}|>{3,}", "", text)
    sanitized = re.sub(r"={3,}", "", sanitized)
    return sanitized.strip()


def apply_clinical_safety_disclaimer(
    answer: str,
    is_emergency: bool = False,
    emergency_category: str | None = None,
) -> str:
    """
    Attaches standardized clinical safety notices and emergency escalation banners to AI outputs.
    Guarantees disclaimers are present and idempotent.
    """
    result = answer.rstrip()

    # Prepend or append emergency escalation banner if acute signs are present
    if is_emergency:
        category_note = f" (Identified Indicator: {emergency_category})" if emergency_category else ""
        banner = EMERGENCY_ESCALATION_BANNER + category_note
        if EMERGENCY_ESCALATION_BANNER not in result:
            result = f"{result}\n{banner}"

    # Append standard clinical disclaimer if not already present
    if CLINICAL_SAFETY_DISCLAIMER not in result:
        result = f"{result}{CLINICAL_SAFETY_DISCLAIMER}"

    return result
