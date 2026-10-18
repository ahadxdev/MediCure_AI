import json
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend.models.entities import (
    Medicine,
    InventoryRecord,
    SalesRecord,
    Supplier,
    QuotationRequest,
    QuotationRequestRecipient,
    Quotation,
    PurchaseOrder,
    AuditEvent,
)


def seed_database_if_empty(db: Session) -> bool:
    """
    Seeds initial Pakistan-specific pharmaceutical inventory, verified suppliers,
    quotations, quotation requests, and purchase orders if the database is not yet fully populated.
    Idempotent: will not create duplicates if records already exist.
    """
    if db.query(Medicine).count() > 0 and db.query(Quotation).count() > 0:
        return False

    # 1. Registered Suppliers in Pakistan
    if db.query(Supplier).count() == 0:
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
        db.flush()

    # 2. Key Demo Medicines with Usable Stock & Reorder Levels
    if db.query(Medicine).count() == 0:
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

            demand = item["daily_demand"]
            if demand > 0:
                for day_offset in range(1, 8):
                    sale = SalesRecord(
                        medicine_id=med.id,
                        sale_date=today - timedelta(days=day_offset),
                        quantity_dispensed=demand,
                    )
                    db.add(sale)
        db.flush()

    # 3. Seed Quotation Requests (RFQs)
    if db.query(QuotationRequest).count() == 0:
        rfq1 = QuotationRequest(
            id="req-101",
            medicine_id="med-panadol-500",
            required_quantity=40.0,
            required_by_date=date.today() + timedelta(days=3),
            delivery_location="Shifa Central Pharmacy, Islamabad",
            status="sent",
        )
        rfq2 = QuotationRequest(
            id="req-102",
            medicine_id="med-augmentin-625",
            required_quantity=25.0,
            required_by_date=date.today() + timedelta(days=5),
            delivery_location="Shifa Central Pharmacy, Islamabad",
            status="awaiting_approval",
        )
        db.add(rfq1)
        db.add(rfq2)
        db.flush()
        for request in (rfq1, rfq2):
            for supplier in db.query(Supplier).filter(Supplier.is_verified.is_(True)).all():
                db.add(QuotationRequestRecipient(request_id=request.id, supplier_id=supplier.id))

    # 4. Seed Validated Quotations
    if db.query(Quotation).count() == 0:
        quotes = [
            Quotation(
                id="quote-001",
                request_id="req-101",
                supplier_id="sup-001",
                price=480.0,
                currency="PKR",
                price_unit="pack of 200",
                quoted_quantity=100.0,
                minimum_order_quantity=20.0,
                delivery_days=2.0,
                delivery_fee=350.0,
                payment_terms="Cash On Delivery / 7-day terms",
                valid_until=str(date.today() + timedelta(days=14)),
                review_status="validated",
                warning_flags=json.dumps([]),
            ),
            Quotation(
                id="quote-002",
                request_id="req-101",
                supplier_id="sup-002",
                price=465.0,
                currency="PKR",
                price_unit="pack of 200",
                quoted_quantity=150.0,
                minimum_order_quantity=50.0,
                delivery_days=3.0,
                delivery_fee=500.0,
                payment_terms="Advance Bank Transfer",
                valid_until=str(date.today() + timedelta(days=10)),
                review_status="validated",
                warning_flags=json.dumps(["High MOQ (50 packs)"]),
            ),
            Quotation(
                id="quote-003",
                request_id="req-101",
                supplier_id="sup-003",
                price=450.0,
                currency="PKR",
                price_unit="pack of 200",
                quoted_quantity=50.0,
                minimum_order_quantity=10.0,
                delivery_days=5.0,
                delivery_fee=0.0,
                payment_terms="Net 15 days",
                valid_until=str(date.today() + timedelta(days=7)),
                review_status="validated",
                warning_flags=json.dumps(["Delivery exceeds lead time window (5 days)"]),
            ),
        ]
        for q in quotes:
            db.add(q)
        db.flush()

    # 5. Seed Purchase Orders
    if db.query(PurchaseOrder).count() == 0:
        po1 = PurchaseOrder(
            id="po-2026-001",
            quotation_id="quote-001",
            po_number="PO-2026-0891",
            total_amount=19550.0,
            status="awaiting_approval",
        )
        po2 = PurchaseOrder(
            id="po-2026-000",
            quotation_id="quote-002",
            po_number="PO-2026-0840",
            total_amount=10800.0,
            status="approved",
            approved_by="Dr. Tariq (Lead Pharmacist)",
            approved_at=datetime.now(timezone.utc) - timedelta(hours=24),
        )
        db.add(po1)
        db.add(po2)
        db.flush()

    # 6. Seed Audit Events
    if db.query(AuditEvent).count() == 0:
        audits = [
            AuditEvent(
                id="aud-001",
                entity_type="shortage_radar",
                entity_id="med-panadol-500",
                event_type="shortage_risk_computed",
                actor="ShortageRiskEngine",
                payload=json.dumps({"usable_stock": 15, "coverage_days": 3.0, "status": "critical"}),
            ),
            AuditEvent(
                id="aud-002",
                entity_type="quotation_request",
                entity_id="req-101",
                event_type="rfq_approved_and_sent",
                actor="Dr. Tariq (Lead Pharmacist)",
                payload=json.dumps({"recipients": ["orders@premiersales.pk"], "mode": "simulated"}),
            ),
            AuditEvent(
                id="aud-003",
                entity_type="purchase_order",
                entity_id="po-2026-001",
                event_type="po_draft_created",
                actor="ProcurementEngine",
                payload=json.dumps({"po_number": "PO-2026-0891", "amount": 19550.0}),
            ),
        ]
        for a in audits:
            db.add(a)

    db.commit()
    return True
