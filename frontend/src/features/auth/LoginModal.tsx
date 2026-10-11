import React, { useState } from 'react';
import { X, Lock, Mail, AlertCircle, ArrowRight, CheckCircle2, User, Stethoscope, RefreshCw, KeyRound } from 'lucide-react';
import { useAuth } from './AuthContext';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose }) => {
  const { requestOtp, verifyOtp } = useAuth();
  const [authMode, setAuthMode] = useState<'signin' | 'register'>('signin');
  const [step, setStep] = useState<'input' | 'verify'>('input');

  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<'reviewer' | 'researcher' | 'admin'>('reviewer');
  const [otp, setOtp] = useState('');
  const [receivedOtp, setReceivedOtp] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleReset = () => {
    setStep('input');
    setOtp('');
    setReceivedOtp(null);
    setErrorMessage(null);
    setSuccessNotice(null);
  };

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !email.includes('@')) {
      setErrorMessage('Please enter a valid clinical or institutional email address.');
      return;
    }

    if (authMode === 'register' && !fullName.trim()) {
      setErrorMessage('Please enter your full name and professional title.');
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await requestOtp(email.trim(), authMode === 'register' ? fullName.trim() : undefined, role);
      setSuccessNotice(res.message);
      if (res.dev_otp) {
        setReceivedOtp(res.dev_otp);
      }
      setStep('verify');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to send verification code. Please verify your email.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otp || otp.length !== 6) {
      setErrorMessage('Please enter the 6-digit verification code.');
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    try {
      await verifyOtp(email.trim(), otp.trim(), authMode === 'register' ? fullName.trim() : undefined, role);
      onClose();
      handleReset();
    } catch (err: any) {
      setErrorMessage(err.message || 'Invalid or expired verification code.');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoFillOtp = () => {
    if (receivedOtp) {
      setOtp(receivedOtp);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        {/* Close Button */}
        <button
          onClick={() => {
            onClose();
            handleReset();
          }}
          className="absolute top-5 right-5 p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header Icon & Title */}
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2.5 rounded-2xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Clinical Access Portal</h2>
            <p className="text-xs text-slate-400">Secure Healthcare Provider Verification</p>
          </div>
        </div>

        {/* Tab Switcher: Sign In vs Register */}
        {step === 'input' && (
          <div className="flex items-center p-1 bg-slate-950/80 border border-slate-800 rounded-2xl mb-6">
            <button
              type="button"
              onClick={() => {
                setAuthMode('signin');
                setErrorMessage(null);
              }}
              className={`flex-1 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
                authMode === 'signin'
                  ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setAuthMode('register');
                setErrorMessage(null);
              }}
              className={`flex-1 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
                authMode === 'register'
                  ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Register New Clinician
            </button>
          </div>
        )}

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-5 p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Success Notice */}
        {successNotice && step === 'verify' && (
          <div className="mb-4 p-3 rounded-2xl bg-teal-500/10 border border-teal-500/20 text-teal-300 text-xs flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-teal-400" />
            <span>{successNotice}</span>
          </div>
        )}

        {/* STEP 1: Enter Email & Details */}
        {step === 'input' ? (
          <form onSubmit={handleRequestOtp} className="space-y-4">
            {authMode === 'register' && (
              <>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Full Name & Clinical Title
                  </label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. Dr. Jane Smith, MD"
                      className="w-full pl-10 pr-4 py-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 transition-colors"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Primary Healthcare Role
                  </label>
                  <div className="relative">
                    <Stethoscope className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                    <select
                      value={role}
                      onChange={(e) => setRole(e.target.value as any)}
                      className="w-full pl-10 pr-4 py-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-teal-500 transition-colors"
                    >
                      <option value="reviewer">Physician / Clinical Reviewer</option>
                      <option value="researcher">Medical Researcher / Academic</option>
                      <option value="admin">Clinical Director / Administrator</option>
                    </select>
                  </div>
                </div>
              </>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Clinical Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="doctor@hospital.org"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 transition-colors"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1.5">
                A 6-digit one-time security code (OTP) will be dispatched to this address.
              </p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3 px-4 bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-slate-950 font-semibold text-xs rounded-xl transition-all flex items-center justify-center space-x-2 shadow-lg shadow-teal-500/20 cursor-pointer"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Dispatching Security Code...</span>
                </>
              ) : (
                <>
                  <span>Send Verification Code (OTP)</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        ) : (
          /* STEP 2: Verify OTP */
          <form onSubmit={handleVerifyOtp} className="space-y-4">
            <div className="p-4 rounded-2xl bg-teal-500/10 border border-teal-500/20 text-xs text-teal-300 space-y-1">
              <div className="flex items-center space-x-2 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-teal-400" />
                <span>Verification Code Sent</span>
              </div>
              <p className="text-slate-300">
                A 6-digit passcode was dispatched to <span className="font-semibold text-white">{email}</span>.
              </p>
            </div>

            {/* Simulated OTP Helper for Immediate Access */}
            {receivedOtp && (
              <div className="p-3 rounded-xl bg-slate-950/80 border border-cyan-500/30 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2 text-cyan-300">
                  <KeyRound className="w-4 h-4 text-cyan-400" />
                  <span>Your Code: <strong className="font-mono text-white text-sm tracking-widest">{receivedOtp}</strong></span>
                </div>
                <button
                  type="button"
                  onClick={handleAutoFillOtp}
                  className="px-2.5 py-1 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 font-medium text-[11px] transition-colors cursor-pointer"
                >
                  Auto-fill Code
                </button>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Enter 6-Digit Passcode
              </label>
              <input
                type="text"
                required
                maxLength={6}
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                placeholder="000000"
                className="w-full text-center tracking-[0.5em] font-mono text-xl py-3 bg-slate-950/80 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-teal-500 transition-colors"
              />
            </div>

            <div className="flex items-center space-x-3 pt-2">
              <button
                type="button"
                onClick={handleReset}
                className="flex-1 py-2.5 px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs rounded-xl transition-all cursor-pointer"
              >
                Change Email
              </button>
              <button
                type="submit"
                disabled={loading || otp.length !== 6}
                className="flex-1 py-2.5 px-3 bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-slate-950 font-semibold text-xs rounded-xl transition-all flex items-center justify-center space-x-2 shadow-lg shadow-teal-500/20 cursor-pointer"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Verifying...</span>
                  </>
                ) : (
                  <>
                    <span>Verify & Enter</span>
                    <CheckCircle2 className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        )}

        {/* Footer Note */}
        <div className="mt-6 pt-4 border-t border-slate-800/60 text-center text-[11px] text-slate-500">
          Protected under HIPAA clinical privacy and institutional security protocols.
        </div>
      </div>
    </div>
  );
};
