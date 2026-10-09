# Patient360: Automated Testing Strategy

## 1. Testing Pyramid & Principles

Patient360 follows a disciplined multi-tier automated testing strategy:
1. **Zero Flakiness:** All CI/CD test suites run against deterministic fixtures without relying on external third-party API availability.
2. **Offline Mocking:** A high-fidelity `MockLLMProvider` is provided so the entire test suite executes offline with zero API keys or external costs.
3. **Comprehensive Coverage:** Target $> 80\%$ test coverage across all business logic, ingestion pipelines, and retrieval services.

```
                      ┌─────────────────────────┐
                      │    E2E / Workflow Tests │
                      │  (Full Q&A, Agent Flow) │
                      ├─────────────────────────┤
                      │    Security & Isolation │
                      │   (RBAC, Cross-Patient) │
                      ├─────────────────────────┤
                      │    Integration Tests    │
                      │  (FastAPI, DB, Qdrant)  │
                      ├─────────────────────────┤
                      │        Unit Tests       │
                      │ (Chunker, RRF, Citations)
                      └─────────────────────────┘
```

---

## 2. Test Tiers and Responsibilities

### 2.1 Unit Tests (`tests/unit/`)
* **Chunking & Parsing:** Verify that PyMuPDF extracts accurate page numbers and semantic chunker respects 512-token limits with 64-token overlap.
* **Text Normalization:** Assert that clinical decimals (`0.5 mg`) and units (`mg/dL`) are preserved.
* **Retrieval Fusion:** Verify mathematical correctness of the Reciprocal Rank Fusion algorithm against controlled rank lists.
* **Citation Parser:** Verify regex extraction of `[Doc: X, Page Y]` tags across edge cases (multiple citations, malformed brackets).
* **Security & Tokens:** Verify Argon2 password hashing and JWT token creation/expiry.

### 2.2 Integration Tests (`tests/integration/`)
* **API Endpoints:** Exercise FastAPI endpoints using `httpx.AsyncClient` / `TestClient`.
* **Database & Migrations:** Verify Alembic schema migrations execute up and down without errors on PostgreSQL.
* **Vector Store Isolation:** Insert chunks for Patient A and Patient B into Qdrant; assert that queries for Patient A return zero chunks from Patient B.
* **Document Ingestion:** Upload synthetic PDFs; assert that chunks, metadata, and status records are accurately written to PostgreSQL and Qdrant.

### 2.3 Security & Isolation Tests (`tests/security/`)
* **Cross-Tenant Access:** Attempt to read or query documents using tokens from an unassigned reviewer; assert HTTP 403 Forbidden.
* **Expired / Forged JWTs:** Submit requests with expired or tampered signatures; assert HTTP 401 Unauthorized.
* **Adversarial Prompt Injection:** Ingest PDFs containing prompt override commands; assert that system instructions take precedence and no command execution occurs.
* **Audit Logging:** Execute CRUD operations; assert that corresponding sanitized audit log entries are generated.

### 2.4 End-to-End & Workflow Tests (`tests/e2e/`)
* **Grounded Q&A Journey:** Complete flow from upload, ingestion, query, to verified citation output.
* **Agentic State Machine:** Execute research workflow; assert that execution halts at 5 iterations if unresolved and respects human approval gates.

---

## 3. Static Analysis and Quality Gates

Every phase must pass static checks before being marked complete:
* **Python Code Quality:**
  * Linter & Formatter: `ruff check .` and `ruff format --check .`
  * Strict Type Checking: `mypy --strict backend/`
* **Frontend Code Quality:**
  * Linter: `npm run lint` (ESLint)
  * Strict Type Checking: `npm run type-check` (`tsc --noEmit`)
* **Dependency Safety:**
  * Automated vulnerability audit: `pip-audit` / `npm audit`
