"""
Automated unit tests for the PharmacyGuard clinical verification tools:
1. diagnosis_medication_check
2. allergy_check
3. duplicate_medication_check
4. medication_interaction_check
5. dosage_check
"""

import unittest
from backend.data.database import initialize_database
from backend.tools.verification_tools import (
    diagnosis_medication_check,
    allergy_check,
    duplicate_medication_check,
    medication_interaction_check,
    dosage_check,
)


class TestClinicalVerificationTools(unittest.TestCase):
    """Test suite verifying all 5 clinical verification tools individually."""

    def setUp(self):
        initialize_database()

    def test_tools_metadata(self):
        """Verify all 5 verification tools have proper Strands tool attributes."""
        tools = [
            diagnosis_medication_check,
            allergy_check,
            duplicate_medication_check,
            medication_interaction_check,
            dosage_check,
        ]
        for t in tools:
            self.assertTrue(callable(t))
            self.assertTrue(hasattr(t, "tool_name"))
            self.assertIsNotNone(t.__doc__)

    # --- 1. Diagnosis-Medication Check Tests ---
    def test_diagnosis_medication_match(self):
        """Verify diagnosis_medication_check returns MATCH for standard therapy (Strep Throat -> Amoxicillin)."""
        res = diagnosis_medication_check("Streptococcal pharyngitis (Strep throat)", "Amoxicillin 500mg")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["relevant"])
        self.assertEqual(res["category"], "MATCH")
        self.assertEqual(res["finding_priority"], "CLEAR")
        self.assertTrue(res["requires_pharmacist_review"])

    def test_diagnosis_medication_mismatch(self):
        """Verify diagnosis_medication_check returns POTENTIAL_MISMATCH (Diabetes -> Lisinopril)."""
        res = diagnosis_medication_check("Type 2 diabetes mellitus without complications", "Lisinopril 20mg")
        self.assertEqual(res["status"], "success")
        self.assertFalse(res["relevant"])
        self.assertEqual(res["category"], "POTENTIAL_MISMATCH")
        self.assertEqual(res["finding_priority"], "REVIEW")
        self.assertIn("not documented as standard first-line", res["evidence"])

    # --- 2. Allergy Check Tests ---
    def test_allergy_check_severe_conflict(self):
        """Verify allergy_check detects severe Penicillin cross-reactivity for Augmentin."""
        res = allergy_check(
            "Penicillin (Beta-Lactams) - Severe Anaphylaxis",
            ["Augmentin 875mg / 125mg"]
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["has_allergy_conflict"])
        self.assertEqual(res["finding_priority"], "HIGH PRIORITY REVIEW")
        self.assertGreaterEqual(len(res["conflicts"]), 1)
        self.assertEqual(res["conflicts"][0]["allergen_group"], "Penicillin")

    def test_allergy_check_no_conflict(self):
        """Verify allergy_check passes clean for patients with NKDA."""
        res = allergy_check(
            "No known drug allergies (NKDA)",
            ["Amoxicillin 500mg"]
        )
        self.assertEqual(res["status"], "success")
        self.assertFalse(res["has_allergy_conflict"])
        self.assertEqual(res["finding_priority"], "CLEAR")

    # --- 3. Duplicate Medication Check Tests ---
    def test_duplicate_medication_detected(self):
        """Verify duplicate_medication_check detects dual systemic NSAID therapy (Ibuprofen + Naproxen)."""
        res = duplicate_medication_check(["Ibuprofen 600mg", "Naproxen 500mg"])
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["has_duplicates"])
        self.assertEqual(res["finding_priority"], "HIGH PRIORITY REVIEW")
        self.assertIn("NSAID", res["explanation"])

    def test_duplicate_medication_single_drug(self):
        """Verify duplicate_medication_check passes for a single medication."""
        res = duplicate_medication_check(["Amoxicillin 500mg"])
        self.assertEqual(res["status"], "success")
        self.assertFalse(res["has_duplicates"])
        self.assertEqual(res["finding_priority"], "CLEAR")

    # --- 4. Medication Interaction Check Tests ---
    def test_medication_interaction_major(self):
        """Verify medication_interaction_check flags major dual NSAID interaction."""
        res = medication_interaction_check(["Ibuprofen 600mg", "Naproxen 500mg"])
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["has_interactions"])
        self.assertEqual(res["finding_priority"], "HIGH PRIORITY REVIEW")
        severities = [i["severity"] for i in res["interactions"]]
        self.assertIn("Major", severities)

    def test_medication_interaction_minor_synergy(self):
        """Verify medication_interaction_check identifies Lisinopril + Amlodipine combination."""
        res = medication_interaction_check(["Lisinopril 10mg", "Amlodipine 5mg"])
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["has_interactions"])
        self.assertEqual(res["finding_priority"], "REVIEW")
        self.assertIn("Minor", [i["severity"] for i in res["interactions"]])

    def test_medication_interaction_none(self):
        """Verify medication_interaction_check returns clean when no known interactions exist."""
        res = medication_interaction_check(["Amoxicillin 500mg"])
        self.assertEqual(res["status"], "success")
        self.assertFalse(res["has_interactions"])
        self.assertEqual(res["finding_priority"], "CLEAR")

    # --- 5. Dosage Check Tests ---
    def test_dosage_check_standard_range(self):
        """Verify dosage_check approves standard 500mg TID Amoxicillin."""
        res = dosage_check("Amoxicillin", "500mg", "Every 8 hours (Three times daily)")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["within_standard_range"])
        self.assertEqual(res["finding_priority"], "CLEAR")
        self.assertEqual(res["parsed_single_dose_mg"], 500.0)
        self.assertEqual(res["estimated_daily_dose_mg"], 1500.0)

    def test_dosage_check_exceeds_max_dose(self):
        """Verify dosage_check flags an excessive Lisinopril dose (100mg once daily)."""
        res = dosage_check("Lisinopril", "100mg", "Once daily in the morning")
        self.assertEqual(res["status"], "success")
        self.assertFalse(res["within_standard_range"])
        self.assertEqual(res["finding_priority"], "HIGH PRIORITY REVIEW")
        self.assertTrue(any("exceeds" in f.lower() for f in res["flags"]))


if __name__ == "__main__":
    unittest.main()
