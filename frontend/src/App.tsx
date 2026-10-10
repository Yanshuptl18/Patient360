import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { HealthStatus } from './components/HealthStatus';
import { RoadmapCard } from './components/RoadmapCard';
import { AuthProvider, useAuth } from './features/auth/AuthContext';
import { LoginModal } from './features/auth/LoginModal';
import { PatientList } from './features/patients/PatientList';
import { DocumentList } from './features/documents/DocumentList';
import { ClinicalRAGPanel } from './features/rag/ClinicalRAGPanel';
import { ClinicalTimelinePanel } from './features/timeline/ClinicalTimelinePanel';
import { ClinicalAgentPanel } from './features/agents/ClinicalAgentPanel';
import { ResearchIntelligencePanel } from './features/research/ResearchIntelligencePanel';
import { PhaseInfo, Patient, Document } from './types';
import { FileText, Clock, FileSearch, Bot, CheckCircle2, ShieldCheck, ShieldAlert, KeyRound, Database, FolderGit2, Sparkles } from 'lucide-react';

const PHASES_DATA: PhaseInfo[] = [
  { number: 1, name: 'Discovery & Architecture', status: 'Verified', description: 'Complete 15-file blueprint, data models, and specifications.', tag: 'Architecture' },
  { number: 2, name: 'Development Foundation', status: 'Verified', description: 'Docker Compose, FastAPI, React/Vite, health probes, and pytest.', tag: 'Foundation' },
  { number: 3, name: 'Auth, Authorization & RBAC', status: 'Verified', description: 'JWT authentication, Argon2 hashing, and server-side RBAC guards.', tag: 'Security' },
  { number: 4, name: 'Patient & Doc Management', status: 'Verified', description: 'Patient records, PDF upload, storage adapter, and tenant isolation.', tag: 'Core Data' },
  { number: 5, name: 'Ingestion & Chunking', status: 'Verified', description: 'PyMuPDF page-aware extraction, clinical normalizer, and chunker.', tag: 'Ingestion' },
  { number: 6, name: 'Embeddings & Qdrant', status: 'Verified', description: 'FastEmbed CPU vectors (384-dim) and Qdrant payload filters.', tag: 'Vector Store' },
  { number: 7, name: 'Baseline Grounded RAG', status: 'Verified', description: 'End-to-end Q&A, context builder, and citation parser.', tag: 'RAG Pipeline' },
  { number: 8, name: 'Advanced Hybrid RAG', status: 'Verified', description: 'BM25 sparse search, Reciprocal Rank Fusion, and citation verifier.', tag: 'Hybrid Search' },
  { number: 9, name: 'Timeline & Event Synthesis', status: 'Verified', description: 'Chronological clinical timeline and contradiction surfacing.', tag: 'Timeline' },
  { number: 10, name: 'Bounded Agentic Workflows', status: 'Verified', description: 'LangGraph multi-step workflows, read-only tools, and approval gates.', tag: 'Agents' },
  { number: 11, name: 'Research Intelligence', status: 'Verified', description: 'Literature search, comparative study matrices, and report export.', tag: 'Research' },
  { number: 12, name: 'Evaluation Laboratory', status: 'Planned', description: '50-item synthetic benchmark runner, Recall, Faithfulness, Precision.', tag: 'Evaluation' },
  { number: 13, name: 'Security & Responsible AI', status: 'Planned', description: 'Prompt-injection pen tests, audit logs, and data erasure.', tag: 'Hardening' },
  { number: 14, name: 'Production Hardening', status: 'Planned', description: 'Multi-stage Docker, Prometheus metrics, and CI/CD pipelines.', tag: 'DevOps' },
  { number: 15, name: 'Portfolio & Demo Release', status: 'Planned', description: 'Pre-seeded synthetic cohorts, case studies, and documentation.', tag: 'Release' },
];

const MainContent: React.FC = () => {
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [activePatientTab, setActivePatientTab] = useState<'documents' | 'rag' | 'timeline' | 'agents' | 'research'>('documents');

  const { user, isAuthenticated, token } = useAuth();

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
      } catch (err) {
        console.error('Failed to load documents:', err);
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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header onOpenLogin={() => setIsLoginOpen(true)} />

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* User Session Status Banner */}
        {isAuthenticated && user ? (
          <div className="mb-6 p-4 rounded-2xl bg-teal-500/10 border border-teal-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-xl bg-teal-500/20 text-teal-300">
                <KeyRound className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-teal-300">
                  Authenticated as {user.full_name} ({user.email})
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Role: <span className="font-semibold text-slate-200 uppercase">{user.role}</span> • Permissions:{' '}
                  {user.role === 'admin'
                    ? 'Full Administrative & RBAC Configuration'
                    : user.role === 'reviewer'
                    ? 'Permitted Patient Records & Longitudinal Timelines'
                    : user.role === 'researcher'
                    ? 'Biomedical Literature & Comparative Study Matrices'
                    : 'Synthetic Demonstration Datasets Only'}
                </div>
              </div>
            </div>

            <div className="text-[11px] font-mono text-teal-400/80 shrink-0">
              Session Active
            </div>
          </div>
        ) : (
          <div className="mb-6 p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-xl bg-slate-800 text-slate-400">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-200">Unauthenticated Session</div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Sign in with a demo persona to test server-side role-based access control and patient isolation.
                </p>
              </div>
            </div>

            <button
              onClick={() => setIsLoginOpen(true)}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors border border-slate-700 shrink-0"
            >
              Sign In as Demo Persona
            </button>
          </div>
        )}

        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-slate-900 to-slate-900/60 border border-slate-800 p-8 sm:p-10 mb-8 shadow-2xl">
          <div className="absolute top-0 right-0 -mt-10 -mr-10 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-0 -mb-10 -ml-10 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 max-w-3xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-medium mb-4">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Evidence-Grounded Healthcare Intelligence</span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-white leading-tight">
              Evidence-Based Clinical Intelligence, <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-cyan-400">Strictly Provenanced</span>
            </h1>

            <p className="mt-3 text-sm sm:text-base text-slate-300 leading-relaxed">
              Patient360 synthesizes fragmented medical records and biomedical research into structured, verifiable knowledge with page-level citations, longitudinal timeline reconstruction, and bounded agentic verification.
            </p>

            <div className="mt-6 flex flex-wrap gap-4 text-xs text-slate-400">
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-teal-400" />
                <span>Zero Autonomous Diagnostic Claims</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-teal-400" />
                <span>Page-Anchored Provenance</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-teal-400" />
                <span>Server-Side RBAC Enforcement</span>
              </div>
            </div>
          </div>
        </div>

        {/* Core Pillars Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all">
            <div className="w-9 h-9 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20 flex items-center justify-center mb-3">
              <FileText className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-white">Document Intelligence</h3>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Hybrid retrieval (Dense + BM25) with exact claim-to-passage citation tracking.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center justify-center mb-3">
              <Clock className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-white">Longitudinal Timeline</h3>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Chronological clinical events surfacing conflicting dates, allergies, and dosages.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center mb-3">
              <FileSearch className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-white">Research Intelligence</h3>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Cross-study evidence comparison matrices across clinical trials and guidelines.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mb-3">
              <Bot className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-white">Bounded Agents</h3>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              LangGraph state machine with 5-iteration ceiling, timeouts, and human approval gates.
            </p>
          </div>
        </div>

        {/* Patient & Document Management Workspace (Authenticated) */}
        {isAuthenticated && (
          <section className="mb-8">
            <div className="flex items-center space-x-2 mb-4">
              <div className="p-1.5 rounded-lg bg-teal-500/10 text-teal-400">
                <FolderGit2 className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-white">Patient Dossiers & Document Registry</h2>
                <p className="text-xs text-slate-400">
                  Phase 4 — Isolated clinical records, PDF validation, and cryptographic SHA-256 storage
                </p>
              </div>
            </div>

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
                    {/* Tab Navigation */}
                    <div className="flex items-center space-x-2 mb-3 bg-slate-900/60 p-1.5 rounded-2xl border border-slate-800 shrink-0 w-fit">
                      <button
                        type="button"
                        onClick={() => setActivePatientTab('documents')}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                          activePatientTab === 'documents'
                            ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>Attached Documents ({documents.length})</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setActivePatientTab('rag')}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                          activePatientTab === 'rag'
                            ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Grounded Clinical RAG</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setActivePatientTab('timeline')}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                          activePatientTab === 'timeline'
                            ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        <Clock className="w-3.5 h-3.5" />
                        <span>Longitudinal Timeline</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setActivePatientTab('agents')}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                          activePatientTab === 'agents'
                            ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        <Bot className="w-3.5 h-3.5" />
                        <span>Bounded Agents</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setActivePatientTab('research')}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer ${
                          activePatientTab === 'research'
                            ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        <FileSearch className="w-3.5 h-3.5" />
                        <span>Research Intelligence</span>
                      </button>
                    </div>

                    {/* Active View */}
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
                      ) : activePatientTab === 'agents' ? (
                        <ClinicalAgentPanel
                          patientId={selectedPatient.id}
                          patientName={`${selectedPatient.first_name} ${selectedPatient.last_name}`}
                        />
                      ) : (
                        <ResearchIntelligencePanel />
                      )}
                    </div>

                  </div>
                ) : (
                  <div className="h-full rounded-3xl bg-slate-900/60 border border-slate-800 p-8 flex flex-col items-center justify-center text-center">
                    <Database className="w-12 h-12 text-slate-600 mb-3" />
                    <h3 className="text-sm font-semibold text-white">No Patient Selected</h3>
                    <p className="text-xs text-slate-400 mt-1 max-w-sm">
                      Select an authorized patient dossier from the left panel to inspect attached clinical documents, or register a new synthetic cohort member.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        {/* Live Infrastructure Health Monitor */}
        <HealthStatus />

        {/* Phase Progression Tracker */}
        <RoadmapCard phases={PHASES_DATA} />
      </main>

      {/* Login Modal */}
      <LoginModal isOpen={isLoginOpen} onClose={() => setIsLoginOpen(false)} />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/40 py-6 mt-12 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© 2026 Patient360 Platform. Developed under strict modular architecture and healthcare safety standards.</p>
          <div className="flex items-center space-x-4">
            <a href="http://127.0.0.1:8000/api/v1/health" target="_blank" rel="noreferrer" className="hover:text-slate-300 transition-colors">
              Health Probe API
            </a>
            <span className="text-slate-700">•</span>
            <a href="http://127.0.0.1:8000/api/v1/docs" target="_blank" rel="noreferrer" className="hover:text-slate-300 transition-colors">
              OpenAPI Spec
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
