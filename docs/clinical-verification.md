# PharmacyGuard — Clinical Verification & Safety Guidelines

This document details the clinical verification rules, pharmacological mechanisms, guideline references, and safety rationales embedded in **PharmacyGuard**.

---

## 1. Indication & Guideline Alignment

Prescription verification starts with verifying that the prescribed drug aligns with evidence-based clinical guidelines for the patient's active diagnoses (identified via ICD-10 codes).

### Guideline Reference Matrix
| ICD-10 | Clinical Diagnosis | Guideline First-Line Therapies | Common Off-Guideline Misprescriptions |
|---|---|---|---|
| **`J02.0`** | Streptococcal pharyngitis | Amoxicillin 500mg po q8h or Penicillin V | Fluoroquinolones (unnecessary broad-spectrum) |
| **`J01.90`** | Acute bacterial sinusitis | Augmentin (Amoxicillin/Clavulanate) 875/125mg | Macrolides (high Streptococcus pneumoniae resistance) |
| **`E11.9`** | Type 2 diabetes mellitus | Metformin, SGLT2 inhibitors, GLP-1 receptor agonists | Lisinopril (without documented hypertension or proteinuria) |
| **`I10`** | Essential (primary) hypertension | ACE inhibitors (Lisinopril), ARBs, CCBs (Amlodipine), Thiazides | Beta-blockers as first-line monotherapy |
| **`M17.9`** | Osteoarthritis of knee | Topical NSAIDs, Acetaminophen, Single oral NSAID | Concurrent multiple oral systemic NSAIDs |

### Indication Mismatch Logic
When `diagnosis_medication_check` evaluates **`RX-1002`** (Lisinopril 20mg for Type 2 diabetes without hypertension):
- **Clinical Rationale:** While ACE inhibitors provide nephroprotection in diabetic patients with confirmed proteinuria (microalbuminuria), prescribing Lisinopril with no documented hypertension or renal indication warrants pharmacist review.
- **Agent Action:** Flags `POTENTIAL_MISMATCH` with priority `REVIEW`, prompting the pharmacist to verify whether an active hypertension diagnosis was omitted or if renal lab values exist.

---

## 2. Allergy Cross-Reactivity & Immunological Mechanisms

Allergy screening must evaluate more than literal string matches. Cross-reactivity between related chemical structures presents a significant risk of severe adverse events.

```
                    Penicillin Core (Beta-Lactam Ring + Thiazolidine Ring)
                                       |
        +------------------------------+------------------------------+
        |                                                             |
        v                                                             v
Aminopenicillins (Amoxicillin, Ampicillin)           Cephalosporins (Shared Beta-Lactam Ring)
  - Direct 100% Beta-Lactam cross-reactivity           - 1st Generation (Cefazolin): ~5-10% cross-reactivity
  - Augmentin contains Amoxicillin                     - 3rd/4th Gen (Ceftriaxone): <1-2% cross-reactivity
  - Triggers Type-1 IgE Anaphylaxis                   - Side-chain structural similarity governs risk
```

### Beta-Lactam Cross-Reactivity Rules
1. **Severe Penicillin Allergy $\rightarrow$ Aminopenicillins (Augmentin, Amoxicillin):**
   - **Risk:** Contraindicated. 100% core structural homology.
   - **Reaction:** High risk of immediate IgE-mediated anaphylaxis, bronchospasm, angioedema, and cardiovascular collapse.
   - **Triage Level:** 🔴 **`HIGH_PRIORITY_REVIEW`**.
   - **Recommendation:** Withhold dispensing. Switch to non-beta-lactam alternative (e.g., Doxycycline, Macrolides, or Respiratory Fluoroquinolones).
2. **Penicillin Allergy $\rightarrow$ Cephalosporins:**
   - **Risk:** Evaluated based on side-chain identity. First-generation cephalosporins (Cephalexin, Cefazolin) carry higher cross-reactivity than third/fourth-generation agents (Ceftriaxone, Cefepime).

---

## 3. Therapeutic Class Duplication (Dual NSAIDs)

Concurrent use of multiple medications within the same pharmacological class multiplies toxicities without enhancing clinical efficacy.

```
       Ibuprofen (Oral NSAID)              Naproxen (Oral NSAID)
                 \                                /
                  \                              /
                   v                            v
               Systemic Non-Selective COX-1 / COX-2 Inhibition
                                       |
        +------------------------------+------------------------------+
        |                                                             |
        v                                                             v
Gastrointestinal Mucosal Depletion                  Renal Afferent Vasoconstriction
  - Decreased protective prostaglandins (PGE2)        - Blocked vasodilatory prostaglandins
  - Multiplied risk of peptic ulcer disease           - Decreased Glomerular Filtration Rate (GFR)
  - Acute Upper GI Bleeding                           - Acute Kidney Injury (AKI) & Fluid Retention
```

### Evaluation Logic (`RX-1004`)
- Prescribing **Ibuprofen 600mg tid** concurrently with **Naproxen 500mg bid** provides no additional pain relief due to receptor saturation.
- Multiplies the hazard ratio for serious upper gastrointestinal bleeding and acute tubular necrosis.
- **Triage Level:** 🔴 **`HIGH_PRIORITY_REVIEW`**.
- **Action:** Pharmacist contacts prescriber to discontinue one NSAID or add gastroprotection (e.g., Proton Pump Inhibitors).

---

## 4. Drug-Drug Interactions (DDIs)

PharmacyGuard screens for both pharmacokinetic and pharmacodynamic interactions:

| Interaction Pair | Classification | Clinical Mechanism | Clinical Manifestation & Advice |
|---|---|---|---|
| **Lisinopril + Amlodipine** | Pharmacodynamic (Synergistic) | Concurrent renin-angiotensin-aldosterone system (RAAS) inhibition and peripheral arteriolar vasodilation. | Additive blood pressure reduction. Monitor for orthostatic dizziness upon initial combination therapy. |
| **Atorvastatin + Metformin** | Metabolic Co-administration | Concomitant management of hyperlipidemia and dysglycemia in metabolic syndrome. | Standard cardiovascular prevention regimen; monitor liver transaminases (ALT/AST) and HbA1c periodically. |
| **NSAID + ACE Inhibitor** | Pharmacodynamic (Antagonistic / Nephrotoxic) | NSAIDs inhibit renal vasodilatory prostaglandins while ACE inhibitors dilate efferent arterioles. | Reduced antihypertensive efficacy and elevated risk of acute renal functional decline. |

---

## 5. Dosage Range & Frequency Boundaries

The dosage check tool (`dosage_check`) evaluates single and cumulative 24-hour doses against clinical references:

### Dosing Frequency Multiplier Table
| Frequency String | Daily Multiplier | Calculated Doses / 24h |
|---|---|---|
| `Once daily`, `qd`, `morning`, `bedtime` | 1.0 | 1 |
| `Twice daily`, `bid`, `Every 12 hours`, `q12h` | 2.0 | 2 |
| `Three times daily`, `tid`, `Every 8 hours`, `q8h` | 3.0 | 3 |
| `Four times daily`, `qid`, `Every 6 hours`, `q6h` | 4.0 | 4 |
| `Every 4 hours`, `q4h` | 6.0 | 6 |

### Calculation & Boundary Rules
- **Daily Dose Calculation:** $\text{Daily Dose (mg)} = \text{Single Dose (mg)} \times \text{Daily Multiplier}$
- **Single Dose Ceilings:** If $\text{Single Dose} > \text{Max Single Dose Reference} \rightarrow$ Flags 🔴 **`HIGH_PRIORITY_REVIEW`**.
- **Daily Dose Ceilings:** If $\text{Daily Dose} > \text{Max Daily Dose Reference} \rightarrow$ Flags 🔴 **`HIGH_PRIORITY_REVIEW`**.
- **Sub-therapeutic Dosing:** If $\text{Single Dose} < \text{Min Therapeutic Dose} \rightarrow$ Flags 🟡 **`REVIEW`** for underdosing.
