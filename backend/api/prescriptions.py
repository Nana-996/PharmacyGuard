"""
Prescriptions API router for PharmacyGuard.
Supports real prescription entry, modification/editing by pharmacists,
patient demographics lookup, and re-triggering AI verification.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, status

from backend.auth.dependencies import require_roles
from backend.data.database import (
    fetch_prescription_details,
    fetch_all_prescriptions_summary,
    fetch_all_patients,
    create_or_update_patient,
    create_patient_diagnosis,
    create_prescription_case,
    update_prescription_items,
    insert_audit_event,
)
from backend.services.review_service import create_review
from backend.security.demo_guard import is_approved_synthetic_patient

router = APIRouter(prefix="/api/prescriptions", tags=["prescriptions"])

PHARMACIST_ROLES = ["STAFF_PHARMACIST", "CHIEF_PHARMACIST"]


class MedicationItemInput(BaseModel):
    medication: str = Field(..., min_length=1, description="Medication name")
    strength: str = Field(..., min_length=1, description="Strength (e.g. 500mg, 20mg)")
    dosage: str = Field(..., min_length=1, description="Dosage (e.g. 1 capsule, 1 tablet)")
    frequency: str = Field(..., min_length=1, description="Frequency (e.g. Every 8 hours)")
    route: str = Field(default="Oral", description="Route of administration")
    duration: str = Field(default="7 days", description="Course duration")


class EditPrescriptionRequest(BaseModel):
    medications: List[MedicationItemInput] = Field(..., min_length=1, description="Updated medication regimen")
    prescribing_doctor: Optional[str] = None
    prescription_date: Optional[str] = None
    modification_notes: Optional[str] = Field(default=None, description="Pharmacist clinical rationale for editing prescription")
    auto_trigger_re_review: bool = Field(default=False, description="Automatically re-run AI verification after editing")


class CreatePrescriptionRequest(BaseModel):
    patient_id: Optional[str] = None
    patient_name: str = Field(..., min_length=1, description="Patient full name")
    patient_age: int = Field(..., ge=0, le=130, description="Patient age")
    patient_sex: str = Field(..., min_length=1, description="Patient biological sex")
    patient_allergies: Optional[str] = Field(default="NKDA (No known drug allergies)")
    diagnosis: str = Field(..., min_length=1, description="Primary clinical diagnosis")
    diagnosis_date: Optional[str] = None
    prescribing_doctor: str = Field(..., min_length=1, description="Prescribing physician name and credentials")
    prescription_date: Optional[str] = None
    prescription_id: Optional[str] = None
    medications: List[MedicationItemInput] = Field(..., min_length=1, description="List of prescribed medications")
    auto_trigger_review: bool = Field(default=True, description="Automatically invoke AI agent upon ingestion")


@router.get("")
def list_all_prescriptions_endpoint(
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
):
    """Lists all prescriptions currently stored in the hospital database."""
    items = fetch_all_prescriptions_summary()
    return {"status": "success", "total": len(items), "data": items}


@router.get("/patients")
def list_patients_endpoint(
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
):
    """Retrieves all hospital patients with demographics, allergy records, and diagnoses."""
    patients = fetch_all_patients()
    return {"status": "success", "total": len(patients), "data": patients}


@router.get("/{prescription_id}")
def get_prescription_endpoint(
    prescription_id: str,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
):
    """Retrieves full structured details for a prescription by its unique ID."""
    clean_id = prescription_id.strip().upper()
    details = fetch_prescription_details(clean_id)
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription '{clean_id}' not found in the database."
        )
    return {"status": "success", "data": details}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_prescription_endpoint(
    payload: CreatePrescriptionRequest,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
):
    """
    Ingests a new prescription into SQLite.
    Creates or associates the patient, creates the diagnosis, and saves the medication items.
    Optionally launches the Strands Bedrock agent for automated clinical verification.
    """
    # Demo Safety Gate: Block arbitrary non-synthetic patient PII entry
    if not is_approved_synthetic_patient(patient_id=payload.patient_id, patient_name=payload.patient_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Demonstration Sandbox Policy: Arbitrary patient record creation is restricted in this public demo "
                "to prevent unintended PHI/PII entry. Please select an approved synthetic patient profile from the hospital directory or use preloaded case presets."
            )
        )

    # 1. Ensure patient exists or create
    pat = create_or_update_patient(
        patient_id=payload.patient_id,
        name=payload.patient_name,
        age=payload.patient_age,
        sex=payload.patient_sex,
        allergies=payload.patient_allergies
    )
    patient_id = pat["patient_id"]

    # 2. Record diagnosis
    create_patient_diagnosis(
        patient_id=patient_id,
        diagnosis=payload.diagnosis,
        diagnosis_date=payload.diagnosis_date
    )

    # 3. Create prescription items
    meds_data = [m.model_dump() for m in payload.medications]
    rx_details = create_prescription_case(
        patient_id=patient_id,
        medications=meds_data,
        prescribing_doctor=payload.prescribing_doctor,
        prescription_date=payload.prescription_date,
        custom_prescription_id=payload.prescription_id
    )
    rx_id = rx_details["prescription_id"]

    # 4. Record audit log event for ingestion
    from datetime import datetime, timezone
    import json
    insert_audit_event(
        event_type="PRESCRIPTION_INGESTED",
        actor_type="PHARMACIST",
        actor_id=current_user["user_id"],
        prescription_id=rx_id,
        event_data=json.dumps({
            "ingested_by": current_user["user_id"],
            "patient_name": payload.patient_name,
            "medication_count": len(meds_data),
            "prescribing_doctor": payload.prescribing_doctor
        }),
        timestamp=datetime.now(timezone.utc).isoformat()
    )

    # 5. Automatically launch agent review if requested
    review_result = None
    if payload.auto_trigger_review:
        try:
            review_result = create_review(rx_id)
        except Exception as e:
            # If agent invocation fails, return prescription with warning
            return {
                "status": "partial_success",
                "message": f"Prescription '{rx_id}' ingested, but initial AI review encountered an issue: {str(e)}",
                "prescription": rx_details,
                "review": None
            }

    return {
        "status": "success",
        "message": f"Prescription '{rx_id}' successfully ingested into hospital database.",
        "prescription": rx_details,
        "review": review_result
    }


@router.patch("/{prescription_id}")
def edit_prescription_endpoint(
    prescription_id: str,
    payload: EditPrescriptionRequest,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
):
    """
    Modifies an existing doctor's prescription in SQLite.
    Updates medication regimen (dosage, strength, frequency, route, duration).
    Logs the edit under the authenticated pharmacist's ID in the audit trail.
    Optionally re-runs the AI verification on the updated regimen.
    """
    clean_rx_id = prescription_id.strip().upper()
    meds_data = [m.model_dump() for m in payload.medications]

    try:
        updated_rx = update_prescription_items(
            prescription_id=clean_rx_id,
            medications=meds_data,
            prescribing_doctor=payload.prescribing_doctor,
            prescription_date=payload.prescription_date,
            editor_user_id=current_user["user_id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    review_result = None
    if payload.auto_trigger_re_review:
        review_result = create_review(clean_rx_id)

    return {
        "status": "success",
        "message": f"Prescription '{clean_rx_id}' updated successfully.",
        "data": updated_rx,
        "re_review": review_result
    }


@router.post("/{prescription_id}/re-review")
def re_review_prescription_endpoint(
    prescription_id: str,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
):
    """Triggers a fresh Strands AI Bedrock clinical review on a prescription."""
    clean_rx_id = prescription_id.strip().upper()
    rx_details = fetch_prescription_details(clean_rx_id)
    if not rx_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription '{clean_rx_id}' not found in the database."
        )

    review_result = create_review(clean_rx_id)
    return {
        "status": "success",
        "message": f"AI review successfully completed for prescription '{clean_rx_id}'.",
        "data": review_result
    }
