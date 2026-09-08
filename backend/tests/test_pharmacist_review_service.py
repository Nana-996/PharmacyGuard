"""
Unit and integration tests for Pharmacist Review Service, Persistence, Decision Workflows,
and Audit Trails in PharmacyGuard.
"""

import os
import tempfile
import unittest
from backend.data.database import initialize_database, get_db_connection
from backend.agent.pharmacy_agent import AgentFinding, AgentStructuredReview, _extract_json_from_agent_response
from backend.services.review_service import (
    create_review,
    get_pending_reviews,
    get_all_reviews_service,
    get_review,
    accept_review,
    override_review,
    escalate_review,
)


class TestPharmacistReviewService(unittest.TestCase):
    """Test suite for human pharmacist review lifecycle, findings persistence, and audit logs."""

    def setUp(self):
        # Create isolated temporary database for each test to guarantee test independence
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        initialize_database(db_path=self.temp_db_path)

        # Sample structured review matching agent output schema
        self.sample_review_data = AgentStructuredReview(
            prescription_id="RX-1004",
            overall_status="HIGH_PRIORITY_REVIEW",
            findings=[
                AgentFinding(
                    category="DUPLICATION",
                    severity="HIGH",
                    title="Dual NSAID Therapy",
                    description="Ibuprofen 600mg + Naproxen 500mg prescribed simultaneously.",
                    evidence_source="duplicate_medication_check",
                    evidence="Therapeutic duplicate: Ibuprofen + Naproxen",
                    requires_action=True
                ),
                AgentFinding(
                    category="INTERACTION",
                    severity="HIGH",
                    title="Major NSAID Interaction",
                    description="Additive COX-1/COX-2 inhibition increases severe GI bleeding risk.",
                    evidence_source="medication_interaction_check",
                    evidence="Major interaction between Ibuprofen and Naproxen",
                    requires_action=True
                ),
                AgentFinding(
                    category="INVENTORY",
                    severity="HIGH",
                    title="Ibuprofen 600mg Out of Stock",
                    description="0 tablets available on hand.",
                    evidence_source="check_inventory",
                    evidence="OUT OF STOCK: 0 tablets available (reorder: 50).",
                    requires_action=True
                )
            ],
            pharmacist_action_summary="Contact Dr. Kevin Patel regarding dual NSAID duplication and out of stock 600mg strength."
        )

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    # --- 1. Review Creation & Initial PENDING State ---
    def test_create_review_starts_with_pending_decision(self):
        """Verify new reviews start with pharmacist_decision = PENDING."""
        review = create_review("RX-1004", structured_review=self.sample_review_data, db_path=self.temp_db_path)
        self.assertIsNotNone(review)
        self.assertTrue(review["review_id"].startswith("REV-"))
        self.assertEqual(review["prescription_id"], "RX-1004")
        self.assertEqual(review["agent_review_status"], "HIGH_PRIORITY_REVIEW")
        self.assertEqual(review["pharmacist_decision"], "PENDING")
        self.assertIsNone(review["reviewed_by"])
        self.assertIsNone(review["reviewed_at"])
        self.assertIsNone(review["pharmacist_notes"])

    # --- 2. Findings Persistence ---
    def test_agent_findings_persisted_with_actual_evidence_sources(self):
        """Verify structured findings are persisted linked to the review with real evidence sources."""
        review = create_review("RX-1004", structured_review=self.sample_review_data, db_path=self.temp_db_path)
        findings = review["findings"]
        self.assertEqual(len(findings), 3)

        sources = [f["evidence_source"] for f in findings]
        self.assertIn("duplicate_medication_check", sources)
        self.assertIn("medication_interaction_check", sources)
        self.assertIn("check_inventory", sources)

        categories = [f["category"] for f in findings]
        self.assertIn("DUPLICATION", categories)
        self.assertIn("INTERACTION", categories)
        self.assertIn("INVENTORY", categories)

        for f in findings:
            self.assertEqual(f["review_id"], review["review_id"])
            self.assertTrue(f["finding_id"].startswith("FND-"))
            self.assertTrue(f["requires_action"])

    # --- 3. Pharmacist Action: ACCEPT ---
    def test_pharmacist_can_accept_review(self):
        """Verify human pharmacist can ACCEPT a pending review."""
        review = create_review("RX-1004", structured_review=self.sample_review_data, db_path=self.temp_db_path)
        rev_id = review["review_id"]

        updated = accept_review(
            review_id=rev_id,
            pharmacist_id="PHARM-101",
            notes="Contacted Dr. Patel. Discontinuing Naproxen; keeping Ibuprofen with alternative dosing.",
            db_path=self.temp_db_path
        )

        self.assertEqual(updated["pharmacist_decision"], "ACCEPTED")
        self.assertEqual(updated["reviewed_by"], "PHARM-101")
        self.assertIsNotNone(updated["reviewed_at"])
        self.assertIn("Discontinuing Naproxen", updated["pharmacist_notes"])

    # --- 4. Pharmacist Action: OVERRIDE ---
    def test_pharmacist_can_override_review(self):
        """Verify human pharmacist can OVERRIDE agent findings with clinical rationale."""
        review = create_review("RX-1004", structured_review=self.sample_review_data, db_path=self.temp_db_path)
        rev_id = review["review_id"]

        updated = override_review(
            review_id=rev_id,
            pharmacist_id="PHARM-202",
            notes="Patient has specific orthopedic protocol requiring staggered low-dose NSAID transition under close monitoring.",
            db_path=self.temp_db_path
        )

        self.assertEqual(updated["pharmacist_decision"], "OVERRIDDEN")
        self.assertEqual(updated["reviewed_by"], "PHARM-202")
        self.assertIn("orthopedic protocol", updated["pharmacist_notes"])

    # --- 5. Pharmacist Action: ESCALATE ---
    def test_pharmacist_can_escalate_review(self):
        """Verify human pharmacist can ESCALATE complex prescription to chief pharmacist."""
        review = create_review("RX-1004", structured_review=self.sample_review_data, db_path=self.temp_db_path)
        rev_id = review["review_id"]

        updated = escalate_review(
            review_id=rev_id,
            pharmacist_id="PHARM-303",
            notes="Prescribing provider unavailable; severe dual NSAID interaction in patient with history of gastritis requires Chief Pharmacist review.",
            db_path=self.temp_db_path
        )

        self.assertEqual(updated["pharmacist_decision"], "ESCALATED")
        self.assertEqual(updated["reviewed_by"], "PHARM-303")
        self.assertIn("Chief Pharmacist", updated["pharmacist_notes"])

    # --- 6. Audit Trail Creation ---
    def test_audit_records_created_for_agent_and_pharmacist_events(self):
        """Verify immutable audit log events are recorded with proper actor types and timestamps."""
        review = create_review("RX-1004", structured_review=self.sample_review_data, db_path=self.temp_db_path)
        rev_id = review["review_id"]

        accept_review(
            review_id=rev_id,
            pharmacist_id="PHARM-101",
            notes="Approved after prescriber call.",
            db_path=self.temp_db_path
        )

        full_review = get_review(rev_id, db_path=self.temp_db_path)
        audit_history = full_review["audit_history"]

        # Expect: 3 FINDING_CREATED, 1 AGENT_REVIEW_CREATED, 1 PHARMACIST_REVIEWED
        event_types = [a["event_type"] for a in audit_history]
        actor_types = [a["actor_type"] for a in audit_history]

        self.assertIn("AGENT_REVIEW_CREATED", event_types)
        self.assertIn("FINDING_CREATED", event_types)
        self.assertIn("PHARMACIST_REVIEWED", event_types)

        self.assertIn("AGENT", actor_types)
        self.assertIn("PHARMACIST", actor_types)

    # --- 7. Pending Queue Filtering ---
    def test_get_pending_reviews_filtering(self):
        """Verify get_pending_reviews only returns reviews where pharmacist_decision == PENDING."""
        rev1 = create_review("RX-1001", structured_review=AgentStructuredReview(
            prescription_id="RX-1001",
            overall_status="CLEAR",
            findings=[],
            pharmacist_action_summary="No issues detected."
        ), db_path=self.temp_db_path)

        rev2 = create_review("RX-1002", structured_review=AgentStructuredReview(
            prescription_id="RX-1002",
            overall_status="REVIEW",
            findings=[],
            pharmacist_action_summary="Check indication."
        ), db_path=self.temp_db_path)

        pending = get_pending_reviews(db_path=self.temp_db_path)
        self.assertEqual(len(pending), 2)

        # Accept rev1
        accept_review(rev1["review_id"], pharmacist_id="PHARM-001", notes="OK", db_path=self.temp_db_path)

        pending_after = get_pending_reviews(db_path=self.temp_db_path)
        self.assertEqual(len(pending_after), 1)
        self.assertEqual(pending_after[0]["review_id"], rev2["review_id"])

    # --- 8. Case Retrieval Complete Details ---
    def test_get_review_returns_complete_case(self):
        """Verify get_review returns prescription details, patient info, findings, and decision."""
        review = create_review("RX-1004", structured_review=self.sample_review_data, db_path=self.temp_db_path)
        rev_id = review["review_id"]

        full = get_review(rev_id, db_path=self.temp_db_path)
        self.assertEqual(full["review_id"], rev_id)
        self.assertEqual(full["prescription_details"]["prescription_id"], "RX-1004")
        self.assertEqual(full["prescription_details"]["patient"]["name"], "Emily Davis")
        self.assertEqual(len(full["findings"]), 3)
        self.assertGreaterEqual(len(full["audit_history"]), 4)

    # --- 9. Multiple Independent Reviews ---
    def test_multiple_reviews_remain_independent(self):
        """Verify multiple reviews on same or different prescriptions maintain isolated state."""
        rev1 = create_review("RX-1001", structured_review=AgentStructuredReview(
            prescription_id="RX-1001",
            overall_status="CLEAR",
            findings=[],
            pharmacist_action_summary="Clean."
        ), db_path=self.temp_db_path)

        rev2 = create_review("RX-1004", structured_review=self.sample_review_data, db_path=self.temp_db_path)

        accept_review(rev1["review_id"], pharmacist_id="PHARM-001", notes="Approved", db_path=self.temp_db_path)
        escalate_review(rev2["review_id"], pharmacist_id="PHARM-002", notes="Escalated", db_path=self.temp_db_path)

        r1 = get_review(rev1["review_id"], db_path=self.temp_db_path)
        r2 = get_review(rev2["review_id"], db_path=self.temp_db_path)

        self.assertEqual(r1["pharmacist_decision"], "ACCEPTED")
        self.assertEqual(r2["pharmacist_decision"], "ESCALATED")
        self.assertEqual(r1["reviewed_by"], "PHARM-001")
        self.assertEqual(r2["reviewed_by"], "PHARM-002")

    # --- 10. Rejection of Invalid Non-Existent Prescription ---
    def test_create_review_rejects_nonexistent_prescription(self):
        """Verify create_review raises error when prescription does not exist."""
        with self.assertRaises(ValueError):
            create_review("RX-9999", structured_review=self.sample_review_data, db_path=self.temp_db_path)

    # --- 11. Structured JSON Extraction and Schema Safety ---
    def test_extract_json_from_agent_response_safe_handling(self):
        """Verify robust JSON extraction from markdown code fences and raw strings."""
        raw_md = "Here is your review:\n```json\n{\"prescription_id\": \"RX-1001\", \"overall_status\": \"CLEAR\"}\n```\nThank you."
        res = _extract_json_from_agent_response(raw_md)
        self.assertIsNotNone(res)
        self.assertEqual(res["prescription_id"], "RX-1001")

        # Invalid string
        invalid_str = "No json here."
        self.assertIsNone(_extract_json_from_agent_response(invalid_str))


if __name__ == "__main__":
    unittest.main()
