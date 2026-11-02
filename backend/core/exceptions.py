"""Custom domain exceptions and FastAPI exception handlers."""

from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class Patient360Exception(Exception):
    """Base exception for all Patient360 domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class EntityNotFoundError(Patient360Exception):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class AuthorizationError(Patient360Exception):
    def __init__(self, message: str = "Permission denied for this resource."):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class AuthenticationError(Patient360Exception):
    def __init__(self, message: str = "Invalid or expired authentication credentials."):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class DatabaseConnectionError(Patient360Exception):
    def __init__(self, message: str = "Could not establish database connection."):
        super().__init__(
            message=message,
            code="DATABASE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class LLMProviderUnavailableError(Patient360Exception, RuntimeError):
    def __init__(
        self,
        message: str = "Clinical AI service is temporarily unavailable due to upstream provider rate limits, quota exhaustion, or connectivity failure.",
        details: dict[str, Any] | None = None,
    ):
        Patient360Exception.__init__(
            self,
            message=message,
            code="LLM_PROVIDER_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class ConfigurationError(Patient360Exception):
    def __init__(self, message: str = "System configuration error."):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Registers standard JSON exception handlers on the FastAPI application."""

    @app.exception_handler(Patient360Exception)
    async def patient360_exception_handler(
        request: Request, exc: Patient360Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details if exc.details else None,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred.",
                    "details": None,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            },
        )
