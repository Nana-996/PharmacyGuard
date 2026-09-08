# PharmacyGuard — User Interface & Screen Tour

This directory contains the visual gallery, interface layout guides, and screen walkthroughs for **PharmacyGuard**.

---

## 1. Interface Screen Catalog

### Screen 1: One-Click Demo Authentication
- **Location:** `/login`
- **Features:**
  - Modern medical-themed dark/light login card.
  - Three **Direct Sign In** cards for quick judge evaluation without typing passwords:
    - 🩺 **Staff Pharmacist:** Dr. Alex Reed, PharmD
    - 📊 **Chief Pharmacist:** Dr. Eleanor Vance, PharmD
    - 🎓 **Pharmacy Student:** Sam Taylor, Pharmacy Intern
  - Role-based automatic route redirection upon login.

---

### Screen 2: Pharmacist Review Queue
- **Location:** `/queue` (Staff Pharmacist & Chief Pharmacist)
- **Features:**
  - Real-time list of pending inpatient and outpatient prescriptions.
  - Color-coded triage status badges:
    - 🔴 **`HIGH PRIORITY REVIEW`** (Critical safety hazards)
    - 🟡 **`REVIEW`** (Indication mismatches, low stock)
    - 🟢 **`CLEAR`** (Routine guideline-compliant orders)
  - Patient age, gender, and prescribing doctor at a glance.
  - Quick action buttons to launch the verification studio.

---

### Screen 3: Prescription Review & Verification Studio
- **Location:** `/prescriptions/:id/review`
- **Features:**
  - **Patient Summary Header:** Patient name, MRN, age, gender, documented allergies, and active ICD-10 diagnoses.
  - **Medication Order Details:** Drug name, strength, dosage, route, frequency, duration, and doctor instructions.
  - **Strands AI Clinical Findings:**
    - Indication guideline evaluation card.
    - Allergy cross-reactivity warning card (with biological mechanism).
    - Drug interaction alert card (pharmacodynamic/pharmacokinetic).
    - Single and daily dose verification against reference limits.
  - **Live Inventory Status Card:** On-hand physical units, reorder levels, and availability tags (`AVAILABLE`, `LOW STOCK`, `OUT OF STOCK`).
  - **Clinician Decision Action Bar:**
    - 🟢 **Approve & Dispense**
    - 🔴 **Reject Prescription**
    - ⚠️ **Override AI Safety Flag**

---

### Screen 4: Human-in-the-Loop Override Modal
- **Location:** Activated upon overriding a `HIGH_PRIORITY_REVIEW` flag.
- **Features:**
  - Critical safety alert warning explaining the identified hazard.
  - **Mandatory Clinical Justification Field:** Submissions without written rationale are blocked by the system.
  - Permanent attribution to the reviewing pharmacist's credentials and timestamp.

---

### Screen 5: Pharmacy Student Simulation Workspace
- **Location:** `/student/workspace` (Pharmacy Student role)
- **Features:**
  - Anonymized, blind clinical scenarios designed for pharmacy residents and interns.
  - Interactive decision inputs: **Approve**, **Reject**, or **Flag for Clarification**.
  - Student rationale text editor.
  - **AI Coaching Benchmark:** Compares student determination against Strands agent evidence, computes an **Educational Score (0-100%)**, and provides actionable clinical teaching pearls.

---

### Screen 6: Chief Pharmacist Operations & Workload Analytics
- **Location:** `/analytics` (Chief Pharmacist role)
- **Features:**
  - **Workload KPIs:** Total processed orders, pending queue count, and average turnaround time.
  - **Clinical Safety Triage Distribution:** Visual pie/bar charts showing proportions of `CLEAR`, `REVIEW`, and `HIGH_PRIORITY_REVIEW` prescriptions.
  - **Override Audit Ledger:** Full institutional table showing all clinical overrides, the pharmacist who authorized them, and written justifications.
  - **Formulary Health Metrics:** Percentage of inventory items in healthy stock status.

---

### Screen 7: Real-Time Pharmacy Inventory Tracker
- **Location:** `/inventory`
- **Features:**
  - Comprehensive hospital pharmacy catalog tracking over 50 essential medications.
  - Live search by generic name, brand name, or inventory ID.
  - Low-stock and out-of-stock highlight filters.
  - Stock adjustment modal for batch receiving and cycle counts.

---

## 2. Capturing & Adding Screenshots

To add image files to this directory for documentation:
1. Save your captured images in PNG format:
   - `01-login-screen.png`
   - `02-review-queue.png`
   - `03-prescription-review.png`
   - `04-student-workspace.png`
   - `05-chief-analytics.png`
   - `06-inventory-tracker.png`
2. Place the images in `docs/screenshots/`.
3. Reference them in markdown using standard syntax: `![Caption](docs/screenshots/filename.png)`.
