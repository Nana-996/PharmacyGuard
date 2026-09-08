"""
Unit and Integration Tests for Phase 2:
- Pharmacist Prescription Editing & Ingestion
- AI Safety Findings Transmittal to Prescribing Physician
- Custom Pharmacist Clinical Report to Prescribing Physician
- Persistence in SQLite and Immutable Audit Logs
"""

import os
import unittest
import tempfile
import json
from fastapi.testclient import TestClient

from backend.main import app
from backend.data.database import (
    initialize_database,
    fetch_prescription_details,
    fetch_prescriber_communications,
    get_db_connection
)
from backend.auth.security import create_access_token


class TestPrescriptionEntryAndPrescriberReports(unittest.TestCase):
    """Integration test suite for prescription modification and prescriber reporting."""

    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.db_path = cls.temp_db.name
        cls.temp_db.close()
        os.environ["PHARMACYGUARD_DB_PATH"] = cls.db_path
        initialize_database(cls.db_path, force_reseed=True)
        cls.client = TestClient(app)

        # Tokens
        cls.staff_token = create_access_token({
            "sub": "USR-STAFF-001",
            "email": "staff.pharmacist@hospital.dev",
            "role": "STAFF_PHARMACIST",
            "full_name": "Dr. Alex Reed, PharmD"
        })
        cls.staff_headers = {"Authorization": f"Bearer {cls.staff_token}"}

        cls.student_token = create_access_token({
            "sub": "USR-STUD-001",
            "email": "student@hospital.dev",
            "role": "PHARMACY_STUDENT",
            "full_name": "Sam Taylor"
        })
        cls.student_headers = {"Authorization": f"Bearer {cls.student_token}"}

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            try:
                os.remove(cls.db_path)
            except Exception:
                pass

    def test_01_create_new_prescription_and_persist_in_sqlite(self):
        """Tests pharmacist entering a new clinical prescription with multiple medications."""
        payload = {
            "patient_name": "Kofi Mensah",
            "patient_age": 42,
            "patient_sex": "Male",
            "patient_allergies": "Penicillin (Severe anaphylaxis)",
            "diagnosis": "Community-Acquired Pneumonia",
            "prescribing_doctor": "Dr. Sarah Adams, MD (Internal Medicine)",
            "prescription_id": "RX-2001",
            "medications": [
                {
                    "medication": "Azithromycin",
                    "strength": "500mg",
                    "dosage": "1 tablet (500mg)",
                    "frequency": "Once daily",
                    "route": "Oral",
                    "duration": "3 days"
                }
            ],
            "auto_trigger_review": False
        }
        res = self.client.post("/api/prescriptions", json=payload, headers=self.staff_headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["prescription"]["prescription_id"], "RX-2001")
        self.assertEqual(len(data["prescription"]["medications"]), 1)

        # Verify persisted in SQLite
        persisted = fetch_prescription_details("RX-2001", db_path=self.db_path)
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted["patient"]["name"], "Kofi Mensah")
        self.assertEqual(persisted["patient"]["allergies"], "Penicillin (Severe anaphylaxis)")
        self.assertEqual(persisted["medications"][0]["medication"], "Azithromycin")

    def test_02_edit_existing_prescription_modifies_sqlite(self):
        """Tests pharmacist editing a doctor's prescription (e.g. changing strength or swapping drugs)."""
        edit_payload = {
            "medications": [
                {
                    "medication": "Ibuprofen",
                    "strength": "200mg",
                    "dosage": "1 tablet (200mg)",
                    "frequency": "Every 8 hours with food",
                    "route": "Oral",
                    "duration": "5 days"
                }
            ],
            "modification_notes": "Adjusted dosage to 200mg tablets due to 600mg stock shortage.",
            "auto_trigger_re_review": False
        }
        res = self.client.patch("/api/prescriptions/RX-1003", json=edit_payload, headers=self.staff_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["medications"][0]["strength"], "200mg")

        # Verify SQLite state updated
        updated_rx = fetch_prescription_details("RX-1003", db_path=self.db_path)
        self.assertEqual(updated_rx["medications"][0]["strength"], "200mg")

        # Verify PRESCRIPTION_MODIFIED audit event logged
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT event_type, actor_id, prescription_id FROM audit_log WHERE event_type = 'PRESCRIPTION_MODIFIED' AND prescription_id = 'RX-1003'")
        audit_row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(audit_row)
        self.assertEqual(audit_row["actor_id"], "USR-STAFF-001")

    def test_03_send_ai_findings_report_to_prescriber(self):
        """Tests pharmacist sending an AI findings summary report to the prescribing doctor."""
        # Create a dummy review first
        from backend.services.review_service import create_review
        from backend.agent.pharmacy_agent import AgentStructuredReview, AgentFinding

        fake_review = AgentStructuredReview(
            prescription_id="RX-1001",
            overall_status="HIGH_PRIORITY_REVIEW",
            findings=[
                AgentFinding(
                    category="ALLERGY",
                    severity="HIGH",
                    title="Penicillin Cross-Reactivity Risk",
                    description="Augmentin contains amoxicillin, contraindicated in penicillin allergy.",
                    evidence_source="Patient Record & Allergen Knowledge Base",
                    evidence="Patient has documented Penicillin allergy; Augmentin is a beta-lactam penicillin.",
                    requires_action=True
                )
            ],
            summary="Allergy conflict detected.",
            pharmacist_action_summary="Augmentin is contraindicated for Penicillin-allergic patient.",
            raw_agent_response="Augmentin is contraindicated for Penicillin-allergic patient."
        )
        review = create_review("RX-1001", structured_review=fake_review, db_path=self.db_path)
        review_id = review["review_id"]

        report_payload = {
            "recipient_doctor": "Dr. Sarah Adams, MD",
            "report_type": "AI_FINDINGS_REPORT",
            "subject": "[URGENT CLINICAL QUERY] Drug Conflict Detected on RX-1001",
            "message_body": "Please review the attached AI clinical safety alerts regarding severe allergen conflict on this patient.",
            "ai_findings_included": [
                {
                    "category": "ALLERGY",
                    "severity": "HIGH",
                    "title": "Penicillin Cross-Reactivity Risk",
                    "description": "Augmentin contains amoxicillin, contraindicated in penicillin allergy."
                }
            ]
        }

        res = self.client.post(
            f"/api/reviews/{review_id}/send-prescriber-report",
            json=report_payload,
            headers=self.staff_headers
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["recipient_doctor"], "Dr. Sarah Adams, MD")
        self.assertEqual(data["data"]["report_type"], "AI_FINDINGS_REPORT")

        # Verify persisted in SQLite prescriber_communications
        comms = fetch_prescriber_communications(review_id=review_id, db_path=self.db_path)
        self.assertEqual(len(comms), 1)
        self.assertEqual(comms[0]["subject"], "[URGENT CLINICAL QUERY] Drug Conflict Detected on RX-1001")
        self.assertEqual(comms[0]["sender_id"], "USR-STAFF-001")

        # Verify audit log recorded PRESCRIBER_CONSULTATION_SENT
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT event_type, actor_id FROM audit_log WHERE event_type = 'PRESCRIBER_CONSULTATION_SENT'")
        audit_row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(audit_row)
        self.assertEqual(audit_row["actor_id"], "USR-STAFF-001")

    def test_04_send_custom_pharmacist_report_to_prescriber(self):
        """Tests pharmacist composing and sending their own custom clinical consultation report."""
        from backend.services.review_service import create_review
        from backend.agent.pharmacy_agent import AgentStructuredReview

        fake_review = AgentStructuredReview(
            prescription_id="RX-1002",
            overall_status="REVIEW",
            findings=[],
            summary="Clean review.",
            pharmacist_action_summary="Standard antibiotic review.",
            raw_agent_response="Standard antibiotic review."
        )
        review = create_review("RX-1002", structured_review=fake_review, db_path=self.db_path)
        review_id = review["review_id"]

        custom_report = {
            "recipient_doctor": "Dr. Marcus Vance, MD",
            "report_type": "CUSTOM_PHARMACIST_REPORT",
            "subject": "Clinical Clarification: Indication for Lisinopril 20mg",
            "message_body": "Patient's primary recorded diagnosis is Type 2 Diabetes without documented hypertension or proteinuria. Could you confirm if this is for renal protection or if diagnosis code should be updated to Essential Hypertension?",
            "suggested_modifications": [
                {
                    "medication": "Lisinopril",
                    "strength": "10mg",
                    "dosage": "1 tablet (10mg)",
                    "frequency": "Once daily in morning",
                    "route": "Oral",
                    "duration": "30 days"
                }
            ]
        }

        res = self.client.post(
            f"/api/reviews/{review_id}/send-prescriber-report",
            json=custom_report,
            headers=self.staff_headers
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["report_type"], "CUSTOM_PHARMACIST_REPORT")

        # Verify retrieved in review details
        res_review = self.client.get(f"/api/reviews/{review_id}", headers=self.staff_headers)
        self.assertEqual(res_review.status_code, 200)
        review_data = res_review.json()["data"]
        self.assertIn("prescriber_communications", review_data)
        self.assertEqual(len(review_data["prescriber_communications"]), 1)
        self.assertEqual(review_data["prescriber_communications"][0]["recipient_doctor"], "Dr. Marcus Vance, MD")

    def test_05_student_cannot_edit_prescriptions_or_send_reports(self):
        """Verifies pharmacy students receive HTTP 403 when attempting prescription editing or sending doctor reports."""
        edit_payload = {
            "medications": [{"medication": "Amoxicillin", "strength": "500mg", "dosage": "1 cap", "frequency": "TID", "route": "Oral", "duration": "7d"}]
        }
        res_edit = self.client.patch("/api/prescriptions/RX-1001", json=edit_payload, headers=self.student_headers)
        self.assertEqual(res_edit.status_code, 403)

        report_payload = {
            "recipient_doctor": "Dr. Sarah Adams",
            "subject": "Test",
            "message_body": "Student attempt."
        }
        res_report = self.client.post("/api/reviews/REV-FAKE/send-prescriber-report", json=report_payload, headers=self.student_headers)
        self.assertEqual(res_report.status_code, 403)


if __name__ == "__main__":
    unittest.main()
