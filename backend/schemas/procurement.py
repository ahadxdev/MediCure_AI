from datetime import datetime, date
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


# -------------------------------------------------------------------------
# Quotations & RFQ Schemas
# -------------------------------------------------------------------------

class QuotationRequestCreate(BaseModel):
    medicine_id: str = Field(min_length=1)
    required_quantity: float = Field(gt=0)
    required_by_date: date | None = None
    delivery_location: str = Field(default="Central Pharmacy, Islamabad", min_length=1)
    supplier_ids: list[str] = Field(default_factory=list)


class QuotationRequestResponse(BaseModel):
    id: str
    medicine_id: str
    medicine_name: str | None = None
    required_quantity: float
    required_by_date: date | None = None
    delivery_location: str | None = None
    status: str
    created_at: datetime
    supplier_ids: list[str] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class QuotationApprovalRequest(BaseModel):
    approved: bool
    notes: str | None = None


class QuotationResponse(BaseModel):
    id: str
    request_id: str | None = None
    supplier_id: str | None = None
    supplier_name: str | None = None
    medicine_id: str | None = None
    medicine_name: str | None = None
    source_email: str | None = None
    source_thread_id: str | None = None
    price: float | None = None
    currency: str = "PKR"
    price_unit: str | None = None
    quoted_quantity: float | None = None
    minimum_order_quantity: float | None = None
    delivery_days: float | None = None
    delivery_fee: float | None = 0.0
    payment_terms: str | None = None
    valid_until: str | None = None
    review_status: str = "pending"
    warning_flags: list[str] = Field(default_factory=list)
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class QuoteParseRequest(BaseModel):
    raw_email_text: str = Field(min_length=5)
    supplier_id: str | None = None
    request_id: str | None = None


class QuoteInboxSyncRequest(BaseModel):
    query: str = Field(
        default="in:inbox newer_than:90d",
        min_length=1,
        max_length=500,
    )
    max_results: int = Field(default=50, ge=1, le=100)


class QuoteInboxSyncResponse(BaseModel):
    scanned: int
    imported: int
    duplicates: int
    ignored: int
    mode: str


# -------------------------------------------------------------------------
# Procurement Simulation Schemas
# -------------------------------------------------------------------------

class SimulationOption(BaseModel):
    scenario_type: str  # "fastest", "cheapest", "split_order", "infeasible"
    title: str
    supplier_name: str
    allocated_quantity: float
    unit_price: float
    delivery_fee: float
    total_cost: float
    delivery_days: float
    residual_shortage_days: float
    explanation: str
    feasibility_status: str  # "feasible", "warning", "infeasible"
    allocations: list[dict[str, Any]] = Field(default_factory=list)


class SimulationRequest(BaseModel):
    medicine_id: str = Field(min_length=1)
    required_quantity: float = Field(gt=0)
    budget_limit: float = Field(gt=0, default=50000.0)
    max_delivery_days: float = Field(gt=0, default=7.0)
    demand_surge_percent: float = Field(ge=0, le=500, default=0.0)
    supplier_delay_days: float = Field(ge=0, le=365, default=0.0)


class SimulationResponse(BaseModel):
    medicine_id: str
    medicine_name: str
    required_quantity: float
    options: list[SimulationOption]
    quotes_evaluated_count: int


# -------------------------------------------------------------------------
# Purchase Order Schemas
# -------------------------------------------------------------------------

class PurchaseOrderCreate(BaseModel):
    quotation_id: str | None = None
    medicine_id: str = Field(min_length=1)
    supplier_name: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    delivery_fee: float = Field(ge=0, default=0.0)
    total_amount: float = Field(gt=0)
    delivery_estimate_days: float = Field(ge=0, default=3.0)


class AppSettingsResponse(BaseModel):
    dispensary_name: str
    dispensary_city: str
    reorder_threshold_days: float


class AppSettingsUpdate(AppSettingsResponse):
    pass


class PurchaseOrderResponse(BaseModel):
    id: str
    po_number: str
    quotation_id: str | None = None
    medicine_name: str | None = None
    pack_size: str | None = None
    supplier_name: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    delivery_fee: float | None = None
    total_amount: float
    status: str
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime
    delivery_estimate_days: float | None = None
    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderAction(BaseModel):
    approved: bool
    actor_name: str = "Lead Pharmacist"
    notes: str | None = None


# -------------------------------------------------------------------------
# Audit Log Schemas
# -------------------------------------------------------------------------

class AuditEventResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    event_type: str
    actor: str
    timestamp: datetime
    payload: dict[str, Any] | None = None
    model_config = ConfigDict(from_attributes=True)
