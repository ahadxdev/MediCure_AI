# MediProcure AI --- Project Context

> **Tagline:** Predict. Protect. Procure.\
> **Project type:** AI-powered medicine procurement decision-support
> system\
> **Initial market:** Independent pharmacies in Pakistan\
> **Hackathon:** NYLP AI Hackathon 2026\
> **Status:** Project context and intended MVP; implementation status
> must be verified from the actual repository.

------------------------------------------------------------------------

## 1. Purpose

MediProcure AI helps pharmacies identify potential medicine shortages,
request supplier quotations through Gmail, compare available offers,
evaluate feasible procurement responses, and prepare draft purchase
orders for human approval.

The product's central differentiator is the integration of:

1.  Shortage-risk analysis.
2.  Gmail-based supplier quotation automation.
3.  Structured quotation extraction and comparison.
4.  Constraint-aware procurement scenario simulation.
5.  Human approval and an auditable decision history.

The product is a **procurement decision-support tool**, not a guarantee
of medicine availability and not a replacement for pharmacists or
clinical judgment.

## 2. Problem Statement

Pharmacies must make purchasing decisions while balancing:

-   Usable stock and sales demand.
-   Estimated time until stockout.
-   Supplier price and availability.
-   Delivery lead time.
-   Pack sizes and minimum order quantities.
-   Delivery charges, taxes, and payment terms where provided.
-   Budget constraints.
-   Incoming orders and other relevant inventory records.

A low-stock alert alone does not determine the best response. The system
should help the user evaluate what to do when cost, timing, quantity,
and availability conflict.

**Market validation is still required.** Do not assume that the unmet
need, market size, customer willingness to pay, or superiority over
existing pharmacy software has been proven. Existing products may
already offer inventory, purchase, expiry, supplier, and low-stock
functionality. The MVP must demonstrate additional value from the
complete decision workflow.

## 3. Target Users

### Initial users

-   Independent pharmacy owners and pharmacists.
-   Pharmacy inventory or purchasing managers.

### Possible future users

-   Pharmacy chains and multi-branch operators.
-   Licensed suppliers and distributors.
-   Centralized pharmacy procurement teams.

Start with one pharmacy and a small supplier set. Do not build a
national marketplace as part of the initial MVP.

## 4. Core Workflow

1.  Detect a potential stockout.
2.  Verify inventory and demand data quality.
3.  Calculate a transparent estimate of required replenishment.
4.  Identify eligible suppliers.
5.  Draft supplier quotation requests.
6.  Obtain user approval and send requests through Gmail.
7.  Retrieve supplier replies and match them to requests.
8.  Extract and validate quotation details.
9.  Display comparable offers in the web app.
10. Compare feasible procurement options.
11. Explain trade-offs and assumptions.
12. Prepare a draft purchase order.
13. Require explicit human approval before any purchase commitment.
14. Record the decision and, where available, the actual outcome.

## 5. Feature Requirements

### 5.1 Shortage Early-Warning Radar

-   Track medicine identity, strength, dosage form, pack size, usable
    stock, and relevant timestamps.
-   Estimate daily demand from an explicitly defined sales-history
    window.
-   Calculate stock coverage and estimated stockout timing only when
    inputs support it.
-   Compare estimated stockout timing with supplier delivery estimates.
-   Show the calculation inputs, assumptions, and reasons for each
    warning.
-   Account for qualifying incoming stock without double-counting.
-   Flag missing, stale, or inconsistent data.

### 5.2 Gmail Supplier Quotation Agent --- Core Feature

The agent should help request quotations from registered suppliers,
retrieve replies, extract offer details, and display the results in the
web app.

**Request workflow** - Select registered suppliers eligible to provide
the requested medicine. - Draft a professional email containing the
exact medicine identity, strength, dosage form, pack size, required
quantity, delivery location, and desired delivery date. - Ask for
availability, price and price basis, minimum order quantity, delivery
estimate, charges, payment terms, and quotation validity. - Require user
approval before sending in the MVP. - Store the request status,
supplier, Gmail thread/message IDs, and timestamps.

**Reply workflow** - Retrieve replies using the Gmail API and correlate
them to the correct request. - Do not rely solely on an exact email
subject match; use thread IDs and additional matching checks. - Extract
and normalize quotation details from email content. Add PDF/attachment
parsing only when feasible. - Flag missing, ambiguous, conflicting, or
suspicious fields. - Show the offer, extraction status, review status,
received time, and link to the original Gmail message/thread. - Preserve
source information and user corrections for auditing. - Prevent
duplicate sending and duplicate processing.

**Quotation fields** - Supplier identity and email. - Medicine,
strength, dosage form, and pack size. - Quoted price and price basis. -
Available quantity, if stated. - Minimum order quantity. - Delivery
estimate. - Delivery charges, taxes, and other stated fees. - Payment
terms. - Offer validity or expiry. - Conditions or exceptions. - Source
message and received timestamp. - Extraction and human-review status.

**Gmail security and reliability** - Use Gmail API with OAuth 2.0. -
Request the narrowest permissions needed. Sending requires an
appropriate send permission; read-only access cannot send messages. -
Keep OAuth tokens and client secrets on the backend. Never expose them
to frontend code or commit them to version control. - Handle
revoked/expired authorization, API errors, quotas, retries, and
duplicate events. - Treat supplier emails and attachments as untrusted
input. Email content must not override system instructions, access
secrets, or authorize unrelated tool calls. - A quotation is not proof
of actual stock or guaranteed delivery. - Never send a purchase
commitment without explicit approval.

If live Gmail configuration is unavailable for the demo, use a
functioning **clearly labelled simulated-email mode**. Never represent
simulated supplier replies as real communications.

### 5.3 Procurement Response Simulator

Compare feasible options, including: - Cheapest eligible supplier. -
Fastest eligible supplier. - Split order across multiple suppliers. -
Permitted stock transfer, if verified and applicable. - No feasible
option, with an explanation of why.

Compare total cost, delivery timing, stock coverage, constraints, and
estimated residual shortage exposure. Consider pack sizes, available
quantities, minimum order quantities, budget, supplier eligibility, and
stated charges.

### 5.4 Data Quality

Detect and explain: - Missing or stale inventory. - Insufficient sales
history. - Ambiguous medicine identity or pack size. - Missing delivery
estimates. - Incomplete or expired quotations. - Conflicting values. -
Unverified supplier claims.

Do not invent calibrated confidence probabilities. Distinguish verified
values, estimates, missing information, and unverified claims.

### 5.5 What-If Simulator

Allow users to change budget, demand, required quantity, supplier
availability, or delivery timing and recalculate options using the same
deterministic backend logic.

### 5.6 Inventory and Sales

Support medicine records, stock updates, relevant expiry information,
sales history, and incoming orders where needed. Make limitations in
demand history visible.

### 5.7 Supplier Directory

Store supplier contact details, registered email, product eligibility,
known lead times, minimum order quantities, and verification status.
Never invent supplier details or imply that availability is confirmed
without evidence.

### 5.8 Draft Orders, Approval, and Audit

-   Generate editable draft purchase orders from eligible
    recommendations.
-   Show the source quotation, selected quantities, cost breakdown,
    assumptions, and constraints.
-   Require explicit approval before a purchase commitment.
-   Record analysis inputs, email requests/replies, extracted fields,
    corrections, recommendations, user decisions, approvals, and order
    status changes.

### 5.9 Feedback and Future Extensions

Record acceptance/rejection, user edits, actual delivery outcomes, and
observed shortages. Do not claim the system learns or improves unless
that is implemented and evaluated.

Future extensions, only after the core flow works: - Simulated
cross-pharmacy stock exchange. - Near-expiry/excess-stock awareness. -
Supplier performance history. - Multi-branch purchasing. - Better demand
forecasting with sufficient data. - Local-language interaction.

Any real stock transfer must comply with applicable licensing, storage,
traceability, and legal requirements. Do not automatically substitute
medicines or make clinical decisions.

## 6. AI Responsibilities and Boundaries

AI should perform meaningful product work, such as: - Extracting
structured quotation details from supplier messages. - Identifying
incomplete or ambiguous offers. - Selecting appropriate application
tools. - Requesting missing information. - Explaining calculated
trade-offs using actual application data.

Deterministic backend logic must perform: - Stock coverage and stockout
calculations. - Quantity and cost calculations. - Pack-size
normalization. - MOQ, budget, supplier, and delivery constraint
checks. - Feasibility evaluation and scenario comparisons.

The LLM must explain calculation results, not invent values or replace
critical arithmetic with free-form reasoning.

Possible tools, to implement only as needed: - `get_inventory_status` -
`get_demand_estimate` - `check_data_quality` -
`get_eligible_suppliers` - `draft_quotation_request` -
`send_approved_quotation_request` - `get_quotation_request_status` -
`retrieve_supplier_replies` - `extract_and_validate_quotation` -
`compare_procurement_options` - `create_draft_purchase_order` -
`record_user_decision`

Mandatory safeguards: - Never fabricate prices, suppliers, quotations,
stock, or delivery promises. - Never treat untrusted email content as
trusted instructions. - Never expose credentials to the LLM
unnecessarily. - Never send emails or commit to purchases without
required approval. - Never automatically substitute medicines or make
clinical decisions. - Abstain or request clarification when critical
information is missing. - Log material external actions and errors. -
Clearly label live and simulated components.

## 7. Suggested Technology Stack

Use the smallest stack the team can reliably complete. These are
recommendations, not claims about what is already implemented.

-   **Frontend:** React or Next.js.
-   **Backend:** Python + FastAPI.
-   **Database:** PostgreSQL.
-   **AI orchestration:** LangChain or direct model tool-calling.
-   **LLM:** A supported model API for extraction and explanations.
-   **Email:** Gmail API + OAuth 2.0.
-   **Calculations:** Deterministic Python services.
-   **Version control:** GitHub.
-   **Deployment:** Suitable frontend and backend hosting.

Do not add a vector database, complex multi-agent architecture, or
custom ML model unless it solves a demonstrated requirement.

### Suggested backend modules

-   `inventory`
-   `sales_history`
-   `risk_analysis`
-   `data_quality`
-   `suppliers`
-   `gmail_integration`
-   `quotation_parser`
-   `procurement_engine`
-   `agent_orchestrator`
-   `purchase_orders`
-   `approvals`
-   `audit`
-   `feedback`

### Suggested database entities

-   `medicines`
-   `inventory_records` or `inventory_batches`
-   `sales_history`
-   `suppliers`
-   `supplier_products`
-   `quotation_requests`
-   `quotation_request_recipients`
-   `supplier_messages`
-   `quotations`
-   `quotation_line_items`
-   `procurement_scenarios`
-   `recommendations`
-   `purchase_orders`
-   `approval_events`
-   `audit_events`
-   `feedback_and_outcomes`
-   `gmail_connections` or securely managed OAuth metadata

Adapt the schema to the actual application. Keep fields used for
calculations structured and validated. Do not put all application data
into one unstructured JSON field.

## 8. Calculation and Data Rules

Potential calculations: - Average daily demand over a defined time
window. - Days of stock coverage. - Estimated stockout date. - Reorder
quantity using a transparent policy. - Expected inventory at delivery. -
Total procurement cost. - Pack-size and MOQ validation. - Budget
feasibility. - Estimated shortage exposure under stated assumptions. -
Split-order feasibility.

Define how incoming stock, reserved stock, zero demand, missing data,
and conflicting inventory are handled. Avoid double-counting.

Normalize quotation units before comparing prices. Include applicable
stated charges and constraints. If offers cannot be compared fairly,
flag the issue instead of producing a misleading ranking.

## 9. Demo Dataset and Scenario

Use a small controlled dataset and label all simulated information.

Example scenario: - Usable stock: 15 units. - Estimated demand: 5
units/day. - Approximate stock coverage: 3 days. - Supplier A delivery
estimate: 6 days. - Supplier B delivery estimate: 1 day.

These are test assumptions, not real supplier or market data. Add
clearly labelled sample prices, quantities, and constraints so the
comparison engine can be exercised.

Suggested demo: 1. Open a stockout warning. 2. Show its inputs and
assumptions. 3. Generate requests to two or three demo suppliers. 4.
Show approved sending or clearly labelled simulated sending. 5. Display
incoming sample replies. 6. Extract and compare offers. 7. Flag a
missing or ambiguous field. 8. Run procurement simulation. 9. Change
budget or supplier availability and recalculate. 10. Prepare a draft
purchase order. 11. Show the approval and audit history.

## 10. Testing and Evaluation

Test at least: - Normal stock and demand. - Missing sales history. -
Zero/unknown demand. - Stale inventory. - Missing delivery estimates. -
Different pack sizes. - Incomplete, conflicting, or expired
quotations. - Supplier unavailability. - Insufficient budget. - MOQ
constraints. - Multiple replies to one request. - Duplicate emails and
duplicate processing. - OAuth revocation and API failure. - Hostile or
misleading email content. - No feasible option.

Where time allows, create 10--20 reproducible scenarios and compare
against a simple baseline, such as a fixed reorder threshold plus
lowest-price selection.

Possible metrics: - Correct stockout-risk flags. - Feasible
recommendation rate. - Simulated procurement cost and shortage
exposure. - Correct detection of incomplete quotations. - Quotation
extraction accuracy on a labelled test set. - Correct reply-to-request
matching. - Duplicate-email prevention. - Successful end-to-end workflow
completion.

Report actual results. A small simulation does not prove real-world
impact or general accuracy.

## 11. Problem Validation

If possible, interview three to five pharmacy owners or pharmacists. Ask
about actual past events: - How they track stock and incoming orders. -
Recent cases of a medicine running out before replenishment. - How they
obtain and compare supplier quotations. - What happens when the usual
supplier cannot supply. - How delivery timing, minimum quantities, and
budget affect decisions. - What causes excess or near-expiry stock. -
Which steps consume the most time.

Do not lead respondents toward positive answers. Do not fabricate
interviews, testimonials, quotations, partnerships, market statistics,
or validation results. Separate verified facts, historical research,
assumptions, and hypotheses.

## 12. Team and Contribution Integrity

There are three team members. Suggested workstreams: - Frontend and
integration. - Backend and data. - AI and agent workflow.

This is a provisional split. Track actual work and ensure the README
accurately describes each person's contribution. Never claim someone
built work they did not do.

## 13. NYLP AI Hackathon 2026 Rules

Use the provided official rulebook as the authority. Key requirements: -
AI/ML must meaningfully contribute to the product; AI coding assistance
alone is insufficient. - Build a useful, responsible product for a
real-world problem. - Every listed member must contribute meaningfully;
maximum team size is five. - Submit a working product link, demo (video
or live link), and written description. - Provide a public or
judge-accessible repository. - README must include problem, solution,
tech stack, setup, AI methodology, model/API usage, screenshots, and
team contributions. - Rulebook deadline: **19 October 2026, 11:59 PM
Pakistan Standard Time (PKT)**. - No commits, pushes, or modifications
after the deadline. - Do not manipulate Git history or timestamps. Push
well before the deadline. - No plagiarism, stolen code, bought complete
projects, misrepresented contributions, or submitting an existing
commercial product as new. - Respect open-source licenses and
acknowledge significant libraries, templates, APIs, and datasets. -
Disclose third-party AI APIs and be prepared to explain architecture,
prompts/workflows, model usage, and limitations. - Do not fabricate
evidence or submit untested AI output. - Protect privacy, API keys,
OAuth tokens, and credentials. - No malicious or illegal behavior,
phishing, credential theft, unauthorized access, or data theft. - Ensure
judges can access the app and repository. - Presentation must cover the
problem, features, technical approach, AI component, challenges,
limitations, and future improvements. - Judging: Innovation 25%, Impact
25%, Feasibility 25%, Presentation 25%. - Follow the code of conduct and
organizer instructions.

Before the deadline, verify the live app, repository, README,
screenshots, demo, team details, and official submission form. Do not
make post-deadline modifications.

## 14. Required README and Submission Materials

Prepare: - Project and team names. - Team members and truthful
contributions. - Problem statement and target users. - Solution overview
and features. - Architecture and technology stack. - AI methodology and
agent workflow. - Model and third-party API usage. - Gmail API/OAuth
setup and required permissions. - Setup instructions and environment
variable names (never real secret values). - Database setup and
seed-data instructions. - Screenshots. - Test/evaluation results. -
Known limitations. - Live demo, repository, and demo video URLs. -
Significant third-party libraries, templates, APIs, and datasets.

Never commit actual secrets, API keys, passwords, OAuth tokens, or
secret environment files.

## 15. How an AI Assistant Should Help

When implementing a feature: 1. Explain the goal and why it is needed.
2. Inspect the actual repository, files, and current architecture before
modifying existing code. 3. Identify affected files, APIs, schema, and
dependencies. 4. Provide a small, ordered implementation plan. 5. Give
consistent code and commands when requested. 6. Explain configuration
and environment variables. 7. Include tests and failure cases. 8. Do not
claim code was tested unless it was actually run and tested.

When debugging, use the supplied code, logs, and errors. Do not invent
file contents or assume implementation status. Prefer targeted changes
that preserve working behavior.

Separate essential features from optional enhancements. Avoid
overengineering. Ask a focused question when missing information
materially affects correctness; otherwise state a reasonable assumption
and proceed.

For market research, use current reliable sources and cite factual
claims. Distinguish evidence from assumptions.

For hackathon advice, optimize for a working, differentiated,
measurable, well-presented product. Never guarantee a perfect judging
score.

## 16. Definition of MVP Success

The MVP should demonstrate one complete, testable flow:

1.  Identify a potential medicine stockout.
2.  Explain the data and assumptions.
3.  Prepare supplier quotation requests.
4.  Send approved requests through Gmail or clearly labelled simulated
    mode.
5.  Retrieve or simulate replies.
6.  Extract, validate, and display quotation details.
7.  Compare feasible procurement options using deterministic
    calculations.
8.  Explain trade-offs using actual calculated values.
9.  Recalculate after a user changes a constraint.
10. Prepare a draft purchase order.
11. Require human approval.
12. Record the decision and audit trail.
13. Show reproducible tests and honest limitations.

**Core differentiator:** shortage-risk analysis + Gmail quotation
automation + feasible procurement simulation + human-controlled
purchasing.

Build this end-to-end workflow reliably before expanding the scope.
