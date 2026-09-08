"""
Integration test for PharmacyGuard Clinical Verification Agent with Amazon Bedrock.
Verifies multi-tool orchestration for prescription clinical verification.
"""

import os
import sys
import unittest

# Ensure stdout and stderr handle UTF-8 properly across platforms (especially Windows)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from backend.agent.pharmacy_agent import create_pharmacy_agent

load_dotenv()


def run_agent_verification_integration_test(prescription_id: str = "RX-1002") -> bool:
    """
    Executes the PharmacyGuard clinical verification agent with a review prompt,
    and validates that the agent autonomously orchestrated multiple verification tools.
    """
    print("=" * 65, flush=True)
    print(f"  PharmacyGuard - Clinical Verification Agent Test ({prescription_id})", flush=True)
    print("=" * 65, flush=True)

    token = os.getenv("AWS_BEARER_TOKEN_BEDROCK")
    if not token:
        print("[FAIL] AWS_BEARER_TOKEN_BEDROCK is not configured in .env", flush=True)
        return False

    try:
        agent = create_pharmacy_agent()
        test_prompt = f"Review prescription {prescription_id}"
        print(f"[*] Prompt: \"{test_prompt}\"", flush=True)
        print("[*] Invoking PharmacyGuard clinical verification agent via Bedrock...", flush=True)

        response = agent(test_prompt)
        response_text = str(response)

        print("-" * 65, flush=True)
        print("[*] Agent Final Response:")
        print(response_text, flush=True)
        print("-" * 65, flush=True)

        # Inspect agent messages for all tool invocations
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

        print(f"[*] Tools Invoked ({len(tools_invoked)} total):", flush=True)
        for t_name, t_in in tools_invoked:
            print(f"    - {t_name}: {t_in}", flush=True)

        tool_names = [t[0] for t in tools_invoked]

        # 1. Verify get_prescription was invoked
        get_rx_called = "get_prescription" in tool_names
        # 2. Verify verification tools were invoked
        verification_tools_called = any(
            t in tool_names for t in [
                "diagnosis_medication_check",
                "allergy_check",
                "duplicate_medication_check",
                "medication_interaction_check",
                "dosage_check",
            ]
        )
        # 3. Verify status present in response
        has_status = ("REVIEW" in response_text.upper() or "CLEAR" in response_text.upper())
        # 4. Verify safety note / pharmacist recommendation present
        has_safety = "pharmacist" in response_text.lower()
        # 5. Verify no hallucinated approval/rejection claim
        no_fake_approval = "i have approved" not in response_text.lower() and "i have rejected" not in response_text.lower()

        print("-" * 65, flush=True)
        print(f"[*] get_prescription Invoked      : {get_rx_called}", flush=True)
        print(f"[*] Verification Tools Invoked    : {verification_tools_called} ({[t for t in tool_names if t != 'get_prescription']})", flush=True)
        print(f"[*] Structured Status Present     : {has_status}", flush=True)
        print(f"[*] Pharmacist Oversight Stated   : {has_safety}", flush=True)
        print(f"[*] Safe Non-Autonomous Stance    : {no_fake_approval}", flush=True)

        success = (
            get_rx_called
            and verification_tools_called
            and has_status
            and has_safety
            and no_fake_approval
        )

        print("-" * 65, flush=True)
        if success:
            print("[SUCCESS] Agent clinical verification test PASSED!", flush=True)
        else:
            print("[FAIL] Agent clinical verification test failed one or more assertions.", flush=True)
        print("=" * 65, flush=True)
        return success

    except Exception as exc:
        print(f"[FAIL] Error during agent verification test: {exc}", flush=True)
        import traceback
        traceback.print_exc()
        print("=" * 65, flush=True)
        return False


class TestAgentVerificationIntegration(unittest.TestCase):
    """Automated integration test case for multi-tool clinical verification."""

    def test_agent_orchestrates_verification_for_rx_1002(self):
        """Verify agent calls get_prescription and verification tools for RX-1002."""
        success = run_agent_verification_integration_test("RX-1002")
        self.assertTrue(success, "Agent failed to orchestrate clinical verification tools for RX-1002.")


if __name__ == "__main__":
    rx_id = sys.argv[1] if len(sys.argv) > 1 else "RX-1002"
    success = run_agent_verification_integration_test(rx_id)
    sys.exit(0 if success else 1)
