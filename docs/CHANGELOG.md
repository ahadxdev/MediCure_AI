# MediProcure AI — Implementation Notes & Changelog

All implementation milestones and architecture updates are logged here chronologically.

---

## [Milestone 2.1] - Phase 2 Backend Scaffolding, Relational Entities, Inventory & Risk Endpoints
**Date:** 2026-10-17  
**Status:** Completed & Verified (24/24 Tests Passing)

### 1. Goal
Establish the foundational FastAPI application, relational database models (SQLAlchemy 2.x), initial database connectivity with SQLite local fallback and PostgreSQL/Supabase readiness, deterministic shortage-risk calculation integration, inventory endpoint, and automated test suite.

### 2. Files Changed & Added
- `pytest.ini`: Configured test discovery (`testpaths = tests`, `pythonpath = .`) to allow zero-configuration test execution via both `pytest` and `python -m pytest`.
- `.env.example`: Provided environment variables for `APP_ENV`, `DATABASE_URL`, `GMAIL_MODE`, and `CORS_ORIGINS`.
- `backend/requirements.txt`: Specified backend dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `pydantic`, `python-dotenv`, `httpx`, `pytest`).
- `backend/config.py`: Centralized configuration loading from environment variables.
- `backend/database.py`: SQLAlchemy 2.0 engine, `SessionLocal`, `Base` declarative base, `get_db` generator dependency, and `init_db()` table initializer.
- `backend/models/entities.py` & `backend/models/__init__.py`: Normalized relational entities matching `docs/API_AND_DATA_MODELS.md`:
  - `Medicine` (id, name, generic_name, strength, dosage_form, pack_size, created_at)
  - `InventoryRecord` (id, medicine_id, usable_stock, reorder_level, last_counted_at)
  - `SalesRecord` (id, medicine_id, sale_date, quantity_dispensed)
  - `Supplier` (id, name, email, phone, address, is_verified, default_lead_time_days)
  - `QuotationRequest` (id, medicine_id, required_quantity, required_by_date, delivery_location, status, created_at)
  - `Quotation` (id, request_id, supplier_id, raw_email_body, price, currency, price_unit, quoted_quantity, minimum_order_quantity, delivery_days, delivery_fee, payment_terms, valid_until, review_status, warning_flags, created_at)
  - `PurchaseOrder` (id, quotation_id, po_number, total_amount, status, approved_by, approved_at, created_at)
  - `AuditEvent` (id, entity_type, entity_id, event_type, actor, timestamp, payload)
- `backend/schemas/risk.py`: Pydantic v2 validation models (`IncomingShipment`, `RiskAssessmentRequest`, `RiskAssessmentResponse`).
- `backend/schemas/inventory.py`: Pydantic v2 models (`MedicineCreate`, `InventoryItemResponse`, `InventoryListResponse`).
- `backend/services/risk_service.py`: Bridge service invoking the deterministic `assess_shortage_risk()` function from `ai_engine.risk.shortage_risk`.
- `backend/services/seed_data.py`: Seed data loader populating Pakistan-specific demo items (Panadol 500mg, Augmentin 625mg, Brufen 400mg, Disprin 300mg) and verified local distributors.
- `backend/api/health.py`: `GET /api/health` (ping) and `GET /api/system/health` (database probe, Gmail mode indicator).
- `backend/api/inventory.py`: `GET /api/inventory` (catalog stock, sales velocity, coverage days, and risk status), `POST /api/inventory` (add new item), `POST /api/inventory/seed` (trigger demo catalog seed).
- `backend/api/risk.py`: `POST /api/risk/evaluate` (arbitrary payload assessment) and `GET /api/risk/medicines/{id}` (live database assessment).
- `backend/main.py`: Main FastAPI application configured with `lifespan` handler, CORS middleware, and API router inclusions.
- `tests/unit/test_backend_api.py`: 8 unit and integration tests verifying health checks, inventory listing, medicine creation, and shortage risk evaluation edge cases.
- Documentation updates: `README.md`, `docs/EVALUATION_AND_TESTING.md`, `docs/PHASES_AND_ROADMAP.md`.

### 3. Verification & Actual Test Results
Command executed:
```powershell
pytest
```
Result:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-8.4.2, pluggy-1.6.0
rootdir: C:\Users\tahaj\OneDrive - FAST National University\Projects\AI\MediCure NYLP Hackathon\MediCure_AI
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.13.0
collected 24 items

tests\unit\test_backend_api.py ........                                  [ 33%]
tests\unit\test_quote_parser.py ...                                      [ 45%]
tests\unit\test_shortage_risk.py .............                           [100%]

======================== 24 passed, 1 warning in 2.28s ========================
```

### 4. Remaining & Outstanding Work (Next Milestones)
- **Milestone 2.2:** Connect LangGraph quotation agent with backend REST endpoints (`POST /api/quotes/draft`, `POST /api/quotes/approve-and-send`, `GET /api/quotes/inbox`).
- **Milestone 2.3:** Add immutable audit log service and `GET /api/audit` endpoint.
- **Milestone 3.1:** Implement the deterministic Procurement Response Simulator (`backend/services/procurement.py`) and What-If endpoints.
