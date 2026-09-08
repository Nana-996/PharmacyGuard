"""
Unit and Integration Tests for PharmacyGuard Phase 3:
1. Two-Level Chief Pharmacist Escalation Resolution & Audit Trail Isolation
2. Pharmacy Intern / Student Educational Cases & Progress Tracking
3. Real Inventory Dispensing, Stock Decrementation, and Transaction Logging
"""

import os
import unittest
import tempfile
import sqlite3
import json
from fastapi.testclient import TestClient

from backend.main import app
from backend.data.database import (
    initialize_database,
    get_db_connection,
    fetch_review_by_id,
    fetch_escalation_resolutions,
    fetch_educational_cases,
    fetch_educational_case_by_id,
    fetch_student_progress,
    fetch_inventory_transactions,
    insert_pharmacist_review,
    create_or_update_patient,
    create_prescription_case
)
from backend.services.review_service import (
    create_review,
    escalate_review,
    accept_review,
    resolve_chief_escalation,
    dispense_review_prescription
)
from backend.auth.security import create_access_token
from backend.agent.pharmacy_agent import AgentStructuredReview, AgentFinding


class TestPhase3Workflows(unittest.TestCase):

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        os.environ["PHARMACYGUARD_DB_PATH"] = self.db_path
        initialize_database(self.db_path, force_reseed=True)

        self.client = TestClient(app)

        # Tokens
        self.staff_token = create_access_token({
            "sub": "USR-STAFF-001",
            "email": "staff.pharmacist@hospital.dev",
            "role": "STAFF_PHARMACIST"
        })
        self.chief_token = create_access_token({
            "sub": "USR-CHIEF-001",
            "email": "chief.pharmacist@hospital.dev",
            "role": "CHIEF_PHARMACIST"
        })
        self.student_token = create_access_token({
            "sub": "USR-STUD-001",
            "email": "student@hospital.dev",
            "role": "PHARMACY_STUDENT"
        })

        self.staff_headers = {"Authorization": f"Bearer {self.staff_token}"}
        self.chief_headers = {"Authorization": f"Bearer {self.chief_token}"}
        self.student_headers = {"Authorization": f"Bearer {self.student_token}"}

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_01_two_level_chief_escalation_resolution_preserves_pharmacist_decision(self):
        """
        Verifies that when a Chief Pharmacist resolves an escalation:
        1. Original staff pharmacist's reviewed_by and decision='ESCALATED' remain permanently preserved in pharmacist_reviews.
        2. Chief decision is saved in escalation_resolutions table.
        3. ESCALATION_RESOLVED audit log is recorded with Chief user ID.
        """
        # 1. Staff Pharmacist escalates RX-1003
        fake_review = AgentStructuredReview(
            prescription_id="RX-1003",
            overall_status="HIGH_PRIORITY_REVIEW",
            findings=[
                AgentFinding(
                    category="ALLERGY",
                    severity="HIGH",
                    title="Penicillin Allergy Conflict",
                    description="Augmentin contains Amoxicillin, contraindicated in Penicillin allergy.",
                    evidence_source="allergy_check",
                    evidence="Patient has documented Penicillin allergy.",
                    requires_action=True
                )
            ],
            summary="Allergy conflict detected.",
            pharmacist_action_summary="Contraindicated.",
            raw_agent_response="Severe allergy conflict on Augmentin."
        )
        rev = create_review("RX-1003", structured_review=fake_review, db_path=self.db_path)
        rev_id = rev["review_id"]

        # Staff pharmacist escalates
        esc_res = self.client.post(
            f"/api/reviews/{rev_id}/escalate",
            json={"notes": "Complex allergy history with anaphylaxis. Requesting Chief guidance."},
            headers=self.staff_headers
        )
        self.assertEqual(esc_res.status_code, 200)

        # Verify staff decision is ESCALATED
        review_before = fetch_review_by_id(rev_id, db_path=self.db_path)
        self.assertEqual(review_before["pharmacist_decision"], "ESCALATED")
        self.assertEqual(review_before["reviewed_by"], "USR-STAFF-001")
        self.assertIn("Complex allergy history", review_before["pharmacist_notes"])

        # 2. Staff Pharmacist CANNOT resolve escalation (RBAC check)
        forbidden_res = self.client.post(
            f"/api/reviews/{rev_id}/resolve-escalation",
            json={
                "chief_decision": "RESOLVED_APPROVED",
                "chief_notes": "Attempting unauthorized resolution"
            },
            headers=self.staff_headers
        )
        self.assertEqual(forbidden_res.status_code, 403)

        # 3. Chief Pharmacist resolves escalation with RESOLVED_APPROVED
        resolve_res = self.client.post(
            f"/api/reviews/{rev_id}/resolve-escalation",
            json={
                "chief_decision": "RESOLVED_APPROVED",
                "chief_notes": "Reviewed immunology consult. Confirmed cross-reactivity risk. Approved substitution with Doxycycline 100mg BID.",
                "action_required": "Notify prescriber and switch medication to non-beta-lactam."
            },
            headers=self.chief_headers
        )
        self.assertEqual(resolve_res.status_code, 200)
        res_data = resolve_res.json()
        self.assertEqual(res_data["resolution"]["chief_decision"], "RESOLVED_APPROVED")
        self.assertEqual(res_data["resolution"]["chief_id"], "USR-CHIEF-001")

        # 4. CRITICAL CHECK: Staff decision is STILL 'ESCALATED' and reviewed_by is STILL 'USR-STAFF-001'
        review_after = fetch_review_by_id(rev_id, db_path=self.db_path)
        self.assertEqual(review_after["pharmacist_decision"], "ESCALATED")
        self.assertEqual(review_after["reviewed_by"], "USR-STAFF-001")
        self.assertEqual(len(review_after["escalation_resolutions"]), 1)
        self.assertEqual(review_after["escalation_resolutions"][0]["chief_decision"], "RESOLVED_APPROVED")
        self.assertEqual(review_after["escalation_resolutions"][0]["chief_id"], "USR-CHIEF-001")

        # 5. Verify audit log entry
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM audit_log WHERE review_id = ? AND event_type = 'ESCALATION_RESOLVED'", (rev_id,))
        audit_row = cur.fetchone()
        self.assertIsNotNone(audit_row)
        self.assertEqual(audit_row["actor_id"], "USR-CHIEF-001")
        conn.close()

    def test_02_chief_pharmacist_return_to_staff_workflow(self):
        """Tests Chief Pharmacist returning an escalated case with specific directives."""
        fake_review = AgentStructuredReview(
            prescription_id="RX-1002",
            overall_status="REVIEW",
            findings=[],
            summary="Lisinopril diabetes case.",
            pharmacist_action_summary="Verify indications.",
            raw_agent_response="Check indication."
        )
        rev = create_review("RX-1002", structured_review=fake_review, db_path=self.db_path)
        rev_id = rev["review_id"]

        # Escalate
        self.client.post(
            f"/api/reviews/{rev_id}/escalate",
            json={"notes": "Unclear indication for Lisinopril in diabetes."},
            headers=self.staff_headers
        )

        # Return to staff
        return_res = self.client.post(
            f"/api/reviews/{rev_id}/resolve-escalation",
            json={
                "chief_decision": "RETURNED_TO_STAFF",
                "chief_notes": "Please verify patient's recent urinary microalbumin levels before finalizing.",
                "action_required": "Request urine albumin-to-creatinine ratio (UACR) from attending physician."
            },
            headers=self.chief_headers
        )
        self.assertEqual(return_res.status_code, 200)

        resolutions = fetch_escalation_resolutions(review_id=rev_id, db_path=self.db_path)
        self.assertEqual(len(resolutions), 1)
        self.assertEqual(resolutions[0]["chief_decision"], "RETURNED_TO_STAFF")
        self.assertEqual(resolutions[0]["action_required"], "Request urine albumin-to-creatinine ratio (UACR) from attending physician.")

    def test_03_student_learning_cases_and_progress_tracking(self):
        """Tests the Pharmacy Student training portal, answer submission, and progress tracking."""
        # 1. Student lists cases
        cases_res = self.client.get("/api/student/cases", headers=self.student_headers)
        self.assertEqual(cases_res.status_code, 200)
        cases = cases_res.json()["data"]
        self.assertGreaterEqual(len(cases), 4)

        target_case = cases[0]
        case_id = target_case["case_id"]
        correct_index = target_case["correct_option_index"]

        # 2. Student submits correct answer
        submit_res = self.client.post(
            f"/api/student/cases/{case_id}/submit",
            json={
                "selected_option_index": correct_index,
                "student_notes": "Cross-reactivity between beta-lactams requires non-penicillin alternative."
            },
            headers=self.student_headers
        )
        self.assertEqual(submit_res.status_code, 200)
        sub_data = submit_res.json()
        self.assertTrue(sub_data["is_correct"])
        self.assertIn("explanation_text", sub_data)

        # 3. Student fetches progress
        prog_res = self.client.get("/api/student/progress", headers=self.student_headers)
        self.assertEqual(prog_res.status_code, 200)
        prog_data = prog_res.json()["data"]
        self.assertEqual(prog_data["student_id"], "USR-STUD-001")
        self.assertGreaterEqual(prog_data["completed_cases"], 1)
        self.assertEqual(prog_data["correct_submissions"], 1)

    def test_04_real_inventory_dispensing_decrements_sqlite_and_logs_transactions(self):
        """
        Verifies that dispensing an accepted prescription:
        1. Decrements physical stock in the SQLite inventory table.
        2. Inserts an immutable transaction into inventory_transactions.
        3. Emits PRESCRIPTION_DISPENSED in the audit trail.
        """
        fake_review = AgentStructuredReview(
            prescription_id="RX-1001",
            overall_status="CLEAR",
            findings=[],
            summary="Routine Strep case.",
            pharmacist_action_summary="Clean.",
            raw_agent_response="Clean."
        )
        rev = create_review("RX-1001", structured_review=fake_review, db_path=self.db_path)
        rev_id = rev["review_id"]

        # 1. Accept the review
        accept_res = self.client.post(f"/api/reviews/{rev_id}/accept", json={"notes": "Order verified"}, headers=self.staff_headers)
        self.assertEqual(accept_res.status_code, 200)

        # 2. Get Amoxicillin initial stock
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT quantity_on_hand FROM inventory WHERE generic_name = 'Amoxicillin'")
        initial_qty = cur.fetchone()["quantity_on_hand"]
        conn.close()

        # 3. Dispense prescription
        dispense_res = self.client.post(
            f"/api/reviews/{rev_id}/dispense",
            json={"notes": "Dispensed 30 capsules, lot #AMX-9021."},
            headers=self.staff_headers
        )
        if dispense_res.status_code != 200:
            print("DISPENSE ERROR:", dispense_res.status_code, dispense_res.text)
        self.assertEqual(dispense_res.status_code, 200, f"Dispense failed: {dispense_res.text}")
        disp_data = dispense_res.json()["data"]

        self.assertEqual(disp_data["status"], "DISPENSED")

        # 4. Verify inventory quantity decreased in SQLite
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT quantity_on_hand FROM inventory WHERE generic_name = 'Amoxicillin'")
        updated_qty = cur.fetchone()["quantity_on_hand"]
        self.assertEqual(updated_qty, initial_qty - 30)

        # 5. Verify inventory_transactions entry
        cur.execute("SELECT * FROM inventory_transactions WHERE prescription_id = 'RX-1001'")
        tx = cur.fetchone()
        self.assertIsNotNone(tx)
        self.assertEqual(tx["transaction_type"], "DISPENSED")
        self.assertEqual(tx["quantity_change"], -30)
        self.assertEqual(tx["actor_id"], "USR-STAFF-001")

        # 6. Verify audit log entry
        cur.execute("SELECT * FROM audit_log WHERE prescription_id = 'RX-1001' AND event_type = 'PRESCRIPTION_DISPENSED'")
        audit = cur.fetchone()
        self.assertIsNotNone(audit)
        conn.close()


if __name__ == "__main__":
    unittest.main()
