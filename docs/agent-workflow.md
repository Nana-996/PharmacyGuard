# PharmacyGuard — Agent Workflow & Clinical Decision Lifecycle

This document provides a detailed walkthrough of the **PharmacyGuard Strands Agent Workflow**, tracing an electronic prescription from ingestion through deterministic tool evaluation, Amazon Bedrock clinical synthesis, human pharmacist decision-making, and immutable audit persistence.

---

## 1. End-to-End Clinical Verification Lifecycle

```mermaid
flowchart TD
    subgraph Phase 1: Ingestion
        A[New Inpatient / Outpatient Order] --> B[Prescription Ingestion]
        B --> C[Call get_prescription]
    end

    subgraph Phase 2: Parallel Evidence Gathering (<0.1s)
        C --> D1[Indication Alignment Check]
        C --> D2[Allergy & Cross-Reactivity Check]
        C --> D3[Therapeutic Duplication Check]
        C --> D4[Drug-Drug Interaction Check]
        C --> D5[Single & Daily Dose Check]
        C --> D6[Hospital Pharmacy Stock Check]
        D1 & D2 & D3 & D4 & D5 & D6 --> E[Compile Evidence Bundle]
    end

    subgraph Phase 3: Bedrock Synthesis & Triage
        E --> F[Amazon Bedrock Claude Sonnet Synthesis]
        F -->|Within 14s| G[Validate Schema & Parse JSON]
        F -->|Timeout or AWS API Error| H[Deterministic Fallback Engine]
        G & H --> I{Evaluate Overall Triage Status}
        I -->|No Issues & In Stock| J1[CLEAR 🟢]
        I -->|Indication Mismatch / Low Stock| J2[REVIEW 🟡]
        I -->|Allergy Conflict / Overdose / Stockout| J3[HIGH PRIORITY REVIEW 🔴]
    end

    subgraph Phase 4: Human-in-the-Loop Gateway
        J1 & J2 & J3 --> K[Present to Licensed Pharmacist]
        K --> L1[Action: Approve & Clear Dispense]
        K --> L2[Action: Reject & Contact Prescriber]
        K --> L3[Action: Override Safety Flag]
        L3 --> M{Was Clinical Rationale Provided?}
        M -->|No| N[Reject Submission HTTP 422]
        M -->|Yes| O[Accept Override]
    end

    subgraph Phase 5: Audit & Persistence
        L1 & L2 & O --> P[Update Hospital Prescription Status]
        P --> Q[Commit to Immutable audit_events Ledger]
        Q --> R[Update Inventory Stock Count]
    end
```

---

## 2. Phase-by-Phase Operational Details

### Phase 1: Ingestion & Record Retrieval
When an electronic prescription is queued for review:
1. The backend API triggers `run_structured_prescription_review(prescription_id)`.
2. The agent executes `get_prescription(prescription_id)` to query `hospital_sim.db`.
3. The retrieved payload provides:
   - Patient demographics (Age, Gender, Weight, Pregnancy status).
   - Documented drug and environmental allergies.
   - Active ICD-10 diagnoses.
   - Prescribed medications with dosage, route, frequency, and duration.

---

### Phase 2: Deterministic Evidence Gathering
The agent interrogates local clinical and formulary knowledge bases:

1. **Indication Alignment (`diagnosis_medication_check`):**  
   Cross-references each prescribed medication with the patient's active diagnoses in `diagnosis_medication_guidelines`. Confirms whether the drug is established first-line or acceptable therapy.
2. **Allergy & Cross-Reactivity (`allergy_check`):**  
   Evaluates immunological cross-reactivities in `allergy_cross_reactions`. Detects shared core structures (such as the beta-lactam ring in penicillins and cephalosporins).
3. **Therapeutic Duplication (`duplicate_medication_check`):**  
   Groups ordered medications by therapeutic class (`medication_reference`). Identifies concurrent prescriptions that duplicate mechanism of action (e.g., dual oral NSAIDs or dual ACE inhibitors).
4. **Drug-Drug Interactions (`medication_interaction_check`):**  
   Scans the medication list pairwise against `drug_interactions` to flag pharmacokinetic and pharmacodynamic interactions.
5. **Dosage Range Validation (`dosage_check`):**  
   Parses the numeric milligram strength and dosing frequency. Computes the estimated 24-hour cumulative dose and evaluates it against standard single-dose ranges and maximum daily limits.
6. **Formulary Stock Verification (`check_inventory`):**  
   Queries `medication_inventory` to verify whether the prescribed medications and strengths are available in the hospital pharmacy.

---

### Phase 3: Amazon Bedrock Clinical Synthesis
All compiled evidence is fed into a 1-turn synthesis prompt executed via the **Strands Agents SDK** and **Amazon Bedrock (Claude Sonnet)**:
- **Clinical Synthesis:** The model organizes findings into clinical evidence cards, explaining the pharmacologic mechanism behind any flagged conflicts.
- **Triage Determination:**
  - `HIGH_PRIORITY_REVIEW`: Severe allergy conflict, major drug-drug interaction, hazardous therapeutic duplicate, excessive overdose, or critical medication out of stock.
  - `REVIEW`: Potential indication mismatch, moderate drug interaction, sub-therapeutic dosing, or low inventory.
  - `CLEAR`: All clinical verification checks passed and medications are fully stocked.
- **Resilience Cutoff:** A non-blocking thread pool limits the Bedrock call to 14.0 seconds. If the model exceeds this limit or errors, the deterministic fallback engine synthesizes the review directly from tool outputs.

---

### Phase 4: Human-in-the-Loop Gateway
The synthesized review is displayed on the pharmacist's clinical dashboard:
- The pharmacist reviews patient context alongside the AI findings.
- **Routine Approval:** Available for `CLEAR` and standard `REVIEW` cases.
- **Clinical Rejection:** Withholds medication dispensing and generates a prescriber communication template.
- **Safety Override:** If the pharmacist chooses to approve a prescription flagged as `HIGH_PRIORITY_REVIEW`, the system requires a mandatory clinical explanation. Approvals without justification are blocked.

---

### Phase 5: Audit Persistence & Execution
Once the human pharmacist submits their decision:
1. The prescription record in `hospital_sim.db` is updated to `APPROVED`, `REJECTED`, or `OVERRIDDEN`.
2. The review and individual findings are persisted to `pharmacist_reviews` and `review_findings`.
3. An audit record is written to `audit_events` containing the user ID, timestamp, decision, and any override justification.
4. If approved, pharmacy stock counts are decremented accordingly in `medication_inventory`.
