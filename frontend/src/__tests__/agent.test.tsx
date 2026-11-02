import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, cleanup } from '@testing-library/react';
import { ClinicalAgentPanel } from '../features/agents/ClinicalAgentPanel';
import { AuthProvider } from '../features/auth/AuthContext';
import * as AuthContextModule from '../features/auth/AuthContext';
import { AgentRunSnapshot } from '../types';

const mockRunAwaitingApproval: AgentRunSnapshot = {
  run_id: 'run-998877',
  patient_id: 'pat-10001',
  patient_name: 'Eleanor Vance',
  query: 'Synthesize glycemic control and medication contraindications',
  status: 'awaiting_approval',
  iteration_count: 3,
  max_iterations: 5,
  elapsed_seconds: 4.2,
  plan: [
    'Retrieve longitudinal diabetes records',
    'Extract HbA1c trajectory and compare against target thresholds',
    'Verify contraindications against documented renal/cardiac history',
  ],
  steps: [
    {
      step_index: 1,
      node_name: 'retrieve_longitudinal_evidence',
      thought: 'Evidence indicates active pharmacological therapy for diabetes mellitus.',
      timestamp_iso: '2026-11-02T11:00:30Z',
    },
    {
      step_index: 2,
      node_name: 'evaluate_contraindications',
      thought: 'Safe to maintain current oral glycemic regimen.',
      timestamp_iso: '2026-11-02T11:00:45Z',
    },
  ],
  retrieved_evidence_count: 8,
  contradictions_found: [],
  draft_synthesis: 'Patient Eleanor Vance has demonstrated stable glycemic management on Metformin 500mg BID. No active renal contraindications detected.',
  approval_status: 'pending',
  created_at: '2026-11-02T11:00:00Z',
  updated_at: '2026-11-02T11:01:00Z',
};

const mockRunApproved: AgentRunSnapshot = {
  ...mockRunAwaitingApproval,
  status: 'completed',
  approval_status: 'approved',
  final_report: 'Finalized Clinical Synthesis: Glycemic management confirmed by Dr. Marcus Vance on 2026-11-02.',
  clinician_feedback: 'Approved as documented.',
};

describe('Clinical LangGraph Agentic Workflow Panel', () => {
  let currentRunSnapshot: AgentRunSnapshot;

  beforeEach(() => {
    vi.restoreAllMocks();
    currentRunSnapshot = { ...mockRunAwaitingApproval };

    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 'usr-1',
        email: 'doctor@saint-jude-health.org',
        full_name: 'Dr. Marcus Vance',
        role: 'doctor',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
      },
      token: 'mock-agent-token',
      isAuthenticated: true,
      demoMode: true,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshAuth: vi.fn(),
    } as any);

    (globalThis as any).fetch = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/api/v1/agents/patients/pat-10001/runs')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([currentRunSnapshot]),
        });
      }
      if (url.includes('/api/v1/agents/runs/run-998877/review') && init?.method === 'POST') {
        currentRunSnapshot = { ...mockRunApproved };
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'approved', message: 'Review recorded' }),
        });
      }
      if (url.includes('/api/v1/agents/runs/run-998877')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(currentRunSnapshot),
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

  it('renders research queries, input field, and past investigation runs', async () => {
    render(
      <AuthProvider>
        <ClinicalAgentPanel patientId="pat-10001" patientName="Eleanor Vance" />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/Clinical Research Assistant/).length).toBeGreaterThan(0);
    });

    // Preset query buttons
    expect(screen.getAllByText(/Synthesize glycemic control and medication contraindications/).length).toBeGreaterThan(0);
    expect(screen.getByPlaceholderText(/Describe your clinical research question/)).toBeDefined();

    // Renders active run
    await waitFor(() => {
      expect(screen.getByText('retrieve longitudinal evidence')).toBeDefined();
      expect(screen.getByText(/Patient Eleanor Vance has demonstrated stable glycemic management/)).toBeDefined();
    });
  });

  it('renders Clinician Human-in-the-Loop review gate when awaiting approval', async () => {
    render(
      <AuthProvider>
        <ClinicalAgentPanel patientId="pat-10001" patientName="Eleanor Vance" />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getAllByText('Review and Approve Findings').length).toBeGreaterThan(0);
    });

    // Verify approval actions
    expect(screen.getByText('Approve and Finalize Report')).toBeDefined();
    expect(screen.getByText('Reject Findings')).toBeDefined();
    expect(screen.getByPlaceholderText('Optional reviewer notes or comments...')).toBeDefined();
  });

  it('submits clinician approval and transitions to finalized status', async () => {
    render(
      <AuthProvider>
        <ClinicalAgentPanel patientId="pat-10001" patientName="Eleanor Vance" />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Approve and Finalize Report')).toBeDefined();
    });

    const approveButton = screen.getByText('Approve and Finalize Report');
    fireEvent.click(approveButton);

    await waitFor(() => {
      expect(screen.getByText(/Approved Clinical Evidence Report Finalized/)).toBeDefined();
    });
  });
});