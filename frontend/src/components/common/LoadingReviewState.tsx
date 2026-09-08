import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, Circle, Clock, ShieldAlert } from 'lucide-react';

interface LoadingReviewStateProps {
  prescriptionId?: string;
}

export const LoadingReviewState: React.FC<LoadingReviewStateProps> = ({ prescriptionId }) => {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const steps = [
    { label: 'Patient & prescription retrieval', threshold: 1, desc: 'Demographics, active diagnoses, medication regimen' },
    { label: 'Clinical safety & allergy contraindications', threshold: 3, desc: 'Deterministic cross-reactivity & dosing boundaries' },
    { label: 'Hospital pharmacy inventory verification', threshold: 6, desc: 'On-hand stock levels, batch availability, reorder limits' },
    { label: 'AI decision-support synthesis', threshold: 999, desc: 'Compiling structured findings and pharmacist recommendations' },
  ];

  return (
    <div className="rounded-xl border border-[var(--pg-border)] bg-white p-7 max-w-xl mx-auto my-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-[var(--pg-border-light)] pb-4 mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
          </div>
          <div>
            <h3 className="text-[15px] font-semibold text-[var(--pg-text)]">
              {prescriptionId ? `Reviewing ${prescriptionId}` : 'Running Clinical Review'}
            </h3>
            <p className="text-[12px] text-[var(--pg-text-secondary)]">
              Evaluating clinical safety and hospital stock availability
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-[12px] font-mono text-slate-700 font-medium">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span>{elapsed}s elapsed</span>
        </div>
      </div>

      {/* Checklist of steps */}
      <div className="space-y-3.5 mb-6">
        {steps.map((step, idx) => {
          const isComplete = elapsed >= step.threshold;
          const isCurrent = !isComplete && (idx === 0 || elapsed >= steps[idx - 1].threshold);

          return (
            <div
              key={idx}
              className={`flex items-start gap-3 p-2.5 rounded-lg border transition-all ${
                isComplete
                  ? 'bg-emerald-50/50 border-emerald-100 text-emerald-950'
                  : isCurrent
                  ? 'bg-blue-50/50 border-blue-200 text-[var(--pg-text)] ring-1 ring-blue-400/20'
                  : 'bg-slate-50/50 border-transparent text-[var(--pg-text-muted)]'
              }`}
            >
              <div className="mt-0.5 shrink-0">
                {isComplete ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                ) : (
                  <Circle className="w-4 h-4 text-slate-300" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[13px] font-medium leading-tight">{step.label}</div>
                <div className="text-[11px] text-[var(--pg-text-muted)] mt-0.5">{step.desc}</div>
              </div>
              {isComplete && (
                <span className="text-[10px] uppercase font-semibold tracking-wider text-emerald-700 bg-emerald-100/70 px-1.5 py-0.5 rounded">
                  Done
                </span>
              )}
              {isCurrent && (
                <span className="text-[10px] uppercase font-semibold tracking-wider text-blue-700 bg-blue-100/70 px-1.5 py-0.5 rounded animate-pulse">
                  Analyzing
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Helpful reassurance footer */}
      <div className="p-3 bg-slate-50 rounded-lg border border-[var(--pg-border-light)] flex items-start gap-2 text-[12px] text-[var(--pg-text-secondary)]">
        <ShieldAlert className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
        <span>
          PharmacyGuard executes deterministic validation checks followed by AI synthesis. Verification typically completes within 10–18 seconds.
        </span>
      </div>
    </div>
  );
};
