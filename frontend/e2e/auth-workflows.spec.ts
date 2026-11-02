import { test, expect } from '@playwright/test';

test.describe('Workflow A: Authentication, Persona Selection & Role Boundaries', () => {
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
              key: 'doctor',
              name: 'Dr. Marcus Vance, MD',
              title: 'Chief Medical Officer',
              email: 'marcus.vance@saint-jude-health.org',
              role: 'doctor',
              department: 'Endocrinology & Internal Medicine',
              description: 'Attending physician with patient record and RAG question answering access.',
              avatar_initials: 'MV',
            },
            {
              key: 'nurse',
              name: 'Nurse Sarah Jenkins, RN',
              title: 'Clinical Care Coordinator',
              email: 'sarah.jenkins@saint-jude-health.org',
              role: 'nurse',
              department: 'Inpatient Care Coordination',
              description: 'Care coordinator reviewing medical history timelines and conflicting notes.',
              avatar_initials: 'SJ',
            },
            {
              key: 'hospital_admin',
              name: 'Director Harold Finch, FACHE',
              title: 'VP of Hospital Operations',
              email: 'harold.finch@saint-jude-health.org',
              role: 'hospital_admin',
              department: 'Hospital Administration',
              description: 'Facility oversight suite for patient census and ingestion monitoring.',
              avatar_initials: 'HF',
            },
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
            {
              key: 'admin',
              name: 'Root Administrator',
              title: 'Chief Information Security Officer',
              email: 'admin@saint-jude-health.org',
              role: 'admin',
              department: 'Health Informatics & Security',
              description: 'Full administrative access to audit logs, QA testing, and system telemetry.',
              avatar_initials: 'RA',
            },
          ],
        }),
      });
    });

    // Intercept demo login
    await page.route('**/api/v1/auth/demo-login', async (route) => {
      const body = JSON.parse(route.request().postData() || '{}');
      const roleKey = body.role_key || 'doctor';
      const roleMap: Record<string, { name: string; role: string; email: string }> = {
        doctor: { name: 'Dr. Marcus Vance, MD', role: 'doctor', email: 'marcus.vance@saint-jude-health.org' },
        nurse: { name: 'Nurse Sarah Jenkins, RN', role: 'nurse', email: 'sarah.jenkins@saint-jude-health.org' },
        hospital_admin: { name: 'Director Harold Finch, FACHE', role: 'hospital_admin', email: 'harold.finch@saint-jude-health.org' },
        patient: { name: 'Eleanor Vance', role: 'patient', email: 'eleanor.vance@patientmail.org' },
        admin: { name: 'Root Administrator', role: 'admin', email: 'admin@saint-jude-health.org' },
      };
      const persona = roleMap[roleKey] || roleMap.doctor;

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: `mock-token-${roleKey}`,
          refresh_token: `mock-refresh-${roleKey}`,
          token_type: 'bearer',
          expires_in: 3600,
          user: {
            id: `usr-${roleKey}`,
            email: persona.email,
            full_name: persona.name,
            role: persona.role,
            is_active: true,
            created_at: '2026-01-01T00:00:00Z',
          },
        }),
      });
    });

    // Intercept patients list
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
            document_count: 3,
          },
        ]),
      });
    });

    // Intercept documents
    await page.route('**/api/v1/documents*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'doc-1',
            patient_id: 'pat-10001',
            title: 'Discharge_Summary_2026.pdf',
            file_size_bytes: 102400,
            file_hash_sha256: 'abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
            mime_type: 'application/pdf',
            doc_type: 'discharge_summary',
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

  test('User can select Doctor persona and navigate to clinical tabs', async ({ page }) => {
    await page.goto('/');

    // Look for Doctor role button on demo landing page
    const doctorCard = page.locator('h3:has-text("Doctor")').first();
    await expect(doctorCard).toBeVisible();
    await doctorCard.click();

    // Verify authenticated session banner appears
    await expect(page.locator('text=Role: Doctor').first()).toBeVisible();
    await expect(page.locator('text=Ask About Records').first()).toBeVisible();
    await expect(page.locator('text=Medical History Timeline').first()).toBeVisible();
  });

  test('User can sign out cleanly and return to public landing page', async ({ page }) => {
    await page.goto('/');

    const doctorCard = page.locator('h3:has-text("Doctor")').first();
    await doctorCard.click();

    const signOutBtn = page.locator('button:has-text("Sign Out")').first();
    await expect(signOutBtn).toBeVisible();
    await signOutBtn.click();

    // Verify returned to public demo selector
    await expect(page.locator('h3:has-text("Doctor")').first()).toBeVisible();
  });
});
