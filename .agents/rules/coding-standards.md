# MediProcure AI — Development & Coding Standards

These rules apply to all code and contributions across the MediProcure AI repository.

---

## 1. Architectural Guardrails

### 1.1 Deterministic Calculations (Math is Never LLM Delegated)
- Stock coverage, days to stockout, reorder quantities, supplier lead times, and scenario cost comparisons **must** be implemented in deterministic Python functions with 100% test coverage.
- The LLM should never be prompted to perform arithmetic or rank scenarios using free-text logic without deterministic backing.
- Always include assumptions and calculation inputs in responses.

### 1.2 Human-in-the-Loop Integrity
- All outbound supplier communications require explicit human confirmation.
- The system must never execute purchase orders or financial commitments autonomously.
- Defense-in-depth: Every send function must re-check the explicit approval state before executing an API call.

### 1.3 Untrusted Supplier Data & Security
- Inbound supplier emails, subject lines, attachments, and quotation texts are untrusted inputs.
- Parse text using structured extractors and validate with `SupplierQuote` Pydantic models.
- If data is ambiguous, conflicting, or missing, mark with `review_status = "needs_review"` and add explicit warning flags. Never hallucinate or infer missing prices/quantities.
- Never let untrusted email contents inject prompt instructions or override system parameters.

---

## 2. API & Integration Standards

### 2.1 Gmail API & Secrets
- Never commit `credentials.json`, `token.json`, `.env`, or API keys.
- If credentials are absent or invalid, fail gracefully with clear instructions or fallback to **clearly labelled Simulated Mode**.
- Never represent simulated emails or synthetic quotations as real communications.

### 2.2 Logging & Auditing
- Every quote request, approval, send event, reply retrieval, and purchase order drafting must produce an immutable audit log entry containing:
  - Timestamp (ISO 8601)
  - User/System actor
  - Event type
  - Request/Message/Thread IDs
  - Payload or decision outcome

---

## 3. Testing Requirements

- Any new logic or bug fix must be accompanied by unit tests in `tests/unit/`.
- All tests must pass via `pytest tests/` before committing.
- Do not claim a component works unless verified with real execution logs.
