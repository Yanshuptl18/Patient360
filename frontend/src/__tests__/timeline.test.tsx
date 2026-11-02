import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, cleanup } from '@testing-library/react';
import { ClinicalTimelinePanel } from '../features/timeline/ClinicalTimelinePanel';
import { AuthProvider } from '../features/auth/AuthContext';
import * as AuthContextModule from '../features/auth/AuthContext';
import { PatientTimelineResponse } from '../types';

const mockTimelineResponse: PatientTimelineResponse = {
  patient_id: 'pat-10001',
  patient_name: 'Eleanor Vance',
  summary: {
    total_events: 3,
    earliest_date: '2025-04-12',
    latest_date: '2026-01-15',
    total_contradictions: 1,
    event_counts_by_type: {
      diagnosis: 1,
      medication: 1,
      lab_result: 1,
      procedure: 0,
      encounter: 0,
      allergy: 0,
    },
  },
  contradictions: [
    {
      event_id_1: 'ev-1',
      event_id_2: 'ev-2',
      event_1_summary: 'Metformin started at 500mg daily on Jan 10',
      event_2_summary: 'Metformin recorded as 1000mg twice daily on Jan 12',
      document_title_1: 'Clinic_Note_Jan10.pdf',
      document_title_2: 'Discharge_Summary_Jan12.pdf',
      page_number_1: 2,
      page_number_2: 1,
      conflict_type: 'value_conflict',
      severity: 'critical',
      explanation: 'Conflicting dosage documented within 48 hours without titration note.',
    },
  ],
  events: [
    {
      id: 'ev-1',
      patient_id: 'pat-10001',
      document_id: 'doc-1',
      event_type: 'diagnosis',
      event_date: '2025-04-12',
      event_date_precision: 'day',
      description: 'Type 2 Diabetes Mellitus with elevated fasting glucose',
      clinical_status: 'active',
      confidence_score: 0.95,
      contradiction_flag: false,
      created_at: '2025-04-12T00:00:00Z',
      document_title: 'Endocrine_Initial_Eval.pdf',
      page_number: 1,
    },
    {
      id: 'ev-2',
      patient_id: 'pat-10001',
      document_id: 'doc-2',
      event_type: 'medication',
      event_date: '2026-01-10',
      event_date_precision: 'day',
      description: 'Prescribed Metformin 500mg PO BID',
      value_or_dosage: '500mg BID',
      clinical_status: 'active',
      confidence_score: 0.98,
      contradiction_flag: true,
      created_at: '2026-01-10T00:00:00Z',
      document_title: 'Discharge_Summary_Jan10.pdf',
      page_number: 3,
    },
    {
      id: 'ev-3',
      patient_id: 'pat-10001',
      document_id: 'doc-3',
      event_type: 'lab_result',
      event_date: '2026-01-15',
      event_date_precision: 'day',
      description: 'Hemoglobin A1c measured at 7.8%',
      value_or_dosage: '7.8 %',
      clinical_status: 'active',
      confidence_score: 0.99,
      contradiction_flag: false,
      created_at: '2026-01-15T00:00:00Z',
      document_title: 'Lab_Report_Jan15.pdf',
      page_number: 1,
    },
  ],
};

describe('Clinical Timeline and Contradiction Detection Panel', () => {
  beforeEach(() => {
    vi.restoreAllMocks();

    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 'usr-1',
        email: 'doctor@saint-jude-health.org',
        full_name: 'Dr. Marcus Vance',
        role: 'doctor',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
      },
      token: 'mock-token-xyz',
      isAuthenticated: true,
      demoMode: true,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshAuth: vi.fn(),
    } as any);

    (globalThis as any).fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/timeline/patients/pat-10001')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTimelineResponse),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });
  });

  afterEach(() => {
    cleanup();
  });

  it('loads and renders chronological medical history events and page citations', async () => {
    render(
      <AuthProvider>
        <ClinicalTimelinePanel patientId="pat-10001" patientName="Eleanor Vance" />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Type 2 Diabetes Mellitus with elevated fasting glucose')).toBeDefined();
    });

    expect(screen.getByText('Prescribed Metformin 500mg PO BID')).toBeDefined();
    expect(screen.getByText('Hemoglobin A1c measured at 7.8%')).toBeDefined();

    // Check page citations
    expect(screen.getByText(/Endocrine_Initial_Eval\.pdf/)).toBeDefined();
  });

  it('surfaces detected clinical contradictions with cross-document comparison', async () => {
    render(
      <AuthProvider>
        <ClinicalTimelinePanel patientId="pat-10001" patientName="Eleanor Vance" />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Conflicting Information Detected/)).toBeDefined();
    });

    expect(
      screen.getAllByText(/Conflicting dosage documented within 48 hours without titration note/).length
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Clinic_Note_Jan10\.pdf/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Discharge_Summary_Jan12\.pdf/).length).toBeGreaterThan(0);
  });

  it('filters timeline events by clinical category', async () => {
    render(
      <AuthProvider>
        <ClinicalTimelinePanel patientId="pat-10001" patientName="Eleanor Vance" />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/Prescribed Metformin 500mg PO BID/).length).toBeGreaterThan(0);
    });

    // Filter to Medications only by clicking the Medication filter button
    const medButton = screen.getAllByRole('button', { name: /medication/i })[0];
    fireEvent.click(medButton);

    await waitFor(() => {
      expect(screen.getAllByText(/Prescribed Metformin 500mg PO BID/).length).toBeGreaterThan(0);
      expect(screen.queryByText('Hemoglobin A1c measured at 7.8%')).toBeNull();
    });
  });
});