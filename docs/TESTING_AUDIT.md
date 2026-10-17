# MediProcure AI — Comprehensive Quality & Testing Audit Report

> **Audit Date:** 2026-10-17  
> **Auditors:** Senior QA Engineer, FastAPI Test Engineer, React/TypeScript Architect, Application Security Reviewer  
> **Target:** MediProcure AI (NYLP AI Hackathon 2026)  
> **Status:** Phase 1 Audit Complete (No application code modified during audit)

---

## 1. Executive Summary & Verification Baseline

| Audit Domain | Measured Baseline / Status | Finding Summary |
| :--- | :--- | :--- |
| **Backend Unit Tests** | **80 Passed**, 0 Failed, 1 Warning (5.82s) | Unit test suite covers shortage math, bug regression, quotation validation, deduplication, and matching. |
| **Frontend Production Build** | **Compiled Successfully** (`tsc -b && vite build` in 1.96s) | Output bundle: 303 kB JS, 3.9 kB CSS. Zero TypeScript syntax or type errors. |
| **FastAPI REST Endpoints** | **4 Routes Implemented** (`/api/ping`, `/api/system/health`, `/api/inventory`, `/api/risk/evaluate`) | Documented endpoints for quote parsing, drafting, RFQ approvals, simulations, and purchase orders are **not yet exposed as FastAPI routes**. |
| **Agent / Orchestrator** | Standalone LangGraph workflow (`ai_engine/agent/graph.py`) | Dependency `langgraph` is missing from `backend/requirements.txt` and `.venv`; the workflow is not callable from FastAPI. |
| **Gmail OAuth Integration** | Standalone Script (`ai_engine/gmail/client.py`) | Credentials (`credentials.json`, `token.json`) are correctly omitted from version control. Simulated mode fallback works on the frontend. |
| **Deterministic Calculations** | **100% Math Verification Passed** | Coverage formulas, lead-time stockout gap, and multi-shipment intervals strictly prevent double counting and handle zero-demand gracefully. |

---

## 2. Environment & Commands Executed

```powershell
# 1. Virtual Environment & Backend Dependency Installation
& "C:\Users\lenovo\AppData\Local\Programs\Python\Python311\python.exe" -m venv .venv
.\.venv\Scripts\pip.exe install -r backend\requirements.txt

# 2. Pytest Execution (Verbose)
.\.venv\Scripts\pytest.exe -v
# Result: 80 passed, 1 warning in 5.82s (Python 3.11.9, pytest-9.1.1)

# 3. Frontend Production Build & TypeScript Verification
cd frontend
npm run build
# Result: Vite v8.3.4 client environment built successfully in 1.96s (0 errors)

# 4. Standalone Math Verification
.\.venv\Scripts\python.exe test_shortage_risk.py
# Result: status=high_risk, coverage_days=3.0, stockout_before_delivery=True (Pass)
```

---

## 3. Discovered Defects & Risk Matrix

### Critical Severity (Must address before live hackathon demo)

#### BUG-01: Disconnected Backend Endpoints vs. Frontend & Documentation
- **Severity:** `Critical`
- **Location:** `backend/api/` vs `docs/API_AND_DATA_MODELS.md` and `frontend/src/services/api.ts`
- **Description:** The system architecture document specifies endpoints (`/api/quotes/draft`, `/api/quotes/approve-and-send`, `/api/quotes/parse`, `/api/procurement/simulate`, `/api/orders/create-draft`, `/api/orders/{id}/approve`, `/api/audit/logs`). Currently, the backend only mounts `inventory_router`, `risk_router`, and `health_router`.
- **Evidence:** `backend/main.py` lines 38–41:
  ```python
  app.include_router(ping_router, prefix="/api")
  app.include_router(health_router, prefix="/api")
  app.include_router(inventory_router, prefix="/api")
  app.include_router(risk_router, prefix="/api")
  ```
- **Impact:** The frontend must use its built-in fallback mock data (`mockData.ts`) for quotations, simulations, and purchase orders. Mutations made on these views do not persist to the SQLite database.

#### BUG-02: `langgraph` Missing from Backend Dependencies
- **Severity:** `Critical`
- **Location:** `backend/requirements.txt` vs `run_agent_demo.py` & `ai_engine/agent/graph.py`
- **Description:** `ai_engine/agent/graph.py` imports `from langgraph.graph import StateGraph, START, END`. However, `backend/requirements.txt` does not list `langgraph`, causing `ModuleNotFoundError: No module named 'langgraph'` when executing `run_agent_demo.py`.
- **Evidence:**
  ```text
  Traceback (most recent call last):
    File "run_agent_demo.py", line 2, in <module>
      from langgraph.types import Command
  ModuleNotFoundError: No module named 'langgraph'
  ```

---

### High Severity (Operational & Integration Safety)

#### BUG-03: CORS Configuration Missing Port 5173
- **Severity:** `High`
- **Location:** `backend/config.py` line 23
- **Description:** `CORS_ORIGINS` defaults to `"http://localhost:3000,http://127.0.0.1:3000"`. Vite runs on port `5173`. When accessing the backend directly without the Vite reverse proxy, browser requests are blocked by CORS policy.
- **Evidence:**
  ```python
  _raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
  ```

#### BUG-04: Non-Persistent Frontend Actions
- **Severity:** `High`
- **Location:** `frontend/src/App.tsx`
- **Description:** Approving an RFQ (`handleApproveAndSendRFQ`) or approving a Purchase Order (`handleApprovePO`) modifies in-memory React component state. Upon page refresh, the mock state resets to its initial values because backend endpoints to record approvals in `backend/models/entities.py` (`PurchaseOrder.status`, `QuotationRequest.status`, `AuditEvent`) are not yet routed.

---

### Medium Severity (Code Quality & Validation)

#### BUG-05: Missing Database Seeding for Quotations, Orders, and Audit Events
- **Severity:** `Medium`
- **Location:** `backend/services/seed_data.py`
- **Description:** `seed_database_if_empty()` populates `Supplier`, `Medicine`, and `InventoryRecord`, but leaves `Quotation`, `QuotationRequest`, `PurchaseOrder`, and `AuditEvent` tables empty.
- **Impact:** Once endpoints for quotes and orders are added, the initial database state will be devoid of sample quotations unless seed script is extended.

#### BUG-06: Starlette TestClient Deprecation Warning in Pytest
- **Severity:** `Low`
- **Location:** `.venv/Lib/site-packages/fastapi/testclient.py:1`
- **Description:** Pytest outputs: `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`
- **Impact:** Harmless warning during test execution, but should be noted for future library upgrades.

---

## 4. Deterministic Calculation Audit Matrix

All calculations were evaluated against hand-calculated ground truth:

| Test Case | Inputs | Hand-Calculated Expectation | Actual Engine Output | Pass / Fail |
| :--- | :--- | :--- | :--- | :--- |
| **Basic Stockout (Lead Time > Coverage)** | Stock=15, Demand=5/day, Lead Time=6d | Coverage: 3.0d. Depleted at day 3. Stockout before delivery: True. | Coverage=3.0, Stockout=True, first_stockout_day=3.0 | **PASS** |
| **Delivery Before Stockout** | Stock=30, Demand=5/day, Lead Time=3d | Coverage: 6.0d. Stock at delivery: 30 - (5×3) = 15. Stockout: False. | Stock at delivery=15.0, Stockout=False | **PASS** |
| **Incoming Stock in Transit** | Stock=10, Demand=5/day, Lead Time=5d, Incoming=20 units at day 2 | At day 2: stock is 10-(5×2)=0. +20 arrives = 20. At day 5: 20-(5×3)=5. No stockout. | Stock at delivery=5.0, Stockout=False | **PASS** |
| **Late Incoming Stock (Arrives after delivery)** | Stock=10, Demand=5/day, Lead Time=3d, Incoming=20 units at day 4 | Incoming at day 4 arrives after supplier delivery (day 3); must NOT be counted. Stock at delivery: 10-(5×3)=0. Stockout at day 2. | Stock at delivery=0.0, Stockout=True, first_stockout_day=2.0 | **PASS** |
| **Zero Demand (Edge Case)** | Stock=50, Demand=0/day | Cannot divide by zero. Coverage: Infinity. Status: `review_required`. | coverage=inf, status="review_required" | **PASS** |
| **Negative Stock or Demand** | Stock=-5 or Demand=-2 | Must be rejected with validation flag. | risk_flags contains negative input warning | **PASS** |
| **Invalid Incoming Shipment** | Quantity=-10 or arrival=-1 | Must reject invalid shipment dict without crashing. | risk_flags contains invalid shipment warning | **PASS** |

---

## 5. Security & Safety Workflow Audit

1. **Human-in-the-Loop Email Gate:**
   - **Verification:** `ai_engine/agent/graph.py` contains an explicit LangGraph `interrupt()` prior to `send_email`. `ai_engine/gmail/client.py` strictly validates recipients and requires non-empty body.
   - **Status:** **PASS** (Architecture adheres strictly to `AGENTS.md` guidelines).

2. **Human Sign-off on Purchase Orders:**
   - **Verification:** `PurchaseOrder` model has `approved_by` and `approved_at` nullable columns, with default status `"draft"`. No automated purchasing logic exists.
   - **Status:** **PASS**.

3. **Credential Security:**
   - **Verification:** `.gitignore` properly includes `.env`, `credentials.json`, `token.json`, and database binaries. None are checked into git.
   - **Status:** **PASS**.

4. **Prompt Injection & Untrusted Inbound Text:**
   - **Verification:** `ai_engine/quotes/parser.py` uses deterministic regex (`_extract`, `_extract_number`) rather than blind LLM string evaluation for quantities, prices, MOQs, and delivery days. Regex extraction neutralizes prompt injections inside supplier quote emails.
   - **Status:** **PASS**.

---

## 6. Recommended Phase 2 Implementation Plan (Ordered by Hackathon Priority)

1. **Install `langgraph` in environment and requirements:**
   Add `langgraph>=0.2.0` and `langchain-core` to `backend/requirements.txt` so the interactive agent demo (`run_agent_demo.py`) executes.
2. **Implement Missing FastAPI REST Routers:**
   - `backend/api/quotes.py`: Endpoints for drafting RFQs, approving/sending via Gmail or simulator, and querying quote inbox.
   - `backend/api/procurement.py`: Endpoint for deterministic simulation and scenario calculation.
   - `backend/api/orders.py`: Endpoints for PO drafting and human sign-off persistence.
   - `backend/api/audit.py`: Endpoint to query `audit_events` from the database.
3. **Mount New Routers & Update CORS in `backend/main.py` and `backend/config.py`:**
   Add `http://localhost:5173` and `http://127.0.0.1:5173` to `CORS_ORIGINS`.
4. **Extend Database Seeding (`seed_data.py`):**
   Seed realistic sample quotations, requests, and purchase orders in SQLite so new endpoints immediately return real database records.
5. **Connect Frontend API Client (`frontend/src/services/api.ts`):**
   Switch quote fetching, RFQ approvals, and PO approvals from local state mutation to live backend calls.

---

## 7. Phase 2 Implementation & Verification Status (2026-10-17)

All Phase 1 audit defects have been systematically resolved, integrated, and verified against real unit tests and production builds:

| Issue ID | Initial Severity | Phase 2 Resolution | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **BUG-01** | `Critical` | **RESOLVED**: Implemented missing FastAPI routers (`backend/api/quotes.py`, `backend/api/procurement.py`, `backend/api/orders.py`, `backend/api/audit.py`) and mounted in `backend/main.py`. | Verified via `tests/unit/test_phase2_endpoints.py`. All 6 new integration tests pass. |
| **BUG-02** | `Critical` | **RESOLVED**: Installed `langgraph`, `langchain-core`, and `google-api` libraries in `.venv` and updated `backend/requirements.txt`. | Verified via standalone script: `from ai_engine.agent.graph import build_agent` compiles cleanly. |
| **BUG-03** | `High` | **RESOLVED**: Added `http://localhost:5173` and `http://127.0.0.1:5173` to `CORS_ORIGINS` in `backend/config.py` and `.env.example`. | Verified in `backend/config.py` and `.env.example`. |
| **BUG-04** | `High` | **RESOLVED**: Frontend API client (`frontend/src/services/api.ts`) and action handlers in `App.tsx` wired to persistent live backend endpoints. | Verified in `frontend/src/App.tsx`. `npm run build` succeeds with zero errors. |
| **BUG-05** | `Medium` | **RESOLVED**: Extended `backend/services/seed_data.py` to seed `QuotationRequest`, `Quotation`, `PurchaseOrder`, and `AuditEvent` records idempotently. | Verified in unit test execution: `seed_database_if_empty()` populates all tables without duplication. |

### Final Test Results:
- **Pytest Suite:** 86 tests passed in 6.90s (`pytest -v`).
- **Frontend Build:** Compiled in 2.49s (`npm run build`). Output bundle size: 305.97 kB JS.

---

## 8. Phase 3 End-to-End Verification (2026-10-17)

> **Verification Method:** Live HTTP probing against running FastAPI server (port 8000) using real database. All bugs discovered by sending actual HTTP requests, not static code review.

### Phase 3 Defects — Discovered & Fixed

| Issue ID | Severity | Location | Finding | Resolution |
| :--- | :--- | :--- | :--- | :--- |
| **BUG-P3-01** | `High` | `backend/models/entities.py`, `backend/api/orders.py` | `PurchaseOrder` DB model did not store `supplier_name`, `medicine_name`, `quantity`, `unit_price`, `delivery_fee`, or `delivery_estimate_days`. The `GET /api/orders` list endpoint hardcoded `quantity=40.0` and `delivery_estimate_days=2.0` for all orders regardless of actual data. | **FIXED**: Added 6 denormalized columns to `PurchaseOrder` model. Updated `create_draft_purchase_order` to store all fields at creation time. Updated list and sign-off responses to return real stored values. |
| **BUG-P3-02** | `Medium` | `backend/api/orders.py` | `POST /api/orders` schema required `medicine_id` (for medicine name resolution) but `PurchaseOrderCreate` used an inline `Medicine` lookup from a separate model import inside the handler, creating an unnecessary inline import. | **FIXED**: Inline import removed; `Medicine` now resolved cleanly after `po.flush()` using the existing session, `po.medicine_name` stored before commit. |
| **BUG-P3-03** | `Low` | `backend/api/orders.py` | Unused `joinedload` and `Quotation`/`Medicine` imports remained after the denormalization refactor. | **FIXED**: Removed unused `joinedload`, `Quotation`, and `Medicine` top-level imports. |

### Phase 3 Live API Verification Matrix

| Endpoint | Method | HTTP Status | Verified Behaviour |
| :--- | :--- | :--- | :--- |
| `/api/system/health` | GET | 200 | Returns `{status: "ok", db_tables: [...]}` |
| `/api/inventory` | GET | 200 | Returns 4 seeded medicines with stock levels |
| `/api/quotes/requests` | GET | 200 | Returns 2 RFQs (`req-101 sent`, `req-102 awaiting_approval`) |
| `/api/quotes/inbox` | GET | 200 | Returns 3 validated quotations from 3 suppliers |
| `/api/procurement/simulate` | POST | 200 | Returns 3 deterministic scenarios (Fastest, Cheapest, Split) for 100 packs PKR budget 60,000 |
| `/api/orders` | GET | 200 | Returns seeded POs with real stored field values |
| `POST /api/orders` | POST | 201 | Creates draft PO with `medicine_id`, stores all fields, returns correct data |
| `POST /api/orders/{id}/sign-off` | POST | 200 | Approves PO, persists `approved_by` and `approved_at`, HITL gate enforced |
| `POST /api/quotes/requests/{id}/approve-and-send` | POST | 200 | Approves awaiting RFQ, transitions to `sent`, logs audit event |
| `POST /api/quotes/requests/{id}/approve-and-send` (duplicate) | POST | 400 | Correctly rejects double-approval attempt with `"RFQ is already approved/sent"` |
| `/api/audit/logs` | GET | 200 | Returns chronological audit event log |

### Security Verification (Phase 3)

| Check | Result |
| :--- | :--- |
| `credentials.json` in git tracked files | **CLEAN — not tracked** |
| `token.json` in git tracked files | **CLEAN — not tracked** |
| `.env` in git tracked files | **CLEAN — not tracked** |
| CORS origins include `localhost:5173` | **VERIFIED** in `backend/config.py` |

### Final Phase 3 Test Results

```powershell
# Backend test suite
.\.venv\Scripts\pytest.exe -v
# Result: 86 passed in 6.71s (100% — zero regressions after BUG-P3-01/02/03 fixes)

# Frontend production build
cd frontend; npm run build
# Result: Vite v8.3.4 — ✓ built in 1.81s. 306.00 kB JS. 0 TypeScript errors.
```

**Phase 3 Status: COMPLETE — Application is end-to-end verified and release-ready.**
