import React, { useState, useEffect } from 'react';
import type { CreatePrescriptionPayload, PrescribedMedicationItem, PatientSummary } from '../types';
import { api } from '../services/api';
import {
  User,
  Plus,
  Trash2,
  AlertCircle,
  RotateCw,
  CheckCircle2,
  ArrowLeft,
  Zap
} from 'lucide-react';

interface NewPrescriptionViewProps {
  onPrescriptionCreated: (rxId: string, reviewId?: string) => void;
  onCancel: () => void;
}

export const NewPrescriptionView: React.FC<NewPrescriptionViewProps> = ({
  onPrescriptionCreated,
  onCancel,
}) => {
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('NEW');
  const [rxId, setRxId] = useState<string>(`RX-${Math.floor(1000 + Math.random() * 9000)}`);
  const [patientName, setPatientName] = useState<string>('');
  const [patientAge, setPatientAge] = useState<number>(45);
  const [patientSex, setPatientSex] = useState<string>('Female');
  const [patientAllergies, setPatientAllergies] = useState<string>('NKDA (No known drug allergies)');
  const [diagnosis, setDiagnosis] = useState<string>('Streptococcal pharyngitis (Strep throat)');
  const [prescribingDoctor, setPrescribingDoctor] = useState<string>('Dr. Sarah Adams, MD (Internal Medicine)');
  const [prescriptionDate, setPrescriptionDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [autoTriggerReview, setAutoTriggerReview] = useState<boolean>(true);

  const [medications, setMedications] = useState<PrescribedMedicationItem[]>([
    { medication: 'Amoxicillin', strength: '500mg', dosage: '1 capsule (500mg)', frequency: 'Every 8 hours (Three times daily)', route: 'Oral', duration: '10 days' },
  ]);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getPatients().then((res) => { if (res.data) setPatients(res.data); }).catch(() => {});
  }, []);

  const handlePatientSelect = (pId: string) => {
    setSelectedPatientId(pId);
    if (pId === 'NEW') {
      setPatientName(''); setPatientAge(45); setPatientSex('Female'); setPatientAllergies('NKDA (No known drug allergies)');
    } else {
      const p = patients.find((item) => item.patient_id === pId);
      if (p) {
        setPatientName(p.name); setPatientAge(p.age); setPatientSex(p.sex); setPatientAllergies(p.allergies || 'NKDA');
        if (p.diagnoses && p.diagnoses.length > 0) setDiagnosis(p.diagnoses[0].diagnosis);
      }
    }
  };

  const handleMedChange = (index: number, field: keyof PrescribedMedicationItem, value: string) => {
    setMedications((prev) => { const copy = [...prev]; copy[index] = { ...copy[index], [field]: value }; return copy; });
  };
  const handleAddMed = () => { setMedications((prev) => [...prev, { medication: '', strength: '', dosage: '', frequency: 'Once daily', route: 'Oral', duration: '7 days' }]); };
  const handleRemoveMed = (index: number) => { if (medications.length <= 1) return; setMedications((prev) => prev.filter((_, i) => i !== index)); };

  const loadPreset = (presetType: 'ALLERGY' | 'DUPLICATION' | 'MISMATCH' | 'OOS' | 'CLEAN') => {
    setRxId(`RX-${Math.floor(2000 + Math.random() * 8000)}`);
    if (presetType === 'ALLERGY') {
      setPatientName('Kwame Mensah'); setPatientAge(52); setPatientSex('Male'); setPatientAllergies('Penicillin (Severe anaphylaxis & urticaria)'); setDiagnosis('Acute bacterial sinusitis, unspecified'); setPrescribingDoctor('Dr. Sarah Adams, MD (Internal Medicine)');
      setMedications([{ medication: 'Augmentin (Amoxicillin / Clavulanate)', strength: '875mg / 125mg', dosage: '1 tablet (875/125mg)', frequency: 'Every 12 hours (Twice daily)', route: 'Oral', duration: '10 days' }]);
    } else if (presetType === 'DUPLICATION') {
      setPatientName('Abena Asante'); setPatientAge(61); setPatientSex('Female'); setPatientAllergies('Latex (Mild contact rash)'); setDiagnosis('Osteoarthritis of knee, unspecified'); setPrescribingDoctor('Dr. Robert Sterling, MD (Orthopedics)');
      setMedications([{ medication: 'Ibuprofen', strength: '600mg', dosage: '1 tablet (600mg)', frequency: 'Every 8 hours with food', route: 'Oral', duration: '14 days' }, { medication: 'Naproxen', strength: '500mg', dosage: '1 tablet (500mg)', frequency: 'Twice daily', route: 'Oral', duration: '14 days' }]);
    } else if (presetType === 'MISMATCH') {
      setPatientName('John Doe'); setPatientAge(34); setPatientSex('Male'); setPatientAllergies('No known drug allergies (NKDA)'); setDiagnosis('Type 2 diabetes mellitus without complications'); setPrescribingDoctor('Dr. Marcus Vance, MD (Family Medicine)');
      setMedications([{ medication: 'Lisinopril', strength: '20mg', dosage: '1 tablet (20mg)', frequency: 'Once daily in the morning', route: 'Oral', duration: '30 days' }]);
    } else if (presetType === 'OOS') {
      setPatientName('Esi Mensah'); setPatientAge(48); setPatientSex('Female'); setPatientAllergies('NKDA'); setDiagnosis('Acute Musculoskeletal Strain'); setPrescribingDoctor('Dr. Marcus Vance, MD');
      setMedications([{ medication: 'Ibuprofen', strength: '600mg', dosage: '1 tablet (600mg)', frequency: 'Every 8 hours', route: 'Oral', duration: '7 days' }]);
    } else {
      setPatientName('Akua Boateng'); setPatientAge(55); setPatientSex('Female'); setPatientAllergies('NKDA (No known drug allergies)'); setDiagnosis('Essential hypertension and Hyperlipidemia'); setPrescribingDoctor('Dr. Sarah Adams, MD');
      setMedications([{ medication: 'Lisinopril', strength: '20mg', dosage: '1 tablet (20mg)', frequency: 'Once daily in morning', route: 'Oral', duration: '30 days' }, { medication: 'Amlodipine', strength: '5mg', dosage: '1 tablet (5mg)', frequency: 'Once daily', route: 'Oral', duration: '30 days' }, { medication: 'Atorvastatin', strength: '20mg', dosage: '1 tablet (20mg)', frequency: 'Once daily at bedtime', route: 'Oral', duration: '30 days' }]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(null);
    if (!patientName.trim()) { setError('Patient name is required.'); return; }
    if (!diagnosis.trim()) { setError('Diagnosis is required.'); return; }
    const invalidMed = medications.some((m) => !m.medication?.trim() || !m.strength?.trim() || !m.dosage?.trim());
    if (invalidMed) { setError('Provide Medication, Strength, and Dosage for all items.'); return; }

    setLoading(true);
    try {
      const payload: CreatePrescriptionPayload = {
        patient_id: selectedPatientId !== 'NEW' ? selectedPatientId : undefined,
        patient_name: patientName.trim(), patient_age: Number(patientAge), patient_sex: patientSex.trim(),
        patient_allergies: patientAllergies.trim(), diagnosis: diagnosis.trim(), diagnosis_date: prescriptionDate,
        prescribing_doctor: prescribingDoctor.trim(), prescription_date: prescriptionDate, prescription_id: rxId.trim().toUpperCase(),
        medications: medications.map((m) => ({ medication: m.medication.trim(), strength: m.strength?.trim() || '', dosage: m.dosage?.trim() || '', frequency: m.frequency?.trim() || 'Once daily', route: m.route?.trim() || 'Oral', duration: m.duration?.trim() || '7 days' })),
        auto_trigger_review: autoTriggerReview,
      };
      const res = await api.createPrescription(payload);
      onPrescriptionCreated(res.prescription.prescription_id, res.review?.review_id);
    } catch (err: any) {
      setError(err?.message || 'Failed to create prescription.');
    } finally {
      setLoading(false);
    }
  };

  const inputClasses = "w-full text-[13px] px-3 py-2 rounded-md border border-[var(--pg-border)] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-[var(--pg-text)]";
  const labelClasses = "block text-[12px] font-medium text-[var(--pg-text-secondary)] mb-1";

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <button type="button" onClick={onCancel} className="p-1.5 rounded-md text-[var(--pg-text-muted)] hover:text-[var(--pg-text)] hover:bg-slate-100 border border-[var(--pg-border)] transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-lg font-semibold text-[var(--pg-text)]">New Prescription</h2>
            <p className="text-[13px] text-[var(--pg-text-muted)]">Enter prescription details and trigger AI review</p>
          </div>
        </div>
      </div>

      {/* Preset Bar */}
      <div className="p-3.5 rounded-lg bg-slate-50 border border-[var(--pg-border)] space-y-2">
        <div className="flex items-center gap-2">
          <Zap className="w-3.5 h-3.5 text-amber-500" />
          <span className="text-[13px] font-medium text-[var(--pg-text)]">Quick-Load Test Cases</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {[
            { key: 'ALLERGY' as const, label: 'Allergy Conflict', color: 'text-red-600' },
            { key: 'DUPLICATION' as const, label: 'Dual NSAID', color: 'text-amber-600' },
            { key: 'MISMATCH' as const, label: 'Indication Mismatch', color: 'text-violet-600' },
            { key: 'OOS' as const, label: 'Out-of-Stock', color: 'text-amber-600' },
            { key: 'CLEAN' as const, label: 'Clean 3-Drug', color: 'text-emerald-600' },
          ].map((p) => (
            <button key={p.key} type="button" onClick={() => loadPreset(p.key)} className={`px-2.5 py-1 rounded-md bg-white border border-[var(--pg-border)] hover:bg-slate-100 text-[12px] font-medium ${p.color} transition-colors`}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-md bg-red-50 border border-red-100 text-red-700 text-[13px] flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" /><span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Section 1: Prescription & Prescriber */}
        <div className="p-5 rounded-lg border border-[var(--pg-border)] bg-white space-y-3">
          <h3 className="text-sm font-semibold text-[var(--pg-text)]">1. Prescription & Prescriber</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div><label className={labelClasses}>Prescription ID *</label><input type="text" value={rxId} onChange={(e) => setRxId(e.target.value)} className={`${inputClasses} font-mono font-semibold`} required /></div>
            <div><label className={labelClasses}>Prescribing Doctor *</label><input type="text" value={prescribingDoctor} onChange={(e) => setPrescribingDoctor(e.target.value)} className={inputClasses} required /></div>
            <div><label className={labelClasses}>Date</label><input type="date" value={prescriptionDate} onChange={(e) => setPrescriptionDate(e.target.value)} className={inputClasses} /></div>
          </div>
        </div>

        {/* Section 2: Patient */}
        <div className="p-5 rounded-lg border border-[var(--pg-border)] bg-white space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--pg-text)] flex items-center gap-1.5"><User className="w-4 h-4 text-blue-600" />2. Patient Details</h3>
            {patients.length > 0 && (
              <select value={selectedPatientId} onChange={(e) => handlePatientSelect(e.target.value)} className="text-[13px] px-2 py-1 rounded-md border border-[var(--pg-border)] bg-white text-[var(--pg-text)]">
                <option value="NEW">+ New Patient</option>
                {patients.map((p) => <option key={p.patient_id} value={p.patient_id}>{p.name} ({p.patient_id})</option>)}
              </select>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div className="sm:col-span-2"><label className={labelClasses}>Full Name *</label><input type="text" value={patientName} onChange={(e) => setPatientName(e.target.value)} placeholder="e.g. Kwame Mensah" className={inputClasses} required /></div>
            <div><label className={labelClasses}>Age</label><input type="number" value={patientAge} onChange={(e) => setPatientAge(Number(e.target.value))} min={0} max={125} className={inputClasses} /></div>
            <div><label className={labelClasses}>Sex</label><select value={patientSex} onChange={(e) => setPatientSex(e.target.value)} className={inputClasses}><option value="Male">Male</option><option value="Female">Female</option><option value="Other">Other</option></select></div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div><label className={labelClasses}>Allergies</label><input type="text" value={patientAllergies} onChange={(e) => setPatientAllergies(e.target.value)} className={inputClasses} /></div>
            <div><label className={labelClasses}>Diagnosis *</label><input type="text" value={diagnosis} onChange={(e) => setDiagnosis(e.target.value)} className={inputClasses} required /></div>
          </div>
        </div>

        {/* Section 3: Medications */}
        <div className="p-5 rounded-lg border border-[var(--pg-border)] bg-white space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--pg-text)]">3. Prescribed Medications</h3>
            <button type="button" onClick={handleAddMed} className="px-2.5 py-1 text-[13px] font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors flex items-center gap-1">
              <Plus className="w-3.5 h-3.5" /><span>Add</span>
            </button>
          </div>

          <div className="space-y-3">
            {medications.map((med, idx) => (
              <div key={idx} className="p-3 rounded-md border border-[var(--pg-border-light)] bg-slate-50 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-[12px] font-medium text-[var(--pg-text-muted)]">Medication #{idx + 1}</span>
                  {medications.length > 1 && (
                    <button type="button" onClick={() => handleRemoveMed(idx)} className="p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                  )}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <div className="sm:col-span-2"><label className={labelClasses}>Name *</label><input type="text" value={med.medication} onChange={(e) => handleMedChange(idx, 'medication', e.target.value)} className={inputClasses} required /></div>
                  <div><label className={labelClasses}>Strength *</label><input type="text" value={med.strength || ''} onChange={(e) => handleMedChange(idx, 'strength', e.target.value)} className={inputClasses} required /></div>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <div><label className={labelClasses}>Dosage *</label><input type="text" value={med.dosage || ''} onChange={(e) => handleMedChange(idx, 'dosage', e.target.value)} className={inputClasses} required /></div>
                  <div><label className={labelClasses}>Frequency</label><input type="text" value={med.frequency || ''} onChange={(e) => handleMedChange(idx, 'frequency', e.target.value)} className={inputClasses} /></div>
                  <div><label className={labelClasses}>Route</label><select value={med.route || 'Oral'} onChange={(e) => handleMedChange(idx, 'route', e.target.value)} className={inputClasses}><option value="Oral">Oral</option><option value="Intravenous (IV)">IV</option><option value="Intramuscular (IM)">IM</option><option value="Topical">Topical</option><option value="Sublingual">Sublingual</option><option value="Inhalation">Inhalation</option></select></div>
                  <div><label className={labelClasses}>Duration</label><input type="text" value={med.duration || ''} onChange={(e) => handleMedChange(idx, 'duration', e.target.value)} className={inputClasses} /></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Submit */}
        <div className="p-4 rounded-lg border border-[var(--pg-border)] bg-white flex flex-col sm:flex-row items-center justify-between gap-3">
          <label className="flex items-center gap-2 text-[13px] font-medium text-[var(--pg-text-secondary)] cursor-pointer">
            <input type="checkbox" checked={autoTriggerReview} onChange={(e) => setAutoTriggerReview(e.target.checked)} className="w-4 h-4 text-blue-600 rounded border-[var(--pg-border)] focus:ring-blue-500" />
            <span>Auto-trigger AI review after submission</span>
          </label>
          <div className="flex items-center gap-2">
            <button type="button" onClick={onCancel} disabled={loading} className="px-3.5 py-2 text-[13px] font-medium text-[var(--pg-text-secondary)] hover:bg-slate-100 rounded-md transition-colors disabled:opacity-50">Cancel</button>
            <button type="submit" disabled={loading} className="px-5 py-2 text-[13px] font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors flex items-center gap-1.5 disabled:opacity-50">
              {loading ? (<><RotateCw className="w-4 h-4 animate-spin" /><span>Submitting...</span></>) : (<><CheckCircle2 className="w-4 h-4" /><span>Submit Prescription</span></>)}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
