
import pandas as pd

from ai_engine.risk.category_forecast import (
    CATEGORY_CODES as SALES_COLUMNS,
    DATA_PATH,
    forecast_next_week,
)
from ai_engine.risk.shortage_risk import assess_shortage_risk


# DEMO DATA ONLY: not actual pharmacy inventory or supplier information.
DEMO_INVENTORY = {
    "M01AB": {"stock": 15, "lead_time": 6},
    "M01AE": {"stock": 30, "lead_time": 3},
    "N02BA": {"stock": 20, "lead_time": 5},
    "N02BE": {"stock": 25, "lead_time": 2},
    "N05B":  {"stock": 18, "lead_time": 4},
    "N05C":  {"stock": 10, "lead_time": 6},
    "R03":   {"stock": 40, "lead_time": 3},
    "R06":   {"stock": 20, "lead_time": 5},
}


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    data = pd.read_csv(DATA_PATH)

    missing_columns = [
        col for col in ["datum", *SALES_COLUMNS]
        if col not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Dataset is missing columns: {missing_columns}"
        )

    data["datum"] = pd.to_datetime(
        data["datum"], errors="coerce"
    )

    data = data.dropna(subset=["datum"])
    data = data.sort_values("datum").reset_index(drop=True)

    for col in SALES_COLUMNS:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    if data[SALES_COLUMNS].isna().any().any():
        raise ValueError(
            "Sales data contains missing or non-numeric values. "
            "Clean or investigate them before forecasting."
        )

    if (data[SALES_COLUMNS] < 0).any().any():
        raise ValueError(
            "Negative sales values found. Review the source data."
        )

    print("=" * 65)
    print("MEDIPROCURE AI — SHORTAGE DEMO")
    print("Inventory and lead times below are illustrative demo inputs.")
    print("=" * 65)
    print(f"Latest historical week: {data['datum'].max().date()}")

    for category in SALES_COLUMNS:
        weekly_demand = forecast_next_week(data[category])
        daily_demand = weekly_demand / 7.0

        inventory = DEMO_INVENTORY[category]

        risk = assess_shortage_risk(
            usable_stock=inventory["stock"],
            avg_daily_demand=daily_demand,
            supplier_lead_time_days=inventory["lead_time"],
            incoming_shipments=[],
        )

        print(f"\nCategory: {category}")
        print(f"Forecast next week (units): {weekly_demand:.2f}")
        print(f"Estimated daily demand: {daily_demand:.2f}")
        print(f"Demo usable stock: {inventory['stock']} units")
        print(f"Demo supplier lead time: {inventory['lead_time']} days")
        print(f"Coverage days: {risk['coverage_days']}")
        print(f"Estimated stock at delivery: {risk['stock_at_delivery']}")
        print(f"Stockout before delivery: {risk['stockout_before_delivery']}")
        print(f"Risk status: {risk['status']}")

        for flag in risk["risk_flags"]:
            print(f"  - {flag}")


if __name__ == "__main__":
    main()
