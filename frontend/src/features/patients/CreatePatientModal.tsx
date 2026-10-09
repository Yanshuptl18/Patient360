import React, { useState } from 'react';
import { X, UserPlus, Sparkles, AlertCircle } from 'lucide-react';
import { Patient, PatientCreate } from '../../types';
import { useAuth } from '../auth/AuthContext';

interface CreatePatientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPatientCreated: (patient: Patient) => void;
}

export const CreatePatientModal: React.FC<CreatePatientModalProps> = ({
  isOpen,
  onClose,
  onPatientCreated,
}) => {
  const { token } = useAuth();
  const [mrn, setMrn] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [dob, setDob] = useState('1980-01-01');
  const [gender, setGender] = useState('Female');
  const [primaryCondition, setPrimaryCondition] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleGenerateSyntheticMRN = () => {
    const randomSuffix = Math.floor(100000 + Math.random() * 900000);
    setMrn(`SYN-${randomSuffix}`);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mrn.trim() || !firstName.trim() || !lastName.trim()) {
      setError('MRN, First Name, and Last Name are required.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    const payload: PatientCreate = {
      mrn_synthetic: mrn.trim().toUpperCase(),
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      date_of_birth: dob,
      gender,
      primary_condition: primaryCondition.trim() || undefined,
    };

    try {
      const response = await fetch('/api/v1/patients', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail?.message || errorData.detail || 'Failed to create synthetic patient.');
      }

      const created: Patient = await response.json();
      onPatientCreated(created);
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred while creating patient.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-6 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
              <UserPlus className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Register Synthetic Patient</h2>
              <p className="text-xs text-slate-400">Strictly synthetic patient record for clinical evaluation</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-slate-300">Synthetic MRN</label>
              <button
                type="button"
                onClick={handleGenerateSyntheticMRN}
                className="text-[11px] text-teal-400 hover:text-teal-300 flex items-center space-x-1"
              >
                <Sparkles className="w-3 h-3" />
                <span>Auto-Generate</span>
              </button>
            </div>
            <input
              type="text"
              required
              placeholder="e.g. SYN-100293"
              value={mrn}
              onChange={(e) => setMrn(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-teal-500 font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">First Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Eleanor"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Last Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Vance"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Date of Birth</label>
              <input
                type="date"
                required
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Gender</label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-teal-500"
              >
                <option value="Female">Female</option>
                <option value="Male">Male</option>
                <option value="Non-Binary">Non-Binary</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Primary Condition / Diagnosis</label>
            <input
              type="text"
              placeholder="e.g. Metastatic NSCLC with EGFR L858R Mutation"
              value={primaryCondition}
              onChange={(e) => setPrimaryCondition(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-teal-500"
            />
          </div>

          <div className="pt-3 flex items-center justify-end space-x-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-slate-950 text-xs font-semibold shadow-lg shadow-teal-500/20 transition-all flex items-center space-x-1.5"
            >
              {isSubmitting ? (
                <span>Registering...</span>
              ) : (
                <>
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>Register Patient</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
