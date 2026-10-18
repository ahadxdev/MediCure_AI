import pandas as pd
import pytest

from ai_engine.risk.category_forecast import forecast_category_sales, forecast_next_week
from backend.services.medicine_catalog import get_catalog_entry


def test_random_forest_forecasts_each_category_from_bundled_dataset():
    result = forecast_category_sales()

    assert result["model"] == "Random Forest"
    assert result["latest_observation"] == "2019-10-13"
    assert len(result["categories"]) == 8
    assert all(category["next_week_demand"] >= 0 for category in result["categories"])


def test_forecast_requires_more_than_52_weeks():
    with pytest.raises(ValueError, match="more than 52 weeks"):
        forecast_next_week(pd.Series([1.0] * 52))


def test_forecast_rejects_missing_sales_values():
    with pytest.raises(ValueError, match="non-negative numeric values"):
        forecast_next_week(pd.Series([1.0] * 52 + [None]))


def test_catalog_does_not_force_unrepresented_or_mismatched_categories():
    assert get_catalog_entry("Augmentin 625mg Tablets")["category"] == "other"
    assert get_catalog_entry("Calcium Channel Blocker (Amlodipine 5mg)")["category"] == "other"
    assert get_catalog_entry("Lorazepam 1mg Tablets")["category"] == "N05B"
