"""
PharmacyGuard Operations Support, Clinical Verification & Inventory Agent.
Powered by Amazon Bedrock through the Strands Agent SDK.
"""

import os
import sys
import json
import re
import logging
import concurrent.futures
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

logger = logging.getLogger("pharmacy_agent")

# Ensure stdout and stderr handle UTF-8 properly across platforms (especially Windows)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from strands import Agent
from strands.models.bedrock import BedrockModel
from backend.tools.prescription_tool import get_prescription
from backend.tools.verification_tools import (
    diagnosis_medication_check,
    allergy_check,
    duplicate_medication_check,
    medication_interaction_check,
    dosage_check,
)
from backend.tools.inventory_tools import (
    check_inventory,
    get_low_stock_items,
    get_inventory_summary,
)

# Load environment variables from .env
load_dotenv()


class AgentFinding(BaseModel):
    category: Literal["CLINICAL", "ALLERGY", "DUPLICATION", "INTERACTION", "DOSAGE", "INVENTORY"]
    severity: str = Field(..., description="Severity level, e.g., 'HIGH', 'MODERATE', 'LOW', 'NONE'")
    title: str = Field(..., description="Short summary title of the finding")
    description: str = Field(..., description="Detailed clinical or operational description")
    evidence_source: str = Field(..., description="Name of the tool that produced the finding (e.g., 'allergy_check', 'check_inventory')")
    evidence: str = Field(..., description="Actual evidence data extracted from the tool output")
    requires_action: bool = Field(default=False, description="Whether this finding requires pharmacist intervention")


class AgentStructuredReview(BaseModel):
    prescription_id: str
    overall_status: Literal["CLEAR", "REVIEW", "HIGH_PRIORITY_REVIEW"]
    findings: List[AgentFinding]
    pharmacist_action_summary: str
    safety_disclaimer: str = (
        "This is decision-support information generated from the simulated hospital dataset. "
        "A qualified pharmacist must make the final clinical decision."
    )


PHARMACY_GUARD_SYSTEM_PROMPT = """You are PharmacyGuard's Operations Support, Clinical Verification, and Inventory Agent.

ROLE & MISSION:
You assist pharmacy staff and licensed pharmacists by retrieving prescription records, performing deterministic clinical verification checks, checking hospital pharmacy stock levels, and compiling comprehensive, prioritized decision-support reports.

AVAILABLE TOOLS:
1. Prescription Retrieval:
   - `get_prescription(prescription_id)`: Retrieves prescription, patient demographics, allergies, diagnoses, and prescribed medication items.
2. Clinical Verification:
   - `diagnosis_medication_check(diagnosis, medication)`: Evaluates indication alignment against guideline references.
   - `allergy_check(patient_allergies, prescribed_medications)`: Evaluates drug allergy conflicts and cross-reactivities.
   - `duplicate_medication_check(prescribed_medications)`: Detects duplicate active ingredients and therapeutic class overlaps.
   - `medication_interaction_check(prescribed_medications)`: Queries local simulated interaction knowledge base for drug-drug interactions.
   - `dosage_check(medication, dosage, frequency)`: Evaluates single and daily doses against reference ranges and maximum limits.
3. Pharmacy Inventory & Stock:
   - `check_inventory(prescribed_medications)`: Checks stock availability (AVAILABLE, LOW STOCK, OUT OF STOCK, STRENGTH UNAVAILABLE, NOT FOUND) for all prescribed medicines.
   - `get_low_stock_items()`: Retrieves all pharmacy catalog items currently at or below reorder threshold.
   - `get_inventory_summary()`: Retrieves high-level pharmacy stock health and tracking metrics.

COMPREHENSIVE PRESCRIPTION REVIEW WORKFLOW:
When asked to review, check, or verify a prescription:
1. **Retrieve Prescription**: Call `get_prescription(prescription_id)` first.
2. **Perform Clinical Verification**:
   - Call `diagnosis_medication_check` for each prescribed medication against active diagnoses.
   - Call `allergy_check` comparing the patient's recorded allergies against all prescribed medications.
   - If 2+ medications are prescribed, call `duplicate_medication_check` and `medication_interaction_check`.
   - Call `dosage_check` for each prescribed drug's dose and frequency.
3. **Check Pharmacy Inventory**:
   - Call `check_inventory` with the prescribed medications to determine on-hand stock and availability.
4. **Synthesize Findings & Determine Overall Status**:
   - `HIGH_PRIORITY_REVIEW`: Critical safety flag present (severe allergy conflict, major drug interaction, hazardous duplicate, excessive overdose) OR a critical required medication is OUT OF STOCK.
   - `REVIEW`: Non-critical finding present (potential diagnosis mismatch, moderate interaction, dosage adjustment note, low stock on hand).
   - `CLEAR`: All clinical verification checks passed clean and all medications are fully AVAILABLE in stock.

5. **REPORT FORMAT**:
   Unless specifically asked for JSON, format your response as a clear, professional report with the following structure:

   Prescription Review
   -------------------
   Prescription: [Prescription ID]
   Patient: [Patient Name, Age, Sex, Documented Allergies]

   Overall Status:
   [CLEAR | REVIEW | HIGH_PRIORITY_REVIEW]

   Clinical Findings:
   - [Clinical finding with evidence from tool output and priority]

   Inventory:
   - [Medication Name]: [AVAILABLE | LOW STOCK | OUT OF STOCK | STRENGTH UNAVAILABLE] — [Quantity and details from tool]

   Pharmacist Attention:
   - [Actionable guidance on flagged clinical and inventory issues]

   Safety Note:
   This is decision-support information generated from the simulated hospital dataset. A qualified pharmacist must make the final clinical decision.

6. **STRUCTURED JSON OUTPUT FORMAT**:
   When requested to provide a structured review or JSON output, respond with valid JSON adhering to this exact schema:
   {
     "prescription_id": "<prescription_id>",
     "overall_status": "CLEAR | REVIEW | HIGH_PRIORITY_REVIEW",
     "findings": [
       {
         "category": "CLINICAL | ALLERGY | DUPLICATION | INTERACTION | DOSAGE | INVENTORY",
         "severity": "<HIGH | MODERATE | LOW | NONE>",
         "title": "<Short title>",
         "description": "<Description>",
         "evidence_source": "<Exact Tool Name, e.g. allergy_check, check_inventory, diagnosis_medication_check, dosage_check, duplicate_medication_check, medication_interaction_check, get_prescription>",
         "evidence": "<Direct evidence from tool output>",
         "requires_action": <true | false>
       }
     ],
     "pharmacist_action_summary": "<Clear actionable guidance for the human pharmacist>"
   }

STRICT SAFETY AND COMPLIANCE RULES:
- The tools provide evidence. You reason over the evidence. The pharmacist makes the final decision.
- NEVER automatically substitute a medicine (even if out of stock or strength unavailable).
- NEVER alter dosages, change prescriptions, approve prescriptions, or reject prescriptions autonomously.
- NEVER tell patients what medicine to purchase elsewhere.
- NEVER invent, hallucinate, or assume patient data or inventory numbers not returned by your tools.
- All data in this system is synthetic test data for operational demonstration.
"""


def create_pharmacy_agent(
    model_id: Optional[str] = None,
    region: Optional[str] = None,
    temperature: float = 0.1
) -> Agent:
    """
    Initializes and returns a Strands Agent configured with Amazon Bedrock
    and loaded with the complete suite of retrieval, clinical verification, and inventory tools.
    """
    target_region = region or os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))
    if "AWS_REGION" not in os.environ:
        os.environ["AWS_REGION"] = target_region

    target_model_id = model_id or os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")

    # Initialize Bedrock model provider via Strands SDK
    bedrock_model = BedrockModel(
        model_id=target_model_id,
        region_name=target_region,
        temperature=temperature,
    )

    all_tools = [
        get_prescription,
        diagnosis_medication_check,
        allergy_check,
        duplicate_medication_check,
        medication_interaction_check,
        dosage_check,
        check_inventory,
        get_low_stock_items,
        get_inventory_summary,
    ]

    agent = Agent(
        model=bedrock_model,
        system_prompt=PHARMACY_GUARD_SYSTEM_PROMPT,
        tools=all_tools,
        name="PharmacyGuard-FullAgent",
        description="Comprehensive pharmacy operations support agent for retrieval, clinical verification, and inventory tracking."
    )

    return agent


def run_pharmacy_agent(message: str) -> str:
    """Runs the PharmacyGuard agent on a user message and returns the text response."""
    agent = create_pharmacy_agent()
    result = agent(message)
    return str(result)


def _extract_json_from_agent_response(response_text: str) -> Optional[Dict[str, Any]]:
    """Helper to extract and parse JSON object from agent output text."""
    clean_text = response_text.strip()

    # Match markdown json block: ```json ... ```
    json_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
    if json_block_match:
        try:
            return json.loads(json_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # Direct json match: find outermost { ... }
    outer_json_match = re.search(r"(\{.*\})", clean_text, re.DOTALL)
    if outer_json_match:
        try:
            return json.loads(outer_json_match.group(1))
        except json.JSONDecodeError:
            pass

    return None


def _gather_deterministic_evidence(prescription_id: str) -> Dict[str, Any]:
    """Retrieves prescription and deterministically executes all verification and inventory checks in Python."""
    clean_rx_id = prescription_id.strip().upper()
    rx_resp = get_prescription(clean_rx_id)
    if rx_resp.get("status") != "success" or not rx_resp.get("data"):
        raise ValueError(f"Prescription '{clean_rx_id}' was not found in the hospital database.")

    rx_data = rx_resp["data"]
    patient = rx_data.get("patient", {})
    meds = rx_data.get("medications", [])
    diags = rx_data.get("diagnoses", [])
    med_names = [m.get("medication") for m in meds if m.get("medication")]

    # 1. Indications
    indications = []
    for d in diags:
        diag_name = d.get("diagnosis", "")
        for m in meds:
            med_name = m.get("medication", "")
            if diag_name and med_name:
                indications.append(diagnosis_medication_check(diag_name, med_name))

    # 2. Allergy conflict
    allergies = allergy_check(patient.get("allergies", ""), med_names)

    # 3. Dosages
    dosages = []
    for m in meds:
        dosages.append(dosage_check(m.get("medication", ""), m.get("dosage", ""), m.get("frequency", "")))

    # 4. Duplicates & Interactions (for 2+ meds)
    duplicates = duplicate_medication_check(med_names) if len(med_names) >= 2 else None
    interactions = medication_interaction_check(med_names) if len(med_names) >= 2 else None

    # 5. Inventory check
    inventory_items = [{"medication": m.get("medication", ""), "strength": m.get("strength", "")} for m in meds]
    inventory = check_inventory(inventory_items)

    return {
        "prescription": rx_data,
        "indications": indications,
        "allergies": allergies,
        "dosages": dosages,
        "duplicates": duplicates,
        "interactions": interactions,
        "inventory": inventory
    }


def _synthesize_deterministic_review(prescription_id: str, evidence: Dict[str, Any]) -> AgentStructuredReview:
    """Fallback generator that constructs an AgentStructuredReview directly from tool outputs."""
    rx_data = evidence.get("prescription", {})
    diags = rx_data.get("diagnoses", [])
    meds = rx_data.get("medications", [])
    allergies = evidence.get("allergies", {})
    indications = evidence.get("indications", [])
    dosages = evidence.get("dosages", [])
    inventory = evidence.get("inventory", {})
    duplicates = evidence.get("duplicates")
    interactions = evidence.get("interactions")

    findings: List[AgentFinding] = []
    has_high = False
    has_review = False

    # 1. Allergy
    if allergies.get("has_allergy_conflict"):
        has_high = True
        findings.append(AgentFinding(
            category="ALLERGY",
            severity="HIGH",
            title=f"CRITICAL: Documented Allergy Conflict — {allergies.get('allergen_group', 'Penicillin / Beta-Lactam')}",
            description=allergies.get("clinical_mechanism") or allergies.get("recommendation") or "Severe drug allergy conflict detected.",
            evidence_source="allergy_check",
            evidence=allergies.get("evidence", "Allergy conflict confirmed against recorded patient allergies."),
            requires_action=True
        ))

    # 2. Indications
    for ind in indications:
        is_match = ind.get("relevant", False) and ind.get("category") == "MATCH"
        severity = "NONE" if is_match else "MODERATE"
        if not is_match:
            has_review = True
        findings.append(AgentFinding(
            category="CLINICAL",
            severity=severity,
            title=f"Indication Check: {ind.get('category', 'EVALUATION')}",
            description=ind.get("evidence", "Indication guideline evaluation."),
            evidence_source="diagnosis_medication_check",
            evidence=f"Category: {ind.get('category')} | Priority: {ind.get('finding_priority')}",
            requires_action=not is_match
        ))

    # 3. Dosages
    for dsg in dosages:
        within_range = dsg.get("within_standard_range", True)
        severity = "NONE" if within_range else "HIGH"
        if not within_range:
            has_high = True
        findings.append(AgentFinding(
            category="DOSAGE",
            severity=severity,
            title="Dosage Range Check: " + ("Within Standard Range" if within_range else "Dosage Alert"),
            description=dsg.get("flag", "Dosage evaluation complete."),
            evidence_source="dosage_check",
            evidence=f"Daily: {dsg.get('estimated_daily_dose')} | Max: {dsg.get('max_daily_dose')} | Range: {dsg.get('standard_single_dose_range')}",
            requires_action=not within_range
        ))

    # 4. Duplicates & Interactions
    if duplicates and duplicates.get("has_duplicate_conflict"):
        has_review = True
        findings.append(AgentFinding(
            category="DUPLICATION",
            severity="MODERATE",
            title="Duplicate Therapy Alert",
            description=duplicates.get("evidence", "Overlapping active ingredients or therapeutic class detected."),
            evidence_source="duplicate_medication_check",
            evidence=duplicates.get("evidence", ""),
            requires_action=True
        ))

    if interactions and interactions.get("has_interaction"):
        has_high = True
        findings.append(AgentFinding(
            category="INTERACTION",
            severity="HIGH",
            title="Drug-Drug Interaction Alert",
            description=interactions.get("evidence", "Potentially hazardous drug interaction identified."),
            evidence_source="medication_interaction_check",
            evidence=interactions.get("evidence", ""),
            requires_action=True
        ))

    # 5. Inventory
    for item_stock in inventory.get("inventory_results", []):
        st = item_stock.get("availability_status", "AVAILABLE")
        req_action = item_stock.get("requires_pharmacist_attention", False)
        if st == "OUT OF STOCK":
            has_high = True
            sev = "MODERATE"
        elif st in ["LOW STOCK", "STRENGTH UNAVAILABLE"]:
            has_review = True
            sev = "LOW"
        else:
            sev = "NONE"

        findings.append(AgentFinding(
            category="INVENTORY",
            severity=sev,
            title=f"Inventory: {item_stock.get('requested_medication')} — {st}",
            description=item_stock.get("stock_status", "Stock verified."),
            evidence_source="check_inventory",
            evidence=f"Available: {item_stock.get('quantity_available', 0)} | Status: {st}",
            requires_action=req_action
        ))

    overall = "HIGH_PRIORITY_REVIEW" if has_high else ("REVIEW" if has_review else "CLEAR")

    summary_parts = []
    if allergies.get("has_allergy_conflict"):
        summary_parts.append("CRITICAL: Severe allergy conflict detected. Withhold dispensing immediately and contact prescriber for allergy reconciliation.")
    if inventory.get("has_out_of_stock"):
        summary_parts.append("Medication currently OUT OF STOCK in pharmacy. Pharmacist authorization required for alternative strength or reorder.")
    if not summary_parts:
        summary_parts.append("Prescription passed indication, allergy, dosage, and stock availability verification. Ready for routine pharmacist review.")

    return AgentStructuredReview(
        prescription_id=prescription_id,
        overall_status=overall,
        findings=findings,
        pharmacist_action_summary=" ".join(summary_parts)
    )


def _parse_and_validate_review_json(parsed_json: Dict[str, Any], prescription_id: str) -> AgentStructuredReview:
    """Validates and normalizes parsed JSON object into an AgentStructuredReview instance."""
    # Standardize overall_status formatting
    if "overall_status" in parsed_json and isinstance(parsed_json["overall_status"], str):
        status_val = parsed_json["overall_status"].strip().upper().replace(" ", "_")
        if "HIGH" in status_val or "PRIORITY" in status_val:
            parsed_json["overall_status"] = "HIGH_PRIORITY_REVIEW"
        elif "REVIEW" in status_val:
            parsed_json["overall_status"] = "REVIEW"
        elif "CLEAR" in status_val:
            parsed_json["overall_status"] = "CLEAR"

    # Validate findings category formatting
    if "findings" in parsed_json and isinstance(parsed_json["findings"], list):
        for f in parsed_json["findings"]:
            if "category" in f and isinstance(f["category"], str):
                cat_val = f["category"].strip().upper()
                if cat_val not in ["CLINICAL", "ALLERGY", "DUPLICATION", "INTERACTION", "DOSAGE", "INVENTORY"]:
                    if "ALLERGY" in cat_val:
                        f["category"] = "ALLERGY"
                    elif "DUPLICAT" in cat_val:
                        f["category"] = "DUPLICATION"
                    elif "INTERACT" in cat_val:
                        f["category"] = "INTERACTION"
                    elif "DOSE" in cat_val or "DOSAGE" in cat_val:
                        f["category"] = "DOSAGE"
                    elif "INVENT" in cat_val or "STOCK" in cat_val:
                        f["category"] = "INVENTORY"
                    else:
                        f["category"] = "CLINICAL"

    if "prescription_id" not in parsed_json:
        parsed_json["prescription_id"] = prescription_id

    return AgentStructuredReview.model_validate(parsed_json)


def run_structured_prescription_review(
    prescription_id: str,
    agent: Optional[Agent] = None,
    timeout_seconds: float = 14.0
) -> AgentStructuredReview:
    """
    Executes a structured prescription review.
    1. Gathers deterministic clinical & inventory evidence instantly in Python (<0.1s).
    2. Uses 1-turn Bedrock synthesis with the pre-gathered evidence (15-18s) to generate clinical narrative.
    3. Gracefully falls back to deterministic structured synthesis if Bedrock times out or errors,
       guaranteeing zero stalled requests.
    """
    clean_rx_id = prescription_id.strip().upper()

    # Step 1: Instant deterministic evidence gathering
    evidence = _gather_deterministic_evidence(clean_rx_id)

    # Step 2: Try 1-turn Bedrock synthesis with timeout
    def _call_bedrock_synthesis() -> Optional[AgentStructuredReview]:
        prompt = (
            f"You are PharmacyGuard's Operations Support, Clinical Verification, and Inventory Agent.\n"
            f"Synthesize a concise, structured prescription review report for the pharmacist based on the following verified clinical and inventory evidence.\n\n"
            f"PRESCRIPTION:\n{json.dumps(evidence.get('prescription'))}\n\n"
            f"CLINICAL & INVENTORY EVIDENCE:\n"
            f"1. Indication Check: {json.dumps(evidence.get('indications'))}\n"
            f"2. Allergy Check: {json.dumps(evidence.get('allergies'))}\n"
            f"3. Dosage Check: {json.dumps(evidence.get('dosages'))}\n"
            f"4. Inventory Availability: {json.dumps(evidence.get('inventory'))}\n\n"
            f"Output ONLY a valid JSON object matching this schema:\n"
            f'{{\n'
            f'  "prescription_id": "{clean_rx_id}",\n'
            f'  "overall_status": "HIGH_PRIORITY_REVIEW" | "REVIEW" | "CLEAR",\n'
            f'  "findings": [\n'
            f'    {{\n'
            f'      "category": "CLINICAL" | "ALLERGY" | "DUPLICATION" | "INTERACTION" | "DOSAGE" | "INVENTORY",\n'
            f'      "severity": "HIGH" | "MODERATE" | "LOW" | "NONE",\n'
            f'      "title": "Concise title",\n'
            f'      "description": "Concise clinical explanation",\n'
            f'      "evidence_source": "allergy_check" | "diagnosis_medication_check" | "dosage_check" | "check_inventory",\n'
            f'      "evidence": "Key evidence snippet",\n'
            f'      "requires_action": true | false\n'
            f'    }}\n'
            f'  ],\n'
            f'  "pharmacist_action_summary": "Concise (2-3 sentences) actionable clinical summary and directives for the pharmacist"\n'
            f'}}\n'
        )

        if agent:
            resp_str = str(agent(prompt))
        else:
            synth_agent = Agent(
                model=BedrockModel(
                    model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6"),
                    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                    temperature=0.1,
                    streaming=False,
                ),
                tools=[],
                system_prompt="You are PharmacyGuard's clinical review synthesis specialist. Given prescription and tool evidence, generate the final structured review JSON.",
            )
            resp_str = str(synth_agent(prompt))

        parsed = _extract_json_from_agent_response(resp_str)
        if parsed:
            return _parse_and_validate_review_json(parsed, clean_rx_id)
        return None

    # Execute Bedrock synthesis with non-blocking timeout
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(_call_bedrock_synthesis)
        result = future.result(timeout=timeout_seconds)
        if result:
            logger.info(f"Bedrock synthesis succeeded for {clean_rx_id}")
            executor.shutdown(wait=False, cancel_futures=True)
            return result
    except concurrent.futures.TimeoutError:
        logger.warning(f"Bedrock synthesis timed out after {timeout_seconds}s for {clean_rx_id}. Using deterministic fallback.")
        executor.shutdown(wait=False, cancel_futures=True)
    except Exception as exc:
        logger.warning(f"Bedrock synthesis error for {clean_rx_id}: {exc}. Using deterministic fallback.")
        executor.shutdown(wait=False, cancel_futures=True)

    # Step 3: Reliable deterministic fallback
    logger.info(f"Executing deterministic review synthesis for {clean_rx_id}")
    return _synthesize_deterministic_review(clean_rx_id, evidence)


if __name__ == "__main__":
    rx = sys.argv[1] if len(sys.argv) > 1 else "RX-1002"
    print("=" * 65)
    print(f"  PharmacyGuard - Structured Review for {rx}")
    print("=" * 65)
    review = run_structured_prescription_review(rx)
    print(json.dumps(review.model_dump(), indent=2))
    print("=" * 65)
