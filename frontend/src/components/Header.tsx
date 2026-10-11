import React from 'react';
import { Activity, ShieldAlert, BookOpen, LogOut, LogIn } from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';

interface HeaderProps {
  onOpenLogin: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenLogin }) => {
  const { user, isAuthenticated, logout } = useAuth();

  const getRoleBadge = (role?: string) => {
    switch (role) {
      case 'admin':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case 'reviewer':
        return 'bg-teal-500/10 text-teal-400 border-teal-500/20';
      case 'researcher':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      default:
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
    }
  };

  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-tr from-teal-600 to-cyan-500 rounded-xl shadow-lg shadow-teal-500/20 text-white">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">Patient360</span>
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-teal-500/10 text-teal-400 border border-teal-500/20">
                RBAC Secured
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Healthcare Intelligence & Grounded RAG Platform</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="hidden lg:flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Informational & Research Use Only</span>
          </div>

          <a
            href="/api/v1/docs"
            target="_blank"
            rel="noreferrer"
            className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors border border-slate-700"
          >
            <BookOpen className="w-3.5 h-3.5 text-teal-400" />
            <span>API Docs</span>
          </a>

          {/* User Auth Section */}
          {isAuthenticated && user ? (
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
              <div className="flex items-center space-x-2 bg-slate-800/80 px-2.5 py-1 rounded-xl border border-slate-700/60">
                <div className="w-6 h-6 rounded-full bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-300 text-xs font-bold">
                  {user.full_name[0]}
                </div>
                <div className="hidden sm:block text-left">
                  <div className="text-xs font-medium text-white leading-tight">{user.full_name}</div>
                  <span className={`text-[9px] uppercase px-1 rounded border font-semibold ${getRoleBadge(user.role)}`}>
                    {user.role}
                  </span>
                </div>
              </div>

              <button
                onClick={logout}
                title="Sign Out"
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-500/10 hover:text-rose-400 text-slate-400 border border-slate-700 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenLogin}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-500 hover:to-cyan-500 text-white text-xs font-semibold shadow-lg shadow-teal-500/20 transition-all"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
