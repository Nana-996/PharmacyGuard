import React, { useEffect, useState } from 'react';
import type { InventoryItem, InventorySummary } from '../types';
import { api } from '../services/api';
import { StatusBadge } from '../components/common/StatusBadge';
import { SafetyNotice } from '../components/common/SafetyNotice';
import { AlertTriangle, Search, RefreshCw, AlertCircle } from 'lucide-react';

export const InventoryView: React.FC = () => {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [lowStockItems, setLowStockItems] = useState<InventoryItem[]>([]);
  const [summary, setSummary] = useState<InventorySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [invRes, lowRes, sumRes] = await Promise.all([
        api.getInventory(), api.getLowStockItems(), api.getInventorySummary(),
      ]);
      setItems(invRes.data);
      setLowStockItems(lowRes.data);
      setSummary(sumRes.data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load inventory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const filteredItems = items.filter((item) => {
    const matchesSearch = item.medication.toLowerCase().includes(search.toLowerCase()) || item.generic_name.toLowerCase().includes(search.toLowerCase());
    if (!matchesSearch) return false;
    if (statusFilter === 'ALL') return true;
    return item.stock_status.toUpperCase() === statusFilter.toUpperCase();
  });

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-[var(--pg-text)]">Pharmacy Inventory</h2>
          <p className="text-[13px] text-[var(--pg-text-muted)]">Stock levels and formulary catalog</p>
        </div>
        <button onClick={loadData} disabled={loading} className="px-3 py-1.5 text-[13px] font-medium text-[var(--pg-text-secondary)] bg-white hover:bg-slate-50 rounded-md border border-[var(--pg-border)] transition-colors flex items-center gap-1.5 disabled:opacity-50">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-600' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      <SafetyNotice variant="card" />

      {error && (
        <div className="p-3 rounded-md bg-red-50 border border-red-100 text-red-700 text-[13px] flex items-center justify-between">
          <div className="flex items-center gap-2"><AlertCircle className="w-4 h-4" /><span>{error}</span></div>
          <button onClick={loadData} className="font-medium underline">Retry</button>
        </div>
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg border border-[var(--pg-border)] bg-white">
            <div className="text-[13px] font-medium text-[var(--pg-text-muted)]">Total Catalog</div>
            <div className="text-2xl font-bold text-[var(--pg-text)] mt-1">{summary.total_tracked_medications}</div>
            <div className="text-[12px] text-[var(--pg-text-muted)] mt-1">Formulary medications</div>
          </div>
          <div className="p-4 rounded-lg border border-[var(--pg-border)] bg-white border-l-[3px] border-l-emerald-500">
            <div className="text-[13px] font-medium text-emerald-700">Adequate Stock</div>
            <div className="text-2xl font-bold text-[var(--pg-text)] mt-1">{summary.number_available}</div>
            <div className="text-[12px] text-[var(--pg-text-muted)] mt-1">Above reorder level</div>
          </div>
          <div className="p-4 rounded-lg border border-[var(--pg-border)] bg-white border-l-[3px] border-l-amber-500">
            <div className="text-[13px] font-medium text-amber-700">Low Stock</div>
            <div className="text-2xl font-bold text-[var(--pg-text)] mt-1">{summary.number_low_stock}</div>
            <div className="text-[12px] text-[var(--pg-text-muted)] mt-1">At or below threshold</div>
          </div>
          <div className="p-4 rounded-lg border border-[var(--pg-border)] bg-white border-l-[3px] border-l-red-500">
            <div className="text-[13px] font-medium text-red-700">Out of Stock</div>
            <div className="text-2xl font-bold text-[var(--pg-text)] mt-1">{summary.number_out_of_stock}</div>
            <div className="text-[12px] text-[var(--pg-text-muted)] mt-1">Immediate replenishment</div>
          </div>
        </div>
      )}

      {/* Low Stock Alerts */}
      <div className="p-4 rounded-lg border border-[var(--pg-border)] bg-white space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <h3 className="text-sm font-semibold text-[var(--pg-text)]">Low & Out-of-Stock Alerts ({lowStockItems.length})</h3>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
          {lowStockItems.map((item) => (
            <div key={item.inventory_id} className="p-3 rounded-md border border-[var(--pg-border-light)] bg-slate-50 space-y-1">
              <div className="flex items-start justify-between gap-1">
                <span className="font-medium text-[13px] text-[var(--pg-text)] truncate">{item.medication}</span>
                <StatusBadge status={item.stock_status} size="sm" />
              </div>
              <div className="text-[12px] text-[var(--pg-text-muted)]">{item.dosage_form} · {item.strength}</div>
              <div className="flex items-center justify-between pt-1.5 border-t border-[var(--pg-border-light)] text-[12px]">
                <span className="text-[var(--pg-text-secondary)]">On Hand: <strong className="text-[var(--pg-text)]">{item.quantity_on_hand}</strong> {item.unit}</span>
                <span className="text-red-600 font-medium">-{item.deficit_to_reorder}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Full Catalog Table */}
      <div className="rounded-lg border border-[var(--pg-border)] bg-white overflow-hidden">
        <div className="p-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-[var(--pg-text)]">Catalog ({filteredItems.length})</h3>
            <p className="text-[13px] text-[var(--pg-text-muted)]">Quantity on hand and threshold levels</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative min-w-[180px]">
              <Search className="w-3.5 h-3.5 text-[var(--pg-text-muted)] absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input type="text" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full pl-8 pr-3 py-1.5 text-[13px] text-[var(--pg-text)] bg-white border border-[var(--pg-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-2.5 py-1.5 text-[13px] text-[var(--pg-text-secondary)] bg-white border border-[var(--pg-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="ALL">All Statuses</option>
              <option value="AVAILABLE">Available</option>
              <option value="LOW STOCK">Low Stock</option>
              <option value="OUT OF STOCK">Out of Stock</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead className="bg-slate-50 text-[12px] uppercase text-[var(--pg-text-muted)] font-medium border-y border-[var(--pg-border-light)]">
              <tr>
                <th className="px-4 py-2.5">ID</th>
                <th className="px-4 py-2.5">Medication</th>
                <th className="px-4 py-2.5">Generic</th>
                <th className="px-4 py-2.5">Strength & Form</th>
                <th className="px-4 py-2.5 text-center">On Hand</th>
                <th className="px-4 py-2.5 text-center">Reorder Level</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5 text-right">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--pg-border-light)]">
              {loading ? (
                <tr><td colSpan={8} className="px-4 py-10 text-center text-[var(--pg-text-muted)]"><RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-600" /><span>Loading inventory...</span></td></tr>
              ) : filteredItems.length === 0 ? (
                <tr><td colSpan={8} className="px-4 py-10 text-center text-[var(--pg-text-muted)]">No medications match your filter.</td></tr>
              ) : (
                filteredItems.map((item) => (
                  <tr key={item.inventory_id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-mono text-[var(--pg-text-muted)] text-[12px]">{item.inventory_id}</td>
                    <td className="px-4 py-3 font-semibold text-[var(--pg-text)]">{item.medication}</td>
                    <td className="px-4 py-3 text-[var(--pg-text-secondary)] italic">{item.generic_name}</td>
                    <td className="px-4 py-3 text-[var(--pg-text-secondary)]">{item.strength} · {item.dosage_form}</td>
                    <td className="px-4 py-3 text-center font-semibold text-[var(--pg-text)]">{item.quantity_on_hand} <span className="text-[10px] text-[var(--pg-text-muted)] font-normal">{item.unit}</span></td>
                    <td className="px-4 py-3 text-center text-[var(--pg-text-muted)]">{item.reorder_level} {item.unit}</td>
                    <td className="px-4 py-3"><StatusBadge status={item.stock_status} size="sm" /></td>
                    <td className="px-4 py-3 text-right text-[12px] text-[var(--pg-text-muted)]">{item.last_updated}</td>
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
