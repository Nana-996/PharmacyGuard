import React, { useState, useEffect } from 'react';
import type { PharmacistReview, PrescriptionDetails } from '../types';
import { api } from '../services/api';
import { StatusBadge } from '../components/common/StatusBadge';
import { FindingCard } from '../components/common/FindingCard';
import { PharmacistDecisionPanel } from '../components/common/PharmacistDecisionPanel';
import { LoadingReviewState } from '../components/common/LoadingReviewState';
import { SafetyNotice } from '../components/common/SafetyNotice';
import { EditPrescriptionModal } from '../components/prescriptions/EditPrescriptionModal';
import { PrescriberReportModal } from '../components/prescriptions/PrescriberReportModal';
import { PrescriberCommunicationsHistory } from '../components/prescriptions/PrescriberCommunicationsHistory';
import {
  AlertCircle, CheckCircle2, FileCheck2, Package, FileText,
  ArrowLeft, Edit3, Send, ShieldCheck, PackageCheck, Search
} from 'lucide-react';

interface PrescriptionReviewViewProps {
  initialRxId?: string;
  initialReviewId?: string;
  onNavigateToCaseDetails: (reviewId: string) => void;
  onBackToDashboard: () => void;
}

export const PrescriptionReviewView: React.FC<PrescriptionReviewViewProps> = ({
  initialRxId = 'RX-1003', initialReviewId, onNavigateToCaseDetails, onBackToDashboard,
}) => {
  const [prescriptionId, setPrescriptionId] = useState(initialRxId);
  const [review, setReview] = useState<PharmacistReview | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [dispenseLoading, setDispenseLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [dispenseSuccess, setDispenseSuccess] = useState<any | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  const handleDispense = async () => {
    if (!review) return;
    setDispenseLoading(true); setError(null); setSuccessMessage(null);
    try {
      const res = await api.dispensePrescription(review.review_id, { notes: 'Physical dispensing confirmed.' });
      setDispenseSuccess(res.data);
      setSuccessMessage('Prescription dispensed. Inventory stock decremented.');
    } catch (err: any) { setError(err?.message || 'Failed to dispense.'); } finally { setDispenseLoading(false); }
  };

  useEffect(() => {
    if (initialReviewId) loadReviewById(initialReviewId);
    else if (initialRxId) setPrescriptionId(initialRxId);
  }, [initialReviewId, initialRxId]);

  const loadReviewById = async (id: string) => {
    setLoading(true); setError(null);
    try { const res = await api.getReview(id); setReview(res.data); setPrescriptionId(res.data.prescription_id); }
    catch (err: any) { setError(err?.message || `Failed to load review ${id}`); }
    finally { setLoading(false); }
  };

  const handleStartReview = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prescriptionId.trim()) { setError('Enter a prescription ID.'); return; }
    setLoading(true); setError(null); setSuccessMessage(null); setReview(null);
    try {
      const res = await api.createReview(prescriptionId.trim().toUpperCase());
      setReview(res.data);
      setSuccessMessage(`Review complete for ${res.data.prescription_id}.`);
    } catch (err: any) { setError(err?.message || `Error reviewing ${prescriptionId}.`); }
    finally { setLoading(false); }
  };

  const handleAccept = async (notes?: string) => { if (!review) return; setActionLoading(true); try { const res = await api.acceptReview(review.review_id, notes); setReview(res.data); setSuccessMessage('Review accepted.'); } catch (err: any) { setError(err?.message || 'Failed.'); } finally { setActionLoading(false); } };
  const handleOverride = async (notes: string) => { if (!review) return; setActionLoading(true); try { const res = await api.overrideReview(review.review_id, notes); setReview(res.data); setSuccessMessage('Review overridden with rationale.'); } catch (err: any) { setError(err?.message || 'Failed.'); } finally { setActionLoading(false); } };
  const handleEscalate = async (notes: string) => { if (!review) return; setActionLoading(true); try { const res = await api.escalateReview(review.review_id, notes); setReview(res.data); setSuccessMessage('Escalated to Chief Pharmacist.'); } catch (err: any) { setError(err?.message || 'Failed.'); } finally { setActionLoading(false); } };

  const handlePrescriptionSaved = (updatedRx: PrescriptionDetails, reReviewResult?: any) => {
    if (reReviewResult) { setReview(reReviewResult); setSuccessMessage('Prescription updated and re-verified.'); }
    else if (review) { setReview({ ...review, prescription_details: updatedRx }); setSuccessMessage('Prescription updated.'); }
  };

  const handlePrescriberReportSent = (newComm: any) => {
    if (review) { setReview({ ...review, prescriber_communications: [newComm, ...(review.prescriber_communications || [])] }); setSuccessMessage(`Report sent to ${newComm.recipient_doctor}.`); }
  };

  const clinicalFindings = review?.findings.filter((f) => f.category !== 'INVENTORY') || [];
  const inventoryFindings = review?.findings.filter((f) => f.category === 'INVENTORY') || [];

  return (
    <div className="space-y-5">
      {/* Header & Search */}
      <div className="bg-white p-4 rounded-lg border border-[var(--pg-border)] space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <button onClick={onBackToDashboard} className="p-1.5 rounded-md text-[var(--pg-text-muted)] hover:text-[var(--pg-text)] hover:bg-slate-100 border border-[var(--pg-border)] transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <h2 className="text-lg font-semibold text-[var(--pg-text)]">Prescription Review</h2>
              <p className="text-[13px] text-[var(--pg-text-muted)]">AI verification and pharmacist decision</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            {['RX-1001', 'RX-1002', 'RX-1003', 'RX-1004', 'RX-1005'].map((id) => (
              <button key={id} onClick={() => setPrescriptionId(id)} className={`px-2 py-1 text-[12px] font-mono font-medium rounded border transition-colors ${prescriptionId === id ? 'bg-blue-50 border-blue-200 text-blue-700' : 'bg-white border-[var(--pg-border)] text-[var(--pg-text-secondary)] hover:bg-slate-50'}`}>{id}</button>
            ))}
          </div>
        </div>
        <form onSubmit={handleStartReview} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-[var(--pg-text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
            <input type="text" placeholder="Enter Prescription ID..." value={prescriptionId} onChange={(e) => setPrescriptionId(e.target.value)} disabled={loading} className="w-full pl-9 pr-3 py-2 text-[13px] text-[var(--pg-text)] bg-white border border-[var(--pg-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono uppercase font-semibold" />
          </div>
          <button type="submit" disabled={loading || !prescriptionId.trim()} className="px-4 py-2 text-[13px] font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-md transition-colors shrink-0">Start Review</button>
        </form>
      </div>

      <SafetyNotice variant="card" />

      {error && (<div className="p-3 rounded-md bg-red-50 border border-red-100 text-red-700 text-[13px] flex items-center gap-2"><AlertCircle className="w-4 h-4 shrink-0" /><span>{error}</span></div>)}
      {successMessage && (
        <div className="p-3 rounded-md bg-emerald-50 border border-emerald-100 text-emerald-800 text-[13px] space-y-1.5">
          <div className="flex items-center gap-2 font-medium"><CheckCircle2 className="w-4 h-4 shrink-0" /><span>{successMessage}</span></div>
          {dispenseSuccess?.dispensed_items?.length > 0 && (
            <div className="text-[12px] text-emerald-700 bg-white/70 p-2 rounded border border-emerald-100 flex flex-wrap gap-2">
              {dispenseSuccess.dispensed_items.map((item: any, idx: number) => (<span key={idx}>✓ {item.medication} ({item.strength}): -{item.quantity_dispensed} units (Stock: {item.new_stock})</span>))}
            </div>
          )}
        </div>
      )}

      {loading && <LoadingReviewState prescriptionId={prescriptionId} />}

      {review && !loading && (
        <div className="space-y-5">
          {/* Review Header */}
          <div className="bg-white p-5 rounded-lg border border-[var(--pg-border)] space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-4 pb-3 border-b border-[var(--pg-border-light)]">
              <div>
                <div className="text-[12px] text-[var(--pg-text-muted)]">Review: {review.review_id} · {new Date(review.created_at).toLocaleString()}</div>
                <h1 className="text-xl font-bold text-[var(--pg-text)]">Prescription {review.prescription_id}</h1>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {(review.pharmacist_decision === 'ACCEPTED' || review.pharmacist_decision === 'OVERRIDDEN' || Boolean(review.escalation_resolutions && review.escalation_resolutions.length > 0)) && (
                  <button type="button" onClick={handleDispense} disabled={dispenseLoading} className="px-3 py-1.5 text-[13px] font-medium text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 rounded-md transition-colors flex items-center gap-1.5">
                    <PackageCheck className="w-3.5 h-3.5" /><span>{dispenseLoading ? 'Dispensing...' : 'Dispense'}</span>
                  </button>
                )}
                {review.prescription_details && (
                  <button type="button" onClick={() => setIsEditModalOpen(true)} className="px-3 py-1.5 text-[13px] font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors flex items-center gap-1.5">
                    <Edit3 className="w-3.5 h-3.5" /><span>Edit</span>
                  </button>
                )}
                <button type="button" onClick={() => setIsReportModalOpen(true)} className="px-3 py-1.5 text-[13px] font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-md transition-colors flex items-center gap-1.5">
                  <Send className="w-3.5 h-3.5" /><span>Doctor Report</span>
                </button>
                <StatusBadge status={review.agent_review_status} size="lg" />
              </div>
            </div>

            {/* Escalation Resolution */}
            {review.escalation_resolutions && review.escalation_resolutions.length > 0 && (
              <div className="p-3.5 rounded-md bg-indigo-50 border border-indigo-100 text-[13px] space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-medium text-indigo-900"><ShieldCheck className="w-4 h-4" /><span>Chief Pharmacist Resolution</span></div>
                  <span className="px-1.5 py-0.5 rounded bg-indigo-100 text-[10px] font-medium text-indigo-800">{review.escalation_resolutions[0].chief_decision}</span>
                </div>
                <div className="text-indigo-800 bg-white/80 p-2.5 rounded border border-indigo-100">{review.escalation_resolutions[0].chief_notes}</div>
                {review.escalation_resolutions[0].action_required && (<div className="text-indigo-900 text-[12px] font-medium"><strong>Action:</strong> {review.escalation_resolutions[0].action_required}</div>)}
              </div>
            )}

            {/* Patient Summary */}
            {review.prescription_details && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[13px]">
                <div className="p-3 rounded-md bg-slate-50 border border-[var(--pg-border-light)]">
                  <div className="text-[11px] font-medium uppercase text-[var(--pg-text-muted)]">Patient</div>
                  <div className="font-semibold text-[var(--pg-text)] mt-0.5">{review.prescription_details.patient.name}</div>
                  <div className="text-[var(--pg-text-secondary)] mt-0.5">{review.prescription_details.patient.age} yrs · {review.prescription_details.patient.sex}</div>
                  {review.prescription_details.patient.allergies && (<div className="text-red-600 font-medium mt-1 text-[12px]">Allergies: {review.prescription_details.patient.allergies}</div>)}
                </div>
                <div className="p-3 rounded-md bg-slate-50 border border-[var(--pg-border-light)]">
                  <div className="text-[11px] font-medium uppercase text-[var(--pg-text-muted)]">Diagnosis</div>
                  {review.prescription_details.diagnoses.map((d, idx) => (<div key={idx} className="font-semibold text-[var(--pg-text)] mt-0.5">{d.diagnosis}</div>))}
                  <div className="text-[var(--pg-text-muted)] text-[12px] mt-1">Dr. {review.prescription_details.prescribing_doctor}</div>
                </div>
                <div className="p-3 rounded-md bg-slate-50 border border-[var(--pg-border-light)]">
                  <div className="text-[11px] font-medium uppercase text-[var(--pg-text-muted)]">Medications</div>
                  {review.prescription_details.medications.map((m, idx) => (
                    <div key={idx} className="text-[var(--pg-text)] font-semibold mt-0.5">{m.medication} {m.strength && `(${m.strength})`}
                      <div className="text-[var(--pg-text-secondary)] text-[12px] font-normal">{m.dosage} · {m.frequency} · {m.duration}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Clinical Findings */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <FileCheck2 className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-semibold text-[var(--pg-text)]">Clinical Findings ({clinicalFindings.length})</h3>
            </div>
            {clinicalFindings.length === 0 ? (
              <div className="p-5 rounded-lg border border-emerald-100 bg-emerald-50 text-center text-emerald-800 text-[13px]">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 mx-auto mb-1.5" />
                <div className="font-medium">All Clinical Checks Clear</div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">{clinicalFindings.map((f, idx) => <FindingCard key={idx} finding={f} index={idx} />)}</div>
            )}
          </div>

          {/* Inventory Findings */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Package className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-semibold text-[var(--pg-text)]">Inventory Verification ({inventoryFindings.length})</h3>
            </div>
            {inventoryFindings.length === 0 ? (
              <div className="p-4 rounded-lg border border-[var(--pg-border-light)] bg-slate-50 text-center text-[var(--pg-text-muted)] text-[13px]">No inventory findings.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">{inventoryFindings.map((f, idx) => <FindingCard key={idx} finding={f} index={idx} />)}</div>
            )}
          </div>

          {/* Communications */}
          <PrescriberCommunicationsHistory communications={review.prescriber_communications} onOpenReportModal={() => setIsReportModalOpen(true)} />

          {/* Decision Panel */}
          <PharmacistDecisionPanel review={review} onActionSuccess={(updated) => setReview(updated)} onAccept={handleAccept} onOverride={handleOverride} onEscalate={handleEscalate} isSubmitting={actionLoading} />

          {/* Dossier Link */}
          <div className="flex justify-end">
            <button onClick={() => onNavigateToCaseDetails(review.review_id)} className="px-3 py-1.5 text-[13px] font-medium text-[var(--pg-text-secondary)] hover:text-[var(--pg-text)] bg-white hover:bg-slate-50 rounded-md border border-[var(--pg-border)] transition-colors flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5" /><span>View Full Case Dossier</span>
            </button>
          </div>
        </div>
      )}

      {review?.prescription_details && <EditPrescriptionModal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} prescription={review.prescription_details} onSaved={handlePrescriptionSaved} />}
      {review && <PrescriberReportModal isOpen={isReportModalOpen} onClose={() => setIsReportModalOpen(false)} review={review} onSent={handlePrescriberReportSent} />}
    </div>
  );
};
