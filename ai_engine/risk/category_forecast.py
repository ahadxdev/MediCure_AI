from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "Dataset" / "salesweekly.csv"
CATEGORY_CODES = ["M01AB", "M01AE", "N02BA", "N02BE", "N05B", "N05C", "R03", "R06"]
LAGS = [1, 2, 3, 4, 8, 13, 26, 52]


def forecast_next_week(series: pd.Series) -> float:
    """Fit a Random Forest to one weekly category series and forecast its next value."""
    values = pd.to_numeric(series, errors="coerce").reset_index(drop=True)
    if len(values) <= max(LAGS):
        raise ValueError(f"Not enough history: need more than {max(LAGS)} weeks.")
    if values.isna().any() or (values < 0).any():
        raise ValueError("Sales history must contain only non-negative numeric values.")

    features = pd.DataFrame({
        f"lag_{lag}": values.shift(lag)
        for lag in LAGS
    })
    training_data = features.assign(target=values).dropna()
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=5,
        min_samples_leaf=3,
        random_state=42,
    )
    model.fit(training_data.drop(columns=["target"]), training_data["target"])

    next_week = pd.DataFrame([{
        f"lag_{lag}": float(values.iloc[-lag])
        for lag in LAGS
    }])
    return max(0.0, float(model.predict(next_week)[0]))


def forecast_category_sales(path: Path = DATA_PATH) -> dict:
    """Forecast all supported dataset categories and report the source's latest week."""
    if not path.exists():
        raise FileNotFoundError(f"Sales dataset not found: {path}")

    data = pd.read_csv(path)
    missing = [column for column in ["datum", *CATEGORY_CODES] if column not in data.columns]
    if missing:
        raise ValueError(f"Sales dataset is missing columns: {missing}")

    data["datum"] = pd.to_datetime(data["datum"], errors="coerce")
    data = data.dropna(subset=["datum"]).sort_values("datum").reset_index(drop=True)
    if data.empty:
        raise ValueError("Sales dataset contains no valid observation dates.")

    categories = []
    for code in CATEGORY_CODES:
        sales = pd.to_numeric(data[code], errors="coerce")
        if sales.isna().any() or (sales < 0).any():
            raise ValueError(f"Sales history for {code} contains missing or invalid values.")
        recent_average = float(sales.tail(4).mean())
        forecast = forecast_next_week(sales)
        change_percent = (
            round((forecast - recent_average) / recent_average * 100, 1)
            if recent_average > 0
            else None
        )
        categories.append({
            "category": code,
            "next_week_demand": round(forecast, 2),
            "recent_weekly_average": round(recent_average, 2),
            "change_percent": change_percent,
        })

    return {
        "model": "Random Forest",
        "source": path.name,
        "latest_observation": data["datum"].max().date().isoformat(),
        "categories": categories,
    }
