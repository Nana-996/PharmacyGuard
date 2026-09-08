import React, { useEffect, useState } from 'react';
import type { PharmacistReview } from '../types';
import { api } from '../services/api';
import { StatusBadge } from '../components/common/StatusBadge';
import { FindingCard } from '../components/common/FindingCard';
import { SafetyNotice } from '../components/common/SafetyNotice';
import { PrescriberCommunicationsHistory } from '../components/prescriptions/PrescriberCommunicationsHistory';
import { FileText, Activity, Calendar, AlertCircle, History, ArrowLeft, RefreshCw, Search } from 'lucide-react';

interface CaseDetailsViewProps {
  initialReviewId?: string;
  onOpenReview: (reviewId: string) => void;
  onBack: () => void;
}

export const CaseDetailsView: React.FC<CaseDetailsViewProps> = ({ initialReviewId, onOpenReview, onBack }) => {
  const [searchInput, setSearchInput] = useState(initialReviewId || '');
  const [review, setReview] = useState<PharmacistReview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCase = async (id: string) => {
    if (!id.trim()) return;
    setLoading(true); setError(null);
    try { const res = await api.getReview(id.trim()); setReview(res.data); }
    catch (err: any) { setError(err?.message || `Failed to retrieve case ${id}.`); }
    finally { setLoading(false); }
  };

  useEffect(() => { if (initialReviewId) { setSearchInput(initialReviewId); loadCase(initialReviewId); } }, [initialReviewId]);

  const handleSearchSubmit = (e: React.FormEvent) => { e.preventDefault(); if (searchInput.trim()) loadCase(searchInput.trim()); };

  const getActorBadge = (actorType: string, actorId: string) => {
    const norm = (actorType || '').toUpperCase();
    if (norm === 'AGENT') return <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700">AGENT ({actorId})</span>;
    if (norm === 'PHARMACIST') return <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-violet-50 text-violet-700">PHARMACIST ({actorId})</span>;
    if (norm.includes('CHIEF')) return <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-indigo-50 text-indigo-700">CHIEF ({actorId})</span>;
    return <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-[var(--pg-text-secondary)]">SYSTEM</span>;
  };

  return (
    <div className="space-y-5">
      {/* Header & Search */}
      <div className="bg-white p-4 rounded-lg border border-[var(--pg-border)] space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <button onClick={onBack} className="p-1.5 rounded-md text-[var(--pg-text-muted)] hover:text-[var(--pg-text)] hover:bg-slate-100 border border-[var(--pg-border)] transition-colors"><ArrowLeft className="w-4 h-4" /></button>
            <div>
              <h2 className="text-lg font-semibold text-[var(--pg-text)]">Case Dossier</h2>
              <p className="text-[13px] text-[var(--pg-text-muted)]">Clinical evidence, decisions, and audit trail</p>
            </div>
          </div>
          {review && <button onClick={() => onOpenReview(review.review_id)} className="px-3.5 py-1.5 text-[13px] font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors">Open Review</button>}
        </div>
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-[var(--pg-text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
            <input type="text" placeholder="Search by Review ID..." value={searchInput} onChange={(e) => setSearchInput(e.target.value)} className="w-full pl-9 pr-3 py-2 text-[13px] text-[var(--pg-text)] bg-white border border-[var(--pg-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono uppercase" />
          </div>
          <button type="submit" disabled={loading || !searchInput.trim()} className="px-3.5 py-2 text-[13px] font-medium text-[var(--pg-text-secondary)] bg-slate-100 hover:bg-slate-200 rounded-md border border-[var(--pg-border)] transition-colors disabled:opacity-50">Lookup</button>
        </form>
      </div>

      <SafetyNotice variant="card" />

      {error && (<div className="p-3 rounded-md bg-red-50 border border-red-100 text-red-700 text-[13px] flex items-center gap-2"><AlertCircle className="w-4 h-4 shrink-0" /><span>{error}</span></div>)}
      {loading && (<div className="p-10 text-center text-[var(--pg-text-muted)] bg-white rounded-lg border border-[var(--pg-border)]"><RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-600" /><span className="text-[13px]">Loading dossier...</span></div>)}

      {!review && !loading && !error && (
        <div className="p-10 text-center text-[var(--pg-text-muted)] bg-white rounded-lg border border-[var(--pg-border)]">
          <FileText className="w-7 h-7 text-[var(--pg-border)] mx-auto mb-2" />
          <div className="font-medium text-[var(--pg-text-secondary)]">No Case Selected</div>
          <p className="text-[13px] mt-1">Enter a Review ID or select a case from the queue.</p>
        </div>
      )}

      {review && !loading && (
        <div className="space-y-5">
          {/* Review Header */}
          <div className="bg-white p-5 rounded-lg border border-[var(--pg-border)] space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[var(--pg-border-light)]">
              <div>
                <div className="text-[12px] text-[var(--pg-text-muted)]">Review: {review.review_id}</div>
                <h1 className="text-xl font-bold text-[var(--pg-text)]">Prescription {review.prescription_id}</h1>
                <div className="text-[13px] text-[var(--pg-text-muted)] flex items-center gap-1.5 mt-0.5"><Calendar className="w-3.5 h-3.5" /><span>{new Date(review.created_at).toLocaleString()}</span></div>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right"><div className="text-[10px] font-medium uppercase text-[var(--pg-text-muted)]">Agent</div><StatusBadge status={review.agent_review_status} size="md" /></div>
                <div className="text-right"><div className="text-[10px] font-medium uppercase text-[var(--pg-text-muted)]">Decision</div><StatusBadge status={review.pharmacist_decision} size="md" /></div>
              </div>
            </div>

            {review.prescription_details && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[13px]">
                <div className="p-3 rounded-md bg-slate-50 border border-[var(--pg-border-light)]">
                  <div className="text-[11px] font-medium uppercase text-[var(--pg-text-muted)]">Patient</div>
                  <div className="font-semibold text-[var(--pg-text)] mt-0.5">{review.prescription_details.patient.name}</div>
                  <div className="text-[var(--pg-text-secondary)]">{review.prescription_details.patient.age} yrs · {review.prescription_details.patient.sex}</div>
                  <div className="text-[12px] text-[var(--pg-text-muted)]">ID: {review.prescription_details.patient.patient_id}</div>
                  {review.prescription_details.patient.allergies && (<div className="text-red-600 font-medium text-[12px] mt-1 pt-1 border-t border-[var(--pg-border-light)]">Allergies: {review.prescription_details.patient.allergies}</div>)}
                </div>
                <div className="p-3 rounded-md bg-slate-50 border border-[var(--pg-border-light)]">
                  <div className="text-[11px] font-medium uppercase text-[var(--pg-text-muted)]">Diagnosis & Prescriber</div>
                  {review.prescription_details.diagnoses.map((d, idx) => (<div key={idx}><div className="font-semibold text-[var(--pg-text)] mt-0.5">{d.diagnosis}</div>{d.diagnosis_date && <div className="text-[12px] text-[var(--pg-text-muted)]">{d.diagnosis_date}</div>}</div>))}
                  <div className="text-[var(--pg-text-secondary)] pt-1 mt-1 border-t border-[var(--pg-border-light)]">Dr. {review.prescription_details.prescribing_doctor}</div>
                </div>
                <div className="p-3 rounded-md bg-slate-50 border border-[var(--pg-border-light)]">
                  <div className="text-[11px] font-medium uppercase text-[var(--pg-text-muted)]">Medications</div>
                  {review.prescription_details.medications.map((m, idx) => (
                    <div key={idx} className="mt-1 p-2 bg-white rounded border border-[var(--pg-border-light)]">
                      <div className="font-semibold text-[var(--pg-text)]">{m.medication} {m.strength && `(${m.strength})`}</div>
                      <div className="text-[12px] text-[var(--pg-text-muted)]">{m.dosage} · {m.frequency} · {m.duration}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Decision Record */}
            <div className="p-3 rounded-md bg-slate-50 border border-[var(--pg-border-light)] text-[13px]">
              <div className="flex items-center justify-between">
                <span className="font-medium text-[var(--pg-text)]">Pharmacist Decision</span>
                <StatusBadge status={review.pharmacist_decision} size="sm" />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1 text-[var(--pg-text-secondary)] mt-1.5">
                <div>Reviewer: <strong className="text-[var(--pg-text)]">{review.reviewed_by || 'Pending'}</strong></div>
                <div>Timestamp: <strong className="text-[var(--pg-text)]">{review.reviewed_at ? new Date(review.reviewed_at).toLocaleString() : 'N/A'}</strong></div>
              </div>
              {review.pharmacist_notes && (
                <div className="mt-2 p-2.5 rounded bg-blue-50 border border-blue-100 text-blue-900 text-[13px]">
                  <span className="font-medium">Notes: </span>{review.pharmacist_notes}
                </div>
              )}
            </div>
          </div>

          {/* Findings */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-semibold text-[var(--pg-text)]">Findings ({review.findings.length})</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {review.findings.map((finding, idx) => <FindingCard key={idx} finding={finding} index={idx} />)}
            </div>
          </div>

          {/* Communications */}
          <PrescriberCommunicationsHistory communications={review.prescriber_communications} />

          {/* Audit Trail */}
          <div className="rounded-lg border border-[var(--pg-border)] bg-white p-5 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--pg-border-light)]">
              <div className="flex items-center gap-2">
                <History className="w-4 h-4 text-blue-600" />
                <div>
                  <h3 className="text-sm font-semibold text-[var(--pg-text)]">Audit Trail</h3>
                  <p className="text-[13px] text-[var(--pg-text-muted)]">Chronological event log</p>
                </div>
              </div>
              <span className="text-[12px] text-[var(--pg-text-muted)]">{review.audit_history?.length || 0} events</span>
            </div>
            <div className="space-y-2">
              {review.audit_history?.length === 0 ? (
                <div className="text-center py-4 text-[var(--pg-text-muted)] text-[13px]">No audit events.</div>
              ) : (
                review.audit_history.map((entry, idx) => (
                  <div key={entry.audit_id || idx} className="p-3 rounded-md bg-slate-50 border border-[var(--pg-border-light)] text-[13px]">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        {getActorBadge(entry.actor_type, entry.actor_id)}
                        <span className="font-medium text-[var(--pg-text)]">{entry.event_type}</span>
                      </div>
                      <div className="flex items-center gap-2 text-[12px] text-[var(--pg-text-muted)]">
                        <span>{entry.audit_id}</span><span>·</span><span>{new Date(entry.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
                    {entry.event_data && (
                      <div className="p-2 rounded bg-white text-[12px] text-[var(--pg-text-secondary)] border border-[var(--pg-border-light)] break-words mt-1.5">{entry.event_data}</div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
