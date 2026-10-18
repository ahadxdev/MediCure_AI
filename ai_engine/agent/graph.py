from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

from ai_engine.agent.state import AgentState
from ai_engine.risk.shortage_risk import assess_shortage_risk
from ai_engine.gmail.client import send_email
from backend.config import settings

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

    if state.get("force_rfq"):
        return "prepare_draft"

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

    request_reference = state.get("request_id")
    subject = f"RFQ {request_reference} - {medicine}" if request_reference else f"Quotation Request - {medicine}"

    body = f"""Dear Supplier,

Please provide a quotation for the following medicine:

RFQ reference: {request_reference or "Pending"}
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
        return "send_email"

    return "declined"


def send_email_real(state: AgentState) -> dict:
    # Defense in depth: never send without explicit approval.
    decision = state.get("email_approval", {})
    if decision.get("approved") is not True:
        return {
            "email_status": "not_sent",
            "next_action": "approval_required",
        }

    draft = state["email_draft"]
    recipients = draft.get("to", [])

    if not recipients:
        return {
            "email_status": "send_failed",
            "email_error": "No recipients provided.",
            "next_action": "human_review",
        }

    sent_messages = []
    failures = []

    if settings.GMAIL_MODE != "LIVE":
        return {
            "email_status": "simulated",
            "gmail_messages": [
                {"recipient": recipient, "status": "simulated"}
                for recipient in recipients
            ],
            "next_action": "simulated_send_complete",
        }

    # Send separate emails to protect supplier email privacy.
    for recipient in recipients:
        try:
            result = send_email(
                to=[recipient],
                subject=draft["subject"],
                body=draft["body"],
            )

            sent_messages.append({
                "recipient": recipient,
                "message_id": result["message_id"],
                "thread_id": result["thread_id"],
                "status": "sent",
            })

        except Exception as exc:
            # Do not automatically retry: the send outcome can
            # be uncertain if the API request fails mid-flight.
            failures.append({
                "recipient": recipient,
                "error": str(exc),
            })

    if sent_messages and failures:
        status = "partially_sent"
        next_action = "review_failed_recipients"
    elif sent_messages:
        status = "sent"
        next_action = "await_supplier_replies"
    else:
        status = "send_failed"
        next_action = "review_send_error"

    return {
        "email_status": status,
        "gmail_messages": sent_messages,
        "email_error": "; ".join(
            f"{item['recipient']}: {item['error']}"
            for item in failures
        ),
        "next_action": next_action,
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
    workflow.add_node("send_email", send_email_real)
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
            "send_email": "send_email",
            "declined": "declined",
        },
    )

    workflow.add_edge("send_email", END)
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
