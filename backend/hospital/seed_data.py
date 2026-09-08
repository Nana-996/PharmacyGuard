"""
Realistic fictional hospital dataset for PharmacyGuard development and testing.
All patient names, IDs, and records are 100% synthetic.
"""

SEED_PATIENTS = [
    {
        "patient_id": "PAT-101",
        "first_name": "John",
        "last_name": "Doe",
        "age": 34,
        "gender": "Male",
        "date_of_birth": "1992-04-12"
    },
    {
        "patient_id": "PAT-102",
        "first_name": "Jane",
        "last_name": "Smith",
        "age": 52,
        "gender": "Female",
        "date_of_birth": "1974-08-25"
    },
    {
        "patient_id": "PAT-103",
        "first_name": "Robert",
        "last_name": "Taylor",
        "age": 61,
        "gender": "Male",
        "date_of_birth": "1965-02-14"
    },
    {
        "patient_id": "PAT-104",
        "first_name": "Emily",
        "last_name": "Davis",
        "age": 45,
        "gender": "Female",
        "date_of_birth": "1981-11-03"
    },
    {
        "patient_id": "PAT-105",
        "first_name": "Michael",
        "last_name": "Chen",
        "age": 68,
        "gender": "Male",
        "date_of_birth": "1958-06-19"
    }
]

SEED_ALLERGIES = [
    # PAT-101: No drug allergies
    # PAT-102: Sulfa allergy
    {
        "allergy_id": "ALG-001",
        "patient_id": "PAT-102",
        "allergen": "Sulfamethoxazole / Trimethoprim (Sulfa Drugs)",
        "category": "Drug",
        "reaction": "Maculopapular rash, pruritus",
        "severity": "Moderate"
    },
    # PAT-103: Severe Penicillin Allergy
    {
        "allergy_id": "ALG-002",
        "patient_id": "PAT-103",
        "allergen": "Penicillin (Beta-Lactams)",
        "category": "Drug",
        "reaction": "Anaphylaxis, bronchospasm, facial angioedema",
        "severity": "Severe"
    },
    # PAT-104: Non-drug contact allergy
    {
        "allergy_id": "ALG-003",
        "patient_id": "PAT-104",
        "allergen": "Latex",
        "category": "Environmental",
        "reaction": "Contact dermatitis",
        "severity": "Mild"
    },
    # PAT-105: Codeine intolerance / allergy
    {
        "allergy_id": "ALG-004",
        "patient_id": "PAT-105",
        "allergen": "Codeine / Opioids",
        "category": "Drug",
        "reaction": "Severe nausea, vomiting, dizziness",
        "severity": "Moderate"
    }
]

SEED_DIAGNOSES = [
    {
        "diagnosis_id": "DX-001",
        "icd10_code": "J02.0",
        "description": "Streptococcal pharyngitis (Strep throat)"
    },
    {
        "diagnosis_id": "DX-002",
        "icd10_code": "E11.9",
        "description": "Type 2 diabetes mellitus without complications"
    },
    {
        "diagnosis_id": "DX-003",
        "icd10_code": "J01.90",
        "description": "Acute bacterial sinusitis, unspecified"
    },
    {
        "diagnosis_id": "DX-004",
        "icd10_code": "M17.9",
        "description": "Osteoarthritis of knee, unspecified"
    },
    {
        "diagnosis_id": "DX-005",
        "icd10_code": "I10",
        "description": "Essential (primary) hypertension"
    }
]

# 5 Test Scenarios:
# 1. RX-1001: Normal Prescription (Strep Throat -> Amoxicillin)
# 2. RX-1002: Potential Diagnosis/Medication Inconsistency (Diabetes -> Lisinopril with no HTN/renal indication)
# 3. RX-1003: Potential Allergy Conflict (Severe Penicillin Allergy -> Augmentin / Amoxicillin-Clavulanate)
# 4. RX-1004: Duplicate Medication / NSAID Duplication (Ibuprofen + Naproxen prescribed simultaneously)
# 5. RX-1005: Multiple Medications (Complex multi-drug regimen: Atorvastatin, Metformin, Lisinopril, Amlodipine)

SEED_PRESCRIPTIONS = [
    {
        "prescription_id": "RX-1001",
        "patient_id": "PAT-101",
        "diagnosis_id": "DX-001",
        "prescribed_date": "2026-08-20",
        "prescriber_name": "Dr. Sarah Adams, MD (Internal Medicine)",
        "status": "Pending Verification",
        "notes": "Standard 10-day antibiotic course for acute confirmed strep throat."
    },
    {
        "prescription_id": "RX-1002",
        "patient_id": "PAT-102",
        "diagnosis_id": "DX-002",
        "prescribed_date": "2026-08-21",
        "prescriber_name": "Dr. Marcus Vance, MD (Family Medicine)",
        "status": "Pending Verification",
        "notes": "Potential diagnosis mismatch: prescribed antihypertensive Lisinopril for isolated diabetes without documented hypertension."
    },
    {
        "prescription_id": "RX-1003",
        "patient_id": "PAT-103",
        "diagnosis_id": "DX-003",
        "prescribed_date": "2026-08-21",
        "prescriber_name": "Dr. Elena Rostova, MD (Otolaryngology)",
        "status": "Pending Verification",
        "notes": "Critical allergy alert: Patient has documented severe anaphylaxis to Penicillin, but was prescribed Augmentin."
    },
    {
        "prescription_id": "RX-1004",
        "patient_id": "PAT-104",
        "diagnosis_id": "DX-004",
        "prescribed_date": "2026-08-21",
        "prescriber_name": "Dr. Kevin Patel, MD (Orthopedics)",
        "status": "Pending Verification",
        "notes": "Therapeutic duplication: Concurrently prescribed two oral systemic NSAIDs (Ibuprofen and Naproxen)."
    },
    {
        "prescription_id": "RX-1005",
        "patient_id": "PAT-105",
        "diagnosis_id": "DX-005",
        "prescribed_date": "2026-08-21",
        "prescriber_name": "Dr. Arthur Pendelton, MD (Cardiology)",
        "status": "Pending Verification",
        "notes": "Multi-drug therapy: Comprehensive cardiovascular and metabolic management regimen."
    }
]

SEED_PRESCRIPTION_MEDICATIONS = [
    # RX-1001 (Normal)
    {
        "prescription_id": "RX-1001",
        "medication_name": "Amoxicillin 500mg Capsule",
        "generic_name": "Amoxicillin",
        "dosage": "500 mg",
        "route": "Oral",
        "frequency": "Every 8 hours (Three times daily)",
        "duration": "10 days",
        "instructions": "Take 1 capsule by mouth every 8 hours with or without food. Complete entire course."
    },
    # RX-1002 (Inconsistency: Lisinopril prescribed for Type 2 Diabetes)
    {
        "prescription_id": "RX-1002",
        "medication_name": "Lisinopril 20mg Tablet",
        "generic_name": "Lisinopril",
        "dosage": "20 mg",
        "route": "Oral",
        "frequency": "Once daily in the morning",
        "duration": "30 days",
        "instructions": "Take 1 tablet daily by mouth."
    },
    # RX-1003 (Allergy conflict: Augmentin with Penicillin allergy)
    {
        "prescription_id": "RX-1003",
        "medication_name": "Augmentin 875/125mg Tablet",
        "generic_name": "Amoxicillin / Clavulanate Potassium",
        "dosage": "875 mg / 125 mg",
        "route": "Oral",
        "frequency": "Every 12 hours (Twice daily)",
        "duration": "7 days",
        "instructions": "Take 1 tablet with food every 12 hours for 7 days."
    },
    # RX-1004 (Duplicate NSAID)
    {
        "prescription_id": "RX-1004",
        "medication_name": "Ibuprofen 600mg Tablet",
        "generic_name": "Ibuprofen",
        "dosage": "600 mg",
        "route": "Oral",
        "frequency": "Every 8 hours as needed for joint pain",
        "duration": "14 days",
        "instructions": "Take 1 tablet by mouth three times daily with meals as needed for pain."
    },
    {
        "prescription_id": "RX-1004",
        "medication_name": "Naproxen 500mg Tablet",
        "generic_name": "Naproxen",
        "dosage": "500 mg",
        "route": "Oral",
        "frequency": "Twice daily with meals",
        "duration": "30 days",
        "instructions": "Take 1 tablet twice daily with food or milk."
    },
    # RX-1005 (Multiple medications: 4 drugs)
    {
        "prescription_id": "RX-1005",
        "medication_name": "Atorvastatin Calcium 40mg Tablet",
        "generic_name": "Atorvastatin",
        "dosage": "40 mg",
        "route": "Oral",
        "frequency": "Once daily at bedtime",
        "duration": "90 days",
        "instructions": "Take 1 tablet daily at bedtime."
    },
    {
        "prescription_id": "RX-1005",
        "medication_name": "Metformin HCl 1000mg Tablet",
        "generic_name": "Metformin",
        "dosage": "1000 mg",
        "route": "Oral",
        "frequency": "Twice daily with meals",
        "duration": "90 days",
        "instructions": "Take 1 tablet twice daily with breakfast and dinner."
    },
    {
        "prescription_id": "RX-1005",
        "medication_name": "Lisinopril 10mg Tablet",
        "generic_name": "Lisinopril",
        "dosage": "10 mg",
        "route": "Oral",
        "frequency": "Once daily in the morning",
        "duration": "90 days",
        "instructions": "Take 1 tablet every morning."
    },
    {
        "prescription_id": "RX-1005",
        "medication_name": "Amlodipine Besylate 5mg Tablet",
        "generic_name": "Amlodipine",
        "dosage": "5 mg",
        "route": "Oral",
        "frequency": "Once daily",
        "duration": "90 days",
        "instructions": "Take 1 tablet by mouth daily."
    }
]
