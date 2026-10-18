from pydantic import BaseModel, Field


class IncomingShipment(BaseModel):
    quantity: float = Field(gt=0, description="Shipment quantity in units or packs")
    days_until_arrival: float = Field(ge=0, description="Expected arrival in days from today")


class RiskAssessmentRequest(BaseModel):
    usable_stock: float = Field(ge=0, description="Current usable units on shelf")
    avg_daily_demand: float = Field(ge=0, description="Average daily consumption or sales")
    supplier_lead_time_days: float | None = Field(default=None, ge=0, description="Estimated supplier delivery days")
    incoming_shipments: list[IncomingShipment] = Field(default_factory=list, description="Scheduled incoming orders")


class RiskAssessmentResponse(BaseModel):
    status: str
    coverage_days: float | None = None
    stockout_days_without_incoming: float | None = None
    estimated_stockout_days: float | None = None
    stock_at_delivery: float | None = None
    stockout_before_delivery: bool | None = None
    first_stockout_day: float | None = None
    risk_flags: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class RecommendedMedicine(BaseModel):
    medicine_id: str
    name: str
    strength: str
    dosage_form: str
    pack_size: str
    usable_stock: float
    reorder_level: float
    avg_daily_demand: float | None = None
    coverage_days: float | None = None
    sales_data_type: str
    reasons: list[str] = Field(default_factory=list)


class CategoryRecommendation(BaseModel):
    category: str
    next_week_demand: float
    recent_weekly_average: float
    change_percent: float | None = None
    priority: str
    medicines: list[RecommendedMedicine] = Field(default_factory=list)


class CategoryRecommendationsResponse(BaseModel):
    model: str
    source: str
    latest_observation: str
    note: str
    categories: list[CategoryRecommendation]
