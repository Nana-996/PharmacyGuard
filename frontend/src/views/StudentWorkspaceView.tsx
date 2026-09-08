import React, { useEffect, useState } from 'react';
import {
  GraduationCap,
  BookOpen,
  CheckCircle2,
  XCircle,
  Award,
  ArrowRight,
  RefreshCw,
  HelpCircle,
  Pill,
  Sparkles,
  Filter,
  AlertCircle
} from 'lucide-react';

import { api } from '../services/api';
import type { EducationalCase, StudentProgress } from '../types';
import { SafetyNotice } from '../components/common/SafetyNotice';

export const StudentWorkspaceView: React.FC = () => {
  const [cases, setCases] = useState<EducationalCase[]>([]);
  const [progress, setProgress] = useState<StudentProgress | null>(null);
  const [selectedCase, setSelectedCase] = useState<EducationalCase | null>(null);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [studentNotes, setStudentNotes] = useState('');
  const [submissionResult, setSubmissionResult] = useState<any | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [casesRes, progRes] = await Promise.all([
        api.getEducationalCases({
          category: categoryFilter !== 'ALL' ? categoryFilter : undefined,
          difficulty: difficultyFilter !== 'ALL' ? difficultyFilter : undefined,
        }),
        api.getStudentProgress(),
      ]);
      setCases(casesRes.data || []);
      setProgress(progRes.data || null);
      if (casesRes.data?.length && !selectedCase) {
        setSelectedCase(casesRes.data[0]);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load educational training curriculum.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [categoryFilter, difficultyFilter]);

  const handleSelectCase = (c: EducationalCase) => {
    setSelectedCase(c);
    setSelectedOption(null);
    setStudentNotes('');
    setSubmissionResult(null);
  };

  const handleSubmitAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase || selectedOption === null) return;

    setSubmitting(true);
    setError(null);
    try {
      const res = await api.submitStudentCase(selectedCase.case_id, {
        selected_option_index: selectedOption,
        student_notes: studentNotes.trim() || undefined,
      });
      setSubmissionResult(res);
      // Refresh progress
      const progRes = await api.getStudentProgress();
      setProgress(progRes.data || null);
    } catch (err: any) {
      setError(err?.message || 'Failed to submit case response.');
    } finally {
      setSubmitting(false);
    }
  };

  const getDifficultyBadge = (diff: string) => {
    switch (diff) {
      case 'BEGINNER':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'ADVANCED':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case 'ALLERGY':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'DUPLICATION':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'DOSAGE':
        return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      default:
        return 'bg-teal-100 text-teal-800 border-teal-200';
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-2xs">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-800 border border-indigo-200 flex items-center gap-1">
              <GraduationCap className="w-3.5 h-3.5" />
              Pharmacy Intern & Student Training Laboratory
            </span>
            <span className="text-xs text-slate-400 font-mono">De-Identified Clinical Simulation</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900">Clinical Verification & Decision Practice</h2>
          <p className="text-xs text-slate-600 mt-1">
            Master medication safety triage, allergen cross-reactivities, and guideline-concordant prescribing on simulated cases.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="p-2.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition-colors flex items-center gap-1.5 self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-600' : ''}`} />
          <span>Refresh Curriculum</span>
        </button>
      </div>

      <SafetyNotice variant="card" />

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}


      {/* Student Progress Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl border border-slate-200 bg-white shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase">Available Cases</div>
            <div className="text-2xl font-bold text-slate-900 mt-1">{progress?.total_available_cases ?? cases.length}</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Curriculum modules</div>
          </div>
          <div className="w-11 h-11 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <BookOpen className="w-5 h-5" />
          </div>
        </div>

        <div className="p-5 rounded-xl border border-slate-200 bg-white shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase">Cases Completed</div>
            <div className="text-2xl font-bold text-indigo-950 mt-1">{progress?.completed_cases ?? 0}</div>
            <div className="text-[11px] text-indigo-700 mt-0.5">Attempted vignettes</div>
          </div>
          <div className="w-11 h-11 rounded-xl bg-teal-50 border border-teal-100 flex items-center justify-center text-teal-600">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        <div className="p-5 rounded-xl border border-slate-200 bg-white shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase">Clinical Accuracy</div>
            <div className="text-2xl font-bold text-emerald-900 mt-1">{progress?.accuracy_percentage ?? '0%'}</div>
            <div className="text-[11px] text-emerald-700 mt-0.5">First-attempt accuracy</div>
          </div>
          <div className="w-11 h-11 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
            <Award className="w-5 h-5" />
          </div>
        </div>

        <div className="p-5 rounded-xl border border-slate-200 bg-white shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase">Intern Status</div>
            <div className="text-sm font-bold text-slate-900 mt-1">Active Learner</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Hospital Clinical Unit</div>
          </div>
          <div className="w-11 h-11 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">
            <Sparkles className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Main Workspace Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Case Selector & Filters (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <Filter className="w-3.5 h-3.5 text-slate-500" />
                Filter Case Studies
              </span>
            </div>

            <div className="space-y-2">
              <div>
                <label className="text-[11px] font-semibold text-slate-500 block mb-1">Clinical Safety Area</label>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-200 bg-slate-50 font-medium"
                >
                  <option value="ALL">All Clinical Categories</option>
                  <option value="ALLERGY">Allergy Cross-Reactivity</option>
                  <option value="DUPLICATION">Therapeutic Duplication</option>
                  <option value="INDICATION">Indication Verification</option>
                  <option value="DOSAGE">Dosage & Inventory Substitution</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-500 block mb-1">Difficulty Level</label>
                <select
                  value={difficultyFilter}
                  onChange={(e) => setDifficultyFilter(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-200 bg-slate-50 font-medium"
                >
                  <option value="ALL">All Difficulties</option>
                  <option value="BEGINNER">Beginner (Foundational)</option>
                  <option value="INTERMEDIATE">Intermediate (Core Practice)</option>
                  <option value="ADVANCED">Advanced (Complex / Inventory)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Cases List */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
            <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs font-bold text-slate-700">
              <span>Case Studies ({cases.length})</span>
              <span className="text-[11px] text-slate-400 font-mono">Select to practice</span>
            </div>

            <div className="divide-y divide-slate-100 max-h-[550px] overflow-y-auto">
              {loading ? (
                <div className="p-8 text-center text-xs text-slate-400">
                  <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-indigo-600" />
                  Loading case library...
                </div>
              ) : !cases.length ? (
                <div className="p-8 text-center text-xs text-slate-500">
                  No cases found matching the selected filters.
                </div>
              ) : (
                cases.map((c) => {
                  const isSelected = selectedCase?.case_id === c.case_id;
                  return (
                    <button
                      key={c.case_id}
                      onClick={() => handleSelectCase(c)}
                      className={`w-full text-left p-4 transition-all hover:bg-slate-50 flex flex-col gap-2 ${
                        isSelected ? 'bg-indigo-50/70 border-l-4 border-indigo-600' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-mono text-[11px] font-bold text-indigo-900">{c.case_id}</span>
                        <div className="flex items-center gap-1.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getDifficultyBadge(c.difficulty)}`}>
                            {c.difficulty}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getCategoryBadge(c.clinical_category)}`}>
                            {c.clinical_category}
                          </span>
                        </div>
                      </div>
                      <div className="text-xs font-bold text-slate-900 line-clamp-1">{c.title}</div>
                      <div className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed">
                        {c.key_safety_challenge}
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Case Simulator & Quiz (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {selectedCase ? (
            <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
              {/* Vignette Header */}
              <div className="p-6 bg-slate-900 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="font-mono text-xs text-indigo-300 font-bold">{selectedCase.case_id}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getDifficultyBadge(selectedCase.difficulty)}`}>
                      {selectedCase.difficulty}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getCategoryBadge(selectedCase.clinical_category)}`}>
                      {selectedCase.clinical_category}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white">{selectedCase.title}</h3>
                </div>
                <div className="px-3 py-1.5 rounded-lg bg-indigo-900/60 border border-indigo-700/50 text-[11px] font-mono text-indigo-200 self-start sm:self-auto">
                  De-Identified Training Model
                </div>
              </div>

              {/* Patient Scenario Card */}
              <div className="p-6 border-b border-slate-100 space-y-4">
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
                    De-Identified Patient Scenario Vignette
                  </h4>
                  <p className="text-xs text-slate-800 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-200">
                    {selectedCase.scenario_text}
                  </p>
                </div>

                {/* Prescribed Regimen */}
                {selectedCase.deidentified_prescription?.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
                      <Pill className="w-3.5 h-3.5 text-teal-600" />
                      Prescribed Medication Regimen
                    </h4>
                    <div className="overflow-x-auto rounded-xl border border-slate-200">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 text-slate-500 text-[11px] uppercase font-semibold border-b border-slate-200">
                          <tr>
                            <th className="px-4 py-2.5">Medication & Strength</th>
                            <th className="px-4 py-2.5">Dosage</th>
                            <th className="px-4 py-2.5">Frequency</th>
                            <th className="px-4 py-2.5">Route</th>
                            <th className="px-4 py-2.5">Duration</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {selectedCase.deidentified_prescription.map((m, idx) => (
                            <tr key={idx} className="hover:bg-slate-50/80">
                              <td className="px-4 py-2.5 font-bold text-slate-900">
                                {m.medication} {m.strength && <span className="text-slate-500 font-normal">({m.strength})</span>}
                              </td>
                              <td className="px-4 py-2.5 text-slate-700">{m.dosage || 'Standard'}</td>
                              <td className="px-4 py-2.5 text-slate-700">{m.frequency}</td>
                              <td className="px-4 py-2.5 text-slate-600">{m.route || 'Oral'}</td>
                              <td className="px-4 py-2.5 text-slate-600 font-mono text-[11px]">{m.duration || 'N/A'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>

              {/* Challenge Question & Interactive Answer Form */}
              <form onSubmit={handleSubmitAnswer} className="p-6 space-y-5">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <HelpCircle className="w-4 h-4 text-indigo-600" />
                    <span className="text-xs font-bold uppercase tracking-wider text-indigo-900">Clinical Decision Challenge</span>
                  </div>
                  <h4 className="text-sm font-bold text-slate-900 leading-snug">
                    {selectedCase.multiple_choice_question}
                  </h4>
                </div>

                {/* Multiple Choice Options */}
                <div className="space-y-2.5">
                  {selectedCase.options.map((opt, idx) => {
                    const isSelected = selectedOption === idx;
                    const isSubmitted = submissionResult !== null;
                    const isCorrectChoice = isSubmitted && idx === submissionResult.correct_option_index;
                    const isWrongChoice = isSubmitted && isSelected && !submissionResult.is_correct;

                    return (
                      <label
                        key={idx}
                        className={`p-4 rounded-xl border flex items-start gap-3 cursor-pointer transition-all ${
                          isCorrectChoice
                            ? 'bg-emerald-50 border-emerald-500 ring-2 ring-emerald-500/20 text-emerald-950 font-medium'
                            : isWrongChoice
                            ? 'bg-rose-50 border-rose-500 ring-2 ring-rose-500/20 text-rose-950'
                            : isSelected
                            ? 'bg-indigo-50/80 border-indigo-600 ring-2 ring-indigo-500/20 text-indigo-950 font-medium'
                            : 'bg-white border-slate-200 hover:border-slate-300 text-slate-700'
                        } ${isSubmitted ? 'cursor-default' : ''}`}
                      >
                        <input
                          type="radio"
                          name="student_choice"
                          checked={isSelected}
                          onChange={() => !isSubmitted && setSelectedOption(idx)}
                          disabled={isSubmitted}
                          className="mt-0.5 text-indigo-600 focus:ring-indigo-500"
                        />
                        <div className="flex-1 text-xs leading-relaxed">
                          <span className="font-bold mr-2 text-slate-400">({String.fromCharCode(65 + idx)})</span>
                          {opt}
                        </div>
                        {isCorrectChoice && <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />}
                        {isWrongChoice && <XCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />}
                      </label>
                    );
                  })}
                </div>

                {/* Optional Student Reasoning Notes */}
                {!submissionResult && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">
                      Student Clinical Notes & Rationale (Optional)
                    </label>
                    <textarea
                      rows={2}
                      value={studentNotes}
                      onChange={(e) => setStudentNotes(e.target.value)}
                      placeholder="Briefly state your pharmacological reasoning before submitting..."
                      className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                )}

                {/* Feedback Panel */}
                {submissionResult && (
                  <div
                    className={`p-5 rounded-xl border space-y-3 animate-in fade-in duration-200 ${
                      submissionResult.is_correct
                        ? 'bg-emerald-50/80 border-emerald-200 text-emerald-950'
                        : 'bg-amber-50/80 border-amber-200 text-amber-950'
                    }`}
                  >
                    <div className="flex items-center gap-2 font-bold text-xs">
                      {submissionResult.is_correct ? (
                        <>
                          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                          <span className="text-emerald-900 text-sm">Correct Clinical Assessment!</span>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="w-5 h-5 text-amber-600" />
                          <span className="text-amber-900 text-sm">Review Recommended: Safety Conflict Missed</span>
                        </>
                      )}
                    </div>

                    <div>
                      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                        Pharmacological Teaching Rationale & Clinical Evidence:
                      </div>
                      <p className="text-xs leading-relaxed text-slate-800 bg-white/80 p-3.5 rounded-lg border border-slate-200/60">
                        {submissionResult.explanation_text}
                      </p>
                    </div>

                    <div className="pt-2 flex justify-end">
                      <button
                        type="button"
                        onClick={() => {
                          const nextIdx = (cases.findIndex((c) => c.case_id === selectedCase.case_id) + 1) % cases.length;
                          handleSelectCase(cases[nextIdx]);
                        }}
                        className="px-4 py-2 text-xs font-bold text-white bg-indigo-700 hover:bg-indigo-800 rounded-lg shadow-xs transition-colors flex items-center gap-1.5"
                      >
                        <span>Next Training Case</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Submit Action */}
                {!submissionResult && (
                  <div className="flex items-center justify-end gap-3 pt-2">
                    <button
                      type="submit"
                      disabled={selectedOption === null || submitting}
                      className="px-6 py-2.5 text-xs font-bold text-white bg-indigo-700 hover:bg-indigo-800 disabled:opacity-50 rounded-xl shadow-xs transition-colors flex items-center gap-2"
                    >
                      {submitting ? 'Evaluating Submission...' : 'Submit Decision'}
                    </button>
                  </div>
                )}
              </form>
            </div>
          ) : (
            <div className="bg-white p-12 rounded-xl border border-slate-200 text-center text-xs text-slate-400">
              Select a case study from the left menu to start training.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
