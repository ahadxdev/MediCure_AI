from typing import Literal
from pydantic import BaseModel, Field


class SupplierQuote(BaseModel):
    supplier_name: str | None = None

    request_id: str | None = None
    thread_id: str | None = None
    message_id: str | None = None

    medicine_name: str | None = None
    strength: str | None = None
    dosage_form: str | None = None
    pack_size: str | None = None

    price: float | None = Field(default=None, ge=0)
    price_unit: str | None = None
    currency: str | None = None

    quoted_quantity: float | None = Field(
        default=None, gt=0
    )
    minimum_order_quantity: float | None = Field(
        default=None, gt=0
    )

    delivery_days: float | None = Field(
        default=None, ge=0
    )
    delivery_fee: float | None = Field(default=None, ge=0)
    payment_terms: str | None = None
    valid_until: str | None = None

    conditions: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    warning_flags: list[str] = Field(default_factory=list)

    review_status: Literal[
        "needs_review",
        "validated",
        "rejected"
    ] = "needs_review"
