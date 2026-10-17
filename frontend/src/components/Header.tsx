import React from 'react';
import { Activity, ShieldAlert, BookOpen, LogOut, LogIn, Users } from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';

interface HeaderProps {
  currentView: 'workspace' | 'about' | 'guide';
  onNavigate: (view: 'workspace' | 'about' | 'guide') => void;
  onOpenLogin: () => void;
  onOpenRoleSwitch?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  onNavigate,
  onOpenLogin,
  onOpenRoleSwitch,
}) => {
  const { user, isAuthenticated, logout, demoMode } = useAuth();

  const getRoleBadge = (role?: string) => {
    switch (role) {
      case 'admin':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'doctor':
      case 'reviewer':
        return 'bg-teal-50 text-teal-800 border-teal-200';
      case 'nurse':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'hospital_admin':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'patient':
        return 'bg-sky-50 text-sky-800 border-sky-200';
      case 'researcher':
        return 'bg-indigo-50 text-indigo-800 border-indigo-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const formatRoleLabel = (role?: string) => {
    if (!role) return '';
    if (role === 'hospital_admin') return 'Hospital Admin';
    if (role === 'reviewer') return 'Doctor / Reviewer';
    return role.charAt(0).toUpperCase() + role.slice(1);
  };

  return (
    <header className="border-b border-slate-200 bg-white/95 backdrop-blur-md sticky top-0 z-40 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo and Navigation */}
        <div className="flex items-center space-x-6">
          <button
            onClick={() => onNavigate('workspace')}
            className="flex items-center space-x-2.5 text-left cursor-pointer focus:outline-none"
          >
            <div className="p-2 bg-teal-700 text-white rounded-xl shadow-xs">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-slate-900 tracking-tight">Patient360</span>
                {demoMode && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 uppercase tracking-wider">
                    Demo Mode
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-500 hidden sm:block">Clinical Evidence & Medical Intelligence</p>
            </div>
          </button>

          {/* Navigation items */}
          <nav className="hidden md:flex items-center space-x-1 pl-4 border-l border-slate-200">
            <button
              onClick={() => onNavigate('workspace')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                currentView === 'workspace'
                  ? 'bg-teal-50 text-teal-800 font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              Workspace
            </button>
            <button
              onClick={() => onNavigate('about')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                currentView === 'about'
                  ? 'bg-teal-50 text-teal-800 font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              About Patient360
            </button>
            <button
              onClick={() => onNavigate('guide')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                currentView === 'guide'
                  ? 'bg-teal-50 text-teal-800 font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              Clinical Guide
            </button>
          </nav>
        </div>

        {/* Right Header Elements */}
        <div className="flex items-center space-x-3">
          <div className="hidden xl:flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-[11px]">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span>Clinical Information and Research Use Only</span>
          </div>

          <button
            onClick={() => onNavigate('guide')}
            className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-medium transition-colors border border-slate-200 cursor-pointer"
          >
            <BookOpen className="w-3.5 h-3.5 text-teal-700" />
            <span>Clinical Guide</span>
          </button>

          {/* User Auth Section */}
          {isAuthenticated && user ? (
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
              <div className="flex items-center space-x-2 bg-slate-50 px-2.5 py-1 rounded-xl border border-slate-200">
                <div className="w-6 h-6 rounded-full bg-teal-100 border border-teal-200 flex items-center justify-center text-teal-800 text-xs font-bold">
                  {user.full_name[0]}
                </div>
                <div className="hidden sm:block text-left">
                  <div className="text-xs font-semibold text-slate-900 leading-tight">{user.full_name}</div>
                  <span className={`text-[9px] uppercase px-1.5 py-0.2 rounded border font-semibold ${getRoleBadge(user.role)}`}>
                    {formatRoleLabel(user.role)}
                  </span>
                </div>
              </div>

              {demoMode && (
                <button
                  onClick={onOpenRoleSwitch || onOpenLogin}
                  title="Switch Demo Role"
                  className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-xl bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 text-xs font-medium transition-colors cursor-pointer"
                >
                  <Users className="w-3.5 h-3.5 text-teal-700" />
                  <span className="hidden md:inline">Switch Role</span>
                </button>
              )}

              <button
                onClick={logout}
                title="Sign Out"
                className="p-1.5 rounded-lg bg-slate-50 hover:bg-rose-50 hover:text-rose-700 text-slate-500 border border-slate-200 transition-colors cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenLogin}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold shadow-xs transition-all cursor-pointer"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Demo Access</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
