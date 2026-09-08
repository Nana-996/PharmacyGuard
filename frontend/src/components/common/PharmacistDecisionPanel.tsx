import React, { useState } from 'react';
import type { PharmacistReview } from '../../types';
import { StatusBadge } from './StatusBadge';
import { DecisionModal } from './DecisionModal';
import {
  CheckCircle2,
  RefreshCw,
  ArrowUpRight,
  Calendar,
  FileText,
  Clock
} from 'lucide-react';

interface PharmacistDecisionPanelProps {
  review: PharmacistReview;
  onActionSuccess?: (updatedReview: PharmacistReview) => void;
  onAccept: (notes?: string) => Promise<void>;
  onOverride: (notes: string) => Promise<void>;
  onEscalate: (notes: string) => Promise<void>;
  isSubmitting?: boolean;
}

export const PharmacistDecisionPanel: React.FC<PharmacistDecisionPanelProps> = ({
  review,
  onAccept,
  onOverride,
  onEscalate,
  isSubmitting = false,
}) => {
  const [modalAction, setModalAction] = useState<'ACCEPT' | 'OVERRIDE' | 'ESCALATE' | null>(null);

  return (
    <div className="rounded-lg border border-[var(--pg-border)] bg-white p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[var(--pg-border-light)]">
        <div>
          <h3 className="text-sm font-semibold text-[var(--pg-text)]">Pharmacist Decision</h3>
          <p className="text-[13px] text-[var(--pg-text-muted)]">Human verification required before dispensing</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[13px] text-[var(--pg-text-muted)]">Status:</span>
          <StatusBadge status={review.pharmacist_decision} size="md" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[13px]">
        <div className="p-3 rounded-md bg-slate-50 border border-[var(--pg-border-light)] space-y-1.5">
          <div className="text-[11px] font-medium uppercase text-[var(--pg-text-muted)]">Agent Guidance</div>
          <StatusBadge status={review.agent_review_status} size="sm" />
          <p className="text-[var(--pg-text-secondary)] text-[13px] mt-1.5">
            {review.findings.length} finding{review.findings.length !== 1 ? 's' : ''} across clinical & inventory checks.
          </p>
        </div>

        <div className="p-3 rounded-md bg-slate-50 border border-[var(--pg-border-light)] space-y-1.5">
          <div className="text-[11px] font-medium uppercase text-[var(--pg-text-muted)]">Assignment</div>
          <div className="text-[var(--pg-text)] font-medium">{review.reviewed_by || 'Awaiting pharmacist'}</div>
          {review.reviewed_at ? (
            <div className="text-[var(--pg-text-muted)] flex items-center gap-1 text-[12px]">
              <Calendar className="w-3 h-3" />
              <span>{new Date(review.reviewed_at).toLocaleString()}</span>
            </div>
          ) : (
            <div className="text-amber-600 flex items-center gap-1 text-[12px] font-medium">
              <Clock className="w-3 h-3" />
              <span>Pending</span>
            </div>
          )}
        </div>
      </div>

      {/* Existing Notes */}
      {review.pharmacist_notes && (
        <div className="p-3 rounded-md bg-blue-50 border border-blue-100 text-[13px]">
          <div className="flex items-center gap-1.5 font-medium text-blue-800 mb-1">
            <FileText className="w-3.5 h-3.5" />
            <span>Pharmacist Notes:</span>
          </div>
          <p className="text-blue-900 text-[13px] leading-relaxed">{review.pharmacist_notes}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="pt-2 flex flex-wrap items-center justify-end gap-2">
        <button
          type="button"
          onClick={() => onAccept()}
          disabled={isSubmitting}
          className={`px-3.5 py-2 text-[13px] font-medium rounded-md transition-colors flex items-center gap-1.5 ${
            review.pharmacist_decision === 'ACCEPTED'
              ? 'bg-emerald-700 text-white'
              : 'bg-emerald-600 hover:bg-emerald-700 text-white'
          } disabled:opacity-50`}
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>{review.pharmacist_decision === 'ACCEPTED' ? 'Accepted' : 'Accept'}</span>
        </button>

        <button
          type="button"
          onClick={() => setModalAction('OVERRIDE')}
          disabled={isSubmitting}
          className={`px-3.5 py-2 text-[13px] font-medium rounded-md transition-colors flex items-center gap-1.5 ${
            review.pharmacist_decision === 'OVERRIDDEN'
              ? 'bg-violet-700 text-white'
              : 'bg-violet-600 hover:bg-violet-700 text-white'
          } disabled:opacity-50`}
        >
          <RefreshCw className="w-4 h-4" />
          <span>{review.pharmacist_decision === 'OVERRIDDEN' ? 'Overridden' : 'Override'}</span>
        </button>

        <button
          type="button"
          onClick={() => setModalAction('ESCALATE')}
          disabled={isSubmitting}
          className={`px-3.5 py-2 text-[13px] font-medium rounded-md transition-colors flex items-center gap-1.5 ${
            review.pharmacist_decision === 'ESCALATED'
              ? 'bg-indigo-700 text-white'
              : 'bg-indigo-600 hover:bg-indigo-700 text-white'
          } disabled:opacity-50`}
        >
          <ArrowUpRight className="w-4 h-4" />
          <span>{review.pharmacist_decision === 'ESCALATED' ? 'Escalated' : 'Escalate'}</span>
        </button>
      </div>

      {/* Decision Modal */}
      {modalAction && (
        <DecisionModal
          isOpen={true}
          onClose={() => setModalAction(null)}
          onConfirm={async (notes) => {
            if (modalAction === 'OVERRIDE') {
              await onOverride(notes);
            } else if (modalAction === 'ESCALATE') {
              await onEscalate(notes);
            } else if (modalAction === 'ACCEPT') {
              await onAccept(notes);
            }
          }}
          actionType={modalAction}
          prescriptionId={review.prescription_id}
          isSubmitting={isSubmitting}
        />
      )}
    </div>
  );
};
