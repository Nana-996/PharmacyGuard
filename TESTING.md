# PharmacyGuard — Judge Testing Guide

Welcome, Hackathon Judges! This document provides a **step-by-step, 5-minute evaluation guide** to test every aspect of **PharmacyGuard**—from autonomous AI clinical verification and Human-in-the-Loop decision enforcement to the interactive Pharmacy Student Simulation Workspace.

---

## ⏱️ 5-Minute Evaluation Quick-Start

| Step | Action | What to Look For | Time |
|---|---|---|---|
| **1. Launch App** | Open [http://localhost:5173](http://localhost:5173) | One-Click Demo Login Screen with 3 distinct roles. | 30s |
| **2. Staff Pharmacist Review** | Click **"Staff Pharmacist"** direct login | Prescription Queue with live triage statuses. | 1m |
| **3. Test Severe Allergy** | Open **`RX-1003`** (Robert Taylor) | AI flags **`HIGH_PRIORITY_REVIEW`** (Augmentin vs. Penicillin anaphylaxis). | 1m |
| **4. Test Human-in-the-Loop** | Attempt to Override `RX-1003` | System blocks approval without mandatory clinical justification. | 30s |
| **5. Test Student Workspace** | Log in as **"Pharmacy Student"** | Blind clinical case evaluation, interactive quiz, and AI coaching score. | 1.5m |
| **6. Chief Pharmacist Analytics** | Log in as **"Chief Pharmacist"** | Operational dashboard, clinical override audit logs, and stock health. | 30s |

---

## 🧪 Detailed Test Walkthroughs

### 1. Authentication & Role-Based Access Control (RBAC)

Navigate to [http://localhost:5173](http://localhost:5173). You will see the **One-Click Quick Sign-In Cards**:

- 🩺 **Staff Pharmacist:** `staff.pharmacist@hospital.dev` / `DevStaff123!` (Dr. Alex Reed, PharmD)
- 📊 **Chief Pharmacist:** `chief.pharmacist@hospital.dev` / `DevChief123!` (Dr. Eleanor Vance, PharmD)
- 🎓 **Pharmacy Student:** `student@hospital.dev` / `DevStudent123!` (Sam Taylor, Pharmacy Intern)

Click **"Direct Sign In"** on the **Staff Pharmacist** card to enter the clinical verification queue immediately.

---

### 2. Clinical Verification Scenarios (The 5 Canonical Test Cases)

In the **Review Queue**, click **"Verify"** or select any prescription to open the **Prescription Review Studio**. Test each of the 5 preloaded clinical scenarios:

#### Case 1: `RX-1001` — Normal Clean Prescription
- **Patient:** John Doe (34M) | **Allergies:** NKDA (No Known Drug Allergies)
- **Diagnosis:** `J02.0` — Streptococcal pharyngitis
- **Prescribed:** Amoxicillin 500mg Oral Capsule (q8h x 10 days)
- **Agent Output:** 🟢 **`CLEAR`**
- **Clinical Evidence:**
  - Indication check confirms Amoxicillin is first-line guideline therapy for Streptococcal pharyngitis.
  - Allergy check passes clean (NKDA).
  - Dosage check (500mg q8h = 1500mg/day) is well within reference range (250-500mg single, 1500mg max).
  - Inventory check confirms Amoxicillin 500mg is `AVAILABLE` (120 units on hand).
- **Judge Action:** Click **"Approve & Dispense"**. The prescription status updates to `APPROVED` instantly.

#### Case 2: `RX-1002` — Indication & Diagnosis Mismatch
- **Patient:** Jane Smith (52F) | **Allergies:** NKDA
- **Diagnosis:** `E11.9` — Type 2 diabetes mellitus without complications
- **Prescribed:** Lisinopril 20mg Oral Tablet (once daily)
- **Agent Output:** 🟡 **`REVIEW`**
- **Clinical Evidence:**
  - Indication check flags **`POTENTIAL_MISMATCH`**: Lisinopril is an ACE inhibitor indicated for hypertension or diabetic nephropathy with documented proteinuria. The patient record has no active hypertension diagnosis.
  - The agent advises the pharmacist to verify if the prescriber intended renal protection or if a co-diagnosis of hypertension was omitted.
- **Judge Action:** Notice the orange warning badge and clear clinical evidence explanation.

#### Case 3: `RX-1003` — Severe Allergy Anaphylaxis Conflict *(CRITICAL TEST)*
- **Patient:** Robert Taylor (61M) | **Allergies:** Penicillin (Beta-Lactams) — Severe Anaphylaxis
- **Diagnosis:** `J01.90` — Acute bacterial sinusitis
- **Prescribed:** Augmentin 875/125mg Oral Tablet (q12h x 7 days)
- **Agent Output:** 🔴 **`HIGH_PRIORITY_REVIEW`**
- **Clinical Evidence:**
  - Allergy check triggers critical alarm: Augmentin contains Amoxicillin (an aminopenicillin) and clavulanate. Direct cross-reactivity with documented severe penicillin anaphylaxis.
  - Agent directive: *"Withhold dispensing immediately. Contact prescriber to switch to a non-beta-lactam alternative (e.g., Doxycycline or Levofloxacin)."*
- **Test Human-in-the-Loop Safety:**
  1. Click the **"Approve (Override AI)"** button.
  2. Notice that the system **refuses** to submit the approval unless you provide a mandatory clinical explanation (e.g., *"Prescriber consulted, patient tested negative on recent skin test"*).
  3. Enter an explanation or click **"Reject Prescription"** to withhold dispensing.

#### Case 4: `RX-1004` — Duplicate Therapy Hazard (Dual NSAIDs)
- **Patient:** Emily Davis (45F) | **Allergies:** Sulfa drugs
- **Diagnosis:** `M17.9` — Osteoarthritis of knee
- **Prescribed:** Ibuprofen 600mg Oral Tablet (tid) **AND** Naproxen 500mg Oral Tablet (bid)
- **Agent Output:** 🔴 **`HIGH_PRIORITY_REVIEW`**
- **Clinical Evidence:**
  - Duplicate medication check flags concurrent prescription of two systemic NSAIDs.
  - Agent rationale: Concurrent NSAIDs offer zero additive analgesic efficacy while drastically multiplying the risk of acute gastrointestinal ulceration, upper GI bleeding, and acute kidney injury.
- **Judge Action:** Review the therapeutic class duplication card detailing the mechanism and risks.

#### Case 5: `RX-1005` — Complex Polypharmacy & Multi-Drug Regimen
- **Patient:** Michael Chen (68M) | **Allergies:** NKDA
- **Diagnosis:** `I10` — Essential hypertension
- **Prescribed:** Atorvastatin 40mg, Metformin 1000mg, Lisinopril 20mg, Amlodipine 10mg
- **Agent Output:** Detailed multi-agent verification across 4 drugs.
- **Clinical Evidence:**
  - Evaluates drug interactions (Lisinopril + Amlodipine synergism).
  - Verifies individual single and daily doses against reference ranges.
  - Interrogates hospital pharmacy inventory for all 4 items simultaneously.

---

### 3. Student Simulation & Training Workspace

1. Click **Log Out** from the top-right menu and log in as **Pharmacy Student** (`student@hospital.dev`).
2. The UI switches to the **Student Learning Workspace**:
   - Students are presented with anonymized, blind clinical scenarios.
   - The student conducts a self-directed review: inspecting patient labs, diagnoses, and medication orders.
   - The student submits their clinical determination (**Approve**, **Reject**, or **Request Clarification**) along with their clinical justification.
3. Upon submission:
   - The system reveals the **Strands AI Agent Benchmark Analysis**.
   - An automated **Educational Score (0-100%)** is calculated comparing the student's findings against the agent's deterministic evidence.
   - The student receives targeted mentorship pearls (e.g., explaining beta-lactam side-chain cross-reactivity or guideline-directed medical therapy).

---

### 4. Chief Pharmacist Operations & Workload Analytics

1. Log in as **Chief Pharmacist** (`chief.pharmacist@hospital.dev`).
2. Navigate to **Analytics & Operations**:
   - **Throughput Metrics:** Total verified orders, pending reviews, and average review latency.
   - **Safety Risk Distribution:** Proportions of `CLEAR`, `REVIEW`, and `HIGH_PRIORITY_REVIEW` prescriptions.
   - **Override Audit Ledger:** Real-time table showing all clinical overrides, the pharmacist who authorized each override, timestamps, and recorded justifications.
   - **Inventory Health Overview:** Aggregate stock health percentage, low-stock alerts, and restocking priorities.

---

### 5. Automated Backend Unit & Integration Tests

For judges who wish to inspect test code coverage and automated assertions:

```powershell
# Activate environment
.venv\Scripts\activate

# Run all 12 test suites covering Agent, Tools, Inventory, and RBAC
python -m unittest discover -s backend/tests -p "test_*.py" -v
```

Expected output: All test cases pass with `OK`.

```powershell
# Specific Agent & Tool tests:
python -m unittest backend/tests/test_agent_verification.py
python -m unittest backend/tests/test_agent_inventory_integration.py
python -m unittest backend/tests/test_auth_rbac.py
python -m unittest backend/tests/test_pharmacist_review_service.py
```
