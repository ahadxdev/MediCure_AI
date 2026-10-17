from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.models.entities import Medicine, InventoryRecord, SalesRecord, Supplier


def seed_database_if_empty(db: Session) -> bool:
    """
    Seeds initial Pakistan-specific pharmaceutical inventory and verified suppliers
    if the database has no medicines yet. Returns True if seeded, False if already populated.
    """
    if db.query(Medicine).count() > 0:
        return False

    # 1. Registered Suppliers in Pakistan
    suppliers = [
        Supplier(
            id="sup-001",
            name="Premier Sales & Distribution (Pvt) Ltd",
            email="orders@premiersales.pk",
            phone="+92-21-111-773-643",
            address="Plot 14, Sector 15, Korangi Industrial Area, Karachi",
            is_verified=True,
            default_lead_time_days=2.0,
        ),
        Supplier(
            id="sup-002",
            name="Muller & Phipps Pakistan",
            email="pharma@mulphico.pk",
            phone="+92-42-111-677-725",
            address="Gulberg III, Lahore, Punjab",
            is_verified=True,
            default_lead_time_days=3.0,
        ),
        Supplier(
            id="sup-003",
            name="Lucky Pharma Distributors",
            email="supply@luckypharma.com.pk",
            phone="+92-51-282-9901",
            address="I-9 Industrial Area, Islamabad",
            is_verified=True,
            default_lead_time_days=5.0,
        ),
    ]
    for s in suppliers:
        db.add(s)

    # 2. Key Demo Medicines with Usable Stock & Reorder Levels
    medicine_defs = [
        {
            "id": "med-panadol-500",
            "name": "Panadol 500mg Tablets",
            "generic_name": "Paracetamol",
            "strength": "500 mg",
            "dosage_form": "Tablet",
            "pack_size": "200 tablets (20x10 blister)",
            "usable_stock": 15.0,
            "reorder_level": 50.0,
            "daily_demand": 5.0,
        },
        {
            "id": "med-augmentin-625",
            "name": "Augmentin 625mg Tablets",
            "generic_name": "Amoxicillin + Clavulanic Acid",
            "strength": "625 mg",
            "dosage_form": "Tablet",
            "pack_size": "14 tablets",
            "usable_stock": 30.0,
            "reorder_level": 40.0,
            "daily_demand": 5.0,
        },
        {
            "id": "med-brufen-400",
            "name": "Brufen 400mg Tablets",
            "generic_name": "Ibuprofen",
            "strength": "400 mg",
            "dosage_form": "Tablet",
            "pack_size": "30 tablets",
            "usable_stock": 120.0,
            "reorder_level": 30.0,
            "daily_demand": 8.0,
        },
        {
            "id": "med-disprin-300",
            "name": "Disprin 300mg Soluble Tablets",
            "generic_name": "Aspirin",
            "strength": "300 mg",
            "dosage_form": "Soluble Tablet",
            "pack_size": "100 tablets",
            "usable_stock": 50.0,
            "reorder_level": 20.0,
            "daily_demand": 0.0,
        },
    ]

    today = date.today()

    for item in medicine_defs:
        med = Medicine(
            id=item["id"],
            name=item["name"],
            generic_name=item["generic_name"],
            strength=item["strength"],
            dosage_form=item["dosage_form"],
            pack_size=item["pack_size"],
        )
        db.add(med)

        inv = InventoryRecord(
            medicine_id=med.id,
            usable_stock=item["usable_stock"],
            reorder_level=item["reorder_level"],
        )
        db.add(inv)

        # Populate 7 days of recent sales history for demand calculation
        demand = item["daily_demand"]
        if demand > 0:
            for day_offset in range(1, 8):
                sale = SalesRecord(
                    medicine_id=med.id,
                    sale_date=today - timedelta(days=day_offset),
                    quantity_dispensed=demand,
                )
                db.add(sale)

    db.commit()
    return True
