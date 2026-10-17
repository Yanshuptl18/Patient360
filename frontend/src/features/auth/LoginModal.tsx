import React, { useState } from 'react';
import { X, Lock, Mail, AlertCircle, ArrowRight, CheckCircle2, User, Stethoscope, RefreshCw, KeyRound, Sparkles } from 'lucide-react';
import { useAuth } from './AuthContext';
import { DemoRoleSelector } from '../../components/DemoRoleSelector';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose }) => {
  const { requestOtp, verifyOtp } = useAuth();
  const [modalTab, setModalTab] = useState<'demo' | 'otp'>('demo');
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
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message || 'Failed to send verification code. Please verify your email.');
      } else {
        setErrorMessage('Failed to send verification code. Please verify your email.');
      }
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
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message || 'Invalid or expired verification code.');
      } else {
        setErrorMessage('Invalid or expired verification code.');
      }
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className={`bg-white border border-slate-200 rounded-3xl w-full p-6 sm:p-8 shadow-xl relative my-8 transition-all text-slate-900 ${modalTab === 'demo' ? 'max-w-5xl' : 'max-w-lg'}`}>
        {/* Close Button */}
        <button
          onClick={() => {
            onClose();
            handleReset();
          }}
          className="absolute top-5 right-5 p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header Icon & Title */}
        <div className="flex items-center space-x-3 mb-5">
          <div className="p-2.5 rounded-2xl bg-teal-50 text-teal-700 border border-teal-200">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Access Portal</h2>
            <p className="text-xs text-slate-500">One-Click Demonstration or Institutional Verification</p>
          </div>
        </div>

        {/* Main Tab Switcher: Demo Roles vs Email OTP */}
        <div className="flex items-center p-1 bg-slate-100 border border-slate-200 rounded-2xl mb-6 max-w-md">
          <button
            type="button"
            onClick={() => {
              setModalTab('demo');
              setErrorMessage(null);
            }}
            className={`flex-1 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer flex items-center justify-center space-x-1.5 ${
              modalTab === 'demo'
                ? 'bg-white text-teal-800 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-teal-700" />
            <span>One-Click Demo Roles</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setModalTab('otp');
              setErrorMessage(null);
            }}
            className={`flex-1 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer flex items-center justify-center space-x-1.5 ${
              modalTab === 'otp'
                ? 'bg-white text-teal-800 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Mail className="w-3.5 h-3.5 text-teal-700" />
            <span>Email OTP Login</span>
          </button>
        </div>

        {/* TAB 1: ONE-CLICK DEMO SELECTOR */}
        {modalTab === 'demo' ? (
          <div>
            <div className="mb-4 text-xs text-slate-600">
              Select any role below to enter the application immediately with predefined permissions and patient records:
            </div>
            <DemoRoleSelector onSuccess={onClose} compact />
          </div>
        ) : (
          /* TAB 2: EMAIL OTP FLOW */
          <div>
            {step === 'input' && (
              <div className="flex items-center p-1 bg-slate-100 border border-slate-200 rounded-2xl mb-6">
                <button
                  type="button"
                  onClick={() => {
                    setAuthMode('signin');
                    setErrorMessage(null);
                  }}
                  className={`flex-1 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
                    authMode === 'signin'
                      ? 'bg-white text-teal-800 shadow-xs font-bold'
                      : 'text-slate-600 hover:text-slate-900'
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
                      ? 'bg-white text-teal-800 shadow-xs font-bold'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Register New Clinician
                </button>
              </div>
            )}

            {/* Error Alert */}
            {errorMessage && (
              <div className="mb-5 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2.5">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Success Notice */}
            {successNotice && (
              <div className="mb-5 p-3.5 rounded-2xl bg-teal-50 border border-teal-200 text-teal-800 text-xs flex items-center space-x-2.5">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-teal-700" />
                <span>{successNotice}</span>
              </div>
            )}

            {/* STEP 1: INPUT FORM */}
            {step === 'input' ? (
              <form onSubmit={handleRequestOtp} className="space-y-4">
                {authMode === 'register' && (
                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1.5">
                      Full Name & Clinical Credentials
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        required
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder="e.g. Dr. Jordan Hayes, MD"
                        className="w-full pl-9 pr-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-slate-900 text-xs placeholder-slate-400 focus:outline-none focus:border-teal-600 transition-colors"
                      />
                      <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">
                    Institutional Email Address
                  </label>
                  <div className="relative">
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="physician@hospital.org"
                      className="w-full pl-9 pr-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-slate-900 text-xs placeholder-slate-400 focus:outline-none focus:border-teal-600 transition-colors"
                    />
                    <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1.5">
                    We will send a one-time secure 6-digit verification code to this email.
                  </p>
                </div>

                {authMode === 'register' && (
                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1.5">
                      Clinical Role / Specialization
                    </label>
                    <div className="relative">
                      <select
                        value={role}
                        onChange={(e) => setRole(e.target.value as 'reviewer' | 'researcher' | 'admin')}
                        className="w-full pl-9 pr-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-slate-900 text-xs focus:outline-none focus:border-teal-600 transition-colors cursor-pointer"
                      >
                        <option value="reviewer">Clinical Reviewer / Physician (Patient Records & Synthesis)</option>
                        <option value="researcher">Clinical Researcher (Trials & Cross-Study Matrices)</option>
                        <option value="admin">Department Security / Administrator</option>
                      </select>
                      <Stethoscope className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    </div>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-2 py-2.5 px-4 bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white font-semibold text-xs rounded-xl transition-all flex items-center justify-center space-x-2 shadow-xs cursor-pointer"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Sending Verification Code...</span>
                    </>
                  ) : (
                    <>
                      <span>{authMode === 'signin' ? 'Send Passcode' : 'Register & Send Passcode'}</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            ) : (
              /* STEP 2: VERIFICATION FORM */
              <form onSubmit={handleVerifyOtp} className="space-y-4">
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs">
                  <div className="text-slate-500">Verification code sent to:</div>
                  <div className="font-semibold text-slate-900 mt-0.5">{email}</div>
                </div>

                {/* Simulated OTP Helper */}
                {receivedOtp && (
                  <div className="p-3 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2 text-teal-800">
                      <KeyRound className="w-4 h-4 text-teal-700" />
                      <span>Your Code: <strong className="font-mono text-slate-900 text-sm tracking-widest">{receivedOtp}</strong></span>
                    </div>
                    <button
                      type="button"
                      onClick={handleAutoFillOtp}
                      className="px-2.5 py-1 rounded-lg bg-teal-100 hover:bg-teal-200 text-teal-800 font-medium text-[11px] transition-colors cursor-pointer"
                    >
                      Auto-fill Code
                    </button>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">
                    Enter 6-Digit Passcode
                  </label>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                    placeholder="000000"
                    className="w-full text-center tracking-[0.5em] font-mono text-xl py-3 bg-white border border-slate-300 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:border-teal-600 transition-colors"
                  />
                </div>

                <div className="flex items-center space-x-3 pt-2">
                  <button
                    type="button"
                    onClick={handleReset}
                    className="flex-1 py-2.5 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl transition-all cursor-pointer"
                  >
                    Change Email
                  </button>
                  <button
                    type="submit"
                    disabled={loading || otp.length !== 6}
                    className="flex-1 py-2.5 px-3 bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white font-semibold text-xs rounded-xl transition-all flex items-center justify-center space-x-2 shadow-xs cursor-pointer"
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
          </div>
        )}

        {/* Footer Note */}
        <div className="mt-6 pt-4 border-t border-slate-100 text-center text-[11px] text-slate-500">
          Protected under institutional security and patient confidentiality protocols.
        </div>
      </div>
    </div>
  );
};
