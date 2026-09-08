from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from backend.hospital.database import get_db_connection, initialize_hospital_db, DEFAULT_DB_PATH
from backend.hospital.models import PrescriptionDetail


class HospitalRepository(ABC):
    """
    Abstract interface for hospital data retrieval.
    Can be backed by SQLite (for local simulation) or a remote Hospital HIS/EHR API.
    """

    @abstractmethod
    def get_prescription_by_id(self, prescription_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full structured prescription details by prescription ID."""
        pass

    @abstractmethod
    def list_all_prescriptions(self) -> List[Dict[str, Any]]:
        """List summary of all available prescriptions."""
        pass


class SQLiteHospitalRepository(HospitalRepository):
    """
    SQLite implementation of HospitalRepository for local development and testing.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        # Ensure database is created and seeded
        initialize_hospital_db(self.db_path)

    def get_prescription_by_id(self, prescription_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        # Query prescription joined with patient and diagnosis
        cursor.execute(
            """
            SELECT 
                rx.prescription_id,
                rx.patient_id,
                p.first_name || ' ' || p.last_name AS patient_name,
                p.age AS patient_age,
                p.gender AS patient_gender,
                d.icd10_code AS diagnosis_code,
                d.description AS diagnosis_description,
                rx.prescribed_date,
                rx.prescriber_name,
                rx.status,
                rx.notes
            FROM prescriptions rx
            JOIN patients p ON rx.patient_id = p.patient_id
            JOIN diagnoses d ON rx.diagnosis_id = d.diagnosis_id
            WHERE UPPER(rx.prescription_id) = UPPER(?)
            """,
            (prescription_id.strip(),)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        # Fetch prescribed medications
        cursor.execute(
            """
            SELECT 
                medication_name,
                generic_name,
                dosage,
                route,
                frequency,
                duration,
                instructions
            FROM prescription_medications
            WHERE UPPER(prescription_id) = UPPER(?)
            """,
            (prescription_id.strip(),)
        )
        med_rows = cursor.fetchall()
        medications = [
            {
                "medication_name": m["medication_name"],
                "generic_name": m["generic_name"],
                "dosage": m["dosage"],
                "route": m["route"],
                "frequency": m["frequency"],
                "duration": m["duration"],
                "instructions": m["instructions"],
            }
            for m in med_rows
        ]

        # Fetch patient allergies
        patient_id = row["patient_id"]
        cursor.execute(
            """
            SELECT 
                allergen,
                category,
                reaction,
                severity
            FROM allergies
            WHERE patient_id = ?
            """,
            (patient_id,)
        )
        allergy_rows = cursor.fetchall()
        allergies = [
            {
                "allergen": a["allergen"],
                "category": a["category"],
                "reaction": a["reaction"],
                "severity": a["severity"],
            }
            for a in allergy_rows
        ]

        conn.close()

        detail = PrescriptionDetail(
            prescription_id=row["prescription_id"],
            patient_id=row["patient_id"],
            patient_name=row["patient_name"],
            patient_age=row["patient_age"],
            patient_gender=row["patient_gender"],
            diagnosis_code=row["diagnosis_code"],
            diagnosis_description=row["diagnosis_description"],
            prescribed_date=row["prescribed_date"],
            prescriber_name=row["prescriber_name"],
            status=row["status"],
            medications=medications,
            allergies=allergies,
        )

        return detail.to_dict()

    def list_all_prescriptions(self) -> List[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                rx.prescription_id,
                rx.patient_id,
                p.first_name || ' ' || p.last_name AS patient_name,
                d.icd10_code,
                d.description AS diagnosis_description,
                rx.status,
                rx.prescribed_date
            FROM prescriptions rx
            JOIN patients p ON rx.patient_id = p.patient_id
            JOIN diagnoses d ON rx.diagnosis_id = d.diagnosis_id
            ORDER BY rx.prescription_id ASC
            """
        )
        rows = cursor.fetchall()
        results = [dict(r) for r in rows]
        conn.close()
        return results


# Default repository instance
_default_repo: Optional[HospitalRepository] = None


def get_hospital_repository() -> HospitalRepository:
    """Singleton getter for the configured hospital repository."""
    global _default_repo
    if _default_repo is None:
        _default_repo = SQLiteHospitalRepository()
    return _default_repo
