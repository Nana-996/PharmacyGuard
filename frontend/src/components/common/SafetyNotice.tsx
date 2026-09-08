import React from 'react';
import { Info } from 'lucide-react';

interface SafetyNoticeProps {
  className?: string;
  variant?: 'banner' | 'card';
}

export const SafetyNotice: React.FC<SafetyNoticeProps> = ({ className = '', variant = 'banner' }) => {
  if (variant === 'card') {
    return (
      <div className={`px-4 py-2.5 rounded-lg bg-blue-50 border border-blue-100 text-[13px] text-blue-800 flex items-center gap-2 ${className}`}>
        <Info className="w-3.5 h-3.5 text-blue-500 shrink-0" />
        <span>
          <strong className="font-semibold">Note:</strong> PharmacyGuard provides decision-support. Final clinical decisions remain with a qualified pharmacist.
        </span>
      </div>
    );
  }

  return (
    <div className={`py-2 px-4 bg-blue-50 border-b border-blue-100 text-blue-700 text-xs flex items-center gap-2 ${className}`}>
      <Info className="w-3.5 h-3.5 text-blue-500 shrink-0" />
      <span>
        <strong className="font-medium">Decision Support:</strong> Final clinical decisions remain with a qualified pharmacist.
      </span>
    </div>
  );
};
