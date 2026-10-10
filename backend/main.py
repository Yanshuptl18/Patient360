"""Patient360: FastAPI Application Entrypoint."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

import backend.models  # noqa: F401 (register models with Base)
from backend.api.v1 import api_router
from backend.core.config import settings
from backend.core.database import Base, engine
from backend.core.exceptions import register_exception_handlers
from backend.core.logging import setup_logging
from backend.core.metrics import MetricsMiddleware, generate_prometheus_response

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown hooks."""
    setup_logging(debug=settings.DEBUG)
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")

    # Initialize tables if database is available
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as exc:
        logger.warning(f"Could not automatically initialize database tables: {exc}")

    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Evidence-grounded healthcare intelligence and bounded RAG platform.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Configure Prometheus Metrics Middleware
app.add_middleware(MetricsMiddleware)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Custom Exception Handlers
register_exception_handlers(app)

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    """Root metadata endpoint."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "health_url": f"{settings.API_V1_STR}/health",
        "notice": "Patient360 is an informational and research synthesis platform. Not a medical device.",
    }


@app.get("/health", tags=["System Health"])
def basic_health() -> dict[str, str]:
    """Basic liveness ping for container orchestrators."""
    return {"status": "OK", "version": settings.VERSION}


@app.get("/metrics", tags=["Observability"], include_in_schema=True)
def get_prometheus_metrics() -> Response:
    """Prometheus exposition endpoint for telemetry scrapers."""
    return generate_prometheus_response()
