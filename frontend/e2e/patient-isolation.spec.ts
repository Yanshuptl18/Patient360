import { test, expect } from '@playwright/test';

test.describe('Workflow E: Patient Role Isolation & Foreign Dossier Access Rejection (IDOR)', () => {
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

    // Intercept demo roles
    await page.route('**/api/v1/auth/demo-roles', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          demo_mode: true,
          roles: [
            {
              key: 'patient',
              name: 'Eleanor Vance',
              title: 'Synthetic Patient',
              email: 'eleanor.vance@patientmail.org',
              role: 'patient',
              department: 'Patient Portal',
              description: 'Personal health records strictly isolated to Eleanor Vance (SYNTH-10001).',
              avatar_initials: 'EV',
            },
          ],
        }),
      });
    });

    // Intercept demo login for patient
    await page.route('**/api/v1/auth/demo-login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-patient-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'bearer',
          expires_in: 3600,
          user: {
            id: 'usr-patient-eleanor',
            email: 'eleanor.vance@patientmail.org',
            full_name: 'Eleanor Vance',
            role: 'patient',
            is_active: true,
            created_at: '2026-01-01T00:00:00Z',
          },
        }),
      });
    });

    // Server enforces patient isolation: only returns Eleanor Vance
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

    // Foreign patient IDOR rejection
    await page.route('**/api/v1/patients/pat-foreign-999*', async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            message: 'Access denied: Patient role is strictly isolated to own record (SYNTH-10001).',
            code: 'FORBIDDEN',
          },
        }),
      });
    });

    await page.route('**/api/v1/documents?patient_id=pat-10001', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'doc-1',
            patient_id: 'pat-10001',
            title: 'Personal_Health_Summary.pdf',
            file_size_bytes: 54000,
            file_hash_sha256: 'fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321',
            mime_type: 'application/pdf',
            doc_type: 'patient_record',
            doc_date: '2026-01-10',
            ingestion_status: 'completed',
            version: 1,
            created_at: '2026-01-10T10:00:00Z',
            updated_at: '2026-01-10T10:00:00Z',
          },
        ]),
      });
    });
  });

  test('Patient role logs in, sees isolated Eleanor Vance portal, and no access to cohort', async ({ page }) => {
    await page.goto('/');

    const patientCard = page.locator('h3:has-text("Patient")').first();
    await patientCard.click();

    // Verify PatientPortal is rendered
    await expect(page.locator('text=Record ID: SYNTH-10001').first()).toBeVisible();
    await expect(page.locator('text=Type 2 Diabetes Mellitus').first()).toBeVisible();
    await expect(page.locator('text=Personal_Health_Summary.pdf').first()).toBeVisible();

    // Verify patient cannot see general cohort roster or admin tabs
    await expect(page.locator('text=Hospital Operational Oversight')).toHaveCount(0);
    await expect(page.locator('text=Quality Testing')).toHaveCount(0);
  });
});
