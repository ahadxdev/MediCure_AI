from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "Dataset" / "salesweekly.csv"

PAKISTANI_MEDICINE_CATALOG: list[dict[str, Any]] = [
    {
        "name": "Panadol 500mg Tablets",
        "generic_name": "Paracetamol",
        "strength": "500 mg",
        "dosage_form": "Tablet",
        "pack_size": "100 tablets",
        "category": "N02BE",
    },
    {
        "name": "Augmentin 625mg Tablets",
        "generic_name": "Amoxicillin + Clavulanic Acid",
        "strength": "625 mg",
        "dosage_form": "Tablet",
        "pack_size": "14 tablets",
        "category": "other",
    },
    {
        "name": "Brufen 400mg Tablets",
        "generic_name": "Ibuprofen",
        "strength": "400 mg",
        "dosage_form": "Tablet",
        "pack_size": "30 tablets",
        "category": "M01AE",
    },
    {
        "name": "Disprin 300mg Tablets",
        "generic_name": "Acetylsalicylic Acid",
        "strength": "300 mg",
        "dosage_form": "Tablet",
        "pack_size": "30 tablets",
        "category": "N02BA",
    },
    {
        "name": "Valium 5mg Tablets",
        "generic_name": "Diazepam",
        "strength": "5 mg",
        "dosage_form": "Tablet",
        "pack_size": "30 tablets",
        "category": "N05B",
    },
    {
        "name": "Lorazepam 1mg Tablets",
        "generic_name": "Lorazepam",
        "strength": "1 mg",
        "dosage_form": "Tablet",
        "pack_size": "30 tablets",
        "category": "N05B",
    },
    {
        "name": "Ventolin Inhaler",
        "generic_name": "Salbutamol",
        "strength": "100 mcg / inhalation",
        "dosage_form": "Inhaler",
        "pack_size": "1 inhaler",
        "category": "R03",
    },
    {
        "name": "Cetirizine 10mg Tablets",
        "generic_name": "Cetirizine",
        "strength": "10 mg",
        "dosage_form": "Tablet",
        "pack_size": "10 tablets",
        "category": "R06",
    },
    {
        "name": "Cefixime 200mg Capsules",
        "generic_name": "Cefixime",
        "strength": "200 mg",
        "dosage_form": "Capsule",
        "pack_size": "10 capsules",
        "category": "other",
    },
    {
        "name": "Naproxen 250mg Tablets",
        "generic_name": "Naproxen",
        "strength": "250 mg",
        "dosage_form": "Tablet",
        "pack_size": "30 tablets",
        "category": "M01AE",
    },
    {
        "name": "Aspirin 75mg Tablets",
        "generic_name": "Acetylsalicylic Acid",
        "strength": "75 mg",
        "dosage_form": "Tablet",
        "pack_size": "30 tablets",
        "category": "N02BA",
    },
    {
        "name": "Zyrtec 10mg Tablets",
        "generic_name": "Cetirizine",
        "strength": "10 mg",
        "dosage_form": "Tablet",
        "pack_size": "30 tablets",
        "category": "R06",
    },
    {
        "name": "Salbutamol Nebules",
        "generic_name": "Salbutamol",
        "strength": "2.5 mg / 2.5 ml",
        "dosage_form": "Nebules",
        "pack_size": "20 ampoules",
        "category": "R03",
    },
    {
        "name": "Calcium Channel Blocker (Amlodipine 5mg)",
        "generic_name": "Amlodipine",
        "strength": "5 mg",
        "dosage_form": "Tablet",
        "pack_size": "30 tablets",
        "category": "other",
    },
    {
        "name": "Zolpidem 10mg Tablets",
        "generic_name": "Zolpidem",
        "strength": "10 mg",
        "dosage_form": "Tablet",
        "pack_size": "30 tablets",
        "category": "N05C",
    },
]

CATEGORY_ORDER = ["M01AB", "M01AE", "N02BA", "N02BE", "N05B", "N05C", "R03", "R06"]


def get_medicine_catalog() -> list[dict[str, Any]]:
    return [entry.copy() for entry in PAKISTANI_MEDICINE_CATALOG]


def get_catalog_entry(name: str | None) -> dict[str, Any] | None:
    if not name:
        return None
    for item in PAKISTANI_MEDICINE_CATALOG:
        if item["name"].lower() == name.strip().lower():
            return item.copy()
    return None


def get_catalog_entry_by_generic(generic_name: str | None) -> dict[str, Any] | None:
    if not generic_name:
        return None
    normalized = generic_name.strip().casefold()
    for item in PAKISTANI_MEDICINE_CATALOG:
        if item["generic_name"].casefold() == normalized:
            return item.copy()
    return None


def _load_category_baselines() -> dict[str, float]:
    if not DATASET_PATH.exists():
        return {category: 15.0 for category in CATEGORY_ORDER}

    with DATASET_PATH.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        data = list(reader)

    baselines: dict[str, float] = {}
    for category in CATEGORY_ORDER:
        values = []
        for row in data:
            raw_value = row.get(category)
            if raw_value is None or raw_value == "":
                continue
            try:
                values.append(float(raw_value))
            except ValueError:
                continue
        baselines[category] = sum(values) / len(values) if values else 15.0
    return baselines


def generate_demo_sales_history_for_category(category: str, weeks: int = 12, as_of: date | None = None) -> list[dict[str, Any]]:
    """Produce deterministic synthetic sales records for a medicine based on the dataset category trend."""
    baseline_by_category = _load_category_baselines()
    base = max(1.0, baseline_by_category.get(category, 15.0) * 0.85)
    current = as_of or date.today()
    history: list[dict[str, Any]] = []

    for offset in range(weeks):
        sale_date = current - timedelta(weeks=weeks - offset)
        wave = 1 + 0.28 * ((offset % 5) - 2) / 2
        seasonal = 1.0 + 0.18 * ((offset % 4) - 1.5)
        quantity = round(max(0.5, base * wave * seasonal), 2)
        history.append({
            "sale_date": sale_date.isoformat(),
            "quantity_dispensed": quantity,
        })

    return history
