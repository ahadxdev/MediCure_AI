import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app
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
