import React, { useState } from 'react';
import type { PrescriptionDetails, PrescribedMedicationItem } from '../../types';
import { api } from '../../services/api';
import {
  Edit3,
  Plus,
  Trash2,
  X,
  Sparkles,
  AlertTriangle,
  FileCheck,
  RotateCw
} from 'lucide-react';

interface EditPrescriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  prescription: PrescriptionDetails;
  onSaved: (updatedDetails: PrescriptionDetails, reReviewResult?: any) => void;
}

export const EditPrescriptionModal: React.FC<EditPrescriptionModalProps> = ({
  isOpen,
  onClose,
  prescription,
  onSaved,
}) => {
  const [medications, setMedications] = useState<PrescribedMedicationItem[]>(
    prescription.medications && prescription.medications.length > 0
      ? prescription.medications.map((m) => ({ ...m }))
      : [{ medication: '', strength: '', dosage: '', frequency: '', route: 'Oral', duration: '7 days' }]
  );
  const [prescribingDoctor, setPrescribingDoctor] = useState<string>(prescription.prescribing_doctor || '');
  const [modificationNotes, setModificationNotes] = useState<string>('');
  const [autoReReview, setAutoReReview] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleMedChange = (index: number, field: keyof PrescribedMedicationItem, value: string) => {
    setMedications((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: value };
      return copy;
    });
  };

  const handleAddMed = () => {
    setMedications((prev) => [
      ...prev,
      { medication: '', strength: '', dosage: '', frequency: 'Once daily', route: 'Oral', duration: '7 days' },
    ]);
  };

  const handleRemoveMed = (index: number) => {
    if (medications.length <= 1) return;
    setMedications((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    const invalidMed = medications.some((m) => !m.medication?.trim() || !m.strength?.trim() || !m.dosage?.trim());
    if (invalidMed) {
      setError('Please fill in Medication Name, Strength, and Dosage for all prescribed items.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        medications: medications.map((m) => ({
          medication: m.medication.trim(),
          strength: m.strength?.trim() || '',
          dosage: m.dosage?.trim() || '',
          frequency: m.frequency?.trim() || 'Once daily',
          route: m.route?.trim() || 'Oral',
          duration: m.duration?.trim() || '7 days',
        })),
        prescribing_doctor: prescribingDoctor.trim(),
        modification_notes: modificationNotes.trim() || undefined,
        auto_trigger_re_review: autoReReview,
      };

      const res = await api.editPrescription(prescription.prescription_id, payload);
      onSaved(res.data, res.re_review);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to update prescription in hospital database.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-teal-500/20 border border-teal-400/30 text-teal-400">
              <Edit3 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-white/10 text-teal-300 font-bold">
                  {prescription.prescription_id}
                </span>
                <span className="text-xs text-slate-400">Prescription Modification</span>
              </div>
              <h2 className="text-base font-bold text-white mt-0.5">
                Edit Doctor's Prescribed Regimen
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Patient Summary Banner */}
        <div className="px-6 py-3 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div>
            <span className="text-slate-500 font-medium">Patient: </span>
            <span className="font-bold text-slate-900">{prescription.patient?.name || 'Hospital Patient'}</span>
            <span className="text-slate-500 font-mono ml-2">({prescription.patient?.age}y, {prescription.patient?.sex})</span>
          </div>
          <div>
            <span className="text-slate-500 font-medium">Documented Allergies: </span>
            <span className={`font-semibold ${prescription.patient?.allergies?.includes('NKDA') ? 'text-emerald-700' : 'text-rose-700'}`}>
              {prescription.patient?.allergies || 'NKDA'}
            </span>
          </div>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Prescribed Medications Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Prescribed Medication Lines
                </h3>
                <p className="text-[11px] text-slate-500">
                  Modify doses, swap strengths for in-stock alternatives, or adjust course duration.
                </p>
              </div>
              <button
                type="button"
                onClick={handleAddMed}
                className="px-2.5 py-1 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 rounded-lg border border-teal-200 transition-colors flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Medication</span>
              </button>
            </div>

            <div className="space-y-3">
              {medications.map((med, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors space-y-3 relative group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-slate-500">
                      Line Item #{idx + 1}
                    </span>
                    {medications.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveMed(idx)}
                        className="p-1 text-rose-500 hover:text-rose-700 hover:bg-rose-50 rounded transition-colors"
                        title="Remove medication"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="sm:col-span-2">
                      <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                        Medication / Generic Name *
                      </label>
                      <input
                        type="text"
                        value={med.medication}
                        onChange={(e) => handleMedChange(idx, 'medication', e.target.value)}
                        placeholder="e.g. Ibuprofen, Amoxicillin, Lisinopril"
                        className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 bg-white"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                        Strength *
                      </label>
                      <input
                        type="text"
                        value={med.strength || ''}
                        onChange={(e) => handleMedChange(idx, 'strength', e.target.value)}
                        placeholder="e.g. 500mg, 200mg"
                        className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 bg-white"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                        Dosage *
                      </label>
                      <input
                        type="text"
                        value={med.dosage || ''}
                        onChange={(e) => handleMedChange(idx, 'dosage', e.target.value)}
                        placeholder="e.g. 1 tablet"
                        className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 bg-white"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                        Frequency
                      </label>
                      <input
                        type="text"
                        value={med.frequency || ''}
                        onChange={(e) => handleMedChange(idx, 'frequency', e.target.value)}
                        placeholder="e.g. Every 8 hours"
                        className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 bg-white"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                        Route
                      </label>
                      <select
                        value={med.route || 'Oral'}
                        onChange={(e) => handleMedChange(idx, 'route', e.target.value)}
                        className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 bg-white"
                      >
                        <option value="Oral">Oral</option>
                        <option value="Intravenous (IV)">Intravenous (IV)</option>
                        <option value="Intramuscular (IM)">Intramuscular (IM)</option>
                        <option value="Topical">Topical</option>
                        <option value="Sublingual">Sublingual</option>
                        <option value="Inhalation">Inhalation</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                        Duration
                      </label>
                      <input
                        type="text"
                        value={med.duration || ''}
                        onChange={(e) => handleMedChange(idx, 'duration', e.target.value)}
                        placeholder="e.g. 7 days"
                        className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 bg-white"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Prescriber & Notes Section */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-200">
            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                Prescribing Doctor
              </label>
              <input
                type="text"
                value={prescribingDoctor}
                onChange={(e) => setPrescribingDoctor(e.target.value)}
                placeholder="Dr. Name, MD"
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 bg-white"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                Pharmacist Modification Rationale
              </label>
              <input
                type="text"
                value={modificationNotes}
                onChange={(e) => setModificationNotes(e.target.value)}
                placeholder="e.g. Substituted 200mg tablets due to 600mg OOS"
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 bg-white"
              />
            </div>
          </div>

          {/* AI Re-Review Checkbox */}
          <div className="p-4 rounded-xl bg-teal-50/60 border border-teal-200 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Sparkles className="w-4 h-4 text-teal-700 shrink-0" />
              <div>
                <div className="text-xs font-bold text-teal-950">
                  Re-Trigger AI Clinical Verification
                </div>
                <div className="text-[11px] text-teal-700">
                  Immediately run Strands Bedrock agent to verify safety of the updated regimen.
                </div>
              </div>
            </div>
            <input
              type="checkbox"
              id="autoReReview"
              checked={autoReReview}
              onChange={(e) => setAutoReReview(e.target.checked)}
              className="w-4 h-4 text-teal-600 rounded border-slate-300 focus:ring-teal-500"
            />
          </div>
        </form>

        {/* Modal Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200 rounded-lg transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="px-5 py-2 text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 rounded-lg shadow-sm transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {loading ? (
              <>
                <RotateCw className="w-3.5 h-3.5 animate-spin" />
                <span>Saving to Database...</span>
              </>
            ) : (
              <>
                <FileCheck className="w-3.5 h-3.5" />
                <span>Save Changes & Update SQLite</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
