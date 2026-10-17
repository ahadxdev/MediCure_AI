# MediProcure AI — Feature Specifications

> **Scope:** Detailed functional, algorithmic, and interface requirements for all 9 core features.  
> **Audience:** Frontend, Backend, and AI Developers, Hackathon Evaluators.

---

## 1. Feature 1: Shortage Early-Warning Radar

### 1.1 Objective
Continuously monitor inventory levels, demand trends, and supplier lead times to detect stockout risks before they disrupt patient care.

### 1.2 Mathematical Model & Logic
- **Stock Coverage ($C$):**
  $$C = \frac{\text{Usable Stock}}{\text{Average Daily Demand}}$$
- **Stockout Estimation ($T_{\text{stockout}}$):**
  - Without incoming stock: $T = C$
  - With incoming shipments $S_i = (q_i, t_i)$:
    Iterate day-by-day from $t=0$ to $t_{\text{lead\_time}}$ or $t_{\text{horizon}}$.
    $$Stock(t+1) = \max(0, Stock(t) - Demand + \sum_{i: t_i = t+1} q_i)$$
    First day where $Stock(t) = 0$ is flagged as `first_stockout_day`.
- **Risk Classification:**
  - `high_risk`: Stock coverage $\le 3$ days OR stockout occurs before supplier delivery.
  - `warning`: Stockout projected within 7 days, or incoming shipment temporarily prevents stockout but safety buffer is slim.
  - `needs_delivery_data`: Coverage is low ($\le 7$ days) but supplier lead time is unknown.
  - `lower_risk`: Stock covers beyond expected supplier arrival with safe buffer.
  - `review_required`: Zero sales history, negative inputs, or stale data.

### 1.3 Inputs & Outputs
- **Inputs:** `usable_stock`, `avg_daily_demand`, `supplier_lead_time_days`, `incoming_shipments`.
- **Outputs:** `status`, `coverage_days`, `stockout_before_delivery`, `stock_at_delivery`, `first_stockout_day`, `risk_flags`, `assumptions`.

### 1.4 UI Representation
- Radar dial/gauge showing days of stock.
- Color-coded severity badge (Red: High Risk, Amber: Warning, Blue: Needs Info, Green: Safe).
- Expandable card listing calculation assumptions and data quality notices.

---

## 2. Feature 2: Gmail Supplier Quotation Agent

### 2.1 Objective
Automate the time-consuming process of reaching out to suppliers, requesting formal quotes, gathering responses, and extracting structured parameters.

### 2.2 Request Generation Workflow
1. When Shortage Radar detects `high_risk` or `warning`, the agent selects eligible suppliers from the Supplier Directory.
2. The agent generates a professional, standardized email draft containing:
   - Medicine name, strength, dosage form, pack size.
   - Required quantity and delivery location.
   - Desired delivery date.
   - Specific requests for unit price, MOQ, delivery fee, lead time, payment terms, and validity.
3. LangGraph pauses execution (`interrupt`) and presents the draft to the pharmacist for verification.
4. Upon approval, individual emails are dispatched via Gmail API (or clearly marked simulated dispatcher).
5. State records `request_id`, `thread_id`, `message_id`, and timestamps.

### 2.3 Reply Retrieval & Correlation
- Polling service queries Gmail API using thread IDs and reference codes.
- Incoming emails are mapped to the open quotation request.
- Handles duplicate messages and multi-supplier threads cleanly.

### 2.4 Field Extraction & Anomaly Validation
- Raw email body is parsed by `ai_engine/quotes/parser.py` extracting 12 standardized fields.
- Validated by `ai_engine/quotes/validator.py`:
  - Flags prices $\le 0$, negative fees, missing lead times, missing validity.
  - Flags mismatch if quoted quantity is below the supplier's stated MOQ.
  - Sets `review_status` to `"validated"` or `"needs_review"`.

### 2.5 Security & Simulated Mode
- Inbound email content cannot execute instructions (treated as raw text).
- If Google OAuth is unavailable, simulated mode generates realistic dummy replies with explicit `[SIMULATED]` badges.

---

## 3. Feature 3: Procurement Response Simulator

### 3.1 Objective
Evaluate incoming valid quotations and simulate multi-variable purchasing decisions when price, delivery speed, and order limits conflict.

### 3.2 Evaluation Scenarios
1. **Cheapest Feasible Supplier:**
   - Minimizes Total Cost:
     $$\text{Total Cost} = (\text{Unit Price} \times \text{Packs Required}) + \text{Delivery Fee} + \text{Taxes}$$
   - Validates that supplier has sufficient quantity and that order meets MOQ.
2. **Fastest Lead Time Supplier:**
   - Minimizes lead time (days until delivery) to avoid patient stockouts, even if unit price is slightly higher.
3. **Split-Order Strategy:**
   - If Supplier A has the lowest price but limited stock, or Supplier B has faster delivery for emergency stock:
     Simulate splitting the order (e.g. 20 packs expedited from B, 80 packs economical from A).
4. **No Feasible Option:**
   - If all suppliers exceed budget, cannot deliver before stockout, or require MOQs exceeding pharmacy capacity, provide an explicit explanation of why no feasible option exists.

### 3.3 Output Metrics
- Total Procurement Cost (PKR).
- Estimated Arrival Date.
- Stock Coverage Post-Delivery.
- Unmet Shortage Exposure (patient demand missed).

---

## 4. Feature 4: Data Quality & Anomaly Engine

### 4.1 Objective
Ensure procurement decisions are never made on corrupt, incomplete, or fabricated data.

### 4.2 Checks Performed
- **Inventory Freshness:** Flags stock records not updated in $> 14$ days.
- **Demand Validity:** Flags medicines with $< 30$ days of sales history or zero historical sales.
- **Ambiguity Checks:** Flags items lacking explicit strength, dosage form, or pack units (e.g. "Paracetamol" without 500mg or pack count).
- **Supplier Claim Auditing:** Distinguishes verified supplier contracts from unverified email claims.

---

## 5. Feature 5: What-If Simulator

### 5.1 Objective
Allow pharmacists to interactively adjust operational variables and view instant recalculations without altering real production data.

### 5.2 Adjustable Levers
- **Budget Slider:** e.g., max PKR 25,000. Recalculates feasible order quantities.
- **Demand Surge:** e.g., $+20\%$ seasonal flu surge. Recalculates days until stockout.
- **Supplier Delay:** e.g., $+2$ days customs delay. Recalculates residual shortage exposure.
- **Order Quantity:** e.g., bump to 200 packs to unlock volume discount / meet MOQ.

---

## 6. Feature 6: Inventory and Sales Management

### 6.1 Objective
Maintain a lightweight, accurate ledger of stock on hand, incoming shipments, and batch expiries.

### 6.2 Data Model
- Medicine Catalog (generic name, brand name, strength, dosage form, pack size).
- Inventory Batches (batch number, expiry date, usable stock quantity, warehouse location).
- Sales History Records (date, quantity dispensed, unit price).
- Incoming Shipments (PO ID, supplier, quantity, expected delivery date, status).

---

## 7. Feature 7: Supplier Directory

### 7.1 Objective
Maintain verified contact details, product eligibility catalogs, and performance records for licensed distributors.

### 7.2 Directory Attributes
- Company Name, Registration/License Number.
- Primary Sales Representative, Verified Email, Phone Number.
- Product Catalog & Typical Lead Times (days).
- Stated Minimum Order Quantities (MOQ) and Delivery Terms.
- Verification Status (`verified`, `pending_verification`, `unverified`).

---

## 8. Feature 8: Draft Purchase Orders, Human Approval & Audit

### 8.1 Objective
Bridge decision simulation to formal procurement while guaranteeing zero unauthorized actions.

### 8.2 Workflow
1. Pharmacist selects the optimal procurement recommendation (e.g., Fastest, Cheapest, or Custom).
2. System compiles a Draft Purchase Order (PO):
   - Formal PO Number, Date, Pharmacy Details.
   - Selected Supplier and Quoted Reference ID.
   - Line items: Medicine, Strength, Pack count, Unit price, Subtotal, Delivery charge, Grand total.
   - Delivery instructions and required delivery date.
3. System requires explicit two-step approval:
   - Primary Pharmacist Sign-off.
   - Confirmation dialog warning that this constitutes a commercial commitment.
4. Generates a printable/downloadable PDF and records an immutable entry in the Audit Log.

---

## 9. Feature 9: Feedback and Real Outcome Tracking

### 9.1 Objective
Track whether real-world deliveries matched supplier promises, enabling future decision improvements without making false algorithmic learning claims.

### 9.2 Tracked Outcomes
- Actual Delivery Date vs. Quoted Delivery Date (Lead Time Accuracy).
- Actual Invoiced Price vs. Quoted Price.
- Damaged / Short-shipped Quantity.
- User Override Rationale (why a pharmacist chose option B instead of recommended option A).
