
from typing import Any


def assess_shortage_risk(
    usable_stock: float | None,
    avg_daily_demand: float | None,
    supplier_lead_time_days: float | None = None,
    incoming_shipments: list[dict[str, float]] | None = None,
) -> dict[str, Any]:
    """
    Deterministic stock-shortage assessment.

    Args:
        usable_stock:
            Current usable inventory. Expired/damaged stock exclude karo.

        avg_daily_demand:
            Expected units sold per day. Forecast weekly ho to / 7.

        supplier_lead_time_days:
            Supplier ki estimated delivery tak days.

        incoming_shipments:
            Example:
            [
                {"quantity": 20, "days_until_arrival": 2},
                {"quantity": 10, "days_until_arrival": 5},
            ]

    Assumptions:
        - Demand is constant over the simulated period.
        - Incoming quantities arrive on their stated arrival days.
        - Unfulfilled demand during a stockout is lost, not backordered.
        - This function does not verify supplier claims.
    """

    result: dict[str, Any] = {
        "status": "unknown",
        "coverage_days": None,
        "estimated_stockout_days": None,
        "stock_at_delivery": None,
        "stockout_before_delivery": None,
        "risk_flags": [],
        "assumptions": [
            "Demand is assumed constant over the forecast period.",
            "Incoming shipments are assumed to arrive as scheduled.",
            "Supplier delivery estimates are not independently verified.",
        ],
    }

    # Validate required inventory data.
    if usable_stock is None or avg_daily_demand is None:
        result["risk_flags"].append(
            "Missing stock or demand data; shortage assessment unavailable."
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

    # Validate incoming inventory records.
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

    # Zero demand means coverage cannot be expressed as a finite number.
    if avg_daily_demand == 0:
        result["coverage_days"] = (
            float("inf") if usable_stock > 0 else None
        )
        result["estimated_stockout_days"] = None

        if usable_stock == 0:
            result["risk_flags"].append(
                "Stock is zero; demand is currently zero. "
                "Future demand is unknown."
            )
            result["status"] = "review_required"
        else:
            result["risk_flags"].append(
                "No demand observed or forecast; verify demand history."
            )
            result["status"] = "review_required"

        return result

    # Current coverage excludes incoming stock.
    coverage = usable_stock / avg_daily_demand
    result["coverage_days"] = round(coverage, 2)
    result["estimated_stockout_days"] = round(coverage, 2)

    if coverage <= 3:
        result["risk_flags"].append(
            "Critical: current stock covers 3 days or less."
        )
    elif coverage <= 7:
        result["risk_flags"].append(
            "Warning: current stock covers 7 days or less."
        )

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

    # Simulate inventory over time, including arrivals.
    # If stock runs out, unmet demand is not carried forward.
    arrivals: dict[float, float] = {}

    for shipment in shipments:
        day = shipment["days_until_arrival"]
        arrivals[day] = arrivals.get(day, 0) + shipment["quantity"]

    current_time = 0.0
    stock = float(usable_stock)
    stockout_before_delivery = False
    first_stockout_day = None

    for arrival_day in sorted(
        day for day in arrivals if day <= supplier_lead_time_days
    ):
        interval = arrival_day - current_time
        demand_in_interval = avg_daily_demand * interval

        if stock < demand_in_interval:
            stockout_time = current_time + stock / avg_daily_demand
            stockout_before_delivery = True

            if first_stockout_day is None:
                first_stockout_day = stockout_time

            stock = 0.0
        else:
            stock -= demand_in_interval

        current_time = arrival_day
        stock += arrivals[arrival_day]

    # Simulate from last arrival until the supplier's delivery day.
    remaining_days = supplier_lead_time_days - current_time
    demand_until_delivery = avg_daily_demand * remaining_days

    if stock < demand_until_delivery:
        stockout_time = current_time + stock / avg_daily_demand
        stockout_before_delivery = True

        if first_stockout_day is None:
            first_stockout_day = stockout_time

        stock = 0.0
    else:
        stock -= demand_until_delivery

    result["stock_at_delivery"] = round(stock, 2)
    result["stockout_before_delivery"] = stockout_before_delivery

    if stockout_before_delivery:
        result["risk_flags"].append(
            "Stockout may occur before the evaluated delivery date."
        )
        result["first_stockout_day"] = round(first_stockout_day, 2)

    if stockout_before_delivery:
        result["status"] = "high_risk"
    elif coverage <= 3:
        result["status"] = "high_risk"
    elif coverage <= 7:
        result["status"] = "warning"
    else:
        result["status"] = "lower_risk"

    return result
