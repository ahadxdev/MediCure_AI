
from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    # Inventory/risk input
    medicine_name: str
    strength: str
    dosage_form: str
    pack_size: str
    usable_stock: float
    avg_daily_demand: float
    supplier_lead_time_days: float | None
    incoming_shipments: list[dict[str, float]]

    # Supplier request details supplied by the user/system
    required_quantity: float
    delivery_location: str
    required_by_date: str
    supplier_emails: list[str]
    request_id: str
    force_rfq: bool

    # Workflow outputs
    risk_result: dict[str, Any]
    email_draft: dict[str, Any]
    email_approval: dict[str, Any]
    email_status: str
    review_reason: str
    next_action: str

    # Gmail integration
    gmail_messages: list[dict[str, Any]]
    email_error: str
