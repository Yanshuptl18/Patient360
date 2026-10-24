import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { HealthStatus } from './components/HealthStatus';
import { AboutPage } from './components/AboutPage';
import { DemoRoleSelector } from './components/DemoRoleSelector';
import { AuthProvider, useAuth } from './features/auth/AuthContext';
import { LoginModal } from './features/auth/LoginModal';
import { PatientList } from './features/patients/PatientList';
import { DocumentList } from './features/documents/DocumentList';
import { ClinicalRAGPanel } from './features/rag/ClinicalRAGPanel';
import { ClinicalTimelinePanel } from './features/timeline/ClinicalTimelinePanel';
import { ClinicalAgentPanel } from './features/agents/ClinicalAgentPanel';
import { ResearchIntelligencePanel } from './features/research/ResearchIntelligencePanel';
import { EvaluationLabPanel } from './features/evaluation/EvaluationLabPanel';
import { PatientPortal } from './features/patient/PatientPortal';
import { OperationalDashboard } from './features/admin/OperationalDashboard';
import { Patient, Document } from './types';
import {
  FileText,
  Clock,
  FileSearch,
  CheckCircle2,
  ShieldCheck,
  KeyRound,
  Database,
  Activity,
  Users,
  LogOut,
  HeartPulse,
  Building2,
  UserCheck,
  Server,
  Stethoscope,
  MessageSquare,
  BookOpen,
  ArrowRight,
} from 'lucide-react';

const MainContent: React.FC = () => {
  const [currentView, setCurrentView] = useState<'workspace' | 'about' | 'guide'>('workspace');
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [activePatientTab, setActivePatientTab] = useState<'documents' | 'rag' | 'timeline' | 'agents' | 'research' | 'evaluation'>('documents');
  const [nurseTab, setNurseTab] = useState<'documents' | 'timeline'>('documents');

  const { user, isAuthenticated, token, logout, demoMode, loading } = useAuth();

  // Synchronize authorized patient and reset documents on user/role switch
  useEffect(() => {
    setSelectedPatient(null);
    setDocuments([]);

    if (!token || !user) return;

    let isMounted = true;
    const loadInitialPatient = async () => {
      try {
        const res = await fetch('/api/v1/patients', {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok && isMounted) {
          const data: Patient[] = await res.json();
          if (data.length > 0) {
            // Default to Eleanor Vance (SYNTH-10001) for rich demonstration dossier, or first patient
            const primary = data.find((p) => p.mrn_synthetic === 'SYNTH-10001') || data[0];
            setSelectedPatient(primary);
          }
        }
      } catch (err) {
        console.warn('Could not load initial patient:', err);
      }
    };
    loadInitialPatient();

    return () => {
      isMounted = false;
    };
  }, [token, user?.id, user?.role]);

  const fetchDocuments = useCallback(
    async (patientId: string) => {
      if (!token) return;
      try {
        const response = await fetch(`/api/v1/documents?patient_id=${patientId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (response.ok) {
          const data: Document[] = await response.json();
          setDocuments(data);
        }
      } catch {
        // Handled silently
      }
    },
    [token]
  );

  useEffect(() => {
    if (selectedPatient) {
      fetchDocuments(selectedPatient.id);
    } else {
      setDocuments([]);
    }
  }, [selectedPatient, fetchDocuments]);

  const getRoleIcon = (role?: string) => {
    switch (role) {
      case 'doctor':
      case 'reviewer':
        return <Stethoscope className="w-5 h-5 text-teal-700" />;
      case 'nurse':
        return <HeartPulse className="w-5 h-5 text-teal-700" />;
      case 'hospital_admin':
        return <Building2 className="w-5 h-5 text-teal-700" />;
      case 'patient':
        return <UserCheck className="w-5 h-5 text-teal-700" />;
      case 'admin':
        return <Server className="w-5 h-5 text-teal-700" />;
      default:
        return <KeyRound className="w-5 h-5 text-teal-700" />;
    }
  };

  const getRoleTitle = (role?: string) => {
    switch (role) {
      case 'doctor':
        return 'Doctor';
      case 'nurse':
        return 'Nurse / Care Coordinator';
      case 'hospital_admin':
        return 'Hospital Administrator';
      case 'patient':
        return 'Patient';
      case 'admin':
        return 'System Administrator';
      case 'reviewer':
        return 'Clinical Reviewer';
      case 'researcher':
        return 'Clinical Researcher';
      default:
        return role || 'User';
    }
  };

  const getRolePermissionsDescription = (role?: string) => {
    switch (role) {
      case 'doctor':
      case 'reviewer':
        return 'Patient medical records, chronological timelines, evidence-grounded questions, clinical research assistant, and biomedical study comparisons';
      case 'nurse':
        return 'Care coordination, patient event tracking, medication schedules, and conflicting clinical information alerts';
      case 'hospital_admin':
        return 'Operational oversight, patient census monitoring, document throughput, and record verification';
      case 'patient':
        return 'Personal health records strictly isolated to Eleanor Vance (SYNTH-10001), care history, and questions about personal documents';
      case 'admin':
        return 'System security administration, quality testing benchmarks, service status, and audit logs';
      default:
        return 'Authorized clinical information access';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="flex flex-col items-center space-y-3">
          <div className="p-3 rounded-2xl bg-teal-50 text-teal-700 border border-teal-200 animate-pulse">
            <Activity className="w-8 h-8" />
          </div>
          <span className="text-sm font-semibold text-slate-700">Connecting to Patient360 Workspace...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans">
      <Header
        currentView={currentView}
        onNavigate={(view) => setCurrentView(view)}
        onOpenLogin={() => setIsLoginOpen(true)}
        onOpenRoleSwitch={() => setIsLoginOpen(true)}
      />

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Render View: About Page */}
        {currentView === 'about' && (
          <AboutPage
            onExploreWorkspace={() => setCurrentView('workspace')}
            onOpenSignIn={() => setIsLoginOpen(true)}
          />
        )}

        {/* Render View: Clinical Guide */}
        {currentView === 'guide' && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2.5 rounded-xl bg-teal-50 text-teal-700 border border-teal-200">
                  <BookOpen className="w-5 h-5" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-slate-900 tracking-tight">Clinical User Guide</h1>
                  <p className="text-xs text-slate-500 mt-0.5">
                    How clinicians, care coordinators, researchers, and administrators use Patient360
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-teal-600" />
                    <span>Adding Medical Documents</span>
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Upload clinical PDF reports up to 25 MB. Every document is assigned a tamper-evident SHA-256 hash, physical page numbers, and categorized for structured evidence retrieval.
                  </p>
                </div>

                <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
                    <MessageSquare className="w-4 h-4 text-teal-600" />
                    <span>Asking About Records</span>
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Enter clinical questions regarding a patient's documented history. Answers are grounded in the authorized records and include exact document names and page numbers. If evidence is missing, the system abstains plainly.
                  </p>
                </div>

                <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-teal-600" />
                    <span>Medical History Timeline</span>
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Examine chronological diagnoses, medications, procedures, encounters, and lab results. Any conflicting dates or contradictory notes between records are highlighted for clinical review.
                  </p>
                </div>

                <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
                    <ShieldCheck className="w-4 h-4 text-teal-600" />
                    <span>Review and Approval Gates</span>
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Multi-step investigations require human clinician review before report finalization. No autonomous clinical diagnosis or treatment prescribing is performed.
                  </p>
                </div>
              </div>

              <div className="mt-8 pt-6 border-t border-slate-200 flex items-center justify-between">
                <span className="text-xs text-slate-500">Ready to examine patient records?</span>
                <button
                  type="button"
                  onClick={() => setCurrentView('workspace')}
                  className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-medium text-xs flex items-center space-x-1.5 transition-colors cursor-pointer shadow-sm"
                >
                  <span>Open Workspace</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Render View: Main Workspace */}
        {currentView === 'workspace' && (
          <div className="space-y-6">
            {/* Authenticated User Session Status Banner */}
            {isAuthenticated && user && (
              <div className="p-4 rounded-xl bg-white border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
                <div className="flex items-start sm:items-center space-x-3.5">
                  <div className="p-2.5 rounded-xl bg-teal-50 border border-teal-200 shrink-0">
                    {getRoleIcon(user.role)}
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-bold text-slate-900">
                        {user.full_name}
                      </span>
                      <span className="text-xs text-slate-500 font-mono">
                        ({user.email})
                      </span>
                      {demoMode && (
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                          Role: {getRoleTitle(user.role)}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-1 max-w-3xl">
                      {getRolePermissionsDescription(user.role)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  {demoMode && (
                    <button
                      onClick={() => setIsLoginOpen(true)}
                      className="px-3 py-1.5 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 border border-teal-200 text-xs font-medium flex items-center space-x-1.5 transition-all cursor-pointer"
                    >
                      <Users className="w-3.5 h-3.5" />
                      <span>Switch Demo Role</span>
                    </button>
                  )}
                  <button
                    onClick={logout}
                    className="px-3 py-1.5 rounded-lg bg-slate-50 hover:bg-rose-50 hover:text-rose-700 text-slate-600 border border-slate-200 text-xs font-medium flex items-center space-x-1.5 transition-all cursor-pointer"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}

            {/* Unauthenticated Landing Experience with 1-Click Demo Selector */}
            {!isAuthenticated && (
              <div className="space-y-6">
                {/* Clean Clinical Hero Card */}
                <div className="rounded-2xl bg-white border border-slate-200 p-8 sm:p-10 shadow-sm">
                  <div className="max-w-3xl space-y-4">
                    <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-700 text-xs font-medium">
                      <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                      <span>Evidence-Grounded Healthcare Intelligence</span>
                    </div>

                    <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 leading-tight">
                      Medical evidence, <span className="text-teal-700">brought together.</span>
                    </h1>

                    <p className="text-sm text-slate-600 leading-relaxed">
                      Explore medical records, understand patient histories, and discover evidence from research documents in one organized workspace.
                    </p>

                    <div className="pt-2 flex flex-wrap gap-4 text-xs text-slate-500">
                      <div className="flex items-center space-x-1.5">
                        <CheckCircle2 className="w-4 h-4 text-teal-600" />
                        <span>Exact physical page citations</span>
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <CheckCircle2 className="w-4 h-4 text-teal-600" />
                        <span>Longitudinal medical history timelines</span>
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <CheckCircle2 className="w-4 h-4 text-teal-600" />
                        <span>Strict server-side patient isolation</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
                  <DemoRoleSelector
                    onRoleSelected={() => {
                      setCurrentView('workspace');
                    }}
                  />
                </div>
              </div>
            )}

            {/* Role-Specific Authenticated Workspaces */}
            {isAuthenticated && user && (
              <div>
                {/* 1. Patient Experience */}
                {user.role === 'patient' && (
                  selectedPatient ? (
                    <PatientPortal
                      patient={selectedPatient}
                      documents={documents}
                      onRefreshDocuments={() => fetchDocuments(selectedPatient.id)}
                    />
                  ) : (
                    <div className="py-16 text-center rounded-2xl bg-white border border-slate-200 shadow-sm">
                      <UserCheck className="w-10 h-10 text-teal-600 mx-auto mb-3 animate-pulse" />
                      <h3 className="text-sm font-semibold text-slate-900">Loading Personal Health Records...</h3>
                      <p className="text-xs text-slate-500 mt-1">Retrieving verified personal records (SYNTH-10001)</p>
                    </div>
                  )
                )}

                {/* 2. Hospital Administrator Experience */}
                {user.role === 'hospital_admin' && (
                  <OperationalDashboard />
                )}

                {/* 3. Nurse / Care Coordinator Experience */}
                {user.role === 'nurse' && (
                  <section>
                    <div className="flex items-center space-x-2 mb-4">
                      <div className="p-1.5 rounded-lg bg-teal-50 text-teal-700 border border-teal-200">
                        <HeartPulse className="w-4 h-4" />
                      </div>
                      <div>
                        <h2 className="text-base font-semibold text-slate-900">Care Coordination and Patient Monitoring</h2>
                        <p className="text-xs text-slate-500">
                          Surfacing clinical events, medication schedules, and conflicting medical documentation
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
                      <div className="lg:col-span-1 min-h-[620px]">
                        <PatientList
                          selectedPatientId={selectedPatient?.id || null}
                          onSelectPatient={(p) => setSelectedPatient(p)}
                        />
                      </div>

                      <div className="lg:col-span-2 min-h-[620px] flex flex-col">
                        {selectedPatient ? (
                          <div className="flex flex-col h-full">
                            <div className="flex items-center space-x-1 mb-3 bg-slate-100 p-1 rounded-xl border border-slate-200 shrink-0 w-fit">
                              <button
                                type="button"
                                onClick={() => setNurseTab('documents')}
                                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                                  nurseTab === 'documents'
                                    ? 'bg-white text-teal-700 shadow-sm'
                                    : 'text-slate-600 hover:text-slate-900'
                                }`}
                              >
                                <FileText className="w-3.5 h-3.5" />
                                <span>Attached Medical Records ({documents.length})</span>
                              </button>

                              <button
                                type="button"
                                onClick={() => setNurseTab('timeline')}
                                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                                  nurseTab === 'timeline'
                                    ? 'bg-white text-teal-700 shadow-sm'
                                    : 'text-slate-600 hover:text-slate-900'
                                }`}
                              >
                                <Clock className="w-3.5 h-3.5" />
                                <span>Medical History Timeline</span>
                              </button>
                            </div>

                            <div className="flex-1 min-h-0">
                              {nurseTab === 'documents' ? (
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
                            <HeartPulse className="w-10 h-10 text-slate-300 mb-3" />
                            <h3 className="text-sm font-semibold text-slate-800">Select a Patient for Care Monitoring</h3>
                            <p className="text-xs text-slate-500 mt-1 max-w-sm">
                              Select an assigned patient from the roster to monitor chronological care events, lab results, and conflicting notes.
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </section>
                )}

                {/* 4. Doctor, Reviewer, Admin, and Researcher Experience */}
                {(user.role === 'doctor' || user.role === 'reviewer' || user.role === 'admin' || user.role === 'researcher') && (
                  <section className="space-y-4">
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-3 border-b border-slate-200 gap-3">
                      <div className="flex items-center space-x-2">
                        <div className="p-1.5 rounded-lg bg-teal-50 text-teal-700 border border-teal-200">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div>
                          <h2 className="text-base font-semibold text-slate-900">
                            {user.role === 'admin'
                              ? 'Administrative Records and Quality Testing'
                              : 'Clinical Patient Records and Research Workspace'}
                          </h2>
                          <p className="text-xs text-slate-500">
                            Authorized medical records, evidence-grounded answers, and verified document storage
                          </p>
                        </div>
                      </div>

                      {/* Top-Level Tab Navigation */}
                      <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl border border-slate-200 shrink-0 overflow-x-auto max-w-full">
                        <button
                          type="button"
                          onClick={() => setActivePatientTab('documents')}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer whitespace-nowrap ${
                            activePatientTab === 'documents'
                              ? 'bg-white text-teal-700 shadow-sm'
                              : 'text-slate-600 hover:text-slate-900'
                          }`}
                        >
                          <FileText className="w-3.5 h-3.5" />
                          <span>Medical Documents ({documents.length})</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => setActivePatientTab('rag')}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer whitespace-nowrap ${
                            activePatientTab === 'rag'
                              ? 'bg-white text-teal-700 shadow-sm'
                              : 'text-slate-600 hover:text-slate-900'
                          }`}
                        >
                          <MessageSquare className="w-3.5 h-3.5" />
                          <span>Ask About Records</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => setActivePatientTab('timeline')}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer whitespace-nowrap ${
                            activePatientTab === 'timeline'
                              ? 'bg-white text-teal-700 shadow-sm'
                              : 'text-slate-600 hover:text-slate-900'
                          }`}
                        >
                          <Clock className="w-3.5 h-3.5" />
                          <span>Medical History Timeline</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => setActivePatientTab('agents')}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer whitespace-nowrap ${
                            activePatientTab === 'agents'
                              ? 'bg-white text-teal-700 shadow-sm'
                              : 'text-slate-600 hover:text-slate-900'
                          }`}
                        >
                          <FileSearch className="w-3.5 h-3.5" />
                          <span>Clinical Research Assistant</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => setActivePatientTab('research')}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer whitespace-nowrap ${
                            activePatientTab === 'research'
                              ? 'bg-white text-teal-700 shadow-sm'
                              : 'text-slate-600 hover:text-slate-900'
                          }`}
                        >
                          <BookOpen className="w-3.5 h-3.5" />
                          <span>Biomedical Studies</span>
                        </button>

                        {user.role === 'admin' && (
                          <button
                            type="button"
                            onClick={() => setActivePatientTab('evaluation')}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer whitespace-nowrap ${
                              activePatientTab === 'evaluation'
                                ? 'bg-white text-teal-700 shadow-sm'
                                : 'text-slate-600 hover:text-slate-900'
                            }`}
                          >
                            <Activity className="w-3.5 h-3.5" />
                            <span>Quality Testing</span>
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Active Content: Full-width for Platform-level features, 1:2 split for Patient records */}
                    {activePatientTab === 'research' ? (
                      <div className="w-full min-h-[640px]">
                        <ResearchIntelligencePanel />
                      </div>
                    ) : activePatientTab === 'evaluation' ? (
                      <div className="w-full min-h-[640px]">
                        <EvaluationLabPanel />
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
                        <div className="lg:col-span-1 min-h-[620px]">
                          <PatientList
                            selectedPatientId={selectedPatient?.id || null}
                            onSelectPatient={(p) => setSelectedPatient(p)}
                          />
                        </div>

                        <div className="lg:col-span-2 min-h-[620px] flex flex-col">
                          {selectedPatient ? (
                            <div className="flex-1 min-h-0">
                              {activePatientTab === 'documents' ? (
                                <DocumentList
                                  patientId={selectedPatient.id}
                                  patientName={`${selectedPatient.first_name} ${selectedPatient.last_name}`}
                                  documents={documents}
                                  onRefresh={() => fetchDocuments(selectedPatient.id)}
                                />
                              ) : activePatientTab === 'rag' ? (
                                <ClinicalRAGPanel
                                  patientId={selectedPatient.id}
                                  patientName={`${selectedPatient.first_name} ${selectedPatient.last_name}`}
                                />
                              ) : activePatientTab === 'timeline' ? (
                                <ClinicalTimelinePanel
                                  patientId={selectedPatient.id}
                                  patientName={`${selectedPatient.first_name} ${selectedPatient.last_name}`}
                                />
                              ) : (
                                <ClinicalAgentPanel
                                  patientId={selectedPatient.id}
                                  patientName={`${selectedPatient.first_name} ${selectedPatient.last_name}`}
                                />
                              )}
                            </div>
                          ) : (
                            <div className="h-full min-h-[500px] rounded-2xl bg-white border border-slate-200 p-8 flex flex-col items-center justify-center text-center shadow-sm">
                              <Database className="w-10 h-10 text-slate-300 mb-3" />
                              <h3 className="text-sm font-semibold text-slate-800">Select a Patient Record</h3>
                              <p className="text-xs text-slate-500 mt-1 max-w-sm mb-4">
                                Select an authorized patient from the list on the left to inspect documents, ask clinical questions, or view timelines.
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </section>
                )}
              </div>
            )}

            {/* Service Status Component */}
            <HealthStatus />
          </div>
        )}
      </main>

      {/* Login Modal */}
      <LoginModal isOpen={isLoginOpen} onClose={() => setIsLoginOpen(false)} />

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 mt-12 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© 2026 Patient360 Platform. Medical evidence and clinical research intelligence.</p>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setCurrentView('about')}
              className="hover:text-slate-800 transition-colors cursor-pointer"
            >
              About Patient360
            </button>
            <span className="text-slate-300">•</span>
            <button
              onClick={() => setCurrentView('guide')}
              className="hover:text-slate-800 transition-colors cursor-pointer"
            >
              Clinical Guide
            </button>
            <span className="text-slate-300">•</span>
            <a
              href="/api/v1/health"
              target="_blank"
              rel="noreferrer"
              className="hover:text-slate-800 transition-colors"
            >
              Service Status
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainContent />
    </AuthProvider>
  );
};
