# Patient360: Local Setup and Deployment Guide

## 1. System Requirements & Prerequisites
* **Operating System:** Windows 10/11 (PowerShell or Windows Terminal)
* **RAM:** 16 GB RAM (Optimized for CPU-friendly execution without dedicated GPU)
* **Software Prerequisites:**
  * **Python:** Python 3.11 (accessible via `py -3.11` or `python`)
  * **Node.js:** Node.js v20+ and npm v10+
  * **Docker:** Docker Desktop with WSL2 backend (for PostgreSQL and Qdrant)
  * **Git:** Installed and configured with LF line endings

---

## 2. Local Development Environment Setup

### 2.1 Clone Repository and Prepare Environment
```powershell
# Navigate to workspace
cd e:\project\Patient360

# Initialize environment variables
Copy-Item .env.example .env
```

### 2.2 Launch Docker Infrastructure (PostgreSQL & Qdrant)
```powershell
# Start PostgreSQL (port 5432) and Qdrant (ports 6333, 6334)
docker compose -f deployment/docker-compose.yml up -d

# Verify container health
docker ps
```

### 2.3 Backend Setup (FastAPI & Python 3.11)
```powershell
# Create Python virtual environment using Python 3.11
py -3.11 -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Seed initial synthetic demonstration data (optional)
python scripts/seed_demo_data.py

# Launch FastAPI development server
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
*API Swagger Documentation is accessible at:* `http://localhost:8000/docs`

### 2.4 Frontend Setup (React, Vite & TypeScript)
```powershell
# In a separate terminal window:
cd e:\project\Patient360\frontend

# Install dependencies
npm install

# Launch Vite development server
npm run dev
```
*Frontend Web Application is accessible at:* `http://localhost:5173`

---

## 3. Container Resource Configuration
To ensure smooth execution within 16 GB of system RAM, Docker containers are bounded:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    deploy:
      resources:
        limits:
          memory: 512M
  qdrant:
    image: qdrant/qdrant:latest
    deploy:
      resources:
        limits:
          memory: 512M
```

---

## 4. Production Deployment Topology

```
Internet / Clinician Client
         │
         ▼ (HTTPS / Port 443)
┌─────────────────────────────────┐
│     Nginx Reverse Proxy         │
├────────────────┬────────────────┤
│ /              │ /api/v1/       │
│ (Static React) │ (Reverse Proxy)│
└────────┬───────┴────────┬───────┘
         │                │
         ▼                ▼
   Static Assets    Gunicorn / Uvicorn Workers
   (Vite Build)     (FastAPI Backend)
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
    PostgreSQL 16                 Qdrant Vector DB
    (Encrypted EBS)               (Encrypted Volume)
```

### 4.1 Production Security Checklist
* Enforce TLS 1.3 encryption for all external traffic.
* Store all database passwords, JWT secrets, and provider API keys in environment variables or cloud secrets managers (AWS Secrets Manager, HashiCorp Vault). Never commit secrets to Git.
* Enforce automated daily PostgreSQL database backups with point-in-time recovery.
