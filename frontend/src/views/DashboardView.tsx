import React, { useEffect, useState } from 'react';
import type { DashboardAnalytics } from '../types';
import { api } from '../services/api';
import { StatusBadge } from '../components/common/StatusBadge';
import { SafetyNotice } from '../components/common/SafetyNotice';
import {
  Clock,
  AlertCircle,
  AlertTriangle,
  Package,
  ArrowRight,
  Search,
  RefreshCw
} from 'lucide-react';

interface DashboardViewProps {
  onStartReview: (rxId: string) => void;
  onOpenReview: (reviewId: string) => void;
  onOpenCaseDetails: (reviewId: string) => void;
  onNavigateToQueue: () => void;
  onNavigateToInventory: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onStartReview,
  onOpenReview,
  onOpenCaseDetails,
  onNavigateToQueue,
  onNavigateToInventory,
}) => {
  const [data, setData] = useState<DashboardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [quickRxInput, setQuickRxInput] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getDashboardAnalytics();
      setData(res.data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load dashboard.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const sampleCases = [
    { id: 'RX-1001', label: 'Amoxicillin', tag: 'Standard' },
    { id: 'RX-1002', label: 'Lisinopril', tag: 'Indication' },
    { id: 'RX-1003', label: 'Augmentin', tag: 'Allergy' },
    { id: 'RX-1004', label: 'Dual NSAID', tag: 'Duplication' },
    { id: 'RX-1005', label: 'Multi-Drug', tag: '4 Meds' },
  ];

  const cards = data?.summary_cards || {
    pending_reviews: 0,
    high_priority_reviews: 0,
    low_stock_items: 0,
    out_of_stock_items: 0,
    total_reviews: 0,
    accepted_reviews: 0,
    overridden_reviews: 0,
    escalated_reviews: 0,
    clear_reviews: 0,
    stock_health_percentage: '0%'
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-[var(--pg-text)]">Dashboard</h2>
          <p className="text-[13px] text-[var(--pg-text-muted)]">Pharmacy operations overview</p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="px-3 py-1.5 text-[13px] font-medium text-[var(--pg-text-secondary)] bg-white hover:bg-slate-50 rounded-md border border-[var(--pg-border)] transition-colors flex items-center gap-1.5 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-600' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      <SafetyNotice variant="card" />

      {error && (
        <div className="p-3 rounded-md bg-red-50 border border-red-100 text-red-700 text-[13px] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
          <button onClick={loadData} className="font-medium underline">Retry</button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          onClick={onNavigateToQueue}
          className="p-4 rounded-lg border border-[var(--pg-border)] bg-white border-l-[3px] border-l-amber-500 hover:shadow-sm transition-shadow cursor-pointer"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[13px] font-medium text-[var(--pg-text-secondary)]">Pending Reviews</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-[var(--pg-text)]">
            {loading ? '—' : cards.pending_reviews}
          </div>
          <div className="text-[12px] text-[var(--pg-text-muted)] mt-1">Awaiting decision</div>
        </div>

        <div
          onClick={onNavigateToQueue}
          className="p-4 rounded-lg border border-[var(--pg-border)] bg-white border-l-[3px] border-l-red-500 hover:shadow-sm transition-shadow cursor-pointer"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[13px] font-medium text-[var(--pg-text-secondary)]">High Priority</span>
            <AlertCircle className="w-4 h-4 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-[var(--pg-text)]">
            {loading ? '—' : cards.high_priority_reviews}
          </div>
          <div className="text-[12px] text-[var(--pg-text-muted)] mt-1">Critical safety flags</div>
        </div>

        <div
          onClick={onNavigateToInventory}
          className="p-4 rounded-lg border border-[var(--pg-border)] bg-white border-l-[3px] border-l-amber-400 hover:shadow-sm transition-shadow cursor-pointer"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[13px] font-medium text-[var(--pg-text-secondary)]">Low Stock</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-[var(--pg-text)]">
            {loading ? '—' : cards.low_stock_items}
          </div>
          <div className="text-[12px] text-[var(--pg-text-muted)] mt-1">Below reorder level</div>
        </div>

        <div
          onClick={onNavigateToInventory}
          className="p-4 rounded-lg border border-[var(--pg-border)] bg-white border-l-[3px] border-l-red-400 hover:shadow-sm transition-shadow cursor-pointer"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[13px] font-medium text-[var(--pg-text-secondary)]">Out of Stock</span>
            <Package className="w-4 h-4 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-[var(--pg-text)]">
            {loading ? '—' : cards.out_of_stock_items}
          </div>
          <div className="text-[12px] text-[var(--pg-text-muted)] mt-1">0 units available</div>
        </div>
      </div>

      {/* Quick Review Launcher */}
      <div className="p-4 rounded-lg border border-[var(--pg-border)] bg-white space-y-3">
        <div>
          <h3 className="text-sm font-semibold text-[var(--pg-text)]">Start Prescription Review</h3>
          <p className="text-[13px] text-[var(--pg-text-muted)]">Enter a prescription ID or select a test case</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-[var(--pg-text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Enter prescription ID (e.g. RX-1003)..."
              value={quickRxInput}
              onChange={(e) => setQuickRxInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && quickRxInput.trim()) {
                  onStartReview(quickRxInput.trim().toUpperCase());
                }
              }}
              className="w-full pl-9 pr-3 py-2 text-[13px] text-[var(--pg-text)] bg-white border border-[var(--pg-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono uppercase"
            />
          </div>
          <button
            onClick={() => {
              if (quickRxInput.trim()) {
                onStartReview(quickRxInput.trim().toUpperCase());
              }
            }}
            disabled={!quickRxInput.trim()}
            className="px-4 py-2 text-[13px] font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-md transition-colors shrink-0"
          >
            Start Review
          </button>
        </div>

        {/* Quick Case Tags */}
        <div className="flex flex-wrap gap-1.5 pt-1">
          {sampleCases.map((sc) => (
            <button
              key={sc.id}
              onClick={() => onStartReview(sc.id)}
              className="px-2.5 py-1 rounded-md border border-[var(--pg-border)] bg-slate-50 hover:bg-slate-100 text-[12px] font-medium text-[var(--pg-text-secondary)] hover:text-[var(--pg-text)] transition-colors flex items-center gap-1.5"
            >
              <span className="font-mono font-bold">{sc.id}</span>
              <span className="text-[var(--pg-text-muted)]">·</span>
              <span>{sc.tag}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Recent Reviews Table */}
      <div className="rounded-lg border border-[var(--pg-border)] bg-white overflow-hidden">
        <div className="p-4 border-b border-[var(--pg-border-light)] flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-[var(--pg-text)]">Recent Reviews</h3>
            <p className="text-[13px] text-[var(--pg-text-muted)]">Latest prescription reviews</p>
          </div>
          <button
            onClick={onNavigateToQueue}
            className="text-[13px] font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead className="bg-slate-50 text-[12px] uppercase text-[var(--pg-text-muted)] font-medium border-b border-[var(--pg-border-light)]">
              <tr>
                <th className="px-4 py-2.5">Prescription</th>
                <th className="px-4 py-2.5">Patient</th>
                <th className="px-4 py-2.5">Date</th>
                <th className="px-4 py-2.5">Agent Status</th>
                <th className="px-4 py-2.5">Decision</th>
                <th className="px-4 py-2.5 text-center">Findings</th>
                <th className="px-4 py-2.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--pg-border-light)]">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-[var(--pg-text-muted)]">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-600" />
                    <span>Loading...</span>
                  </td>
                </tr>
              ) : !data?.recent_reviews?.length ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-[var(--pg-text-muted)]">
                    No reviews yet. Start a review above.
                  </td>
                </tr>
              ) : (
                data.recent_reviews.map((rev) => (
                  <tr key={rev.review_id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-mono font-semibold text-[var(--pg-text)]">
                      {rev.prescription_id}
                    </td>
                    <td className="px-4 py-3 text-[var(--pg-text-secondary)]">
                      {rev.patient_name || 'Patient'}
                    </td>
                    <td className="px-4 py-3 text-[var(--pg-text-muted)] text-[12px]">
                      {new Date(rev.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={rev.agent_review_status} size="sm" />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={rev.pharmacist_decision} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[12px] font-medium bg-slate-100 text-[var(--pg-text-secondary)]">
                        {rev.findings_count}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right space-x-1.5">
                      <button
                        onClick={() => onOpenReview(rev.review_id)}
                        className="px-2.5 py-1 text-[12px] font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded transition-colors"
                      >
                        Review
                      </button>
                      <button
                        onClick={() => onOpenCaseDetails(rev.review_id)}
                        className="px-2.5 py-1 text-[12px] font-medium text-[var(--pg-text-secondary)] bg-slate-100 hover:bg-slate-200 rounded transition-colors"
                      >
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
