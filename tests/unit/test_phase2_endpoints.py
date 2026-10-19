import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app
from backend.auth import require_api_key_strict
from backend.services.seed_data import seed_database_if_empty
from backend.models.entities import (
    Medicine,
    InventoryRecord,
    SalesRecord,
    Supplier,
    QuotationRequest,
    Quotation,
    PurchaseOrder,
    AuditEvent,
)  # noqa: F401

# In-memory isolated database for unit testing with StaticPool
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh in-memory database and populates seed data for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    seed_database_if_empty(session)
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    """Provides a TestClient with the database dependency overridden."""
    from backend.config import settings

    monkeypatch.setattr(settings, "GMAIL_MODE", "SIMULATED")

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_api_key_strict] = lambda: "test-key"
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_list_quotation_requests(client):
    res = client.get("/api/quotes/requests")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 2
    assert any(r["id"] == "req-101" for r in data)


def test_empty_inventory_read_does_not_seed_demo_records(client, db_session):
    for model in (PurchaseOrder, Quotation, QuotationRequest, SalesRecord, InventoryRecord, Medicine, Supplier, AuditEvent):
        db_session.query(model).delete()
    db_session.commit()

    response = client.get("/api/inventory")

    assert response.status_code == 200
    assert response.json() == {"total_items": 0, "items": []}
    assert db_session.query(Medicine).count() == 0
    assert db_session.query(Supplier).count() == 0


def test_category_forecast_recommends_registered_medicine_from_live_stock(client):
    response = client.get("/api/risk/category-recommendations")
    assert response.status_code == 200

    result = response.json()
    assert result["model"] == "Random Forest"
    assert result["source"] == "salesweekly.csv"
    assert result["latest_observation"] == "2019-10-13"
    assert "not pharmacy-specific" in result["note"]

    paracetamol_category = next(
        category for category in result["categories"]
        if category["category"] == "N02BE"
    )
    panadol = next(medicine for medicine in paracetamol_category["medicines"] if medicine["medicine_id"] == "med-panadol-500")
    assert paracetamol_category["priority"] == "order"
    assert panadol["name"] == "Panadol 500mg Tablets"
    assert panadol["reasons"]


def test_demo_sales_are_labeled_included_in_recommendations_and_idempotent(client, db_session):
    first_response = client.post("/api/sales/demo-data")
    assert first_response.status_code == 200
    first_result = first_response.json()
    assert first_result["source"] == "synthetic_demo"
    assert first_result["generated_records"] > 0
    assert first_result["categories_updated"] > 0

    medicine = db_session.query(Medicine).filter_by(id="med-panadol-500").one()
    assert medicine.category == "N02BE"
    demo_records = (
        db_session.query(SalesRecord)
        .filter_by(medicine_id=medicine.id, is_synthetic=True)
        .count()
    )
    assert demo_records == 84

    recommendations = client.get("/api/risk/category-recommendations").json()
    paracetamol_category = next(item for item in recommendations["categories"] if item["category"] == "N02BE")
    panadol = next(item for item in paracetamol_category["medicines"] if item["medicine_id"] == medicine.id)
    assert panadol["sales_data_type"] == "mixed"
    assert panadol["avg_daily_demand"] > 0

    second_response = client.post("/api/sales/demo-data")
    assert second_response.status_code == 200
    assert second_response.json()["generated_records"] == 0
    assert db_session.query(SalesRecord).filter_by(medicine_id=medicine.id, is_synthetic=True).count() == 84


def test_approve_and_send_quotation_request(client):
    # Attempting to re-send already sent req-101 should return 400
    res_duplicate = client.post("/api/quotes/requests/req-101/approve-and-send", json={"approved": True})
    assert res_duplicate.status_code == 400

    # Approving awaiting_approval req-102
    res_approve = client.post("/api/quotes/requests/req-102/approve-and-send", json={"approved": True})
    assert res_approve.status_code == 200
    assert res_approve.json()["status"] == "simulated"
    assert res_approve.json()["mode"] == "SIMULATED"
    assert len(res_approve.json()["recipients"]) == 3


def test_rfq_email_draft_is_available_without_sending(client):
    response = client.get("/api/quotes/requests/req-102/draft")
    assert response.status_code == 200
    draft = response.json()
    assert draft["mode"] == "SIMULATED"
    assert len(draft["to"]) == 3
    assert "RFQ reference: req-102" in draft["body"]
    assert "RFQ req-102" in draft["subject"]


def test_live_rfq_approval_sends_to_approved_recipients(client, monkeypatch):
    from backend.config import settings
    import ai_engine.agent.graph as agent_graph

    sent_to = []
    monkeypatch.setattr(settings, "GMAIL_MODE", "LIVE")

    def fake_send_email(to, subject, body):
        sent_to.extend(to)
        return {"message_id": f"msg-{len(sent_to)}", "thread_id": f"thread-{len(sent_to)}", "status": "sent"}

    monkeypatch.setattr(agent_graph, "send_email", fake_send_email)
    response = client.post("/api/quotes/requests/req-102/approve-and-send", json={"approved": True})
    assert response.status_code == 200
    assert response.json()["status"] == "sent"
    assert response.json()["mode"] == "LIVE"
    assert len(sent_to) == 3


def test_live_rfq_send_failure_is_reported_and_request_stays_pending(client, db_session, monkeypatch):
    from backend.config import settings
    import ai_engine.agent.graph as agent_graph

    monkeypatch.setattr(settings, "GMAIL_MODE", "LIVE")

    def fail_send_email(to, subject, body):
        raise RuntimeError("Gmail authorization failed")

    monkeypatch.setattr(agent_graph, "send_email", fail_send_email)
    response = client.post("/api/quotes/requests/req-102/approve-and-send", json={"approved": True})
    assert response.status_code == 502
    assert "Gmail authorization failed" in response.json()["detail"]
    request = db_session.query(QuotationRequest).filter_by(id="req-102").first()
    assert request.status == "awaiting_approval"


def test_rejected_rfq_never_calls_gmail(client, monkeypatch):
    import ai_engine.agent.graph as agent_graph

    monkeypatch.setattr(
        agent_graph,
        "send_email",
        lambda *args, **kwargs: pytest.fail("Rejected RFQ must not call Gmail"),
    )
    response = client.post("/api/quotes/requests/req-102/approve-and-send", json={"approved": False})
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


def test_supplier_inbox_sync_parses_referenced_email(client, monkeypatch):
    import backend.api.quotes as quotes_api
    from backend.config import settings

    monkeypatch.setattr(settings, "GMAIL_MODE", "LIVE")
    monkeypatch.setattr(
        quotes_api,
        "fetch_supplier_replies",
        lambda query, max_results: [{
            "message_id": "gmail-message-001",
            "thread_id": "gmail-thread-001",
            "from": "Test Distributor <new.supplier@example.test>",
            "subject": "Re: RFQ req-101 - Panadol 500mg",
            "body": """
                Medicine: Panadol 500mg Tablets
                Strength: 500 mg
                Form: Tablet
                Pack: 100 tablets
                Price: PKR 120 / box
                Quantity: 50
                MOQ: 10
                Delivery: 2 days
                Payment terms: COD
                Valid until: 2027-01-01
            """,
        }],
    )
    response = client.post("/api/quotes/inbox/sync", json={"query": "in:inbox", "max_results": 5})
    assert response.status_code == 200
    assert response.json() == {"scanned": 1, "imported": 1, "duplicates": 0, "ignored": 0, "mode": "LIVE"}
    quote_response = client.get("/api/quotes/inbox")
    imported = next(item for item in quote_response.json() if item["source_email"] == "new.supplier@example.test")
    assert imported["price"] == 120
    assert imported["delivery_fee"] is None
    assert imported["medicine_name"] == "Panadol 500mg Tablets"
    assert imported["requested_medicine_name"] == "Panadol 500mg Tablets"
    assert imported["mismatch_fields"] == ["pack_size"]
    assert imported["review_status"] == "needs_review"
    assert "supplier_unverified" in imported["warning_flags"]


def test_supplier_inbox_sync_imports_pdf_only_quote(client, monkeypatch):
    import backend.api.quotes as quotes_api
    from backend.config import settings

    monkeypatch.setattr(settings, "GMAIL_MODE", "LIVE")
    monkeypatch.setattr(
        quotes_api,
        "fetch_supplier_replies",
        lambda query, max_results: [{
            "message_id": "gmail-pdf-message-001",
            "thread_id": "gmail-pdf-thread-001",
            "from": "PDF Supplier <pdf.supplier@example.test>",
            "subject": "Re: RFQ req-101 - Panadol 500mg",
            "body": "",
            "attachments": [{"filename": "quote.pdf", "data": b"pdf-bytes"}],
        }],
    )
    monkeypatch.setattr(
        quotes_api,
        "extract_pdf_text",
        lambda data: """
            Medicine: Panadol 500mg Tablets
            Strength: 500 mg
            Form: Tablet
            Pack: 100 tablets
            Price: PKR 125 / box
            Quantity: 50
            MOQ: 10
            Delivery: 3 days
            Payment terms: Cash on delivery
            Valid until: 2027-01-01
        """,
    )

    response = client.post(
        "/api/quotes/inbox/sync",
        json={"query": "in:inbox", "max_results": 5},
    )

    assert response.status_code == 200
    assert response.json()["imported"] == 1
    inbox_response = client.get("/api/quotes/inbox")
    imported = next(
        item
        for item in inbox_response.json()
        if item["source_email"] == "pdf.supplier@example.test"
    )
    assert imported["price"] == 125
    assert imported["payment_terms"] == "Cash on delivery"
    assert imported["valid_until"] == "2027-01-01"


def test_quote_inbox_explains_disprin_product_mismatch(client, db_session):
    db_session.add(Medicine(
        id="test-disprin-300",
        name="Disprin 300mg Tablets",
        generic_name="Aspirin",
        strength="300 mg",
        dosage_form="Tablet",
        pack_size="30 tablets",
    ))
    db_session.flush()
    db_session.add(QuotationRequest(
        id="test-disprin-request",
        medicine_id="test-disprin-300",
        required_quantity=10,
        status="sent",
    ))
    db_session.flush()
    db_session.add(Quotation(
        id="test-disprin-quote",
        request_id="test-disprin-request",
        supplier_id="sup-001",
        supplier_name="Premier Sales & Distribution (Pvt) Ltd",
        medicine_name="Disprin 300mg Soluble Tablets",
        raw_email_body="""
            Target Product: Disprin 300mg Soluble Tablets
            Strength: 300 mg
            Form: Soluble Tablet
            Pack: 100 tablets
            Price: PKR 2000 / pack
            Quantity: 100
            MOQ: 10
            Delivery: 6 days
            Delivery fee: PKR 6000
            Payment terms: cash
            Valid until: 2099-10-23
        """,
        price=2000,
        currency="PKR",
        price_unit="pack",
        quoted_quantity=100,
        minimum_order_quantity=10,
        delivery_days=6,
        delivery_fee=6000,
        review_status="needs_review",
        warning_flags='["request_mismatch"]',
    ))
    db_session.commit()

    response = client.get("/api/quotes/inbox")
    quote = next(item for item in response.json() if item["id"] == "test-disprin-quote")

    assert quote["medicine_name"] == "Disprin 300mg Soluble Tablets"
    assert quote["requested_medicine_name"] == "Disprin 300mg Tablets"
    assert quote["mismatch_fields"] == ["dosage_form", "medicine_name", "pack_size"]


def test_simulated_inbox_sync_never_reads_real_gmail(client, monkeypatch):
    import backend.api.quotes as quotes_api
    from backend.config import settings

    monkeypatch.setattr(settings, "GMAIL_MODE", "SIMULATED")
    monkeypatch.setattr(
        quotes_api,
        "fetch_supplier_replies",
        lambda *args, **kwargs: pytest.fail("Simulated mode must not access Gmail"),
    )
    response = client.post("/api/quotes/inbox/sync", json={"query": "in:inbox", "max_results": 5})
    assert response.status_code == 200
    result = response.json()
    assert result["mode"] == "SIMULATED"
    assert result["scanned"] > 0
    assert result["imported"] > 0


def test_quotation_inbox(client):
    res = client.get("/api/quotes/inbox")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    assert any(q["price"] == 480.0 for q in data)


def test_procurement_simulation_endpoint(client):
    payload = {
        "medicine_id": "med-panadol-500",
        "required_quantity": 40.0,
        "budget_limit": 30000.0,
        "max_delivery_days": 6.0,
    }
    res = client.post("/api/procurement/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["medicine_id"] == "med-panadol-500"
    assert len(data["options"]) >= 2
    assert data["quotes_evaluated_count"] == 3
    # Verify fastest option exists
    fastest = next(o for o in data["options"] if o["scenario_type"] == "fastest")
    assert fastest["delivery_days"] == 2.0
    assert all(option["scenario_type"] != "cheapest" or option["delivery_days"] <= 6 for option in data["options"])

    # No Panadol quotations may be used for a different medicine.
    other_medicine = client.post("/api/procurement/simulate", json={
        "medicine_id": "med-augmentin-625",
        "required_quantity": 10,
    })
    assert other_medicine.status_code == 200
    assert other_medicine.json()["quotes_evaluated_count"] == 0
    assert other_medicine.json()["options"] == []

    tight_deadline = client.post("/api/procurement/simulate", json={
        "medicine_id": "med-panadol-500",
        "required_quantity": 40,
        "budget_limit": 30000,
        "max_delivery_days": 1,
    })
    assert tight_deadline.status_code == 200
    fastest_with_tight_deadline = next(
        option for option in tight_deadline.json()["options"]
        if option["scenario_type"] == "fastest"
    )
    assert fastest_with_tight_deadline["feasibility_status"] == "warning"
    assert fastest_with_tight_deadline["title"] == "Fastest Delivery"


def test_procurement_simulation_excludes_non_pkr_and_unknown_delivery_fee_quotes(client, db_session):
    foreign_currency = db_session.query(Quotation).filter(Quotation.id == "quote-001").first()
    unknown_delivery_fee = db_session.query(Quotation).filter(Quotation.id == "quote-002").first()
    foreign_currency.currency = "USD"
    unknown_delivery_fee.delivery_fee = None
    db_session.commit()

    response = client.post("/api/procurement/simulate", json={
        "medicine_id": "med-panadol-500",
        "required_quantity": 40,
    })

    assert response.status_code == 200
    result = response.json()
    assert result["quotes_evaluated_count"] == 1
    assert all(option["supplier_name"].startswith("Lucky Pharma") for option in result["options"])


def test_procurement_simulation_allows_split_when_no_supplier_covers_full_quantity(client, db_session):
    first = db_session.query(Quotation).filter(Quotation.id == "quote-001").first()
    second = db_session.query(Quotation).filter(Quotation.id == "quote-002").first()
    third = db_session.query(Quotation).filter(Quotation.id == "quote-003").first()
    first.quoted_quantity = 30
    second.quoted_quantity = 20
    second.minimum_order_quantity = 10
    third.quoted_quantity = 10
    db_session.commit()

    response = client.post("/api/procurement/simulate", json={
        "medicine_id": "med-panadol-500",
        "required_quantity": 40,
        "budget_limit": 30000,
        "max_delivery_days": 6,
        "supplier_delay_days": 2,
    })

    assert response.status_code == 200
    result = response.json()
    assert result["quotes_evaluated_count"] == 3
    assert [option["scenario_type"] for option in result["options"]] == ["split_order"]
    split = result["options"][0]
    assert sum(allocation["quantity"] for allocation in split["allocations"]) == 40
    assert split["delivery_days"] == 5
    assert [allocation["delivery_days"] for allocation in split["allocations"]] == [4, 5]

    drafts = client.post("/api/orders/bulk", json={
        "orders": [
            {
                "medicine_id": "med-panadol-500",
                **allocation,
                "total_amount": allocation["quantity"] * allocation["unit_price"] + allocation["delivery_fee"],
                "delivery_estimate_days": allocation["delivery_days"],
            }
            for allocation in split["allocations"]
        ]
    })
    assert drafts.status_code == 201
    assert [order["delivery_estimate_days"] for order in drafts.json()] == [4, 5]
    assert all(order["status"] == "awaiting_approval" for order in drafts.json())


def test_procurement_simulation_excludes_expired_and_unknown_delivery_quotes(client, db_session):
    expired = db_session.query(Quotation).filter(Quotation.id == "quote-002").first()
    unknown_delivery = db_session.query(Quotation).filter(Quotation.id == "quote-003").first()
    expired.valid_until = "2000-01-01"
    unknown_delivery.delivery_days = None
    db_session.commit()

    response = client.post("/api/procurement/simulate", json={
        "medicine_id": "med-panadol-500",
        "required_quantity": 40,
    })

    assert response.status_code == 200
    result = response.json()
    assert result["quotes_evaluated_count"] == 1
    assert [option["scenario_type"] for option in result["options"]] == ["fastest"]
    assert result["options"][0]["delivery_days"] == 2


def test_procurement_simulation_includes_valid_quote_without_rfq_link(client, db_session):
    db_session.add(Quotation(
        id="quote-unlinked",
        request_id=None,
        supplier_id="sup-001",
        medicine_name="Panadol 500 mg Tablets",
        price=470,
        quoted_quantity=80,
        minimum_order_quantity=10,
        delivery_days=3,
        delivery_fee=0,
        valid_until="2099-12-31",
        review_status="validated",
    ))
    db_session.commit()

    response = client.post("/api/procurement/simulate", json={
        "medicine_id": "med-panadol-500",
        "required_quantity": 40,
    })

    assert response.status_code == 200
    result = response.json()
    assert result["quotes_evaluated_count"] == 4
    assert any(option["supplier_name"].startswith("Premier Sales") for option in result["options"])


def test_procurement_simulation_ranks_cost_after_moq(client, db_session):
    low_unit_price = db_session.query(Quotation).filter(Quotation.id == "quote-002").first()
    low_unit_price.price = 300
    low_unit_price.minimum_order_quantity = 100
    db_session.commit()

    response = client.post("/api/procurement/simulate", json={
        "medicine_id": "med-panadol-500",
        "required_quantity": 40,
        "budget_limit": 50000,
        "max_delivery_days": 10,
    })

    assert response.status_code == 200
    cheapest = next(option for option in response.json()["options"] if option["scenario_type"] == "cheapest")
    assert cheapest["supplier_name"] == "Lucky Pharma Distributors"
    assert cheapest["allocated_quantity"] == 40
    assert cheapest["total_cost"] == 18000


def test_purchase_orders_workflow(client):
    # 1. List existing POs
    res_list = client.get("/api/orders")
    assert res_list.status_code == 200
    orders = res_list.json()
    assert len(orders) >= 2

    # 2. Create new draft PO
    po_payload = {
        "medicine_id": "med-panadol-500",
        "supplier_name": "Premier Sales & Distribution",
        "quantity": 50.0,
        "unit_price": 480.0,
        "delivery_fee": 350.0,
        "total_amount": 24350.0,
        "delivery_estimate_days": 2.0,
    }
    res_create = client.post("/api/orders", json=po_payload)
    assert res_create.status_code == 201
    new_po = res_create.json()
    assert new_po["status"] == "awaiting_approval"

    # 3. Approve draft PO
    res_sign = client.post(
        f"/api/orders/{new_po['id']}/sign-off",
        json={"approved": True, "actor_name": "Dr. Tariq (Lead Pharmacist)"},
    )
    assert res_sign.status_code == 200
    assert res_sign.json()["status"] == "approved"
    assert res_sign.json()["approved_by"] == "Dr. Tariq (Lead Pharmacist)"

    # 4. Reject transition on already-approved PO should return 400
    res_bad = client.post(
        f"/api/orders/{new_po['id']}/sign-off",
        json={"approved": False, "actor_name": "Dr. Tariq"},
    )
    assert res_bad.status_code == 400


def test_audit_logs_retrieval(client):
    res = client.get("/api/audit/logs")
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) >= 3
    assert any(log["entity_type"] == "shortage_radar" for log in logs)
