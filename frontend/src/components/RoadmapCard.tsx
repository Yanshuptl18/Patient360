import React from 'react';
import { CheckCircle2, Clock, CircleDot, ChevronRight } from 'lucide-react';
import { PhaseInfo } from '../types';

interface RoadmapCardProps {
  phases: PhaseInfo[];
}

export const RoadmapCard: React.FC<RoadmapCardProps> = ({ phases }) => {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm mt-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-base font-semibold text-white tracking-tight">Implementation Roadmap & Progression</h2>
          <p className="text-xs text-slate-400 mt-0.5">Strict phase-by-phase execution tracking under the 13-Point Definition of Done.</p>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-mono">
          Phase 2 / 15
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 mt-5">
        {phases.map((phase) => {
          let statusBadge;
          let cardBorder = "border-slate-800/80 bg-slate-950/40";

          if (phase.status === 'Verified') {
            cardBorder = "border-emerald-500/30 bg-emerald-950/10";
            statusBadge = (
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-2.5 h-2.5" />
                <span>VERIFIED</span>
              </span>
            );
          } else if (phase.status === 'In Progress') {
            cardBorder = "border-teal-500/50 bg-teal-950/20 ring-1 ring-teal-500/30";
            statusBadge = (
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/30 animate-pulse">
                <CircleDot className="w-2.5 h-2.5" />
                <span>IN PROGRESS</span>
              </span>
            );
          } else {
            statusBadge = (
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
                <Clock className="w-2.5 h-2.5" />
                <span>PLANNED</span>
              </span>
            );
          }

          return (
            <div
              key={phase.number}
              className={`p-3.5 rounded-xl border ${cardBorder} flex flex-col justify-between transition-all hover:border-slate-700`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[11px] font-mono text-slate-400 font-semibold">
                    PHASE {String(phase.number).padStart(2, '0')}
                  </span>
                  {statusBadge}
                </div>
                <h3 className="text-xs font-semibold text-slate-100 tracking-tight leading-snug">
                  {phase.name}
                </h3>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  {phase.description}
                </p>
              </div>

              <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-400">
                <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                  {phase.tag}
                </span>
                <span className="text-slate-500 flex items-center">
                  <span>Details</span>
                  <ChevronRight className="w-3 h-3 ml-0.5" />
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
