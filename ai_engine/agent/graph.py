from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

from ai_engine.agent.state import AgentState
from ai_engine.risk.shortage_risk import assess_shortage_risk


def assess_risk(state: AgentState) -> dict:
    risk = assess_shortage_risk(
        usable_stock=state["usable_stock"],
        avg_daily_demand=state["avg_daily_demand"],
        supplier_lead_time_days=state.get(
            "supplier_lead_time_days"
        ),
        incoming_shipments=state.get("incoming_shipments", []),
    )
    return {"risk_result": risk}


def route_after_risk(state: AgentState) -> str:
    print("DEBUG delivery:", repr(state.get("delivery_location")))
    print("DEBUG suppliers:", repr(state.get("supplier_emails")))


    
    required_fields = [
        "medicine_name",
        "strength",
        "dosage_form",
        "pack_size",
        "required_quantity",
        "delivery_location",
        "required_by_date",
        "supplier_emails",
    ]

    missing = [
        field for field in required_fields
        if not state.get(field)
    ]

    if missing:
        return "needs_review"

    status = state["risk_result"]["status"]

    if status in ("unknown", "review_required"):
        return "needs_review"

    if status in ("high_risk", "warning", "needs_delivery_data"):
        return "prepare_draft"

    return "no_action"


def prepare_quote_request(state: AgentState) -> dict:
    medicine = (
        f'{state["medicine_name"]} '
        f'{state["strength"]}, '
        f'{state["dosage_form"]}, '
        f'pack: {state["pack_size"]}'
    )

    subject = f"Quotation Request - {medicine}"

    body = f"""Dear Supplier,

Please provide a quotation for the following medicine:

Medicine: {medicine}
Required quantity: {state["required_quantity"]}
Delivery location: {state["delivery_location"]}
Required by: {state["required_by_date"]}

Please confirm:
- Price and price unit
- Available quantity and minimum order quantity (MOQ)
- Expected delivery date/time
- Delivery and other charges
- Payment terms
- Quotation validity

This is a request for quotation, not a purchase order.

Regards,
MediProcure AI
"""

    return {
        "email_draft": {
            "to": state["supplier_emails"],
            "subject": subject,
            "body": body,
        },
        "next_action": "human_approval_required",
    }


def request_human_approval(state: AgentState) -> dict:
    decision = interrupt({
        "type": "supplier_email_approval",
        "message": "Review the draft before sending.",
        "draft": state["email_draft"],
    })

    return {"email_approval": decision}


def route_after_approval(state: AgentState) -> str:
    decision = state.get("email_approval", {})
    if decision.get("approved") is True:
        return "send_mock"
    return "declined"


def send_email_mock(state: AgentState) -> dict:
    # Simulation only: this node does NOT send an email.
    return {
        "email_status": "simulated_send",
        "next_action": "connect_gmail_integration",
    }


def approval_declined(state: AgentState) -> dict:
    return {
        "email_status": "not_sent",
        "next_action": "revise_or_cancel_draft",
    }


def needs_review(state: AgentState) -> dict:
    risk = state.get("risk_result", {})
    missing = [
        field
        for field in [
            "medicine_name", "strength", "dosage_form",
            "pack_size", "required_quantity",
            "delivery_location", "required_by_date",
            "supplier_emails",
        ]
        if not state.get(field)
    ]

    reasons = list(risk.get("risk_flags", []))
    if missing:
        reasons.append("Missing required fields: " + ", ".join(missing))

    return {
        "review_reason": "; ".join(reasons)
        or "Risk assessment requires human review.",
        "next_action": "human_review",
    }


def no_action_needed(state: AgentState) -> dict:
    return {
        "next_action": "monitor_inventory",
        "email_status": "not_needed",
    }


def build_agent():
    workflow = StateGraph(AgentState)

    workflow.add_node("assess_risk", assess_risk)
    workflow.add_node("prepare_draft", prepare_quote_request)
    workflow.add_node("human_approval", request_human_approval)
    workflow.add_node("send_mock", send_email_mock)
    workflow.add_node("declined", approval_declined)
    workflow.add_node("needs_review", needs_review)
    workflow.add_node("no_action", no_action_needed)

    workflow.add_edge(START, "assess_risk")

    workflow.add_conditional_edges(
        "assess_risk",
        route_after_risk,
        {
            "prepare_draft": "prepare_draft",
            "needs_review": "needs_review",
            "no_action": "no_action",
        },
    )

    workflow.add_edge("prepare_draft", "human_approval")

    workflow.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {
            "send_mock": "send_mock",
            "declined": "declined",
        },
    )

    workflow.add_edge("send_mock", END)
    workflow.add_edge("declined", END)
    workflow.add_edge("needs_review", END)
    workflow.add_edge("no_action", END)

    return workflow.compile(checkpointer=InMemorySaver())


# Command is imported for resuming the paused graph.
def resume_agent(graph, approved: bool, config: dict):
    return graph.invoke(
        Command(resume={"approved": approved}),
        config=config,
    )
