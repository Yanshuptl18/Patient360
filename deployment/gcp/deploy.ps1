# ==============================================================================
# Patient360: Google Cloud Run PowerShell Deployment Script
# ==============================================================================

$ErrorActionPreference = "Stop"

$PROJECT_ID = (gcloud config get-value project)
$REGION = if ($env:REGION) { $env:REGION } else { "us-central1" }
$BACKEND_SERVICE = "patient360-backend"
$FRONTEND_SERVICE = "patient360-frontend"

Write-Host "============================================================"
Write-Host " Deploying Patient360 to Google Cloud Run"
Write-Host " Project: $PROJECT_ID | Region: $REGION"
Write-Host "============================================================"

# 1. Enable Required GCP APIs
Write-Host "[1/4] Enabling required Google Cloud APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com

# 2. Ensure Artifact Registry repository exists
Write-Host "[2/4] Verifying Artifact Registry repository..."
try {
    gcloud artifacts repositories describe patient360 --location=$REGION 2>$null
} catch {
    gcloud artifacts repositories create patient360 --repository-format=docker --location=$REGION --description="Patient360 Docker Repository"
}

# 3. Build & Deploy Backend
Write-Host "[3/4] Building and deploying backend container..."
$BACKEND_IMAGE = "${REGION}-docker.pkg.dev/${PROJECT_ID}/patient360/backend:latest"
gcloud builds submit --tag $BACKEND_IMAGE -f deployment/docker/backend.Dockerfile .

gcloud run deploy $BACKEND_SERVICE `
    --image $BACKEND_IMAGE `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 2 `
    --timeout 60s `
    --set-env-vars ENVIRONMENT=production,DEBUG=false,LLM_PROVIDER=gemini,GEMINI_MODEL=gemini-3.5-flash-lite,LLM_FALLBACK_TO_MOCK=true

$BACKEND_URL = (gcloud run services describe $BACKEND_SERVICE --region=$REGION --format="value(status.url)")

# 4. Build & Deploy Frontend
Write-Host "[4/4] Building and deploying frontend container..."
$FRONTEND_IMAGE = "${REGION}-docker.pkg.dev/${PROJECT_ID}/patient360/frontend:latest"
gcloud builds submit --tag $FRONTEND_IMAGE -f deployment/docker/frontend.Dockerfile .

gcloud run deploy $FRONTEND_SERVICE `
    --image $FRONTEND_IMAGE `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 2 `
    --set-env-vars "BACKEND_URL=$BACKEND_URL"

$FRONTEND_URL = (gcloud run services describe $FRONTEND_SERVICE --region=$REGION --format="value(status.url)")

Write-Host "============================================================"
Write-Host " Deployment Complete!"
Write-Host " Frontend: $FRONTEND_URL"
Write-Host " Backend:  $BACKEND_URL"
Write-Host " Health:   $BACKEND_URL/api/v1/health"
Write-Host "============================================================"
