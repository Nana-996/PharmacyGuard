"""
FastAPI router for PharmacyGuard Inventory Catalog & Stock Monitoring.
Protected by JWT authentication and Role-Based Access Control (RBAC).
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from backend.data.database import (
    get_db_connection,
    initialize_database,
)
from backend.tools.inventory_tools import (
    get_low_stock_items,
    get_inventory_summary,
)
from backend.auth.dependencies import require_roles

router = APIRouter(prefix="/api/inventory", tags=["Inventory Management"])

INVENTORY_ROLES = ["STAFF_PHARMACIST", "CHIEF_PHARMACIST", "ADMIN"]


@router.get("")
def list_all_inventory(
    search: Optional[str] = Query(None, description="Search by medication or generic name"),
    status: Optional[str] = Query(None, description="Filter by stock status: AVAILABLE, LOW STOCK, OUT OF STOCK"),
    current_user: Dict[str, Any] = Depends(require_roles(INVENTORY_ROLES))
) -> Dict[str, Any]:
    """Retrieves all hospital pharmacy catalog medications with current stock levels."""
    try:
        initialize_database()
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                inventory_id, medication, generic_name, strength, dosage_form,
                quantity_on_hand, reorder_level, unit, last_updated
            FROM inventory
        """
        conditions = []
        params = []

        if search:
            clean_search = f"%{search.strip().lower()}%"
            conditions.append("(LOWER(medication) LIKE ? OR LOWER(generic_name) LIKE ?)")
            params.extend([clean_search, clean_search])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY quantity_on_hand ASC, medication ASC"

        cursor.execute(query, tuple(params))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        # Compute stock status for each item
        items: List[Dict[str, Any]] = []
        for r in rows:
            qty = r["quantity_on_hand"]
            reorder = r["reorder_level"]
            if qty == 0:
                item_status = "OUT OF STOCK"
            elif qty <= reorder:
                item_status = "LOW STOCK"
            else:
                item_status = "AVAILABLE"

            if status and status.upper() != item_status:
                continue

            items.append({
                "inventory_id": r["inventory_id"],
                "medication": r["medication"],
                "generic_name": r["generic_name"],
                "strength": r["strength"],
                "dosage_form": r["dosage_form"],
                "quantity_on_hand": qty,
                "reorder_level": reorder,
                "unit": r["unit"],
                "deficit_to_reorder": max(0, reorder - qty),
                "stock_status": item_status,
                "last_updated": r["last_updated"]
            })

        return {
            "status": "success",
            "total": len(items),
            "data": items
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/low-stock")
def get_low_stock_endpoint(
    current_user: Dict[str, Any] = Depends(require_roles(INVENTORY_ROLES))
) -> Dict[str, Any]:
    """Retrieves all pharmacy inventory items at or below reorder threshold."""
    try:
        result = get_low_stock_items()
        return {
            "status": "success",
            "total_low_stock_items": result["total_low_stock_items"],
            "data": result["low_stock_items"]
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/summary")
def get_inventory_summary_endpoint(
    current_user: Dict[str, Any] = Depends(require_roles(INVENTORY_ROLES))
) -> Dict[str, Any]:
    """Retrieves aggregate pharmacy stock health metrics and counts."""
    try:
        result = get_inventory_summary()
        return {
            "status": "success",
            "data": result["inventory_summary"]
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
