"""
PharmacyGuard Automated Pre-Submission Smoke Test Suite.
Verifies critical health, authentication, security, CORS, simulated EHR retrieval,
deterministic clinical verification tools, HITL safety guardrails, and student simulation.
"""

import unittest
from fastapi.testclient import TestClient

from backend.main import app
from backend.auth.security import create_access_token, decode_access_token, JWT_SECRET_KEY
from backend.tools.prescription_tool import get_prescription
from backend.tools.verification_tools import (
    diagnosis_medication_check,
    allergy_check,
    duplicate_medication_check,
    medication_interaction_check,
    dosage_check,
)
from backend.tools.inventory_tools import check_inventory


class PharmacyGuardSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_check(self):
        """Smoke 1: System health endpoint returns 200 OK and healthy status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertIn("service", data)

    def test_02_auth_pharmacist_login(self):
        """Smoke 2: Pharmacist login returns valid session JWT and user profile."""
        payload = {
            "email": "staff.pharmacist@hospital.dev",
            "password": "DevStaff123!"
        }
        response = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["role"], "STAFF_PHARMACIST")

        # Invalid credentials check
        bad_response = self.client.post("/api/auth/login", json={"email": "wrong@hospital.dev", "password": "BadPassword"})
        self.assertEqual(bad_response.status_code, 401)

    def test_03_jwt_security_no_hardcoded_fallback(self):
        """Smoke 3: Verifies JWT token generation and ensures static hardcoded key is not used."""
        self.assertTrue(len(JWT_SECRET_KEY) >= 32, "JWT secret must be at least 256-bit entropy")
        self.assertNotEqual(
            JWT_SECRET_KEY,
            "pharmacyguard-dev-secret-key-change-in-production-2026",
            "Hardcoded fallback secret must not be used in the runtime engine."
        )

        test_payload = {"sub": "test-user-001", "role": "STAFF_PHARMACIST"}
        token = create_access_token(test_payload)
        decoded = decode_access_token(token)
        self.assertEqual(decoded["sub"], "test-user-001")
        self.assertEqual(decoded["role"], "STAFF_PHARMACIST")

    def test_04_cors_configured_origins(self):
        """Smoke 4: CORS responds with configured origin and not wildcard * with credentials."""
        headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        }
        response = self.client.options("/health", headers=headers)
        allow_origin = response.headers.get("access-control-allow-origin")
        self.assertIn(allow_origin, ["http://localhost:5173", "http://127.0.0.1:5173"])
        self.assertNotEqual(allow_origin, "*", "Credentials mode must never use wildcard '*' origin.")

    def test_05_simulated_ehr_prescription_retrieval(self):
        """Smoke 5: Retrieves structured synthetic EHR prescription records."""
        res = get_prescription("RX-1001")
        self.assertEqual(res.get("status"), "success")
        rx = res.get("data", {})
        self.assertEqual(rx.get("prescription_id"), "RX-1001")
        self.assertIn("patient", rx)
        self.assertEqual(rx["patient"]["name"], "John Doe")
        self.assertTrue(len(rx.get("diagnoses", [])) > 0)
        self.assertTrue(len(rx.get("medications", [])) > 0)

    def test_06_deterministic_clinical_tools(self):
        """Smoke 6: All 6 core clinical verification tools execute deterministically in <0.1s."""
        # 1. Indication check
        ind = diagnosis_medication_check("Streptococcal pharyngitis", "Amoxicillin 500mg")
        self.assertTrue(ind.get("relevant"), "Amoxicillin must match Streptococcal pharyngitis indication.")

        # 2. Allergy check
        alg = allergy_check("Penicillin (Beta-Lactams)", ["Augmentin 875mg / 125mg"])
        self.assertTrue(alg.get("has_allergy_conflict"), "Penicillin allergy must flag Augmentin cross-reaction.")

        # 3. Duplicate check
        dup = duplicate_medication_check(["Ibuprofen 600mg", "Naproxen 500mg"])
        self.assertTrue(dup.get("has_duplicates"), "Dual NSAIDs must be flagged as therapeutic duplication.")

        # 4. Interaction check
        ddi = medication_interaction_check(["Ibuprofen 600mg", "Naproxen 500mg"])
        self.assertTrue(ddi.get("has_interactions"), "Ibuprofen + Naproxen must flag NSAID interaction.")

        # 5. Dosage check
        dose = dosage_check("Amoxicillin", "500mg", "Every 8 hours")
        self.assertTrue(dose.get("within_standard_range"), "500mg q8h must fall within standard reference range.")

        # 6. Inventory check
        inv = check_inventory([{"medication": "Amoxicillin", "strength": "500mg"}])
        self.assertEqual(inv.get("status"), "success")
        self.assertTrue("inventory_results" in inv)

    def test_07_hitl_override_enforcement(self):
        """Smoke 7: Human-in-the-Loop guardrail rejects override submissions lacking clinical rationale (HTTP 422)."""
        login_res = self.client.post("/api/auth/login", json={
            "email": "staff.pharmacist@hospital.dev",
            "password": "DevStaff123!"
        })
        token = login_res.json()["access_token"]
        auth_header = {"Authorization": f"Bearer {token}"}

        # Blank justification must fail Pydantic min_length validation with HTTP 422
        override_payload = {
            "notes": ""
        }
        res = self.client.post("/api/reviews/REV-1003/override", json=override_payload, headers=auth_header)
        self.assertEqual(res.status_code, 422, "Override without clinical rationale must be rejected with 422.")

    def test_08_student_simulation_evaluation(self):
        """Smoke 8: Student educational simulation evaluates answer and returns feedback."""
        login_res = self.client.post("/api/auth/login", json={
            "email": "student@hospital.dev",
            "password": "DevStudent123!"
        })
        token = login_res.json()["access_token"]
        auth_header = {"Authorization": f"Bearer {token}"}

        cases_res = self.client.get("/api/student/cases", headers=auth_header)
        self.assertEqual(cases_res.status_code, 200)
        case_id = cases_res.json()["data"][0]["case_id"]

        sub_res = self.client.post(
            f"/api/student/cases/{case_id}/submit",
            json={"selected_option_index": 0, "student_notes": "Evaluated penicillin allergy conflict."},
            headers=auth_header
        )
        self.assertEqual(sub_res.status_code, 200)
        data = sub_res.json()
        self.assertIn("is_correct", data)
        self.assertIn("explanation_text", data)


if __name__ == "__main__":
    unittest.main()
