"""
Clinical Verification Tools for PharmacyGuard Strands Agent.
Exposes deterministic evidence-gathering checks backed by simulated SQLite clinical knowledge bases.

NOTE: These tools provide evidence only. The Strands agent reasons over this evidence
and the licensed pharmacist makes the final clinical decision. All data is synthetic.
"""

import re
from typing import Dict, Any, List, Union, Optional
from strands import tool
from backend.data.database import (
    query_diagnosis_medication_match,
    query_allergy_cross_reactions,
    query_drug_interactions,
    query_medication_reference,
    get_db_connection,
)


def _normalize_med_list(meds: Union[List[Any], str]) -> List[str]:
    """Helper to convert various input formats into a clean list of medication strings."""
    if isinstance(meds, list):
        result = []
        for item in meds:
            if isinstance(item, dict):
                result.append(item.get("medication") or item.get("medication_name") or item.get("generic_name") or str(item))
            elif isinstance(item, str) and item.strip():
                result.append(item.strip())
        return result
    elif isinstance(meds, str):
        parts = [p.strip() for p in meds.split(",") if p.strip()]
        return parts if parts else [meds.strip()]
    return []


def _extract_numeric_mg(dosage_str: str) -> Optional[float]:
    """Extracts numeric milligram value from dosage string (e.g., '500mg', '20 mg', '875mg / 125mg')."""
    if not dosage_str:
        return None
    # Check for combo dosage like 875/125mg -> primary active is 875
    combo_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:mg)?\s*/\s*(\d+(?:\.\d+)?)", dosage_str, re.IGNORECASE)
    if combo_match:
        return float(combo_match.group(1))
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:mg|milligram)", dosage_str, re.IGNORECASE)
    if match:
        return float(match.group(1))
    # General number fallback
    num_match = re.search(r"(\d+(?:\.\d+)?)", dosage_str)
    if num_match:
        return float(num_match.group(1))
    return None


def _calculate_daily_multiplier(frequency_str: str) -> float:
    """Calculates daily multiplier from frequency string."""
    freq = (frequency_str or "").lower()
    if "8 hour" in freq or "three times" in freq or "tid" in freq or "3 times" in freq:
        return 3.0
    if "12 hour" in freq or "twice" in freq or "bid" in freq or "2 times" in freq:
        return 2.0
    if "6 hour" in freq or "four times" in freq or "qid" in freq or "4 times" in freq:
        return 4.0
    if "daily" in freq or "once" in freq or "morning" in freq or "bedtime" in freq or "qd" in freq:
        return 1.0
    if "4 hour" in freq:
        return 6.0
    return 1.0  # default assumption if unspecified


@tool
def diagnosis_medication_check(diagnosis: str, medication: str) -> Dict[str, Any]:
    """Compare a patient's documented diagnosis with a prescribed medication to verify indication alignment.

    Call this tool to evaluate whether the prescribed medication is standard or recognized therapy
    for the patient's active diagnosis according to simulated hospital guideline records.

    Args:
        diagnosis: The patient's documented active diagnosis (e.g., 'Streptococcal pharyngitis', 'Type 2 diabetes').
        medication: The prescribed medication name (e.g., 'Amoxicillin 500mg', 'Lisinopril 20mg').

    Returns:
        A dictionary containing:
        - relevant: boolean indicating if medication is indicated for diagnosis
        - category: 'MATCH', 'POTENTIAL_MISMATCH', or 'UNRECOGNIZED_DIAGNOSIS'
        - evidence: Clinical rationale from local reference guidelines
        - finding_priority: 'CLEAR' (if match) or 'REVIEW' (if potential mismatch)
        - requires_pharmacist_review: True (safety reminder)
    """
    if not diagnosis or not medication:
        return {
            "status": "error",
            "relevant": False,
            "category": "INSUFFICIENT_INPUT",
            "evidence": "Both diagnosis and medication must be provided.",
            "finding_priority": "REVIEW",
            "requires_pharmacist_review": True,
            "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
        }

    match_result = query_diagnosis_medication_match(diagnosis, medication)
    priority = "CLEAR" if match_result.get("relevant") else "REVIEW"

    return {
        "status": "success",
        "diagnosis": diagnosis,
        "medication": medication,
        "relevant": match_result.get("relevant", False),
        "category": match_result.get("category", "POTENTIAL_MISMATCH"),
        "evidence": match_result.get("evidence", ""),
        "finding_priority": priority,
        "requires_pharmacist_review": True,
        "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
    }


@tool
def allergy_check(patient_allergies: str, prescribed_medications: Union[List[Any], str]) -> Dict[str, Any]:
    """Check a patient's documented drug/environmental allergies against prescribed medications for potential conflicts or cross-reactivity.

    Call this tool to verify whether any prescribed medication matches or cross-reacts with
    the patient's recorded allergies (e.g., Penicillin allergy vs. Augmentin/Amoxicillin).

    Args:
        patient_allergies: The patient's allergy string (e.g., 'Penicillin (Beta-Lactams) - Severe Anaphylaxis', 'NKDA').
        prescribed_medications: List of prescribed medication names or comma-separated string.

    Returns:
        A dictionary containing:
        - has_allergy_conflict: boolean indicating if a cross-reactive allergy conflict exists
        - conflicts: List of detected conflict details with allergen, conflicting medication, risk level, and explanation
        - finding_priority: 'HIGH PRIORITY REVIEW' (if severe conflict found), 'REVIEW', or 'CLEAR' (if no conflict)
        - recommendation: Actionable guidance for the reviewing pharmacist
        - requires_pharmacist_review: True
    """
    meds_list = _normalize_med_list(prescribed_medications)

    if not patient_allergies or not meds_list:
        return {
            "status": "success",
            "has_allergy_conflict": False,
            "conflicts": [],
            "finding_priority": "CLEAR",
            "recommendation": "No documented allergies or medications provided to evaluate.",
            "requires_pharmacist_review": True,
            "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
        }

    all_conflicts = []
    for med in meds_list:
        conflicts = query_allergy_cross_reactions(patient_allergies, med)
        all_conflicts.extend(conflicts)

    has_conflict = len(all_conflicts) > 0
    if has_conflict:
        is_severe = any(c.get("reaction_risk") == "Severe" for c in all_conflicts)
        priority = "HIGH PRIORITY REVIEW" if is_severe else "REVIEW"
        recom = f"Documented allergy conflict detected ({all_conflicts[0]['allergen_group']}). Withhold dispensing pending prescriber contact and allergy reconciliation."
    else:
        priority = "CLEAR"
        recom = "No documented allergy conflicts identified against prescribed medications."

    return {
        "status": "success",
        "patient_allergies": patient_allergies,
        "evaluated_medications": meds_list,
        "has_allergy_conflict": has_conflict,
        "conflicts": all_conflicts,
        "finding_priority": priority,
        "recommendation": recom,
        "requires_pharmacist_review": True,
        "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
    }


@tool
def duplicate_medication_check(prescribed_medications: Union[List[Any], str]) -> Dict[str, Any]:
    """Identify duplicate active ingredients or therapeutic class duplication among prescribed medications.

    Call this tool to check for duplicated therapies within a prescription or regimen
    (e.g., concurrent prescription of multiple systemic NSAIDs like Ibuprofen and Naproxen).

    Args:
        prescribed_medications: List of all prescribed medications in the prescription.

    Returns:
        A dictionary containing:
        - has_duplicates: boolean indicating if duplicates or therapeutic overlaps were found
        - detected_duplicates: List of duplication records detailing drugs involved, class, and explanation
        - finding_priority: 'HIGH PRIORITY REVIEW' (if major therapeutic duplicate found) or 'CLEAR'
        - explanation: Clinical summary of the therapeutic duplication
        - requires_pharmacist_review: True
    """
    meds_list = _normalize_med_list(prescribed_medications)

    if len(meds_list) < 2:
        return {
            "status": "success",
            "has_duplicates": False,
            "detected_duplicates": [],
            "finding_priority": "CLEAR",
            "explanation": "Single medication prescribed; no internal duplication possible.",
            "requires_pharmacist_review": True,
            "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
        }

    # Fetch therapeutic classes for all prescribed medications
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT generic_name, brand_names, therapeutic_class FROM medication_reference")
    ref_rows = cursor.fetchall()
    conn.close()

    med_classes: Dict[str, str] = {}
    for med in meds_list:
        med_lower = med.lower()
        matched_class = "Unknown"
        for r in ref_rows:
            gen = r["generic_name"].lower()
            brands = r["brand_names"].lower()
            if gen in med_lower or any(b.strip() in med_lower for b in brands.split(",")):
                matched_class = r["therapeutic_class"]
                break
        med_classes[med] = matched_class

    # Group medications by therapeutic class
    class_groups: Dict[str, List[str]] = {}
    for med, t_class in med_classes.items():
        if t_class != "Unknown":
            class_groups.setdefault(t_class, []).append(med)

    duplicates = []
    for t_class, grouped_meds in class_groups.items():
        if len(grouped_meds) > 1:
            if "NSAID" in t_class or "Nonsteroidal" in t_class:
                duplicates.append({
                    "duplicate_type": "Therapeutic Class Duplication (NSAIDs)",
                    "medications_involved": grouped_meds,
                    "therapeutic_class": t_class,
                    "severity": "High",
                    "explanation": f"Concurrent prescription of multiple systemic NSAIDs ({', '.join(grouped_meds)}) provides no additive pain relief but substantially multiplies risk of gastrointestinal bleeding, ulcers, and acute nephrotoxicity."
                })
            else:
                duplicates.append({
                    "duplicate_type": "Therapeutic Class Duplication",
                    "medications_involved": grouped_meds,
                    "therapeutic_class": t_class,
                    "severity": "Moderate",
                    "explanation": f"Multiple medications belonging to the same therapeutic class ({t_class}) are prescribed concurrently: {', '.join(grouped_meds)}."
                })

    has_duplicates = len(duplicates) > 0
    priority = "HIGH PRIORITY REVIEW" if (has_duplicates and any(d["severity"] == "High" for d in duplicates)) else ("REVIEW" if has_duplicates else "CLEAR")

    return {
        "status": "success",
        "has_duplicates": has_duplicates,
        "detected_duplicates": duplicates,
        "finding_priority": priority,
        "explanation": duplicates[0]["explanation"] if duplicates else "No duplicate active ingredients or therapeutic class overlaps detected.",
        "requires_pharmacist_review": True,
        "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
    }


@tool
def medication_interaction_check(prescribed_medications: Union[List[Any], str]) -> Dict[str, Any]:
    """Check for drug-drug interactions among prescribed medications against the local simulated interaction knowledge base.

    Call this tool whenever multiple medications are prescribed together to identify documented
    pharmacodynamic or pharmacokinetic interactions (e.g., ACEI + CCB, NSAID + NSAID).

    Args:
        prescribed_medications: List of all prescribed medications in the prescription.

    Returns:
        A dictionary containing:
        - has_interactions: boolean indicating if interactions were documented in the local database
        - interactions: List of interaction details (medication_a, medication_b, severity, mechanism, description, recommendation)
        - finding_priority: 'HIGH PRIORITY REVIEW' (Major interaction), 'REVIEW' (Moderate/Minor), or 'CLEAR' (none)
        - requires_pharmacist_review: True
    """
    meds_list = _normalize_med_list(prescribed_medications)

    if len(meds_list) < 2:
        return {
            "status": "success",
            "has_interactions": False,
            "interactions": [],
            "finding_priority": "CLEAR",
            "requires_pharmacist_review": True,
            "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
        }

    detected_interactions = query_drug_interactions(meds_list)
    has_interactions = len(detected_interactions) > 0

    if has_interactions:
        has_major = any(i.get("severity") == "Major" for i in detected_interactions)
        priority = "HIGH PRIORITY REVIEW" if has_major else "REVIEW"
    else:
        priority = "CLEAR"

    return {
        "status": "success",
        "evaluated_medications": meds_list,
        "has_interactions": has_interactions,
        "interactions": detected_interactions,
        "finding_priority": priority,
        "requires_pharmacist_review": True,
        "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
    }


@tool
def dosage_check(medication: str, dosage: str, frequency: str) -> Dict[str, Any]:
    """Compare a prescribed medication's dose and frequency against local simulated clinical reference ranges.

    Call this tool to evaluate whether the prescribed single dose or calculated daily dose falls within
    standard expected minimum/maximum boundaries or requires dosage adjustment review.

    Args:
        medication: The medication name (e.g., 'Amoxicillin', 'Lisinopril 20mg').
        dosage: The prescribed single dose (e.g., '500mg', '1 tablet (20mg)').
        frequency: The prescribed administration frequency (e.g., 'Every 8 hours', 'Once daily').

    Returns:
        A dictionary containing:
        - within_standard_range: boolean indicating if dose is within reference bounds
        - reference_data: Expected single dose range, maximum daily dose, and standard notes
        - parsed_single_dose_mg: numeric value in mg
        - estimated_daily_dose_mg: estimated daily total in mg
        - flags: List of dosage observations or warnings
        - finding_priority: 'CLEAR', 'REVIEW', or 'HIGH PRIORITY REVIEW'
        - requires_pharmacist_review: True
    """
    if not medication or not dosage:
        return {
            "status": "error",
            "within_standard_range": False,
            "flags": ["Missing medication or dosage string for dosage verification."],
            "finding_priority": "REVIEW",
            "requires_pharmacist_review": True,
            "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
        }

    ref = query_medication_reference(medication)
    if not ref:
        return {
            "status": "success",
            "within_standard_range": True,
            "reference_data": None,
            "flags": [f"No specific reference range stored for '{medication}'; manual pharmacist verification advised."],
            "finding_priority": "REVIEW",
            "requires_pharmacist_review": True,
            "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
        }

    single_mg = _extract_numeric_mg(dosage)
    multiplier = _calculate_daily_multiplier(frequency)
    daily_mg = (single_mg * multiplier) if single_mg is not None else None

    flags = []
    priority = "CLEAR"
    within_range = True

    min_single = ref["min_single_dose_mg"]
    max_single = ref["max_single_dose_mg"]
    max_daily = ref["max_daily_dose_mg"]

    if single_mg is not None:
        if single_mg > max_single:
            within_range = False
            priority = "HIGH PRIORITY REVIEW"
            flags.append(f"Single dose ({single_mg} mg) exceeds standard maximum single dose reference ({max_single} mg).")
        elif single_mg < min_single:
            priority = "REVIEW"
            flags.append(f"Single dose ({single_mg} mg) is below standard therapeutic single dose reference ({min_single} mg).")

    if daily_mg is not None and daily_mg > max_daily:
        within_range = False
        priority = "HIGH PRIORITY REVIEW"
        flags.append(f"Estimated daily dose ({daily_mg} mg/day) exceeds maximum daily reference dose ({max_daily} mg/day).")

    if not flags:
        flags.append(f"Prescribed dose ({dosage}, {frequency}) is within standard reference boundaries ({min_single}-{max_single} mg/dose, max {max_daily} mg/day).")

    return {
        "status": "success",
        "medication": medication,
        "prescribed_dosage": dosage,
        "prescribed_frequency": frequency,
        "parsed_single_dose_mg": single_mg,
        "estimated_daily_dose_mg": daily_mg,
        "within_standard_range": within_range,
        "reference_data": {
            "generic_name": ref["generic_name"],
            "therapeutic_class": ref["therapeutic_class"],
            "standard_single_dose_range_mg": f"{min_single} - {max_single} mg",
            "max_daily_dose_mg": f"{max_daily} mg",
            "dosage_notes": ref["dosage_notes"]
        },
        "flags": flags,
        "finding_priority": priority,
        "requires_pharmacist_review": True,
        "safety_disclaimer": "This finding is decision-support evidence from local simulated records. Final verification rests with the licensed pharmacist."
    }
