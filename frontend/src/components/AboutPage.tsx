import React from 'react';
import {
  FileText,
  Clock,
  Search,
  BookOpen,
  CheckCircle2,
  ShieldCheck,
  ArrowRight,
  ChevronDown,
  Layers,
  FileCheck,
  AlertCircle,
  Eye,
  GitCompare,
  Lock,
  Stethoscope,
  HeartPulse,
} from 'lucide-react';

interface AboutPageProps {
  onExploreWorkspace: () => void;
  onOpenSignIn: () => void;
}

export const AboutPage: React.FC<AboutPageProps> = ({
  onExploreWorkspace,
  onOpenSignIn,
}) => {
  const scrollToFeatures = () => {
    const el = document.getElementById('what-patient360-helps-you-do');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="space-y-16 py-4 animate-fade-in text-slate-900">
      {/* A. Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-white border border-slate-200 shadow-sm p-8 sm:p-12 lg:p-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-800 text-xs font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
              <span>Evidence-Grounded Clinical Intelligence</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
              Medical evidence, <span className="text-teal-700">brought together.</span>
            </h1>

            <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl">
              Explore medical records, understand patient histories, and discover evidence from research documents in one organized workspace.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                type="button"
                onClick={onExploreWorkspace}
                className="px-5 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-medium text-sm flex items-center space-x-2 shadow-sm transition-all cursor-pointer"
              >
                <span>Explore the workspace</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={scrollToFeatures}
                className="px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-sm flex items-center space-x-2 border border-slate-200 transition-all cursor-pointer"
              >
                <span>Discover what Patient360 can do</span>
                <ChevronDown className="w-4 h-4 text-slate-500" />
              </button>
            </div>

            <div className="pt-4 flex flex-wrap items-center gap-6 text-xs text-slate-500 border-t border-slate-100">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-teal-600" />
                <span>Zero autonomous diagnosis</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-teal-600" />
                <span>Exact page-level citations</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-teal-600" />
                <span>Server-enforced access controls</span>
              </div>
            </div>
          </div>

          {/* Elegant Connected Records Illustration (No robot illustration) */}
          <div className="lg:col-span-5 relative">
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200 text-xs font-semibold text-slate-700">
                <span className="flex items-center space-x-1.5">
                  <FileText className="w-4 h-4 text-teal-700" />
                  <span>Clinical Records & Evidence Graph</span>
                </span>
                <span className="px-2 py-0.5 rounded bg-teal-100 text-teal-800 text-[10px]">Verified</span>
              </div>

              {/* Connected node card 1: Patient Note */}
              <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-xs flex items-start space-x-3">
                <div className="p-2 rounded-lg bg-teal-50 text-teal-700 mt-0.5 shrink-0">
                  <Stethoscope className="w-4 h-4" />
                </div>
                <div className="text-xs">
                  <div className="font-semibold text-slate-800">Discharge Summary & Pathology</div>
                  <div className="text-slate-500 mt-0.5">Egfr Exon 19 Deletion identified • Page 2</div>
                </div>
              </div>

              {/* Connecting indicator */}
              <div className="flex justify-center -my-1">
                <div className="w-0.5 h-4 bg-teal-300"></div>
              </div>

              {/* Connected node card 2: Longitudinal Timeline */}
              <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-xs flex items-start space-x-3">
                <div className="p-2 rounded-lg bg-blue-50 text-blue-700 mt-0.5 shrink-0">
                  <Clock className="w-4 h-4" />
                </div>
                <div className="text-xs">
                  <div className="font-semibold text-slate-800">Longitudinal Timeline Event</div>
                  <div className="text-slate-500 mt-0.5">Prior cardiac stent 2021-08-14 • No contradiction</div>
                </div>
              </div>

              {/* Connecting indicator */}
              <div className="flex justify-center -my-1">
                <div className="w-0.5 h-4 bg-teal-300"></div>
              </div>

              {/* Connected node card 3: Research Evidence */}
              <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-xs flex items-start space-x-3">
                <div className="p-2 rounded-lg bg-indigo-50 text-indigo-700 mt-0.5 shrink-0">
                  <BookOpen className="w-4 h-4" />
                </div>
                <div className="text-xs">
                  <div className="font-semibold text-slate-800">Biomedical Clinical Study</div>
                  <div className="text-slate-500 mt-0.5">FLAURA Phase III Trial • Osimertinib vs Standard EGFR-TKI</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* B. The Problem */}
      <section className="rounded-3xl bg-white border border-slate-200 p-8 sm:p-12 shadow-sm">
        <div className="max-w-3xl">
          <div className="text-xs uppercase font-bold tracking-wider text-teal-800 mb-2">
            The Healthcare Challenge
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Critical medical details become scattered across disconnected documents.
          </h2>
          <p className="mt-4 text-sm sm:text-base text-slate-600 leading-relaxed">
            In routine hospital care and clinical research, patient data is frequently divided across disparate clinical notes, outpatient consultation letters, laboratory panels, imaging reports, and scientific trials. Clinicians must manually cross-reference dozens of PDF pages under tight time constraints.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-700 border border-amber-200 flex items-center justify-center mb-3">
              <Layers className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900">Fragmented Records</h3>
            <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
              Discharge summaries, pathology findings, and clinic visit notes often live in separate files, making comprehensive evaluation slow and error-prone.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="w-9 h-9 rounded-xl bg-rose-50 text-rose-700 border border-rose-200 flex items-center justify-center mb-3">
              <AlertCircle className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900">Unnoticed Conflicts</h3>
            <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
              Conflicting medication dosages, recorded allergy dates, or opposing clinical notes across years can easily go undetected without chronological alignment.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-700 border border-blue-200 flex items-center justify-center mb-3">
              <BookOpen className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900">Disconnected Research</h3>
            <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
              Connecting specific patient molecular profiles or comorbidities with emerging trial literature requires hours of manual database searches.
            </p>
          </div>
        </div>
      </section>

      {/* C. What Patient360 Helps You Do (8 Feature Cards) */}
      <section id="what-patient360-helps-you-do" className="space-y-6">
        <div>
          <div className="text-xs uppercase font-bold tracking-wider text-teal-800 mb-2">
            Clinical Capabilities
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            What Patient360 helps you accomplish
          </h2>
          <p className="text-sm text-slate-600 mt-1 max-w-2xl">
            Eight focused workflows designed for doctors, care teams, and biomedical researchers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* Card 1 */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-teal-300 hover:shadow-md transition-all flex flex-col justify-between">
            <div>
              <div className="w-9 h-9 rounded-xl bg-teal-50 text-teal-700 border border-teal-200 flex items-center justify-center mb-3">
                <FileText className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-900">1. Organizing Patient Records</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Centralize medical PDFs into structured patient profiles with server-enforced access boundaries and tamper-evident SHA-256 verification.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] font-medium text-teal-700">
              Implemented & Verified
            </div>
          </div>

          {/* Card 2 */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-teal-300 hover:shadow-md transition-all flex flex-col justify-between">
            <div>
              <div className="w-9 h-9 rounded-xl bg-teal-50 text-teal-700 border border-teal-200 flex items-center justify-center mb-3">
                <Search className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-900">2. Asking Questions About Records</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Query patient files in plain language to locate medications, previous procedures, pathology findings, and lab panels in seconds.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] font-medium text-teal-700">
              Implemented & Verified
            </div>
          </div>

          {/* Card 3 */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-teal-300 hover:shadow-md transition-all flex flex-col justify-between">
            <div>
              <div className="w-9 h-9 rounded-xl bg-teal-50 text-teal-700 border border-teal-200 flex items-center justify-center mb-3">
                <Eye className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-900">3. Finding Supporting Evidence</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Every generated statement links directly to its source document, exact page number, and original quotation for clinical validation.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] font-medium text-teal-700">
              Implemented & Verified
            </div>
          </div>

          {/* Card 4 */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-teal-300 hover:shadow-md transition-all flex flex-col justify-between">
            <div>
              <div className="w-9 h-9 rounded-xl bg-teal-50 text-teal-700 border border-teal-200 flex items-center justify-center mb-3">
                <Clock className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-900">4. Viewing Histories Chronologically</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Reconstruct longitudinal care journeys across encounters, diagnoses, procedures, and prescriptions in a clear timeline view.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] font-medium text-teal-700">
              Implemented & Verified
            </div>
          </div>

          {/* Card 5 */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-teal-300 hover:shadow-md transition-all flex flex-col justify-between">
            <div>
              <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-700 border border-amber-200 flex items-center justify-center mb-3">
                <AlertCircle className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-900">5. Identifying Conflicting Information</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Automatically detect and flag discordant dates, conflicting dosages, and opposing statements across differing clinical encounters.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] font-medium text-teal-700">
              Implemented & Verified
            </div>
          </div>

          {/* Card 6 */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-teal-300 hover:shadow-md transition-all flex flex-col justify-between">
            <div>
              <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center justify-center mb-3">
                <GitCompare className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-900">6. Comparing Biomedical Studies</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Extract structured PICO metrics from clinical trials and compare outcomes, sample sizes, and limitations side by side.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] font-medium text-teal-700">
              Implemented & Verified
            </div>
          </div>

          {/* Card 7 */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-teal-300 hover:shadow-md transition-all flex flex-col justify-between">
            <div>
              <div className="w-9 h-9 rounded-xl bg-teal-50 text-teal-700 border border-teal-200 flex items-center justify-center mb-3">
                <FileCheck className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-900">7. Preparing Evidence Summaries</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Compile comprehensive cross-document dossiers and clinical findings with complete references into portable Markdown reports.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] font-medium text-teal-700">
              Implemented & Verified
            </div>
          </div>

          {/* Card 8 */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-teal-300 hover:shadow-md transition-all flex flex-col justify-between">
            <div>
              <div className="w-9 h-9 rounded-xl bg-teal-50 text-teal-700 border border-teal-200 flex items-center justify-center mb-3">
                <HeartPulse className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-900">8. Reviewing Findings Before Approval</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Multi-step investigations require clinician review and approval gates before any synthesized report is accepted as clinical reference.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] font-medium text-teal-700">
              Implemented & Verified
            </div>
          </div>
        </div>
      </section>

      {/* D. How It Works (Simple 5-Step Visual Sequence) */}
      <section className="rounded-3xl bg-white border border-slate-200 p-8 sm:p-12 shadow-sm">
        <div className="max-w-2xl mb-8">
          <div className="text-xs uppercase font-bold tracking-wider text-teal-800 mb-2">
            Workflow Architecture
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            How Patient360 works in clinical practice
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            A transparent five-step process ensuring total data provenance from upload to clinical sign-off.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
            <div>
              <div className="w-8 h-8 rounded-full bg-teal-700 text-white text-xs font-bold flex items-center justify-center mb-3">
                1
              </div>
              <h4 className="text-xs font-bold text-slate-900">Add Documents</h4>
              <p className="text-[11px] text-slate-600 mt-1.5 leading-relaxed">
                Upload authorized clinical PDFs (up to 25 MB) with tamper-evident cryptographic validation.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
            <div>
              <div className="w-8 h-8 rounded-full bg-teal-700 text-white text-xs font-bold flex items-center justify-center mb-3">
                2
              </div>
              <h4 className="text-xs font-bold text-slate-900">Organize & Examine</h4>
              <p className="text-[11px] text-slate-600 mt-1.5 leading-relaxed">
                Patient360 parses sections, indexes clinical events, and extracts timeline dates.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
            <div>
              <div className="w-8 h-8 rounded-full bg-teal-700 text-white text-xs font-bold flex items-center justify-center mb-3">
                3
              </div>
              <h4 className="text-xs font-bold text-slate-900">Ask or Explore</h4>
              <p className="text-[11px] text-slate-600 mt-1.5 leading-relaxed">
                Inquire about medications, lab trends, previous surgeries, or longitudinal history.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
            <div>
              <div className="w-8 h-8 rounded-full bg-teal-700 text-white text-xs font-bold flex items-center justify-center mb-3">
                4
              </div>
              <h4 className="text-xs font-bold text-slate-900">Review Evidence</h4>
              <p className="text-[11px] text-slate-600 mt-1.5 leading-relaxed">
                Examine answers side by side with original source quotations and physical PDF page numbers.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
            <div>
              <div className="w-8 h-8 rounded-full bg-teal-700 text-white text-xs font-bold flex items-center justify-center mb-3">
                5
              </div>
              <h4 className="text-xs font-bold text-slate-900">Approve Findings</h4>
              <p className="text-[11px] text-slate-600 mt-1.5 leading-relaxed">
                The licensed clinician reviews, validates, and approves the synthesized summary.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* E. Responsible Use & F. Privacy and Trust */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 sm:p-8 rounded-3xl bg-white border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-700 border border-amber-200 flex items-center justify-center mb-4">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">Responsible Clinical Use</h3>
          <p className="text-xs sm:text-sm text-slate-600 mt-2 leading-relaxed">
            Patient360 is an informational retrieval and research synthesis platform. It is explicitly designed to assist clinicians in navigating complex medical documentation.
          </p>
          <div className="mt-4 p-3.5 rounded-xl bg-amber-50/60 border border-amber-200 text-xs text-amber-900 space-y-1.5">
            <div className="font-semibold flex items-center space-x-1.5">
              <AlertCircle className="w-4 h-4 text-amber-700 shrink-0" />
              <span>Clinical Mandate</span>
            </div>
            <p>
              It does not replace professional clinical judgment, provide autonomous diagnoses, or prescribe treatments. All AI-generated summaries must be verified against original source documents prior to clinical decision-making.
            </p>
          </div>
        </div>

        <div className="p-6 sm:p-8 rounded-3xl bg-white border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 border border-teal-200 flex items-center justify-center mb-4">
            <Lock className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">Privacy & Access Controls</h3>
          <p className="text-xs sm:text-sm text-slate-600 mt-2 leading-relaxed">
            Patient information is strictly isolated by role-based access controls enforced directly on the server.
          </p>
          <ul className="mt-4 space-y-2 text-xs text-slate-600">
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
              <span>Server-enforced patient cohort boundaries prevent cross-patient data exposure.</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
              <span>Immutable cryptographic hash auditing ensures document integrity.</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
              <span>Synthetic demonstration data only is utilized for portfolio testing.</span>
            </li>
          </ul>
        </div>
      </section>

      {/* G. Final Call to Action */}
      <section className="rounded-3xl bg-teal-900 text-white p-8 sm:p-12 text-center shadow-md">
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
          Ready to explore the clinical workspace?
        </h2>
        <p className="text-sm sm:text-base text-teal-100 mt-2 max-w-xl mx-auto">
          Sign in with your institutional credentials or select a one-click demonstration role to review patient records, timelines, and research synthesis.
        </p>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <button
            type="button"
            onClick={onExploreWorkspace}
            className="px-6 py-2.5 rounded-xl bg-white hover:bg-slate-100 text-teal-900 font-semibold text-sm transition-all shadow-sm cursor-pointer"
          >
            Enter Workspace
          </button>
          <button
            type="button"
            onClick={onOpenSignIn}
            className="px-6 py-2.5 rounded-xl bg-teal-800 hover:bg-teal-700 text-white font-medium text-sm border border-teal-700 transition-all cursor-pointer"
          >
            Select Demo Role
          </button>
        </div>
      </section>
    </div>
  );
};
