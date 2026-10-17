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
