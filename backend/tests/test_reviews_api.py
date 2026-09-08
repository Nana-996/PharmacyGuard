"""
Automated integration tests for PharmacyGuard Pharmacist Review API Endpoints.
Uses FastAPI TestClient to verify all HTTP routes and review workflows.
"""

import os
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.data.database import initialize_database
from backend.agent.pharmacy_agent import AgentFinding, AgentStructuredReview


class TestReviewsAPI(unittest.TestCase):
    """Integration test suite for the /api/reviews REST API endpoints."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()

        os.environ["PHARMACYGUARD_DB_PATH"] = self.temp_db_path
        initialize_database(db_path=self.temp_db_path)
        self.client = TestClient(app)

        from backend.auth.security import create_access_token
        self.token = create_access_token({
            "sub": "USR-STAFF-001",
            "role": "STAFF_PHARMACIST",
            "email": "staff.pharmacist@hospital.dev"
        })
        self.headers = {"Authorization": f"Bearer {self.token}"}

        self.mock_review = AgentStructuredReview(
            prescription_id="RX-1001",
            overall_status="CLEAR",
            findings=[
                AgentFinding(
                    category="CLINICAL",
                    severity="NONE",
                    title="Diagnosis Match",
                    description="Amoxicillin aligns with Strep throat.",
                    evidence_source="diagnosis_medication_check",
                    evidence="MATCH",
                    requires_action=False
                )
            ],
            pharmacist_action_summary="Routine antibiotic prescription. All checks clear."
        )

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    @patch("backend.services.review_service.run_structured_prescription_review")
    def test_post_create_review_endpoint(self, mock_agent_run):
        """Test POST /api/reviews triggers agent review and returns 201 with PENDING decision."""
        mock_agent_run.return_value = self.mock_review

        res = self.client.post("/api/reviews", json={"prescription_id": "RX-1001"}, headers=self.headers)
        self.assertEqual(res.status_code, 201)

        body = res.json()
        self.assertEqual(body["status"], "success")
        data = body["data"]
        self.assertTrue(data["review_id"].startswith("REV-"))
        self.assertEqual(data["prescription_id"], "RX-1001")
        self.assertEqual(data["agent_review_status"], "CLEAR")
        self.assertEqual(data["pharmacist_decision"], "PENDING")
        self.assertEqual(len(data["findings"]), 1)
        self.assertGreaterEqual(len(data["audit_history"]), 2)

    @patch("backend.services.review_service.run_structured_prescription_review")
    def test_get_reviews_and_pending_endpoints(self, mock_agent_run):
        """Test GET /api/reviews and GET /api/reviews/pending."""
        mock_agent_run.return_value = self.mock_review

        # Create two reviews
        create_res1 = self.client.post("/api/reviews", json={"prescription_id": "RX-1001"}, headers=self.headers)
        rev_id_1 = create_res1.json()["data"]["review_id"]

        mock_agent_run.return_value = AgentStructuredReview(
            prescription_id="RX-1002",
            overall_status="REVIEW",
            findings=[],
            pharmacist_action_summary="Review indication."
        )
        create_res2 = self.client.post("/api/reviews", json={"prescription_id": "RX-1002"}, headers=self.headers)
        rev_id_2 = create_res2.json()["data"]["review_id"]

        # List all
        list_res = self.client.get("/api/reviews", headers=self.headers)
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(list_res.json()["total"], 2)

        # List pending
        pending_res = self.client.get("/api/reviews/pending", headers=self.headers)
        self.assertEqual(pending_res.status_code, 200)
        self.assertEqual(pending_res.json()["total_pending"], 2)

        # Accept the first review
        accept_res = self.client.post(
            f"/api/reviews/{rev_id_1}/accept",
            json={"pharmacist_id": "PHARM-101", "notes": "Approved."},
            headers=self.headers
        )
        self.assertEqual(accept_res.status_code, 200)
        self.assertEqual(accept_res.json()["data"]["pharmacist_decision"], "ACCEPTED")

        # Check pending again -> should now be 1
        pending_after = self.client.get("/api/reviews/pending", headers=self.headers)
        self.assertEqual(pending_after.json()["total_pending"], 1)
        self.assertEqual(pending_after.json()["data"][0]["review_id"], rev_id_2)

    @patch("backend.services.review_service.run_structured_prescription_review")
    def test_get_review_by_id_endpoint(self, mock_agent_run):
        """Test GET /api/reviews/{review_id} returns full prescription case, findings, and audit trail."""
        mock_agent_run.return_value = self.mock_review
        create_res = self.client.post("/api/reviews", json={"prescription_id": "RX-1001"}, headers=self.headers)
        rev_id = create_res.json()["data"]["review_id"]

        res = self.client.get(f"/api/reviews/{rev_id}", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["review_id"], rev_id)
        self.assertEqual(data["prescription_details"]["patient"]["name"], "John Doe")
        self.assertEqual(len(data["findings"]), 1)

    @patch("backend.services.review_service.run_structured_prescription_review")
    def test_post_override_review_endpoint(self, mock_agent_run):
        """Test POST /api/reviews/{review_id}/override transitions status and records notes."""
        mock_agent_run.return_value = self.mock_review
        create_res = self.client.post("/api/reviews", json={"prescription_id": "RX-1001"}, headers=self.headers)
        rev_id = create_res.json()["data"]["review_id"]

        override_res = self.client.post(
            f"/api/reviews/{rev_id}/override",
            json={
                "notes": "Patient reports previously unrecorded allergy symptoms to Penicillin during intake."
            },
            headers=self.headers
        )
        self.assertEqual(override_res.status_code, 200)
        data = override_res.json()["data"]
        self.assertEqual(data["pharmacist_decision"], "OVERRIDDEN")
        self.assertEqual(data["reviewed_by"], "USR-STAFF-001")
        self.assertIn("unrecorded allergy", data["pharmacist_notes"])

    @patch("backend.services.review_service.run_structured_prescription_review")
    def test_post_escalate_review_endpoint(self, mock_agent_run):
        """Test POST /api/reviews/{review_id}/escalate transitions status to ESCALATED."""
        mock_agent_run.return_value = self.mock_review
        create_res = self.client.post("/api/reviews", json={"prescription_id": "RX-1001"}, headers=self.headers)
        rev_id = create_res.json()["data"]["review_id"]

        escalate_res = self.client.post(
            f"/api/reviews/{rev_id}/escalate",
            json={
                "notes": "Unusual dosage discrepancy; escalating to chief clinical pharmacist for verification."
            },
            headers=self.headers
        )
        self.assertEqual(escalate_res.status_code, 200)
        data = escalate_res.json()["data"]
        self.assertEqual(data["pharmacist_decision"], "ESCALATED")
        self.assertEqual(data["reviewed_by"], "USR-STAFF-001")
        self.assertIn("chief clinical pharmacist", data["pharmacist_notes"])

    def test_404_for_nonexistent_review(self):
        """Test 404 response when requesting non-existent review ID."""
        res = self.client.get("/api/reviews/REV-NONEXISTENT", headers=self.headers)
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()

