from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ai_engine.risk.category_forecast import DATA_PATH, forecast_category_sales
from ai_engine.risk.shortage_risk import assess_shortage_risk
from backend.models.entities import Medicine, SalesRecord, Supplier
from backend.services.medicine_catalog import get_catalog_entry


@lru_cache(maxsize=4)
def _cached_category_forecast(dataset_path: str, modified_at_ns: int) -> dict:
    return forecast_category_sales(Path(dataset_path))


def get_category_recommendations(db: Session) -> dict:
    forecast = _cached_category_forecast(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns)
    medicine_rows = (
        db.query(Medicine)
        .options(joinedload(Medicine.inventory))
        .order_by(Medicine.name.asc())
        .all()
    )

    cutoff = date.today() - timedelta(days=30)
    sales_rows = (
        db.query(
            SalesRecord.medicine_id,
            func.sum(SalesRecord.quantity_dispensed).label("total_sold"),
        )
        .filter(SalesRecord.sale_date >= cutoff)
        .group_by(SalesRecord.medicine_id)
        .all()
    )
    daily_demand = {
        row.medicine_id: float(row.total_sold or 0) / 30
        for row in sales_rows
    }
    supplier_lead_time = (
        db.query(func.min(Supplier.default_lead_time_days))
        .filter(Supplier.is_verified.is_(True), Supplier.default_lead_time_days.isnot(None))
        .scalar()
    )

    recommendations = []
    for category in forecast["categories"]:
        medicines = []
        for medicine in medicine_rows:
            medicine_category = medicine.category
            if not medicine_category or medicine_category == "other":
                catalog_entry = get_catalog_entry(medicine.name)
                medicine_category = catalog_entry["category"] if catalog_entry else medicine_category
            if medicine_category != category["category"]:
                continue

            stock = medicine.inventory.usable_stock if medicine.inventory else 0.0
            reorder_level = medicine.inventory.reorder_level if medicine.inventory else 0.0
            demand = daily_demand.get(medicine.id)
            reasons = []
            if reorder_level > 0 and stock <= reorder_level:
                reasons.append("At or below the pharmacy reorder level")

            if demand is not None and demand > 0:
                risk = assess_shortage_risk(
                    usable_stock=stock,
                    avg_daily_demand=demand,
                    supplier_lead_time_days=supplier_lead_time,
                )
                coverage = risk["coverage_days"]
                if coverage is not None and coverage <= 7:
                    reasons.append("Seven days of stock coverage or less")
            else:
                demand = None
                coverage = None

            if reasons:
                medicines.append({
                    "medicine_id": medicine.id,
                    "name": medicine.name,
                    "strength": medicine.strength,
                    "dosage_form": medicine.dosage_form,
                    "pack_size": medicine.pack_size,
                    "usable_stock": stock,
                    "reorder_level": reorder_level,
                    "avg_daily_demand": round(demand, 2) if demand is not None else None,
                    "coverage_days": round(coverage, 2) if coverage is not None else None,
                    "reasons": reasons,
                })

        recommendations.append({
            **category,
            "priority": "order" if medicines else "monitor",
            "medicines": medicines,
        })

    recommendations.sort(
        key=lambda item: (
            item["priority"] != "order",
            item["change_percent"] is None,
            -(item["change_percent"] or 0),
            item["category"],
        )
    )
    return {
        **forecast,
        "note": (
            "The model forecasts category-level demand from the bundled historical dataset. "
            "Medicine recommendations use your registered stock, reorder levels, and sales "
            "recorded in the last 30 days; dataset forecasts are not pharmacy-specific."
        ),
        "categories": recommendations,
    }
