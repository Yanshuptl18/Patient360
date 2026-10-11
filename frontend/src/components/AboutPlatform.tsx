import React, { useState } from 'react';
import {
  FileText,
  Clock,
  Sparkles,
  FileSearch,
  Bot,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Stethoscope,
  GraduationCap,
  Building2,
  ChevronRight,
  BookOpen,
  Layers,
  Lock,
} from 'lucide-react';

export const AboutPlatform: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'capabilities' | 'beneficiaries' | 'safety' | 'architecture'>('capabilities');

  return (
    <section className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-sm mb-12">
      {/* Section Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800/80 gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-medium mb-3">
            <BookOpen className="w-3.5 h-3.5" />
            <span>Platform Overview & Clinical Guide</span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">About Patient360</h2>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
            An enterprise clinical intelligence platform designed to synthesize fragmented medical records and scientific literature into evidence-grounded, verifiable knowledge without medical hallucination.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center p-1.5 bg-slate-950/80 border border-slate-800 rounded-2xl shrink-0 self-start md:self-center">
          <button
            type="button"
            onClick={() => setActiveTab('capabilities')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'capabilities'
                ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Capabilities
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('beneficiaries')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'beneficiaries'
                ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Who It Helps
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('safety')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'safety'
                ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Safety Guardrails
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('architecture')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'architecture'
                ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            System Highlights
          </button>
        </div>
      </div>

      {/* Tab 1: Capabilities */}
      {activeTab === 'capabilities' && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 animate-fade-in">
          <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-teal-500/30 transition-all flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20 flex items-center justify-center mb-3">
                <FileText className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Unified Patient Dossiers</h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                Aggregates diverse medical documentation—including discharge summaries, pathology reports, molecular genetics, and outpatient notes—into isolated, structured patient profiles with SHA-256 cryptographic file integrity.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/60 text-[11px] text-teal-400 flex items-center space-x-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Multi-Document Aggregation</span>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-cyan-500/30 transition-all flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center justify-center mb-3">
                <Clock className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Clinical Timeline & Conflict Detection</h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                Chronologically reconstructs clinical encounters and actively surfaces medical contradictions across visits—such as discordant medication dosages, conflicting allergy listings, or opposing diagnoses.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/60 text-[11px] text-cyan-400 flex items-center space-x-1.5 font-medium">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Automated Discrepancy Flagging</span>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-emerald-500/30 transition-all flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mb-3">
                <Sparkles className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Evidence-Grounded RAG</h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                Responds to complex clinical inquiries with verbatim document quotes and page citations. The system strictly abstains from answering when facts are not supported in the patient record, eliminating hallucinations.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/60 text-[11px] text-emerald-400 flex items-center space-x-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Page-Level Provenance & Abstention</span>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-indigo-500/30 transition-all flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center mb-3">
                <FileSearch className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Biomedical Literature Matrix</h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                Retrieves published clinical trials and practice guidelines, automatically synthesizing structured PICO matrices (Population, Intervention, Comparator, Outcome) for comparative efficacy analysis.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/60 text-[11px] text-indigo-400 flex items-center space-x-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Structured PICO Evidence Matrices</span>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-amber-500/30 transition-all flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center mb-3">
                <Bot className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Bounded Agentic Synthesis</h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                Multi-step synthesis workflows governed by strict iteration ceilings and read-only tools. Mandates clinician review and approval gates before any generated synthesis is certified or finalized.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/60 text-[11px] text-amber-400 flex items-center space-x-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Clinician Approval Gates</span>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-purple-500/30 transition-all flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center mb-3">
                <Lock className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Role-Based Governance</h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                Enforces server-side permissions for Clinical Reviewers, Medical Researchers, and Administrators. Automatic sanitization redacts PII and confidential keys from system audit trails.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/60 text-[11px] text-purple-400 flex items-center space-x-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>HIPAA-Ready Audit Sanitization</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Who It Helps */}
      {activeTab === 'beneficiaries' && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-5 animate-fade-in">
          <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex flex-col justify-between">
            <div>
              <div className="p-2.5 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20 w-fit mb-4">
                <Stethoscope className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Physicians & Clinical Reviewers</h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                Reduce clinical chart review time while maintaining complete confidence in evidence. Instantly spot contradictory dosages across encounters, inspect original PDF passages, and verify diagnostic timelines.
              </p>
              <ul className="mt-4 space-y-2 text-xs text-slate-400">
                <li className="flex items-start space-x-2">
                  <ChevronRight className="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5" />
                  <span>Rapid longitudinal summary generation</span>
                </li>
                <li className="flex items-start space-x-2">
                  <ChevronRight className="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5" />
                  <span>Immediate alerts on conflicting medication regimens</span>
                </li>
                <li className="flex items-start space-x-2">
                  <ChevronRight className="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5" />
                  <span>One-click jump to verbatim source PDF pages</span>
                </li>
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 text-[11px] text-teal-300 font-medium">
              Persona: Clinical Reviewer (`reviewer@patient360.org`)
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex flex-col justify-between">
            <div>
              <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 w-fit mb-4">
                <GraduationCap className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Medical Researchers & Academics</h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                Cross-analyze landmark trial data and comparative therapeutic outcomes alongside structured patient cohorts. Compare hazard ratios, primary endpoints, and guideline recommendations side-by-side.
              </p>
              <ul className="mt-4 space-y-2 text-xs text-slate-400">
                <li className="flex items-start space-x-2">
                  <ChevronRight className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                  <span>Comparative trial matrices with structured PICO data</span>
                </li>
                <li className="flex items-start space-x-2">
                  <ChevronRight className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                  <span>Automated benchmark evaluations (Faithfulness, Recall)</span>
                </li>
                <li className="flex items-start space-x-2">
                  <ChevronRight className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                  <span>Direct literature synthesis for clinical trial protocols</span>
                </li>
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 text-[11px] text-indigo-300 font-medium">
              Persona: Medical Researcher (`researcher@patient360.org`)
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex flex-col justify-between">
            <div>
              <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 w-fit mb-4">
                <Building2 className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Healthcare Administrators & Compliance</h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                Ensure organizational compliance with immutable audit logging, granular tenant isolation, and strict role guards. Eliminate unauthorized data access between distinct patient records.
              </p>
              <ul className="mt-4 space-y-2 text-xs text-slate-400">
                <li className="flex items-start space-x-2">
                  <ChevronRight className="w-3.5 h-3.5 text-purple-400 shrink-0 mt-0.5" />
                  <span>Tenant-isolated vector payload boundaries</span>
                </li>
                <li className="flex items-start space-x-2">
                  <ChevronRight className="w-3.5 h-3.5 text-purple-400 shrink-0 mt-0.5" />
                  <span>Sanitized audit logging of all clinical inquiries</span>
                </li>
                <li className="flex items-start space-x-2">
                  <ChevronRight className="w-3.5 h-3.5 text-purple-400 shrink-0 mt-0.5" />
                  <span>Zero-cost development and deployment support</span>
                </li>
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800/60 text-[11px] text-purple-300 font-medium">
              Persona: Platform Administrator (`admin@patient360.org`)
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Safety Guardrails */}
      {activeTab === 'safety' && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-5 animate-fade-in">
          <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800/80">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Evidence-Anchored Decision Support</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Patient360 is built as an informational synthesis and research platform. It does not issue autonomous diagnoses or direct treatment commands. Every clinical synthesis requires clinician oversight and provides verified provenance back to original documentation.
            </p>
            <div className="mt-4 space-y-2.5 text-xs text-slate-400">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
                <span>Explicit abstention: Returns refusal if supporting evidence is missing</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
                <span>Exact citation formatting: [Doc: ID, Page: N] citation verification</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
                <span>Prominent regulatory notices on all clinical workspaces</span>
              </div>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-slate-950/60 border border-slate-800/80">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white">Emergency Detection & Prompt Sanitization</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Inquiries containing acute life-threatening signs (such as acute chest pain, anaphylaxis, or stroke symptoms) trigger an emergency escalation banner directing immediate contact with emergency medical services.
            </p>
            <div className="mt-4 space-y-2.5 text-xs text-slate-400">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
                <span>Emergency red-flag detector with immediate escalation guidance</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
                <span>Strict prompt injection sanitization against adversarial overrides</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
                <span>Human review approval gate before agentic summaries are finalized</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: System Highlights */}
      {activeTab === 'architecture' && (
        <div className="mt-6 p-6 rounded-2xl bg-slate-950/60 border border-slate-800/80 animate-fade-in">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">Integrated Platform Capabilities</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed mb-6">
            The platform combines hybrid retrieval, structured information extraction, and secure storage adapters into a cohesive clinical workflow.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="text-xs font-semibold text-teal-400 mb-1">Hybrid Retrieval</div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Reciprocal Rank Fusion merging dense vector cosine similarity (FastEmbed) with sparse keyword search (BM25).
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="text-xs font-semibold text-cyan-400 mb-1">Vector Storage</div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Qdrant vector engine supporting embedded in-memory mode or standalone clusters with isolated tenant filtering.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="text-xs font-semibold text-emerald-400 mb-1">Multi-LLM Gateway</div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Provider-agnostic interface supporting Google Gemini, local offline Ollama (Qwen 4B), and zero-cost mock providers.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="text-xs font-semibold text-purple-400 mb-1">Audit Trail</div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Cryptographic logging of all access, exports, and document reads with automated PII/PHI sanitization.
              </p>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
