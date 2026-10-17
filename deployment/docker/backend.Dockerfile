# ==============================================================================
# Patient360 Backend: Multi-Stage Production Dockerfile
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Dependencies
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --user --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Minimal Runtime Environment
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runner

# Security: Create unprivileged application user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/false -m appuser

WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Set runtime environment variables
ENV PATH="/home/appuser/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production

# Copy application source code
COPY --chown=appuser:appgroup backend /app/backend
COPY --chown=appuser:appgroup scripts /app/scripts
COPY --chown=appuser:appgroup pyproject.toml /app/pyproject.toml

# Prepare writable storage directory for uploaded documents
RUN mkdir -p /app/storage/documents && \
    chown -R appuser:appgroup /app/storage

USER appuser

# Cloud Run dynamic port support (defaults to 8080 on GCP, fallback 8000)
ENV PORT=8080
EXPOSE 8080

# Container liveness healthcheck
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request, os; p = os.environ.get('PORT', '8080'); urllib.request.urlopen(f'http://127.0.0.1:{p}/health')" || exit 1

# Launch ASGI production server respecting PORT environment variable
CMD ["sh", "-c", "python scripts/seed_demo_data.py || true; exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
