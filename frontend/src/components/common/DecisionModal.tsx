import React, { useState } from 'react';
import { X, AlertCircle, ArrowUpRight, RefreshCw, CheckCircle2 } from 'lucide-react';

interface DecisionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (notes: string) => Promise<void>;
  actionType: 'OVERRIDE' | 'ESCALATE' | 'ACCEPT';
  prescriptionId: string;
  isSubmitting: boolean;
}

export const DecisionModal: React.FC<DecisionModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  actionType,
  prescriptionId,
  isSubmitting,
}) => {
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const isNotesMandatory = actionType === 'OVERRIDE' || actionType === 'ESCALATE';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isNotesMandatory && (!notes.trim() || notes.trim().length < 3)) {
      setError('Clinical notes are required (min 3 characters).');
      return;
    }
    setError(null);
    try {
      await onConfirm(notes);
      setNotes('');
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to submit decision.');
    }
  };

  const getDetails = () => {
    switch (actionType) {
      case 'OVERRIDE':
        return {
          title: 'Override Findings',
          description: `Override the system findings for ${prescriptionId}. Clinical rationale is required.`,
          icon: RefreshCw,
          btnColor: 'bg-violet-600 hover:bg-violet-700',
          btnText: 'Confirm Override',
          placeholder: 'Provide clinical justification for overriding...'
        };
      case 'ESCALATE':
        return {
          title: 'Escalate to Chief Pharmacist',
          description: `Escalate ${prescriptionId} to senior pharmacy leadership for review.`,
          icon: ArrowUpRight,
          btnColor: 'bg-indigo-600 hover:bg-indigo-700',
          btnText: 'Confirm Escalation',
          placeholder: 'Detail the clinical complexity requiring escalation...'
        };
      case 'ACCEPT':
      default:
        return {
          title: 'Accept Findings',
          description: `Accept the review assessment for ${prescriptionId}.`,
          icon: CheckCircle2,
          btnColor: 'bg-emerald-600 hover:bg-emerald-700',
          btnText: 'Confirm Accept',
          placeholder: 'Optional notes...'
        };
    }
  };

  const details = getDetails();
  const Icon = details.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
      <div className="relative w-full max-w-lg bg-white rounded-lg shadow-xl border border-[var(--pg-border)] overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--pg-border-light)]">
          <div className="flex items-center gap-2.5">
            <Icon className="w-5 h-5 text-[var(--pg-text-secondary)]" />
            <div>
              <h3 className="text-base font-semibold text-[var(--pg-text)]">{details.title}</h3>
              <p className="text-[13px] text-[var(--pg-text-muted)]">{prescriptionId}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="p-1 rounded text-[var(--pg-text-muted)] hover:text-[var(--pg-text)] hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <p className="text-[13px] text-[var(--pg-text-secondary)]">{details.description}</p>

          <div>
            <label className="block text-[13px] font-medium text-[var(--pg-text)] mb-1.5">
              Clinical Notes {isNotesMandatory && <span className="text-red-500">*</span>}
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => {
                setNotes(e.target.value);
                if (error) setError(null);
              }}
              placeholder={details.placeholder}
              required={isNotesMandatory}
              className="w-full px-3 py-2 text-[13px] text-[var(--pg-text)] bg-white border border-[var(--pg-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder:text-[var(--pg-text-muted)]"
            />
          </div>

          {error && (
            <div className="p-2.5 text-[13px] text-red-700 bg-red-50 border border-red-100 rounded-md flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--pg-border-light)]">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-3.5 py-2 text-[13px] font-medium text-[var(--pg-text-secondary)] bg-slate-100 hover:bg-slate-200 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || (isNotesMandatory && notes.trim().length < 3)}
              className={`px-3.5 py-2 text-[13px] font-medium text-white rounded-md transition-colors flex items-center gap-1.5 ${details.btnColor} disabled:opacity-50`}
            >
              {isSubmitting ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                details.btnText
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
