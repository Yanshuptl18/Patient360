import { test, expect } from '@playwright/test';

test.describe('Workflow B: Document Ingestion, Status Tracking & Chunk Inspection', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    // Intercept health check
    await page.route('**/api/v1/health', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'HEALTHY',
          environment: 'testing',
          version: '1.0.0',
          uptime_seconds: 1200,
          timestamp: new Date().toISOString(),
          components: {
            database: { status: 'UP', latency_ms: 1, message: 'Ready' },
            vector_store: { status: 'UP', latency_ms: 1, message: 'Ready' },
            storage: { status: 'UP', latency_ms: 1, message: 'Ready' },
            llm_provider: { status: 'UP', latency_ms: 5, message: 'Ready' },
          },
        }),
      });
    });

    // Intercept demo roles and login
    await page.route('**/api/v1/auth/demo-roles', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          demo_mode: true,
          roles: [
            {
              key: 'doctor',
              name: 'Dr. Marcus Vance, MD',
              title: 'Chief Medical Officer',
              email: 'marcus.vance@saint-jude-health.org',
              role: 'doctor',
              department: 'Endocrinology & Internal Medicine',
              description: 'Attending physician.',
              avatar_initials: 'MV',
            },
          ],
        }),
      });
    });

    await page.route('**/api/v1/auth/demo-login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-doctor-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'bearer',
          expires_in: 3600,
          user: {
            id: 'usr-doctor',
            email: 'marcus.vance@saint-jude-health.org',
            full_name: 'Dr. Marcus Vance, MD',
            role: 'doctor',
            is_active: true,
            created_at: '2026-01-01T00:00:00Z',
          },
        }),
      });
    });

    // Intercept patient
    await page.route('**/api/v1/patients', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'pat-10001',
            mrn_synthetic: 'SYNTH-10001',
            first_name: 'Eleanor',
            last_name: 'Vance',
            date_of_birth: '1974-06-12',
            gender: 'Female',
            primary_condition: 'Type 2 Diabetes Mellitus',
            created_at: '2026-01-01T00:00:00Z',
            updated_at: '2026-01-01T00:00:00Z',
            document_count: 1,
          },
        ]),
      });
    });

    // Intercept documents
    await page.route('**/api/v1/documents?patient_id=pat-10001', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'doc-101',
            patient_id: 'pat-10001',
            title: 'Endocrine_Clinical_Summary_2026.pdf',
            file_size_bytes: 145000,
            file_hash_sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
            mime_type: 'application/pdf',
            doc_type: 'discharge_summary',
            doc_date: '2026-01-15',
            ingestion_status: 'completed',
            version: 1,
            created_at: '2026-01-15T10:00:00Z',
            updated_at: '2026-01-15T10:00:00Z',
          },
        ]),
      });
    });

    // Intercept document chunks
    await page.route('**/api/v1/documents/doc-101/chunks', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'chk-1',
            document_id: 'doc-101',
            chunk_index: 0,
            page_number: 1,
            content: 'History of Present Illness: Eleanor Vance is a 51-year-old female with Type 2 Diabetes Mellitus.',
            raw_content: 'History of Present Illness: Eleanor Vance is a 51-year-old female with Type 2 Diabetes Mellitus.',
            token_count: 24,
            metadata_json: { section: 'HPI' },
            created_at: '2026-01-15T10:00:00Z',
          },
          {
            id: 'chk-2',
            document_id: 'doc-101',
            chunk_index: 1,
            page_number: 2,
            content: 'Discharge Medications: Metformin 500mg PO BID with meals. Lisinopril 10mg PO QD.',
            raw_content: 'Discharge Medications: Metformin 500mg PO BID with meals. Lisinopril 10mg PO QD.',
            token_count: 22,
            metadata_json: { section: 'Medications' },
            created_at: '2026-01-15T10:00:00Z',
          },
        ]),
      });
    });
  });

  test('Inspect attached document metadata and explore physical page chunks', async ({ page }) => {
    await page.goto('/');

    // Log in as Doctor
    const doctorCard = page.locator('h3:has-text("Doctor")').first();
    await doctorCard.click();

    // Verify document list displays attached record
    await expect(page.locator('text=Endocrine_Clinical_Summary_2026.pdf').first()).toBeVisible();
    await expect(page.locator('text=Examined and Ready').first()).toBeVisible();

    // Click on Inspect Extracted Evidence button
    const inspectBtn = page.locator('button[title*="Inspect" i], button:has-text("Inspect")').first();
    await expect(inspectBtn).toBeVisible();
    await inspectBtn.click();
    await expect(page.locator('text=Eleanor Vance is a 51-year-old female').first()).toBeVisible();
  });
});
