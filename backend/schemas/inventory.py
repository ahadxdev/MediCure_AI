from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class MedicineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    generic_name: str | None = Field(default=None, max_length=255)
    category: str | None = Field(default="other", max_length=100)
    strength: str = Field(min_length=1, max_length=100)
    dosage_form: str = Field(min_length=1, max_length=100)
    pack_size: str = Field(min_length=1, max_length=100)
    usable_stock: float = Field(ge=0, default=0.0)
    reorder_level: float = Field(ge=0, default=0.0)


class InventoryItemResponse(BaseModel):
    medicine_id: str
    name: str
    generic_name: str | None = None
    category: str | None = None
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
