"""Audit log sanitizer preventing API keys, secrets, tokens, and PHI from leaking into audit storage."""

import re
from typing import Any

# Sensitive dictionary keys to immediately redact
SENSITIVE_KEYS = {
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "auth",
    "authorization",
    "private_key",
    "credit_card",
    "ssn",
}

# Regex patterns for credential masking
SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Gemini / Google API Keys
    (re.compile(r"AQ\.[A-Za-z0-9_-]{20,}", re.IGNORECASE), "[REDACTED_GEMINI_KEY]"),
    (re.compile(r"AIza[0-9A-Za-z-_]{20,}", re.IGNORECASE), "[REDACTED_GOOGLE_KEY]"),
    # Bearer tokens
    (re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{15,}", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    # JWT tokens
    (re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), "[REDACTED_JWT]"),
    # Key-value secret assignments in strings (e.g. key=xyz123)
    (
        re.compile(r"(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.]{6,})['\"]?", re.IGNORECASE),
        r"\1=[REDACTED_SECRET]",
    ),
]

# Regex patterns for sensitive identifiers (PHI / PII)
PHI_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Social Security Numbers (XXX-XX-XXXX)
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    # Credit Card Numbers
    (re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), "[REDACTED_CREDIT_CARD]"),
    # Email addresses (preserve domain for debugging if helpful, or mask completely)
    (re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b"), r"[REDACTED_USER]@\1"),
]


def sanitize_text(text: str) -> str:
    """
    Masks API keys, security tokens, and high-risk sensitive patterns in an arbitrary string.
    """
    if not text:
        return ""

    sanitized = text
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    for pattern, replacement in PHI_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    return sanitized


def sanitize_value(value: Any) -> Any:
    """
    Recursively sanitizes primitive values, lists, and dicts.
    """
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, dict):
        return sanitize_audit_details(value)
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_value(item) for item in value)
    return value


def sanitize_audit_details(details: dict[str, Any] | None) -> dict[str, Any]:
    """
    Returns a sanitized copy of an audit event details dictionary.
    Keys matching sensitive names are replaced with '[REDACTED_SECRET]',
    and all string values are scrubbed of API keys, tokens, and PHI patterns.
    """
    if not details:
        return {}

    sanitized: dict[str, Any] = {}
    for key, val in details.items():
        lower_key = str(key).lower()
        if any(s in lower_key for s in SENSITIVE_KEYS):
            sanitized[key] = "[REDACTED_SECRET]"
        else:
            sanitized[key] = sanitize_value(val)

    return sanitized
