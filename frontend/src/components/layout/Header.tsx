import React from 'react';
import { User, Cpu, RefreshCw, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';


interface HeaderProps {
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onRefresh, isRefreshing = false }) => {
  const { user, logout } = useAuth();

  const getRoleBadgeStyle = (role?: string) => {
    switch (role) {
      case 'CHIEF_PHARMACIST':
        return 'bg-violet-50 text-violet-700 border-violet-200';
      case 'PHARMACY_STUDENT':
        return 'bg-sky-50 text-sky-700 border-sky-200';
      case 'ADMIN':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'STAFF_PHARMACIST':
      default:
        return 'bg-blue-50 text-blue-700 border-blue-200';
    }
  };

  const formatRoleName = (role?: string) => {
    switch (role) {
      case 'CHIEF_PHARMACIST':
        return 'Chief Pharmacist';
      case 'PHARMACY_STUDENT':
        return 'Pharmacy Student';
      case 'ADMIN':
        return 'Administrator';
      case 'STAFF_PHARMACIST':
      default:
        return 'Staff Pharmacist';
    }
  };

  return (
    <header className="h-14 bg-white border-b border-[var(--pg-border)] px-5 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-2 text-[13px] text-[var(--pg-text-secondary)]">
        <span className="font-medium text-[var(--pg-text)]">St. Jude Medical Center</span>
        <span className="text-[var(--pg-border)]">·</span>
        <span>Inpatient Pharmacy</span>
        <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
          Simulated Data
        </span>
      </div>

      <div className="flex items-center gap-3">
        {/* AI Agent Status Pill — retained per user request */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-medium">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
          </span>
          <Cpu className="w-3 h-3" />
          <span>AI Agent Online</span>
        </div>

        {/* Manual Refresh */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Refresh data"
            className="p-1.5 rounded-md text-[var(--pg-text-muted)] hover:text-[var(--pg-text-secondary)] hover:bg-slate-100 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-blue-600' : ''}`} />
          </button>
        )}

        {/* User Profile */}
        <div className="flex items-center gap-2.5 pl-3 border-l border-[var(--pg-border)]">
          <div className="w-7 h-7 rounded-full bg-blue-50 text-blue-600 border border-blue-200 flex items-center justify-center">
            <User className="w-3.5 h-3.5" />
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-[13px] font-semibold text-[var(--pg-text)] leading-tight">
              {user?.full_name || 'User'}
            </div>
            <div className="mt-0.5">
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${getRoleBadgeStyle(user?.role)}`}>
                {formatRoleName(user?.role)}
              </span>
            </div>
          </div>

          <button
            onClick={() => logout()}
            title="Sign out"
            className="p-1.5 rounded-md text-[var(--pg-text-muted)] hover:text-red-600 hover:bg-red-50 transition-colors ml-0.5"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
