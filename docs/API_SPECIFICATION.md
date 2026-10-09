# Patient360: API Specification

## 1. Global API Standards
* **Base URL:** `/api/v1`
* **Content Type:** `application/json` (except file uploads using `multipart/form-data`)
* **Authentication:** `Authorization: Bearer <jwt_access_token>`
* **Standard Error Schema:**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested patient record was not found or access is denied.",
    "details": null,
    "timestamp": "2026-10-09T15:30:00Z"
  }
}
```

---

## 2. Authentication and Authorization (`/auth`)

### 2.1 Login
* **Method & Path:** `POST /api/v1/auth/login`
* **Request Body:**
```json
{
  "email": "reviewer@patient360.local",
  "password": "SecurePassword123!"
}
```
* **Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "c1f8e123-4567-4890-abcd-ef1234567890",
    "email": "reviewer@patient360.local",
    "full_name": "Dr. Evelyn Reed",
    "role": "reviewer"
  }
}
```

### 2.2 Refresh Token
* **Method & Path:** `POST /api/v1/auth/refresh`
* **Request Body:** `{ "refresh_token": "eyJhbGciOi..." }`
* **Response (200 OK):** `{ "access_token": "eyJhbGci...", "token_type": "bearer", "expires_in": 1800 }`

### 2.3 Current User Profile
* **Method & Path:** `GET /api/v1/auth/me`
* **Response (200 OK):** User demographic record and role permissions.

---

## 3. Patient Dossier Management (`/patients`)

### 3.1 List Authorized Patients
* **Method & Path:** `GET /api/v1/patients`
* **Query Params:** `skip=0`, `limit=20`, `search=John`
* **Response (200 OK):**
```json
[
  {
    "id": "3c90f235-5a8e-4a6c-947b-7b0b6c52a0a2",
    "mrn_synthetic": "SYNTH-84920",
    "first_name": "Eleanor",
    "last_name": "Vance",
    "date_of_birth": "1964-08-14",
    "gender": "female",
    "primary_condition": "Cardio-Oncology / Heart Failure",
    "document_count": 8,
    "created_at": "2026-09-01T10:00:00Z"
  }
]
```

### 3.2 Patient Clinical Timeline
* **Method & Path:** `GET /api/v1/patients/{id}/timeline`
* **Query Params:** `event_type=medication,diagnosis`, `start_date=2021-01-01`, `end_date=2024-12-31`
* **Response (200 OK):**
```json
[
  {
    "id": "e4b1a2c3-1111-2222-3333-444455556666",
    "event_date": "2021-04-12",
    "event_date_precision": "day",
    "document_date": "2021-04-14",
    "event_type": "medication",
    "description": "Lisinopril discontinued due to facial angioedema",
    "value_or_dosage": "10 mg daily",
    "clinical_status": "historical",
    "contradiction_flag": true,
    "contradiction_details": "Clinic note from 2023 lists Lisinopril under active medications without allergy mention.",
    "source_citation": {
      "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "document_title": "Discharge_Summary_2021.pdf",
      "page_number": 3
    }
  }
]
```

---

## 4. Document Management & Ingestion (`/documents`)

### 4.1 Upload Document
* **Method & Path:** `POST /api/v1/documents/upload`
* **Content-Type:** `multipart/form-data`
* **Form Fields:**
  * `file`: (binary PDF file)
  * `patient_id`: `3c90f235-5a8e-4a6c-947b-7b0b6c52a0a2` (optional, for patient record)
  * `doc_type`: `discharge_summary`
  * `doc_date`: `2021-04-14`
* **Response (202 Accepted):**
```json
{
  "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "processing",
  "message": "Document accepted for ingestion and vector indexing.",
  "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

### 4.2 Document Status & Chunks
* **Method & Path:** `GET /api/v1/documents/{id}`
* **Response (200 OK):** Metadata, parsing metrics, chunk count, and ingestion status (`completed`).
* **Method & Path:** `GET /api/v1/documents/{id}/chunks`
* **Response (200 OK):** Paginated extracted chunks with token count and page numbers.

---

## 5. Grounded RAG & Question Answering (`/rag`)

### 5.1 Evidence-Grounded Query
* **Method & Path:** `POST /api/v1/rag/query`
* **Request Body:**
```json
{
  "query": "Has this patient experienced adverse reactions or contraindications to ACE inhibitors?",
  "patient_id": "3c90f235-5a8e-4a6c-947b-7b0b6c52a0a2",
  "top_k": 5
}
```
* **Response (200 OK):**
```json
{
  "answer": "Documented facial angioedema was observed on 2021-04-12 following Lisinopril administration [Doc: 9b1deb4d, Page 3]. However, a subsequent clinic note from 2023-01-15 lists Lisinopril under active medications without allergy notation [Doc: a4c810ef, Page 1].",
  "citations": [
    {
      "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "document_title": "Discharge_Summary_2021.pdf",
      "page_number": 3,
      "exact_quote": "Patient developed severe facial angioedema within 48 hours of starting Lisinopril 10mg.",
      "claim_text": "Documented facial angioedema was observed on 2021-04-12 following Lisinopril administration",
      "verification_status": "supported"
    }
  ],
  "limitations": [
    "Potential historical contradiction detected between 2021 discharge and 2023 clinic notes."
  ],
  "confidence_score": 0.94,
  "retrieval_metadata": {
    "dense_candidates_count": 20,
    "sparse_candidates_count": 20,
    "merged_candidates_count": 5,
    "total_latency_ms": 340
  }
}
```

### 5.2 User Feedback on Response
* **Method & Path:** `POST /api/v1/rag/feedback`
* **Request Body:**
```json
{
  "message_id": "8a7b6c5d-4e3f-2a1b-0c9d-8e7f6a5b4c3d",
  "rating": "negative",
  "issue_type": "contradiction_unnoticed",
  "comment": "Missed note about lisinopril allergy."
}
```
* **Response (201 Created):** `{ "status": "FEEDBACK_LOGGED" }`

---

## 6. Medical Research Intelligence (`/research`)

### 6.1 Evidence Comparison Matrix
* **Method & Path:** `POST /api/v1/research/compare`
* **Request Body:**
```json
{
  "study_ids": [
    "f1e2d3c4-0000-1111-2222-333344445555",
    "a1b2c3d4-5555-6666-7777-888899990000"
  ]
}
```
* **Response (200 OK):**
```json
[
  {
    "study_id": "f1e2d3c4-0000-1111-2222-333344445555",
    "title": "Empagliflozin in Heart Failure with a Preserved Ejection Fraction (EMPEROR-Preserved)",
    "publication_date": "2021-08-27",
    "sample_size": 5988,
    "population": "Adults with NYHA class II-IV heart failure and EF > 40%",
    "intervention": "Empagliflozin 10 mg once daily vs. placebo",
    "primary_outcome": "Composite of cardiovascular death or hospitalization for heart failure (HR 0.79; 95% CI 0.69-0.90)",
    "limitations": "Underrepresentation of non-white populations; secondary outcomes on renal decline did not achieve statistical significance."
  }
]
```

---

## 7. Bounded Agent Workflows (`/agents`)

### 7.1 Submit Agent Research Task
* **Method & Path:** `POST /api/v1/agents/tasks`
* **Request Body:**
```json
{
  "task_type": "PATIENT_RECONCILIATION",
  "patient_id": "3c90f235-5a8e-4a6c-947b-7b0b6c52a0a2",
  "prompt": "Synthesize oncology treatment history and flag prior cardiotoxicity signals."
}
```
* **Response (202 Accepted):**
```json
{
  "task_id": "11223344-5566-7788-9900-aabbccddeeff",
  "status": "RUNNING",
  "current_step": "Planning sub-queries",
  "iteration_count": 1
}
```

### 7.2 Human-in-the-Loop Approval Gate
* **Method & Path:** `POST /api/v1/agents/tasks/{id}/approve`
* **Request Body:** `{ "decision": "APPROVED", "reviewer_notes": "Reviewed and confirmed." }`
* **Response (200 OK):** Finalized synthesized dossier with download URI.

---

## 8. Health, Metrics & Audit (`/health`, `/metrics`, `/audit`)
* `GET /api/v1/health` — Returns status of Postgres, Qdrant, and storage subsystem.
* `GET /api/v1/metrics` — Prometheus metrics (latency histograms, token counters).
* `GET /api/v1/audit/logs` — *(Admin only)* Queryable audit trail with date/action filters.
