import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, RotateCcw, AlertTriangle, X, Lock } from 'lucide-react';

import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

interface ChiefEscalationResolutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  reviewId: string;
  prescriptionId: string;
  patientName?: string;
  escalatingPharmacist?: string;
  escalationReason?: string;
  onSuccess: () => void;
}

export const ChiefEscalationResolutionModal: React.FC<ChiefEscalationResolutionModalProps> = ({
  isOpen,
  onClose,
  reviewId,
  prescriptionId,
  patientName,
  escalatingPharmacist,
  escalationReason,
  onSuccess,
}) => {
  const { user } = useAuth();
  const [decision, setDecision] = useState<'RESOLVED_APPROVED' | 'RETURNED_TO_STAFF' | 'DIRECT_OVERRIDE_APPROVED'>('RESOLVED_APPROVED');
  const [notes, setNotes] = useState('');
  const [actionRequired, setActionRequired] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notes.trim() || notes.trim().length < 5) {
      setError('Please provide comprehensive clinical notes (at least 5 characters).');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await api.resolveEscalation(reviewId, {
        chief_decision: decision,
        chief_notes: notes.trim(),
        action_required: actionRequired.trim() || undefined,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to record Chief Pharmacist escalation resolution.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="bg-slate-900 text-white px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-300">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-300">Executive Departmental Sign-off</span>
                <span className="px-1.5 py-0.5 rounded bg-indigo-900/80 text-[10px] font-mono text-indigo-200">2-Level Governance</span>
              </div>
              <h2 className="text-lg font-bold text-white">Resolve Pharmacist Escalation</h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Case Summary Pill */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div>
            <span className="text-slate-500">Prescription ID: </span>
            <span className="font-mono font-bold text-indigo-950">{prescriptionId}</span>
            {patientName && (
              <span className="ml-3 text-slate-700 font-medium">({patientName})</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-500">Escalated by:</span>
            <span className="font-mono font-semibold text-slate-800 bg-white px-2 py-0.5 rounded border border-slate-200">
              {escalatingPharmacist || 'Staff Pharmacist'}
            </span>
          </div>
        </div>

        {escalationReason && (
          <div className="mx-6 mt-4 p-3.5 bg-amber-50/80 border border-amber-200 rounded-xl text-xs">
            <div className="font-semibold text-amber-900 mb-1 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
              <span>Staff Pharmacist Escalation Reason:</span>
            </div>
            <p className="text-amber-800 leading-relaxed italic">"{escalationReason}"</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800">
              {error}
            </div>
          )}

          {/* Decision Selector */}
          <div>
            <label className="block text-xs font-bold uppercase text-slate-600 tracking-wider mb-2">
              Chief Pharmacist Decision & Action
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setDecision('RESOLVED_APPROVED')}
                className={`p-3.5 rounded-xl border text-left transition-all flex flex-col justify-between gap-2 ${
                  decision === 'RESOLVED_APPROVED'
                    ? 'border-emerald-600 bg-emerald-50/80 text-emerald-950 ring-2 ring-emerald-500/20'
                    : 'border-slate-200 bg-white hover:border-slate-300 text-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <CheckCircle2 className={`w-4 h-4 ${decision === 'RESOLVED_APPROVED' ? 'text-emerald-600' : 'text-slate-400'}`} />
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700">Approve</span>
                </div>
                <div>
                  <div className="text-xs font-bold">Resolve & Authorize</div>
                  <div className="text-[11px] text-slate-500 mt-0.5 leading-tight">Authorize dispensing with Chief sign-off</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setDecision('RETURNED_TO_STAFF')}
                className={`p-3.5 rounded-xl border text-left transition-all flex flex-col justify-between gap-2 ${
                  decision === 'RETURNED_TO_STAFF'
                    ? 'border-amber-600 bg-amber-50/80 text-amber-950 ring-2 ring-amber-500/20'
                    : 'border-slate-200 bg-white hover:border-slate-300 text-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <RotateCcw className={`w-4 h-4 ${decision === 'RETURNED_TO_STAFF' ? 'text-amber-600' : 'text-slate-400'}`} />
                  <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Return</span>
                </div>
                <div>
                  <div className="text-xs font-bold">Return to Staff</div>
                  <div className="text-[11px] text-slate-500 mt-0.5 leading-tight">Send back with clinical directives</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setDecision('DIRECT_OVERRIDE_APPROVED')}
                className={`p-3.5 rounded-xl border text-left transition-all flex flex-col justify-between gap-2 ${
                  decision === 'DIRECT_OVERRIDE_APPROVED'
                    ? 'border-indigo-600 bg-indigo-50/80 text-indigo-950 ring-2 ring-indigo-500/20'
                    : 'border-slate-200 bg-white hover:border-slate-300 text-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <ShieldCheck className={`w-4 h-4 ${decision === 'DIRECT_OVERRIDE_APPROVED' ? 'text-indigo-600' : 'text-slate-400'}`} />
                  <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700">Executive</span>
                </div>
                <div>
                  <div className="text-xs font-bold">Chief Override</div>
                  <div className="text-[11px] text-slate-500 mt-0.5 leading-tight">Executive clinical override approval</div>
                </div>
              </button>
            </div>
          </div>

          {/* Chief Consultation Notes */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Chief Pharmacist Consultation Rationale & Documentation <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Detail your departmental evaluation, benefit-risk assessment, and rationale..."
              className="w-full text-xs p-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-sans"
              required
            />
          </div>

          {/* Action Directives (especially when returned to staff) */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Required Action Directive / Follow-up Instructions {decision === 'RETURNED_TO_STAFF' ? '(Recommended)' : '(Optional)'}
            </label>
            <input
              type="text"
              value={actionRequired}
              onChange={(e) => setActionRequired(e.target.value)}
              placeholder="e.g. Consult prescriber to request renal function labs before clearing"
              className="w-full text-xs p-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Non-destructive notice */}
          <div className="p-3 rounded-lg bg-indigo-50/60 border border-indigo-100 flex items-start gap-2 text-[11px] text-indigo-900 leading-relaxed">
            <Lock className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
            <span>
              <strong>Compliance Notice:</strong> This action records a permanent Chief Pharmacist sign-off under your account (<strong>{user?.user_id}</strong>) without erasing the staff pharmacist's original escalation history.
            </span>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 text-xs font-bold text-white bg-indigo-700 hover:bg-indigo-800 disabled:opacity-50 rounded-xl shadow-xs transition-colors flex items-center gap-2"
            >
              {submitting ? 'Submitting Resolution...' : 'Confirm Resolution'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
