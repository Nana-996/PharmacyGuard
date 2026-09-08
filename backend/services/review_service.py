"""
Pharmacist Review & Escalation Service for PharmacyGuard.
Manages the human-in-the-loop workflow, structured agent reviews,
finding persistence, pharmacist decision actions, and immutable audit logs.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from backend.data.database import (
    insert_pharmacist_review,
    insert_review_finding,
    insert_audit_event,
    update_pharmacist_decision,
    fetch_review_by_id,
    fetch_all_reviews,
    fetch_prescription_details,
    insert_escalation_resolution,
    fetch_escalation_resolutions,
    dispense_prescription_inventory,
)

from backend.agent.pharmacy_agent import run_structured_prescription_review, AgentStructuredReview


def create_review(
    prescription_id: str,
    structured_review: Optional[AgentStructuredReview] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a new prescription review by invoking the Strands AI agent (or using provided review),
    validating the structured findings, persisting them in SQLite, initializing the pharmacist decision
    as 'PENDING', and logging audit trail events.
    """
    clean_rx_id = prescription_id.strip().upper()

    # 1. Verify prescription exists in database
    rx_details = fetch_prescription_details(clean_rx_id, db_path=db_path)
    if not rx_details:
        raise ValueError(f"Prescription '{clean_rx_id}' not found in the hospital system.")

    # 2. Run agent investigation if not directly supplied (e.g. during mock/direct testing)
    review_output = structured_review or run_structured_prescription_review(clean_rx_id)

    # 3. Generate unique identifiers and timestamp
    review_id = f"REV-{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()

    # 4. Persist review record with PENDING decision
    insert_pharmacist_review(
        review_id=review_id,
        prescription_id=clean_rx_id,
        agent_review_status=review_output.overall_status,
        pharmacist_decision="PENDING",
        pharmacist_notes=None,
        reviewed_by=None,
        created_at=created_at,
        reviewed_at=None,
        db_path=db_path
    )

    # 5. Persist individual findings
    for idx, finding in enumerate(review_output.findings, start=1):
        finding_id = f"FND-{uuid.uuid4().hex[:8].upper()}"
        insert_review_finding(
            finding_id=finding_id,
            review_id=review_id,
            category=finding.category,
            severity=finding.severity,
            title=finding.title,
            description=finding.description,
            evidence_source=finding.evidence_source,
            evidence_data=finding.evidence,
            requires_action=finding.requires_action,
            created_at=created_at,
            db_path=db_path
        )
        # Log finding creation event
        insert_audit_event(
            event_type="FINDING_CREATED",
            actor_type="AGENT",
            actor_id="PharmacyGuard-Agent",
            prescription_id=clean_rx_id,
            review_id=review_id,
            event_data=json.dumps({
                "finding_id": finding_id,
                "category": finding.category,
                "title": finding.title,
                "severity": finding.severity
            }),
            timestamp=created_at,
            db_path=db_path
        )

    # 6. Log audit event for review creation
    insert_audit_event(
        event_type="AGENT_REVIEW_CREATED",
        actor_type="AGENT",
        actor_id="PharmacyGuard-Agent",
        prescription_id=clean_rx_id,
        review_id=review_id,
        event_data=json.dumps({
            "overall_status": review_output.overall_status,
            "total_findings": len(review_output.findings),
            "pharmacist_action_summary": review_output.pharmacist_action_summary
        }),
        timestamp=created_at,
        db_path=db_path
    )

    # 7. Return complete persisted case
    result = fetch_review_by_id(review_id, db_path=db_path)
    if not result:
        raise RuntimeError(f"Failed to retrieve newly created review '{review_id}'.")
    return result


def get_pending_reviews(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all reviews currently pending human pharmacist decision."""
    return fetch_all_reviews(decision="PENDING", db_path=db_path)


def get_all_reviews_service(
    decision: Optional[str] = None,
    status: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves reviews with optional decision and status filtering."""
    return fetch_all_reviews(decision=decision, status=status, db_path=db_path)


def get_review(review_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a single complete review record by ID."""
    return fetch_review_by_id(review_id.strip(), db_path=db_path)


def accept_review(
    review_id: str,
    pharmacist_id: str,
    notes: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Pharmacist action: Agrees with agent's findings and accepts the review.
    Transitions decision to 'ACCEPTED' and logs audit event.
    """
    clean_rev_id = review_id.strip()
    clean_pharm_id = pharmacist_id.strip()
    if not clean_pharm_id:
        raise ValueError("Pharmacist ID must be provided to accept a review.")

    review = fetch_review_by_id(clean_rev_id, db_path=db_path)
    if not review:
        raise ValueError(f"Review '{clean_rev_id}' not found.")

    ts = datetime.now(timezone.utc).isoformat()
    success = update_pharmacist_decision(
        review_id=clean_rev_id,
        decision="ACCEPTED",
        pharmacist_id=clean_pharm_id,
        notes=notes,
        reviewed_at=ts,
        db_path=db_path
    )
    if not success:
        raise RuntimeError(f"Failed to update decision for review '{clean_rev_id}'.")

    insert_audit_event(
        event_type="PHARMACIST_REVIEWED",
        actor_type="PHARMACIST",
        actor_id=clean_pharm_id,
        prescription_id=review["prescription_id"],
        review_id=clean_rev_id,
        event_data=json.dumps({
            "action": "ACCEPTED",
            "notes": notes,
            "agent_status": review["agent_review_status"]
        }),
        timestamp=ts,
        db_path=db_path
    )

    updated = fetch_review_by_id(clean_rev_id, db_path=db_path)
    return updated  # type: ignore


def override_review(
    review_id: str,
    pharmacist_id: str,
    notes: str,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Pharmacist action: Disagrees with or modifies agent's assessment.
    Transitions decision to 'OVERRIDDEN' with mandatory clinical rationale notes.
    """
    clean_rev_id = review_id.strip()
    clean_pharm_id = pharmacist_id.strip()
    if not clean_pharm_id:
        raise ValueError("Pharmacist ID must be provided to override a review.")
    if not notes or not notes.strip():
        raise ValueError("Pharmacist notes explaining clinical rationale are mandatory when overriding a review.")

    review = fetch_review_by_id(clean_rev_id, db_path=db_path)
    if not review:
        raise ValueError(f"Review '{clean_rev_id}' not found.")

    ts = datetime.now(timezone.utc).isoformat()
    success = update_pharmacist_decision(
        review_id=clean_rev_id,
        decision="OVERRIDDEN",
        pharmacist_id=clean_pharm_id,
        notes=notes.strip(),
        reviewed_at=ts,
        db_path=db_path
    )
    if not success:
        raise RuntimeError(f"Failed to override review '{clean_rev_id}'.")

    insert_audit_event(
        event_type="PHARMACIST_OVERRIDDEN",
        actor_type="PHARMACIST",
        actor_id=clean_pharm_id,
        prescription_id=review["prescription_id"],
        review_id=clean_rev_id,
        event_data=json.dumps({
            "action": "OVERRIDDEN",
            "notes": notes.strip(),
            "agent_status": review["agent_review_status"]
        }),
        timestamp=ts,
        db_path=db_path
    )

    updated = fetch_review_by_id(clean_rev_id, db_path=db_path)
    return updated  # type: ignore


def escalate_review(
    review_id: str,
    pharmacist_id: str,
    notes: str,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Pharmacist action: Escalates complex prescription to senior / chief pharmacist.
    Transitions decision to 'ESCALATED' with escalation reasons.
    """
    clean_rev_id = review_id.strip()
    clean_pharm_id = pharmacist_id.strip()
    if not clean_pharm_id:
        raise ValueError("Pharmacist ID must be provided to escalate a review.")
    if not notes or not notes.strip():
        raise ValueError("Pharmacist notes detailing escalation reasons are required.")

    review = fetch_review_by_id(clean_rev_id, db_path=db_path)
    if not review:
        raise ValueError(f"Review '{clean_rev_id}' not found.")

    ts = datetime.now(timezone.utc).isoformat()
    success = update_pharmacist_decision(
        review_id=clean_rev_id,
        decision="ESCALATED",
        pharmacist_id=clean_pharm_id,
        notes=notes.strip(),
        reviewed_at=ts,
        db_path=db_path
    )
    if not success:
        raise RuntimeError(f"Failed to escalate review '{clean_rev_id}'.")

    insert_audit_event(
        event_type="REVIEW_ESCALATED",
        actor_type="PHARMACIST",
        actor_id=clean_pharm_id,
        prescription_id=review["prescription_id"],
        review_id=clean_rev_id,
        event_data=json.dumps({
            "action": "ESCALATED",
            "notes": notes.strip(),
            "agent_status": review["agent_review_status"]
        }),
        timestamp=ts,
        db_path=db_path
    )

    updated = fetch_review_by_id(clean_rev_id, db_path=db_path)
    return updated  # type: ignore


def resolve_chief_escalation(
    review_id: str,
    chief_id: str,
    chief_decision: str,
    chief_notes: str,
    action_required: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Chief Pharmacist Action: Resolves an escalated case.
    Options: 'RESOLVED_APPROVED', 'RETURNED_TO_STAFF', 'DIRECT_OVERRIDE_APPROVED'.
    Crucially preserves the staff pharmacist's original reviewed_by and decision permanently in SQLite.
    """
    clean_rev_id = review_id.strip()
    clean_chief_id = chief_id.strip()
    if not clean_chief_id:
        raise ValueError("Chief Pharmacist ID must be provided.")
    if not chief_notes or not chief_notes.strip():
        raise ValueError("Chief Pharmacist consultation rationale notes are mandatory.")

    review = fetch_review_by_id(clean_rev_id, db_path=db_path)
    if not review:
        raise ValueError(f"Review '{clean_rev_id}' not found.")

    res_id = f"RES-{uuid.uuid4().hex[:8].upper()}"
    ts = datetime.now(timezone.utc).isoformat()

    # 1. Insert escalation resolution record
    resolution = insert_escalation_resolution(
        resolution_id=res_id,
        review_id=clean_rev_id,
        prescription_id=review["prescription_id"],
        chief_id=clean_chief_id,
        chief_decision=chief_decision.strip().upper(),
        chief_notes=chief_notes.strip(),
        action_required=action_required.strip() if action_required else None,
        resolved_at=ts,
        db_path=db_path
    )

    # 2. Log immutable audit trail entry
    event_type = "ESCALATION_RESOLVED" if chief_decision.strip().upper() != "RETURNED_TO_STAFF" else "ESCALATION_RETURNED"
    insert_audit_event(
        event_type=event_type,
        actor_type="CHIEF_PHARMACIST",
        actor_id=clean_chief_id,
        prescription_id=review["prescription_id"],
        review_id=clean_rev_id,
        event_data=json.dumps({
            "chief_decision": chief_decision.strip().upper(),
            "chief_notes": chief_notes.strip(),
            "action_required": action_required,
            "original_pharmacist": review.get("reviewed_by"),
            "original_notes": review.get("pharmacist_notes")
        }),
        timestamp=ts,
        db_path=db_path
    )

    # 3. Return full updated review with escalation resolution attached
    updated_review = fetch_review_by_id(clean_rev_id, db_path=db_path)
    return {
        "status": "success",
        "message": f"Escalation successfully resolved by Chief Pharmacist ({chief_decision}).",
        "resolution": resolution,
        "review": updated_review
    }


def dispense_review_prescription(
    review_id: str,
    pharmacist_id: str,
    notes: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Pharmacist Action: Executes physical dispensing for an accepted/authorized prescription.
    Decrements stock in inventory and logs inventory transaction.
    """
    clean_rev_id = review_id.strip()
    clean_pharm_id = pharmacist_id.strip()

    review = fetch_review_by_id(clean_rev_id, db_path=db_path)
    if not review:
        raise ValueError(f"Review '{clean_rev_id}' not found.")

    decision = review.get("pharmacist_decision", "")
    has_chief_approval = any(
        r.get("chief_decision") in ["RESOLVED_APPROVED", "DIRECT_OVERRIDE_APPROVED"]
        for r in review.get("escalation_resolutions", [])
    )

    if decision not in ["ACCEPTED", "OVERRIDDEN"] and not has_chief_approval:
        raise ValueError(f"Prescription review is in status '{decision}' and cannot be dispensed without clinical approval or Chief resolution.")

    dispense_result = dispense_prescription_inventory(
        prescription_id=review["prescription_id"],
        actor_id=clean_pharm_id,
        notes=notes,
        db_path=db_path
    )

    return {
        "status": "success",
        "message": f"Prescription '{review['prescription_id']}' dispensed successfully.",
        "data": dispense_result
    }

