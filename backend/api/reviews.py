"""
FastAPI router for PharmacyGuard Pharmacist Review & Escalation Workflows.
Protected by JWT authentication and Role-Based Access Control (RBAC).
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status, Depends
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user, require_roles
from backend.services.review_service import (
    create_review,
    get_pending_reviews,
    get_all_reviews_service,
    get_review,
    accept_review,
    override_review,
    escalate_review,
    resolve_chief_escalation,
    dispense_review_prescription,
)


router = APIRouter(prefix="/api/reviews", tags=["Pharmacist Reviews"])

PHARMACIST_ROLES = ["STAFF_PHARMACIST", "CHIEF_PHARMACIST"]


class CreateReviewRequest(BaseModel):
    prescription_id: str = Field(..., min_length=1, description="Prescription ID to investigate and review (e.g. 'RX-1001')")


class PharmacistDecisionRequest(BaseModel):
    pharmacist_id: Optional[str] = Field(None, description="Optional pharmacist ID (automatically derived from session)")
    notes: Optional[str] = Field(None, description="Pharmacist clinical rationale or escalation notes")


class PharmacistOverrideRequest(BaseModel):
    pharmacist_id: Optional[str] = Field(None, description="Optional pharmacist ID (automatically derived from session)")
    notes: str = Field(..., min_length=3, description="Mandatory clinical rationale explaining why the agent findings are overridden")


class PharmacistEscalateRequest(BaseModel):
    pharmacist_id: Optional[str] = Field(None, description="Optional pharmacist ID (automatically derived from session)")
    notes: str = Field(..., min_length=3, description="Mandatory notes describing why the case requires escalation to chief pharmacist")


@router.post("", status_code=status.HTTP_201_CREATED)
def start_review_endpoint(
    payload: CreateReviewRequest,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
) -> Dict[str, Any]:
    """
    Triggers an agent prescription review: retrieves prescription, performs clinical verification,
    checks inventory stock, persists structured findings, sets decision to PENDING, and records audit logs.
    """
    try:
        review = create_review(prescription_id=payload.prescription_id)
        return {
            "status": "success",
            "message": f"Prescription review created successfully with decision PENDING.",
            "data": review
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating prescription review: {str(exc)}"
        )


@router.get("")
def list_reviews_endpoint(
    decision: Optional[str] = Query(None, description="Filter by decision (PENDING, ACCEPTED, OVERRIDDEN, ESCALATED)"),
    status: Optional[str] = Query(None, description="Filter by agent status (CLEAR, REVIEW, HIGH_PRIORITY_REVIEW)"),
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
) -> Dict[str, Any]:
    """Retrieves all reviews or filtered reviews."""
    try:
        reviews = get_all_reviews_service(decision=decision, status=status)
        return {
            "status": "success",
            "total": len(reviews),
            "data": reviews
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/pending")
def list_pending_reviews_endpoint(
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
) -> Dict[str, Any]:
    """Retrieves all prescription reviews pending human pharmacist action."""
    try:
        pending = get_pending_reviews()
        return {
            "status": "success",
            "total_pending": len(pending),
            "data": pending
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{review_id}")
def get_review_details_endpoint(
    review_id: str,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
) -> Dict[str, Any]:
    """
    Retrieves complete review details by review_id including prescription details,
    clinical findings, inventory findings, tool evidence, pharmacist decision, and audit trail.
    """
    review = get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail=f"Review '{review_id}' not found.")
    return {
        "status": "success",
        "data": review
    }


@router.post("/{review_id}/accept")
def accept_review_endpoint(
    review_id: str,
    payload: PharmacistDecisionRequest,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
) -> Dict[str, Any]:
    """
    Pharmacist action: Accept the review findings and recommendations.
    Transitions status to ACCEPTED using authenticated user identity and records audit event.
    """
    effective_pharm_id = current_user["user_id"]
    try:
        updated = accept_review(
            review_id=review_id,
            pharmacist_id=effective_pharm_id,
            notes=payload.notes
        )
        return {
            "status": "success",
            "message": f"Review '{review_id}' accepted by pharmacist {effective_pharm_id}.",
            "data": updated
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{review_id}/override")
def override_review_endpoint(
    review_id: str,
    payload: PharmacistOverrideRequest,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
) -> Dict[str, Any]:
    """
    Pharmacist action: Override agent findings with clinical rationale.
    Transitions status to OVERRIDDEN using authenticated user identity and records audit event.
    """
    effective_pharm_id = current_user["user_id"]
    try:
        updated = override_review(
            review_id=review_id,
            pharmacist_id=effective_pharm_id,
            notes=payload.notes
        )
        return {
            "status": "success",
            "message": f"Review '{review_id}' overridden by pharmacist {effective_pharm_id}.",
            "data": updated
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{review_id}/escalate")
def escalate_review_endpoint(
    review_id: str,
    payload: PharmacistEscalateRequest,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
) -> Dict[str, Any]:
    """
    Pharmacist action: Escalate review to senior/chief pharmacist for secondary evaluation.
    Transitions status to ESCALATED using authenticated user identity and records audit event.
    """
    effective_pharm_id = current_user["user_id"]
    try:
        updated = escalate_review(
            review_id=review_id,
            pharmacist_id=effective_pharm_id,
            notes=payload.notes
        )
        return {
            "status": "success",
            "message": f"Review '{review_id}' escalated by pharmacist {effective_pharm_id}.",
            "data": updated
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class SendPrescriberReportRequest(BaseModel):
    recipient_doctor: str = Field(..., min_length=1, description="Prescribing physician name")
    report_type: str = Field(default="AI_FINDINGS_REPORT", description="'AI_FINDINGS_REPORT' or 'CUSTOM_PHARMACIST_REPORT'")
    subject: str = Field(..., min_length=3, description="Subject of clinical consultation")
    message_body: str = Field(..., min_length=5, description="Full message body / report content")
    ai_findings_included: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of structured AI findings attached")
    suggested_modifications: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional suggested regimen modifications")



@router.post("/{review_id}/send-prescriber-report", status_code=status.HTTP_201_CREATED)
def send_prescriber_report_endpoint(
    review_id: str,
    payload: SendPrescriberReportRequest,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
) -> Dict[str, Any]:
    """
    Sends a clinical safety finding report or custom pharmacist evaluation to the prescribing doctor.
    Persists communication record in SQLite and logs audit event under authenticated user.
    """
    from backend.data.database import insert_prescriber_communication, fetch_review_by_id
    import uuid

    review = fetch_review_by_id(review_id)
    if not review:
        raise HTTPException(status_code=404, detail=f"Review '{review_id}' not found.")

    cid = f"COM-{uuid.uuid4().hex[:8].upper()}"
    comm = insert_prescriber_communication(
        communication_id=cid,
        prescription_id=review["prescription_id"],
        review_id=review_id,
        sender_id=current_user["user_id"],
        recipient_doctor=payload.recipient_doctor,
        report_type=payload.report_type,
        subject=payload.subject,
        message_body=payload.message_body,
        ai_findings_included=payload.ai_findings_included,
        suggested_modifications=payload.suggested_modifications
    )

    return {
        "status": "success",
        "message": f"Prescriber communication '{cid}' sent to {payload.recipient_doctor}.",
        "data": comm
    }


@router.get("/{review_id}/communications")
def get_review_communications_endpoint(
    review_id: str,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
) -> Dict[str, Any]:
    """Retrieves all prescriber communications sent for a review."""
    from backend.data.database import fetch_prescriber_communications
    items = fetch_prescriber_communications(review_id=review_id)
    return {
        "status": "success",
        "total": len(items),
        "data": items
    }


class ChiefEscalationResolutionRequest(BaseModel):
    chief_decision: str = Field(..., description="'RESOLVED_APPROVED', 'RETURNED_TO_STAFF', or 'DIRECT_OVERRIDE_APPROVED'")
    chief_notes: str = Field(..., min_length=3, description="Mandatory clinical rationale and departmental sign-off notes")
    action_required: Optional[str] = Field(None, description="Optional action directive when returning case to staff pharmacist")


class DispensePrescriptionRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Optional pharmacist dispensing notes or lot confirmation")


@router.post("/{review_id}/resolve-escalation")
def resolve_escalation_endpoint(
    review_id: str,
    payload: ChiefEscalationResolutionRequest,
    current_user: Dict[str, Any] = Depends(require_roles(["CHIEF_PHARMACIST"]))
) -> Dict[str, Any]:
    """
    Chief Pharmacist only endpoint: Formally resolves an escalated clinical review.
    Preserves original staff pharmacist decision and notes while recording executive decision.
    """
    try:
        result = resolve_chief_escalation(
            review_id=review_id,
            chief_id=current_user["user_id"],
            chief_decision=payload.chief_decision,
            chief_notes=payload.chief_notes,
            action_required=payload.action_required
        )
        return result
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{review_id}/dispense")
def dispense_prescription_endpoint(
    review_id: str,
    payload: Optional[DispensePrescriptionRequest] = None,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
) -> Dict[str, Any]:
    """
    Pharmacist Action: Executes physical dispensing for an accepted or Chief-authorized prescription.
    Decrements SQLite inventory quantities and logs inventory transactions.
    """
    try:
        notes = payload.notes if payload else None
        result = dispense_review_prescription(
            review_id=review_id,
            pharmacist_id=current_user["user_id"],
            notes=notes
        )
        return result
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


