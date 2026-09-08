import React, { useState } from 'react';
import type { PrescriberCommunication } from '../../types';
import {
  Send,
  Bot,
  UserCheck,
  ChevronDown,
  ChevronUp,
  Clock
} from 'lucide-react';

interface PrescriberCommunicationsHistoryProps {
  communications?: PrescriberCommunication[];
  onOpenReportModal?: () => void;
}

export const PrescriberCommunicationsHistory: React.FC<PrescriberCommunicationsHistoryProps> = ({
  communications = [],
  onOpenReportModal,
}) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-2xs overflow-hidden">
      <div className="p-4 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-indigo-100 text-indigo-800">
            <Send className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Prescriber Clinical Communications & Reports
            </h3>
            <p className="text-[11px] text-slate-500">
              Archived consultation queries and safety notifications transmitted to attending doctors
            </p>
          </div>
        </div>

        {onOpenReportModal && (
          <button
            onClick={onOpenReportModal}
            className="px-2.5 py-1 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-lg border border-indigo-200 transition-colors flex items-center gap-1.5"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Consult Doctor</span>
          </button>
        )}
      </div>

      {communications.length === 0 ? (
        <div className="p-6 text-center text-slate-400 text-xs">
          No prescriber reports or clarification queries sent for this prescription yet.
        </div>
      ) : (
        <div className="divide-y divide-slate-100">
          {communications.map((comm) => {
            const isExpanded = expandedId === comm.communication_id;
            const isAiReport = comm.report_type === 'AI_FINDINGS_REPORT';

            return (
              <div key={comm.communication_id} className="p-4 hover:bg-slate-50/60 transition-colors">
                <div
                  className="flex items-start justify-between gap-3 cursor-pointer"
                  onClick={() => toggleExpand(comm.communication_id)}
                >
                  <div className="space-y-1 flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center gap-1 ${
                          isAiReport
                            ? 'bg-indigo-100 text-indigo-800 border border-indigo-200'
                            : 'bg-teal-100 text-teal-800 border border-teal-200'
                        }`}
                      >
                        {isAiReport ? <Bot className="w-3 h-3" /> : <UserCheck className="w-3 h-3" />}
                        <span>{isAiReport ? 'AI Safety Findings' : 'Pharmacist Report'}</span>
                      </span>

                      <span className="text-xs font-bold text-slate-900 truncate">
                        {comm.subject}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono">
                      <span>To: <strong>{comm.recipient_doctor}</strong></span>
                      <span>From: {comm.sender_id}</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(comm.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {comm.status}
                    </span>
                    <button className="p-1 text-slate-400 hover:text-slate-600">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-100 space-y-3 text-xs animate-in fade-in duration-100">
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 font-mono text-[11px] text-slate-800 whitespace-pre-wrap leading-relaxed">
                      {comm.message_body}
                    </div>

                    {comm.ai_findings_included && Array.isArray(comm.ai_findings_included) && comm.ai_findings_included.length > 0 && (
                      <div className="space-y-1.5">
                        <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                          Attached AI Safety Alerts ({comm.ai_findings_included.length})
                        </div>
                        <div className="space-y-1">
                          {comm.ai_findings_included.map((f: any, i: number) => (
                            <div
                              key={i}
                              className="p-2 rounded bg-indigo-50/50 border border-indigo-100 text-[11px] flex items-center justify-between"
                            >
                              <span className="font-semibold text-slate-900">{f.title || f.category}</span>
                              <span className="text-slate-600">{f.description}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
