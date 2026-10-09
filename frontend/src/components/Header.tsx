import React from 'react';
import { Activity, ShieldAlert, BookOpen, Terminal } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-tr from-teal-600 to-cyan-500 rounded-xl shadow-lg shadow-teal-500/20 text-white">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">Patient360</span>
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-teal-500/10 text-teal-400 border border-teal-500/20">
                Phase 2 Foundation
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Healthcare Intelligence & Grounded RAG Platform</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="hidden md:flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Informational & Research Use Only</span>
          </div>

          <a
            href="http://127.0.0.1:8000/api/v1/docs"
            target="_blank"
            rel="noreferrer"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors border border-slate-700"
          >
            <BookOpen className="w-3.5 h-3.5 text-teal-400" />
            <span>Swagger API</span>
          </a>

          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-800/80 text-slate-300 text-xs border border-slate-700/60 font-mono">
            <Terminal className="w-3 h-3 text-cyan-400" />
            <span>v0.1.0</span>
          </div>
        </div>
      </div>
    </header>
  );
};
