import React from 'react';
import {
  LayoutDashboard,
  ListOrdered,
  Boxes,
  ShieldCheck,
  FileText,
  Activity,
  GraduationCap,
  FilePlus
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Logo } from '../common/Logo';

export type NavView = 'dashboard' | 'new_prescription' | 'review' | 'queue' | 'inventory' | 'analytics' | 'case_details' | 'student';

interface SidebarProps {
  activeView: NavView;
  onNavigate: (view: NavView) => void;
  pendingCount?: number;
  lowStockCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeView,
  onNavigate,
  pendingCount = 0,
  lowStockCount = 0,
}) => {
  const { user } = useAuth();
  const role = user?.role;

  // Define role-specific access permissions
  const navItems = [
    {
      id: 'dashboard' as NavView,
      label: 'Dashboard',
      icon: LayoutDashboard,
      roles: ['STAFF_PHARMACIST', 'CHIEF_PHARMACIST', 'ADMIN'],
    },
    {
      id: 'new_prescription' as NavView,
      label: 'New Prescription',
      icon: FilePlus,
      roles: ['STAFF_PHARMACIST', 'CHIEF_PHARMACIST'],
    },
    {
      id: 'review' as NavView,
      label: 'Prescription Review',
      icon: Activity,
      roles: ['STAFF_PHARMACIST', 'CHIEF_PHARMACIST'],
    },
    {
      id: 'queue' as NavView,
      label: 'Review Queue',
      icon: ListOrdered,
      count: pendingCount,
      roles: ['STAFF_PHARMACIST', 'CHIEF_PHARMACIST'],
    },
    {
      id: 'inventory' as NavView,
      label: 'Inventory',
      icon: Boxes,
      count: lowStockCount,
      countType: 'danger',
      roles: ['STAFF_PHARMACIST', 'CHIEF_PHARMACIST', 'ADMIN'],
    },
    {
      id: 'analytics' as NavView,
      label: 'Chief Pharmacist',
      icon: ShieldCheck,
      roles: ['CHIEF_PHARMACIST'],
    },
    {
      id: 'case_details' as NavView,
      label: 'Case Dossier',
      icon: FileText,
      roles: ['STAFF_PHARMACIST', 'CHIEF_PHARMACIST'],
    },
    {
      id: 'student' as NavView,
      label: 'Training Lab',
      icon: GraduationCap,
      roles: ['PHARMACY_STUDENT', 'STAFF_PHARMACIST', 'CHIEF_PHARMACIST', 'ADMIN'],
    }
  ];

  // Filter items matching the user's role
  const visibleItems = navItems.filter((item) => !role || item.roles.includes(role));

  return (
    <aside className="w-56 bg-white flex flex-col shrink-0 min-h-screen border-r border-[var(--pg-border)] select-none">
      {/* Brand Header */}
      <div className="px-5 py-4 border-b border-[var(--pg-border)]">
        <Logo size="sm" showText={true} />
      </div>

      {/* Navigation List */}
      <nav className="flex-1 py-3 px-3 space-y-0.5 overflow-y-auto">
        <div className="px-2 pb-2 pt-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--pg-text-muted)]">
          {role === 'PHARMACY_STUDENT' ? 'Student' : 'Workflows'}
        </div>

        {visibleItems.map((item) => {
          const isActive = activeView === item.id;
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center justify-between px-2.5 py-2 rounded-md text-[13px] font-medium transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700 font-semibold'
                  : 'text-[var(--pg-text-secondary)] hover:bg-slate-50 hover:text-[var(--pg-text)]'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    isActive ? 'text-blue-600' : 'text-[var(--pg-text-muted)]'
                  }`}
                />
                <span>{item.label}</span>
              </div>

              {item.count !== undefined && item.count > 0 && (
                <span
                  className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold min-w-[18px] text-center ${
                    item.countType === 'danger'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-amber-100 text-amber-700'
                  }`}
                >
                  {item.count}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Environment Indicator */}
      <div className="p-3 border-t border-[var(--pg-border)] bg-slate-50/60">
        <div className="flex items-center gap-1.5 text-[11px] text-[var(--pg-text-muted)] font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></span>
          <span className="truncate">Simulated EHR & Formulary</span>
        </div>
      </div>
    </aside>
  );
};
