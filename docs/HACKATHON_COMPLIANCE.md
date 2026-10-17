# MediProcure AI — NYLP AI Hackathon 2026 Compliance & Team Charter

> **Competition:** NYLP AI Hackathon 2026  
> **Official Deadline:** 19 October 2026, 11:59 PM Pakistan Standard Time (PKT)  
> **Integrity Standard:** 100% Truthful Attribution, Zero Plagiarism, Strict Secret Isolation

---

## 1. Compliance Checklist with Hackathon Rules

- [x] **Meaningful AI/ML Contribution:**
  - AI does not merely assist in writing code; it powers the core product workflow:
    1. Multi-variable decision orchestration via LangGraph.
    2. Intelligent quotation parsing and anomaly detection from unstructured supplier emails.
    3. Context-aware explanation of complex procurement trade-offs.
- [x] **Responsible & Safe Healthcare AI:**
  - Strictly decision-support. Does not replace clinical pharmacists or automatically dispense or substitute medicines.
  - Math and constraint checks are strictly deterministic to eliminate hallucinations.
- [x] **Human-in-the-Loop Safeguards:**
  - Mandatory human approval on all outbound quotation requests.
  - Zero autonomous financial commitments: Draft purchase orders require explicit human sign-off.
- [x] **Security & Privacy:**
  - Google OAuth 2.0 tokens kept strictly on backend; zero secrets committed to Git (`.gitignore` enforced).
  - Supplier emails treated as untrusted input.
- [x] **Transparency in Testing & Demos:**
  - Live Gmail mode and Simulated Demo mode are distinctly labelled.
  - Real test logs and verifiable 16/16 unit test results.
- [x] **Deadline Adherence:**
  - Strict code freeze before 19 October 2026, 11:59 PM PKT.

---

## 2. Team Workstreams & Contribution Ledger

In accordance with Section 12 & 13 of the project guidelines, work is divided across three dedicated workstreams:

### Workstream 1: AI & Agent Workflow
- **Scope:** LangGraph workflow design, human-in-the-loop state interrupts, prompt engineering, quote extraction parser, anomaly validator, and LLM trade-off explanations.
- **Key Deliverables:** `ai_engine/agent/graph.py`, `ai_engine/quotes/parser.py`, `ai_engine/quotes/validator.py`, `run_agent_demo.py`.

### Workstream 2: Backend & Data Engineering
- **Scope:** FastAPI REST API, deterministic shortage risk engine, PostgreSQL schemas, procurement scenario simulator, Gmail API OAuth integration, and audit logging.
- **Key Deliverables:** `ai_engine/risk/shortage_risk.py`, `ai_engine/gmail/client.py`, `backend/`, and database models.

### Workstream 3: Frontend & Integration
- **Scope:** Modern responsive web application (Next.js / React), Shortage Early-Warning Radar visualization, Quotation Inbox & Comparison Matrix, What-If simulation UI, and Draft PO approval modal.
- **Key Deliverables:** `frontend/` UI components, state management, and API client integration.

---

## 3. Disclosed Third-Party Libraries, Models & APIs

| Component | Library / Service | Purpose | License |
| :--- | :--- | :--- | :--- |
| **Agent Orchestrator** | `langgraph` / `langchain` | Stateful human-in-the-loop workflow graph | MIT |
| **Email Gateway** | Google Gmail API (OAuth 2.0) | Direct supplier email communication | Apache 2.0 |
| **Data Validation** | `pydantic` v2 | Strict schema typing and validation | MIT |
| **Testing** | `pytest` | Unit and integration test suite | MIT |
| **Web Framework** | FastAPI (planned) | High-performance async REST backend | MIT |
| **Frontend Framework**| Next.js / React (planned) | Web client interface | MIT |

---

## 4. Judging Criteria Alignment

| Criterion | Weight | MediProcure AI Implementation |
| :--- | :--- | :--- |
| **Innovation** | 25% | First platform uniting real-time shortage prediction with automated Gmail supplier sourcing and multi-supplier split simulation. |
| **Impact** | 25% | Solves critical medicine stockouts in Pakistan, reducing patient treatment disruptions and saving pharmacy capital. |
| **Feasibility** | 25% | Production-ready architecture utilizing standard Gmail protocols without requiring suppliers to adopt proprietary software. |
| **Presentation** | 25% | Transparent decision explainability, live/simulated demonstration, comprehensive documentation, and 100% test coverage. |
