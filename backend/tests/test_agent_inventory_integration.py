"""
Integration tests for PharmacyGuard full Agent:
Clinical Verification & Pharmacy Inventory Stock Awareness on Amazon Bedrock.
"""

import os
import sys
import unittest
from typing import Dict, Any, List

# Ensure stdout and stderr handle UTF-8 properly across platforms (especially Windows)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from backend.agent.pharmacy_agent import create_pharmacy_agent

load_dotenv()


def run_agent_inventory_review(prescription_id: str) -> Dict[str, Any]:
    """
    Executes the full agent on a prescription review prompt, returns the text response
    and list of invoked tools.
    """
    token = os.getenv("AWS_BEARER_TOKEN_BEDROCK")
    if not token:
        raise ValueError("AWS_BEARER_TOKEN_BEDROCK is not set in environment or .env")

    agent = create_pharmacy_agent()
    prompt = f"Review prescription {prescription_id}"
    response = agent(prompt)
    response_text = str(response)

    tools_invoked = []
    for msg in agent.messages:
        if isinstance(msg, dict):
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and "toolUse" in block:
                        tool_name = block["toolUse"].get("name")
                        tool_input = block["toolUse"].get("input")
                        tools_invoked.append((tool_name, tool_input))

    return {
        "prescription_id": prescription_id,
        "response_text": response_text,
        "tools_invoked": tools_invoked,
        "tool_names": [t[0] for t in tools_invoked]
    }


class TestAgentClinicalAndInventoryIntegration(unittest.TestCase):
    """Live Bedrock integration test suite covering clinical and inventory orchestration."""

    def test_case_1_fully_available_prescription(self):
        """TEST 1: Prescription where everything is available (RX-1001)."""
        res = run_agent_inventory_review("RX-1001")
        text = res["response_text"]
        tool_names = res["tool_names"]

        # Verify tool invocations
        self.assertIn("get_prescription", tool_names)
        self.assertIn("check_inventory", tool_names)

        # Verify content mentions stock availability
        self.assertTrue("available" in text.lower() or "350" in text or "in stock" in text.lower())
        self.assertTrue("review" in text.lower() and "1001" in text)
        self.assertTrue("inventory" in text.lower())

    def test_case_2_out_of_stock_prescription(self):
        """TEST 2: Prescription containing an out-of-stock medication (RX-1003)."""
        res = run_agent_inventory_review("RX-1003")
        text = res["response_text"]
        tool_names = res["tool_names"]

        self.assertIn("get_prescription", tool_names)
        self.assertIn("check_inventory", tool_names)
        self.assertTrue("out of stock" in text.lower() or "0" in text)
        self.assertTrue("HIGH" in text.upper() and "REVIEW" in text.upper())

    def test_case_3_low_stock_prescription(self):
        """TEST 3: Prescription containing a low-stock medication (RX-1002)."""
        res = run_agent_inventory_review("RX-1002")
        text = res["response_text"]
        tool_names = res["tool_names"]

        self.assertIn("get_prescription", tool_names)
        self.assertIn("check_inventory", tool_names)
        self.assertTrue("low stock" in text.lower() or "12" in text)
        self.assertTrue("REVIEW" in text.upper())

    def test_case_4_both_clinical_and_inventory_findings(self):
        """TEST 5: Prescription with both clinical findings and inventory findings (RX-1004 / RX-1002)."""
        res = run_agent_inventory_review("RX-1004")
        text = res["response_text"]
        tool_names = res["tool_names"]

        # Verified multi-tool orchestration across clinical & inventory
        self.assertIn("get_prescription", tool_names)
        self.assertIn("check_inventory", tool_names)
        self.assertTrue(any(t in tool_names for t in ["duplicate_medication_check", "medication_interaction_check", "allergy_check"]))

        # Check structured report sections
        self.assertTrue("clinical" in text.lower() or "duplication" in text.lower() or "interaction" in text.lower())
        self.assertTrue("inventory" in text.lower())
        self.assertTrue("pharmacist" in text.lower())
        self.assertTrue("safety" in text.lower() or "decision" in text.lower())


if __name__ == "__main__":
    unittest.main()
