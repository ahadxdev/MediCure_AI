from typing import Annotated
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from backend.database import get_db
from backend.models.entities import Medicine, InventoryRecord, SalesRecord
from backend.schemas.inventory import (
    InventoryItemResponse,
    InventoryListResponse,
    MedicineCreate,
)
from backend.services.seed_data import seed_database_if_empty
from ai_engine.risk.shortage_risk import assess_shortage_risk

router = APIRouter(prefix="/inventory", tags=["Inventory & Shortage Radar"])


@router.get("", response_model=InventoryListResponse)
def list_inventory(db: Annotated[Session, Depends(get_db)]):
    """
    Returns current stock levels, reorder levels, sales velocity,
    calculated coverage days, and shortage risk status for all catalog medicines.
    """
    # Auto-seed if database is completely empty on first run
    seed_database_if_empty(db)

    medicines = (
        db.query(Medicine)
        .options(joinedload(Medicine.inventory))
        .order_by(Medicine.name.asc())
        .all()
    )

    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    # Calculate average daily sales demand over past 30 days for each medicine
    sales_sums = (
        db.query(
            SalesRecord.medicine_id,
            func.sum(SalesRecord.quantity_dispensed).label("total_sold"),
            func.count(func.distinct(SalesRecord.sale_date)).label("days_recorded"),
        )
        .filter(SalesRecord.sale_date >= thirty_days_ago)
        .group_by(SalesRecord.medicine_id)
        .all()
    )
    sales_map = {
        row.medicine_id: (row.total_sold / max(1, row.days_recorded))
        for row in sales_sums
    }

    items: list[InventoryItemResponse] = []
    for med in medicines:
        inv = med.inventory
        usable_stock = inv.usable_stock if inv else 0.0
        reorder_level = inv.reorder_level if inv else 0.0
        last_counted = inv.last_counted_at if inv else None
        avg_demand = round(sales_map.get(med.id, 0.0), 2)

        # Deterministic coverage & status
        risk = assess_shortage_risk(
            usable_stock=usable_stock,
            avg_daily_demand=avg_demand,
        )

        items.append(
            InventoryItemResponse(
                medicine_id=med.id,
                name=med.name,
                generic_name=med.generic_name,
                strength=med.strength,
                dosage_form=med.dosage_form,
                pack_size=med.pack_size,
                usable_stock=usable_stock,
                reorder_level=reorder_level,
                avg_daily_demand=avg_demand,
                coverage_days=risk.get("coverage_days"),
                status=risk.get("status", "unknown"),
                last_counted_at=last_counted,
            )
        )

    return InventoryListResponse(total_items=len(items), items=items)


@router.post("/seed", status_code=status.HTTP_200_OK)
def trigger_seed(db: Annotated[Session, Depends(get_db)]):
    """Manually triggers Pakistan pharmaceutical sample catalog seeding."""
    was_seeded = seed_database_if_empty(db)
    return {
        "status": "success",
        "seeded": was_seeded,
        "message": "Demo catalog initialized" if was_seeded else "Database already contains medicine records",
    }


@router.post("", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
def create_medicine(
    payload: MedicineCreate,
    db: Annotated[Session, Depends(get_db)],
):
    """Adds a new medicine and its inventory record into the pharmacy catalog."""
    med = Medicine(
        name=payload.name,
        generic_name=payload.generic_name,
        strength=payload.strength,
        dosage_form=payload.dosage_form,
        pack_size=payload.pack_size,
    )
    db.add(med)
    db.flush()

    inv = InventoryRecord(
        medicine_id=med.id,
        usable_stock=payload.usable_stock,
        reorder_level=payload.reorder_level,
    )
    db.add(inv)
    db.commit()
    db.refresh(med)

    return InventoryItemResponse(
        medicine_id=med.id,
        name=med.name,
        generic_name=med.generic_name,
        strength=med.strength,
        dosage_form=med.dosage_form,
        pack_size=med.pack_size,
        usable_stock=inv.usable_stock,
        reorder_level=inv.reorder_level,
        avg_daily_demand=0.0,
        coverage_days=None,
        status="review_required",
        last_counted_at=inv.last_counted_at,
    )
