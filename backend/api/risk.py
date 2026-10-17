from typing import Annotated
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models.entities import Medicine, InventoryRecord, SalesRecord, Supplier
from backend.schemas.risk import RiskAssessmentRequest, RiskAssessmentResponse, IncomingShipment
from backend.services.risk_service import evaluate_risk

router = APIRouter(prefix="/risk", tags=["Shortage Risk Engine"])


@router.post("/evaluate", response_model=RiskAssessmentResponse)
def evaluate_shortage_risk(payload: RiskAssessmentRequest) -> RiskAssessmentResponse:
    """
    Deterministically computes stock coverage days, projected stockout timeline,
    and delivery feasibility for supplied inventory and scheduled incoming shipments.
    """
    return evaluate_risk(payload)


@router.get("/medicines/{medicine_id}", response_model=RiskAssessmentResponse)
def evaluate_medicine_risk(
    medicine_id: str,
    db: Annotated[Session, Depends(get_db)],
    supplier_lead_time_days: Annotated[float | None, Query(ge=0)] = None,
) -> RiskAssessmentResponse:
    """
    Evaluates live shortage risk for a specific registered medicine directly
    from its current inventory and 30-day recorded sales history.
    """
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID '{medicine_id}' not found",
        )

    inv = db.query(InventoryRecord).filter(InventoryRecord.medicine_id == medicine_id).first()
    usable_stock = inv.usable_stock if inv else 0.0

    thirty_days_ago = date.today() - timedelta(days=30)
    sales_stats = (
        db.query(
            func.sum(SalesRecord.quantity_dispensed).label("total_sold"),
            func.count(func.distinct(SalesRecord.sale_date)).label("days_recorded"),
        )
        .filter(SalesRecord.medicine_id == medicine_id, SalesRecord.sale_date >= thirty_days_ago)
        .first()
    )

    total_sold = sales_stats.total_sold if sales_stats and sales_stats.total_sold else 0.0
    days_recorded = sales_stats.days_recorded if sales_stats and sales_stats.days_recorded else 1
    avg_demand = round(total_sold / max(1, days_recorded), 2)

    # If supplier lead time not passed in query, attempt to find default from verified supplier
    lead_time = supplier_lead_time_days
    if lead_time is None:
        first_supplier = db.query(Supplier).filter(Supplier.default_lead_time_days.isnot(None)).first()
        if first_supplier:
            lead_time = first_supplier.default_lead_time_days

    request_payload = RiskAssessmentRequest(
        usable_stock=usable_stock,
        avg_daily_demand=avg_demand,
        supplier_lead_time_days=lead_time,
        incoming_shipments=[],
    )
    return evaluate_risk(request_payload)
