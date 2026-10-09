"""Structured logging with PHI sanitization filters."""

import logging
import re
import sys


class PHISanitizingFilter(logging.Filter):
    """
    Sanitizes log records to prevent accidental logging of sensitive medical text,
    MRNs, SSNs, or prompt payloads.
    """

    # Patterns matching potential MRNs or clinical document snippets
    SENSITIVE_PATTERNS = [
        re.compile(r"SYNTH-\d{5,8}", re.IGNORECASE),
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN pattern
        re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),  # Auth tokens
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern in self.SENSITIVE_PATTERNS:
                record.msg = pattern.sub("[REDACTED_SENSITIVE]", record.msg)
        return True


def setup_logging(debug: bool = False) -> None:
    """Configures root logger with PHI sanitization and structured formatting."""
    log_level = logging.DEBUG if debug else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(PHISanitizingFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = [handler]

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)
