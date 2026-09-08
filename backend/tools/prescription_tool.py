"""
Prescription Retrieval Tool for Strands Agent.
Exposes hospital database records (patient, diagnoses, prescriptions, medications) to the AI agent.
"""

from typing import Dict, Any, Optional
from strands import tool
from backend.data.database import fetch_prescription_details


@tool
def get_prescription(prescription_id: str) -> Dict[str, Any]:
    """Retrieve structured prescription, patient demographics, allergies, and diagnosis data from the hospital database.

    Call this tool whenever you need to look up a prescription by its ID (e.g., 'RX-1001', 'RX-1002', 'RX-1003', 'RX-1004', 'RX-1005').
    It retrieves all relevant details including patient name, age, sex, documented allergies, active diagnoses, prescribed medications,
    strengths, dosages, routes, frequencies, durations, and the prescribing physician.

    Args:
        prescription_id: The unique identifier of the prescription (e.g., 'RX-1001').

    Returns:
        A dictionary containing:
        - status: 'success' or 'error'
        - prescription_id: The requested prescription identifier
        - patient: Dictionary with patient_id, name, age, sex, and documented allergies
        - diagnoses: List of active diagnosis records for the patient
        - medications: List of prescribed medication items with dosage, route, frequency, and duration
        - prescribing_doctor: Name and title of the prescribing doctor
        - prescription_date: Date the prescription was written
    """
    if not prescription_id or not isinstance(prescription_id, str) or not prescription_id.strip():
        return {
            "status": "error",
            "message": "Prescription ID must be a non-empty string.",
            "data": None
        }

    clean_id = prescription_id.strip()
    record = fetch_prescription_details(clean_id)

    if not record:
        return {
            "status": "error",
            "message": f"Prescription with ID '{clean_id}' was not found in the hospital database.",
            "data": None
        }

    return {
        "status": "success",
        "message": f"Prescription '{clean_id}' retrieved successfully.",
        "data": record
    }
