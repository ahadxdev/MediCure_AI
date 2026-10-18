from datetime import date, timedelta

from sqlalchemy.orm import Session

from backend.models.entities import Medicine, SalesRecord
from backend.services.medicine_catalog import (
    CATEGORY_ORDER,
    get_catalog_entry,
    get_catalog_entry_by_generic,
    generate_demo_sales_history_for_category,
)


def add_demo_sales_data(db: Session) -> dict:
    medicines = db.query(Medicine).order_by(Medicine.name.asc()).all()
    generated_records = 0
    skipped_existing = 0
    skipped_uncategorized = 0
    categories_updated = 0
    skipped_without_history = 0

    for medicine in medicines:
        existing_demo_records = (
            db.query(SalesRecord.id)
            .filter(
                SalesRecord.medicine_id == medicine.id,
                SalesRecord.is_synthetic.is_(True),
            )
            .first()
        )
        if existing_demo_records:
            skipped_existing += 1
            continue

        catalog_entry = get_catalog_entry(medicine.name) or get_catalog_entry_by_generic(medicine.generic_name)
        category = medicine.category
        if (not category or category == "other") and catalog_entry:
            category = catalog_entry["category"]
            if category != "other":
                medicine.category = category
                categories_updated += 1

        if category not in CATEGORY_ORDER:
            skipped_uncategorized += 1
            continue

        history = generate_demo_sales_history_for_category(category, weeks=12)
        if not history:
            skipped_without_history += 1
            continue

        for week in history:
            first_day = date.fromisoformat(week["sale_date"])
            daily_quantity = week["quantity_dispensed"] / 7
            for day_offset in range(7):
                db.add(SalesRecord(
                    medicine_id=medicine.id,
                    sale_date=first_day + timedelta(days=day_offset),
                    quantity_dispensed=round(daily_quantity, 4),
                    is_synthetic=True,
                ))
                generated_records += 1

    db.commit()
    return {
        "generated_records": generated_records,
        "skipped_existing_medicines": skipped_existing,
        "skipped_uncategorized_medicines": skipped_uncategorized,
        "skipped_without_history_medicines": skipped_without_history,
        "categories_updated": categories_updated,
        "source": "synthetic_demo",
    }
