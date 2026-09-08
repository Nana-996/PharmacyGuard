import React, { useState, useEffect } from 'react';
import type { PharmacistReviewSummary } from '../types';
import { api } from '../services/api';
import { StatusBadge } from '../components/common/StatusBadge';
import { SafetyNotice } from '../components/common/SafetyNotice';
import {
  ListOrdered,
  Search,
  RefreshCw,
  AlertCircle,
  Plus
} from 'lucide-react';

interface ReviewQueueViewProps {
  onOpenReview: (reviewId: string) => void;
  onOpenCaseDetails: (reviewId: string) => void;
  onNewReview: () => void;
}

type FilterTab = 'ALL' | 'PENDING' | 'HIGH_PRIORITY' | 'ESCALATED' | 'COMPLETED';

export const ReviewQueueView: React.FC<ReviewQueueViewProps> = ({
  onOpenReview,
  onOpenCaseDetails,
  onNewReview,
}) => {
  const [reviews, setReviews] = useState<PharmacistReviewSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState<FilterTab>('PENDING');

  const loadReviews = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getReviews();
      setReviews(res.data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load reviews.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReviews();
  }, []);

  const filteredReviews = reviews.filter((r) => {
    const matchesSearch =
      r.prescription_id.toLowerCase().includes(search.toLowerCase()) ||
      (r.patient_name || '').toLowerCase().includes(search.toLowerCase());
    if (!matchesSearch) return false;
    switch (activeTab) {
      case 'PENDING': return r.pharmacist_decision === 'PENDING';
      case 'HIGH_PRIORITY': return r.agent_review_status === 'HIGH_PRIORITY_REVIEW';
      case 'ESCALATED': return r.pharmacist_decision === 'ESCALATED';
      case 'COMPLETED': return r.pharmacist_decision === 'ACCEPTED' || r.pharmacist_decision === 'OVERRIDDEN';
      default: return true;
    }
  });

  const pendingCount = reviews.filter((r) => r.pharmacist_decision === 'PENDING').length;
  const highPriorityCount = reviews.filter((r) => r.agent_review_status === 'HIGH_PRIORITY_REVIEW').length;
  const escalatedCount = reviews.filter((r) => r.pharmacist_decision === 'ESCALATED').length;
  const completedCount = reviews.filter((r) => r.pharmacist_decision === 'ACCEPTED' || r.pharmacist_decision === 'OVERRIDDEN').length;

  const tabs: { key: FilterTab; label: string; count: number; activeColor: string }[] = [
    { key: 'PENDING', label: 'Pending', count: pendingCount, activeColor: 'bg-amber-50 text-amber-800 border-amber-200' },
    { key: 'HIGH_PRIORITY', label: 'High Priority', count: highPriorityCount, activeColor: 'bg-red-50 text-red-800 border-red-200' },
    { key: 'ESCALATED', label: 'Escalated', count: escalatedCount, activeColor: 'bg-indigo-50 text-indigo-800 border-indigo-200' },
    { key: 'COMPLETED', label: 'Completed', count: completedCount, activeColor: 'bg-emerald-50 text-emerald-800 border-emerald-200' },
    { key: 'ALL', label: 'All', count: reviews.length, activeColor: 'bg-slate-800 text-white border-slate-800' },
  ];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-[var(--pg-text)]">Review Queue</h2>
          <p className="text-[13px] text-[var(--pg-text-muted)]">Triage and authorise prescription dispensing</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadReviews}
            disabled={loading}
            className="p-2 text-[var(--pg-text-muted)] hover:text-[var(--pg-text-secondary)] bg-white hover:bg-slate-50 rounded-md border border-[var(--pg-border)] transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-600' : ''}`} />
          </button>
          <button
            onClick={onNewReview}
            className="px-3.5 py-2 text-[13px] font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            <span>New Review</span>
          </button>
        </div>
      </div>

      <SafetyNotice variant="card" />

      {error && (
        <div className="p-3 rounded-md bg-red-50 border border-red-100 text-red-700 text-[13px] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
          <button onClick={loadReviews} className="font-medium underline">Retry</button>
        </div>
      )}

      {/* Filters & Search */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-2.5 py-1.5 text-[12px] font-medium rounded-md transition-colors border ${
                activeTab === tab.key
                  ? tab.activeColor
                  : 'bg-white text-[var(--pg-text-secondary)] border-[var(--pg-border)] hover:bg-slate-50'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>

        <div className="relative min-w-[220px]">
          <Search className="w-3.5 h-3.5 text-[var(--pg-text-muted)] absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-[13px] text-[var(--pg-text)] bg-white border border-[var(--pg-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-[var(--pg-border)] bg-white overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead className="bg-slate-50 text-[12px] uppercase text-[var(--pg-text-muted)] font-medium border-b border-[var(--pg-border-light)]">
              <tr>
                <th className="px-4 py-2.5">Prescription</th>
                <th className="px-4 py-2.5">Patient</th>
                <th className="px-4 py-2.5">Created</th>
                <th className="px-4 py-2.5">Agent Status</th>
                <th className="px-4 py-2.5 text-center">Findings</th>
                <th className="px-4 py-2.5">Decision</th>
                <th className="px-4 py-2.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--pg-border-light)]">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-[var(--pg-text-muted)]">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-600" />
                    <span>Loading queue...</span>
                  </td>
                </tr>
              ) : filteredReviews.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-[var(--pg-text-muted)] space-y-1">
                    <ListOrdered className="w-6 h-6 mx-auto text-[var(--pg-border)]" />
                    <div className="font-medium text-[var(--pg-text-secondary)]">No matching reviews</div>
                    <p className="text-[12px]">{search ? `No results for "${search}".` : `No reviews in this filter.`}</p>
                  </td>
                </tr>
              ) : (
                filteredReviews.map((rev) => (
                  <tr key={rev.review_id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-mono font-semibold text-[var(--pg-text)]">{rev.prescription_id}</td>
                    <td className="px-4 py-3 text-[var(--pg-text-secondary)]">{rev.patient_name || 'Patient'}</td>
                    <td className="px-4 py-3 text-[var(--pg-text-muted)] text-[12px]">{new Date(rev.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3"><StatusBadge status={rev.agent_review_status} size="sm" /></td>
                    <td className="px-4 py-3 text-center">
                      <span className="px-1.5 py-0.5 rounded text-[12px] font-medium bg-slate-100 text-[var(--pg-text-secondary)]">{rev.findings_count}</span>
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={rev.pharmacist_decision} size="sm" /></td>
                    <td className="px-4 py-3 text-right space-x-1.5">
                      <button onClick={() => onOpenReview(rev.review_id)} className="px-2.5 py-1 text-[12px] font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors">
                        Open
                      </button>
                      <button onClick={() => onOpenCaseDetails(rev.review_id)} className="px-2.5 py-1 text-[12px] font-medium text-[var(--pg-text-secondary)] bg-slate-100 hover:bg-slate-200 rounded transition-colors">
                        Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
