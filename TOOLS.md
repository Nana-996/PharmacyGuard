# Agent Tools

This document provides technical documentation for the suite of specialized tools available to the **PharmacyGuard Strands Agent**. Each tool is decorated with the Strands Agents SDK `@tool` decorator, executing deterministic queries against local clinical and inventory databases.

---

## allergy_check

### Purpose:
Checks whether a prescribed medication conflicts with recorded allergies. Evaluates both direct allergen matches and immunological class cross-reactivities (such as aminopenicillins or cephalosporins in patients with documented penicillin allergy).

### Input:
- **`patient_allergies`** (*str*): The patient's recorded allergy string from the electronic health record (e.g., `"Penicillin (Beta-Lactams) - Severe Anaphylaxis"`, `"Sulfa"`, or `"NKDA"`).
- **`prescribed_medications`** (*list[str]* or *str*): List of prescribed medication names or a comma-separated string (e.g., `["Augmentin 875/125mg"]` or `"Amoxicillin, Lisinopril"`).

### Output:
Returns a structured dictionary indicating whether an allergy conflict exists, along with severity, mechanism, and recommendations:
```json
{
  "status": "success",
  "patient_allergies": "Penicillin (Beta-Lactams) - Severe Anaphylaxis",
  "evaluated_medications": ["Augmentin"],
  "has_allergy_conflict": true,
  "conflicts": [
    {
      "allergen_group": "Penicillin / Beta-Lactam",
      "conflicting_medication": "Augmentin (Amoxicillin/Clavulanate)",
      "reaction_risk": "Severe",
      "clinical_mechanism": "Augmentin contains Amoxicillin, an aminopenicillin. Patients with documented severe penicillin allergy risk immediate IgE-mediated type-I anaphylaxis."
    }
  ],
  "finding_priority": "HIGH PRIORITY REVIEW",
  "recommendation": "Documented allergy conflict detected (Penicillin / Beta-Lactam). Withhold dispensing pending prescriber contact and allergy reconciliation.",
  "requires_pharmacist_review": true,
  "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
}
```

### Data source:
- **Database:** `pharmacyguard.db`
- **Table:** `allergy_cross_reactions`
- **Fields:** `allergen_pattern`, `medication_pattern`, `allergen_group`, `reaction_risk`, `clinical_mechanism`

---

## diagnosis_medication_check

### Purpose:
Compares a patient's documented diagnosis against a prescribed medication to verify indication alignment according to clinical guideline references. Detects off-guideline therapies, unapproved indications, and diagnosis omissions.

### Input:
- **`diagnosis`** (*str*): The patient's active documented diagnosis or ICD-10 description (e.g., `"Type 2 diabetes mellitus without complications"`, `"Streptococcal pharyngitis"`).
- **`medication`** (*str*): The prescribed medication name (e.g., `"Lisinopril 20mg"`, `"Amoxicillin 500mg"`).

### Output:
Returns a structured dictionary evaluating guideline concordance:
```json
{
  "status": "success",
  "diagnosis": "Type 2 diabetes mellitus without complications",
  "medication": "Lisinopril 20mg",
  "relevant": false,
  "category": "POTENTIAL_MISMATCH",
  "evidence": "Lisinopril is an ACE inhibitor indicated for Essential Hypertension and Heart Failure. While indicated for Diabetic Nephropathy with documented proteinuria, no hypertension or nephropathy diagnosis is recorded for this patient.",
  "finding_priority": "REVIEW",
  "requires_pharmacist_review": true,
  "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
}
```

### Data source:
- **Database:** `pharmacyguard.db`
- **Table:** `diagnosis_medication_guidelines`
- **Fields:** `icd10_code`, `diagnosis_name`, `recommended_medications`, `is_first_line`, `clinical_evidence`

---

## duplicate_medication_check

### Purpose:
Identifies duplicate active ingredients or therapeutic class duplication among prescribed medications (e.g., concurrent prescription of multiple systemic NSAIDs like Ibuprofen and Naproxen).

### Input:
- **`prescribed_medications`** (*list[str]* or *str*): List of all prescribed medications in the order (e.g., `["Ibuprofen 600mg", "Naproxen 500mg"]`).

### Output:
Returns a structured dictionary indicating whether duplicate active ingredients or class redundancies were detected:
```json
{
  "status": "success",
  "has_duplicates": true,
  "detected_duplicates": [
    {
      "duplicate_type": "Therapeutic Class Duplication (NSAIDs)",
      "medications_involved": ["Ibuprofen 600mg", "Naproxen 500mg"],
      "therapeutic_class": "Nonsteroidal Anti-inflammatory Drug (NSAID)",
      "severity": "High",
      "explanation": "Concurrent prescription of multiple systemic NSAIDs (Ibuprofen 600mg, Naproxen 500mg) provides no additive pain relief but substantially multiplies risk of gastrointestinal bleeding, ulcers, and acute nephrotoxicity."
    }
  ],
  "finding_priority": "HIGH PRIORITY REVIEW",
  "explanation": "Concurrent prescription of multiple systemic NSAIDs provides no additive pain relief but substantially multiplies risk of gastrointestinal bleeding, ulcers, and acute nephrotoxicity.",
  "requires_pharmacist_review": true,
  "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
}
```

### Data source:
- **Database:** `pharmacyguard.db`
- **Table:** `medication_reference`
- **Fields:** `generic_name`, `brand_names`, `therapeutic_class`

---

## medication_interaction_check

### Purpose:
Screens all prescribed medications pairwise against the simulated drug-drug interaction knowledge base to identify documented pharmacodynamic and pharmacokinetic hazards.

### Input:
- **`prescribed_medications`** (*list[str]* or *str*): List of prescribed medications in the patient's regimen (e.g., `["Lisinopril 20mg", "Amlodipine 10mg"]`).

### Output:
Returns a structured dictionary detailing interaction mechanisms, clinical severity, and monitoring directives:
```json
{
  "status": "success",
  "evaluated_medications": ["Lisinopril 20mg", "Amlodipine 10mg"],
  "has_interactions": true,
  "interactions": [
    {
      "medication_a": "Lisinopril",
      "medication_b": "Amlodipine",
      "severity": "Moderate",
      "mechanism": "Additive pharmacodynamic blood pressure lowering effects.",
      "description": "Concurrent use of an ACE inhibitor and a calcium channel blocker enhances antihypertensive effect. Monitor for orthostatic hypotension.",
      "recommendation": "Monitor seated and standing blood pressure during initial titration."
    }
  ],
  "finding_priority": "REVIEW",
  "requires_pharmacist_review": true,
  "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
}
```

### Data source:
- **Database:** `pharmacyguard.db`
- **Table:** `drug_interactions`
- **Fields:** `medication_a`, `medication_b`, `severity`, `mechanism`, `description`, `recommendation`

---

## dosage_check

### Purpose:
Calculates estimated 24-hour cumulative doses based on administration frequency and compares single and daily totals against established clinical minimum and maximum boundaries.

### Input:
- **`medication`** (*str*): The medication name (e.g., `"Amoxicillin"`, `"Lisinopril"`).
- **`dosage`** (*str*): Prescribed single dose string (e.g., `"500mg"`, `"20mg"`, `"875/125mg"`).
- **`frequency`** (*str*): Administration frequency (e.g., `"Every 8 hours"`, `"Once daily"`, `"bid"`).

### Output:
Returns a structured dictionary evaluating dose safety against reference limits:
```json
{
  "status": "success",
  "medication": "Amoxicillin",
  "prescribed_dosage": "500mg",
  "prescribed_frequency": "Every 8 hours",
  "parsed_single_dose_mg": 500.0,
  "estimated_daily_dose_mg": 1500.0,
  "within_standard_range": true,
  "reference_data": {
    "generic_name": "Amoxicillin",
    "therapeutic_class": "Aminopenicillin Antibiotic",
    "standard_single_dose_range_mg": "250.0 - 500.0 mg",
    "max_daily_dose_mg": "1500.0 mg",
    "dosage_notes": "Take every 8 hours. Standard adult upper limit is 1500mg/day for pharyngitis."
  },
  "flags": [
    "Prescribed dose (500mg, Every 8 hours) is within standard reference boundaries (250.0-500.0 mg/dose, max 1500.0 mg/day)."
  ],
  "finding_priority": "CLEAR",
  "requires_pharmacist_review": true,
  "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
}
```

### Data source:
- **Database:** `pharmacyguard.db`
- **Table:** `medication_reference`
- **Fields:** `generic_name`, `therapeutic_class`, `min_single_dose_mg`, `max_single_dose_mg`, `max_daily_dose_mg`, `dosage_notes`

### Format Handling & Limitations:
- **Supported Formats:** Parses milligram single-dose values (e.g., `"500mg"`, `"20 mg"`) and standard frequency intervals (`"Every 8 hours"`, `"Three times daily"`, `"TID"`, `"Every 12 hours"`, `"BID"`, `"Once daily"`, `"QID"`).
- **Unrecognized Frequency Handling:** When a frequency string cannot be mapped to a known cadence, the daily multiplier conservatively defaults to `1.0` (assuming once-daily single-dose exposure) and preserves the original raw frequency string for clinician review.
- **Unrecognized Medication / Missing Reference:** If the medication is not mapped in `medication_reference` or the dosage cannot be parsed numerically, the tool does not mark it as passed; it returns `finding_priority: "REVIEW"` with an explicit note advising manual pharmacist verification.
- **Clinical Scope:** This tool provides prototype decision support on recognized synthetic formats. It is not a general clinical dosage engine (it does not perform renal CrCl clearance adjustments, body surface area calculation, pediatric weight-based scaling, or complex infusion titrations).

---

## inventory_check

*(Exposed in Python as `check_inventory`)*

### Purpose:
Checks stock availability in the hospital pharmacy for one or more prescribed medications, identifying whether items are in stock, low in stock, out of stock, or if the exact strength/dosage form is unavailable.

### Input:
- **`prescribed_medications`** (*list[dict]* or *list[str]*): List of prescribed medications with strength and formulation (e.g., `[{"medication": "Amoxicillin", "strength": "500mg", "dosage_form": "Oral Capsule"}]`).

### Output:
Returns a structured dictionary reporting on-hand inventory levels and availability flags:
```json
{
  "status": "success",
  "total_checked": 1,
  "has_out_of_stock": false,
  "has_low_stock": false,
  "has_strength_unavailable": false,
  "all_available": true,
  "inventory_results": [
    {
      "requested_medication": "Amoxicillin",
      "requested_strength": "500mg",
      "availability_status": "AVAILABLE",
      "quantity_available": 120,
      "reorder_level": 40,
      "stock_status": "Amoxicillin 500mg Oral Capsule is AVAILABLE with 120 units in stock.",
      "requires_pharmacist_attention": false
    }
  ],
  "safety_disclaimer": "This is decision-support information generated from simulated hospital inventory records. The licensed pharmacist makes all physical verification, substitution, and dispensing decisions."
}
```

### Data source:
- **Database:** `pharmacyguard.db`
- **Table:** `medication_inventory`
- **Fields:** `inventory_id`, `medication_name`, `generic_name`, `strength`, `dosage_form`, `quantity_on_hand`, `reorder_level`, `batch_number`, `expiry_date`

---

## low_stock_alert

*(Exposed in Python as `get_low_stock_items`)*

### Purpose:
Retrieves all pharmacy formulary medications whose on-hand quantity has dropped to or below their configured reorder threshold. Used for pharmacy supply chain coordination and restocking alerts.

### Input:
- *None* (No input arguments required).

### Output:
Returns a structured dictionary listing items needing replenishment:
```json
{
  "status": "success",
  "total_low_stock_items": 4,
  "low_stock_items": [
    {
      "inventory_id": "INV-012",
      "medication": "Albuterol Sulfate Inhalation Aerosol",
      "strength": "90mcg/actuation",
      "quantity_on_hand": 8,
      "reorder_level": 25,
      "deficit_to_reorder": 17,
      "stock_status": "LOW STOCK"
    },
    {
      "inventory_id": "INV-019",
      "medication": "Lisinopril Oral Tablet",
      "strength": "20mg",
      "quantity_on_hand": 12,
      "reorder_level": 30,
      "deficit_to_reorder": 18,
      "stock_status": "LOW STOCK"
    }
  ],
  "safety_disclaimer": "Simulated hospital inventory monitoring data for pharmacy supply chain coordination."
}
```

### Data source:
- **Database:** `pharmacyguard.db`
- **Table:** `medication_inventory`
- **Filter Query:** `WHERE quantity_on_hand <= reorder_level ORDER BY (reorder_level - quantity_on_hand) DESC`

---

## inventory_summary

*(Exposed in Python as `get_inventory_summary`)*

### Purpose:
Computes high-level pharmacy inventory overview metrics and stock health statistics for operational dashboards and Chief Pharmacist monitoring.

### Input:
- *None* (No input arguments required).

### Output:
Returns aggregate formulary metrics:
```json
{
  "status": "success",
  "inventory_summary": {
    "total_tracked_medications": 52,
    "number_available": 46,
    "number_low_stock": 4,
    "number_out_of_stock": 2,
    "number_below_reorder_level": 6,
    "stock_health_percentage": 88.5,
    "last_inventory_sync": "2026-09-08T03:30:00Z"
  },
  "safety_disclaimer": "Simulated hospital inventory metrics for pharmacy operations decision support."
}
```

### Data source:
- **Database:** `pharmacyguard.db`
- **Table:** `medication_inventory`
- **Aggregations:** `COUNT(*)`, `SUM(CASE WHEN quantity_on_hand > reorder_level THEN 1 ELSE 0 END)`, etc.

---

## get_prescription

### Purpose:
Retrieves complete electronic prescription data, patient demographics, documented allergy history, active ICD-10 diagnoses, and medication order items from the hospital electronic health record.

### Input:
- **`prescription_id`** (*str*): The unique identifier of the prescription order (e.g., `"RX-1001"`, `"RX-1003"`).

### Output:
Returns the complete patient and prescription record:
```json
{
  "status": "success",
  "message": "Prescription 'RX-1003' retrieved successfully.",
  "data": {
    "prescription_id": "RX-1003",
    "patient": {
      "patient_id": "PAT-003",
      "name": "Robert Taylor",
      "age": 61,
      "gender": "Male",
      "allergies": "Penicillin (Beta-Lactams) - Severe Anaphylaxis"
    },
    "diagnoses": [
      {
        "icd10_code": "J01.90",
        "diagnosis": "Acute bacterial sinusitis, unspecified"
      }
    ],
    "medications": [
      {
        "medication": "Augmentin",
        "dosage": "875/125mg",
        "route": "Oral",
        "frequency": "Every 12 hours",
        "duration": "7 days",
        "instructions": "Take with food to prevent gastrointestinal upset."
      }
    ],
    "prescribing_doctor": "Dr. Sarah Jenkins, MD",
    "prescription_date": "2026-09-07"
  }
}
```

### Data source:
- **Database:** `hospital_sim.db`
- **Tables:** `prescriptions`, `patients`, `allergies`, `diagnoses`, `prescription_medications`
