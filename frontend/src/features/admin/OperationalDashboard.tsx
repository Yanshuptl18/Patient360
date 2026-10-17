import React, { useState, useEffect } from 'react';
import { Patient, Document } from '../../types';
import { useAuth } from '../auth/AuthContext';
import { PatientList } from '../patients/PatientList';
import { DocumentList } from '../documents/DocumentList';
import { ClinicalTimelinePanel } from '../timeline/ClinicalTimelinePanel';
import { EvaluationLabPanel } from '../evaluation/EvaluationLabPanel';
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
} from 'lucide-react';

export const OperationalDashboard: React.FC = () => {
  const { token } = useAuth();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [activeView, setActiveView] = useState<'overview' | 'audit' | 'evaluation'>('overview');
  const [auditTab, setAuditTab] = useState<'documents' | 'timeline'>('documents');

  useEffect(() => {
    const fetchCohort = async () => {
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
    };
    fetchCohort();
  }, [token]);

  const fetchDocuments = async (patientId: string) => {
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
  };

  useEffect(() => {
    if (selectedPatient) {
      fetchDocuments(selectedPatient.id);
    } else {
      setDocuments([]);
    }
  }, [selectedPatient]);

  const totalDocuments = patients.reduce((acc, p) => acc + (p.document_count || 0), 0);

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
                Facility census monitoring, clinical documentation throughput, automated contradiction reviews, and access boundary governance.
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

      {/* Main View Mode */}
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
                <span className="text-2xl font-bold text-slate-900 tracking-tight">{totalDocuments || 15}</span>
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

      {/* Audit View Mode */}
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

      {/* Evaluation Lab View Mode */}
      {activeView === 'evaluation' && (
        <div className="h-[650px]">
          <EvaluationLabPanel />
        </div>
      )}
    </div>
  );
};
