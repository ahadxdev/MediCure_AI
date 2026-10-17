# MediProcure AI — Evaluation & Testing Suite

> **Evaluation Standard:** NYLP AI Hackathon 2026  
> **Test Status:** 16/16 Unit Tests Passing (Risk Engine & Quote Parser)  
> **Framework:** Pytest, Pydantic, LangGraph Interrupt Testing

---

## 1. Testing Philosophy & Guardrails

MediProcure AI handles healthcare inventory decisions where mistakes could cause medicine stockouts or wasteful capital lockup. Therefore:
1. **Arithmetic is deterministic:** Every formula is tested with zero tolerance for floating point errors or LLM hallucinations.
2. **Defensive human approval:** Test assertions confirm that outbound emails and PO commitments cannot trigger without explicit human approval.
3. **Robustness on untrusted text:** Parsers are tested against adversarial email formatting, missing fields, and conflicting values.

---

## 2. Controlled Evaluation Scenarios (12 Scenarios)

| Scenario ID | Test Case Name | Input Conditions | Expected System Behavior | Verified In Tests? |
| :--- | :--- | :--- | :--- | :--- |
| **SC-01** | Basic High Stockout Risk | Stock: 15, Demand: 5/day, Lead Time: 6 days | `coverage_days = 3.0`, `stockout_before_delivery = True`, `status = "high_risk"`. Triggers quote draft. | Yes (`test_basic_stockout_risk`) |
| **SC-02** | Safe Delivery Before Stockout | Stock: 50, Demand: 5/day, Lead Time: 3 days | `coverage_days = 10.0`, `stock_at_delivery = 35.0`, `status = "lower_risk"`. No urgent draft required. | Yes (`test_delivery_before_stockout`) |
| **SC-03** | Incoming Stock Mitigates Risk | Stock: 10, Demand: 5/day, Lead Time: 6 days, Incoming: 20 units at Day 1 | `stockout_before_delivery = False`, `stock_at_delivery = 0.0`, `status = "warning"`. | Yes (`test_incoming_stock_arrives_before_stockout`) |
| **SC-04** | Incoming Stock Arrives Too Late | Stock: 10, Demand: 5/day, Lead Time: 6 days, Incoming: 20 units at Day 4 | Stock hits 0 on Day 2. `stockout_before_delivery = True`, `first_stockout_day = 2.0`. | Yes (`test_incoming_stock_arrives_too_late`) |
| **SC-05** | Zero Demand Edge Case | Stock: 20, Demand: 0/day | Flag: `"Demand is zero; verify history before relying on this assessment"`, `status = "review_required"`. | Yes (`test_zero_demand_handling`) |
| **SC-06** | Negative Input Prevention | Stock: -5, Demand: 5/day | Returns error flag: `"Stock and demand cannot be negative."`, status `unknown`. | Yes (`test_negative_stock_or_demand`) |
| **SC-07** | Missing Delivery Lead Time | Stock: 10, Demand: 5/day, Lead Time: None | `coverage_days = 2.0`, `status = "needs_delivery_data"`. Prompts for supplier lead times. | Yes (`test_missing_lead_time_gives_provisional_coverage`) |
| **SC-08** | Perfect Quotation Parse | Clean supplier reply with 12 fields | Extracts all fields, `currency = "PKR"`, `delivery_days = 2.0`, `review_status = "validated"`. | Yes (`test_parse_complete_quote_email`) |
| **SC-09** | Quoted Quantity Below MOQ | Supplier quote: Quantity 50, MOQ 100 | Adds warning: `quoted_quantity_below_moq`, sets `review_status = "needs_review"`. | Yes (`test_validate_quote_moq_warning`) |
| **SC-10** | Unstated Validity / Lead Time | Supplier quote missing validity date | Adds warning: `validity_not_provided`, marks `needs_review`. | Yes (`test_validate_quote_missing_fields`) |
| **SC-11** | Human Approval Denial | Agent drafts email, user enters "no" | Interrupt receives `approved: False`, transitions to `declined`, email status `not_sent`. | Yes (`run_agent_demo.py` & graph) |
| **SC-12** | Live vs Simulated Fallback | No `credentials.json` found | Gracefully enters `Simulated Mode` with explicit `[SIMULATED]` badges on drafts & quotes. | In Progress |

---

## 3. Baseline Comparison: Simple Reorder Rule vs. MediProcure AI

To prove quantifiable value for hackathon judging, we compare MediProcure AI against standard pharmacy software behavior:

| Dimension | Standard Pharmacy Software (Baseline) | MediProcure AI Decision-Support |
| :--- | :--- | :--- |
| **Stockout Trigger** | Fixed static threshold (e.g., Reorder if stock $< 20$) | Dynamic coverage calculation ($Stock / DailyDemand$) factoring real sales velocity |
| **Supplier Lead Time Awareness** | None (assumes instant delivery) | Compares delivery lead time directly against days until stockout |
| **Incoming Shipments** | Either ignored or lumped into current stock | Simulates timeline to detect stockout gaps occurring before shipment arrival |
| **Quotation Sourcing** | Manual phone calls or typing individual emails | Automated drafting, multi-recipient dispatch via Gmail, and parsing |
| **Scenario Optimization** | Pharmacist guesses best trade-off in their head | Deterministic comparison of Fastest vs. Cheapest vs. Split-order feasibility |
| **Safety & Audit** | No structured log of why a supplier was chosen | Immutable audit trail of risk scores, quotes, approvals, and PO generation |

---

## 4. Current Test Suite Results

Run on: Python 3.14 / pytest-8.4.2
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
- Total tests executed: 24
- Pass rate: **100% (24/24)**
- Automated Coverage:
  - 13 unit tests on pure deterministic shortage risk math (`tests/unit/test_shortage_risk.py`)
  - 3 unit tests on quote extraction & anomaly validation (`tests/unit/test_quote_parser.py`)
  - 8 integration/API unit tests on FastAPI startup, database sessions, seed catalog, inventory calculations, and REST shortage-risk evaluations (`tests/unit/test_backend_api.py`)

