import React from 'react';
import type { AgentFinding } from '../../types';
import { StatusBadge } from './StatusBadge';
import {
  AlertOctagon,
  Copy,
  Zap,
  Gauge,
  Package,
  HelpCircle,
  FileSearch
} from 'lucide-react';

interface FindingCardProps {
  finding: AgentFinding;
  index?: number;
}

export const FindingCard: React.FC<FindingCardProps> = ({ finding, index }) => {
  const getToolDisplayName = (source: string): string => {
    const s = (source || '').toLowerCase();
    if (s.includes('allergy')) return 'Allergy Check';
    if (s.includes('diagnosis') || s.includes('indication')) return 'Indication Check';
    if (s.includes('dosage') || s.includes('dose')) return 'Dosage Check';
    if (s.includes('duplicat')) return 'Duplicate Check';
    if (s.includes('interact')) return 'Interaction Check';
    if (s.includes('inventory') || s.includes('stock')) return 'Inventory Check';
    if (s.includes('prescription')) return 'Prescription Retrieval';
    return source || 'System';
  };

  const getCategoryIcon = (category: string) => {
    switch (category?.toUpperCase()) {
      case 'ALLERGY': return AlertOctagon;
      case 'CLINICAL': return FileSearch;
      case 'DUPLICATION': return Copy;
      case 'INTERACTION': return Zap;
      case 'DOSAGE': return Gauge;
      case 'INVENTORY': return Package;
      default: return HelpCircle;
    }
  };

  const getBorderColor = () => {
    if (finding.severity === 'HIGH' || finding.requires_action) return 'border-l-red-500';
    if (finding.severity === 'MODERATE') return 'border-l-amber-500';
    return 'border-l-blue-500';
  };

  const CategoryIcon = getCategoryIcon(finding.category);
  const toolName = getToolDisplayName(finding.evidence_source);
  const rawEvidence = finding.evidence || finding.evidence_data || '';

  return (
    <div className={`rounded-lg border border-[var(--pg-border)] bg-white p-4 border-l-[3px] ${getBorderColor()} transition-shadow hover:shadow-sm`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <CategoryIcon className="w-4 h-4 text-[var(--pg-text-muted)] shrink-0" />
          <div>
            <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--pg-text-muted)]">
              {finding.category}
              {index !== undefined && <span className="ml-1">#{index + 1}</span>}
            </span>
            <h4 className="text-sm font-semibold text-[var(--pg-text)] leading-snug">{finding.title}</h4>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <StatusBadge status={finding.severity} size="sm" />
          {finding.requires_action && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-700">
              Action Required
            </span>
          )}
        </div>
      </div>

      <p className="text-[13px] text-[var(--pg-text-secondary)] leading-relaxed mb-3">{finding.description}</p>

      {/* Evidence */}
      <div className="rounded bg-slate-50 border border-[var(--pg-border-light)] p-2.5 text-xs">
        <div className="flex items-center justify-between mb-1.5 text-[var(--pg-text-muted)]">
          <span className="font-medium">Source: <span className="text-[var(--pg-text-secondary)]">{toolName}</span></span>
        </div>
        <div className="text-[var(--pg-text-secondary)] text-[12px] leading-relaxed break-words">
          {rawEvidence}
        </div>
      </div>
    </div>
  );
};
