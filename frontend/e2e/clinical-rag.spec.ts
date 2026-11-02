import { test, expect } from '@playwright/test';

test.describe('Workflow C: Evidence-Grounded Clinical RAG, Citations & Abstention', () => {
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
    await page.route('**/api/v1/patients*', async (route) => {
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
            document_count: 2,
          },
        ]),
      });
    });

    await page.route('**/api/v1/documents*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    // Intercept RAG queries
    await page.route('**/api/v1/rag/query', async (route) => {
      const body = JSON.parse(route.request().postData() || '{}');
      const query = (body.query || '').toLowerCase();

      if (query.includes('unrecorded') || query.includes('unknown') || query.includes('appendectomy')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            query: body.query,
            patient_id: body.patient_id || 'pat-10001',
            answer: 'This information is not documented in the authorized medical records for this patient.',
            citations: [],
            limitations: ['Absence of surgical records in dossier'],
            confidence_score: 0.0,
            retrieval_metadata: {
              dense_candidates_count: 0,
              sparse_candidates_count: 0,
              merged_candidates_count: 0,
              retrieval_latency_ms: 45,
              generation_latency_ms: 75,
              total_latency_ms: 120,
              is_abstention: true,
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            query: body.query,
            patient_id: body.patient_id || 'pat-10001',
            answer: 'According to the Discharge Summary dated January 10, 2026, Eleanor Vance is prescribed Metformin 500mg PO BID with meals [Discharge_Summary_2026.pdf, page 2].',
            citations: [
              {
                document_id: 'doc-101',
                document_title: 'Discharge_Summary_2026.pdf',
                page_number: 2,
                exact_quote: 'Discharge Medications: Metformin 500mg PO BID with meals.',
                claim_text: 'Metformin 500mg PO BID with meals',
                verification_status: 'supported',
              },
            ],
            limitations: [],
            confidence_score: 0.96,
            retrieval_metadata: {
              dense_candidates_count: 5,
              sparse_candidates_count: 5,
              merged_candidates_count: 5,
              retrieval_latency_ms: 85,
              generation_latency_ms: 155,
              total_latency_ms: 240,
              is_abstention: false,
            },
          }),
        });
      }
    });
  });

  test('Doctor asks clinical question, receives grounded answer with physical page citation', async ({ page }) => {
    await page.goto('/');

    // Login as Doctor
    const doctorCard = page.locator('h3:has-text("Doctor")').first();
    await doctorCard.click();

    // Navigate to Ask About Records tab
    const ragTab = page.locator('button:has-text("Ask About Records")').first();
    await ragTab.click();

    // Type query
    const queryInput = page.locator('input[placeholder*="Ask about this patient"]').first();
    await expect(queryInput).toBeVisible();
    await queryInput.fill('What is the current dosage of Metformin?');
    const submitBtn = page.locator('button[type="submit"]:has-text("Ask")').first();
    await submitBtn.click();

    // Expect grounded answer and citation
    await expect(page.locator('text=Discharge_Summary_2026.pdf').first()).toBeVisible();
    await expect(page.locator('text=/page 2/i').first()).toBeVisible();
  });

  test('System abstains honestly when queried for unrecorded clinical information', async ({ page }) => {
    await page.goto('/');

    const doctorCard = page.locator('h3:has-text("Doctor")').first();
    await doctorCard.click();

    const ragTab = page.locator('button:has-text("Ask About Records")').first();
    await ragTab.click();

    const queryInput = page.locator('input[placeholder*="Ask about this patient"]').first();
    await expect(queryInput).toBeVisible();
    await queryInput.fill('When was the patient appendectomy performed? (unrecorded)');
    const submitBtn = page.locator('button[type="submit"]:has-text("Ask")').first();
    await submitBtn.click();

    await expect(page.locator('text=not documented in the authorized medical records').first()).toBeVisible();
  });
});
