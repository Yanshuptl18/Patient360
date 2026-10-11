import React, { useState, useEffect } from 'react';
import { Database, Cpu, HardDrive, RefreshCw, CheckCircle2, AlertTriangle, XCircle, Sparkles } from 'lucide-react';
import { HealthResponse } from '../types';

export const HealthStatus: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/health');
      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`);
      }
      const data: HealthResponse = await res.json();
      setHealth(data);
      setLastChecked(new Date());
    } catch (err: any) {
      setError(err.message || 'Failed to reach API gateway');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'UP':
      case 'HEALTHY':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            <span>OPERATIONAL</span>
          </span>
        );
      case 'DEGRADED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3 h-3" />
            <span>DEGRADED</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3 h-3" />
            <span>OFFLINE</span>
          </span>
        );
    }
  };

  const db = health?.components?.database;
  const vector = health?.components?.vector_store;
  const storage = health?.components?.storage;
  const llm = health?.components?.llm_provider;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-800/80 gap-3">
        <div>
          <div className="flex items-center space-x-3">
            <h2 className="text-base font-semibold text-white tracking-tight">System Infrastructure Health</h2>
            {getStatusBadge(health?.status || (loading ? 'UP' : 'DOWN'))}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time operational availability for patient records, clinical search, document archive, and AI synthesis.
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs text-slate-400">
          <span>Checked: {lastChecked.toLocaleTimeString()}</span>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700 disabled:opacity-50 cursor-pointer"
            title="Refresh Status"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-teal-400' : ''}`} />
          </button>
        </div>
      </div>

      {error ? (
        <div className="mt-5 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-3">
          <XCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <div>
            <p className="font-semibold">Clinical Service Notice</p>
            <p className="text-rose-400/80 mt-0.5">{error}. Contact hospital IT or clinical systems administration.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
          {/* Relational Database */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/90 flex flex-col justify-between hover:border-slate-700 transition-all">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-slate-200">Patient Database</h3>
                  <span className="text-[11px] text-slate-400">Encrypted Clinical Records</span>
                </div>
              </div>
              {getStatusBadge(db?.status)}
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
              <span className="truncate max-w-[170px]" title={db?.message || 'Verifying connection...'}>
                {db?.message ? 'Connected & Active' : 'Verifying...'}
              </span>
              <span className="font-mono text-slate-300 font-medium">
                {db?.latency_ms ?? 0} ms
              </span>
            </div>
          </div>

          {/* Semantic Index Engine */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/90 flex flex-col justify-between hover:border-slate-700 transition-all">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg bg-teal-500/10 text-teal-400 border border-teal-500/20">
                  <Cpu className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-slate-200">Semantic Search</h3>
                  <span className="text-[11px] text-slate-400">Contextual Knowledge Engine</span>
                </div>
              </div>
              {getStatusBadge(vector?.status)}
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
              <span className="truncate max-w-[170px]" title={vector?.message || 'Checking vector engine...'}>
                {vector?.message ? 'Ready & Indexed' : 'Checking...'}
              </span>
              <span className="font-mono text-slate-300 font-medium">
                {vector?.latency_ms ?? 0} ms
              </span>
            </div>
          </div>

          {/* Document Storage */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/90 flex flex-col justify-between hover:border-slate-700 transition-all">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  <HardDrive className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-slate-200">Document Archive</h3>
                  <span className="text-[11px] text-slate-400">Verified File Storage</span>
                </div>
              </div>
              {getStatusBadge(storage?.status)}
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
              <span className="truncate max-w-[170px]" title={storage?.message || 'Verifying storage...'}>
                {storage?.message ? 'Securely Mounted' : 'Verifying...'}
              </span>
              <span className="font-mono text-slate-300 font-medium">
                {storage?.latency_ms ?? 0} ms
              </span>
            </div>
          </div>

          {/* LLM Inference Engine */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/90 flex flex-col justify-between hover:border-slate-700 transition-all">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-slate-200">Clinical AI Assistant</h3>
                  <span className="text-[11px] text-slate-400">Evidence Synthesis Active</span>
                </div>
              </div>
              {getStatusBadge(llm?.status || (health ? 'UP' : undefined))}
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
              <span className="truncate max-w-[170px]" title={llm?.message || 'Ready'}>
                {llm?.message ? 'Operational' : 'Ready'}
              </span>
              <span className="font-mono text-slate-300 font-medium">
                {llm?.latency_ms ?? 1} ms
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
