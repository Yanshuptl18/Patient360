import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { OperationalDashboard } from '../features/admin/OperationalDashboard';
import { AuthProvider } from '../features/auth/AuthContext';
import * as AuthContextModule from '../features/auth/AuthContext';
import api from '../services/api';
import { Patient, Document, AuditLogItem } from '../types';

const mockPatients: Patient[] = [
  {
    id: 'pat-1',
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
  {
    id: 'pat-2',
    mrn_synthetic: 'SYNTH-10002',
    first_name: 'Arthur',
    last_name: 'Pendleton',
    date_of_birth: '1968-03-24',
    gender: 'Male',
    primary_condition: 'Coronary Artery Disease',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    document_count: 4,
  },
];

const mockFacilityDocs: Document[] = [
  {
    id: 'doc-1',
    patient_id: 'pat-1',
    title: 'Eleanor_Discharge_Summary.pdf',
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
  {
    id: 'doc-2',
    patient_id: 'pat-2',
    title: 'Arthur_Coronary_Angiogram.pdf',
    file_size_bytes: 204800,
    file_hash_sha256: '123456abcdef7890123456abcdef7890123456abcdef7890123456abcdef7890',
    mime_type: 'application/pdf',
    doc_type: 'lab_report',
    doc_date: '2026-01-12',
    ingestion_status: 'failed',
    version: 1,
    created_at: '2026-01-12T10:00:00Z',
    updated_at: '2026-01-12T10:00:00Z',
  },
];

const mockAuditLogs: AuditLogItem[] = [
  {
    id: 'log-1',
    user_id: 'usr-admin-1',
    action: 'DEMO_LOGIN_SUCCESS',
    resource_type: 'auth',
    resource_id: 'usr-admin-1',
    patient_id: null,
    ip_address: '127.0.0.1',
    status: 'SUCCESS',
    created_at: '2026-11-02T10:00:00Z',
  },
  {
    id: 'log-2',
    user_id: 'usr-doc-1',
    action: 'EHR_ACCESSED',
    resource_type: 'patient',
    resource_id: 'pat-1',
    patient_id: 'pat-1',
    ip_address: '192.168.1.50',
    status: 'SUCCESS',
    created_at: '2026-11-02T10:05:00Z',
  },
];

describe('Hospital Operational Dashboard Integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks();

    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 'usr-admin',
        email: 'director@saint-jude-health.org',
        full_name: 'Director Finch',
        role: 'hospital_admin',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
      },
      token: 'mock-token',
      isAuthenticated: true,
      demoMode: true,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshAuth: vi.fn(),
    } as any);

    (globalThis as any).fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/patients')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockPatients),
        });
      }
      if (url.includes('/api/v1/documents')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockFacilityDocs),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      });
    });

    vi.spyOn(api.documents, 'list').mockResolvedValue(mockFacilityDocs);
    vi.spyOn(api.documents, 'recover').mockResolvedValue({
      document_id: 'doc-2',
      status: 'completed',
      chunk_count: 8,
      total_tokens: 1540,
      pages_processed: 3,
      message: 'Document successfully re-indexed into Qdrant.',
    });
    vi.spyOn(api.audit, 'listLogs').mockResolvedValue(mockAuditLogs);
  });

  it('renders operational metrics including exact census count and document count', async () => {
    render(
      <AuthProvider>
        <OperationalDashboard />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getAllByText('Hospital Operational Oversight').length).toBeGreaterThan(0);
    });

    // Active census is 2
    expect(screen.getByText('2')).toBeDefined();
    // Total documents is 3 + 4 = 7
    expect(screen.getByText('7')).toBeDefined();
    expect(screen.getByText('Eleanor Vance')).toBeDefined();
    expect(screen.getByText('Arthur Pendleton')).toBeDefined();
  });

  it('switches to Ingestion Monitoring tab and executes document recovery', async () => {
    render(
      <AuthProvider>
        <OperationalDashboard />
      </AuthProvider>
    );

    const ingestionBtn = screen.getAllByText('Ingestion Monitoring')[0];
    fireEvent.click(ingestionBtn);

    await waitFor(() => {
      expect(screen.getByText('Document Ingestion Monitoring & Recovery')).toBeDefined();
    });

    expect(screen.getByText('Eleanor_Discharge_Summary.pdf')).toBeDefined();
    expect(screen.getByText('Arthur_Coronary_Angiogram.pdf')).toBeDefined();

    // Click Recover on Arthur's document
    const recoverButtons = screen.getAllByText('Recover');
    expect(recoverButtons.length).toBeGreaterThan(0);
    fireEvent.click(recoverButtons[1]);

    await waitFor(() => {
      expect(api.documents.recover).toHaveBeenCalledWith('doc-2');
      expect(screen.getByText(/Document successfully recovered: 8 chunks indexed/)).toBeDefined();
    });
  });

  it('switches to Security Audit Trail and filters security events', async () => {
    render(
      <AuthProvider>
        <OperationalDashboard />
      </AuthProvider>
    );

    const securityBtn = screen.getAllByText('Security Audit Trail')[0];
    fireEvent.click(securityBtn);

    await waitFor(() => {
      expect(screen.getByText('Security & Clinical Access Audit Trail')).toBeDefined();
    });

    expect(screen.getByText('DEMO_LOGIN_SUCCESS')).toBeDefined();
    expect(screen.getByText('EHR_ACCESSED')).toBeDefined();
  });
});