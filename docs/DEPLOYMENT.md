# Patient360: Local Setup and Deployment Guide

## 1. System Requirements & Prerequisites
* **Operating System:** Windows 10/11, macOS, or Linux
* **RAM:** 16 GB RAM (Optimized for CPU-friendly execution without requiring a dedicated GPU)
* **Software Prerequisites:**
  * **Python:** Python 3.11 (accessible via `py -3.11` or `python`)
  * **Node.js:** Node.js v20+ and npm v10+
  * **Docker:** Docker Desktop (for local PostgreSQL and Qdrant instances)
  * **Git:** Installed and configured with LF line endings

---

## 2. Multi-Provider LLM Gateway Options (Zero-Cost Focus)

Patient360 implements a provider-independent LLM architecture designed for zero or near-zero operational costs across development, testing, and production:

| Deployment Tier | Provider | Model | Cost | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Production / Online** | Google Gemini API | `gemini-3.5-flash-lite` | **$0.00** | Hosted REST API on Google's free tier (15 RPM, 1M TPM, 1,500 RPD). |
| **Local Offline Dev** | Ollama | `qwen3:4b` | **$0.00** | Self-hosted local inference on `http://localhost:11434`. Runs on CPU or GPU. |
| **Automated CI / Test** | Mock Provider | `mock-clinical-grounded-v1` | **$0.00** | In-memory, deterministic citation generator. Zero latency, 100% offline. |

### 2.1 Provider Configuration (`.env`)

#### Option A: Hosted Google Gemini API (Recommended for Deployed App)
```ini
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
LLM_FALLBACK_TO_MOCK=true
```

#### Option B: Local Ollama (Recommended for Offline Development)
```powershell
# 1. Install Ollama (https://ollama.ai)
# 2. Pull the Qwen3 4B model:
ollama pull qwen3:4b

# 3. Configure .env:
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b
OLLAMA_TIMEOUT_SECONDS=60.0
```

#### Option C: Mock Provider (Default for Offline Tests & CI)
```ini
LLM_PROVIDER=mock
```

---

## 3. Local Development Environment Setup

### 3.1 Clone Repository and Prepare Environment
```powershell
# Navigate to workspace
cd e:\project\Patient360

# Initialize environment variables
Copy-Item .env.example .env
```

### 3.2 Launch Local Storage Infrastructure (Docker)
```powershell
# Start PostgreSQL (port 5432) and Qdrant (ports 6333, 6334)
docker compose -f deployment/docker-compose.yml up -d

# Verify container health
docker ps
```

### 3.3 Backend Setup (FastAPI & Python 3.11)
```powershell
# Create Python virtual environment using Python 3.11
py -3.11 -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Seed initial synthetic demonstration data (optional)
python scripts/seed_demo_data.py

# Launch FastAPI development server
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
*API Swagger Documentation is accessible at:* `http://localhost:8000/docs`

### 3.4 Frontend Setup (React, Vite & TypeScript)
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

## 4. Zero-Cost Online Production Deployment Strategy

To deploy Patient360 online while maintaining **$0 monthly infrastructure bills**, use the following battle-tested free-tier architecture:

```
                            ┌─────────────────────────────────┐
                            │      Vercel / Cloudflare Pages  │
                            │      (React SPA Frontend - $0)  │
                            └────────────────┬────────────────┘
                                             │ HTTPS
                                             ▼
                            ┌─────────────────────────────────┐
                            │       Render / Fly.io Free      │
                            │    (FastAPI Backend Service - $0)│
                            └────┬───────────────┬────────────┘
                                 │               │
                 SQL Statements  │               │ REST API
                                 ▼               ▼
        ┌──────────────────────────────┐   ┌──────────────────────────────┐
        │   Neon / Supabase Serverless │   │   Qdrant Cloud Free Tier     │
        │   PostgreSQL (500MB DB - $0) │   │   (1GB Cluster - $0)         │
        └──────────────────────────────┘   └──────────────────────────────┘
                                                 │
                                                 │ HTTPS REST (Native httpx)
                                                 ▼
                                   ┌──────────────────────────────┐
                                   │  Google Gemini Free Tier     │
                                   │  (gemini-3.5-flash-lite - $0)│
                                   └──────────────────────────────┘
```

### 4.1 Free-Tier Component Breakdown
1. **Frontend Hosting (Vercel or Cloudflare Pages - $0):**
   * Connect Git repository. Set build command `npm run build` and publish directory `dist`.
   * Configure environment variable: `VITE_API_BASE_URL=https://your-backend.onrender.com/api/v1`.
2. **Backend Hosting (Render Web Service - $0):**
   * Connect Git repo as a Python Web Service.
   * Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
   * Set environment variables in Render Dashboard (`GEMINI_API_KEY`, `DATABASE_URL`, `QDRANT_HOST`, `QDRANT_API_KEY`, `JWT_SECRET_KEY`).
3. **Database (Neon Serverless PostgreSQL - $0):**
   * Neon provides a permanent free-tier PostgreSQL instance with connection pooling.
   * Set `DATABASE_URL=postgresql://user:pass@ep-xyz.neon.tech/patient360?sslmode=require`.
4. **Vector Store (Qdrant Cloud Free Tier - $0):**
   * Qdrant Cloud provides a 1GB persistent cluster for free without expiring.
   * Set `QDRANT_HOST=your-cluster-id.us-east4-0.gcp.cloud.qdrant.io`, `QDRANT_PORT=6333`, `QDRANT_API_KEY=xyz`.
5. **LLM Inference (Google Gemini Free Tier - $0):**
   * Free tier provides 15 Requests Per Minute (RPM) and 1,000,000 Tokens Per Minute (TPM) on `gemini-3.5-flash-lite`.
   * Zero credit card required; zero pay-per-token API costs.

---

## 5. Security & Responsible AI Deployment Checklist
* **Zero API Key Leakage:** Never include API keys in frontend environment variables (`VITE_*`) or commit `.env` to Git.
* **Audit Sanitization:** All audit records written to the database automatically scrub API keys, tokens, SSNs, and credit cards.
* **Right-to-be-Forgotten:** Administrators can invoke `DELETE /api/v1/patients/{id}` to atomically purge relational records, binary storage files, and vector embeddings.
* **Emergency Escalation:** Inquiries exhibiting acute emergency symptoms automatically trigger red-flag escalation banners and disclaimers.
