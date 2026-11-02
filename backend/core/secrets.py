"""Secret management and key rotation utilities for cloud and local deployments."""

import logging
import os
import secrets
from typing import Any

logger = logging.getLogger(__name__)


def generate_secure_secret_key(num_bytes: int = 32) -> str:
    """Generates a cryptographically strong hex string suitable for JWT_SECRET_KEY."""
    return secrets.token_hex(num_bytes)


def get_secret(
    secret_id: str,
    default: str | None = None,
    gcp_project_id: str | None = None,
) -> str | None:
    """
    Retrieves a secret from GCP Secret Manager if available, otherwise falls back to environment variables.
    """
    # 1. Attempt GCP Secret Manager if configured
    project = gcp_project_id or os.environ.get("GCP_PROJECT_ID")
    if project:
        try:
            from google.cloud import secretmanager  # type: ignore[import-untyped]

            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project}/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            payload: str = response.payload.data.decode("UTF-8").strip()
            if payload:
                return str(payload)
        except Exception as e:
            logger.debug("GCP Secret Manager lookup for %s bypassed: %s", secret_id, e)

    # 2. Fall back to OS environment variable
    val = os.environ.get(secret_id, default)
    return str(val) if val is not None else None


def validate_secret_strength(secret_value: str, min_length: int = 32) -> dict[str, Any]:
    """Validates entropy and length requirements for cryptographic secrets."""
    if not secret_value:
        return {"valid": False, "reason": "Secret cannot be empty."}

    if len(secret_value) < min_length:
        return {
            "valid": False,
            "reason": f"Secret length ({len(secret_value)}) is under required minimum {min_length}.",
        }

    weak_substrings = ["default", "secret", "insecure", "password", "test", "development"]
    if any(weak in secret_value.lower() for weak in weak_substrings):
        return {
            "valid": False,
            "reason": "Secret contains common insecure substrings.",
        }

    return {"valid": True, "length": len(secret_value), "entropy_bits": len(secret_value) * 4}
