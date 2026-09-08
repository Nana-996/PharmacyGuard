"""
Integration test for PharmacyGuard Strands Agent and Amazon Bedrock.
Verifies that the agent autonomously invokes the get_prescription tool
to retrieve and summarize prescription information.
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


def run_agent_prescription_integration_test() -> bool:
    """
    Executes the PharmacyGuard operations agent with a prompt requesting RX-1001,
    and validates that the agent actively invoked the get_prescription tool.
    """
    print("=" * 65, flush=True)
    print("  PharmacyGuard - Agent Tool-Calling Integration Test (Strands)", flush=True)
    print("=" * 65, flush=True)

    token = os.getenv("AWS_BEARER_TOKEN_BEDROCK")
    if not token:
        print("[FAIL] AWS_BEARER_TOKEN_BEDROCK is not set in environment or .env", flush=True)
        return False

    try:
        agent = create_pharmacy_agent()
        test_prompt = "Retrieve prescription RX-1001 and summarize the information available to the pharmacist."
        print(f"[*] Prompt: \"{test_prompt}\"", flush=True)
        print("[*] Invoking PharmacyGuard operations agent via Bedrock...", flush=True)

        response = agent(test_prompt)
        response_text = str(response)

        print("-" * 65, flush=True)
        print("[*] Agent Output Summary:")
        print(response_text[:400] + ("..." if len(response_text) > 400 else ""), flush=True)
        print("-" * 65, flush=True)

        # Inspect agent messages / conversation history for tool invocation
        tool_called = False
        tool_call_details = []

        for msg in agent.messages:
            if isinstance(msg, dict):
                content = msg.get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            # AWS Bedrock / Converse API toolUse format
                            if "toolUse" in block:
                                tu = block["toolUse"]
                                if tu.get("name") == "get_prescription":
                                    tool_called = True
                                    tool_call_details.append(f"{tu.get('name')}({tu.get('input')})")
                            # Tool result confirmation
                            if "toolResult" in block:
                                tr = block["toolResult"]
                                if "RX-1001" in str(tr):
                                    tool_called = True
            elif hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_called = True
                tool_call_details.append(str(msg.tool_calls))
            elif "get_prescription" in str(msg):
                tool_called = True
                tool_call_details.append(str(msg)[:150])

        print(f"[*] Tool 'get_prescription' Invoked: {tool_called}", flush=True)
        if tool_call_details:
            print(f"[*] Tool Call Detail: {tool_call_details[0]}", flush=True)

        # Verify key retrieved facts are present in the response
        contains_patient = "john doe" in response_text.lower() or "pat-101" in response_text.lower()
        contains_med = "amoxicillin" in response_text.lower()
        contains_diagnosis = "strep" in response_text.lower() or "pharyngitis" in response_text.lower()

        print(f"[*] Contains Patient Name/ID : {contains_patient}", flush=True)
        print(f"[*] Contains Prescribed Med  : {contains_med}", flush=True)
        print(f"[*] Contains Diagnosis       : {contains_diagnosis}", flush=True)

        success = tool_called and contains_patient and contains_med
        print("-" * 65, flush=True)
        if success:
            print("[SUCCESS] Agent tool-calling integration test PASSED!", flush=True)
        else:
            print("[FAIL] Agent integration test failed verification checks.", flush=True)
        print("=" * 65, flush=True)
        return success

    except Exception as exc:
        print(f"[FAIL] Error during agent integration test: {exc}", flush=True)
        import traceback
        traceback.print_exc()
        print("=" * 65, flush=True)
        return False


class TestAgentPrescriptionIntegration(unittest.TestCase):
    """Automated integration test case for agent tool execution."""

    def test_agent_retrieves_prescription_autonomously(self):
        """Verify the agent calls get_prescription when prompted to review RX-1001."""
        success = run_agent_prescription_integration_test()
        self.assertTrue(success, "Agent failed to autonomously call get_prescription tool or summarize data.")


if __name__ == "__main__":
    import sys
    success = run_agent_prescription_integration_test()
    sys.exit(0 if success else 1)
