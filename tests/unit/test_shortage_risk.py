
from unittest import result

from unittest import result

import pytest

from ai_engine.risk.shortage_risk import assess_shortage_risk


def test_basic_stockout_risk():
    result = assess_shortage_risk(
        usable_stock=15,
        avg_daily_demand=5,
        supplier_lead_time_days=6,
    )

    assert result["coverage_days"] == 3.0
    assert result["estimated_stockout_days"] == 3.0
    assert result["stock_at_delivery"] == 0.0
    assert result["stockout_before_delivery"] is True
    assert result["status"] == "high_risk"
    assert result["first_stockout_day"] == 3.0

def test_delivery_before_stockout():
    result = assess_shortage_risk(
        usable_stock=50,
        avg_daily_demand=5,
        supplier_lead_time_days=3,
    )

    assert result["coverage_days"] == 10.0
    assert result["stock_at_delivery"] == 35.0
    assert result["stockout_before_delivery"] is False
    assert result["status"] == "lower_risk"
    assert result["estimated_stockout_days"] is None
    assert result["first_stockout_day"] is None
    assert result["estimated_stockout_days"] is None
    assert result["first_stockout_day"] is None

def test_incoming_stock_arrives_before_stockout():
    result = assess_shortage_risk(
        usable_stock=10,
        avg_daily_demand=5,
        supplier_lead_time_days=6,
        incoming_shipments=[
            {"quantity": 20, "days_until_arrival": 1}
        ],
    )

    assert result["stockout_before_delivery"] is False
    assert result["stock_at_delivery"] == 0.0
    assert result["status"] == "warning"
    assert result["estimated_stockout_days"] is None
    assert result["first_stockout_day"] is None


def test_incoming_stock_arrives_too_late():
    result = assess_shortage_risk(
        usable_stock=10,
        avg_daily_demand=5,
        supplier_lead_time_days=6,
        incoming_shipments=[
            {"quantity": 20, "days_until_arrival": 3}
        ],
    )

    assert result["stockout_before_delivery"] is True
    assert result["first_stockout_day"] == 2.0
    assert result["status"] == "high_risk"


def test_incoming_stock_after_delivery_is_not_counted():
    result = assess_shortage_risk(
        usable_stock=50,
        avg_daily_demand=5,
        supplier_lead_time_days=3,
        incoming_shipments=[
            {"quantity": 100, "days_until_arrival": 5}
        ],
    )

    assert result["stock_at_delivery"] == 35.0
    assert result["stockout_before_delivery"] is False


def test_missing_stock_returns_unknown():
    result = assess_shortage_risk(
        usable_stock=None,
        avg_daily_demand=5,
        supplier_lead_time_days=3,
    )

    assert result["status"] == "unknown"
    assert result["stock_at_delivery"] is None


def test_missing_demand_returns_unknown():
    result = assess_shortage_risk(
        usable_stock=20,
        avg_daily_demand=None,
        supplier_lead_time_days=3,
    )

    assert result["status"] == "unknown"
    assert result["coverage_days"] is None


def test_missing_lead_time_flags_delivery_uncertainty():
    result = assess_shortage_risk(
        usable_stock=50,
        avg_daily_demand=5,
        supplier_lead_time_days=None,
    )

    assert result["status"] == "needs_delivery_data"
    assert result["stock_at_delivery"] is None
    assert any(
        "lead time missing" in flag.lower()
        for flag in result["risk_flags"]
    )


def test_zero_demand_requires_review():
    result = assess_shortage_risk(
        usable_stock=20,
        avg_daily_demand=0,
        supplier_lead_time_days=3,
    )

    assert result["status"] == "review_required"
    assert result["estimated_stockout_days"] is None


@pytest.mark.parametrize(
    "stock, demand, lead_time",
    [
        (-1, 5, 3),
        (10, -1, 3),
        (10, 5, -1),
    ],
)
def test_negative_inputs_are_rejected(stock, demand, lead_time):
    result = assess_shortage_risk(
        usable_stock=stock,
        avg_daily_demand=demand,
        supplier_lead_time_days=lead_time,
    )

    assert result["status"] == "unknown"
    assert result["stock_at_delivery"] is None
    assert result["risk_flags"]


def test_invalid_incoming_shipment_is_rejected():
    result = assess_shortage_risk(
        usable_stock=20,
        avg_daily_demand=5,
        supplier_lead_time_days=3,
        incoming_shipments=[
            {"quantity": -10, "days_until_arrival": 1}
        ],
    )

    assert result["status"] == "unknown"
    assert result["stock_at_delivery"] is None
    assert any(
        "invalid incoming shipment" in flag.lower()
        for flag in result["risk_flags"]
    )
