from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class MedicineCreate(BaseModel):
    name: str = Field(min_length=1)
    generic_name: str | None = None
    strength: str = Field(min_length=1)
    dosage_form: str = Field(min_length=1)
    pack_size: str = Field(min_length=1)
    usable_stock: float = Field(ge=0, default=0.0)
    reorder_level: float = Field(ge=0, default=0.0)


class InventoryItemResponse(BaseModel):
    medicine_id: str
    name: str
    generic_name: str | None = None
    strength: str
    dosage_form: str
    pack_size: str
    usable_stock: float
    reorder_level: float
    avg_daily_demand: float
    coverage_days: float | None = None
    status: str
    last_counted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class InventoryListResponse(BaseModel):
    total_items: int
    items: list[InventoryItemResponse]
