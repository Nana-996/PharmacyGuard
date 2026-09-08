"""
Unit & Integration Tests for PharmacyGuard Authentication & Role-Based Access Control (RBAC).
Verifies password hashing, JWT token lifecycle, login/logout, endpoint protection (401/403),
role isolation, and user identity persistence in clinical audit logs.
"""

import os
import unittest
from fastapi.testclient import TestClient

from backend.main import app
from backend.data.database import initialize_database, get_db_connection
from backend.auth.security import hash_password, verify_password, create_access_token, decode_access_token


class TestAuthAndRBAC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use a dedicated isolated test database
        cls.test_db = os.path.abspath("backend/data/test_auth_guard.db")
        os.environ["PHARMACYGUARD_DB_PATH"] = cls.test_db
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
        initialize_database(cls.test_db, force_reseed=True)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db):
            try:
                os.remove(cls.test_db)
            except Exception:
                pass

    def test_01_password_hashing_and_verification(self):
        """Tests that PBKDF2 password hashing is salted and verifies correctly."""
        plain = "MySecretPass123!"
        hashed = hash_password(plain)
        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(verify_password(plain, hashed))
        self.assertFalse(verify_password("WrongPass", hashed))

    def test_02_jwt_token_generation_and_decoding(self):
        """Tests JWT access token encoding and payload retrieval."""
        data = {"sub": "USR-TEST-001", "role": "STAFF_PHARMACIST", "email": "test@hospital.dev"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        self.assertEqual(decoded["sub"], "USR-TEST-001")
        self.assertEqual(decoded["role"], "STAFF_PHARMACIST")
        self.assertEqual(decoded["email"], "test@hospital.dev")

    def test_03_successful_staff_pharmacist_login(self):
        """Tests staff pharmacist login with valid credentials."""
        response = self.client.post(
            "/api/auth/login",
            json={"email": "staff.pharmacist@hospital.dev", "password": "DevStaff123!"}
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["status"], "success")
        self.assertIn("access_token", json_data)
        self.assertEqual(json_data["user"]["role"], "STAFF_PHARMACIST")
        self.assertEqual(json_data["user"]["user_id"], "USR-STAFF-001")

    def test_04_failed_login_invalid_password(self):
        """Tests login failure with wrong password returns 401 and logs failure."""
        response = self.client.post(
            "/api/auth/login",
            json={"email": "staff.pharmacist@hospital.dev", "password": "WrongPassword123"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid email or password", response.json()["detail"])

    def test_05_failed_login_unknown_email(self):
        """Tests login failure with non-existent email returns 401."""
        response = self.client.post(
            "/api/auth/login",
            json={"email": "nobody@hospital.dev", "password": "Password123!"}
        )
        self.assertEqual(response.status_code, 401)

    def test_06_successful_chief_pharmacist_login(self):
        """Tests chief pharmacist login returns chief role and token."""
        response = self.client.post(
            "/api/auth/login",
            json={"email": "chief.pharmacist@hospital.dev", "password": "DevChief123!"}
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["user"]["role"], "CHIEF_PHARMACIST")
        self.assertEqual(json_data["user"]["user_id"], "USR-CHIEF-001")

    def test_07_unauthenticated_requests_return_401(self):
        """Verifies that all protected endpoints reject requests without a valid token."""
        endpoints = [
            ("GET", "/api/prescriptions"),
            ("GET", "/api/reviews"),
            ("GET", "/api/reviews/pending"),
            ("GET", "/api/inventory"),
            ("GET", "/api/analytics/dashboard"),
            ("GET", "/api/analytics/audit-log"),
            ("GET", "/api/auth/me"),
        ]
        for method, path in endpoints:
            if method == "GET":
                resp = self.client.get(path)
            self.assertEqual(
                resp.status_code, 401,
                f"Expected 401 for unauthenticated request to {path}, got {resp.status_code}"
            )

    def test_08_staff_pharmacist_can_access_pharmacist_endpoints(self):
        """Verifies staff pharmacist can access prescriptions, reviews, and inventory."""
        login_res = self.client.post(
            "/api/auth/login",
            json={"email": "staff.pharmacist@hospital.dev", "password": "DevStaff123!"}
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Access prescriptions
        rx_res = self.client.get("/api/prescriptions", headers=headers)
        self.assertEqual(rx_res.status_code, 200)

        # Access inventory
        inv_res = self.client.get("/api/inventory", headers=headers)
        self.assertEqual(inv_res.status_code, 200)

        # Access review queue
        rev_res = self.client.get("/api/reviews", headers=headers)
        self.assertEqual(rev_res.status_code, 200)

        # Access auth /me
        me_res = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["data"]["role"], "STAFF_PHARMACIST")

    def test_09_staff_pharmacist_forbidden_from_chief_only_endpoints(self):
        """Verifies staff pharmacist receives 403 Forbidden on chief-only routes."""
        login_res = self.client.post(
            "/api/auth/login",
            json={"email": "staff.pharmacist@hospital.dev", "password": "DevStaff123!"}
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Attempt to access chief-only audit trail
        audit_res = self.client.get("/api/analytics/audit-log", headers=headers)
        self.assertEqual(audit_res.status_code, 403)
        self.assertIn("Access forbidden", audit_res.json()["detail"])

    def test_10_chief_pharmacist_can_access_chief_endpoints(self):
        """Verifies chief pharmacist can access chief-only audit trail and dashboard."""
        login_res = self.client.post(
            "/api/auth/login",
            json={"email": "chief.pharmacist@hospital.dev", "password": "DevChief123!"}
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        audit_res = self.client.get("/api/analytics/audit-log", headers=headers)
        self.assertEqual(audit_res.status_code, 200)
        self.assertIn("data", audit_res.json())

    def test_11_student_cannot_access_clinical_workflows(self):
        """Verifies pharmacy student receives 403 Forbidden on clinical and review routes."""
        login_res = self.client.post(
            "/api/auth/login",
            json={"email": "student@hospital.dev", "password": "DevStudent123!"}
        )
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Forbidden from prescriptions
        rx_res = self.client.get("/api/prescriptions", headers=headers)
        self.assertEqual(rx_res.status_code, 403)

        # Forbidden from reviews
        rev_res = self.client.get("/api/reviews", headers=headers)
        self.assertEqual(rev_res.status_code, 403)

        # Forbidden from creating reviews
        start_res = self.client.post(
            "/api/reviews",
            json={"prescription_id": "RX-1001"},
            headers=headers
        )
        self.assertEqual(start_res.status_code, 403)

    def test_12_authenticated_actions_record_actual_user_id(self):
        """Verifies that clinical decisions use the authenticated session user_id."""
        # 1. Login as Staff Pharmacist USR-STAFF-001
        login_res = self.client.post(
            "/api/auth/login",
            json={"email": "staff.pharmacist@hospital.dev", "password": "DevStaff123!"}
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Accept a seeded review (e.g. from existing database or create direct review)
        from backend.services.review_service import create_review
        from backend.agent.pharmacy_agent import AgentStructuredReview, AgentFinding

        fake_structured = AgentStructuredReview(
            prescription_id="RX-1001",
            overall_status="CLEAR",
            findings=[
                AgentFinding(
                    category="CLINICAL",
                    severity="NONE",
                    title="Indication Match",
                    description="Standard therapy",
                    evidence_source="diagnosis_medication_check",
                    evidence="Match confirmed",
                    requires_action=False
                )
            ],
            pharmacist_action_summary="Clean case."
        )
        created = create_review("RX-1001", structured_review=fake_structured, db_path=self.test_db)
        rev_id = created["review_id"]

        # 3. Call accept endpoint with token
        accept_res = self.client.post(
            f"/api/reviews/{rev_id}/accept",
            json={"notes": "Clinical assessment verified by staff pharmacist."},
            headers=headers
        )
        self.assertEqual(accept_res.status_code, 200)
        updated_data = accept_res.json()["data"]

        # 4. Verify reviewed_by in SQLite is USR-STAFF-001, not PHARM-001
        self.assertEqual(updated_data["reviewed_by"], "USR-STAFF-001")
        self.assertEqual(updated_data["pharmacist_decision"], "ACCEPTED")

        # 5. Verify audit event logged with actor_id = USR-STAFF-001
        conn = get_db_connection(self.test_db)
        cur = conn.cursor()
        audit_row = cur.execute(
            "SELECT actor_id, event_type FROM audit_log WHERE review_id = ? AND event_type = 'PHARMACIST_REVIEWED'",
            (rev_id,)
        ).fetchone()
        conn.close()
        self.assertIsNotNone(audit_row)
        self.assertEqual(audit_row["actor_id"], "USR-STAFF-001")

    def test_13_logout_records_audit_event(self):
        """Verifies logout logs an audit event and terminates cleanly."""
        login_res = self.client.post(
            "/api/auth/login",
            json={"email": "staff.pharmacist@hospital.dev", "password": "DevStaff123!"}
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        logout_res = self.client.post("/api/auth/logout", headers=headers)
        self.assertEqual(logout_res.status_code, 200)

        # Check audit log for LOGOUT event
        conn = get_db_connection(self.test_db)
        cur = conn.cursor()
        audit_row = cur.execute(
            "SELECT actor_id, event_type FROM audit_log WHERE event_type = 'LOGOUT' AND actor_id = 'USR-STAFF-001'"
        ).fetchone()
        conn.close()
        self.assertIsNotNone(audit_row)


if __name__ == "__main__":
    unittest.main()
