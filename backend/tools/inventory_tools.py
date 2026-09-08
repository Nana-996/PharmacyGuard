"""
Pharmacy Inventory & Stock Awareness Tools for PharmacyGuard Strands Agent.
Exposes real-time stock availability, low-stock alerts, and operational inventory metrics.

NOTE: All inventory records are synthetic. The agent must never autonomously substitute
or change medications based on stock availability. The licensed pharmacist makes all decisions.
"""

from typing import Dict, Any, List, Union
from strands import tool
from backend.data.database import (
    query_inventory_check,
    query_low_stock_inventory,
    query_inventory_overview_summary,
)


def _normalize_inventory_input(meds: Union[List[Any], str]) -> List[Dict[str, str]]:
    """Helper to convert varied input formats into structured list of medication dicts with strength."""
    results: List[Dict[str, str]] = []

    if isinstance(meds, list):
        for item in meds:
            if isinstance(item, dict):
                results.append({
                    "medication": item.get("medication") or item.get("medication_name") or item.get("generic_name") or "",
                    "strength": item.get("strength") or "",
                    "dosage_form": item.get("dosage_form") or item.get("route") or ""
                })
            elif isinstance(item, str) and item.strip():
                results.append({"medication": item.strip(), "strength": "", "dosage_form": ""})
    elif isinstance(meds, str) and meds.strip():
        parts = [p.strip() for p in meds.split(",") if p.strip()]
        for p in parts:
            results.append({"medication": p, "strength": "", "dosage_form": ""})

    return results


@tool
def check_inventory(prescribed_medications: Union[List[Any], str]) -> Dict[str, Any]:
    """Check stock availability in the hospital pharmacy for one or more prescribed medications.

    Call this tool to evaluate whether prescribed medicines are in stock, low in stock, out of stock,
    or if the exact strength is unavailable.

    Args:
        prescribed_medications: List of prescribed medication names or dictionaries with medication, strength, and dosage form.

    Returns:
        A dictionary containing:
        - status: 'success'
        - inventory_results: List of stock checks for each requested drug (requested_medication, requested_strength,
          requested_dosage_form, availability_status, quantity_available, stock_status, last_updated, requires_pharmacist_attention)
        - has_out_of_stock: boolean indicating if any requested drug is out of stock
        - has_low_stock: boolean indicating if any requested drug is low stock
        - all_available: boolean indicating if all requested items are fully in stock
        - safety_disclaimer: Standard safety reminder
    """
    items = _normalize_inventory_input(prescribed_medications)

    if not items:
        return {
            "status": "error",
            "inventory_results": [],
            "message": "No medications provided to check inventory.",
            "has_out_of_stock": False,
            "has_low_stock": False,
            "all_available": False,
            "safety_disclaimer": "This is decision-support information generated from simulated hospital inventory records. The pharmacist makes the final dispensing decision."
        }

    results = []
    has_out = False
    has_low = False
    has_strength_unavail = False

    for item in items:
        check = query_inventory_check(
            medication_name=item["medication"],
            strength=item.get("strength"),
            dosage_form=item.get("dosage_form")
        )
        results.append(check)

        stat = check.get("availability_status")
        if stat == "OUT OF STOCK":
            has_out = True
        elif stat == "LOW STOCK":
            has_low = True
        elif stat == "STRENGTH UNAVAILABLE":
            has_strength_unavail = True

    all_avail = (not has_out) and (not has_low) and (not has_strength_unavail) and all(r.get("availability_status") == "AVAILABLE" for r in results)

    return {
        "status": "success",
        "inventory_results": results,
        "total_checked": len(results),
        "has_out_of_stock": has_out,
        "has_low_stock": has_low,
        "has_strength_unavailable": has_strength_unavail,
        "all_available": all_avail,
        "requires_pharmacist_attention": has_out or has_low or has_strength_unavail,
        "safety_disclaimer": "This is decision-support information generated from simulated hospital inventory records. The licensed pharmacist makes all physical verification, substitution, and dispensing decisions."
    }


@tool
def get_low_stock_items() -> Dict[str, Any]:
    """Retrieve all pharmacy medications currently below or at their configured reorder threshold.

    Call this tool for pharmacy inventory management, restocking workflows, and chief pharmacist monitoring.

    Returns:
        A dictionary containing:
        - status: 'success'
        - total_low_stock_items: Number of items needing replenishment
        - low_stock_items: List of items with inventory_id, medication, strength, quantity_on_hand,
          reorder_level, deficit_to_reorder, and stock_status
    """
    items = query_low_stock_inventory()
    return {
        "status": "success",
        "total_low_stock_items": len(items),
        "low_stock_items": items,
        "safety_disclaimer": "Simulated hospital inventory monitoring data for pharmacy supply chain coordination."
    }


@tool
def get_inventory_summary() -> Dict[str, Any]:
    """Retrieve high-level pharmacy inventory overview metrics for dashboard and operational monitoring.

    Call this tool to get aggregate statistics including total tracked medications, available count,
    low stock count, out of stock count, and overall stock health percentage.

    Returns:
        A dictionary containing:
        - total_tracked_medications: Total medication entries in the catalog
        - number_available: Number of medications with stock above reorder level
        - number_low_stock: Number of medications with stock between 1 and reorder level
        - number_out_of_stock: Number of medications with 0 stock
        - number_below_reorder_level: Sum of low stock and out of stock items
        - stock_health_percentage: Percentage of catalog in healthy stock
        - last_inventory_sync: Timestamp of the last inventory count
    """
    summary = query_inventory_overview_summary()
    return {
        "status": "success",
        "inventory_summary": summary,
        "safety_disclaimer": "Simulated hospital inventory metrics for pharmacy operations decision support."
    }
