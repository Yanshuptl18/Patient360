import { test, expect } from '@playwright/test';

test.describe('Workflow D: Agentic Research Investigation & Clinician Approval Gate', () => {
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

    let isApproved = false;

    // Intercept agent runs list
    await page.route('**/api/v1/agents/patients/pat-10001/runs', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            run_id: 'run-playwright-1',
            patient_id: 'pat-10001',
            query: 'Reconcile longitudinal glycemic metrics and contraindications',
            status: isApproved ? 'completed' : 'awaiting_approval',
            iteration_count: 3,
            max_iterations: 5,
            elapsed_seconds: 3.5,
            plan: ['Retrieve labs', 'Evaluate contraindications'],
            steps: [
              {
                step_index: 1,
                node_name: 'retrieve_longitudinal_evidence',
                thought: 'Scanned 12 medical document chunks; baseline HbA1c is 7.8%.',
                duration_seconds: 1.1,
              },
            ],
            retrieved_evidence_count: 6,
            contradictions_found: [],
            draft_synthesis: 'Patient shows stable glycemic control. No renal contraindications identified.',
            final_report: isApproved ? 'Clinician Approved Synthesis: Report finalized by Dr. Marcus Vance.' : null,
            approval_status: isApproved ? 'approved' : 'pending',
            created_at: '2026-11-02T12:00:00Z',
            updated_at: '2026-11-02T12:01:00Z',
          },
        ]),
      });
    });

    // Intercept agent review
    await page.route('**/api/v1/agents/runs/run-playwright-1/review', async (route) => {
      isApproved = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'approved', message: 'Review successfully recorded.' }),
      });
    });

    await page.route('**/api/v1/agents/runs/run-playwright-1', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          run_id: 'run-playwright-1',
          patient_id: 'pat-10001',
          query: 'Reconcile longitudinal glycemic metrics and contraindications',
          status: isApproved ? 'completed' : 'awaiting_approval',
          iteration_count: 3,
          max_iterations: 5,
          elapsed_seconds: 3.5,
          plan: ['Retrieve labs', 'Evaluate contraindications'],
          steps: [],
          retrieved_evidence_count: 6,
          contradictions_found: [],
          draft_synthesis: 'Patient shows stable glycemic control. No renal contraindications identified.',
          final_report: isApproved ? 'Clinician Approved Synthesis: Report finalized by Dr. Marcus Vance.' : null,
          approval_status: isApproved ? 'approved' : 'pending',
          created_at: '2026-11-02T12:00:00Z',
          updated_at: '2026-11-02T12:01:00Z',
        }),
      });
    });
  });

  test('Doctor opens research assistant, inspects review gate, and approves report', async ({ page }) => {
    await page.goto('/');

    const doctorCard = page.locator('h3:has-text("Doctor")').first();
    await doctorCard.click();

    // Click on Clinical Research Assistant tab
    const agentTab = page.locator('button:has-text("Clinical Research Assistant")').first();
    await agentTab.click();

    // Verify Review and Approve Findings gate is rendered
    await expect(page.locator('text=Review and Approve Findings').first()).toBeVisible();
    await expect(page.locator('text=Approve and Finalize Report').first()).toBeVisible();

    // Click Approve
    const approveBtn = page.locator('button:has-text("Approve and Finalize Report")').first();
    await approveBtn.click();

    // Verify status changes to finalized
    await expect(page.locator('text=Approved Clinical Evidence Report Finalized').first()).toBeVisible();
  });
});
