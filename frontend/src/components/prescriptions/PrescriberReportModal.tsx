import React, { useState, useEffect } from 'react';
import type { PharmacistReview } from '../../types';

import { api } from '../../services/api';
import {
  Send,
  X,
  Bot,
  UserCheck,
  AlertTriangle,
  FileText,
  RotateCw,
  Sparkles
} from 'lucide-react';

interface PrescriberReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  review: PharmacistReview;
  onSent: (newCommunication: any) => void;
}

export const PrescriberReportModal: React.FC<PrescriberReportModalProps> = ({
  isOpen,
  onClose,
  review,
  onSent,
}) => {
  const [reportType, setReportType] = useState<'AI_FINDINGS_REPORT' | 'CUSTOM_PHARMACIST_REPORT'>('AI_FINDINGS_REPORT');
  const [recipientDoctor, setRecipientDoctor] = useState<string>('');
  const [subject, setSubject] = useState<string>('');
  const [messageBody, setMessageBody] = useState<string>('');
  const [selectedFindings, setSelectedFindings] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const rxDetails = review.prescription_details;
  const doctorName = rxDetails?.prescribing_doctor || 'Attending Physician';
  const patientName = rxDetails?.patient?.name || 'Hospital Patient';

  useEffect(() => {
    if (isOpen) {
      setRecipientDoctor(doctorName);
      
      // Default findings selected
      const initSelected: Record<string, boolean> = {};
      review.findings.forEach((f, idx) => {
        initSelected[f.finding_id || `idx-${idx}`] = true;
      });
      setSelectedFindings(initSelected);

      if (reportType === 'AI_FINDINGS_REPORT') {
        setSubject(`[CLINICAL SAFETY ALERT] AI Safety Query for ${patientName} (${review.prescription_id})`);
        setMessageBody(
          `Dear ${doctorName},\n\nPharmacyGuard clinical decision support flagged potential safety/inventory considerations regarding prescription ${review.prescription_id} for patient ${patientName}. Please review the attached findings below and confirm if medication adjustment is authorized.\n\nThank you,\nClinical Pharmacy Directorate`
        );
      } else {
        setSubject(`[PHARMACIST CLINICAL EVALUATION] Prescription ${review.prescription_id} - ${patientName}`);
        setMessageBody(
          `Dear ${doctorName},\n\nFollowing clinical evaluation of prescription ${review.prescription_id}, I recommend reviewing the regimen for the following clinical reason:\n\n[Insert clinical rationale, laboratory values, or proposed alternatives here]\n\nPlease advise if we may update the order accordingly.\n\nRespectfully,\nClinical Pharmacist`
        );
      }
    }
  }, [isOpen, reportType, doctorName, patientName, review.prescription_id]);

  if (!isOpen) return null;

  const handleToggleFinding = (id: string) => {
    setSelectedFindings((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!recipientDoctor.trim()) {
      setError('Recipient physician name is required.');
      return;
    }
    if (!subject.trim()) {
      setError('Subject line is required.');
      return;
    }
    if (!messageBody.trim()) {
      setError('Report message body is required.');
      return;
    }

    setLoading(true);
    try {
      const includedFindingsList = reportType === 'AI_FINDINGS_REPORT'
        ? review.findings
            .filter((f, idx) => selectedFindings[f.finding_id || `idx-${idx}`])
            .map((f) => ({
              category: f.category,
              severity: f.severity,
              title: f.title,
              description: f.description,
              evidence: f.evidence || f.evidence_data
            }))
        : undefined;

      const payload = {
        recipient_doctor: recipientDoctor.trim(),
        report_type: reportType,
        subject: subject.trim(),
        message_body: messageBody.trim(),
        ai_findings_included: includedFindingsList,
      };

      const res = await api.sendPrescriberReport(review.review_id, payload);
      onSent(res.data);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to send prescriber report.');
    } finally {
      setLoading(false);
    }
  };

  const quickTemplates = [
    {
      label: 'Allergy Alternative Recommendation',
      text: `Patient has documented allergy cross-reactivity with the prescribed beta-lactam agent. Recommend switching to oral Azithromycin 500mg daily or Doxycycline 100mg BID. Please authorize substitution.`
    },
    {
      label: 'Dual NSAID Duplication Warning',
      text: `Prescription contains two concurrent systemic NSAIDs. Recommend discontinuing one agent to reduce severe GI ulceration and acute kidney injury risk. Please confirm preferred NSAID.`
    },
    {
      label: 'Inventory Shortage Strength Swap',
      text: `The prescribed strength is currently out of stock in the hospital central pharmacy. We have alternative strengths in stock. Please authorize dispensing with adjusted tablet count.`
    }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-500/20 border border-indigo-400/30 text-indigo-300">
              <Send className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-white/10 text-indigo-300 font-bold">
                  {review.prescription_id}
                </span>
                <span className="text-xs text-slate-400">Prescriber Communication</span>
              </div>
              <h2 className="text-base font-bold text-white mt-0.5">
                Send Clinical Report / Query to Prescribing Doctor
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Report Type Selector Tabs */}
        <div className="px-6 pt-4 pb-2 bg-slate-50 border-b border-slate-200">
          <div className="grid grid-cols-2 gap-2 p-1 bg-slate-200/80 rounded-xl">
            <button
              type="button"
              onClick={() => setReportType('AI_FINDINGS_REPORT')}
              className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-bold transition-all ${
                reportType === 'AI_FINDINGS_REPORT'
                  ? 'bg-white text-indigo-950 shadow-xs ring-1 ring-slate-300'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Bot className="w-4 h-4 text-indigo-600" />
              <span>Transcribe AI Safety Findings</span>
            </button>

            <button
              type="button"
              onClick={() => setReportType('CUSTOM_PHARMACIST_REPORT')}
              className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-bold transition-all ${
                reportType === 'CUSTOM_PHARMACIST_REPORT'
                  ? 'bg-white text-indigo-950 shadow-xs ring-1 ring-slate-300'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <UserCheck className="w-4 h-4 text-teal-600" />
              <span>Compose Custom Pharmacist Report</span>
            </button>
          </div>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSend} className="flex-1 overflow-y-auto p-6 space-y-5">
          {error && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Recipient & Subject */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                Recipient Physician *
              </label>
              <input
                type="text"
                value={recipientDoctor}
                onChange={(e) => setRecipientDoctor(e.target.value)}
                placeholder="Dr. Prescriber Name, MD"
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 bg-white"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                Subject Line *
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 bg-white font-medium"
                required
              />
            </div>
          </div>

          {/* Attached AI Findings Selection (in AI findings mode) */}
          {reportType === 'AI_FINDINGS_REPORT' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Select AI Findings to Include in Doctor Report</span>
                </label>
                <span className="text-[11px] text-slate-500 font-mono">
                  {review.findings.length} findings available
                </span>
              </div>

              {review.findings.length === 0 ? (
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-500 text-center">
                  No critical findings recorded for this prescription.
                </div>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {review.findings.map((f, idx) => {
                    const fid = f.finding_id || `idx-${idx}`;
                    const isChecked = !!selectedFindings[fid];
                    return (
                      <div
                        key={fid}
                        onClick={() => handleToggleFinding(fid)}
                        className={`p-3 rounded-lg border text-xs cursor-pointer transition-all flex items-start gap-3 ${
                          isChecked
                            ? 'bg-indigo-50/50 border-indigo-200 ring-1 ring-indigo-200'
                            : 'bg-slate-50 border-slate-200 opacity-60'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}}
                          className="w-4 h-4 text-indigo-600 rounded border-slate-300 mt-0.5"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                f.severity === 'HIGH'
                                  ? 'bg-rose-100 text-rose-800'
                                  : 'bg-amber-100 text-amber-800'
                              }`}
                            >
                              {f.category}
                            </span>
                            <span className="font-semibold text-slate-900 truncate">
                              {f.title}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-600 mt-1 line-clamp-2">
                            {f.description}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Quick clinical templates in custom pharmacist mode */}
          {reportType === 'CUSTOM_PHARMACIST_REPORT' && (
            <div className="space-y-1.5">
              <label className="text-[11px] font-semibold text-slate-700">
                Quick Clinical Communication Templates:
              </label>
              <div className="flex flex-wrap gap-2">
                {quickTemplates.map((t, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setMessageBody(
                        `Dear ${recipientDoctor},\n\nRegarding prescription ${review.prescription_id} for ${patientName}:\n\n${t.text}\n\nRespectfully,\nClinical Pharmacist`
                      );
                    }}
                    className="px-2.5 py-1 text-[11px] bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md border border-slate-200 transition-colors"
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Message Body Textarea */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-700 mb-1">
              Clinical Report Body *
            </label>
            <textarea
              rows={6}
              value={messageBody}
              onChange={(e) => setMessageBody(e.target.value)}
              className="w-full text-xs px-3 py-2.5 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 bg-white font-mono leading-relaxed resize-none"
              required
            />
          </div>
        </form>

        {/* Modal Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-slate-400" />
            <span>Communication will be permanently archived in SQLite audit history.</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200 rounded-lg transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSend}
              disabled={loading}
              className="px-5 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RotateCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Transmitting Report...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Transmit Report to Doctor</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
