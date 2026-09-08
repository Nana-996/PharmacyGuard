# PharmacyGuard — Synthetic Data & Clinical Dataset Reference

This document describes the synthetic data architecture, clinical reference tables, simulated hospital schemas, and privacy compliance standards utilized across **PharmacyGuard**.

---

## 1. Dual-Database Data Architecture

PharmacyGuard utilizes a **dual-database design** to cleanly separate external hospital electronic health records from the internal pharmacy clinical intelligence and audit layers:

```
+---------------------------------------------------------------------------------+
|                                DATA ARCHITECTURE                                |
|                                                                                 |
|  +-------------------------------------+   +---------------------------------+  |
|  |     hospital_sim.db (EHR Simulation)|   |  pharmacyguard.db (App Database)|  |
|  |  - patients                         |   |  - users & authentication       |  |
|  |  - allergies                        |   |  - medication_reference         |  |
|  |  - diagnoses (ICD-10 codes)         |   |  - diagnosis_guidelines         |  |
|  |  - prescriptions                    |   |  - allergy_cross_reactions      |  |
|  |  - prescription_medications         |   |  - drug_interactions            |  |
|  |                                     |   |  - medication_inventory         |  |
|  |  (Accessed via HospitalRepository   |   |  - pharmacist_reviews           |  |
|  |   swappable for real FHIR/HL7)      |   |  - immutable audit_events       |  |
|  +-------------------------------------+   +---------------------------------+  |
+---------------------------------------------------------------------------------+
```

---

## 2. Hospital Electronic Health Record (`hospital_sim.db`)

This database simulates an external inpatient/outpatient Hospital Information System:

### Table: `patients`
| Column | Type | Description |
|---|---|---|
| `patient_id` | `TEXT PRIMARY KEY` | Fictional hospital patient identifier (e.g., `PAT-001`). |
| `first_name` | `TEXT` | Fictional first name. |
| `last_name` | `TEXT` | Fictional last name. |
| `age` | `INTEGER` | Patient age in years. |
| `gender` | `TEXT` | Patient biological sex (`Male`, `Female`). |
| `date_of_birth` | `TEXT` | Synthetic date of birth (`YYYY-MM-DD`). |

### Table: `allergies`
| Column | Type | Description |
|---|---|---|
| `allergy_id` | `INTEGER PRIMARY KEY` | Unique allergy record identifier. |
| `patient_id` | `TEXT FOREIGN KEY` | References `patients.patient_id`. |
| `allergen` | `TEXT` | Allergen substance (e.g., `Penicillin`, `Sulfa`). |
| `category` | `TEXT` | `Drug`, `Environmental`, `Food`. |
| `reaction` | `TEXT` | Clinical reaction (e.g., `Anaphylaxis`, `Rash`, `Hives`). |
| `severity` | `TEXT` | Risk level (`Severe`, `Moderate`, `Mild`). |

### Table: `diagnoses`
| Column | Type | Description |
|---|---|---|
| `diagnosis_id` | `INTEGER PRIMARY KEY` | Unique diagnosis record ID. |
| `icd10_code` | `TEXT` | Standard ICD-10 diagnostic code (e.g., `J02.0`, `E11.9`). |
| `description` | `TEXT` | Formal clinical description. |

### Table: `prescriptions`
| Column | Type | Description |
|---|---|---|
| `prescription_id` | `TEXT PRIMARY KEY` | Order identifier (e.g., `RX-1001` through `RX-1005`). |
| `patient_id` | `TEXT FOREIGN KEY` | Patient receiving medication. |
| `diagnosis_id` | `INTEGER FOREIGN KEY` | Associated primary clinical indication. |
| `prescribed_date` | `TEXT` | Date order was signed. |
| `prescriber_name` | `TEXT` | Fictional prescribing physician. |
| `status` | `TEXT` | `PENDING`, `APPROVED`, `REJECTED`, `OVERRIDDEN`. |
| `notes` | `TEXT` | Prescriber instructions and clinical notes. |

### Table: `prescription_medications`
| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY` | Ordered item sequence ID. |
| `prescription_id` | `TEXT FOREIGN KEY` | References `prescriptions.prescription_id`. |
| `medication_name` | `TEXT` | Prescribed brand/generic name. |
| `generic_name` | `TEXT` | Active pharmaceutical ingredient. |
| `dosage` | `TEXT` | Single dose strength (e.g., `500mg`, `875/125mg`). |
| `route` | `TEXT` | Route of administration (`Oral`, `IV`, `Inhalation`). |
| `frequency` | `TEXT` | Administration frequency (e.g., `Every 8 hours`, `Once daily`). |
| `duration` | `TEXT` | Planned treatment duration (e.g., `10 days`). |
| `instructions` | `TEXT` | Patient administration directives. |

---

## 3. Clinical Intelligence & Operations (`pharmacyguard.db`)

### Clinical Reference Tables

1. **`medication_reference`:** Contains generic names, brand names, therapeutic classes, minimum/maximum single dose thresholds (mg), maximum 24-hour daily limits (mg), and clinical pearls.
2. **`diagnosis_medication_guidelines`:** Matches ICD-10 diagnostic codes to guideline-recommended therapeutic options, first-line vs. second-line status, and evidence citations.
3. **`allergy_cross_reactions`:** Codifies immunological cross-reactivities between drug classes (e.g., penicillins $\rightarrow$ aminopenicillins, first-generation cephalosporins, and carbapenems) with biological risk mechanisms.
4. **`drug_interactions`:** Catalog of significant pairwise drug interactions with severity levels (`Major`, `Moderate`, `Minor`), pharmacokinetic/pharmacodynamic mechanisms, and clinical actions.

### Table: `medication_inventory`
Simulates a live hospital inpatient/outpatient pharmacy inventory containing over 50 essential medications:

| Column | Type | Description |
|---|---|---|
| `inventory_id` | `TEXT PRIMARY KEY` | Stock tracking code (e.g., `INV-001`). |
| `medication_name` | `TEXT` | Medication product name. |
| `generic_name` | `TEXT` | Active pharmaceutical ingredient. |
| `strength` | `TEXT` | Packaged dosage strength (e.g., `500mg`, `20mg`). |
| `dosage_form` | `TEXT` | Formulation (`Oral Capsule`, `Oral Tablet`, `IV Solution`). |
| `quantity_on_hand` | `INTEGER` | Real-time physical units available in stock. |
| `reorder_level` | `INTEGER` | Low-stock trigger threshold. |
| `unit_cost` | `REAL` | Unit acquisition cost for pharmacy financial tracking. |
| `batch_number` | `TEXT` | Lot/batch tracking number. |
| `expiry_date` | `TEXT` | Expiration date (`YYYY-MM-DD`). |

---

## 4. Preloaded Fictional Test Cases

| Prescription ID | Patient Name | Age/Sex | Documented Allergies | Primary Diagnosis | Prescribed Medication | Intended Clinical Demonstration |
|---|---|---|---|---|---|---|
| **`RX-1001`** | John Doe | 34M | NKDA | `J02.0` (Strep pharyngitis) | Amoxicillin 500mg (q8h x 10d) | **Normal Clean Flow:** Standard first-line antibiotic, correct dose, fully in stock. |
| **`RX-1002`** | Jane Smith | 52F | NKDA | `E11.9` (Type 2 diabetes) | Lisinopril 20mg (qd) | **Indication Mismatch:** ACE inhibitor prescribed without documented hypertension diagnosis. |
| **`RX-1003`** | Robert Taylor | 61M | Penicillin (Severe Anaphylaxis) | `J01.90` (Acute bacterial sinusitis) | Augmentin 875/125mg (q12h) | **Severe Allergy Conflict:** Beta-lactam anaphylaxis hazard; testing Human-in-the-Loop override rationale. |
| **`RX-1004`** | Emily Davis | 45F | Sulfa drugs | `M17.9` (Knee osteoarthritis) | Ibuprofen 600mg + Naproxen 500mg | **Duplicate Therapy:** Concurrent oral NSAIDs multiplying gastrointestinal and renal toxicity. |
| **`RX-1005`** | Michael Chen | 68M | NKDA | `I10` (Essential hypertension) | Atorvastatin, Metformin, Lisinopril, Amlodipine | **Polypharmacy & Inventory:** Multi-drug cardiovascular regimen + 4-drug concurrent stock check. |

---

## 5. Ethical Statement & HIPAA Compliance

- **Completely Synthetic:** All names, dates, addresses, medical histories, and identifiers were synthetically authored. Any resemblance to real individuals, living or deceased, is purely coincidental.
- **HIPAA Safe Harbor:** Zero actual Protected Health Information (PHI) is contained within this codebase or any associated artifacts.
- **Safe for Open Demonstration:** This synthetic dataset is safe for academic evaluation, hackathon judging, and open-source distribution without compliance liability.
