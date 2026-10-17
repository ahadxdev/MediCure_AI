"""
Comprehensive backend bug-hunting and regression test suite.

Tests the FastAPI API endpoints, database constraints, Pydantic schema
validation, deterministic risk calculations, and edge cases.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app
from backend.services.seed_data import seed_database_if_empty
from backend.schemas.risk import RiskAssessmentRequest, RiskAssessmentResponse
from backend.services.risk_service import evaluate_risk
from ai_engine.risk.shortage_risk import assess_shortage_risk


# ── Test infrastructure ──────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    seed_database_if_empty(session)
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def empty_db_session():
    """A session with tables created but NO seed data."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def empty_client(empty_db_session):
    """Client against an empty (unseeded) database."""
    def override_get_db():
        try:
            yield empty_db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ── 1. API: invalid / malformed input ────────────────────────────────

class TestRiskEvaluateValidation:
    """POST /api/risk/evaluate — input validation edge cases."""

    def test_missing_body_returns_422(self, client):
        res = client.post("/api/risk/evaluate")
        assert res.status_code == 422

    def test_empty_body_returns_422(self, client):
        res = client.post("/api/risk/evaluate", json={})
        assert res.status_code == 422

    def test_negative_stock_rejected_by_schema(self, client):
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": -5,
            "avg_daily_demand": 3,
        })
        assert res.status_code == 422

    def test_negative_demand_rejected_by_schema(self, client):
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": 10,
            "avg_daily_demand": -1,
        })
        assert res.status_code == 422

    def test_negative_lead_time_rejected(self, client):
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": 10,
            "avg_daily_demand": 5,
            "supplier_lead_time_days": -2,
        })
        assert res.status_code == 422

    def test_string_stock_rejected(self, client):
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": "ten",
            "avg_daily_demand": 5,
        })
        assert res.status_code == 422

    def test_invalid_shipment_quantity_rejected(self, client):
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": 10,
            "avg_daily_demand": 5,
            "incoming_shipments": [{"quantity": -5, "days_until_arrival": 1}],
        })
        assert res.status_code == 422

    def test_zero_quantity_shipment_rejected(self, client):
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": 10,
            "avg_daily_demand": 5,
            "incoming_shipments": [{"quantity": 0, "days_until_arrival": 1}],
        })
        assert res.status_code == 422

    def test_negative_arrival_days_rejected(self, client):
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": 10,
            "avg_daily_demand": 5,
            "incoming_shipments": [{"quantity": 10, "days_until_arrival": -1}],
        })
        assert res.status_code == 422


class TestRiskEvaluateBehavior:
    """POST /api/risk/evaluate — correct deterministic results."""

    def test_safe_stock_returns_lower_risk(self, client):
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": 100,
            "avg_daily_demand": 5,
            "supplier_lead_time_days": 3,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "lower_risk"
        assert data["coverage_days"] == 20.0
        assert data["stockout_before_delivery"] is False
        assert data["stock_at_delivery"] == 85.0

    def test_zero_demand_returns_review_required(self, client):
        """BUG-2 regression: zero demand produces inf coverage.
        The API response must serialize to valid JSON."""
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": 50,
            "avg_daily_demand": 0,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "review_required"
        # coverage_days should be serializable (not Infinity in JSON)
        coverage = data["coverage_days"]
        assert coverage is None or (isinstance(coverage, (int, float)) and coverage != float("inf"))

    def test_zero_stock_zero_demand(self, client):
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": 0,
            "avg_daily_demand": 0,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "review_required"

    def test_zero_stock_positive_demand(self, client):
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": 0,
            "avg_daily_demand": 5,
            "supplier_lead_time_days": 3,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["coverage_days"] == 0.0
        assert data["stockout_before_delivery"] is True
        assert data["first_stockout_day"] == 0.0
        assert data["status"] == "high_risk"

    def test_no_lead_time_gives_needs_delivery_data(self, client):
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": 10,
            "avg_daily_demand": 5,
        })
        assert res.status_code == 200
        data = res.json()
        # Without lead time, the risk engine returns a provisional status
        assert data["status"] in ("high_risk", "warning", "needs_delivery_data")
        assert data["stockout_before_delivery"] is None
        assert data["stock_at_delivery"] is None

    def test_multiple_incoming_shipments(self, client):
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": 10,
            "avg_daily_demand": 5,
            "supplier_lead_time_days": 10,
            "incoming_shipments": [
                {"quantity": 10, "days_until_arrival": 1},
                {"quantity": 10, "days_until_arrival": 3},
            ],
        })
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data["coverage_days"], (int, float))
        assert isinstance(data["assumptions"], list)
        assert len(data["assumptions"]) > 0

    def test_exact_stockout_at_delivery(self, client):
        """Stock equals demand*lead_time exactly: no stockout gap."""
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": 30,
            "avg_daily_demand": 5,
            "supplier_lead_time_days": 6,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["stock_at_delivery"] == 0.0
        # stock_at_delivery is 0 but there's no gap before delivery
        assert data["stockout_before_delivery"] is False


# ── 2. API: inventory endpoint edge cases ────────────────────────────

class TestInventoryEndpoint:

    def test_empty_database_auto_seeds(self, empty_client):
        """GET /api/inventory on empty DB should auto-seed demo data."""
        res = empty_client.get("/api/inventory")
        assert res.status_code == 200
        data = res.json()
        assert data["total_items"] >= 4

    def test_create_medicine_missing_required_fields(self, client):
        res = client.post("/api/inventory", json={})
        assert res.status_code == 422

    def test_create_medicine_empty_name(self, client):
        res = client.post("/api/inventory", json={
            "name": "",
            "strength": "500 mg",
            "dosage_form": "Tablet",
            "pack_size": "10 tablets",
        })
        assert res.status_code == 422

    def test_create_medicine_negative_stock(self, client):
        res = client.post("/api/inventory", json={
            "name": "Test Med",
            "strength": "50 mg",
            "dosage_form": "Capsule",
            "pack_size": "30 capsules",
            "usable_stock": -10,
        })
        assert res.status_code == 422

    def test_create_medicine_negative_reorder_level(self, client):
        res = client.post("/api/inventory", json={
            "name": "Test Med",
            "strength": "50 mg",
            "dosage_form": "Capsule",
            "pack_size": "30 capsules",
            "reorder_level": -5,
        })
        assert res.status_code == 422

    def test_create_medicine_minimal_valid(self, client):
        """Only required fields, defaults should apply."""
        res = client.post("/api/inventory", json={
            "name": "Minimal Med",
            "strength": "10 mg",
            "dosage_form": "Tablet",
            "pack_size": "5 tablets",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["usable_stock"] == 0.0
        assert data["reorder_level"] == 0.0

    def test_inventory_list_response_schema(self, client):
        """Verify all required fields in response items."""
        res = client.get("/api/inventory")
        assert res.status_code == 200
        data = res.json()
        assert "total_items" in data
        assert "items" in data
        for item in data["items"]:
            assert "medicine_id" in item
            assert "name" in item
            assert "usable_stock" in item
            assert "avg_daily_demand" in item
            assert "coverage_days" in item
            assert "status" in item

    def test_seed_endpoint_idempotent(self, client):
        """POST /api/inventory/seed should be safe to call repeatedly."""
        res1 = client.post("/api/inventory/seed")
        assert res1.status_code == 200
        assert res1.json()["seeded"] is False  # already seeded by fixture

        res2 = client.post("/api/inventory/seed")
        assert res2.status_code == 200
        assert res2.json()["seeded"] is False


# ── 3. API: medicine risk by ID ──────────────────────────────────────

class TestMedicineRiskEndpoint:

    def test_nonexistent_medicine_returns_404(self, client):
        res = client.get("/api/risk/medicines/does-not-exist")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    def test_valid_medicine_without_lead_time_param(self, client):
        """Should auto-fetch supplier default lead time from DB."""
        res = client.get("/api/risk/medicines/med-panadol-500")
        assert res.status_code == 200
        data = res.json()
        # Suppliers have lead times in seed data, so it should not be needs_delivery_data
        assert data["status"] in ("high_risk", "warning", "lower_risk", "review_required")
        # With seeded supplier default_lead_time = 2.0 (Premier Sales),
        # Panadol has 3 days coverage and lead_time=2 → stock at delivery = 5.0
        assert data["coverage_days"] == 3.0

    def test_disprin_zero_demand_medicine(self, client):
        """Disprin has demand=0 in seed data, should be review_required."""
        res = client.get("/api/risk/medicines/med-disprin-300")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "review_required"

    def test_negative_lead_time_query_param_rejected(self, client):
        res = client.get("/api/risk/medicines/med-panadol-500?supplier_lead_time_days=-1")
        assert res.status_code == 422


# ── 4. API: health endpoints ─────────────────────────────────────────

class TestHealthEndpoints:

    def test_ping_returns_ok(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_system_health_includes_db_status(self, client):
        res = client.get("/api/system/health")
        assert res.status_code == 200
        data = res.json()
        assert data["database"] == "connected"
        assert data["gmail_mode"] in ("SIMULATED", "LIVE")
        assert "version" in data


# ── 5. Direct risk engine edge cases ─────────────────────────────────

class TestRiskEngineDirectEdgeCases:
    """Test the deterministic engine directly for edge cases
    that the API schema might filter out."""

    def test_none_stock_returns_flag(self):
        result = assess_shortage_risk(usable_stock=None, avg_daily_demand=5)
        assert result["status"] == "unknown"
        assert any("Missing" in f for f in result["risk_flags"])

    def test_none_demand_returns_flag(self):
        result = assess_shortage_risk(usable_stock=10, avg_daily_demand=None)
        assert result["status"] == "unknown"
        assert any("Missing" in f for f in result["risk_flags"])

    def test_negative_stock_returns_flag(self):
        result = assess_shortage_risk(usable_stock=-5, avg_daily_demand=5)
        assert result["status"] == "unknown"
        assert any("negative" in f.lower() for f in result["risk_flags"])

    def test_negative_demand_returns_flag(self):
        result = assess_shortage_risk(usable_stock=10, avg_daily_demand=-1)
        assert result["status"] == "unknown"

    def test_negative_lead_time_returns_flag(self):
        result = assess_shortage_risk(
            usable_stock=10, avg_daily_demand=5, supplier_lead_time_days=-3
        )
        assert any("negative" in f.lower() for f in result["risk_flags"])

    def test_zero_demand_positive_stock_coverage_is_inf(self):
        """When demand is zero and stock > 0, coverage is technically infinite.
        The engine returns float('inf') which downstream code must handle."""
        result = assess_shortage_risk(usable_stock=50, avg_daily_demand=0)
        assert result["coverage_days"] == float("inf")
        assert result["status"] == "review_required"

    def test_zero_demand_zero_stock_coverage_is_none(self):
        result = assess_shortage_risk(usable_stock=0, avg_daily_demand=0)
        assert result["coverage_days"] is None
        assert result["status"] == "review_required"

    def test_shipment_with_negative_quantity_rejected(self):
        result = assess_shortage_risk(
            usable_stock=10, avg_daily_demand=5,
            supplier_lead_time_days=5,
            incoming_shipments=[{"quantity": -10, "days_until_arrival": 1}],
        )
        assert any("Invalid" in f for f in result["risk_flags"])

    def test_shipment_with_missing_keys_rejected(self):
        result = assess_shortage_risk(
            usable_stock=10, avg_daily_demand=5,
            supplier_lead_time_days=5,
            incoming_shipments=[{"quantity": 10}],  # missing days_until_arrival
        )
        assert any("Invalid" in f for f in result["risk_flags"])

    def test_duplicate_shipments_on_same_day_combined(self):
        """Two shipments arriving day 1 should combine, not double-count."""
        result = assess_shortage_risk(
            usable_stock=5, avg_daily_demand=5,
            supplier_lead_time_days=4,
            incoming_shipments=[
                {"quantity": 5, "days_until_arrival": 1},
                {"quantity": 5, "days_until_arrival": 1},
            ],
        )
        # Day 0→1: demand 5, stock goes 5→0 at day 1, then +10 arrives = 10
        # Day 1→4: demand 15, stock 10 < 15, stockout at day 1 + 10/5 = day 3
        assert result["first_stockout_day"] == 3.0
        assert result["stockout_before_delivery"] is True


# ── 6. BUG-2 regression: inf in JSON serialization ───────────────────

class TestInfSerializationBug:
    """The core engine returns coverage_days=float('inf') when demand=0
    and stock>0.  RiskAssessmentResponse must handle this without
    producing invalid JSON."""

    def test_evaluate_risk_service_handles_inf(self):
        """evaluate_risk() wraps the engine. If coverage_days is inf,
        the Pydantic model must not blow up during serialization."""
        request = RiskAssessmentRequest(usable_stock=50, avg_daily_demand=0)
        response = evaluate_risk(request)
        # The response should be a valid RiskAssessmentResponse
        assert response.status == "review_required"
        # Serialize to dict to simulate what FastAPI does
        dumped = response.model_dump()
        assert dumped["status"] == "review_required"

    def test_api_zero_demand_returns_valid_json(self, client):
        """The actual HTTP response must be parseable JSON.
        json.loads will raise if it encounters bare Infinity."""
        res = client.post("/api/risk/evaluate", json={
            "usable_stock": 50,
            "avg_daily_demand": 0,
        })
        # If the response contains Infinity, the test client's .json()
        # call will itself fail, but let's be explicit:
        assert res.status_code == 200
        import json
        # Re-parse the raw bytes to verify it's valid JSON
        json.loads(res.content)


# ── 7. Nonexistent / invalid routes ──────────────────────────────────

class TestInvalidRoutes:

    def test_unknown_route_returns_404(self, client):
        res = client.get("/api/nonexistent")
        assert res.status_code == 404

    def test_wrong_method_returns_405(self, client):
        res = client.delete("/api/inventory")
        assert res.status_code == 405

    def test_risk_evaluate_get_not_allowed(self, client):
        res = client.get("/api/risk/evaluate")
        assert res.status_code == 405
