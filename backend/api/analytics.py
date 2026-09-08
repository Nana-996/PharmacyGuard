"""
FastAPI router for PharmacyGuard Chief Pharmacist Analytics & Operations Dashboard metrics.
Protected by JWT authentication and Role-Based Access Control (RBAC).
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from backend.data.database import (
    get_db_connection,
    initialize_database,
    query_inventory_overview_summary,
)
from backend.auth.dependencies import require_roles

router = APIRouter(prefix="/api/analytics", tags=["Chief Pharmacist Analytics"])

ANALYTICS_ROLES = ["STAFF_PHARMACIST", "CHIEF_PHARMACIST", "ADMIN"]
AUDIT_ROLES = ["CHIEF_PHARMACIST", "ADMIN"]


@router.get("/dashboard")
def get_dashboard_analytics(
    current_user: Dict[str, Any] = Depends(require_roles(ANALYTICS_ROLES))
) -> Dict[str, Any]:
    """
    Computes real aggregate metrics across reviews, pharmacist actions, findings,
    and inventory health for the dashboard and operations view.
    """
    try:
        initialize_database()
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Review status and decision metrics
        cursor.execute("SELECT COUNT(*) AS total FROM pharmacist_reviews")
        total_reviews = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS pending FROM pharmacist_reviews WHERE pharmacist_decision = 'PENDING'")
        pending_reviews = cursor.fetchone()["pending"]

        cursor.execute("SELECT COUNT(*) AS accepted FROM pharmacist_reviews WHERE pharmacist_decision = 'ACCEPTED'")
        accepted_reviews = cursor.fetchone()["accepted"]

        cursor.execute("SELECT COUNT(*) AS overridden FROM pharmacist_reviews WHERE pharmacist_decision = 'OVERRIDDEN'")
        overridden_reviews = cursor.fetchone()["overridden"]

        cursor.execute("SELECT COUNT(*) AS escalated FROM pharmacist_reviews WHERE pharmacist_decision = 'ESCALATED'")
        escalated_reviews = cursor.fetchone()["escalated"]

        cursor.execute("SELECT COUNT(*) AS high_priority FROM pharmacist_reviews WHERE agent_review_status = 'HIGH_PRIORITY_REVIEW'")
        high_priority_reviews = cursor.fetchone()["high_priority"]

        cursor.execute("SELECT COUNT(*) AS review_count FROM pharmacist_reviews WHERE agent_review_status = 'REVIEW'")
        standard_review_status = cursor.fetchone()["review_count"]

        cursor.execute("SELECT COUNT(*) AS clear_count FROM pharmacist_reviews WHERE agent_review_status = 'CLEAR'")
        clear_reviews = cursor.fetchone()["clear_count"]

        # 2. Recurring findings by category
        cursor.execute("""
            SELECT category, COUNT(*) as count,
                   SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as high_severity_count
            FROM review_findings
            GROUP BY category
            ORDER BY count DESC
        """)
        category_rows = cursor.fetchall()
        finding_categories = [
            {
                "category": r["category"],
                "count": r["count"],
                "high_severity_count": r["high_severity_count"]
            }
            for r in category_rows
        ]

        # 3. Recent escalations for chief pharmacist oversight
        cursor.execute("""
            SELECT r.review_id, r.prescription_id, r.reviewed_by AS pharmacist_id,
                   r.pharmacist_notes AS reason, r.reviewed_at AS timestamp,
                   r.agent_review_status, p.name AS patient_name
            FROM pharmacist_reviews r
            JOIN prescriptions rx ON r.prescription_id = rx.prescription_id
            JOIN patients p ON rx.patient_id = p.patient_id
            WHERE r.pharmacist_decision = 'ESCALATED'
            GROUP BY r.review_id
            ORDER BY r.reviewed_at DESC
            LIMIT 10
        """)
        escalation_rows = cursor.fetchall()
        recent_escalations = [dict(e) for e in escalation_rows]

        # 4. Recent reviews list with patient name and findings count
        cursor.execute("""
            SELECT r.review_id, r.prescription_id, r.agent_review_status, r.pharmacist_decision,
                   r.created_at, r.reviewed_at, p.name AS patient_name,
                   (SELECT COUNT(*) FROM review_findings f WHERE f.review_id = r.review_id) AS findings_count
            FROM pharmacist_reviews r
            JOIN prescriptions rx ON r.prescription_id = rx.prescription_id
            JOIN patients p ON rx.patient_id = p.patient_id
            GROUP BY r.review_id
            ORDER BY r.created_at DESC
            LIMIT 8
        """)
        recent_review_rows = cursor.fetchall()
        recent_reviews = [dict(rr) for rr in recent_review_rows]

        conn.close()

        # 5. Inventory summary metrics
        inv_summary = query_inventory_overview_summary()

        return {
            "status": "success",
            "data": {
                "summary_cards": {
                    "pending_reviews": pending_reviews,
                    "high_priority_reviews": high_priority_reviews,
                    "low_stock_items": inv_summary.get("number_low_stock", 0),
                    "out_of_stock_items": inv_summary.get("number_out_of_stock", 0),
                    "total_reviews": total_reviews,
                    "accepted_reviews": accepted_reviews,
                    "overridden_reviews": overridden_reviews,
                    "escalated_reviews": escalated_reviews,
                    "clear_reviews": clear_reviews,
                    "stock_health_percentage": inv_summary.get("stock_health_percentage", "0%")
                },
                "finding_categories": finding_categories,
                "recent_escalations": recent_escalations,
                "recent_reviews": recent_reviews,
                "inventory_overview": inv_summary
            }
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/audit-log")
def get_audit_trail_endpoint(
    limit: int = Query(50, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(require_roles(AUDIT_ROLES))
):
    """
    Chief Pharmacist only endpoint: Access comprehensive hospital pharmacy audit log trail.
    """
    try:
        initialize_database()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT audit_id, event_type, actor_type, actor_id, prescription_id, review_id, event_data, timestamp
            FROM audit_log
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,)
        )
        logs = [dict(r) for r in cursor.fetchall()]
        conn.close()

        return {
            "status": "success",
            "total": len(logs),
            "data": logs
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
