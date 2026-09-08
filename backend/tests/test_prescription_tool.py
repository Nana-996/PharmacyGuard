"""
Automated unit tests for the PharmacyGuard simulated hospital database
and Strands get_prescription tool.
"""

import os
import unittest
import tempfile
from backend.data.database import (
    initialize_database,
    get_db_connection,
    fetch_prescription_details,
)
from backend.tools.prescription_tool import get_prescription


class TestHospitalDatabaseAndTool(unittest.TestCase):
    """Test suite for the simulated hospital SQLite database and get_prescription tool."""

    def setUp(self):
        """Ensure fresh initialization of the database."""
        initialize_database()

    def test_database_schema_and_tables(self):
        """Verify all 4 required tables exist with valid row counts."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check table existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row["name"] for row in cursor.fetchall()}
        self.assertIn("patients", tables)
        self.assertIn("diagnoses", tables)
        self.assertIn("medications", tables)
        self.assertIn("prescriptions", tables)

        # Check record counts
        cursor.execute("SELECT COUNT(*) AS c FROM patients")
        self.assertGreaterEqual(cursor.fetchone()["c"], 5)

        cursor.execute("SELECT COUNT(*) AS c FROM diagnoses")
        self.assertGreaterEqual(cursor.fetchone()["c"], 5)

        cursor.execute("SELECT COUNT(*) AS c FROM medications")
        self.assertGreaterEqual(cursor.fetchone()["c"], 8)

        cursor.execute("SELECT COUNT(*) AS c FROM prescriptions")
        self.assertGreaterEqual(cursor.fetchone()["c"], 9)

        conn.close()

    def test_tool_metadata(self):
        """Verify Strands tool metadata and callable attributes."""
        self.assertEqual(get_prescription.tool_name, "get_prescription")
        self.assertEqual(get_prescription.__name__, "get_prescription")
        self.assertIsNotNone(get_prescription.__doc__)
        self.assertIn("Retrieve structured prescription", get_prescription.__doc__)
        self.assertTrue(callable(get_prescription))

    def test_case_1_routine_prescription(self):
        """Test Case 1: Routine prescription with no obvious issue (RX-1001: Amoxicillin for Strep Throat)."""
        result = get_prescription("RX-1001")
        self.assertEqual(result["status"], "success")
        data = result["data"]

        self.assertEqual(data["prescription_id"], "RX-1001")
        self.assertEqual(data["patient"]["patient_id"], "PAT-101")
        self.assertEqual(data["patient"]["name"], "John Doe")
        self.assertEqual(data["patient"]["age"], 34)
        self.assertEqual(data["patient"]["sex"], "Male")
        self.assertIn("NKDA", data["patient"]["allergies"])

        self.assertEqual(len(data["diagnoses"]), 1)
        self.assertIn("pharyngitis", data["diagnoses"][0]["diagnosis"].lower())

        self.assertEqual(len(data["medications"]), 1)
        med = data["medications"][0]
        self.assertEqual(med["medication"], "Amoxicillin")
        self.assertEqual(med["strength"], "500mg")
        self.assertIn("8 hours", med["frequency"])

    def test_case_2_diagnosis_mismatch(self):
        """Test Case 2: Prescription where medication may not correspond with diagnosis (RX-1002: Lisinopril for Diabetes)."""
        result = get_prescription("RX-1002")
        self.assertEqual(result["status"], "success")
        data = result["data"]

        self.assertEqual(data["prescription_id"], "RX-1002")
        self.assertEqual(data["patient"]["patient_id"], "PAT-102")
        self.assertEqual(data["patient"]["name"], "Jane Smith")
        self.assertIn("diabetes", data["diagnoses"][0]["diagnosis"].lower())

        self.assertEqual(len(data["medications"]), 1)
        self.assertEqual(data["medications"][0]["medication"], "Lisinopril")
        self.assertEqual(data["medications"][0]["strength"], "20mg")

    def test_case_3_documented_allergy(self):
        """Test Case 3: Prescription involving documented patient allergy (RX-1003: Augmentin for Penicillin allergy)."""
        result = get_prescription("RX-1003")
        self.assertEqual(result["status"], "success")
        data = result["data"]

        self.assertEqual(data["prescription_id"], "RX-1003")
        self.assertEqual(data["patient"]["name"], "Robert Taylor")
        self.assertIn("Penicillin", data["patient"]["allergies"])
        self.assertIn("Anaphylaxis", data["patient"]["allergies"])

        self.assertEqual(len(data["medications"]), 1)
        self.assertIn("Augmentin", data["medications"][0]["medication"])

    def test_case_4_duplicate_medication(self):
        """Test Case 4: Prescription containing duplicate medication / NSAID duplication (RX-1004: Ibuprofen + Naproxen)."""
        result = get_prescription("RX-1004")
        self.assertEqual(result["status"], "success")
        data = result["data"]

        self.assertEqual(data["prescription_id"], "RX-1004")
        self.assertEqual(data["patient"]["name"], "Emily Davis")
        self.assertIn("Osteoarthritis", data["diagnoses"][0]["diagnosis"])

        meds = data["medications"]
        self.assertEqual(len(meds), 2)
        med_names = [m["medication"] for m in meds]
        self.assertIn("Ibuprofen", med_names)
        self.assertIn("Naproxen", med_names)

    def test_case_5_multiple_medications(self):
        """Test Case 5: Prescription containing multiple medications (RX-1005: 4-drug regimen)."""
        result = get_prescription("RX-1005")
        self.assertEqual(result["status"], "success")
        data = result["data"]

        self.assertEqual(data["prescription_id"], "RX-1005")
        self.assertEqual(data["patient"]["name"], "Michael Chen")
        self.assertEqual(data["patient"]["age"], 68)

        meds = data["medications"]
        self.assertEqual(len(meds), 4)
        med_names = [m["medication"] for m in meds]
        self.assertTrue(any("Atorvastatin" in n for n in med_names))
        self.assertTrue(any("Metformin" in n for n in med_names))
        self.assertTrue(any("Lisinopril" in n for n in med_names))
        self.assertTrue(any("Amlodipine" in n for n in med_names))

    def test_nonexistent_prescription_id(self):
        """Test lookup for non-existent prescription ID."""
        result = get_prescription("RX-9999")
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["data"])
        self.assertIn("not found", result["message"].lower())

    def test_empty_or_invalid_prescription_id(self):
        """Test lookup with empty or non-string prescription ID."""
        result_empty = get_prescription("")
        self.assertEqual(result_empty["status"], "error")
        self.assertIsNone(result_empty["data"])

        result_spaces = get_prescription("   ")
        self.assertEqual(result_spaces["status"], "error")
        self.assertIsNone(result_spaces["data"])

    def test_isolated_custom_database_path(self):
        """Verify database initialization and query work with an isolated temporary database path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_db = os.path.join(tmp_dir, "custom_pharmacy.db")
            initialize_database(temp_db)
            record = fetch_prescription_details("RX-1001", db_path=temp_db)
            self.assertIsNotNone(record)
            self.assertEqual(record["prescription_id"], "RX-1001")
            self.assertEqual(record["patient"]["name"], "John Doe")


if __name__ == "__main__":
    unittest.main()
