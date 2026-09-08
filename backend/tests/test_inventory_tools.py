"""
Automated unit tests for the PharmacyGuard inventory tools:
1. check_inventory
2. get_low_stock_items
3. get_inventory_summary
"""

import unittest
from backend.data.database import initialize_database
from backend.tools.inventory_tools import (
    check_inventory,
    get_low_stock_items,
    get_inventory_summary,
)


class TestPharmacyInventoryTools(unittest.TestCase):
    """Test suite for pharmacy inventory checking and monitoring tools."""

    def setUp(self):
        initialize_database()

    def test_tools_metadata(self):
        """Verify all 3 inventory tools have proper Strands tool attributes."""
        tools = [check_inventory, get_low_stock_items, get_inventory_summary]
        for t in tools:
            self.assertTrue(callable(t))
            self.assertTrue(hasattr(t, "tool_name"))
            self.assertIsNotNone(t.__doc__)

    # --- 1. check_inventory Tests ---
    def test_check_inventory_available(self):
        """Verify check_inventory returns AVAILABLE for fully stocked medication (Amoxicillin 500mg)."""
        res = check_inventory([{"medication": "Amoxicillin", "strength": "500mg", "dosage_form": "Capsule"}])
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["all_available"])
        self.assertFalse(res["has_out_of_stock"])
        self.assertFalse(res["has_low_stock"])
        self.assertEqual(len(res["inventory_results"]), 1)

        item = res["inventory_results"][0]
        self.assertEqual(item["availability_status"], "AVAILABLE")
        self.assertEqual(item["quantity_available"], 350)
        self.assertEqual(item["unit"], "capsules")
        self.assertFalse(item["requires_pharmacist_attention"])

    def test_check_inventory_out_of_stock(self):
        """Verify check_inventory returns OUT OF STOCK when quantity is 0 (Augmentin 875/125mg)."""
        res = check_inventory([{"medication": "Augmentin", "strength": "875mg / 125mg", "dosage_form": "Tablet"}])
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["has_out_of_stock"])
        self.assertFalse(res["all_available"])

        item = res["inventory_results"][0]
        self.assertEqual(item["availability_status"], "OUT OF STOCK")
        self.assertEqual(item["quantity_available"], 0)
        self.assertTrue(item["requires_pharmacist_attention"])
        self.assertIn("OUT OF STOCK", item["stock_status"])

    def test_check_inventory_low_stock(self):
        """Verify check_inventory returns LOW STOCK when quantity is below reorder level (Lisinopril 20mg)."""
        res = check_inventory([{"medication": "Lisinopril", "strength": "20mg", "dosage_form": "Tablet"}])
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["has_low_stock"])
        self.assertFalse(res["all_available"])

        item = res["inventory_results"][0]
        self.assertEqual(item["availability_status"], "LOW STOCK")
        self.assertEqual(item["quantity_available"], 12)
        self.assertEqual(item["reorder_level"], 30)
        self.assertTrue(item["requires_pharmacist_attention"])

    def test_check_inventory_strength_unavailable(self):
        """Verify check_inventory returns STRENGTH UNAVAILABLE when exact strength is not stocked but other strengths exist."""
        res = check_inventory([{"medication": "Amlodipine Besylate", "strength": "10mg", "dosage_form": "Tablet"}])
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["has_strength_unavailable"])

        item = res["inventory_results"][0]
        self.assertEqual(item["availability_status"], "STRENGTH UNAVAILABLE")
        self.assertIn("5mg", item["stock_status"])
        self.assertTrue(item["requires_pharmacist_attention"])

    def test_check_inventory_multiple_medications_mixed_statuses(self):
        """Verify check_inventory handles multi-drug prescriptions with varying stock statuses (RX-1005)."""
        meds = [
            {"medication": "Atorvastatin Calcium", "strength": "40mg"},
            {"medication": "Metformin HCl", "strength": "1000mg"},
            {"medication": "Lisinopril", "strength": "10mg"},
            {"medication": "Amlodipine Besylate", "strength": "5mg"},
        ]
        res = check_inventory(meds)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["total_checked"], 4)
        self.assertTrue(res["has_low_stock"])  # Metformin 1000mg has 6 units
        self.assertFalse(res["has_out_of_stock"])

        statuses = {r["requested_medication"]: r["availability_status"] for r in res["inventory_results"]}
        self.assertEqual(statuses["Atorvastatin Calcium"], "AVAILABLE")
        self.assertEqual(statuses["Metformin HCl"], "LOW STOCK")
        self.assertEqual(statuses["Lisinopril"], "AVAILABLE")
        self.assertEqual(statuses["Amlodipine Besylate"], "AVAILABLE")

    def test_check_inventory_empty_input(self):
        """Verify check_inventory gracefully handles empty input."""
        res = check_inventory([])
        self.assertEqual(res["status"], "error")
        self.assertEqual(len(res["inventory_results"]), 0)

    # --- 2. get_low_stock_items Tests ---
    def test_get_low_stock_items(self):
        """Verify get_low_stock_items returns all items at or below reorder threshold."""
        res = get_low_stock_items()
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(res["total_low_stock_items"], 3)

        items = res["low_stock_items"]
        med_names = [i["medication"] for i in items]
        # Should include Lisinopril 20mg (12 units vs reorder 30), Augmentin 875/125mg (0 units), Ibuprofen 600mg (0 units), Metformin 1000mg (6 units)
        self.assertTrue(any("Lisinopril 20mg" in n for n in med_names))
        self.assertTrue(any("Augmentin 875" in n for n in med_names))
        self.assertTrue(any("Metformin" in n for n in med_names))

        for item in items:
            self.assertLessEqual(item["quantity_on_hand"], item["reorder_level"])
            self.assertIn(item["stock_status"], ["LOW STOCK", "OUT OF STOCK"])

    # --- 3. get_inventory_summary Tests ---
    def test_get_inventory_summary(self):
        """Verify get_inventory_summary returns accurate aggregate metrics."""
        res = get_inventory_summary()
        self.assertEqual(res["status"], "success")
        summary = res["inventory_summary"]

        self.assertGreaterEqual(summary["total_tracked_medications"], 14)
        self.assertGreater(summary["number_available"], 0)
        self.assertGreater(summary["number_low_stock"], 0)
        self.assertGreater(summary["number_out_of_stock"], 0)
        self.assertEqual(
            summary["number_below_reorder_level"],
            summary["number_low_stock"] + summary["number_out_of_stock"]
        )
        self.assertIn("%", summary["stock_health_percentage"])


if __name__ == "__main__":
    unittest.main()
