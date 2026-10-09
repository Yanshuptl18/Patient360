import React, { useState } from 'react';
import { X, Lock, Mail, AlertCircle, ArrowRight } from 'lucide-react';
import { useAuth } from './AuthContext';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const PRESET_PERSONAS = [
  {
    name: 'Dr. Evelyn Reed',
    email: 'reviewer@patient360.org',
    role: 'Clinical Reviewer',
    description: 'Access patient records, clinical timelines, and grounded citations.',
    badgeClass: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  },
  {
    name: 'Dr. Marcus Vance',
    email: 'researcher@patient360.org',
    role: 'Medical Researcher',
    description: 'Literature retrieval, comparative trial matrices, evidence synthesis.',
    badgeClass: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  },
  {
    name: 'Sarah Jenkins',
    email: 'admin@patient360.org',
    role: 'Platform Administrator',
    description: 'Platform configuration, RBAC permissions, audit log review.',
    badgeClass: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  },
  {
    name: 'Alex Chen',
    email: 'demo@patient360.org',
    role: 'Demo User',
    description: 'Explore pre-seeded synthetic patient records and evaluation metrics.',
    badgeClass: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  },
];

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('Patient360Secure!');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage(null);
    try {
      await login(email, password);
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPreset = async (presetEmail: string) => {
    setEmail(presetEmail);
    setLoading(true);
    setErrorMessage(null);
    try {
      await login(presetEmail, 'Patient360Secure!');
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative overflow-hidden">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center space-x-2.5 mb-1">
          <div className="p-2 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">Authenticate Access</h2>
            <p className="text-xs text-slate-400">Server-Side Role-Based Access Control (RBAC)</p>
          </div>
        </div>

        {errorMessage && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Quick Demo Persona Presets */}
        <div className="mt-5">
          <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
            Select a Demo Persona (1-Click Authenticate):
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {PRESET_PERSONAS.map((p) => (
              <button
                key={p.email}
                type="button"
                onClick={() => handleSelectPreset(p.email)}
                disabled={loading}
                className="p-3 rounded-xl border border-slate-800 bg-slate-950/60 hover:bg-slate-800/80 hover:border-slate-700 text-left transition-all group disabled:opacity-50"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-white group-hover:text-teal-400 transition-colors">
                    {p.name}
                  </span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${p.badgeClass}`}>
                    {p.role.split(' ')[0]}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-1">{p.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div className="relative my-5">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-800" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="px-2 bg-slate-900 text-slate-500">or enter credentials</span>
          </div>
        </div>

        {/* Manual Credentials Form */}
        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@patient360.org"
                className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 px-4 bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-500 hover:to-cyan-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-teal-500/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        <p className="mt-4 text-[11px] text-center text-slate-500">
          Default password for all synthetic demonstration personas is <code className="text-teal-400 font-mono">Patient360Secure!</code>
        </p>
      </div>
    </div>
  );
};
