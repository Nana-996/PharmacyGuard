export type UserRole = 'STAFF_PHARMACIST' | 'CHIEF_PHARMACIST' | 'PHARMACY_STUDENT' | 'ADMIN';

export interface UserProfile {
  user_id: string;
  full_name: string;
  email: string;
  role: UserRole;
  active: number;
  created_at: string;
  last_login_at?: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  status: string;
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export type AgentReviewStatus = 'CLEAR' | 'REVIEW' | 'HIGH_PRIORITY_REVIEW';
export type PharmacistDecision = 'PENDING' | 'ACCEPTED' | 'OVERRIDDEN' | 'ESCALATED';
export type FindingCategory = 'CLINICAL' | 'ALLERGY' | 'DUPLICATION' | 'INTERACTION' | 'DOSAGE' | 'INVENTORY';
export type FindingSeverity = 'HIGH' | 'MODERATE' | 'LOW' | 'NONE';
export type StockStatus = 'AVAILABLE' | 'LOW STOCK' | 'OUT OF STOCK' | 'STRENGTH UNAVAILABLE' | 'NOT FOUND';


export interface Patient {
  patient_id: string;
  name: string;
  age: number;
  sex: string;
  allergies?: string;
}

export interface Diagnosis {
  diagnosis_id?: string;
  diagnosis: string;
  diagnosis_date?: string;
}

export interface PrescribedMedicationItem {
  medication: string;
  strength?: string;
  dosage?: string;
  frequency?: string;
  route?: string;
  duration?: string;
}

export interface PrescriptionDetails {
  prescription_id: string;
  prescription_date: string;
  prescribing_doctor: string;
  patient: Patient;
  diagnoses: Diagnosis[];
  medications: PrescribedMedicationItem[];
}

export interface PrescriptionSummary {
  prescription_id: string;
  patient_id: string;
  patient_name: string;
  icd10_code?: string;
  diagnosis_description?: string;
  status: string;
  prescribed_date: string;
}

export interface AgentFinding {
  finding_id?: string;
  review_id?: string;
  category: FindingCategory;
  severity: FindingSeverity | string;
  title: string;
  description: string;
  evidence_source: string;
  evidence: string;
  evidence_data?: string;
  requires_action: boolean;
  created_at?: string;
}

export interface AuditLogEntry {
  audit_id: string;
  event_type: 'AGENT_REVIEW_CREATED' | 'FINDING_CREATED' | 'PHARMACIST_REVIEWED' | 'PHARMACIST_OVERRIDDEN' | 'REVIEW_ESCALATED' | string;
  actor_type: 'AGENT' | 'PHARMACIST' | 'CHIEF_PHARMACIST' | 'SYSTEM' | string;
  actor_id: string;
  prescription_id: string;
  review_id?: string;
  event_data?: string;
  timestamp: string;
}

export interface PrescriberCommunication {
  communication_id: string;
  prescription_id: string;
  review_id?: string;
  sender_id: string;
  recipient_doctor: string;
  report_type: 'AI_FINDINGS_REPORT' | 'CUSTOM_PHARMACIST_REPORT' | string;
  subject: string;
  message_body: string;
  ai_findings_included?: any;
  suggested_modifications?: any;
  status: string;
  created_at: string;
}

export interface SendPrescriberReportPayload {
  recipient_doctor: string;
  report_type: 'AI_FINDINGS_REPORT' | 'CUSTOM_PHARMACIST_REPORT';
  subject: string;
  message_body: string;
  ai_findings_included?: any[];
  suggested_modifications?: PrescribedMedicationItem[];
}

export interface EditPrescriptionPayload {
  medications: PrescribedMedicationItem[];
  prescribing_doctor?: string;
  prescription_date?: string;
  modification_notes?: string;
  auto_trigger_re_review?: boolean;
}

export interface CreatePrescriptionPayload {
  patient_id?: string;
  patient_name: string;
  patient_age: number;
  patient_sex: string;
  patient_allergies?: string;
  diagnosis: string;
  diagnosis_date?: string;
  prescribing_doctor: string;
  prescription_date?: string;
  prescription_id?: string;
  medications: PrescribedMedicationItem[];
  auto_trigger_review?: boolean;
}

export interface PatientSummary {
  patient_id: string;
  name: string;
  age: number;
  sex: string;
  allergies?: string;
  diagnoses?: Diagnosis[];
}

export interface EscalationResolution {
  resolution_id: string;
  review_id: string;
  prescription_id: string;
  chief_id: string;
  chief_decision: 'RESOLVED_APPROVED' | 'RETURNED_TO_STAFF' | 'DIRECT_OVERRIDE_APPROVED' | string;
  chief_notes: string;
  action_required?: string | null;
  resolved_at: string;
}

export interface PharmacistReview {
  review_id: string;
  prescription_id: string;
  agent_review_status: AgentReviewStatus;
  pharmacist_decision: PharmacistDecision;
  pharmacist_notes?: string | null;
  reviewed_by?: string | null;
  created_at: string;
  reviewed_at?: string | null;
  findings: AgentFinding[];
  audit_history: AuditLogEntry[];
  prescriber_communications?: PrescriberCommunication[];
  escalation_resolutions?: EscalationResolution[];
  prescription_details?: PrescriptionDetails;
}

export interface PharmacistReviewSummary {
  review_id: string;
  prescription_id: string;
  agent_review_status: AgentReviewStatus;
  pharmacist_decision: PharmacistDecision;
  pharmacist_notes?: string | null;
  reviewed_by?: string | null;
  created_at: string;
  reviewed_at?: string | null;
  patient_name?: string;
  findings_count: number;
}

export interface InventoryItem {
  inventory_id: string;
  medication: string;
  generic_name: string;
  strength: string;
  dosage_form: string;
  quantity_on_hand: number;
  reorder_level: number;
  unit: string;
  deficit_to_reorder: number;
  stock_status: StockStatus;
  last_updated: string;
}

export interface InventoryTransaction {
  transaction_id: string;
  inventory_id: string;
  prescription_id?: string;
  transaction_type: 'DISPENSED' | 'RESTOCKED' | 'ADJUSTMENT' | string;
  quantity_change: number;
  quantity_after: number;
  actor_id: string;
  notes?: string;
  timestamp: string;
  medication?: string;
  generic_name?: string;
  strength?: string;
}

export interface InventorySummary {
  total_tracked_medications: number;
  number_available: number;
  number_low_stock: number;
  number_out_of_stock: number;
  number_below_reorder_level: number;
  stock_health_percentage: string;
  last_inventory_sync: string;
}

export interface FindingCategoryStat {
  category: FindingCategory;
  count: number;
  high_severity_count: number;
}

export interface EscalationSummary {
  review_id: string;
  prescription_id: string;
  pharmacist_id: string;
  reason: string;
  timestamp: string;
  agent_review_status: AgentReviewStatus;
  patient_name: string;
  resolution?: EscalationResolution | null;
}

export interface EducationalCase {
  case_id: string;
  title: string;
  clinical_category: 'ALLERGY' | 'DUPLICATION' | 'INDICATION' | 'DOSAGE' | 'INTERACTION' | string;
  difficulty: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED' | string;
  scenario_text: string;
  deidentified_prescription: PrescribedMedicationItem[];
  key_safety_challenge: string;
  multiple_choice_question: string;
  options: string[];
  correct_option_index: number;
  explanation_text: string;
  source_review_id?: string;
  published_by: string;
  created_at: string;
}

export interface StudentSubmission {
  submission_id: string;
  case_id: string;
  title?: string;
  clinical_category?: string;
  difficulty?: string;
  selected_option_index: number;
  is_correct: boolean | number;
  student_notes?: string;
  submitted_at: string;
}

export interface StudentProgress {
  student_id: string;
  total_available_cases: number;
  completed_cases: number;
  total_submissions: number;
  correct_submissions: number;
  accuracy_percentage: string;
  recent_submissions: StudentSubmission[];
}

export interface DashboardAnalytics {
  summary_cards: {
    pending_reviews: number;
    high_priority_reviews: number;
    low_stock_items: number;
    out_of_stock_items: number;
    total_reviews: number;
    accepted_reviews: number;
    overridden_reviews: number;
    escalated_reviews: number;
    clear_reviews: number;
    stock_health_percentage: string;
  };
  finding_categories: FindingCategoryStat[];
  recent_escalations: EscalationSummary[];
  recent_reviews: PharmacistReviewSummary[];
  inventory_overview: InventorySummary;
}

