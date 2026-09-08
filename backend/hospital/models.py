from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Patient:
    patient_id: str
    first_name: str
    last_name: str
    age: int
    gender: str
    date_of_birth: str


@dataclass
class Allergy:
    allergy_id: str
    patient_id: str
    allergen: str
    category: str  # e.g., 'Drug', 'Food', 'Environmental'
    reaction: str  # e.g., 'Anaphylaxis', 'Rash', 'Nausea'
    severity: str  # e.g., 'Severe', 'Moderate', 'Mild'


@dataclass
class Diagnosis:
    diagnosis_id: str
    icd10_code: str
    description: str


@dataclass
class PrescribedMedication:
    medication_id: str
    medication_name: str
    generic_name: str
    dosage: str
    route: str  # e.g., 'Oral', 'Intravenous', 'Topical'
    frequency: str  # e.g., 'Every 8 hours', 'Once daily'
    duration: str  # e.g., '10 days', '30 days', 'Ongoing'
    instructions: str


@dataclass
class PrescriptionDetail:
    prescription_id: str
    patient_id: str
    patient_name: str
    patient_age: int
    patient_gender: str
    diagnosis_code: str
    diagnosis_description: str
    prescribed_date: str
    prescriber_name: str
    status: str
    medications: List[dict] = field(default_factory=list)
    allergies: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "prescription_id": self.prescription_id,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "patient_age": self.patient_age,
            "patient_gender": self.patient_gender,
            "diagnosis": {
                "code": self.diagnosis_code,
                "description": self.diagnosis_description,
            },
            "prescribed_date": self.prescribed_date,
            "prescriber": self.prescriber_name,
            "status": self.status,
            "prescribed_medications": self.medications,
            "allergies": self.allergies,
        }
