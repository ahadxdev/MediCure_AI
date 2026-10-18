import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app
from backend.auth import require_api_key_strict
from backend.services.seed_data import seed_database_if_empty

from sqlalchemy.pool import StaticPool

# In-memory isolated database for unit testing
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
    app.dependency_overrides[require_api_key_strict] = lambda: "test-key"
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "MediProcure AI API"
    assert "/docs" in data["docs"]


def test_health_endpoints(client):
    # Lightweight ping
    res_ping = client.get("/api/health")
    assert res_ping.status_code == 200
    assert res_ping.json()["status"] == "ok"

    # Comprehensive health check
    res_health = client.get("/api/system/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["status"] == "ok"
    assert health_data["database"] == "connected"
    assert health_data["gmail_mode"] in ["SIMULATED", "LIVE"]


def test_inventory_list(client):
    response = client.get("/api/inventory")
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] >= 4

    item_names = [item["name"] for item in data["items"]]
    assert any("Panadol" in name for name in item_names)
    assert any("Augmentin" in name for name in item_names)
    assert any("Brufen" in name for name in item_names)

    # Verify Panadol 500mg has high risk status (stock: 15, demand: 5, coverage: 3 days)
    panadol = next(item for item in data["items"] if "Panadol" in item["name"])
    assert panadol["usable_stock"] == 15.0
    assert panadol["avg_daily_demand"] == 5.0
    assert panadol["coverage_days"] == 3.0
    assert panadol["status"] == "high_risk"


def test_create_medicine(client):
    payload = {
        "name": "Calamox 156mg Syrup",
        "generic_name": "Amoxicillin + Clavulanic Acid",
        "strength": "156 mg / 5 ml",
        "dosage_form": "Suspension",
        "pack_size": "60 ml bottle",
        "usable_stock": 25.0,
        "reorder_level": 10.0,
    }
    response = client.post("/api/inventory", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Calamox 156mg Syrup"
    assert data["usable_stock"] == 25.0
    assert data["status"] == "review_required"


def test_medicine_crud(client):
    created = client.post("/api/inventory", json={
        "name": "CRUD Medicine",
        "generic_name": "Test compound",
        "strength": "20 mg",
        "dosage_form": "Capsule",
        "pack_size": "10 capsules",
        "usable_stock": 8,
        "reorder_level": 3,
    })
    assert created.status_code == 201
    medicine_id = created.json()["medicine_id"]

    detail = client.get(f"/api/inventory/{medicine_id}")
    assert detail.status_code == 200
    assert detail.json()["name"] == "CRUD Medicine"

    updated = client.put(f"/api/inventory/{medicine_id}", json={
        "name": "Updated CRUD Medicine",
        "generic_name": None,
        "strength": "25 mg",
        "dosage_form": "Capsule",
        "pack_size": "20 capsules",
        "usable_stock": 12,
        "reorder_level": 4,
    })
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated CRUD Medicine"
    assert updated.json()["usable_stock"] == 12

    deleted = client.delete(f"/api/inventory/{medicine_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/inventory/{medicine_id}").status_code == 404


def test_medicine_delete_preserves_procurement_history(client):
    response = client.delete("/api/inventory/med-panadol-500")
    assert response.status_code == 409


def test_supplier_crud(client):
    created = client.post("/api/suppliers", json={
        "name": "CRUD Supplier",
        "email": "crud.supplier@example.test",
        "phone": "+92-300-0000000",
        "address": "Islamabad",
        "is_verified": False,
        "default_lead_time_days": 4,
    })
    assert created.status_code == 201
    supplier_id = created.json()["id"]

    assert client.get(f"/api/suppliers/{supplier_id}").json()["name"] == "CRUD Supplier"
    assert any(item["id"] == supplier_id for item in client.get("/api/suppliers").json())

    updated = client.put(f"/api/suppliers/{supplier_id}", json={
        "name": "Updated CRUD Supplier",
        "email": "CRUD.Supplier@example.test",
        "phone": None,
        "address": None,
        "is_verified": True,
        "default_lead_time_days": 2,
    })
    assert updated.status_code == 200
    assert updated.json()["email"] == "crud.supplier@example.test"
    assert updated.json()["name"] == "Updated CRUD Supplier"

    assert client.delete(f"/api/suppliers/{supplier_id}").status_code == 204
    assert client.get(f"/api/suppliers/{supplier_id}").status_code == 404


def test_supplier_email_is_unique_and_validated(client):
    response = client.post("/api/suppliers", json={
        "name": "Invalid Supplier",
        "email": "not-an-email",
    })
    assert response.status_code == 422

    duplicate = client.post("/api/suppliers", json={
        "name": "Duplicate Supplier",
        "email": "ORDERS@PREMIERSALES.PK",
    })
    assert duplicate.status_code == 409


def test_supplier_delete_preserves_quotation_history(client):
    response = client.delete("/api/suppliers/sup-001")
    assert response.status_code == 409


def test_evaluate_shortage_risk_basic(client):
    payload = {
        "usable_stock": 15,
        "avg_daily_demand": 5,
        "supplier_lead_time_days": 6,
        "incoming_shipments": [],
    }
    response = client.post("/api/risk/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["coverage_days"] == 3.0
    assert data["stockout_before_delivery"] is True
    assert data["status"] == "high_risk"
    assert data["first_stockout_day"] == 3.0


def test_evaluate_shortage_risk_with_incoming_stock(client):
    payload = {
        "usable_stock": 10,
        "avg_daily_demand": 5,
        "supplier_lead_time_days": 6,
        "incoming_shipments": [
            {"quantity": 20, "days_until_arrival": 1}
        ],
    }
    response = client.post("/api/risk/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["stockout_before_delivery"] is False
    assert data["status"] == "warning"


def test_evaluate_shortage_risk_zero_demand(client):
    payload = {
        "usable_stock": 20,
        "avg_daily_demand": 0,
        "supplier_lead_time_days": 4,
        "incoming_shipments": [],
    }
    response = client.post("/api/risk/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "review_required"
    assert any("Demand is zero" in flag for flag in data["risk_flags"])


def test_evaluate_medicine_risk_endpoint(client):
    # Test live database evaluation for panadol
    response = client.get("/api/risk/medicines/med-panadol-500?supplier_lead_time_days=6")
    assert response.status_code == 200
    data = response.json()
    assert data["coverage_days"] == 3.0
    assert data["status"] == "high_risk"
    assert data["stockout_before_delivery"] is True

    # Test non-existent medicine
    res_not_found = client.get("/api/risk/medicines/non-existent-id")
    assert res_not_found.status_code == 404
