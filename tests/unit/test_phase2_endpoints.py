import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app
from backend.services.seed_data import seed_database_if_empty
from backend.models.entities import Medicine, QuotationRequest, Quotation, PurchaseOrder, AuditEvent  # noqa: F401

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
def client(db_session):
    """Provides a TestClient with the database dependency overridden."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_list_quotation_requests(client):
    res = client.get("/api/quotes/requests")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 2
    assert any(r["id"] == "req-101" for r in data)


def test_approve_and_send_quotation_request(client):
    # Attempting to re-send already sent req-101 should return 400
    res_duplicate = client.post("/api/quotes/requests/req-101/approve-and-send", json={"approved": True})
    assert res_duplicate.status_code == 400

    # Approving awaiting_approval req-102
    res_approve = client.post("/api/quotes/requests/req-102/approve-and-send", json={"approved": True})
    assert res_approve.status_code == 200
    assert res_approve.json()["status"] == "sent"


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
    # Verify fastest option exists
    fastest = next(o for o in data["options"] if o["scenario_type"] == "fastest")
    assert fastest["delivery_days"] == 2.0


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
