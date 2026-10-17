---
name: mediprocure-agent
description: >-
  Operational runbook and workflow guide for MediProcure AI. Use this skill when
  developing, testing, running, or debugging the shortage risk engine, Gmail quotation agent,
  quotation parser, procurement simulator, FastAPI backend, or web frontend.
---

# MediProcure AI — Workspace Skill & Runbook

This skill provides step-by-step procedures to develop, run, and test MediProcure AI collaboratively. It is stored locally in the `.agents/skills/` directory so all team members have immediate access upon cloning without external installations.

---

## 1. Environment & Dependency Setup

### Prerequisites
- Python 3.11+ (Python 3.12 / 3.14 compatible)
- Node.js 18+ (for frontend web application)

### Python Virtual Environment Setup
```powershell
# Create virtual environment if not present
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install required AI and engine dependencies
pip install -r ai_engine/requirements-ml.txt
pip install pytest
```

---

## 2. Core Testing Procedures

MediProcure AI relies strictly on deterministic calculation and validation logic before any AI agent actions. Always run the unit test suite after making changes.

### Running All Unit Tests
```powershell
python -m pytest tests/
```

### Running Shortage Risk Engine Standalone
```powershell
python test_shortage_risk.py
```
*Expected Output:*
- Displays `coverage_days`, `stockout_before_delivery`, `stock_at_delivery`, and risk classification (`high_risk`, `warning`, `lower_risk`, `review_required`).

### Running Unit Tests for Quote Parser & Risk Engine
```powershell
python -m pytest tests/unit/test_shortage_risk.py
python -m pytest tests/unit/test_quote_parser.py
```

---

## 3. Gmail Integration & Supplier Agent Workflows

The system communicates with suppliers via Gmail API and LangGraph with strict Human-in-the-Loop approval.

### A. Testing Gmail API Connection (Read/Auth Check)
```powershell
python test_gmail_connection.py
```
- Verifies `credentials.json` and `token.json` exist and the Google OAuth client initializes cleanly.
- Does **not** read private emails or send messages.

### B. Testing Controlled Outbound Gmail Send
```powershell
python test_gmail_send.py
```
- Prompts for a destination email address and explicit `yes/no` confirmation before dispatching a controlled test email.

### C. Running the LangGraph Agent Demo (Human-in-the-Loop)
```powershell
python run_agent_demo.py
```
*Workflow Steps Executed:*
1. **assess_risk**: Deterministically calculates stock coverage and stockout risks.
2. **route_after_risk**: Evaluates missing data or risk level; transitions to `prepare_draft` or `needs_review`.
3. **prepare_draft**: Formulates a standardized supplier quotation request.
4. **human_approval**: Triggers a LangGraph `interrupt()`. Displays recipient, subject, and body in the terminal and waits for explicit user confirmation (`yes/no`).
5. **send_email_real**: Dispatches separate individual emails to suppliers only if approved; otherwise routes to `approval_declined`.

---

## 4. Architecture & Engineering Rules

When extending the codebase, observe these mandatory patterns:

1. **Separation of Concerns:**
   - Calculations (coverage, lead times, total cost, scenario comparisons) belong in pure deterministic Python functions under `ai_engine/risk/` or `backend/services/`.
   - AI and LLM orchestration belongs in `ai_engine/agent/` or `ai_engine/quotes/`.
2. **Untrusted Inbound Data:**
   - All supplier replies (text and attachments) parsed by `ai_engine/quotes/parser.py` must pass through `ai_engine/quotes/validator.py`.
   - Never auto-fill missing fields or suppress warning flags.
3. **Audit Trail:**
   - Every state transition, user decision, and email exchange must be logged with timestamps and message IDs.
4. **Secret Isolation:**
   - Never commit `credentials.json`, `token.json`, or `.env` to Git. Ensure `.gitignore` ignores them at all times.

---

## 5. Hackathon Verification Checklist

Before pushing or submitting for NYLP AI Hackathon 2026:
- [ ] Run `python -m pytest tests/` — all tests must pass (100% green).
- [ ] Verify both Live Gmail mode and Simulated mode are clearly labelled.
- [ ] Verify that no credentials or secrets exist in git staging (`git status`).
- [ ] Ensure all new documentation in `docs/` is up to date with implementation progress.
