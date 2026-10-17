# MediProcure AI — Development Phases & Progress Roadmap

> **Hackathon Deadline:** 19 October 2026, 11:59 PM PKT  
> **Team Workstreams:**  
> 1. AI & Agent Workflow  
> 2. Backend & Data Engineering  
> 3. Frontend & Integration  

---

## 1. Phase Overview & Current Status

| Phase | Description | Target Completion | Current Status | Responsible Workstream |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | Core AI Engine, Deterministic Risk & Quotation Parser | Oct 17 | **COMPLETED & TESTED** | AI & Agent Workflow |
| **Phase 2** | Database Schemas, FastAPI Backend & Audit Engine | Oct 18 (Morning) | **READY FOR IMPLEMENTATION** | Backend & Data |
| **Phase 3** | Procurement Response Simulator & What-If Engine | Oct 18 (Afternoon) | **READY FOR IMPLEMENTATION** | Backend + AI Engine |
| **Phase 4** | Web Frontend (Dashboard, Radar, Approval, Simulator UI) | Oct 18 (Night) - Oct 19 | **READY FOR IMPLEMENTATION** | Frontend & Integration |
| **Phase 5** | End-to-End Integration, Evaluation Scenarios, Video & Polish | Oct 19 (Before Deadline) | **PLANNED** | Full Team |

---

## 2. Detailed Task Breakdown & Progress Tracker

### Phase 1: Core AI Engine, Risk Module & Quotation Parser
- [x] **Shortage Risk Calculation Engine (`ai_engine/risk/shortage_risk.py`)**
  - [x] Deterministic calculation of stock coverage days
  - [x] Simulation of stock trajectory with incoming scheduled shipments
  - [x] Detection of stockout before supplier delivery
  - [x] Zero-demand and negative value validation
  - [x] 13 comprehensive unit tests passing (`tests/unit/test_shortage_risk.py`)
- [x] **Quotation Parser & Anomaly Validator (`ai_engine/quotes/`)**
  - [x] Pydantic `SupplierQuote` schema with 12 structured parameters
  - [x] Extraction of medicine, strength, dosage form, pack size, price, currency, quantity, MOQ, delivery days, payment terms, validity
  - [x] Anomaly validation rules (invalid prices, negative delivery fee, quantity below MOQ, unstated validity)
  - [x] Unit test suite passing (`tests/unit/test_quote_parser.py`)
- [x] **Gmail API Gateway (`ai_engine/gmail/client.py`)**
  - [x] Google OAuth 2.0 credential management and client initialization
  - [x] Send email functionality supporting separate recipient dispatch
  - [x] Controlled test scripts (`test_gmail_connection.py`, `test_gmail_send.py`)
- [x] **Stateful LangGraph Workflow (`ai_engine/agent/graph.py`)**
  - [x] State graph linking `assess_risk` -> `prepare_draft` -> `human_approval` -> `send_email`
  - [x] LangGraph `interrupt()` breakpoint for human approval
  - [x] Standalone runnable demonstration script (`run_agent_demo.py`)

---

### Phase 2: FastAPI Backend, Relational Schemas & Audit Trail
- [x] **Data Model & Schema Migration (`backend/models/`)**
  - [x] SQLAlchemy entities:
    - `Medicine` (id, name, generic_name, strength, dosage_form, pack_size, created_at)
    - `InventoryRecord` (id, medicine_id, usable_stock, reorder_level, last_counted_at)
    - `SalesRecord` (id, medicine_id, sale_date, quantity_dispensed)
    - `Supplier` (id, name, email, phone, address, is_verified, default_lead_time_days)
    - `QuotationRequest` (id, medicine_id, required_quantity, required_by_date, status, created_at)
    - `Quotation` (id, request_id, supplier_id, raw_email_body, price, currency, review_status)
    - `PurchaseOrder` (id, quotation_id, po_number, total_amount, status, approved_by, approved_at)
    - `AuditEvent` (id, entity_type, entity_id, event_type, actor, timestamp, payload)
- [x] **FastAPI Core Application (`backend/main.py`)**
  - [x] CORS middleware, lifespan database initialization, health-check endpoints (`GET /api/health`, `GET /api/system/health`)
- [ ] **API Endpoints (`backend/api/`)**
  - [x] `GET /api/inventory` — list medicines, stock levels, sales velocity, and calculated coverage
  - [x] `POST /api/inventory` — add medicine with inventory parameters
  - [x] `POST /api/inventory/seed` — manual seed trigger
  - [x] `POST /api/risk/evaluate` — evaluate deterministic shortage risk for given payload
  - [x] `GET /api/risk/medicines/{id}` — evaluate live shortage risk for registered medicine
  - [ ] `POST /api/quotes/draft` — draft quotation email request
  - [ ] `POST /api/quotes/approve-and-send` — approve draft and dispatch via Gmail
  - [ ] `GET /api/quotes/inbox` — fetch received quotations and extraction statuses
  - [ ] `POST /api/procurement/simulate` — run procurement scenario evaluations
  - [ ] `POST /api/orders/draft` — generate draft purchase order
  - [ ] `POST /api/orders/approve` — final human approval of purchase order
  - [ ] `GET /api/audit` — immutable activity ledger
- [x] **Dual Mode Support (Live Gmail vs. Simulated)**
  - [x] Environment flag `GMAIL_MODE=LIVE` or `GMAIL_MODE=SIMULATED`
  - [x] Seed data loader with Pakistan-specific pharmaceutical demo items (Panadol 500mg, Augmentin 625mg, Brufen 400mg, Disprin 300mg) and registered local distributors

---

### Phase 3: Procurement Response Simulator & What-If Engine
- [ ] **Deterministic Scenario Evaluator (`backend/services/procurement.py`)**
  - [ ] Scenario A: Lowest Total Cost algorithm
  - [ ] Scenario B: Fastest Lead Time algorithm
  - [ ] Scenario C: Split-Order combination algorithm
  - [ ] Scenario D: Infeasibility explanation generator
- [ ] **Interactive What-If Engine**
  - [ ] Parameterized endpoint accepting temporary overrides for budget, demand surge, or supplier delays
  - [ ] Instant recalculation preserving calculation transparency

---

### Phase 4: Modern Web Frontend Application
- [ ] **Project Setup & Design System (`frontend/`)**
  - [ ] Next.js / React with curated typography, dark mode, smooth transitions, glassmorphic cards
  - [ ] Responsive navigation (Dashboard, Early-Warning Radar, Quotations & Inbox, Procurement Simulator, Purchase Orders, Audit Log)
- [ ] **Core Views & Components**
  - [ ] **Dashboard:** High-level summary of stock health, active quotation requests, and pending approvals
  - [ ] **Shortage Radar:** Visual gauge displaying stock coverage days, stockout projections, and incoming shipment timelines
  - [ ] **Agent Approval Center:** Modal displaying email draft, recipient list, and explicit "Approve & Send via Gmail" / "Decline" actions
  - [ ] **Quotation Comparison Matrix:** Side-by-side card comparison of supplier offers with missing field warning badges
  - [ ] **Procurement Simulator:** Interactive card deck comparing Cheapest, Fastest, and Split-Order scenarios with What-If sliders
  - [ ] **Purchase Order & Audit View:** Step-by-step PO sign-off and chronological audit log

---

### Phase 5: End-to-End Integration, Evaluation & Submission
- [ ] Full end-to-end user testing (Risk Alert -> Email Approval -> Gmail Send -> Quote Parse -> Simulation -> PO Approval)
- [ ] Execution of 12 reproducible evaluation test scenarios
- [ ] Recording 3-minute demo video showcasing real decision workflow
- [ ] Final security audit (verify zero secrets in git, verify live/simulated labels)
- [ ] Final README and NYLP Hackathon portal submission prior to deadline (19 Oct 2026, 11:59 PM PKT)
