import React, { useState } from 'react';
import {
  Stethoscope,
  HeartPulse,
  Building2,
  UserCheck,
  Server,
  ArrowRight,
  Loader2,
  AlertCircle,
  Check,
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';

interface DemoRoleSelectorProps {
  onSuccess?: () => void;
  onRoleSelected?: (roleKey: string) => void;
  compact?: boolean;
}

interface RoleConfig {
  key: string;
  name: string;
  badge: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
  accentColor: string;
  badgeClass: string;
  iconBg: string;
  borderColor: string;
  buttonBg: string;
  description: string;
  features: string[];
}

const DEMO_ROLES_CONFIG: RoleConfig[] = [
  {
    key: 'doctor',
    name: 'Doctor',
    badge: 'Clinical Reviewer',
    subtitle: 'Dr. Evelyn Reed, MD',
    icon: Stethoscope,
    accentColor: 'text-teal-700',
    badgeClass: 'bg-teal-50 text-teal-800 border-teal-200',
    iconBg: 'bg-teal-50 text-teal-700 border-teal-200',
    borderColor: 'border-slate-200 hover:border-teal-400',
    buttonBg: 'bg-teal-700 hover:bg-teal-800 text-white',
    description: 'Clinical dashboard, authorized patient records, evidence inquiries with exact page citations, and research intelligence.',
    features: ['Patient Dossiers', 'Evidence-Grounded Inquiries', 'Clinical Research Workflows'],
  },
  {
    key: 'nurse',
    name: 'Nurse / Care Coordinator',
    badge: 'Care Coordination',
    subtitle: 'Sarah Jenkins, RN',
    icon: HeartPulse,
    accentColor: 'text-emerald-700',
    badgeClass: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    iconBg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    borderColor: 'border-slate-200 hover:border-emerald-400',
    buttonBg: 'bg-emerald-700 hover:bg-emerald-800 text-white',
    description: 'Care coordination, permitted patient records, medication history, and cross-document conflicting information alerts.',
    features: ['Care Trajectories', 'Conflicting Information', 'Physical Document Records'],
  },
  {
    key: 'hospital_admin',
    name: 'Hospital Administrator',
    badge: 'Executive Governance',
    subtitle: 'Marcus Vance, MHA',
    icon: Building2,
    accentColor: 'text-blue-700',
    badgeClass: 'bg-blue-50 text-blue-800 border-blue-200',
    iconBg: 'bg-blue-50 text-blue-700 border-blue-200',
    borderColor: 'border-slate-200 hover:border-blue-400',
    buttonBg: 'bg-blue-700 hover:bg-blue-800 text-white',
    description: 'Operational overview, patient cohort distributions, document throughput volume, compliance audit logs, and infrastructure status.',
    features: ['Census Overview', 'Document Throughput', 'Compliance Audit Trails'],
  },
  {
    key: 'patient',
    name: 'Patient',
    badge: 'Personal Health Portal',
    subtitle: 'Eleanor Vance (SYNTH-10001)',
    icon: UserCheck,
    accentColor: 'text-sky-700',
    badgeClass: 'bg-sky-50 text-sky-800 border-sky-200',
    iconBg: 'bg-sky-50 text-sky-700 border-sky-200',
    borderColor: 'border-slate-200 hover:border-sky-400',
    buttonBg: 'bg-sky-700 hover:bg-sky-800 text-white',
    description: 'Personal health record access, medical history timeline, plain-language care summaries, and verified medical documents.',
    features: ['Personal Dossier Isolation', 'Plain-Language Summaries', 'Visit & Care Journey'],
  },
  {
    key: 'system_admin',
    name: 'System Administrator',
    badge: 'Infrastructure & Testing',
    subtitle: 'Alex Chen',
    icon: Server,
    accentColor: 'text-purple-700',
    badgeClass: 'bg-purple-50 text-purple-800 border-purple-200',
    iconBg: 'bg-purple-50 text-purple-700 border-purple-200',
    borderColor: 'border-slate-200 hover:border-purple-400',
    buttonBg: 'bg-purple-700 hover:bg-purple-800 text-white',
    description: 'Platform management, service telemetry, quality testing benchmarks, and security access audit logs.',
    features: ['Quality Testing Lab', 'Service Telemetry', 'Security & User Governance'],
  },
];

export const DemoRoleSelector: React.FC<DemoRoleSelectorProps> = ({ onSuccess, onRoleSelected, compact = false }) => {
  const { loginAsDemo, user } = useAuth();
  const [activeRoleKey, setActiveRoleKey] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSelectRole = async (roleKey: string) => {
    setActiveRoleKey(roleKey);
    setErrorMessage(null);
    try {
      await loginAsDemo(roleKey);
      if (onRoleSelected) {
        onRoleSelected(roleKey);
      }
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to sign in as demo user. Please try again.');
      }
    } finally {
      setActiveRoleKey(null);
    }
  };

  return (
    <div className="w-full">
      {/* Error Alert */}
      {errorMessage && (
        <div className="mb-4 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Grid of 5 Demo Roles */}
      <div
        className={`grid gap-4 ${
          compact
            ? 'grid-cols-1 sm:grid-cols-2'
            : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5'
        }`}
      >
        {DEMO_ROLES_CONFIG.map((role) => {
          const Icon = role.icon;
          const isLoadingThis = activeRoleKey === role.key;
          const isCurrentlyActive = user && (
            (role.key === 'doctor' && (user.role === 'doctor' || user.role === 'reviewer')) ||
            (role.key === 'nurse' && user.role === 'nurse') ||
            (role.key === 'hospital_admin' && user.role === 'hospital_admin') ||
            (role.key === 'patient' && user.role === 'patient') ||
            (role.key === 'system_admin' && user.role === 'admin')
          );

          return (
            <div
              key={role.key}
              className={`relative rounded-2xl bg-white border p-5 flex flex-col justify-between transition-all duration-200 shadow-xs hover:shadow-md ${
                isCurrentlyActive
                  ? 'border-teal-600 ring-2 ring-teal-600/20'
                  : role.borderColor
              }`}
            >
              {/* Active Badge if currently logged in */}
              {isCurrentlyActive && (
                <div className="absolute -top-2.5 right-4 px-2 py-0.5 rounded-full bg-teal-700 text-white text-[10px] font-bold flex items-center space-x-1 shadow-xs">
                  <Check className="w-3 h-3" />
                  <span>Active Role</span>
                </div>
              )}

              <div>
                {/* Header: Icon & Role Badge */}
                <div className="flex items-center justify-between mb-3">
                  <div className={`p-2.5 rounded-xl border ${role.iconBg}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${role.badgeClass}`}>
                    {role.badge}
                  </span>
                </div>

                {/* Role Title & Persona */}
                <h3 className="text-base font-bold text-slate-900 tracking-tight leading-snug">
                  {role.name}
                </h3>
                <div className="text-xs text-slate-500 font-medium mt-0.5 mb-2.5">
                  {role.subtitle}
                </div>

                {/* Description */}
                <p className="text-xs text-slate-600 leading-relaxed mb-4">
                  {role.description}
                </p>

                {/* Features Pills */}
                <div className="space-y-1.5 mb-5">
                  {role.features.map((feat) => (
                    <div
                      key={feat}
                      className="text-[11px] text-slate-700 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg flex items-center space-x-1.5"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-teal-600" />
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Button: Continue as Demo User */}
              <button
                type="button"
                disabled={isLoadingThis}
                onClick={() => handleSelectRole(role.key)}
                className={`w-full py-2.5 px-3 rounded-xl text-xs font-semibold flex items-center justify-center space-x-2 transition-all shadow-xs disabled:opacity-60 cursor-pointer ${role.buttonBg}`}
              >
                {isLoadingThis ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Signing in...</span>
                  </>
                ) : isCurrentlyActive ? (
                  <>
                    <span>Current Session</span>
                    <Check className="w-3.5 h-3.5" />
                  </>
                ) : (
                  <>
                    <span>Continue as Demo User</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
