# MediProcure AI — API Specifications & Data Models

> **Protocol:** RESTful JSON over HTTP  
> **Backend Framework:** FastAPI  
> **Data Validation:** Pydantic v2  
> **Database:** PostgreSQL (with SQLite local fallback)

---

## 1. Entity-Relationship Data Model

```mermaid
erDiagram
    MEDICINE ||--o{ INVENTORY_RECORD : has
    MEDICINE ||--o{ SALES_RECORD : records
    MEDICINE ||--o{ QUOTATION_REQUEST : targets
    SUPPLIER ||--o{ SUPPLIER_PRODUCT : offers
    SUPPLIER ||--o{ QUOTATION : submits
    MEDICINE ||--o{ SUPPLIER_PRODUCT : catalogued
    QUOTATION_REQUEST ||--o{ QUOTATION : receives
    QUOTATION ||--o{ PURCHASE_ORDER : converts_to
    PURCHASE_ORDER ||--o{ AUDIT_EVENT : logs

    MEDICINE {
        string id PK
        string name
        string generic_name
        string strength
        string dosage_form
        string pack_size
        string created_at
    }

    INVENTORY_RECORD {
        string id PK
        string medicine_id FK
        float usable_stock
        float reorder_level
        datetime last_counted_at
    }

    SALES_RECORD {
        string id PK
        string medicine_id FK
        date sale_date
        float quantity_dispensed
    }

    SUPPLIER {
        string id PK
        string name
        string email
        string phone
        string address
        boolean is_verified
        float default_lead_time_days
    }

    QUOTATION_REQUEST {
        string id PK
        string medicine_id FK
        float required_quantity
        date required_by_date
        string delivery_location
        string status
        datetime created_at
    }

    QUOTATION {
        string id PK
        string request_id FK
        string supplier_id FK
        string raw_email_body
        float price
        string currency
        string price_unit
        float quoted_quantity
        float minimum_order_quantity
        float delivery_days
        float delivery_fee
        string payment_terms
        string valid_until
        string review_status
        string warning_flags
    }

    PURCHASE_ORDER {
        string id PK
        string quotation_id FK
        string po_number
        float total_amount
        string status
        string approved_by
        datetime approved_at
    }

    AUDIT_EVENT {
        string id PK
        string entity_type
        string entity_id
        string event_type
        string actor
        datetime timestamp
        json payload
    }
```

---

## 2. Pydantic Schemas

### 2.1 Shortage Risk Assessment
```python
from pydantic import BaseModel, Field

class IncomingShipment(BaseModel):
    quantity: float = Field(gt=0)
    days_until_arrival: float = Field(ge=0)

class RiskAssessmentRequest(BaseModel):
    usable_stock: float = Field(ge=0)
    avg_daily_demand: float = Field(ge=0)
    supplier_lead_time_days: float | None = Field(default=None, ge=0)
    incoming_shipments: list[IncomingShipment] = Field(default_factory=list)

class RiskAssessmentResponse(BaseModel):
    status: str
    coverage_days: float | None
    stockout_days_without_incoming: float | None
    estimated_stockout_days: float | None
    stock_at_delivery: float | None
    stockout_before_delivery: bool | None
    first_stockout_day: float | None
    risk_flags: list[str]
    assumptions: list[str]
```

### 2.2 Quotation Request & Email Draft
```python
class EmailDraft(BaseModel):
    to: list[str]
    subject: str
    body: str

class QuotationDraftRequest(BaseModel):
    medicine_id: str
    required_quantity: float = Field(gt=0)
    delivery_location: str
    required_by_date: str
    supplier_ids: list[str]

class QuotationApprovalAction(BaseModel):
    thread_id: str
    approved: bool
    notes: str | None = None
```

### 2.3 Procurement Simulation Models
```python
class ScenarioOption(BaseModel):
    scenario_type: str  # "cheapest", "fastest", "split_order", "infeasible"
    supplier_name: str | None
    allocated_quantity: float
    unit_price: float | None
    delivery_fee: float | None
    total_cost: float | None
    delivery_days: float | None
    residual_shortage_days: float
    explanation: str

class SimulationResult(BaseModel):
    medicine_name: str
    options: list[ScenarioOption]
    data_quality_flags: list[str]
```

---

## 3. Core REST Endpoints

### 3.1 Inventory & Shortage Radar
- `GET /api/inventory`: Returns current stock, reorder levels, and 30-day demand velocity for all catalog medicines.
- `POST /api/risk/evaluate`: Computes deterministic shortage risk for a specific medicine record.

### 3.2 Quotations & Supplier Messaging
- `POST /api/quotes/draft`: Generates standardized quote request draft without sending.
- `POST /api/quotes/approve-and-send`: Pharmacist human approval. Dispatches email through Gmail API or simulated dispatcher.
- `GET /api/quotes/requests/{id}/replies`: Retrieves incoming supplier messages mapped to the request ID.
- `POST /api/quotes/parse`: Runs parser and anomaly validator on raw quotation text.

### 3.3 Procurement Simulation & Purchase Orders
- `POST /api/procurement/simulate`: Runs multi-criteria comparison across verified quotes.
- `POST /api/procurement/what-if`: Runs dynamic constraint recalculations with user-specified budget/demand overrides.
- `POST /api/orders/create-draft`: Generates formal Draft Purchase Order based on selected simulation option.
- `POST /api/orders/{id}/approve`: Final human sign-off committing the PO and logging audit record.

### 3.4 Auditing & System Status
- `GET /api/audit/logs`: Fetches chronological audit trail with pagination and entity filtering.
- `GET /api/system/health`: Reports health status of FastAPI server, DB connection, and Gmail OAuth status.
