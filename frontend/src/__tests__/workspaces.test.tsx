import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { App } from '../App';
import * as AuthContextModule from '../features/auth/AuthContext';
import { Patient, User, Document } from '../types';

const mockPatient: Patient = {
  id: 'pat-10001',
  mrn_synthetic: 'SYNTH-10001',
  first_name: 'Eleanor',
  last_name: 'Vance',
  date_of_birth: '1974-06-12',
  gender: 'Female',
  primary_condition: 'Type 2 Diabetes Mellitus',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  document_count: 5,
};

const mockDocs: Document[] = [
  {
    id: 'doc-1',
    patient_id: 'pat-10001',
    title: 'Discharge_Summary_2026.pdf',
    file_size_bytes: 102400,
    mime_type: 'application/pdf',
    doc_type: 'discharge_summary',
    doc_date: '2026-01-10',
    ingestion_status: 'completed',
    version: 1,
    created_at: '2026-01-10T10:00:00Z',
    updated_at: '2026-01-10T10:00:00Z',
  },
];

describe('Five Role-Based Workspaces End-to-End Rendering', () => {
  beforeEach(() => {
    vi.restoreAllMocks();

    // Mock global fetch
    (globalThis as any).fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/patients')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([mockPatient]),
        });
      }
      if (url.includes('/api/v1/documents')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockDocs),
        });
      }
      if (url.includes('/api/v1/health')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              status: 'HEALTHY',
              environment: 'testing',
              version: '1.0.0',
              uptime_seconds: 3600,
              timestamp: '2026-11-02T12:00:00Z',
              components: {
                database: { status: 'UP', latency_ms: 2, message: 'Ready' },
                vector_store: { status: 'UP', latency_ms: 3, message: 'Ready' },
                storage: { status: 'UP', latency_ms: 1, message: 'Ready' },
                llm_provider: { status: 'UP', latency_ms: 10, message: 'Ready' },
              },
            }),
        });
      }
      if (url.includes('/api/v1/auth/audit-logs')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });
  });

  const setupAuthMock = (role: string, fullName: string, email: string) => {
    const user: User = {
      id: `usr-${role}`,
      email,
      full_name: fullName,
      role: role as any,
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    };

    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user,
      token: 'mock-jwt-token-xyz',
      isAuthenticated: true,
      demoMode: true,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshAuth: vi.fn(),
    } as any);
  };

  it('1. Doctor Workspace: renders patient records, ask about records, and clinical research tabs', async () => {
    setupAuthMock('doctor', 'Dr. Marcus Vance, MD', 'marcus.vance@saint-jude-health.org');

    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('Dr. Marcus Vance, MD').length).toBeGreaterThan(0);
    });

    expect(screen.getByText('Ask About Records')).toBeDefined();
    expect(screen.getByText('Medical History Timeline')).toBeDefined();
    expect(screen.getByText('Clinical Research Assistant')).toBeDefined();
    expect(screen.getByText('Biomedical Studies')).toBeDefined();
  });

  it('2. Nurse Workspace: renders care coordination, patient summary, medications, and allergies', async () => {
    setupAuthMock('nurse', 'Nurse Sarah Jenkins, RN', 'sarah.jenkins@saint-jude-health.org');

    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('Nurse Sarah Jenkins, RN').length).toBeGreaterThan(0);
    });

    expect(screen.getAllByText('Care Coordination and Patient Monitoring').length).toBeGreaterThan(0);
    expect(screen.getByText('Patient Summary & Alerts')).toBeDefined();
    expect(screen.getByText('Current Medication Regimen')).toBeDefined();
    expect(screen.getByText('Documented Allergies & Sensitivities')).toBeDefined();
    expect(screen.getByText('Metformin HCl')).toBeDefined();
  });

  it('3. Hospital Admin Workspace: renders Operational Oversight suite, census roster, and security metrics', async () => {
    setupAuthMock('hospital_admin', 'Director Harold Finch, FACHE', 'harold.finch@saint-jude-health.org');

    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('Director Harold Finch, FACHE').length).toBeGreaterThan(0);
    });

    expect(screen.getAllByText('Hospital Operational Oversight').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Operations Overview').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Ingestion Monitoring').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Security Audit Trail').length).toBeGreaterThan(0);
  });

  it('4. Patient Portal Workspace: renders strictly isolated Eleanor Vance records', async () => {
    setupAuthMock('patient', 'Eleanor Vance', 'eleanor.vance@patientmail.org');

    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('Eleanor Vance').length).toBeGreaterThan(0);
    });

    expect(screen.getByText('Record ID: SYNTH-10001')).toBeDefined();
    expect(screen.getByText('Type 2 Diabetes Mellitus')).toBeDefined();
  });

  it('5. System Admin Workspace: renders System Admin Monitor, telemetry, and operational suite controls', async () => {
    setupAuthMock('admin', 'Root Administrator', 'admin@saint-jude-health.org');

    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('Root Administrator').length).toBeGreaterThan(0);
    });

    expect(screen.getAllByText('System Admin Monitor').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Database: PostgreSQL (Ready)').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Vector Store: Qdrant (Ready)').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Open Full Operational Suite').length).toBeGreaterThan(0);
  });
});