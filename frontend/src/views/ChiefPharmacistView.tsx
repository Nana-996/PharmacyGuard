import React, { useEffect, useState } from 'react';
import type { DashboardAnalytics, EscalationSummary } from '../types';
import { api } from '../services/api';
import { SafetyNotice } from '../components/common/SafetyNotice';
import { ChiefEscalationResolutionModal } from '../components/chief/ChiefEscalationResolutionModal';
import { ArrowUpRight, RefreshCw, AlertCircle, ShieldCheck } from 'lucide-react';

interface ChiefPharmacistViewProps {
  onOpenCaseDetails: (reviewId: string) => void;
  onOpenReview: (reviewId: string) => void;
}

export const ChiefPharmacistView: React.FC<ChiefPharmacistViewProps> = ({ onOpenCaseDetails, onOpenReview }) => {
  const [data, setData] = useState<DashboardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEscalation, setSelectedEscalation] = useState<EscalationSummary | null>(null);
  const [resolutionModalOpen, setResolutionModalOpen] = useState(false);

  const loadData = async () => {
    setLoading(true); setError(null);
    try { const res = await api.getDashboardAnalytics(); setData(res.data); }
    catch (err: any) { setError(err?.message || 'Failed to load analytics.'); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, []);

  const cards = data?.summary_cards || { total_reviews: 0, pending_reviews: 0, accepted_reviews: 0, overridden_reviews: 0, escalated_reviews: 0, high_priority_reviews: 0, clear_reviews: 0, stock_health_percentage: '0%', low_stock_items: 0, out_of_stock_items: 0 };
  const totalDecided = cards.accepted_reviews + cards.overridden_reviews + cards.escalated_reviews;
  const acceptRate = totalDecided > 0 ? Math.round((cards.accepted_reviews / totalDecided) * 100) : 0;
  const overrideRate = totalDecided > 0 ? Math.round((cards.overridden_reviews / totalDecided) * 100) : 0;
  const escalationRate = totalDecided > 0 ? Math.round((cards.escalated_reviews / totalDecided) * 100) : 0;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-[var(--pg-text)]">Chief Pharmacist Overview</h2>
          <p className="text-[13px] text-[var(--pg-text-muted)]">Quality assurance, statistics, and escalations</p>
        </div>
        <button onClick={loadData} disabled={loading} className="px-3 py-1.5 text-[13px] font-medium text-[var(--pg-text-secondary)] bg-white hover:bg-slate-50 rounded-md border border-[var(--pg-border)] transition-colors flex items-center gap-1.5 disabled:opacity-50">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-600' : ''}`} /><span>Refresh</span>
        </button>
      </div>

      <SafetyNotice variant="card" />

      {error && (<div className="p-3 rounded-md bg-red-50 border border-red-100 text-red-700 text-[13px] flex items-center justify-between"><div className="flex items-center gap-2"><AlertCircle className="w-4 h-4" /><span>{error}</span></div><button onClick={loadData} className="font-medium underline">Retry</button></div>)}

      {/* Decision Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg border border-[var(--pg-border)] bg-white">
          <div className="text-[13px] font-medium text-[var(--pg-text-muted)]">Total Reviews</div>
          <div className="text-2xl font-bold text-[var(--pg-text)] mt-1">{cards.total_reviews}</div>
          <div className="text-[12px] text-[var(--pg-text-muted)] mt-1">{cards.pending_reviews} pending</div>
        </div>
        <div className="p-4 rounded-lg border border-[var(--pg-border)] bg-white border-l-[3px] border-l-emerald-500">
          <div className="text-[13px] font-medium text-emerald-700">Accepted</div>
          <div className="text-2xl font-bold text-[var(--pg-text)] mt-1">{cards.accepted_reviews}</div>
          <div className="text-[12px] text-[var(--pg-text-muted)] mt-1">{acceptRate}% acceptance rate</div>
        </div>
        <div className="p-4 rounded-lg border border-[var(--pg-border)] bg-white border-l-[3px] border-l-violet-500">
          <div className="text-[13px] font-medium text-violet-700">Overrides</div>
          <div className="text-2xl font-bold text-[var(--pg-text)] mt-1">{cards.overridden_reviews}</div>
          <div className="text-[12px] text-[var(--pg-text-muted)] mt-1">{overrideRate}% override rate</div>
        </div>
        <div className="p-4 rounded-lg border border-[var(--pg-border)] bg-white border-l-[3px] border-l-indigo-500">
          <div className="text-[13px] font-medium text-indigo-700">Escalations</div>
          <div className="text-2xl font-bold text-[var(--pg-text)] mt-1">{cards.escalated_reviews}</div>
          <div className="text-[12px] text-[var(--pg-text-muted)] mt-1">{escalationRate}% escalated</div>
        </div>
      </div>

      {/* Two Column: Findings & Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="p-5 rounded-lg border border-[var(--pg-border)] bg-white space-y-3">
          <div>
            <h3 className="text-sm font-semibold text-[var(--pg-text)]">Finding Categories</h3>
            <p className="text-[13px] text-[var(--pg-text-muted)]">Safety alert distribution</p>
          </div>
          {!data?.finding_categories?.length ? (
            <div className="p-6 text-center text-[var(--pg-text-muted)] text-[13px]">No findings recorded yet.</div>
          ) : (
            <div className="space-y-2.5">
              {data.finding_categories.map((fc) => (
                <div key={fc.category} className="space-y-1">
                  <div className="flex items-center justify-between text-[13px]">
                    <span className="font-medium text-[var(--pg-text)]">{fc.category}</span>
                    <span className="text-[var(--pg-text-muted)] text-[12px]">{fc.count} ({fc.high_severity_count} high)</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${fc.category === 'ALLERGY' || fc.category === 'DUPLICATION' ? 'bg-red-500' : fc.category === 'INTERACTION' ? 'bg-amber-500' : 'bg-blue-500'}`}
                      style={{ width: `${Math.min(100, Math.max(12, (fc.count / (cards.total_reviews || 1)) * 50))}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-5 rounded-lg border border-[var(--pg-border)] bg-white space-y-3">
          <div>
            <h3 className="text-sm font-semibold text-[var(--pg-text)]">Triage Distribution</h3>
            <p className="text-[13px] text-[var(--pg-text-muted)]">AI severity classifications</p>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="p-3 rounded-md border border-emerald-100 bg-emerald-50">
              <div className="text-[12px] font-medium text-emerald-700">Clear</div>
              <div className="text-xl font-bold text-[var(--pg-text)] mt-0.5">{cards.clear_reviews}</div>
            </div>
            <div className="p-3 rounded-md border border-amber-100 bg-amber-50">
              <div className="text-[12px] font-medium text-amber-700">Review</div>
              <div className="text-xl font-bold text-[var(--pg-text)] mt-0.5">{cards.total_reviews - cards.high_priority_reviews - cards.clear_reviews}</div>
            </div>
            <div className="p-3 rounded-md border border-red-100 bg-red-50">
              <div className="text-[12px] font-medium text-red-700">High Priority</div>
              <div className="text-xl font-bold text-[var(--pg-text)] mt-0.5">{cards.high_priority_reviews}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Escalations Table */}
      <div className="rounded-lg border border-[var(--pg-border)] bg-white overflow-hidden">
        <div className="p-4 border-b border-[var(--pg-border-light)] flex items-center gap-2">
          <ArrowUpRight className="w-4 h-4 text-indigo-600" />
          <div>
            <h3 className="text-sm font-semibold text-[var(--pg-text)]">Escalations</h3>
            <p className="text-[13px] text-[var(--pg-text-muted)]">Cases requiring senior review</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead className="bg-slate-50 text-[12px] uppercase text-[var(--pg-text-muted)] font-medium border-b border-[var(--pg-border-light)]">
              <tr>
                <th className="px-4 py-2.5">Prescription</th>
                <th className="px-4 py-2.5">Patient</th>
                <th className="px-4 py-2.5">Escalating Pharmacist</th>
                <th className="px-4 py-2.5">Reason</th>
                <th className="px-4 py-2.5">Date</th>
                <th className="px-4 py-2.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--pg-border-light)]">
              {loading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-[var(--pg-text-muted)]"><RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-600" />Loading...</td></tr>
              ) : !data?.recent_escalations?.length ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-[var(--pg-text-muted)]">No escalations.</td></tr>
              ) : (
                data.recent_escalations.map((esc) => (
                  <tr key={esc.review_id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-mono font-semibold text-indigo-700">{esc.prescription_id}</td>
                    <td className="px-4 py-3 text-[var(--pg-text-secondary)]">{esc.patient_name || 'Patient'}</td>
                    <td className="px-4 py-3 text-[var(--pg-text-secondary)]">{esc.pharmacist_id || 'N/A'}</td>
                    <td className="px-4 py-3 text-[var(--pg-text-secondary)] max-w-md break-words">{esc.reason}</td>
                    <td className="px-4 py-3 text-[var(--pg-text-muted)] text-[12px]">{esc.timestamp ? new Date(esc.timestamp).toLocaleString() : 'Recent'}</td>
                    <td className="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
                      <button onClick={() => { setSelectedEscalation(esc); setResolutionModalOpen(true); }} className="px-2.5 py-1 text-[12px] font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded transition-colors inline-flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3" /><span>Resolve</span>
                      </button>
                      <button onClick={() => onOpenReview(esc.review_id)} className="px-2.5 py-1 text-[12px] font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded transition-colors">Review</button>
                      <button onClick={() => onOpenCaseDetails(esc.review_id)} className="px-2.5 py-1 text-[12px] font-medium text-[var(--pg-text-secondary)] bg-slate-100 hover:bg-slate-200 rounded transition-colors">Details</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selectedEscalation && (
        <ChiefEscalationResolutionModal isOpen={resolutionModalOpen} onClose={() => { setResolutionModalOpen(false); setSelectedEscalation(null); }} reviewId={selectedEscalation.review_id} prescriptionId={selectedEscalation.prescription_id} patientName={selectedEscalation.patient_name} escalatingPharmacist={selectedEscalation.pharmacist_id} escalationReason={selectedEscalation.reason} onSuccess={loadData} />
      )}
    </div>
  );
};
