import React, { useState, useEffect, useCallback } from 'react';
import { Patient, Document, AuditLogItem } from '../../types';
import { useAuth } from '../auth/AuthContext';
import { PatientList } from '../patients/PatientList';
import { DocumentList } from '../documents/DocumentList';
import { ClinicalTimelinePanel } from '../timeline/ClinicalTimelinePanel';
import { EvaluationLabPanel } from '../evaluation/EvaluationLabPanel';
import api from '../../services/api';
import {
  Building2,
  Users,
  FileText,
  ShieldCheck,
  Activity,
  AlertTriangle,
  Clock,
  Sparkles,
  CheckCircle2,
  Database,
  ArrowRight,
  RotateCcw,
  RefreshCw,
  Lock,
  Search,
} from 'lucide-react';

export const OperationalDashboard: React.FC = () => {
  const { token } = useAuth();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [activeView, setActiveView] = useState<'overview' | 'ingestion' | 'audit' | 'security' | 'evaluation'>('overview');
  const [auditTab, setAuditTab] = useState<'documents' | 'timeline'>('documents');

  // Ingestion & Recovery State
  const [facilityDocuments, setFacilityDocuments] = useState<Document[]>([]);
  const [loadingFacilityDocs, setLoadingFacilityDocs] = useState<boolean>(false);
  const [recoveringDocId, setRecoveringDocId] = useState<string | null>(null);
  const [recoveryFeedback, setRecoveryFeedback] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [ingestionFilter, setIngestionFilter] = useState<string>('all');

  // Security Audit Logs State
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [loadingAuditLogs, setLoadingAuditLogs] = useState<boolean>(false);
  const [auditSearchQuery, setAuditSearchQuery] = useState<string>('');

  const fetchCohort = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch('/api/v1/patients', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data: Patient[] = await res.json();
        setPatients(data);
        if (data.length > 0 && !selectedPatient) {
          setSelectedPatient(data[0]);
        }
      }
    } catch {
      // Handled silently
    }
  }, [token, selectedPatient]);

  const fetchDocuments = useCallback(async (patientId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`/api/v1/documents?patient_id=${patientId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data: Document[] = await res.json();
        setDocuments(data);
      }
    } catch {
      // Handled silently
    }
  }, [token]);

  const fetchFacilityDocuments = useCallback(async () => {
    setLoadingFacilityDocs(true);
    try {
      const docs = await api.documents.list();
      setFacilityDocuments(docs);
    } catch {
      // Handled silently
    } finally {
      setLoadingFacilityDocs(false);
    }
  }, []);

  const fetchAuditLogs = useCallback(async () => {
    setLoadingAuditLogs(true);
    try {
      const logs = await api.audit.listLogs(100);
      setAuditLogs(logs);
    } catch {
      // Handled silently
    } finally {
      setLoadingAuditLogs(false);
    }
  }, []);

  useEffect(() => {
    fetchCohort();
  }, [fetchCohort]);

  useEffect(() => {
    if (selectedPatient) {
      fetchDocuments(selectedPatient.id);
    } else {
      setDocuments([]);
    }
  }, [selectedPatient, fetchDocuments]);

  useEffect(() => {
    if (activeView === 'ingestion') {
      fetchFacilityDocuments();
    } else if (activeView === 'security') {
      fetchAuditLogs();
    }
  }, [activeView, fetchFacilityDocuments, fetchAuditLogs]);

  const handleRecoverDocument = async (docId: string) => {
    setRecoveringDocId(docId);
    setRecoveryFeedback(null);
    try {
      const resp = await api.documents.recover(docId);
      setRecoveryFeedback({
        type: 'success',
        text: `Document successfully recovered: ${resp.chunk_count} chunks indexed across ${resp.pages_processed} pages.`,
      });
      // Refresh facility docs and selected patient docs
      fetchFacilityDocuments();
      if (selectedPatient) {
        fetchDocuments(selectedPatient.id);
      }
    } catch (err) {
      setRecoveryFeedback({
        type: 'error',
        text: err instanceof Error ? err.message : 'Document recovery failed.',
      });
    } finally {
      setRecoveringDocId(null);
    }
  };

  const totalDocuments = patients.reduce((acc, p) => acc + (p.document_count || 0), 0);

  const filteredFacilityDocuments = facilityDocuments.filter((doc) => {
    if (ingestionFilter === 'all') return true;
    return doc.ingestion_status === ingestionFilter;
  });

  const filteredAuditLogs = auditLogs.filter((log) => {
    if (!auditSearchQuery.trim()) return true;
    const q = auditSearchQuery.toLowerCase();
    return (
      log.action.toLowerCase().includes(q) ||
      (log.resource_type && log.resource_type.toLowerCase().includes(q)) ||
      (log.ip_address && log.ip_address.toLowerCase().includes(q)) ||
      (log.status && log.status.toLowerCase().includes(q)) ||
      (log.user_id && log.user_id.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6">
      {/* Executive Header */}
      <div className="rounded-2xl bg-white border border-slate-200 p-6 sm:p-7 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start sm:items-center space-x-4">
            <div className="w-14 h-14 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 shrink-0">
              <Building2 className="w-7 h-7" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                  Hospital Operational Oversight
                </h2>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200 font-semibold">
                  Administrator Suite
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1 max-w-2xl">
                Facility census monitoring, live document ingestion tracking, security audit logging, and clinical access governance.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              onClick={() => setActiveView('overview')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                activeView === 'overview'
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Operations Overview</span>
            </button>

            <button
              onClick={() => setActiveView('ingestion')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                activeView === 'ingestion'
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
              }`}
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Ingestion Monitoring</span>
            </button>

            <button
              onClick={() => setActiveView('audit')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                activeView === 'audit'
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Record Audit</span>
            </button>

            <button
              onClick={() => setActiveView('security')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                activeView === 'security'
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
              }`}
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Security Audit Trail</span>
            </button>

            <button
              onClick={() => setActiveView('evaluation')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                activeView === 'evaluation'
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Internal Quality Testing</span>
            </button>
          </div>
        </div>
      </div>

      {/* 1. Overview Mode */}
      {activeView === 'overview' && (
        <div className="space-y-6">
          {/* Key Metric Tiles */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Active Patient Census</span>
                <div className="p-2 rounded-lg bg-teal-50 text-teal-700 border border-teal-200">
                  <Users className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-bold text-slate-900 tracking-tight">{patients.length}</span>
                <span className="text-xs text-slate-500 ml-2">patient records</span>
              </div>
              <p className="text-xs text-teal-700 mt-1 flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3 text-teal-600" />
                <span>Server-enforced role isolation</span>
              </p>
            </div>

            <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Added Records Volume</span>
                <div className="p-2 rounded-lg bg-teal-50 text-teal-700 border border-teal-200">
                  <FileText className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-bold text-slate-900 tracking-tight">{totalDocuments}</span>
                <span className="text-xs text-slate-500 ml-2">clinical documents</span>
              </div>
              <p className="text-xs text-teal-700 mt-1 flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3 text-teal-600" />
                <span>SHA-256 integrity verification</span>
              </p>
            </div>

            <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Conflicting Information</span>
                <div className="p-2 rounded-lg bg-amber-50 text-amber-700 border border-amber-200">
                  <AlertTriangle className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-bold text-slate-900 tracking-tight">Active</span>
                <span className="text-xs text-slate-500 ml-2">heuristic review</span>
              </div>
              <p className="text-xs text-amber-700 mt-1 flex items-center space-x-1">
                <Activity className="w-3 h-3 text-amber-600" />
                <span>Flagging conflicting dates and notes</span>
              </p>
            </div>

            <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">Access and Security</span>
                <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <ShieldCheck className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-bold text-emerald-700 tracking-tight">Verified</span>
                <span className="text-xs text-slate-500 ml-2">role protection</span>
              </div>
              <p className="text-xs text-emerald-700 mt-1 flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                <span>Patient isolation enforced</span>
              </p>
            </div>
          </div>

          {/* Clinical Governance Highlights */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
                <Users className="w-4 h-4 text-teal-700" />
                <span>Hospital Census Roster Summary</span>
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Overview of current patient records under clinical review.
              </p>

              <div className="mt-4 space-y-2">
                {patients.map((p) => (
                  <div
                    key={p.id}
                    className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-xs font-semibold text-slate-900">
                        {p.first_name} {p.last_name}
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        Record ID: <span className="font-mono text-slate-700">{p.mrn_synthetic}</span> • {p.primary_condition}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-white text-slate-700 border border-slate-200">
                        {p.document_count || 0} documents
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-teal-700" />
                  <span>Quality Assurance and Evidence Standards</span>
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Systematic verification to ensure citation precision and evidence fidelity across medical records.
                </p>

                <div className="mt-4 space-y-2.5">
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                    <div className="flex items-center justify-between text-slate-800 font-medium">
                      <span>Evidence Citation Verification</span>
                      <span className="text-emerald-700 font-semibold">100% Page Anchored</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      Every generated summary includes exact document name and physical page citations.
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                    <div className="flex items-center justify-between text-slate-800 font-medium">
                      <span>Clinician Review Requirement</span>
                      <span className="text-teal-700 font-semibold">Mandatory Review</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      Zero autonomous diagnostic actions permitted without authorized human clinician approval.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-200 flex items-center justify-between">
                <span className="text-xs text-slate-500">Run quality and precision testing suite:</span>
                <button
                  onClick={() => setActiveView('evaluation')}
                  className="px-3.5 py-1.5 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 border border-teal-200 text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer"
                >
                  <span>Open Quality Testing</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 2. Document Ingestion Monitoring & Recovery */}
      {activeView === 'ingestion' && (
        <div className="space-y-4">
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
                  <RotateCcw className="w-4 h-4 text-teal-700" />
                  <span>Document Ingestion Monitoring & Recovery</span>
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Track document processing states, inspect indexing health, and execute one-click document recovery.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <select
                  value={ingestionFilter}
                  onChange={(e) => setIngestionFilter(e.target.value)}
                  className="text-xs px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-teal-500"
                >
                  <option value="all">All Statuses ({facilityDocuments.length})</option>
                  <option value="completed">Completed</option>
                  <option value="processing">Processing</option>
                  <option value="pending">Pending</option>
                  <option value="failed">Failed / Recovery Needed</option>
                </select>

                <button
                  onClick={fetchFacilityDocuments}
                  disabled={loadingFacilityDocs}
                  className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loadingFacilityDocs ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </button>
              </div>
            </div>

            {recoveryFeedback && (
              <div
                className={`p-3 rounded-xl border text-xs font-medium flex items-center space-x-2 ${
                  recoveryFeedback.type === 'success'
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : 'bg-rose-50 border-rose-200 text-rose-800'
                }`}
              >
                {recoveryFeedback.type === 'success' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                )}
                <span>{recoveryFeedback.text}</span>
              </div>
            )}

            {/* Ingestion Status Summary Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <span className="text-xs text-slate-500 block">Total Tracked</span>
                <span className="text-lg font-bold text-slate-800">{facilityDocuments.length}</span>
              </div>
              <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-center">
                <span className="text-xs text-emerald-700 block">Completed</span>
                <span className="text-lg font-bold text-emerald-800">
                  {facilityDocuments.filter((d) => d.ingestion_status === 'completed').length}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-sky-50 border border-sky-200 text-center">
                <span className="text-xs text-sky-700 block">Processing</span>
                <span className="text-lg font-bold text-sky-800">
                  {facilityDocuments.filter((d) => d.ingestion_status === 'processing').length}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-center">
                <span className="text-xs text-rose-700 block">Failed / Pending</span>
                <span className="text-lg font-bold text-rose-800">
                  {facilityDocuments.filter((d) => d.ingestion_status === 'failed' || d.ingestion_status === 'pending').length}
                </span>
              </div>
            </div>

            {/* Ingestion Monitoring Table */}
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                    <th className="py-2.5 px-3">Document Title</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">SHA-256 Hash</th>
                    <th className="py-2.5 px-3">Updated</th>
                    <th className="py-2.5 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredFacilityDocuments.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-400">
                        No documents found matching the selected filter.
                      </td>
                    </tr>
                  ) : (
                    filteredFacilityDocuments.map((doc) => (
                      <tr key={doc.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-2.5 px-3 font-medium text-slate-900 max-w-[200px] truncate" title={doc.title}>
                          {doc.title}
                        </td>
                        <td className="py-2.5 px-3 text-slate-500 capitalize">
                          {doc.doc_type.replace('_', ' ')}
                        </td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-2 py-0.5 rounded-full font-medium inline-block ${
                              doc.ingestion_status === 'completed'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : doc.ingestion_status === 'processing'
                                ? 'bg-sky-50 text-sky-700 border border-sky-200'
                                : doc.ingestion_status === 'failed'
                                ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                : 'bg-amber-50 text-amber-700 border border-amber-200'
                            }`}
                          >
                            {doc.ingestion_status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-500 text-[11px] max-w-[120px] truncate" title={doc.file_hash_sha256 || ''}>
                          {doc.file_hash_sha256 ? `${doc.file_hash_sha256.slice(0, 10)}...` : 'N/A'}
                        </td>
                        <td className="py-2.5 px-3 text-slate-500">
                          {new Date(doc.updated_at || doc.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => handleRecoverDocument(doc.id)}
                            disabled={recoveringDocId === doc.id}
                            className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center space-x-1 ml-auto cursor-pointer transition-all ${
                              doc.ingestion_status === 'failed' || doc.ingestion_status === 'pending'
                                ? 'bg-amber-600 hover:bg-amber-700 text-white shadow-sm'
                                : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                            }`}
                          >
                            <RotateCcw className={`w-3 h-3 ${recoveringDocId === doc.id ? 'animate-spin' : ''}`} />
                            <span>{recoveringDocId === doc.id ? 'Recovering...' : 'Recover'}</span>
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 3. Audit View Mode */}
      {activeView === 'audit' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          <div className="lg:col-span-1 h-[620px]">
            <PatientList
              selectedPatientId={selectedPatient?.id || null}
              onSelectPatient={(p) => setSelectedPatient(p)}
            />
          </div>

          <div className="lg:col-span-2 h-[620px] flex flex-col">
            {selectedPatient ? (
              <div className="flex flex-col h-full">
                <div className="flex items-center space-x-1 mb-3 bg-slate-100 p-1 rounded-xl border border-slate-200 shrink-0 w-fit">
                  <button
                    type="button"
                    onClick={() => setAuditTab('documents')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                      auditTab === 'documents'
                        ? 'bg-white text-teal-700 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Audit Attached Records ({documents.length})</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setAuditTab('timeline')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                      auditTab === 'timeline'
                        ? 'bg-white text-teal-700 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <Clock className="w-3.5 h-3.5" />
                    <span>Audit Medical History Timeline</span>
                  </button>
                </div>

                <div className="flex-1 min-h-0">
                  {auditTab === 'documents' ? (
                    <DocumentList
                      patientId={selectedPatient.id}
                      patientName={`${selectedPatient.first_name} ${selectedPatient.last_name}`}
                      documents={documents}
                      onRefresh={() => fetchDocuments(selectedPatient.id)}
                    />
                  ) : (
                    <ClinicalTimelinePanel
                      patientId={selectedPatient.id}
                      patientName={`${selectedPatient.first_name} ${selectedPatient.last_name}`}
                    />
                  )}
                </div>
              </div>
            ) : (
              <div className="h-full rounded-2xl bg-white border border-slate-200 p-8 flex flex-col items-center justify-center text-center shadow-sm">
                <Database className="w-10 h-10 text-slate-300 mb-3" />
                <h3 className="text-sm font-semibold text-slate-800">Select a Patient Record to Audit</h3>
                <p className="text-xs text-slate-500 mt-1 max-w-sm">
                  Choose a patient from the list to review documents, SHA-256 hashes, and medical history timeline.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 4. Security Audit Trail Mode */}
      {activeView === 'security' && (
        <div className="space-y-4">
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
                  <Lock className="w-4 h-4 text-teal-700" />
                  <span>Security & Clinical Access Audit Trail</span>
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Immutable, append-only security logs for user authentication, record accesses, and administrative changes.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search action, IP, user..."
                    value={auditSearchQuery}
                    onChange={(e) => setAuditSearchQuery(e.target.value)}
                    className="text-xs pl-8 pr-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-teal-500 w-48 sm:w-64"
                  />
                </div>

                <button
                  onClick={fetchAuditLogs}
                  disabled={loadingAuditLogs}
                  className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loadingAuditLogs ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </button>
              </div>
            </div>

            {/* Audit Log Table */}
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                    <th className="py-2.5 px-3">Timestamp</th>
                    <th className="py-2.5 px-3">Action</th>
                    <th className="py-2.5 px-3">User ID</th>
                    <th className="py-2.5 px-3">Resource Type</th>
                    <th className="py-2.5 px-3">Resource / Patient ID</th>
                    <th className="py-2.5 px-3">IP Address</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                  {filteredAuditLogs.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-400 font-sans text-xs">
                        {loadingAuditLogs ? 'Loading immutable audit trail...' : 'No audit events found.'}
                      </td>
                    </tr>
                  ) : (
                    filteredAuditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-2.5 px-3 text-slate-500 whitespace-nowrap">
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                        <td className="py-2.5 px-3 font-sans font-semibold text-slate-800">
                          {log.action}
                        </td>
                        <td className="py-2.5 px-3 text-slate-600 max-w-[100px] truncate" title={log.user_id || 'system'}>
                          {log.user_id ? log.user_id.slice(0, 8) : 'system'}
                        </td>
                        <td className="py-2.5 px-3 text-slate-600 font-sans">
                          {log.resource_type}
                        </td>
                        <td className="py-2.5 px-3 text-slate-600 max-w-[120px] truncate" title={log.resource_id || log.patient_id || '-'}>
                          {log.resource_id || log.patient_id || '-'}
                        </td>
                        <td className="py-2.5 px-3 text-slate-500">
                          {log.ip_address || '-'}
                        </td>
                        <td className="py-2.5 px-3 font-sans">
                          <span
                            className={`px-2 py-0.5 rounded-full font-semibold text-[10px] ${
                              log.status === 'SUCCESS'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : 'bg-rose-50 text-rose-700 border border-rose-200'
                            }`}
                          >
                            {log.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 5. Evaluation Lab View Mode */}
      {activeView === 'evaluation' && (
        <div className="w-full">
          <EvaluationLabPanel />
        </div>
      )}
    </div>
  );
};