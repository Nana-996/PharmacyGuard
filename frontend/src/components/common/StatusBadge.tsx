import React from 'react';
import type { AgentReviewStatus, PharmacistDecision, StockStatus, FindingSeverity } from '../../types';

interface StatusBadgeProps {
  status: AgentReviewStatus | PharmacistDecision | StockStatus | FindingSeverity | string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const norm = (status || '').toUpperCase().trim();

  let colorClasses = 'bg-slate-100 text-slate-600';
  let label = norm.replace(/_/g, ' ');

  if (norm === 'CLEAR' || norm === 'AVAILABLE' || norm === 'ACCEPTED' || norm === 'NONE' || norm === 'LOW') {
    colorClasses = 'bg-emerald-50 text-emerald-700';
  } else if (norm === 'REVIEW' || norm === 'LOW STOCK' || norm === 'PENDING' || norm === 'MODERATE') {
    colorClasses = 'bg-amber-50 text-amber-700';
  } else if (norm === 'HIGH_PRIORITY_REVIEW' || norm === 'HIGH PRIORITY REVIEW' || norm === 'HIGH' || norm === 'OUT OF STOCK') {
    colorClasses = 'bg-red-50 text-red-700 font-semibold';
    label = norm === 'HIGH_PRIORITY_REVIEW' ? 'HIGH PRIORITY' : norm;
  } else if (norm === 'OVERRIDDEN') {
    colorClasses = 'bg-violet-50 text-violet-700';
  } else if (norm === 'ESCALATED') {
    colorClasses = 'bg-indigo-50 text-indigo-700 font-semibold';
  } else if (norm === 'STRENGTH UNAVAILABLE' || norm === 'NOT FOUND') {
    colorClasses = 'bg-orange-50 text-orange-700';
  }

  const sizeClasses = {
    sm: 'px-1.5 py-0.5 text-[10px]',
    md: 'px-2 py-0.5 text-[11px]',
    lg: 'px-2.5 py-1 text-xs',
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded font-medium uppercase tracking-wide ${colorClasses} ${sizeClasses}`}
    >
      {label}
    </span>
  );
};
