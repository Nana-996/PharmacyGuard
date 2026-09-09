import React, { useState, useEffect } from 'react';
import { ShieldAlert, Cpu, Sparkles } from 'lucide-react';

interface QuotaData {
  max_quota: number;
  used: number;
  remaining: number;
  quota_exhausted: boolean;
}

export const DemoNoticeBanner: React.FC = () => {
  const [quota, setQuota] = useState<QuotaData | null>(null);

  const fetchQuota = async () => {
    try {
      const res = await fetch('/api/demo/quota');
      if (res.ok) {
        const json = await res.json();
        if (json.quota) {
          setQuota(json.quota);
        }
      }
    } catch {
      // Non-blocking quota fetch
    }
  };

  useEffect(() => {
    fetchQuota();
    const interval = setInterval(fetchQuota, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-slate-900 border-b border-slate-800 text-slate-200 text-xs px-4 py-1.5 flex flex-wrap items-center justify-between gap-2 z-50 select-none shadow-sm">
      {/* Left: Badge & Core Policy */}
      <div className="flex items-center gap-2.5">
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-semibold tracking-wider text-[10px] uppercase border border-blue-400/30">
          <ShieldAlert className="w-3 h-3 text-blue-400" />
          Competition Demo
        </span>
        <span className="hidden sm:inline text-slate-400">·</span>
        <span className="text-[11px] text-slate-300 font-medium">
          Synthetic Clinical Data Only <span className="hidden md:inline text-slate-500">(No real PHI accepted)</span>
        </span>
        <span className="hidden md:inline text-slate-400">·</span>
        <span className="hidden md:inline-flex items-center gap-1 text-[11px] text-emerald-300 font-medium">
          <Cpu className="w-3 h-3 text-emerald-400" />
          Server-Side Bedrock Gating
        </span>
      </div>

      {/* Right: AI Quota & HITL indicator */}
      <div className="flex items-center gap-2 text-[11px]">
        {quota && (
          <div
            className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[10px] font-semibold ${
              quota.remaining <= 3
                ? 'bg-red-500/20 text-red-300 border-red-500/40'
                : 'bg-slate-800 text-slate-300 border-slate-700'
            }`}
            title="Public competition demo quota per session to protect AWS Bedrock API resources"
          >
            <Sparkles className="w-2.5 h-2.5 text-amber-400" />
            <span>
              {quota.remaining}/{quota.max_quota} AI Calls Left
            </span>
          </div>
        )}
        <span className="hidden lg:inline text-[10px] text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/50">
          Human-in-the-Loop Enforced
        </span>
      </div>
    </div>
  );
};
