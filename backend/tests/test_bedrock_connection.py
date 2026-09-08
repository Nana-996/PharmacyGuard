import os
import sys
import unittest
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


def run_bedrock_connectivity_check() -> bool:
    """
    Invokes the Amazon Bedrock model through the Strands Agent SDK
    and prints a clear, structured success or failure report.
    """
    print("=" * 65, flush=True)
    print("  PharmacyGuard - Amazon Bedrock Connectivity Test (Strands)", flush=True)
    print("=" * 65, flush=True)

    token = os.getenv("AWS_BEARER_TOKEN_BEDROCK")
    region = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")

    print(f"[*] Target Region  : {region}", flush=True)
    print(f"[*] Target Model   : {model_id}", flush=True)
    print(f"[*] Bearer Token   : {'[CONFIGURED]' if token else '[MISSING - AWS_BEARER_TOKEN_BEDROCK not set]'}", flush=True)
    print("-" * 65, flush=True)

    if not token:
        print("[FAIL] AWS_BEARER_TOKEN_BEDROCK environment variable is not set.", flush=True)
        print("       Please configure AWS_BEARER_TOKEN_BEDROCK in your .env file.", flush=True)
        print("=" * 65, flush=True)
        return False

    try:
        from strands.models.bedrock import BedrockModel
        from strands import Agent

        # Sync region into environment
        if "AWS_REGION" not in os.environ:
            os.environ["AWS_REGION"] = region

        print("[*] Initializing Strands BedrockModel provider...", flush=True)
        bedrock_model = BedrockModel(
            model_id=model_id,
            region_name=region,
            temperature=0.1,
        )

        agent = Agent(
            model=bedrock_model,
            system_prompt="You are PharmacyGuard's connectivity test agent. Confirm status concisely.",
            name="BedrockConnectivityTester"
        )

        test_prompt = "Hello Bedrock! Confirm PharmacyGuard connectivity in 1 short sentence."
        print(f"[*] Invoking model with prompt: \"{test_prompt}\"", flush=True)
        
        response = agent(test_prompt)
        response_text = str(response).strip()

        print("-" * 65, flush=True)
        print("[SUCCESS] Amazon Bedrock connectivity test PASSED!", flush=True)
        print(f"[*] Agent Response: {response_text}", flush=True)
        print("=" * 65, flush=True)
        return True

    except Exception as exc:
        print("-" * 65, flush=True)
        print("[FAIL] Amazon Bedrock connectivity test FAILED!", flush=True)
        print(f"[*] Error Type   : {type(exc).__name__}", flush=True)
        print(f"[*] Error Message: {exc}", flush=True)
        if "Anthropic use case details" in str(exc):
            print("\n[NOTE] Anthropic models require a one-time use-case registration in AWS Bedrock console.", flush=True)
            print("       Navigate to AWS Console -> Amazon Bedrock -> Model access -> Anthropic use case details.", flush=True)
        print("=" * 65, flush=True)
        return False


class TestBedrockConnectivity(unittest.TestCase):
    """Unit test for verifying Amazon Bedrock invocation through Strands SDK."""

    def test_bedrock_model_connectivity(self):
        """Invoke Bedrock model and assert successful response."""
        success = run_bedrock_connectivity_check()
        self.assertTrue(success, "Bedrock connectivity test failed. Check AWS_BEARER_TOKEN_BEDROCK and model configuration.")


if __name__ == "__main__":
    success = run_bedrock_connectivity_check()
    sys.exit(0 if success else 1)
