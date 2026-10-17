
from langgraph.types import Command

from ai_engine.agent.graph import build_agent


def main():
    graph = build_agent()

    config = {
        "configurable": {
            "thread_id": "mediprocure-demo-001"
        }
    }

    initial_state = {
        "medicine_name": "Paracetamol",
        "strength": "500 mg",
        "dosage_form": "Tablet",
        "pack_size": "10 tablets per strip",
        "usable_stock": 15,
        "avg_daily_demand": 5,
        "supplier_lead_time_days": 6,
        "incoming_shipments": [],
        "required_quantity": 100,
        "delivery_location": "Karachi",
        "required_by_date": "2026-10-20",
        "supplier_emails": ["supplier-demo@example.invalid"],
    }

    print("\n=== MediProcure AI Agent Demo ===")
    print("Delivery location:", initial_state.get("delivery_location"))
    print("Supplier emails:", initial_state.get("supplier_emails"))
    result = graph.invoke(initial_state, config=config)

    if "__interrupt__" in result:
        approval_prompt = result["__interrupt__"][0].value
        print("\n--- Approval Required ---")
        print(approval_prompt["message"])
        print("\nTo:", approval_prompt["draft"]["to"])
        print("Subject:", approval_prompt["draft"]["subject"])
        print("\n", approval_prompt["draft"]["body"])

        answer = input("\nApprove simulated send? (yes/no): ")
        approved = answer.strip().lower() == "yes"

        result = graph.invoke(
            Command(resume={"approved": approved}),
            config=config,
        )

    print("\n--- Agent Result ---")
    print("Risk:", result.get("risk_result", {}).get("status"))
    print("Email status:", result.get("email_status", "not sent"))
    print("Next action:", result.get("next_action"))
    print("Review reason:", result.get("review_reason", "None"))


if __name__ == "__main__":
    main()
