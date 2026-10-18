from typing import Annotated
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from backend.database import get_db
from backend.auth import require_api_key
from backend.models.entities import Medicine, InventoryRecord, SalesRecord, QuotationRequest, AppSetting
from backend.schemas.inventory import (
    InventoryItemResponse,
    InventoryListResponse,
    MedicineCreate,
)
from ai_engine.risk.shortage_risk import assess_shortage_risk
from backend.services.medicine_catalog import get_catalog_entry, get_medicine_catalog

router = APIRouter(prefix="/inventory", tags=["Inventory & Shortage Radar"])


def _critical_threshold(db: Session) -> float:
    setting = db.get(AppSetting, "reorder_threshold_days")
    try:
        return float(setting.value) if setting else 3.0
    except (TypeError, ValueError):
        return 3.0


@router.get("", response_model=InventoryListResponse)
def list_inventory(db: Annotated[Session, Depends(get_db)]):
    """
    Returns current stock levels, reorder levels, sales velocity,
    calculated coverage days, and shortage risk status for all catalog medicines.
    """
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
    critical_threshold = _critical_threshold(db)
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

        if risk.get("coverage_days") is not None and risk["coverage_days"] <= critical_threshold and risk.get("status") not in {"unknown", "review_required"}:
            risk["status"] = "high_risk"
        items.append(
            InventoryItemResponse(
                medicine_id=med.id,
                name=med.name,
                generic_name=med.generic_name,
                category=med.category,
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


@router.get("/catalog")
def get_medicine_catalog_endpoint():
    """Returns the curated Pakistani medicine catalog used for dropdown-driven entry."""
    return get_medicine_catalog()


@router.post("", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
def create_medicine(
    payload: MedicineCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(require_api_key)],
):
    """Adds a new medicine and its inventory record into the pharmacy catalog."""
    matched = get_catalog_entry(payload.name)
    med = Medicine(
        name=payload.name,
        generic_name=payload.generic_name or (matched["generic_name"] if matched else None),
        category=(payload.category or (matched["category"] if matched else "other")).strip() or "other",
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
        category=med.category,
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


def _inventory_item(medicine: Medicine, avg_demand: float, critical_threshold: float = 3.0) -> InventoryItemResponse:
    inventory = medicine.inventory
    usable_stock = inventory.usable_stock if inventory else 0.0
    risk = assess_shortage_risk(
        usable_stock=usable_stock,
        avg_daily_demand=avg_demand,
    )
    if risk.get("coverage_days") is not None and risk["coverage_days"] <= critical_threshold and risk.get("status") not in {"unknown", "review_required"}:
        risk["status"] = "high_risk"
    return InventoryItemResponse(
        medicine_id=medicine.id,
        name=medicine.name,
        generic_name=medicine.generic_name,
        category=medicine.category,
        strength=medicine.strength,
        dosage_form=medicine.dosage_form,
        pack_size=medicine.pack_size,
        usable_stock=usable_stock,
        reorder_level=inventory.reorder_level if inventory else 0.0,
        avg_daily_demand=avg_demand,
        coverage_days=risk.get("coverage_days"),
        status=risk.get("status", "unknown"),
        last_counted_at=inventory.last_counted_at if inventory else None,
    )


@router.get("/{medicine_id}", response_model=InventoryItemResponse)
def get_medicine(medicine_id: str, db: Annotated[Session, Depends(get_db)]):
    medicine = (
        db.query(Medicine)
        .options(joinedload(Medicine.inventory))
        .filter(Medicine.id == medicine_id)
        .first()
    )
    if medicine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")

    cutoff = date.today() - timedelta(days=30)
    sales = (
        db.query(
            func.sum(SalesRecord.quantity_dispensed),
            func.count(func.distinct(SalesRecord.sale_date)),
        )
        .filter(SalesRecord.medicine_id == medicine_id, SalesRecord.sale_date >= cutoff)
        .first()
    )
    avg_demand = round((sales[0] or 0.0) / max(1, sales[1] or 0), 2)
    return _inventory_item(medicine, avg_demand, _critical_threshold(db))


@router.put("/{medicine_id}", response_model=InventoryItemResponse)
def update_medicine(
    medicine_id: str,
    payload: MedicineCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(require_api_key)],
):
    medicine = (
        db.query(Medicine)
        .options(joinedload(Medicine.inventory))
        .filter(Medicine.id == medicine_id)
        .first()
    )
    if medicine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")

    values = payload.model_dump()
    matched = get_catalog_entry(payload.name)
    for field in ("name", "generic_name", "strength", "dosage_form", "pack_size"):
        setattr(medicine, field, values[field])
    medicine.category = (payload.category or (matched["category"] if matched else medicine.category) or "other").strip() or "other"
    if payload.generic_name is not None:
        medicine.generic_name = payload.generic_name
    elif matched and not medicine.generic_name:
        medicine.generic_name = matched["generic_name"]

    if medicine.inventory is None:
        medicine.inventory = InventoryRecord(
            usable_stock=payload.usable_stock,
            reorder_level=payload.reorder_level,
        )
    else:
        medicine.inventory.usable_stock = payload.usable_stock
        medicine.inventory.reorder_level = payload.reorder_level
        medicine.inventory.last_counted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(medicine)
    return get_medicine(medicine_id, db)


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medicine(
    medicine_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(require_api_key)],
):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if medicine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
    if medicine.sales_records or medicine.quotation_requests:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Medicine cannot be deleted because sales or quotation history references it",
        )

    db.delete(medicine)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
