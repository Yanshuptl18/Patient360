#!/usr/bin/env bash
# ==============================================================================
# Patient360: Google Cloud Run Deployment Script
# Deploys Backend and Frontend containers directly to Google Cloud Run
# ==============================================================================

set -euo pipefail

PROJECT_ID=$(gcloud config get-value project)
REGION=${REGION:-"us-central1"}
BACKEND_SERVICE="patient360-backend"
FRONTEND_SERVICE="patient360-frontend"

echo "============================================================"
echo " Deploying Patient360 to Google Cloud Run"
echo " Project: ${PROJECT_ID} | Region: ${REGION}"
echo "============================================================"

# 1. Enable Required Google Cloud APIs
echo "[1/4] Enabling required GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    sqladmin.googleapis.com

# 2. Ensure Artifact Registry repository exists
echo "[2/4] Verifying Artifact Registry repository..."
gcloud artifacts repositories describe patient360 --location="${REGION}" >/dev/null 2>&1 || \
gcloud artifacts repositories create patient360 \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Patient360 Docker Repository"

# 3. Build & Deploy Backend
echo "[3/4] Building and deploying backend service..."
BACKEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/patient360/backend:latest"
gcloud builds submit --tag "${BACKEND_IMAGE}" -f deployment/docker/backend.Dockerfile .

gcloud run deploy "${BACKEND_SERVICE}" \
    --image "${BACKEND_IMAGE}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 60s \
    --concurrency 80 \
    --min-instances 0 \
    --max-instances 2 \
    --set-env-vars ENVIRONMENT=production,DEBUG=false,LLM_PROVIDER=gemini,GEMINI_MODEL=gemini-3.5-flash-lite,LLM_FALLBACK_TO_MOCK=true

BACKEND_URL=$(gcloud run services describe "${BACKEND_SERVICE}" --region="${REGION}" --format="value(status.url)")
echo "Backend deployed at: ${BACKEND_URL}"

# 4. Build & Deploy Frontend
echo "[4/4] Building and deploying frontend service..."
FRONTEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/patient360/frontend:latest"
gcloud builds submit --tag "${FRONTEND_IMAGE}" -f deployment/docker/frontend.Dockerfile .

gcloud run deploy "${FRONTEND_SERVICE}" \
    --image "${FRONTEND_IMAGE}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 30s \
    --min-instances 0 \
    --max-instances 2 \
    --set-env-vars "BACKEND_URL=${BACKEND_URL}"

FRONTEND_URL=$(gcloud run services describe "${FRONTEND_SERVICE}" --region="${REGION}" --format="value(status.url)")

echo "============================================================"
echo " Deployment Complete!"
echo " Frontend: ${FRONTEND_URL}"
echo " Backend:  ${BACKEND_URL}"
echo " Health:   ${BACKEND_URL}/api/v1/health"
echo "============================================================"
