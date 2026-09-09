import type {
  PharmacistReview,
  PharmacistReviewSummary,
  InventoryItem,
  InventorySummary,
  DashboardAnalytics,
  PrescriptionSummary,
  PrescriptionDetails,
  AgentReviewStatus,
  PharmacistDecision,
  LoginRequest,
  LoginResponse,
  UserProfile,
  EscalationResolution,
  EducationalCase,
  StudentProgress,
  AuditLogEntry
} from '../types';


const API_BASE = import.meta.env.VITE_API_URL || '';
const TOKEN_KEY = 'pharmacyguard_token';

let memoryToken: string | null = localStorage.getItem(TOKEN_KEY);

export const authStorage = {
  getToken(): string | null {
    return memoryToken || localStorage.getItem(TOKEN_KEY);
  },
  setToken(token: string | null) {
    memoryToken = token;
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  },
  clear() {
    memoryToken = null;
    localStorage.removeItem(TOKEN_KEY);
  }
};

function getAuthHeaders(customHeaders: HeadersInit = {}): HeadersInit {
  const token = authStorage.getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(customHeaders as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } else if (errJson && errJson.message) {
        errorDetail = errJson.message;
      }
    } catch {
      // Use fallback error message
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export const api = {
  // --- Authentication ---
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    const data: LoginResponse = await handleResponse(res);
    authStorage.setToken(data.access_token);
    return data;
  },

  async logout(): Promise<{ status: string; message: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/auth/logout`, {
        method: 'POST',
        headers: getAuthHeaders(),
      });
      return await handleResponse(res);
    } finally {
      authStorage.clear();
    }
  },

  async getMe(): Promise<{ status: string; data: UserProfile }> {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  // --- Health Check ---
  async getHealth(): Promise<{ status: string; service: string; version: string; mode?: string }> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse(res);
  },

  // --- Prescriptions ---
  async getPrescriptions(): Promise<{ status: string; data: PrescriptionSummary[] }> {
    const res = await fetch(`${API_BASE}/api/prescriptions`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  async getPrescription(prescriptionId: string): Promise<{ status: string; data: PrescriptionDetails }> {
    const res = await fetch(`${API_BASE}/api/prescriptions/${encodeURIComponent(prescriptionId)}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  async getPatients(): Promise<{ status: string; total: number; data: any[] }> {
    const res = await fetch(`${API_BASE}/api/prescriptions/patients`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  async createPrescription(payload: any): Promise<{ status: string; message: string; prescription: PrescriptionDetails; review?: PharmacistReview }> {
    const res = await fetch(`${API_BASE}/api/prescriptions`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async editPrescription(prescriptionId: string, payload: any): Promise<{ status: string; message: string; data: PrescriptionDetails; re_review?: PharmacistReview }> {
    const res = await fetch(`${API_BASE}/api/prescriptions/${encodeURIComponent(prescriptionId)}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async reReviewPrescription(prescriptionId: string): Promise<{ status: string; message: string; data: PharmacistReview }> {
    const res = await fetch(`${API_BASE}/api/prescriptions/${encodeURIComponent(prescriptionId)}/re-review`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  // --- Prescriber Communication / Doctor Reporting ---
  async sendPrescriberReport(reviewId: string, payload: any): Promise<{ status: string; message: string; data: any }> {
    const res = await fetch(`${API_BASE}/api/reviews/${encodeURIComponent(reviewId)}/send-prescriber-report`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async getPrescriberCommunications(reviewId: string): Promise<{ status: string; total: number; data: any[] }> {
    const res = await fetch(`${API_BASE}/api/reviews/${encodeURIComponent(reviewId)}/communications`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },


  // --- Reviews & Agent Workflow ---
  async createReview(prescriptionId: string): Promise<{ status: string; message: string; data: PharmacistReview }> {
    const res = await fetch(`${API_BASE}/api/reviews`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ prescription_id: prescriptionId.trim().toUpperCase() }),
    });
    return handleResponse(res);
  },

  async getReviews(params?: { decision?: PharmacistDecision | string; status?: AgentReviewStatus | string }): Promise<{ status: string; total: number; data: PharmacistReviewSummary[] }> {
    const query = new URLSearchParams();
    if (params?.decision) query.append('decision', params.decision);
    if (params?.status) query.append('status', params.status);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await fetch(`${API_BASE}/api/reviews${qs}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  async getPendingReviews(): Promise<{ status: string; total_pending: number; data: PharmacistReviewSummary[] }> {
    const res = await fetch(`${API_BASE}/api/reviews/pending`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  async getReview(reviewId: string): Promise<{ status: string; data: PharmacistReview }> {
    const res = await fetch(`${API_BASE}/api/reviews/${encodeURIComponent(reviewId)}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  // --- Pharmacist Human-in-the-Loop Actions ---
  async acceptReview(reviewId: string, notes?: string): Promise<{ status: string; message: string; data: PharmacistReview }> {
    const res = await fetch(`${API_BASE}/api/reviews/${encodeURIComponent(reviewId)}/accept`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ notes: notes || undefined }),
    });
    return handleResponse(res);
  },

  async overrideReview(reviewId: string, notes: string): Promise<{ status: string; message: string; data: PharmacistReview }> {
    const res = await fetch(`${API_BASE}/api/reviews/${encodeURIComponent(reviewId)}/override`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ notes: notes.trim() }),
    });
    return handleResponse(res);
  },

  async escalateReview(reviewId: string, notes: string): Promise<{ status: string; message: string; data: PharmacistReview }> {
    const res = await fetch(`${API_BASE}/api/reviews/${encodeURIComponent(reviewId)}/escalate`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ notes: notes.trim() }),
    });
    return handleResponse(res);
  },

  // --- Inventory API ---
  async getInventory(params?: { search?: string; status?: string }): Promise<{ status: string; total: number; data: InventoryItem[] }> {
    const query = new URLSearchParams();
    if (params?.search) query.append('search', params.search);
    if (params?.status) query.append('status', params.status);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await fetch(`${API_BASE}/api/inventory${qs}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  async getLowStockItems(): Promise<{ status: string; total_low_stock_items: number; data: InventoryItem[] }> {
    const res = await fetch(`${API_BASE}/api/inventory/low-stock`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  async getInventorySummary(): Promise<{ status: string; data: InventorySummary }> {
    const res = await fetch(`${API_BASE}/api/inventory/summary`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  // --- Chief Pharmacist Escalation Resolution ---
  async resolveEscalation(reviewId: string, payload: { chief_decision: string; chief_notes: string; action_required?: string }): Promise<{ status: string; message: string; resolution: EscalationResolution; review: PharmacistReview }> {
    const res = await fetch(`${API_BASE}/api/reviews/${encodeURIComponent(reviewId)}/resolve-escalation`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  // --- Real Inventory Dispensing ---
  async dispensePrescription(reviewId: string, payload?: { notes?: string }): Promise<{ status: string; message: string; data: any }> {
    const res = await fetch(`${API_BASE}/api/reviews/${encodeURIComponent(reviewId)}/dispense`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload || {}),
    });
    return handleResponse(res);
  },

  // --- Student Training & Educational Cases API ---
  async getEducationalCases(params?: { category?: string; difficulty?: string }): Promise<{ status: string; total: number; data: EducationalCase[] }> {
    const query = new URLSearchParams();
    if (params?.category) query.append('category', params.category);
    if (params?.difficulty) query.append('difficulty', params.difficulty);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await fetch(`${API_BASE}/api/student/cases${qs}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  async getEducationalCaseById(caseId: string): Promise<{ status: string; data: EducationalCase }> {
    const res = await fetch(`${API_BASE}/api/student/cases/${encodeURIComponent(caseId)}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  async submitStudentCase(caseId: string, payload: { selected_option_index: number; student_notes?: string }): Promise<{ status: string; is_correct: boolean; selected_option_index: number; correct_option_index: number; explanation_text: string; submission: any }> {
    const res = await fetch(`${API_BASE}/api/student/cases/${encodeURIComponent(caseId)}/submit`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async getStudentProgress(): Promise<{ status: string; data: StudentProgress }> {
    const res = await fetch(`${API_BASE}/api/student/progress`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  async publishEducationalCase(payload: any): Promise<{ status: string; message: string; data: EducationalCase }> {
    const res = await fetch(`${API_BASE}/api/student/cases/publish`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  // --- Analytics Dashboard API ---
  async getDashboardAnalytics(): Promise<{ status: string; data: DashboardAnalytics }> {
    const res = await fetch(`${API_BASE}/api/analytics/dashboard`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  async getAuditLogs(limit: number = 50): Promise<{ status: string; total: number; data: AuditLogEntry[] }> {
    const res = await fetch(`${API_BASE}/api/analytics/audit-log?limit=${limit}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  }
};

