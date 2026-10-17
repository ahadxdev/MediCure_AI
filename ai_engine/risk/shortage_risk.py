
from typing import Any


def assess_shortage_risk(
    usable_stock: float | None,
    avg_daily_demand: float | None,
    supplier_lead_time_days: float | None = None,
    incoming_shipments: list[dict[str, float]] | None = None,
) -> dict[str, Any]:
    """
    Deterministic shortage assessment up to the evaluated
    supplier delivery time.

    Shipment format:
        {"quantity": 20, "days_until_arrival": 2}

    Assumptions:
        - Demand remains constant.
        - Shipments arrive on schedule.
        - A shipment is added at its stated arrival time.
        - Unmet demand is not backordered.
        - The supplier delivery being evaluated is not itself
          added to stock; this evaluates stock before that delivery.
    """

    result: dict[str, Any] = {
        "status": "unknown",
        "coverage_days": None,
        "stockout_days_without_incoming": None,
        "estimated_stockout_days": None,
        "stock_at_delivery": None,
        "stockout_before_delivery": None,
        "first_stockout_day": None,
        "risk_flags": [],
        "assumptions": [
            "Demand is assumed constant.",
            "Incoming shipments are assumed to arrive on schedule.",
            "Supplier delivery estimates are not independently verified.",
            "Unmet demand is not carried forward as backorders.",
        ],
    }

    # Validate required values.
    if usable_stock is None or avg_daily_demand is None:
        result["risk_flags"].append(
            "Missing stock or demand data; assessment unavailable."
        )
        return result

    if usable_stock < 0 or avg_daily_demand < 0:
        result["risk_flags"].append(
            "Stock and demand cannot be negative."
        )
        return result

    if supplier_lead_time_days is not None:
        if supplier_lead_time_days < 0:
            result["risk_flags"].append(
                "Supplier lead time cannot be negative."
            )
            return result

    shipments = incoming_shipments or []

    # Validate shipment records before simulating.
    for shipment in shipments:
        quantity = shipment.get("quantity")
        arrival_day = shipment.get("days_until_arrival")

        if (
            quantity is None
            or arrival_day is None
            or quantity < 0
            or arrival_day < 0
        ):
            result["risk_flags"].append(
                "Invalid incoming shipment record."
            )
            return result

    # Zero demand cannot produce a meaningful finite coverage estimate.
    if avg_daily_demand == 0:
        result["coverage_days"] = (
            float("inf") if usable_stock > 0 else None
        )
        result["risk_flags"].append(
            "Demand is zero; verify history before relying on this assessment."
        )
        result["status"] = "review_required"
        return result

    # Coverage based on current stock alone.
    coverage = usable_stock / avg_daily_demand
    result["coverage_days"] = round(coverage, 2)
    result["stockout_days_without_incoming"] = round(coverage, 2)

    if coverage <= 3:
        result["risk_flags"].append(
            "Critical: current stock covers 3 days or less without replenishment."
        )
    elif coverage <= 7:
        result["risk_flags"].append(
            "Warning: current stock covers 7 days or less without replenishment."
        )

    # Without a lead time, we cannot assess stock at delivery.
    if supplier_lead_time_days is None:
        result["risk_flags"].append(
            "Supplier lead time missing; delivery risk cannot be assessed."
        )
        result["status"] = (
            "high_risk" if coverage <= 3
            else "warning" if coverage <= 7
            else "needs_delivery_data"
        )
        return result

    # Combine shipments arriving on the same day.
    arrivals: dict[float, float] = {}

    for shipment in shipments:
        day = shipment["days_until_arrival"]
        if day <= supplier_lead_time_days:
            arrivals[day] = arrivals.get(day, 0.0) + shipment["quantity"]

    stock = float(usable_stock)
    current_time = 0.0
    first_stockout_day = None

    # Simulate each interval before an incoming shipment.
    for arrival_day in sorted(arrivals):
        elapsed = arrival_day - current_time
        demand_in_interval = avg_daily_demand * elapsed

        # Strictly less means stock runs out before the interval ends.
        # Equality means stock reaches zero exactly at arrival, where
        # the shipment is available before subsequent demand.
        if stock < demand_in_interval:
            first_stockout_day = (
                current_time + stock / avg_daily_demand
            )
            stock = 0.0
        else:
            stock -= demand_in_interval

        current_time = arrival_day
        stock += arrivals[arrival_day]

    # Simulate the interval from the last arrival to delivery time.
    remaining_days = supplier_lead_time_days - current_time
    demand_until_delivery = avg_daily_demand * remaining_days

    if stock < demand_until_delivery:
        if first_stockout_day is None:
            first_stockout_day = (
                current_time + stock / avg_daily_demand
            )
        stock = 0.0
    else:
        stock -= demand_until_delivery

    stockout_before_delivery = first_stockout_day is not None

    result["stock_at_delivery"] = round(stock, 2)
    result["stockout_before_delivery"] = stockout_before_delivery
    result["first_stockout_day"] = (
        round(first_stockout_day, 2)
        if first_stockout_day is not None
        else None
    )
    result["estimated_stockout_days"] = (
        result["first_stockout_day"]
    )

    if stockout_before_delivery:
        result["risk_flags"].append(
            "Stockout is expected before the evaluated delivery time "
            "under the stated assumptions."
        )
        result["status"] = "high_risk"
    elif coverage <= 3:
        result["risk_flags"].append(
            "Low initial coverage; the plan depends on timely replenishment."
        )
        result["status"] = "warning"
    elif coverage <= 7:
        result["status"] = "warning"
    else:
        result["status"] = "lower_risk"

    return result
