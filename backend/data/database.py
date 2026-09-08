"""
Simulated Hospital Prescription Database (SQLite) for PharmacyGuard.
Provides storage, schema initialization, synthetic test case seeding,
clinical reference knowledge bases, pharmacy inventory stock tracking,
pharmacist review records, structured findings, and audit trails.

NOTE: All data in this module is 100% synthetic/fictional and used solely
for development, testing, and operations agent demonstration.
"""

import os
import re
import json
import uuid
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union


# Default path for SQLite database: backend/data/pharmacyguard.db
DEFAULT_DB_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "pharmacyguard.db")


SEED_PATIENTS = [
    {
        "patient_id": "PAT-101",
        "name": "John Doe",
        "age": 34,
        "sex": "Male",
        "allergies": "No known drug allergies (NKDA)"
    },
    {
        "patient_id": "PAT-102",
        "name": "Jane Smith",
        "age": 52,
        "sex": "Female",
        "allergies": "Sulfamethoxazole / Trimethoprim (Sulfa)"
    },
    {
        "patient_id": "PAT-103",
        "name": "Robert Taylor",
        "age": 61,
        "sex": "Male",
        "allergies": "Penicillin (Beta-Lactams) - Severe Anaphylaxis"
    },
    {
        "patient_id": "PAT-104",
        "name": "Emily Davis",
        "age": 45,
        "sex": "Female",
        "allergies": "Latex (Mild contact rash)"
    },
    {
        "patient_id": "PAT-105",
        "name": "Michael Chen",
        "age": 68,
        "sex": "Male",
        "allergies": "Codeine (Moderate nausea/vomiting)"
    }
]

SEED_DIAGNOSES = [
    {
        "diagnosis_id": "DX-101",
        "patient_id": "PAT-101",
        "diagnosis": "Streptococcal pharyngitis (Strep throat)",
        "diagnosis_date": "2026-08-20"
    },
    {
        "diagnosis_id": "DX-102",
        "patient_id": "PAT-102",
        "diagnosis": "Type 2 diabetes mellitus without complications",
        "diagnosis_date": "2026-08-21"
    },
    {
        "diagnosis_id": "DX-103",
        "patient_id": "PAT-103",
        "diagnosis": "Acute bacterial sinusitis, unspecified",
        "diagnosis_date": "2026-08-21"
    },
    {
        "diagnosis_id": "DX-104",
        "patient_id": "PAT-104",
        "diagnosis": "Osteoarthritis of knee, unspecified",
        "diagnosis_date": "2026-08-21"
    },
    {
        "diagnosis_id": "DX-105",
        "patient_id": "PAT-105",
        "diagnosis": "Essential hypertension and Hyperlipidemia",
        "diagnosis_date": "2026-08-21"
    }
]

SEED_MEDICATIONS = [
    {
        "medication_id": "MED-001",
        "generic_name": "Amoxicillin",
        "brand_name": "Amoxil",
        "therapeutic_class": "Penicillin Antibiotic"
    },
    {
        "medication_id": "MED-002",
        "generic_name": "Lisinopril",
        "brand_name": "Prinivil / Zestril",
        "therapeutic_class": "ACE Inhibitor (Antihypertensive)"
    },
    {
        "medication_id": "MED-003",
        "generic_name": "Amoxicillin / Clavulanate Potassium",
        "brand_name": "Augmentin",
        "therapeutic_class": "Beta-Lactam Antibiotic"
    },
    {
        "medication_id": "MED-004",
        "generic_name": "Ibuprofen",
        "brand_name": "Advil / Motrin",
        "therapeutic_class": "Nonsteroidal Anti-inflammatory Drug (NSAID)"
    },
    {
        "medication_id": "MED-005",
        "generic_name": "Naproxen",
        "brand_name": "Aleve / Naprosyn",
        "therapeutic_class": "Nonsteroidal Anti-inflammatory Drug (NSAID)"
    },
    {
        "medication_id": "MED-006",
        "generic_name": "Atorvastatin Calcium",
        "brand_name": "Lipitor",
        "therapeutic_class": "HMG-CoA Reductase Inhibitor (Statin)"
    },
    {
        "medication_id": "MED-007",
        "generic_name": "Metformin Hydrochloride",
        "brand_name": "Glucophage",
        "therapeutic_class": "Biguanide Antidiabetic"
    },
    {
        "medication_id": "MED-008",
        "generic_name": "Amlodipine Besylate",
        "brand_name": "Norvasc",
        "therapeutic_class": "Calcium Channel Blocker"
    }
]

SEED_PRESCRIPTIONS = [
    # Case 1: Routine
    {
        "prescription_id": "RX-1001",
        "patient_id": "PAT-101",
        "medication": "Amoxicillin",
        "strength": "500mg",
        "dosage": "1 capsule (500mg)",
        "frequency": "Every 8 hours (Three times daily)",
        "route": "Oral",
        "duration": "10 days",
        "prescribing_doctor": "Dr. Sarah Adams, MD (Internal Medicine)",
        "prescription_date": "2026-08-20"
    },
    # Case 2: Potential Diagnosis Mismatch
    {
        "prescription_id": "RX-1002",
        "patient_id": "PAT-102",
        "medication": "Lisinopril",
        "strength": "20mg",
        "dosage": "1 tablet (20mg)",
        "frequency": "Once daily in the morning",
        "route": "Oral",
        "duration": "30 days",
        "prescribing_doctor": "Dr. Marcus Vance, MD (Family Medicine)",
        "prescription_date": "2026-08-21"
    },
    # Case 3: Documented Allergy Conflict
    {
        "prescription_id": "RX-1003",
        "patient_id": "PAT-103",
        "medication": "Augmentin (Amoxicillin / Clavulanate)",
        "strength": "875mg / 125mg",
        "dosage": "1 tablet (875/125mg)",
        "frequency": "Every 12 hours (Twice daily)",
        "route": "Oral",
        "duration": "7 days",
        "prescribing_doctor": "Dr. Elena Rostova, MD (Otolaryngology)",
        "prescription_date": "2026-08-21"
    },
    # Case 4: Duplicate Medication (Two systemic NSAIDs)
    {
        "prescription_id": "RX-1004",
        "patient_id": "PAT-104",
        "medication": "Ibuprofen",
        "strength": "600mg",
        "dosage": "1 tablet (600mg)",
        "frequency": "Every 8 hours with meals as needed",
        "route": "Oral",
        "duration": "14 days",
        "prescribing_doctor": "Dr. Kevin Patel, MD (Orthopedics)",
        "prescription_date": "2026-08-21"
    },
    {
        "prescription_id": "RX-1004",
        "patient_id": "PAT-104",
        "medication": "Naproxen",
        "strength": "500mg",
        "dosage": "1 tablet (500mg)",
        "frequency": "Twice daily with food",
        "route": "Oral",
        "duration": "30 days",
        "prescribing_doctor": "Dr. Kevin Patel, MD (Orthopedics)",
        "prescription_date": "2026-08-21"
    },
    # Case 5: Multiple Medications (4 drugs)
    {
        "prescription_id": "RX-1005",
        "patient_id": "PAT-105",
        "medication": "Atorvastatin Calcium",
        "strength": "40mg",
        "dosage": "1 tablet (40mg)",
        "frequency": "Once daily at bedtime",
        "route": "Oral",
        "duration": "90 days",
        "prescribing_doctor": "Dr. Arthur Pendelton, MD (Cardiology)",
        "prescription_date": "2026-08-21"
    },
    {
        "prescription_id": "RX-1005",
        "patient_id": "PAT-105",
        "medication": "Metformin HCl",
        "strength": "1000mg",
        "dosage": "1 tablet (1000mg)",
        "frequency": "Twice daily with meals",
        "route": "Oral",
        "duration": "90 days",
        "prescribing_doctor": "Dr. Arthur Pendelton, MD (Cardiology)",
        "prescription_date": "2026-08-21"
    },
    {
        "prescription_id": "RX-1005",
        "patient_id": "PAT-105",
        "medication": "Lisinopril",
        "strength": "10mg",
        "dosage": "1 tablet (10mg)",
        "frequency": "Once daily in the morning",
        "route": "Oral",
        "duration": "90 days",
        "prescribing_doctor": "Dr. Arthur Pendelton, MD (Cardiology)",
        "prescription_date": "2026-08-21"
    },
    {
        "prescription_id": "RX-1005",
        "patient_id": "PAT-105",
        "medication": "Amlodipine Besylate",
        "strength": "5mg",
        "dosage": "1 tablet (5mg)",
        "frequency": "Once daily",
        "route": "Oral",
        "duration": "90 days",
        "prescribing_doctor": "Dr. Arthur Pendelton, MD (Cardiology)",
        "prescription_date": "2026-08-21"
    }
]

# Simulated Clinical Reference Data: Drug Interactions
SEED_MEDICATION_INTERACTIONS = [
    {
        "medication_a": "Ibuprofen",
        "medication_b": "Naproxen",
        "severity": "Major",
        "mechanism": "Concurrent dual systemic NSAID therapy",
        "description": "Additive cyclooxygenase (COX-1/COX-2) inhibition significantly increases risk of major gastrointestinal ulceration, severe bleeding, and acute renal impairment without additional analgesic benefit.",
        "recommendation": "Avoid concurrent use. Select a single appropriate NSAID or consider non-NSAID multimodal pain therapy."
    },
    {
        "medication_a": "Lisinopril",
        "medication_b": "Amlodipine",
        "severity": "Minor",
        "mechanism": "Additive antihypertensive synergy",
        "description": "Synergistic blood pressure reduction. Frequently utilized guideline combination (ACEI + CCB), but requires routine blood pressure and symptom monitoring for excessive hypotension.",
        "recommendation": "Appropriate combination when indicated; monitor blood pressure and dizziness upon initiation."
    },
    {
        "medication_a": "Atorvastatin",
        "medication_b": "Clarithromycin",
        "severity": "Major",
        "mechanism": "Strong CYP3A4 enzymatic inhibition",
        "description": "Clarithromycin substantially elevates atorvastatin plasma concentrations, markedly increasing risk of myopathy and rhabdomyolysis.",
        "recommendation": "Temporarily suspend atorvastatin during macrolide therapy or use an alternative antibiotic."
    },
    {
        "medication_a": "Lisinopril",
        "medication_b": "Potassium Chloride",
        "severity": "Major",
        "mechanism": "Inhibition of aldosterone-mediated potassium excretion",
        "description": "ACE inhibitors reduce aldosterone production, leading to potassium retention; concomitant potassium supplementation risks life-threatening hyperkalemia.",
        "recommendation": "Monitor serum potassium and renal function closely; avoid routine potassium supplements unless hypokalemic."
    },
    {
        "medication_a": "Metformin",
        "medication_b": "Iodinated Contrast",
        "severity": "Moderate",
        "mechanism": "Contrast-induced acute nephropathy with metformin accumulation",
        "description": "Iodinated contrast may cause transient acute renal failure, leading to accumulation of metformin and potential lactic acidosis.",
        "recommendation": "Withhold metformin prior to or at time of iodinated contrast procedure and resume 48 hours post-procedure after renal function is re-evaluated."
    }
]

# Simulated Clinical Reference Data: Dosage Ranges and Standard Indications
SEED_MEDICATION_REFERENCE = [
    {
        "medication_id": "REF-001",
        "generic_name": "Amoxicillin",
        "brand_names": "Amoxil, Trimox",
        "therapeutic_class": "Penicillin Antibiotic",
        "standard_indications": "Streptococcal pharyngitis, acute otitis media, lower respiratory tract infections, skin infections",
        "min_single_dose_mg": 250.0,
        "max_single_dose_mg": 1000.0,
        "max_daily_dose_mg": 3000.0,
        "common_routes": "Oral",
        "dosage_notes": "Standard adult dose for strep throat: 500mg every 8 hours or 1000mg every 12 hours for 10 days."
    },
    {
        "medication_id": "REF-002",
        "generic_name": "Lisinopril",
        "brand_names": "Prinivil, Zestril, Qbrelis",
        "therapeutic_class": "ACE Inhibitor (Antihypertensive)",
        "standard_indications": "Essential hypertension, heart failure (reduced ejection fraction), acute myocardial infarction (adjunct), diabetic nephropathy (with proteinuria)",
        "min_single_dose_mg": 2.5,
        "max_single_dose_mg": 40.0,
        "max_daily_dose_mg": 40.0,
        "common_routes": "Oral",
        "dosage_notes": "Initial hypertension dose 10mg once daily, maintenance 20-40mg once daily."
    },
    {
        "medication_id": "REF-003",
        "generic_name": "Amoxicillin / Clavulanate Potassium",
        "brand_names": "Augmentin, Augmentin XR",
        "therapeutic_class": "Beta-Lactam Antibiotic (Penicillin/Beta-lactamase inhibitor)",
        "standard_indications": "Acute bacterial sinusitis, community-acquired pneumonia, acute otitis media, bite wounds",
        "min_single_dose_mg": 500.0,
        "max_single_dose_mg": 1000.0,
        "max_daily_dose_mg": 2000.0,
        "common_routes": "Oral",
        "dosage_notes": "Standard adult dose: 875/125mg orally every 12 hours or 500/125mg orally every 8 hours."
    },
    {
        "medication_id": "REF-004",
        "generic_name": "Ibuprofen",
        "brand_names": "Advil, Motrin",
        "therapeutic_class": "Nonsteroidal Anti-inflammatory Drug (NSAID)",
        "standard_indications": "Osteoarthritis, rheumatoid arthritis, mild to moderate pain, dysmenorrhea, fever",
        "min_single_dose_mg": 200.0,
        "max_single_dose_mg": 800.0,
        "max_daily_dose_mg": 2400.0,
        "common_routes": "Oral",
        "dosage_notes": "Adult analgesic dose: 400-600mg every 6 to 8 hours with food; maximum prescription dose 2400mg/day."
    },
    {
        "medication_id": "REF-005",
        "generic_name": "Naproxen",
        "brand_names": "Aleve, Naprosyn, Anaprox",
        "therapeutic_class": "Nonsteroidal Anti-inflammatory Drug (NSAID)",
        "standard_indications": "Osteoarthritis, rheumatoid arthritis, ankylosing spondylitis, acute gout, mild-moderate pain",
        "min_single_dose_mg": 250.0,
        "max_single_dose_mg": 500.0,
        "max_daily_dose_mg": 1250.0,
        "common_routes": "Oral",
        "dosage_notes": "Standard adult anti-inflammatory dose: 250-500mg twice daily with meals."
    },
    {
        "medication_id": "REF-006",
        "generic_name": "Atorvastatin Calcium",
        "brand_names": "Lipitor",
        "therapeutic_class": "HMG-CoA Reductase Inhibitor (Statin)",
        "standard_indications": "Hyperlipidemia, primary dysbetalipoproteinemia, prevention of cardiovascular disease",
        "min_single_dose_mg": 10.0,
        "max_single_dose_mg": 80.0,
        "max_daily_dose_mg": 80.0,
        "common_routes": "Oral",
        "dosage_notes": "Daily dose 10mg to 80mg once daily at any time of day."
    },
    {
        "medication_id": "REF-007",
        "generic_name": "Metformin Hydrochloride",
        "brand_names": "Glucophage, Fortamet, Glumetza",
        "therapeutic_class": "Biguanide Antidiabetic",
        "standard_indications": "Type 2 diabetes mellitus (first-line monotherapy or combination)",
        "min_single_dose_mg": 500.0,
        "max_single_dose_mg": 1000.0,
        "max_daily_dose_mg": 2550.0,
        "common_routes": "Oral",
        "dosage_notes": "Initial 500mg twice daily or 850mg once daily with meals; titrated up to maximum 2000-2550mg daily."
    },
    {
        "medication_id": "REF-008",
        "generic_name": "Amlodipine Besylate",
        "brand_names": "Norvasc",
        "therapeutic_class": "Calcium Channel Blocker (Dihydropyridine)",
        "standard_indications": "Essential hypertension, chronic stable angina, vasospastic angina",
        "min_single_dose_mg": 2.5,
        "max_single_dose_mg": 10.0,
        "max_daily_dose_mg": 10.0,
        "common_routes": "Oral",
        "dosage_notes": "Initial dose 5mg once daily; maximum dose 10mg once daily."
    }
]

# Simulated Allergy Cross-Reactivity Reference Data
SEED_ALLERGY_CROSS_REACTIONS = [
    {
        "allergen_group": "Penicillin",
        "medication_pattern": "penicillin, amoxicillin, augmentin, ampicillin, piperacillin, amoxil",
        "reaction_risk": "Severe",
        "explanation": "Penicillins and aminopenicillins share the core beta-lactam and thiazolidine ring structures. Patients with documented penicillin allergy (especially severe/anaphylactic) have high risk of acute type I IgE-mediated allergic reactions to Amoxicillin and Augmentin."
    },
    {
        "allergen_group": "Sulfa",
        "medication_pattern": "sulfamethoxazole, trimethoprim-sulfamethoxazole, bactrim, sulfasalazine, sulfadiazine",
        "reaction_risk": "Moderate",
        "explanation": "Sulfonamide arylamine medications share the N1-substituted aromatic sulfonamide structure, carrying significant cross-reactivity risk causing maculopapular rash, erythema multiforme, or Stevens-Johnson syndrome."
    },
    {
        "allergen_group": "NSAIDs",
        "medication_pattern": "ibuprofen, naproxen, aspirin, meloxicam, ketorolac, diclofenac, indomethacin, celecoxib",
        "reaction_risk": "Moderate",
        "explanation": "Nonsteroidal anti-inflammatory drugs cause cross-reactive pseudoallergic reactions via COX-1 inhibition and leukotriene shunting."
    },
    {
        "allergen_group": "Codeine / Opioids",
        "medication_pattern": "codeine, morphine, hydrocodone, oxycodone, hydromorphone",
        "reaction_risk": "Moderate",
        "explanation": "Phenanthrene class opioids share structural features that may precipitate histamine release or true opioid receptor-associated intolerance."
    }
]

# Simulated Diagnosis Indications Reference Data
SEED_DIAGNOSIS_INDICATIONS = [
    {
        "diagnosis_keyword": "pharyngitis",
        "approved_drug_classes": "Penicillin Antibiotics, Cephalosporins, Macrolides",
        "approved_generic_drugs": "amoxicillin, penicillin v, cephalexin, azithromycin, clarithromycin",
        "clinical_rationale": "Streptococcal pharyngitis is a Group A Streptococcal bacterial infection for which oral Amoxicillin or Penicillin V is first-line standard therapy."
    },
    {
        "diagnosis_keyword": "sinusitis",
        "approved_drug_classes": "Beta-Lactam/Beta-lactamase inhibitors, Fluoroquinolones, Tetracyclines",
        "approved_generic_drugs": "amoxicillin / clavulanate, augmentin, doxycycline, levofloxacin",
        "clinical_rationale": "Acute bacterial rhinosinusitis standard first-line empirical antibiotic therapy is Amoxicillin-Clavulanate (Augmentin)."
    },
    {
        "diagnosis_keyword": "diabetes",
        "approved_drug_classes": "Biguanides, SGLT2 Inhibitors, GLP-1 Receptor Agonists, Sulfonylureas, DPP-4 Inhibitors, Insulin",
        "approved_generic_drugs": "metformin, empagliflozin, semaglutide, glipizide, sitagliptin, insulin glargine",
        "clinical_rationale": "First-line pharmacotherapy for Type 2 Diabetes Mellitus consists of Metformin and glycemic agents. Antihypertensives like Lisinopril are indicated only when comorbid hypertension or diabetic nephropathy with albuminuria is documented."
    },
    {
        "diagnosis_keyword": "osteoarthritis",
        "approved_drug_classes": "NSAIDs, Analgesics, Topical NSAIDs",
        "approved_generic_drugs": "ibuprofen, naproxen, acetaminophen, meloxicam, diclofenac",
        "clinical_rationale": "Osteoarthritis pain management includes single-agent oral NSAIDs or topical agents alongside physical therapy."
    },
    {
        "diagnosis_keyword": "hypertension",
        "approved_drug_classes": "ACE Inhibitors, Angiotensin Receptor Blockers, Calcium Channel Blockers, Thiazide Diuretics",
        "approved_generic_drugs": "lisinopril, amlodipine, hydrochlorothiazide, losartan, valsartan",
        "clinical_rationale": "First-line antihypertensive agents include ACE inhibitors (Lisinopril), CCBs (Amlodipine), and thiazides."
    },
    {
        "diagnosis_keyword": "hyperlipidemia",
        "approved_drug_classes": "HMG-CoA Reductase Inhibitors (Statins), Cholesterol Absorption Inhibitors, PCSK9 Inhibitors",
        "approved_generic_drugs": "atorvastatin, rosuvastatin, simvastatin, ezetimibe",
        "clinical_rationale": "Standard lipid-lowering therapy for hyperlipidemia and cardiovascular risk reduction centers on statin therapy (Atorvastatin)."
    }
]

# Simulated Hospital Pharmacy Inventory Records
SEED_INVENTORY = [
    {
        "inventory_id": "INV-001",
        "medication": "Amoxicillin 500mg Capsule",
        "generic_name": "Amoxicillin",
        "strength": "500mg",
        "dosage_form": "Capsule",
        "quantity_on_hand": 350,
        "reorder_level": 50,
        "unit": "capsules",
        "last_updated": "2026-08-25 08:00:00"
    },
    {
        "inventory_id": "INV-002",
        "medication": "Amoxicillin 250mg Capsule",
        "generic_name": "Amoxicillin",
        "strength": "250mg",
        "dosage_form": "Capsule",
        "quantity_on_hand": 120,
        "reorder_level": 30,
        "unit": "capsules",
        "last_updated": "2026-08-25 08:00:00"
    },
    {
        "inventory_id": "INV-003",
        "medication": "Lisinopril 20mg Tablet",
        "generic_name": "Lisinopril",
        "strength": "20mg",
        "dosage_form": "Tablet",
        "quantity_on_hand": 12,
        "reorder_level": 30,
        "unit": "tablets",
        "last_updated": "2026-08-25 08:00:00"
    },
    {
        "inventory_id": "INV-004",
        "medication": "Lisinopril 10mg Tablet",
        "generic_name": "Lisinopril",
        "strength": "10mg",
        "dosage_form": "Tablet",
        "quantity_on_hand": 180,
        "reorder_level": 40,
        "unit": "tablets",
        "last_updated": "2026-08-25 08:00:00"
    },
    {
        "inventory_id": "INV-005",
        "medication": "Augmentin 875/125mg Tablet",
        "generic_name": "Amoxicillin / Clavulanate Potassium",
        "strength": "875mg / 125mg",
        "dosage_form": "Tablet",
        "quantity_on_hand": 0,
        "reorder_level": 25,
        "unit": "tablets",
        "last_updated": "2026-08-25 08:00:00"
    },
    {
        "inventory_id": "INV-006",
        "medication": "Augmentin 500/125mg Tablet",
        "generic_name": "Amoxicillin / Clavulanate Potassium",
        "strength": "500mg / 125mg",
        "dosage_form": "Tablet",
        "quantity_on_hand": 45,
        "reorder_level": 20,
        "unit": "tablets",
        "last_updated": "2026-08-25 08:00:00"
    },
    {
        "inventory_id": "INV-007",
        "medication": "Ibuprofen 600mg Tablet",
        "generic_name": "Ibuprofen",
        "strength": "600mg",
        "dosage_form": "Tablet",
        "quantity_on_hand": 0,
        "reorder_level": 50,
        "unit": "tablets",
        "last_updated": "2026-08-25 08:00:00"
    },
    {
        "inventory_id": "INV-008",
        "medication": "Ibuprofen 200mg Tablet",
        "generic_name": "Ibuprofen",
        "strength": "200mg",
        "dosage_form": "Tablet",
        "quantity_on_hand": 500,
        "reorder_level": 100,
        "unit": "tablets",
        "last_updated": "2026-08-25 08:00:00"
    },
    {
        "inventory_id": "INV-009",
        "medication": "Naproxen 500mg Tablet",
        "generic_name": "Naproxen",
        "strength": "500mg",
        "dosage_form": "Tablet",
        "quantity_on_hand": 140,
        "reorder_level": 30,
        "unit": "tablets",
        "last_updated": "2026-08-25 08:00:00"
    },
    {
        "inventory_id": "INV-010",
        "medication": "Atorvastatin Calcium 40mg Tablet",
        "generic_name": "Atorvastatin",
        "strength": "40mg",
        "dosage_form": "Tablet",
        "quantity_on_hand": 80,
        "reorder_level": 25,
        "unit": "tablets",
        "last_updated": "2026-08-25 08:00:00"
    },
    {
        "inventory_id": "INV-011",
        "medication": "Metformin HCl 1000mg Tablet",
        "generic_name": "Metformin",
        "strength": "1000mg",
        "dosage_form": "Tablet",
        "quantity_on_hand": 6,
        "reorder_level": 40,
        "unit": "tablets",
        "last_updated": "2026-08-25 08:00:00"
    },
    {
        "inventory_id": "INV-012",
        "medication": "Metformin HCl 500mg Tablet",
        "generic_name": "Metformin",
        "strength": "500mg",
        "dosage_form": "Tablet",
        "quantity_on_hand": 220,
        "reorder_level": 50,
        "unit": "tablets",
        "last_updated": "2026-08-25 08:00:00"
    },
    {
        "inventory_id": "INV-013",
        "medication": "Amlodipine Besylate 5mg Tablet",
        "generic_name": "Amlodipine",
        "strength": "5mg",
        "dosage_form": "Tablet",
        "quantity_on_hand": 95,
        "reorder_level": 20,
        "unit": "tablets",
        "last_updated": "2026-08-25 08:00:00"
    },
    {
        "inventory_id": "INV-014",
        "medication": "Amlodipine Besylate 2.5mg Tablet",
        "generic_name": "Amlodipine",
        "strength": "2.5mg",
        "dosage_form": "Tablet",
        "quantity_on_hand": 60,
        "reorder_level": 15,
        "unit": "tablets",
        "last_updated": "2026-08-25 08:00:00"
    }
]


# Development Seed Users (Explicitly for local development and demonstration)
SEED_USERS = [
    {
        "user_id": "USR-STAFF-001",
        "full_name": "Dr. Alex Reed, PharmD",
        "email": "staff.pharmacist@hospital.dev",
        "password_plain": "DevStaff123!",
        "role": "STAFF_PHARMACIST",
        "active": 1,
        "created_at": "2026-08-20T08:00:00Z"
    },
    {
        "user_id": "USR-CHIEF-001",
        "full_name": "Dr. Eleanor Vance, PharmD (Chief)",
        "email": "chief.pharmacist@hospital.dev",
        "password_plain": "DevChief123!",
        "role": "CHIEF_PHARMACIST",
        "active": 1,
        "created_at": "2026-08-20T08:00:00Z"
    },
    {
        "user_id": "USR-STUD-001",
        "full_name": "Sam Taylor (Pharmacy Intern)",
        "email": "student@hospital.dev",
        "password_plain": "DevStudent123!",
        "role": "PHARMACY_STUDENT",
        "active": 1,
        "created_at": "2026-08-20T08:00:00Z"
    },
    {
        "user_id": "USR-ADMIN-001",
        "full_name": "System Administrator",
        "email": "admin@hospital.dev",
        "password_plain": "DevAdmin123!",
        "role": "ADMIN",
        "active": 1,
        "created_at": "2026-08-20T08:00:00Z"
    }
]

# Development Seed Educational Cases for Pharmacy Intern / Student Training
SEED_EDUCATIONAL_CASES = [
    {
        "case_id": "EDU-101",
        "title": "Beta-Lactam Cross-Reactivity in Severe Penicillin Anaphylaxis",
        "clinical_category": "ALLERGY",
        "difficulty": "INTERMEDIATE",
        "scenario_text": "A 54-year-old female presents to the acute care outpatient clinic with severe purulent rhinosinusitis and fever. Her electronic health record documents a confirmed severe Penicillin anaphylaxis reaction (hives, bronchospasm, emergency epinephrine). A prescription order is received for Augmentin (Amoxicillin / Clavulanate) 875mg / 125mg PO BID for 10 days.",
        "deidentified_prescription_json": json.dumps([
            {
                "medication": "Augmentin (Amoxicillin / Clavulanate)",
                "strength": "875mg / 125mg",
                "dosage": "1 tablet",
                "frequency": "Twice daily",
                "route": "Oral",
                "duration": "10 days"
            }
        ]),
        "key_safety_challenge": "Identifying beta-lactam shared core ring allergenicity and recommending safe non-cross-reactive alternatives.",
        "multiple_choice_question": "Which of the following clinical decisions represents the most appropriate, guideline-concordant course of action for this patient?",
        "options_json": json.dumps([
            "Dispense Augmentin as prescribed since Clavulanate neutralizes aminopenicillin allergenicity.",
            "Contact the prescriber to recommend switching to a non-beta-lactam antibiotic (e.g. Doxycycline or Levofloxacin) due to high risk of recurrent anaphylaxis.",
            "Reduce the Augmentin dose to 500mg/125mg once daily to lower the allergic threshold.",
            "Override the clinical alert and advise the patient to co-administer an over-the-counter antihistamine."
        ]),
        "correct_option_index": 1,
        "explanation_text": "Augmentin contains Amoxicillin, an aminopenicillin sharing the core beta-lactam ring. In patients with a documented history of severe IgE-mediated penicillin anaphylaxis, all penicillins and aminopenicillins are strictly contraindicated. Non-beta-lactam alternatives such as Doxycycline (100mg PO BID) or a respiratory fluoroquinolone provide safe and effective coverage without cross-reactivity risk.",
        "source_review_id": "REV-1003",
        "published_by": "USR-CHIEF-001",
        "created_at": "2026-08-26T10:00:00Z"
    },
    {
        "case_id": "EDU-102",
        "title": "Dual Systemic NSAID Therapy & Acute Gastrointestinal Bleeding Risk",
        "clinical_category": "DUPLICATION",
        "difficulty": "BEGINNER",
        "scenario_text": "A 68-year-old male with chronic osteoarthritis presents a new outpatient prescription for Naproxen 500mg PO BID while hospital records confirm an active concurrent inpatient order for Ibuprofen 800mg PO TID for acute post-operative shoulder pain.",
        "deidentified_prescription_json": json.dumps([
            {
                "medication": "Ibuprofen",
                "strength": "800mg",
                "dosage": "1 tablet",
                "frequency": "Three times daily",
                "route": "Oral",
                "duration": "7 days"
            },
            {
                "medication": "Naproxen",
                "strength": "500mg",
                "dosage": "1 tablet",
                "frequency": "Twice daily",
                "route": "Oral",
                "duration": "14 days"
            }
        ]),
        "key_safety_challenge": "Preventing therapeutic duplication of systemic COX inhibitors, mucosal ulceration, and renal vasoconstriction.",
        "multiple_choice_question": "What is the primary pharmacological consequence of concurrent systemic Ibuprofen and Naproxen therapy?",
        "options_json": json.dumps([
            "Competitive enzyme inhibition leading to subtherapeutic analgesia for both drugs.",
            "Severe additive risk of gastrointestinal mucosal bleeding, ulceration, and acute renal impairment without additive analgesic benefit.",
            "Accelerated hepatic glucuronidation resulting in rapid drug clearance.",
            "Direct hypertensive crisis mediated by peripheral beta-2 adrenergic stimulation."
        ]),
        "correct_option_index": 1,
        "explanation_text": "Concurrent administration of two systemic non-steroidal anti-inflammatory drugs (NSAIDs) provides no additive pain relief due to receptor saturation (ceiling effect) while exponentially increasing the risk of mucosal ulceration, acute upper gastrointestinal bleeding, platelet dysfunction, and pre-renal azotemia.",
        "source_review_id": "REV-1004",
        "published_by": "USR-CHIEF-001",
        "created_at": "2026-08-26T11:00:00Z"
    },
    {
        "case_id": "EDU-103",
        "title": "Cardiovascular Indication Verification in Isolated Diabetes Mellitus",
        "clinical_category": "INDICATION",
        "difficulty": "INTERMEDIATE",
        "scenario_text": "A 45-year-old patient diagnosed solely with Type 2 Diabetes Mellitus without documented hypertension, microalbuminuria, or heart failure is prescribed Lisinopril 20mg PO daily.",
        "deidentified_prescription_json": json.dumps([
            {
                "medication": "Lisinopril",
                "strength": "20mg",
                "dosage": "1 tablet",
                "frequency": "Once daily",
                "route": "Oral",
                "duration": "30 days"
            }
        ]),
        "key_safety_challenge": "Differentiating guideline-indicated diabetic nephropathy protection from unverified off-label prescribing in normotensive patients.",
        "multiple_choice_question": "When verifying Lisinopril for a patient diagnosed with Diabetes, what clinical documentation is required to validate therapeutic indication?",
        "options_json": json.dumps([
            "Documented co-existing Hypertension or persistent microalbuminuria (urine albumin-to-creatinine ratio >= 30 mg/g).",
            "Fasting blood glucose strictly under 95 mg/dL.",
            "Concurrent initiation of daily subcutaneous insulin.",
            "Patient confirmation that Lisinopril is administered with a high-potassium breakfast."
        ]),
        "correct_option_index": 0,
        "explanation_text": "According to ADA and KDIGO clinical guidelines, ACE inhibitors like Lisinopril are indicated in diabetic patients specifically for the management of hypertension or for renal protection in patients with documented persistent albuminuria (UACR >= 30 mg/g). In normotensive diabetic patients with normal albumin excretion, ACE inhibitor therapy is not recommended.",
        "source_review_id": "REV-1002",
        "published_by": "USR-CHIEF-001",
        "created_at": "2026-08-26T12:00:00Z"
    },
    {
        "case_id": "EDU-104",
        "title": "Inventory Shortage Mitigation via Strength Equivalency Substitution",
        "clinical_category": "DOSAGE",
        "difficulty": "ADVANCED",
        "scenario_text": "A prescription order is received for Metformin HCl 1000mg PO BID for a newly stabilized diabetic patient. Hospital pharmacy stock surveillance indicates that Metformin 1000mg tablets are completely OUT OF STOCK, whereas Metformin 500mg tablets have over 500 tablets available on hand.",
        "deidentified_prescription_json": json.dumps([
            {
                "medication": "Metformin HCl",
                "strength": "1000mg",
                "dosage": "1 tablet",
                "frequency": "Twice daily",
                "route": "Oral",
                "duration": "30 days"
            }
        ]),
        "key_safety_challenge": "Resolving acute inventory shortages safely through therapeutic strength equivalency and accurate patient counseling.",
        "multiple_choice_question": "What is the most appropriate operational and clinical action for the dispensing pharmacist?",
        "options_json": json.dumps([
            "Refuse dispensing and instruct the patient to delay therapy until 1000mg stock is replenished.",
            "Substitute with Metformin 500mg tablets (take 2 tablets BID), update the pharmacy order record with the strength modification, and counsel the patient on pill count.",
            "Unilaterally switch the patient to Glipizide 10mg without prescriber consultation.",
            "Dispense 1 Metformin 500mg tablet BID to conserve remaining hospital supply."
        ]),
        "correct_option_index": 1,
        "explanation_text": "Substituting two 500mg tablets for each 1000mg dose achieves the exact target therapeutic dose (1000mg BID) without delaying patient therapy. Documenting the modification in the electronic pharmacy system and counseling the patient ensures adherence and prevents medication underdosing.",
        "source_review_id": "REV-1005",
        "published_by": "USR-CHIEF-001",
        "created_at": "2026-08-26T13:00:00Z"
    }
]



def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns a connection to the SQLite database with row factory configured."""
    target_path = db_path or os.getenv("PHARMACYGUARD_DB_PATH", DEFAULT_DB_PATH)
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path, timeout=60.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn





def initialize_database(db_path: Optional[str] = None, force_reseed: bool = False) -> None:
    """Creates SQLite tables and seeds them with synthetic test records."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            last_login_at TEXT
        );
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            sex TEXT NOT NULL,
            allergies TEXT
        );

        CREATE TABLE IF NOT EXISTS diagnoses (
            diagnosis_id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            diagnosis TEXT NOT NULL,
            diagnosis_date TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
        );

        CREATE TABLE IF NOT EXISTS medications (
            medication_id TEXT PRIMARY KEY,
            generic_name TEXT NOT NULL,
            brand_name TEXT NOT NULL,
            therapeutic_class TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            medication TEXT NOT NULL,
            strength TEXT NOT NULL,
            dosage TEXT NOT NULL,
            frequency TEXT NOT NULL,
            route TEXT NOT NULL,
            duration TEXT NOT NULL,
            prescribing_doctor TEXT NOT NULL,
            prescription_date TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
        );

        CREATE TABLE IF NOT EXISTS medication_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_a TEXT NOT NULL,
            medication_b TEXT NOT NULL,
            severity TEXT NOT NULL,
            mechanism TEXT NOT NULL,
            description TEXT NOT NULL,
            recommendation TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS medication_reference (
            medication_id TEXT PRIMARY KEY,
            generic_name TEXT NOT NULL,
            brand_names TEXT NOT NULL,
            therapeutic_class TEXT NOT NULL,
            standard_indications TEXT NOT NULL,
            min_single_dose_mg REAL NOT NULL,
            max_single_dose_mg REAL NOT NULL,
            max_daily_dose_mg REAL NOT NULL,
            common_routes TEXT NOT NULL,
            dosage_notes TEXT
        );

        CREATE TABLE IF NOT EXISTS allergy_cross_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            allergen_group TEXT NOT NULL,
            medication_pattern TEXT NOT NULL,
            reaction_risk TEXT NOT NULL,
            explanation TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS diagnosis_indications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            diagnosis_keyword TEXT NOT NULL,
            approved_drug_classes TEXT NOT NULL,
            approved_generic_drugs TEXT NOT NULL,
            clinical_rationale TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS inventory (
            inventory_id TEXT PRIMARY KEY,
            medication TEXT NOT NULL,
            generic_name TEXT NOT NULL,
            strength TEXT NOT NULL,
            dosage_form TEXT NOT NULL,
            quantity_on_hand INTEGER NOT NULL,
            reorder_level INTEGER NOT NULL,
            unit TEXT NOT NULL,
            last_updated TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pharmacist_reviews (
            review_id TEXT PRIMARY KEY,
            prescription_id TEXT NOT NULL,
            agent_review_status TEXT NOT NULL,
            pharmacist_decision TEXT NOT NULL,
            pharmacist_notes TEXT,
            reviewed_by TEXT,
            created_at TEXT NOT NULL,
            reviewed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS review_findings (
            finding_id TEXT PRIMARY KEY,
            review_id TEXT NOT NULL,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            evidence_source TEXT NOT NULL,
            evidence_data TEXT NOT NULL,
            requires_action INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (review_id) REFERENCES pharmacist_reviews (review_id)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            audit_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            actor_type TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            prescription_id TEXT NOT NULL,
            review_id TEXT,
            event_data TEXT,
            timestamp TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prescriber_communications (
            communication_id TEXT PRIMARY KEY,
            prescription_id TEXT NOT NULL,
            review_id TEXT,
            sender_id TEXT NOT NULL,
            recipient_doctor TEXT NOT NULL,
            report_type TEXT NOT NULL,
            subject TEXT NOT NULL,
            message_body TEXT NOT NULL,
            ai_findings_included TEXT,
            suggested_modifications TEXT,
            status TEXT NOT NULL DEFAULT 'SENT',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS escalation_resolutions (
            resolution_id TEXT PRIMARY KEY,
            review_id TEXT NOT NULL,
            prescription_id TEXT NOT NULL,
            chief_id TEXT NOT NULL,
            chief_decision TEXT NOT NULL,
            chief_notes TEXT NOT NULL,
            action_required TEXT,
            resolved_at TEXT NOT NULL,
            FOREIGN KEY (review_id) REFERENCES pharmacist_reviews (review_id)
        );

        CREATE TABLE IF NOT EXISTS educational_cases (
            case_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            clinical_category TEXT NOT NULL,
            difficulty TEXT NOT NULL DEFAULT 'INTERMEDIATE',
            scenario_text TEXT NOT NULL,
            deidentified_prescription_json TEXT NOT NULL,
            key_safety_challenge TEXT NOT NULL,
            multiple_choice_question TEXT NOT NULL,
            options_json TEXT NOT NULL,
            correct_option_index INTEGER NOT NULL,
            explanation_text TEXT NOT NULL,
            source_review_id TEXT,
            published_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS student_case_submissions (
            submission_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            selected_option_index INTEGER NOT NULL,
            is_correct INTEGER NOT NULL,
            student_notes TEXT,
            submitted_at TEXT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES educational_cases (case_id)
        );

        CREATE TABLE IF NOT EXISTS inventory_transactions (
            transaction_id TEXT PRIMARY KEY,
            inventory_id TEXT NOT NULL,
            prescription_id TEXT,
            transaction_type TEXT NOT NULL,
            quantity_change INTEGER NOT NULL,
            quantity_after INTEGER NOT NULL,
            actor_id TEXT NOT NULL,
            notes TEXT,
            timestamp TEXT NOT NULL
        );
    """)


    cursor.execute("SELECT COUNT(*) as count FROM patients")
    count = cursor.fetchone()["count"]

    if count == 0 or force_reseed:
        if force_reseed:
            cursor.execute("DELETE FROM student_case_submissions")
            cursor.execute("DELETE FROM educational_cases")
            cursor.execute("DELETE FROM escalation_resolutions")
            cursor.execute("DELETE FROM inventory_transactions")
            cursor.execute("DELETE FROM prescriber_communications")
            cursor.execute("DELETE FROM audit_log")
            cursor.execute("DELETE FROM review_findings")
            cursor.execute("DELETE FROM pharmacist_reviews")
            cursor.execute("DELETE FROM inventory")
            cursor.execute("DELETE FROM prescriptions")
            cursor.execute("DELETE FROM medications")
            cursor.execute("DELETE FROM diagnoses")
            cursor.execute("DELETE FROM patients")
            cursor.execute("DELETE FROM medication_interactions")
            cursor.execute("DELETE FROM medication_reference")
            cursor.execute("DELETE FROM allergy_cross_reactions")
            cursor.execute("DELETE FROM diagnosis_indications")


        for p in SEED_PATIENTS:
            cursor.execute(
                """
                INSERT OR REPLACE INTO patients (patient_id, name, age, sex, allergies)
                VALUES (?, ?, ?, ?, ?)
                """,
                (p["patient_id"], p["name"], p["age"], p["sex"], p["allergies"])
            )

        for d in SEED_DIAGNOSES:
            cursor.execute(
                """
                INSERT OR REPLACE INTO diagnoses (diagnosis_id, patient_id, diagnosis, diagnosis_date)
                VALUES (?, ?, ?, ?)
                """,
                (d["diagnosis_id"], d["patient_id"], d["diagnosis"], d["diagnosis_date"])
            )

        for m in SEED_MEDICATIONS:
            cursor.execute(
                """
                INSERT OR REPLACE INTO medications (medication_id, generic_name, brand_name, therapeutic_class)
                VALUES (?, ?, ?, ?)
                """,
                (m["medication_id"], m["generic_name"], m["brand_name"], m["therapeutic_class"])
            )

        for rx in SEED_PRESCRIPTIONS:
            cursor.execute(
                """
                INSERT INTO prescriptions (
                    prescription_id, patient_id, medication, strength, dosage,
                    frequency, route, duration, prescribing_doctor, prescription_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rx["prescription_id"], rx["patient_id"], rx["medication"], rx["strength"],
                    rx["dosage"], rx["frequency"], rx["route"], rx["duration"],
                    rx["prescribing_doctor"], rx["prescription_date"]
                )
            )

        for inter in SEED_MEDICATION_INTERACTIONS:
            cursor.execute(
                """
                INSERT INTO medication_interactions (medication_a, medication_b, severity, mechanism, description, recommendation)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (inter["medication_a"], inter["medication_b"], inter["severity"], inter["mechanism"], inter["description"], inter["recommendation"])
            )

        for ref in SEED_MEDICATION_REFERENCE:
            cursor.execute(
                """
                INSERT OR REPLACE INTO medication_reference (
                    medication_id, generic_name, brand_names, therapeutic_class, standard_indications,
                    min_single_dose_mg, max_single_dose_mg, max_daily_dose_mg, common_routes, dosage_notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ref["medication_id"], ref["generic_name"], ref["brand_names"], ref["therapeutic_class"],
                    ref["standard_indications"], ref["min_single_dose_mg"], ref["max_single_dose_mg"],
                    ref["max_daily_dose_mg"], ref["common_routes"], ref["dosage_notes"]
                )
            )

        for ac in SEED_ALLERGY_CROSS_REACTIONS:
            cursor.execute(
                """
                INSERT INTO allergy_cross_reactions (allergen_group, medication_pattern, reaction_risk, explanation)
                VALUES (?, ?, ?, ?)
                """,
                (ac["allergen_group"], ac["medication_pattern"], ac["reaction_risk"], ac["explanation"])
            )

        for di in SEED_DIAGNOSIS_INDICATIONS:
            cursor.execute(
                """
                INSERT INTO diagnosis_indications (diagnosis_keyword, approved_drug_classes, approved_generic_drugs, clinical_rationale)
                VALUES (?, ?, ?, ?)
                """,
                (di["diagnosis_keyword"], di["approved_drug_classes"], di["approved_generic_drugs"], di["clinical_rationale"])
            )

        for inv in SEED_INVENTORY:
            cursor.execute(
                """
                INSERT OR REPLACE INTO inventory (
                    inventory_id, medication, generic_name, strength, dosage_form,
                    quantity_on_hand, reorder_level, unit, last_updated
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inv["inventory_id"], inv["medication"], inv["generic_name"], inv["strength"],
                    inv["dosage_form"], inv["quantity_on_hand"], inv["reorder_level"],
                    inv["unit"], inv["last_updated"]
                )
            )

        # Seed development users with PBKDF2 hashed passwords
        from backend.auth.security import hash_password
        for u in SEED_USERS:
            p_hash = hash_password(u["password_plain"])
            cursor.execute(
                """
                INSERT OR REPLACE INTO users (
                    user_id, full_name, email, password_hash, role, active, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    u["user_id"], u["full_name"], u["email"].lower(), p_hash,
                    u["role"], u["active"], u["created_at"]
                )
            )

        # Seed initial educational cases if empty
        cursor.execute("SELECT COUNT(*) as edu_count FROM educational_cases")
        edu_count = cursor.fetchone()["edu_count"]
        if edu_count == 0:
            for ec in SEED_EDUCATIONAL_CASES:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO educational_cases (
                        case_id, title, clinical_category, difficulty, scenario_text,
                        deidentified_prescription_json, key_safety_challenge, multiple_choice_question,
                        options_json, correct_option_index, explanation_text, source_review_id,
                        published_by, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ec["case_id"], ec["title"], ec["clinical_category"], ec["difficulty"],
                        ec["scenario_text"], ec["deidentified_prescription_json"], ec["key_safety_challenge"],
                        ec["multiple_choice_question"], ec["options_json"], ec["correct_option_index"],
                        ec["explanation_text"], ec["source_review_id"], ec["published_by"], ec["created_at"]
                    )
                )

        conn.commit()

    # Ensure users table is populated even if patients table was already populated
    cursor.execute("SELECT COUNT(*) as u_count FROM users")
    u_count = cursor.fetchone()["u_count"]
    if u_count == 0:
        from backend.auth.security import hash_password
        for u in SEED_USERS:
            p_hash = hash_password(u["password_plain"])
            cursor.execute(
                """
                INSERT OR REPLACE INTO users (
                    user_id, full_name, email, password_hash, role, active, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    u["user_id"], u["full_name"], u["email"].lower(), p_hash,
                    u["role"], u["active"], u["created_at"]
                )
            )
        conn.commit()

    # Ensure educational_cases table is populated
    cursor.execute("SELECT COUNT(*) as ec_count FROM educational_cases")
    ec_count = cursor.fetchone()["ec_count"]
    if ec_count == 0:
        for ec in SEED_EDUCATIONAL_CASES:
            cursor.execute(
                """
                INSERT OR REPLACE INTO educational_cases (
                    case_id, title, clinical_category, difficulty, scenario_text,
                    deidentified_prescription_json, key_safety_challenge, multiple_choice_question,
                    options_json, correct_option_index, explanation_text, source_review_id,
                    published_by, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ec["case_id"], ec["title"], ec["clinical_category"], ec["difficulty"],
                    ec["scenario_text"], ec["deidentified_prescription_json"], ec["key_safety_challenge"],
                    ec["multiple_choice_question"], ec["options_json"], ec["correct_option_index"],
                    ec["explanation_text"], ec["source_review_id"], ec["published_by"], ec["created_at"]
                )
            )
        conn.commit()

    conn.close()



# ==============================================================================
# User Authentication & RBAC Database Helpers
# ==============================================================================

def get_user_by_email(email: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves an active user record by email."""
    if not email or not email.strip():
        return None

    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id, full_name, email, password_hash, role, active, created_at, last_login_at
        FROM users
        WHERE LOWER(email) = LOWER(?)
        """,
        (email.strip(),)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a user record by user_id."""
    if not user_id or not user_id.strip():
        return None

    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id, full_name, email, password_hash, role, active, created_at, last_login_at
        FROM users
        WHERE user_id = ?
        """,
        (user_id.strip(),)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_last_login(user_id: str, db_path: Optional[str] = None) -> None:
    """Updates the last_login_at timestamp for a user."""
    if not user_id:
        return

    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    ts = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        UPDATE users
        SET last_login_at = ?
        WHERE user_id = ?
        """,
        (ts, user_id.strip())
    )
    conn.commit()
    conn.close()


def create_user(
    full_name: str,
    email: str,
    password_hash: str,
    role: str,
    user_id: Optional[str] = None,
    active: int = 1,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a new user record in the database."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    uid = user_id or f"USR-{uuid.uuid4().hex[:8].upper()}"
    ts = datetime.now(timezone.utc).isoformat()

    cursor.execute(
        """
        INSERT INTO users (user_id, full_name, email, password_hash, role, active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (uid, full_name.strip(), email.strip().lower(), password_hash, role, active, ts)
    )
    conn.commit()
    conn.close()

    return get_user_by_id(uid, db_path=db_path)  # type: ignore



def fetch_prescription_details(prescription_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves full structured prescription details, patient demographics, allergies,
    and associated diagnoses for a given prescription ID.
    """
    clean_id = prescription_id.strip()
    if not clean_id:
        return None

    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 
            rx.id,
            rx.prescription_id,
            rx.patient_id,
            rx.medication,
            rx.strength,
            rx.dosage,
            rx.frequency,
            rx.route,
            rx.duration,
            rx.prescribing_doctor,
            rx.prescription_date,
            p.name AS patient_name,
            p.age AS patient_age,
            p.sex AS patient_sex,
            p.allergies AS patient_allergies
        FROM prescriptions rx
        JOIN patients p ON rx.patient_id = p.patient_id
        WHERE UPPER(rx.prescription_id) = UPPER(?)
        ORDER BY rx.id ASC
        """,
        (clean_id,)
    )
    rows = cursor.fetchall()

    if not rows:
        conn.close()
        return None

    first_row = rows[0]
    patient_id = first_row["patient_id"]

    cursor.execute(
        """
        SELECT diagnosis_id, diagnosis, diagnosis_date
        FROM diagnoses
        WHERE patient_id = ?
        ORDER BY diagnosis_date DESC
        """,
        (patient_id,)
    )
    diag_rows = cursor.fetchall()
    diagnoses = [
        {
            "diagnosis_id": d["diagnosis_id"],
            "diagnosis": d["diagnosis"],
            "diagnosis_date": d["diagnosis_date"]
        }
        for d in diag_rows
    ]

    medications = [
        {
            "medication": r["medication"],
            "strength": r["strength"],
            "dosage": r["dosage"],
            "frequency": r["frequency"],
            "route": r["route"],
            "duration": r["duration"]
        }
        for r in rows
    ]

    conn.close()

    return {
        "prescription_id": first_row["prescription_id"],
        "prescription_date": first_row["prescription_date"],
        "prescribing_doctor": first_row["prescribing_doctor"],
        "patient": {
            "patient_id": first_row["patient_id"],
            "name": first_row["patient_name"],
            "age": first_row["patient_age"],
            "sex": first_row["patient_sex"],
            "allergies": first_row["patient_allergies"]
        },
        "diagnoses": diagnoses,
        "medications": medications
    }


def query_drug_interactions(medications: List[str], db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Queries local simulated drug interactions database for pairwise drug interactions
    between the provided list of prescribed medications.
    """
    if len(medications) < 2:
        return []

    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT medication_a, medication_b, severity, mechanism, description, recommendation FROM medication_interactions")
    all_interactions = cursor.fetchall()
    conn.close()

    detected: List[Dict[str, Any]] = []
    normalized_meds = [m.lower() for m in medications]

    for inter in all_interactions:
        med_a = inter["medication_a"].lower()
        med_b = inter["medication_b"].lower()

        has_a = any(med_a in m for m in normalized_meds)
        has_b = any(med_b in m for m in normalized_meds)

        if has_a and has_b:
            detected.append({
                "medication_a": inter["medication_a"],
                "medication_b": inter["medication_b"],
                "severity": inter["severity"],
                "mechanism": inter["mechanism"],
                "description": inter["description"],
                "recommendation": inter["recommendation"]
            })

    return detected


def query_medication_reference(medication_name: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Queries local simulated medication reference table for dosing guidelines and indications.
    """
    if not medication_name or not medication_name.strip():
        return None

    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    clean_name = medication_name.strip().lower()
    cursor.execute(
        """
        SELECT 
            medication_id, generic_name, brand_names, therapeutic_class,
            standard_indications, min_single_dose_mg, max_single_dose_mg,
            max_daily_dose_mg, common_routes, dosage_notes
        FROM medication_reference
        """
    )
    rows = cursor.fetchall()
    conn.close()

    for r in rows:
        gen = r["generic_name"].lower()
        brands = r["brand_names"].lower()
        if gen in clean_name or clean_name in gen or any(b.strip() in clean_name for b in brands.split(",")):
            return dict(r)

    return None


def query_allergy_cross_reactions(allergen_str: str, medication_name: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Checks if a prescribed medication conflicts with documented patient allergies
    based on local simulated allergy cross-reactivity records.
    """
    if not allergen_str or not medication_name:
        return []

    clean_allergen = allergen_str.strip().lower()
    clean_med = medication_name.strip().lower()

    if "nkda" in clean_allergen or "no known" in clean_allergen or "none" in clean_allergen:
        return []

    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT allergen_group, medication_pattern, reaction_risk, explanation FROM allergy_cross_reactions")
    rows = cursor.fetchall()
    conn.close()

    conflicts: List[Dict[str, Any]] = []

    for r in rows:
        allergen_group = r["allergen_group"].lower()
        patterns = [p.strip().lower() for p in r["medication_pattern"].split(",")]

        if allergen_group in clean_allergen or any(part in clean_allergen for part in allergen_group.split("/")):
            for p in patterns:
                if p and p in clean_med:
                    conflicts.append({
                        "allergen_group": r["allergen_group"],
                        "documented_allergy": allergen_str,
                        "conflicting_medication": medication_name,
                        "reaction_risk": r["reaction_risk"],
                        "explanation": r["explanation"]
                    })
                    break

    return conflicts


def query_diagnosis_medication_match(diagnosis: str, medication_name: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Compares a diagnosis with a prescribed medication against local clinical indications data.
    """
    if not diagnosis or not medication_name:
        return {
            "relevant": False,
            "category": "INSUFFICIENT_INPUT",
            "evidence": "Diagnosis or medication name was missing or empty.",
            "requires_pharmacist_review": True
        }

    clean_diag = diagnosis.lower()
    clean_med = medication_name.lower()

    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT diagnosis_keyword, approved_drug_classes, approved_generic_drugs, clinical_rationale FROM diagnosis_indications")
    rows = cursor.fetchall()
    conn.close()

    matched_indication = None
    for r in rows:
        if r["diagnosis_keyword"] in clean_diag:
            matched_indication = r
            break

    if not matched_indication:
        return {
            "relevant": False,
            "category": "UNRECOGNIZED_DIAGNOSIS",
            "evidence": f"Diagnosis '{diagnosis}' does not match standard reference indications in the simulated hospital database.",
            "requires_pharmacist_review": True
        }

    approved_drugs = [d.strip().lower() for d in matched_indication["approved_generic_drugs"].split(",")]
    is_drug_matched = any(d in clean_med for d in approved_drugs)

    if is_drug_matched:
        return {
            "relevant": True,
            "category": "MATCH",
            "evidence": f"Medication '{medication_name}' is consistent with reference guideline therapy for '{diagnosis}'. {matched_indication['clinical_rationale']}",
            "requires_pharmacist_review": True
        }
    else:
        return {
            "relevant": False,
            "category": "POTENTIAL_MISMATCH",
            "evidence": f"Medication '{medication_name}' is not documented as standard first-line therapy for diagnosis '{diagnosis}'. Approved classes for this diagnosis include: {matched_indication['approved_drug_classes']}. {matched_indication['clinical_rationale']}",
            "requires_pharmacist_review": True
        }


# --- Pharmacy Inventory Queries ---

def _clean_str(text: Optional[str]) -> str:
    """Helper to clean and normalize strings."""
    return re.sub(r"[^\w\s/]", "", (text or "").lower()).strip()


def query_inventory_check(
    medication_name: str,
    strength: Optional[str] = None,
    dosage_form: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Checks stock availability for a prescribed medication against the simulated SQLite inventory.
    """
    if not medication_name or not medication_name.strip():
        return {
            "requested_medication": medication_name,
            "requested_strength": strength or "Unspecified",
            "requested_dosage_form": dosage_form or "Unspecified",
            "availability_status": "NOT FOUND",
            "quantity_available": 0,
            "reorder_level": 0,
            "unit": "units",
            "stock_status": "Item name is empty or unspecified.",
            "requires_pharmacist_attention": True,
            "last_updated": "N/A"
        }

    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 
            inventory_id, medication, generic_name, strength, dosage_form,
            quantity_on_hand, reorder_level, unit, last_updated
        FROM inventory
        """
    )
    all_inventory = [dict(r) for r in cursor.fetchall()]
    conn.close()

    clean_med = _clean_str(medication_name)
    clean_strength = _clean_str(strength)
    if not clean_strength:
        mg_match = re.search(r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|g)(?:\s*/\s*\d+(?:\.\d+)?\s*mg)?)\b", medication_name, re.IGNORECASE)
        if mg_match:
            clean_strength = _clean_str(mg_match.group(1))

    matching_items = []
    for item in all_inventory:
        item_med = _clean_str(item["medication"])
        item_gen = _clean_str(item["generic_name"])

        if (clean_med in item_med or item_med in clean_med or
            clean_med in item_gen or item_gen in clean_med or
            any(part in clean_med for part in item_gen.split("/")) or
            any(part in clean_med for part in item_med.split())):
            matching_items.append(item)

    if not matching_items:
        return {
            "requested_medication": medication_name,
            "requested_strength": strength or "Unspecified",
            "requested_dosage_form": dosage_form or "Unspecified",
            "availability_status": "NOT FOUND",
            "quantity_available": 0,
            "reorder_level": 0,
            "unit": "units",
            "stock_status": f"Medication '{medication_name}' is not currently stocked in the hospital pharmacy catalog.",
            "requires_pharmacist_attention": True,
            "last_updated": "N/A"
        }

    exact_match = None
    if clean_strength:
        for item in matching_items:
            item_strength = _clean_str(item["strength"])
            if clean_strength == item_strength or clean_strength in item_strength or item_strength in clean_strength:
                exact_match = item
                break
    else:
        exact_match = matching_items[0]

    if exact_match:
        qty = exact_match["quantity_on_hand"]
        reorder = exact_match["reorder_level"]
        unit = exact_match["unit"]
        last_updated = exact_match["last_updated"]

        if qty == 0:
            status = "OUT OF STOCK"
            stock_desc = f"OUT OF STOCK: 0 {unit} available (reorder threshold: {reorder} {unit})."
            attention = True
        elif qty <= reorder:
            status = "LOW STOCK"
            stock_desc = f"LOW STOCK: {qty} {unit} remaining on hand (reorder threshold: {reorder} {unit})."
            attention = True
        else:
            status = "AVAILABLE"
            stock_desc = f"AVAILABLE: {qty} {unit} on hand (sufficient stock above reorder level {reorder})."
            attention = False

        alt_strengths = []
        if qty == 0:
            for item in matching_items:
                if item["inventory_id"] != exact_match["inventory_id"] and item["quantity_on_hand"] > 0:
                    alt_strengths.append(f"{item['strength']} ({item['quantity_on_hand']} {item['unit']} available)")

        if alt_strengths:
            stock_desc += f" Note: Alternative strength(s) in stock: {', '.join(alt_strengths)}. (Pharmacist decision required; do not autonomously substitute)."

        return {
            "requested_medication": medication_name,
            "requested_strength": exact_match["strength"],
            "requested_dosage_form": exact_match["dosage_form"],
            "availability_status": status,
            "quantity_available": qty,
            "reorder_level": reorder,
            "unit": unit,
            "stock_status": stock_desc,
            "requires_pharmacist_attention": attention,
            "last_updated": last_updated
        }

    in_stock_alts = [item for item in matching_items if item["quantity_on_hand"] > 0]
    if in_stock_alts:
        alt_details = [f"{item['strength']} {item['dosage_form']} ({item['quantity_on_hand']} {item['unit']})" for item in in_stock_alts]
        return {
            "requested_medication": medication_name,
            "requested_strength": strength or "Unspecified",
            "requested_dosage_form": dosage_form or "Unspecified",
            "availability_status": "STRENGTH UNAVAILABLE",
            "quantity_available": 0,
            "reorder_level": in_stock_alts[0]["reorder_level"],
            "unit": in_stock_alts[0]["unit"],
            "stock_status": f"Exact prescribed strength ({strength or 'requested'}) is not stocked. Available alternative strength(s): {', '.join(alt_details)}. Requires prescriber/pharmacist consultation for any dosage adjustments.",
            "requires_pharmacist_attention": True,
            "last_updated": in_stock_alts[0]["last_updated"]
        }
    else:
        return {
            "requested_medication": medication_name,
            "requested_strength": strength or "Unspecified",
            "requested_dosage_form": dosage_form or "Unspecified",
            "availability_status": "OUT OF STOCK",
            "quantity_available": 0,
            "reorder_level": matching_items[0]["reorder_level"],
            "unit": matching_items[0]["unit"],
            "stock_status": f"All strengths of '{medication_name}' are currently OUT OF STOCK in the hospital pharmacy.",
            "requires_pharmacist_attention": True,
            "last_updated": matching_items[0]["last_updated"]
        }


def query_low_stock_inventory(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all inventory items at or below reorder level."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 
            inventory_id, medication, generic_name, strength, dosage_form,
            quantity_on_hand, reorder_level, unit, last_updated
        FROM inventory
        WHERE quantity_on_hand <= reorder_level
        ORDER BY quantity_on_hand ASC, reorder_level DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        qty = r["quantity_on_hand"]
        reorder = r["reorder_level"]
        status = "OUT OF STOCK" if qty == 0 else "LOW STOCK"
        results.append({
            "inventory_id": r["inventory_id"],
            "medication": r["medication"],
            "generic_name": r["generic_name"],
            "strength": r["strength"],
            "dosage_form": r["dosage_form"],
            "quantity_on_hand": qty,
            "reorder_level": reorder,
            "unit": r["unit"],
            "deficit_to_reorder": max(0, reorder - qty),
            "stock_status": status,
            "last_updated": r["last_updated"]
        })

    return results


def query_inventory_overview_summary(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Computes summary metrics across the complete hospital pharmacy inventory."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM inventory")
    total_medications = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS out_count FROM inventory WHERE quantity_on_hand = 0")
    out_of_stock = cursor.fetchone()["out_count"]

    cursor.execute("SELECT COUNT(*) AS low_count FROM inventory WHERE quantity_on_hand > 0 AND quantity_on_hand <= reorder_level")
    low_stock = cursor.fetchone()["low_count"]

    cursor.execute("SELECT COUNT(*) AS avail_count FROM inventory WHERE quantity_on_hand > reorder_level")
    available = cursor.fetchone()["avail_count"]

    below_reorder = out_of_stock + low_stock
    health_pct = round((available / total_medications * 100), 1) if total_medications > 0 else 0.0

    conn.close()

    return {
        "total_tracked_medications": total_medications,
        "number_available": available,
        "number_low_stock": low_stock,
        "number_out_of_stock": out_of_stock,
        "number_below_reorder_level": below_reorder,
        "stock_health_percentage": f"{health_pct}%",
        "last_inventory_sync": "2026-08-25 08:00:00"
    }


# ==============================================================================
# Pharmacist Review, Findings, and Audit Log Persistence Helpers
# ==============================================================================

def insert_pharmacist_review(
    review_id: str,
    prescription_id: str,
    agent_review_status: str,
    pharmacist_decision: str = "PENDING",
    pharmacist_notes: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    created_at: Optional[str] = None,
    reviewed_at: Optional[str] = None,
    db_path: Optional[str] = None
) -> None:
    """Inserts a new pharmacist review record."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    ts = created_at or datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        INSERT INTO pharmacist_reviews (
            review_id, prescription_id, agent_review_status, pharmacist_decision,
            pharmacist_notes, reviewed_by, created_at, reviewed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (review_id, prescription_id, agent_review_status, pharmacist_decision, pharmacist_notes, reviewed_by, ts, reviewed_at)
    )
    conn.commit()
    conn.close()


def insert_review_finding(
    finding_id: str,
    review_id: str,
    category: str,
    severity: str,
    title: str,
    description: str,
    evidence_source: str,
    evidence_data: str,
    requires_action: bool = True,
    created_at: Optional[str] = None,
    db_path: Optional[str] = None
) -> None:
    """Inserts a structured finding record linked to a review."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    ts = created_at or datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        INSERT INTO review_findings (
            finding_id, review_id, category, severity, title,
            description, evidence_source, evidence_data, requires_action, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            finding_id, review_id, category, severity, title,
            description, evidence_source, evidence_data, 1 if requires_action else 0, ts
        )
    )
    conn.commit()
    conn.close()


def insert_audit_event(
    event_type: str,
    actor_type: str,
    actor_id: str,
    prescription_id: str,
    review_id: Optional[str] = None,
    event_data: Optional[str] = None,
    timestamp: Optional[str] = None,
    audit_id: Optional[str] = None,
    db_path: Optional[str] = None
) -> str:
    """Inserts an immutable audit event for human-in-the-loop tracking."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    aid = audit_id or f"AUD-{uuid.uuid4().hex[:8].upper()}"
    ts = timestamp or datetime.now(timezone.utc).isoformat()

    data_str = event_data
    if isinstance(event_data, (dict, list)):
        data_str = json.dumps(event_data)

    cursor.execute(
        """
        INSERT INTO audit_log (
            audit_id, event_type, actor_type, actor_id,
            prescription_id, review_id, event_data, timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (aid, event_type, actor_type, actor_id, prescription_id, review_id, data_str, ts)
    )

    conn.commit()
    conn.close()
    return aid


def update_pharmacist_decision(
    review_id: str,
    decision: str,
    pharmacist_id: str,
    notes: Optional[str] = None,
    reviewed_at: Optional[str] = None,
    db_path: Optional[str] = None
) -> bool:
    """Updates the pharmacist decision on a review record."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    ts = reviewed_at or datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        UPDATE pharmacist_reviews
        SET pharmacist_decision = ?,
            pharmacist_notes = ?,
            reviewed_by = ?,
            reviewed_at = ?
        WHERE review_id = ?
        """,
        (decision, notes, pharmacist_id, ts, review_id)
    )
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0


def fetch_review_by_id(review_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves full review details including prescription, findings, and audit history."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT review_id, prescription_id, agent_review_status, pharmacist_decision,
               pharmacist_notes, reviewed_by, created_at, reviewed_at
        FROM pharmacist_reviews
        WHERE review_id = ?
        """,
        (review_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    review_data = dict(row)

    # Fetch findings
    cursor.execute(
        """
        SELECT finding_id, review_id, category, severity, title, description,
               evidence_source, evidence_data, requires_action, created_at
        FROM review_findings
        WHERE review_id = ?
        ORDER BY created_at ASC
        """,
        (review_id,)
    )
    findings = [
        {
            "finding_id": f["finding_id"],
            "review_id": f["review_id"],
            "category": f["category"],
            "severity": f["severity"],
            "title": f["title"],
            "description": f["description"],
            "evidence_source": f["evidence_source"],
            "evidence_data": f["evidence_data"],
            "requires_action": bool(f["requires_action"]),
            "created_at": f["created_at"]
        }
        for f in cursor.fetchall()
    ]

    # Fetch audit logs
    cursor.execute(
        """
        SELECT audit_id, event_type, actor_type, actor_id, prescription_id,
               review_id, event_data, timestamp
        FROM audit_log
        WHERE review_id = ?
        ORDER BY timestamp ASC
        """,
        (review_id,)
    )
    audit_logs = [dict(a) for a in cursor.fetchall()]

    # Fetch prescriber communications
    cursor.execute(
        """
        SELECT communication_id, prescription_id, review_id, sender_id, recipient_doctor,
               report_type, subject, message_body, ai_findings_included,
               suggested_modifications, status, created_at
        FROM prescriber_communications
        WHERE review_id = ? OR prescription_id = ?
        ORDER BY created_at ASC
        """,
        (review_id, review_data["prescription_id"])
    )
    comm_rows = cursor.fetchall()
    communications = []
    for c in comm_rows:
        comm_dict = dict(c)
        if comm_dict.get("ai_findings_included"):
            try:
                comm_dict["ai_findings_included"] = json.loads(comm_dict["ai_findings_included"])
            except Exception:
                pass
        if comm_dict.get("suggested_modifications"):
            try:
                comm_dict["suggested_modifications"] = json.loads(comm_dict["suggested_modifications"])
            except Exception:
                pass
        communications.append(comm_dict)

    # Fetch escalation resolutions

    cursor.execute(
        """
        SELECT resolution_id, review_id, prescription_id, chief_id, chief_decision,
               chief_notes, action_required, resolved_at
        FROM escalation_resolutions
        WHERE review_id = ?
        ORDER BY resolved_at ASC
        """,
        (review_id,)
    )
    resolutions = [dict(r) for r in cursor.fetchall()]

    conn.close()

    # Get underlying prescription details
    rx_details = fetch_prescription_details(review_data["prescription_id"], db_path=db_path)

    review_data["findings"] = findings
    review_data["audit_history"] = audit_logs
    review_data["prescriber_communications"] = communications
    review_data["escalation_resolutions"] = resolutions
    review_data["prescription_details"] = rx_details
    return review_data



def fetch_all_reviews(
    decision: Optional[str] = None,
    status: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves all reviews matching optional decision or status filters."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    query = """
        SELECT r.review_id, r.prescription_id, r.agent_review_status, r.pharmacist_decision,
               r.pharmacist_notes, r.reviewed_by, r.created_at, r.reviewed_at,
               p.name AS patient_name,
               (SELECT COUNT(*) FROM review_findings f WHERE f.review_id = r.review_id) AS findings_count
        FROM pharmacist_reviews r
        JOIN prescriptions rx ON r.prescription_id = rx.prescription_id
        JOIN patients p ON rx.patient_id = p.patient_id
    """
    conditions = []
    params = []

    if decision:
        conditions.append("r.pharmacist_decision = ?")
        params.append(decision.upper())
    if status:
        conditions.append("r.agent_review_status = ?")
        params.append(status.upper())

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " GROUP BY r.review_id ORDER BY r.created_at DESC"

    cursor.execute(query, tuple(params))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ==============================================================================
# Prescriber Communications & Prescription Modification Helpers
# ==============================================================================

def insert_prescriber_communication(
    communication_id: str,
    prescription_id: str,
    review_id: Optional[str],
    sender_id: str,
    recipient_doctor: str,
    report_type: str,
    subject: str,
    message_body: str,
    ai_findings_included: Optional[Any] = None,
    suggested_modifications: Optional[Any] = None,
    created_at: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Persists a clinical consultation / report sent from the pharmacist to the prescribing doctor."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cid = communication_id or f"COM-{uuid.uuid4().hex[:8].upper()}"
    ts = created_at or datetime.now(timezone.utc).isoformat()

    findings_json = json.dumps(ai_findings_included) if ai_findings_included is not None else None
    mods_json = json.dumps(suggested_modifications) if suggested_modifications is not None else None

    cursor.execute(
        """
        INSERT INTO prescriber_communications (
            communication_id, prescription_id, review_id, sender_id,
            recipient_doctor, report_type, subject, message_body,
            ai_findings_included, suggested_modifications, status, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'SENT', ?)
        """,
        (
            cid, prescription_id.strip().upper(), review_id, sender_id,
            recipient_doctor.strip(), report_type, subject.strip(),
            message_body.strip(), findings_json, mods_json, ts
        )
    )
    conn.commit()
    conn.close()

    # Log audit event
    insert_audit_event(
        event_type="PRESCRIBER_CONSULTATION_SENT",
        actor_type="PHARMACIST",
        actor_id=sender_id,
        prescription_id=prescription_id.strip().upper(),
        review_id=review_id,
        event_data=json.dumps({
            "communication_id": cid,
            "report_type": report_type,
            "recipient_doctor": recipient_doctor,
            "subject": subject
        }),
        timestamp=ts,
        db_path=db_path
    )

    return {
        "communication_id": cid,
        "prescription_id": prescription_id.strip().upper(),
        "review_id": review_id,
        "sender_id": sender_id,
        "recipient_doctor": recipient_doctor,
        "report_type": report_type,
        "subject": subject,
        "message_body": message_body,
        "ai_findings_included": ai_findings_included,
        "suggested_modifications": suggested_modifications,
        "status": "SENT",
        "created_at": ts
    }


def fetch_prescriber_communications(
    prescription_id: Optional[str] = None,
    review_id: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves all prescriber communication reports for a prescription or review."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    query = """
        SELECT communication_id, prescription_id, review_id, sender_id,
               recipient_doctor, report_type, subject, message_body,
               ai_findings_included, suggested_modifications, status, created_at
        FROM prescriber_communications
    """
    conditions = []
    params = []
    if prescription_id:
        conditions.append("UPPER(prescription_id) = ?")
        params.append(prescription_id.strip().upper())
    if review_id:
        conditions.append("review_id = ?")
        params.append(review_id.strip())

    if conditions:
        query += " WHERE " + " OR ".join(conditions)

    query += " ORDER BY created_at DESC"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        item = dict(r)
        if item.get("ai_findings_included"):
            try:
                item["ai_findings_included"] = json.loads(item["ai_findings_included"])
            except Exception:
                pass
        if item.get("suggested_modifications"):
            try:
                item["suggested_modifications"] = json.loads(item["suggested_modifications"])
            except Exception:
                pass
        results.append(item)
    return results


def update_prescription_items(
    prescription_id: str,
    medications: List[Dict[str, Any]],
    prescribing_doctor: Optional[str] = None,
    prescription_date: Optional[str] = None,
    editor_user_id: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Updates the medication regimen of an existing doctor's prescription in SQLite.
    Preserves the patient link and replaces old prescribed lines with updated clinical regimen.
    """
    clean_rx_id = prescription_id.strip().upper()
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Verify prescription exists and get patient_id
    cursor.execute("SELECT patient_id, prescribing_doctor, prescription_date FROM prescriptions WHERE UPPER(prescription_id) = ?", (clean_rx_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise ValueError(f"Prescription '{clean_rx_id}' not found.")

    patient_id = existing["patient_id"]
    doc = prescribing_doctor or existing["prescribing_doctor"]
    p_date = prescription_date or existing["prescription_date"]

    # Delete existing medication lines for this prescription
    cursor.execute("DELETE FROM prescriptions WHERE UPPER(prescription_id) = ?", (clean_rx_id,))

    # Insert updated medication lines
    for med in medications:
        cursor.execute(
            """
            INSERT INTO prescriptions (
                prescription_id, patient_id, medication, strength,
                dosage, frequency, route, duration, prescribing_doctor, prescription_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clean_rx_id, patient_id,
                med.get("medication", "").strip(),
                med.get("strength", "").strip(),
                med.get("dosage", "").strip(),
                med.get("frequency", "").strip(),
                med.get("route", "Oral").strip(),
                med.get("duration", "").strip(),
                doc, p_date
            )
        )
    conn.commit()
    conn.close()

    # Log audit event for prescription modification
    if editor_user_id:
        insert_audit_event(
            event_type="PRESCRIPTION_MODIFIED",
            actor_type="PHARMACIST",
            actor_id=editor_user_id,
            prescription_id=clean_rx_id,
            event_data=json.dumps({
                "modified_by": editor_user_id,
                "medications_count": len(medications),
                "medications": medications
            }),
            timestamp=datetime.now(timezone.utc).isoformat(),
            db_path=db_path
        )

    updated = fetch_prescription_details(clean_rx_id, db_path=db_path)
    return updated  # type: ignore


def create_or_update_patient(
    patient_id: Optional[str],
    name: str,
    age: int,
    sex: str,
    allergies: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Creates or updates a patient record."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    pid = patient_id or f"PAT-{uuid.uuid4().hex[:6].upper()}"
    cursor.execute(
        """
        INSERT OR REPLACE INTO patients (patient_id, name, age, sex, allergies)
        VALUES (?, ?, ?, ?, ?)
        """,
        (pid, name.strip(), age, sex.strip(), allergies.strip() if allergies else "NKDA (No known drug allergies)")
    )
    conn.commit()
    conn.close()
    return {"patient_id": pid, "name": name, "age": age, "sex": sex, "allergies": allergies}


def create_patient_diagnosis(
    patient_id: str,
    diagnosis: str,
    diagnosis_date: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Adds a clinical diagnosis for a patient."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    did = f"DX-{uuid.uuid4().hex[:6].upper()}"
    ts = diagnosis_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    cursor.execute(
        """
        INSERT INTO diagnoses (diagnosis_id, patient_id, diagnosis, diagnosis_date)
        VALUES (?, ?, ?, ?)
        """,
        (did, patient_id, diagnosis.strip(), ts)
    )
    conn.commit()
    conn.close()
    return {"diagnosis_id": did, "patient_id": patient_id, "diagnosis": diagnosis, "diagnosis_date": ts}


def create_prescription_case(
    patient_id: str,
    medications: List[Dict[str, Any]],
    prescribing_doctor: str,
    prescription_date: Optional[str] = None,
    custom_prescription_id: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a new prescription record in SQLite for a patient with 1 or more medications."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    rx_id = (custom_prescription_id or f"RX-{uuid.uuid4().hex[:6].upper()}").strip().upper()
    ts = prescription_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for med in medications:
        cursor.execute(
            """
            INSERT INTO prescriptions (
                prescription_id, patient_id, medication, strength,
                dosage, frequency, route, duration, prescribing_doctor, prescription_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rx_id, patient_id,
                med.get("medication", "").strip(),
                med.get("strength", "").strip(),
                med.get("dosage", "").strip(),
                med.get("frequency", "").strip(),
                med.get("route", "Oral").strip(),
                med.get("duration", "").strip(),
                prescribing_doctor.strip(), ts
            )
        )
    conn.commit()
    conn.close()

    return fetch_prescription_details(rx_id, db_path=db_path)  # type: ignore


def fetch_all_patients(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists all patients with demographics, allergies, and diagnoses."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT patient_id, name, age, sex, allergies FROM patients ORDER BY name ASC")
    patients = [dict(p) for p in cursor.fetchall()]

    for p in patients:
        cursor.execute(
            "SELECT diagnosis_id, diagnosis, diagnosis_date FROM diagnoses WHERE patient_id = ? ORDER BY diagnosis_date DESC",
            (p["patient_id"],)
        )
        p["diagnoses"] = [dict(d) for d in cursor.fetchall()]

    conn.close()
    return patients


def fetch_all_prescriptions_summary(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves summaries of all distinct prescriptions currently stored in SQLite."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 
            rx.prescription_id,
            rx.patient_id,
            p.name AS patient_name,
            p.age AS patient_age,
            p.sex AS patient_sex,
            p.allergies AS patient_allergies,
            rx.prescribing_doctor,
            rx.prescription_date,
            GROUP_CONCAT(rx.medication || ' ' || rx.strength, ', ') AS medications_summary,
            COUNT(rx.id) AS medication_count
        FROM prescriptions rx
        JOIN patients p ON rx.patient_id = p.patient_id
        GROUP BY rx.prescription_id
        ORDER BY rx.prescription_date DESC, rx.prescription_id ASC
        """
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ==============================================================================
# Phase 3: Chief Escalation Resolution Helpers
# ==============================================================================

def insert_escalation_resolution(
    resolution_id: str,
    review_id: str,
    prescription_id: str,
    chief_id: str,
    chief_decision: str,
    chief_notes: str,
    action_required: Optional[str] = None,
    resolved_at: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Records a Chief Pharmacist escalation resolution action.
    Crucially, preserves the original staff pharmacist's reviewed_by and decision in pharmacist_reviews.
    """
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    ts = resolved_at or datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        INSERT INTO escalation_resolutions (
            resolution_id, review_id, prescription_id, chief_id,
            chief_decision, chief_notes, action_required, resolved_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            resolution_id, review_id, prescription_id, chief_id,
            chief_decision, chief_notes, action_required, ts
        )
    )
    conn.commit()
    conn.close()

    return {
        "resolution_id": resolution_id,
        "review_id": review_id,
        "prescription_id": prescription_id,
        "chief_id": chief_id,
        "chief_decision": chief_decision,
        "chief_notes": chief_notes,
        "action_required": action_required,
        "resolved_at": ts
    }


def fetch_escalation_resolutions(
    review_id: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves escalation resolutions for a review or all reviews."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    if review_id:
        cursor.execute(
            """
            SELECT resolution_id, review_id, prescription_id, chief_id,
                   chief_decision, chief_notes, action_required, resolved_at
            FROM escalation_resolutions
            WHERE review_id = ?
            ORDER BY resolved_at DESC
            """,
            (review_id,)
        )
    else:
        cursor.execute(
            """
            SELECT resolution_id, review_id, prescription_id, chief_id,
                   chief_decision, chief_notes, action_required, resolved_at
            FROM escalation_resolutions
            ORDER BY resolved_at DESC
            """
        )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ==============================================================================
# Phase 3: Educational Case & Student Training System Helpers
# ==============================================================================

def fetch_educational_cases(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves de-identified educational cases with optional category and difficulty filtering."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    query = """
        SELECT case_id, title, clinical_category, difficulty, scenario_text,
               deidentified_prescription_json, key_safety_challenge, multiple_choice_question,
               options_json, correct_option_index, explanation_text, source_review_id,
               published_by, created_at
        FROM educational_cases
        WHERE 1=1
    """
    params: List[Any] = []
    if category:
        query += " AND clinical_category = ?"
        params.append(category.upper())
    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty.upper())

    query += " ORDER BY created_at DESC"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    cases = []
    for r in rows:
        c_dict = dict(r)
        try:
            c_dict["deidentified_prescription"] = json.loads(c_dict["deidentified_prescription_json"])
        except Exception:
            c_dict["deidentified_prescription"] = []
        try:
            c_dict["options"] = json.loads(c_dict["options_json"])
        except Exception:
            c_dict["options"] = []
        cases.append(c_dict)
    return cases


def fetch_educational_case_by_id(
    case_id: str,
    db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Retrieves a single educational case by ID."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT case_id, title, clinical_category, difficulty, scenario_text,
               deidentified_prescription_json, key_safety_challenge, multiple_choice_question,
               options_json, correct_option_index, explanation_text, source_review_id,
               published_by, created_at
        FROM educational_cases
        WHERE case_id = ?
        """,
        (case_id.strip(),)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None
    c_dict = dict(row)
    try:
        c_dict["deidentified_prescription"] = json.loads(c_dict["deidentified_prescription_json"])
    except Exception:
        c_dict["deidentified_prescription"] = []
    try:
        c_dict["options"] = json.loads(c_dict["options_json"])
    except Exception:
        c_dict["options"] = []
    return c_dict


def insert_educational_case(
    case_id: str,
    title: str,
    clinical_category: str,
    difficulty: str,
    scenario_text: str,
    deidentified_prescription_json: str,
    key_safety_challenge: str,
    multiple_choice_question: str,
    options_json: str,
    correct_option_index: int,
    explanation_text: str,
    source_review_id: Optional[str] = None,
    published_by: str = "USR-STAFF-001",
    created_at: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Persists a new de-identified educational case created by a pharmacist."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    ts = created_at or datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        INSERT INTO educational_cases (
            case_id, title, clinical_category, difficulty, scenario_text,
            deidentified_prescription_json, key_safety_challenge, multiple_choice_question,
            options_json, correct_option_index, explanation_text, source_review_id,
            published_by, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case_id, title, clinical_category, difficulty, scenario_text,
            deidentified_prescription_json, key_safety_challenge, multiple_choice_question,
            options_json, correct_option_index, explanation_text, source_review_id,
            published_by, ts
        )
    )
    conn.commit()
    conn.close()

    return fetch_educational_case_by_id(case_id, db_path=db_path)  # type: ignore


def record_student_submission(
    submission_id: str,
    case_id: str,
    student_id: str,
    selected_option_index: int,
    is_correct: bool,
    student_notes: Optional[str] = None,
    submitted_at: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Records a student's answer submission for an educational training case."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    ts = submitted_at or datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        INSERT INTO student_case_submissions (
            submission_id, case_id, student_id, selected_option_index,
            is_correct, student_notes, submitted_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            submission_id, case_id, student_id, selected_option_index,
            1 if is_correct else 0, student_notes, ts
        )
    )
    conn.commit()
    conn.close()

    return {
        "submission_id": submission_id,
        "case_id": case_id,
        "student_id": student_id,
        "selected_option_index": selected_option_index,
        "is_correct": is_correct,
        "student_notes": student_notes,
        "submitted_at": ts
    }


def fetch_student_progress(
    student_id: str,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Calculates training metrics, score, and completion progress for a pharmacy student."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total_cases FROM educational_cases")
    total_cases = cursor.fetchone()["total_cases"]

    cursor.execute(
        """
        SELECT COUNT(DISTINCT case_id) AS attempted_cases,
               COUNT(*) AS total_submissions,
               SUM(is_correct) AS correct_submissions
        FROM student_case_submissions
        WHERE student_id = ?
        """,
        (student_id,)
    )
    stat = cursor.fetchone()
    attempted = stat["attempted_cases"] or 0
    total_subs = stat["total_submissions"] or 0
    correct_subs = stat["correct_submissions"] or 0

    cursor.execute(
        """
        SELECT s.submission_id, s.case_id, ec.title, ec.clinical_category, ec.difficulty,
               s.selected_option_index, s.is_correct, s.student_notes, s.submitted_at
        FROM student_case_submissions s
        JOIN educational_cases ec ON s.case_id = ec.case_id
        WHERE s.student_id = ?
        ORDER BY s.submitted_at DESC
        """,
        (student_id,)
    )
    recent_submissions = [dict(r) for r in cursor.fetchall()]
    conn.close()

    accuracy_pct = round((correct_subs / total_subs * 100), 1) if total_subs > 0 else 0.0

    return {
        "student_id": student_id,
        "total_available_cases": total_cases,
        "completed_cases": attempted,
        "total_submissions": total_subs,
        "correct_submissions": correct_subs,
        "accuracy_percentage": f"{accuracy_pct}%",
        "recent_submissions": recent_submissions
    }


# ==============================================================================
# Phase 3: Real Inventory Dispensing & Stock Decrementation Helpers
# ==============================================================================

def dispense_prescription_inventory(
    prescription_id: str,
    actor_id: str,
    notes: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes real dispensing for an approved prescription:
    1. Identifies prescribed medications.
    2. Decrements quantity_on_hand in inventory table.
    3. Records immutable transactions in inventory_transactions table.
    4. Logs PRESCRIPTION_DISPENSED and INVENTORY_DISPENSED in audit_log.
    """
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # 1. Fetch prescription items
    cursor.execute(
        """
        SELECT medication, strength, dosage, frequency, duration
        FROM prescriptions
        WHERE UPPER(prescription_id) = UPPER(?)
        """,
        (prescription_id.strip(),)
    )
    med_rows = cursor.fetchall()
    if not med_rows:
        conn.close()
        raise ValueError(f"Prescription '{prescription_id}' not found for dispensing.")

    dispensed_items = []
    ts = datetime.now(timezone.utc).isoformat()

    cursor.execute("SELECT inventory_id, medication, generic_name, strength, quantity_on_hand, reorder_level FROM inventory")
    all_inv = [dict(r) for r in cursor.fetchall()]

    # 2. Match and decrement inventory for each prescribed item
    for med in med_rows:
        med_name = med["medication"].strip().lower()
        strength = (med["strength"] or "").strip().lower()

        # Find best inventory match
        matched_inv = None
        for item in all_inv:
            i_gen = item["generic_name"].lower()
            i_med = item["medication"].lower()
            i_str = item["strength"].lower()
            if (i_gen in med_name or med_name in i_gen or i_med in med_name or med_name in i_med):
                if not strength or strength in i_str or i_str in strength:
                    matched_inv = item
                    break

        if not matched_inv and all_inv:
            # Fallback to loose medication name match
            for item in all_inv:
                if item["generic_name"].lower() in med_name or med_name in item["generic_name"].lower():
                    matched_inv = item
                    break

        if matched_inv:
            current_qty = matched_inv["quantity_on_hand"]
            dispense_qty = 30  # Standard 30-day unit dose dispensing default
            new_qty = max(0, current_qty - dispense_qty)

            # Update inventory quantity
            cursor.execute(
                """
                UPDATE inventory
                SET quantity_on_hand = ?,
                    last_updated = ?
                WHERE inventory_id = ?
                """,
                (new_qty, ts, matched_inv["inventory_id"])
            )

            # Record inventory transaction
            tx_id = f"TX-{uuid.uuid4().hex[:8].upper()}"
            cursor.execute(
                """
                INSERT INTO inventory_transactions (
                    transaction_id, inventory_id, prescription_id, transaction_type,
                    quantity_change, quantity_after, actor_id, notes, timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tx_id, matched_inv["inventory_id"], prescription_id.strip().upper(),
                    "DISPENSED", -dispense_qty, new_qty, actor_id,
                    notes or f"Dispensed for prescription {prescription_id}", ts
                )
            )

            dispensed_items.append({
                "inventory_id": matched_inv["inventory_id"],
                "medication": matched_inv["medication"],
                "strength": matched_inv["strength"],
                "quantity_dispensed": dispense_qty,
                "previous_stock": current_qty,
                "new_stock": new_qty,
                "status": "OUT OF STOCK" if new_qty == 0 else ("LOW STOCK" if new_qty <= matched_inv["reorder_level"] else "AVAILABLE")
            })

    # 3. Record audit event within the same active transaction
    aid = f"AUD-{uuid.uuid4().hex[:8].upper()}"
    cursor.execute(
        """
        INSERT INTO audit_log (
            audit_id, event_type, actor_type, actor_id,
            prescription_id, review_id, event_data, timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            aid, "PRESCRIPTION_DISPENSED", "PHARMACIST", actor_id,
            prescription_id.strip().upper(), None,
            json.dumps({"dispensed_items": dispensed_items, "pharmacist_notes": notes}), ts
        )
    )

    conn.commit()
    conn.close()

    return {
        "prescription_id": prescription_id.strip().upper(),
        "status": "DISPENSED",
        "dispensed_by": actor_id,
        "timestamp": ts,
        "dispensed_items": dispensed_items
    }



def fetch_inventory_transactions(
    limit: int = 50,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves recent stock dispensing and replenishment transactions."""
    initialize_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT tx.transaction_id, tx.inventory_id, tx.prescription_id, tx.transaction_type,
               tx.quantity_change, tx.quantity_after, tx.actor_id, tx.notes, tx.timestamp,
               inv.medication, inv.generic_name, inv.strength
        FROM inventory_transactions tx
        JOIN inventory inv ON tx.inventory_id = inv.inventory_id
        ORDER BY tx.timestamp DESC
        LIMIT ?
        """,
        (limit,)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


