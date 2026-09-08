"""
FastAPI router for PharmacyGuard Student Learning Workspace & De-Identified Educational Training Cases.
Accessible to Pharmacy Students, Interns, and Clinical Faculty.
"""

import json
import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status, Depends
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user, require_roles
from backend.data.database import (
    fetch_educational_cases,
    fetch_educational_case_by_id,
    insert_educational_case,
    record_student_submission,
    fetch_student_progress,
    insert_audit_event,
    fetch_review_by_id
)

router = APIRouter(prefix="/api/student", tags=["Student Training & Educational Cases"])

ALL_USERS = ["PHARMACY_STUDENT", "STAFF_PHARMACIST", "CHIEF_PHARMACIST", "ADMIN"]
PHARMACIST_ROLES = ["STAFF_PHARMACIST", "CHIEF_PHARMACIST"]


class StudentSubmissionRequest(BaseModel):
    selected_option_index: int = Field(..., ge=0, description="0-indexed chosen multiple choice option")
    student_notes: Optional[str] = Field(None, description="Optional clinical reasoning or student notes")


class PublishCaseRequest(BaseModel):
    title: str = Field(..., min_length=3, description="Educational case title")
    clinical_category: str = Field(..., description="'ALLERGY', 'DUPLICATION', 'INDICATION', 'DOSAGE', or 'INTERACTION'")
    difficulty: str = Field(default="INTERMEDIATE", description="'BEGINNER', 'INTERMEDIATE', or 'ADVANCED'")
    scenario_text: str = Field(..., min_length=10, description="De-identified patient clinical scenario vignette")
    medications: List[Dict[str, Any]] = Field(..., min_length=1, description="De-identified list of prescribed medications")
    key_safety_challenge: str = Field(..., min_length=5, description="Core safety challenge summary")
    multiple_choice_question: str = Field(..., min_length=5, description="Challenge question prompt")
    options: List[str] = Field(..., min_length=2, max_length=6, description="Multiple choice options list")
    correct_option_index: int = Field(..., ge=0, description="Index of the correct choice")
    explanation_text: str = Field(..., min_length=10, description="Pharmacological teaching rationale and guideline citations")
    source_review_id: Optional[str] = Field(None, description="Optional review ID from which this case was synthesized")


@router.get("/cases")
def list_educational_cases(
    category: Optional[str] = Query(None, description="Filter by clinical category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    current_user: Dict[str, Any] = Depends(require_roles(ALL_USERS))
) -> Dict[str, Any]:
    """Retrieves all published de-identified clinical training cases."""
    try:
        cases = fetch_educational_cases(category=category, difficulty=difficulty)
        return {
            "status": "success",
            "total": len(cases),
            "data": cases
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/cases/{case_id}")
def get_educational_case(
    case_id: str,
    current_user: Dict[str, Any] = Depends(require_roles(ALL_USERS))
) -> Dict[str, Any]:
    """Retrieves a single de-identified educational case by ID."""
    case = fetch_educational_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Educational case '{case_id}' not found.")
    return {
        "status": "success",
        "data": case
    }


@router.post("/cases/{case_id}/submit")
def submit_case_answer(
    case_id: str,
    payload: StudentSubmissionRequest,
    current_user: Dict[str, Any] = Depends(require_roles(ALL_USERS))
) -> Dict[str, Any]:
    """
    Submits a student's answer for a clinical training case.
    Evaluates correctness, records submission, and returns the pharmacological explanation.
    """
    case = fetch_educational_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Educational case '{case_id}' not found.")

    correct_index = case["correct_option_index"]
    is_correct = (payload.selected_option_index == correct_index)

    sub_id = f"SUB-{uuid.uuid4().hex[:8].upper()}"
    submission = record_student_submission(
        submission_id=sub_id,
        case_id=case_id,
        student_id=current_user["user_id"],
        selected_option_index=payload.selected_option_index,
        is_correct=is_correct,
        student_notes=payload.student_notes
    )

    insert_audit_event(
        event_type="STUDENT_CASE_COMPLETED",
        actor_type=current_user["role"],
        actor_id=current_user["user_id"],
        prescription_id=case.get("source_review_id") or case_id,
        review_id=case.get("source_review_id"),
        event_data={
            "case_id": case_id,
            "case_title": case["title"],
            "selected_index": payload.selected_option_index,
            "is_correct": is_correct,
            "student_notes": payload.student_notes
        }
    )

    return {
        "status": "success",
        "is_correct": is_correct,
        "selected_option_index": payload.selected_option_index,
        "correct_option_index": correct_index,
        "explanation_text": case["explanation_text"],
        "submission": submission
    }


@router.get("/progress")
def get_student_progress(
    current_user: Dict[str, Any] = Depends(require_roles(ALL_USERS))
) -> Dict[str, Any]:
    """Retrieves current student completion statistics, accuracy, and recent submissions."""
    try:
        progress = fetch_student_progress(student_id=current_user["user_id"])
        return {
            "status": "success",
            "data": progress
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/cases/publish", status_code=status.HTTP_201_CREATED)
def publish_educational_case(
    payload: PublishCaseRequest,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
) -> Dict[str, Any]:
    """
    Staff Pharmacist / Chief Pharmacist endpoint:
    Publishes a de-identified clinical case from resolved hospital reviews into the student training curriculum.
    """
    try:
        cid = f"EDU-{uuid.uuid4().hex[:6].upper()}"
        created = insert_educational_case(
            case_id=cid,
            title=payload.title,
            clinical_category=payload.clinical_category,
            difficulty=payload.difficulty,
            scenario_text=payload.scenario_text,
            deidentified_prescription_json=json.dumps(payload.medications),
            key_safety_challenge=payload.key_safety_challenge,
            multiple_choice_question=payload.multiple_choice_question,
            options_json=json.dumps(payload.options),
            correct_option_index=payload.correct_option_index,
            explanation_text=payload.explanation_text,
            source_review_id=payload.source_review_id,
            published_by=current_user["user_id"]
        )

        insert_audit_event(
            event_type="EDUCATIONAL_CASE_PUBLISHED",
            actor_type="PHARMACIST",
            actor_id=current_user["user_id"],
            prescription_id=payload.source_review_id or cid,
            review_id=payload.source_review_id,
            event_data={
                "case_id": cid,
                "title": payload.title,
                "clinical_category": payload.clinical_category
            }
        )

        return {
            "status": "success",
            "message": f"Educational case '{cid}' published successfully.",
            "data": created
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
