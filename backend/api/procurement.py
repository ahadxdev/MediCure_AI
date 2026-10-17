import json
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db
from backend.models.entities import Medicine, Quotation, AuditEvent
from backend.schemas.procurement import (
    SimulationRequest,
    SimulationResponse,
    SimulationOption,
)

router = APIRouter(prefix="/procurement", tags=["Procurement Simulator"])


@router.post("/simulate", response_model=SimulationResponse)
def simulate_procurement_scenarios(
    payload: SimulationRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Deterministic multi-criteria procurement scenario comparison.
    Calculates fastest delivery, lowest landed cost, and split-order options
    based on verified supplier quotations in the database.
    """
    med = db.query(Medicine).filter(Medicine.id == payload.medicine_id).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Medicine '{payload.medicine_id}' not found")

    quotes = (
        db.query(Quotation)
        .options(joinedload(Quotation.supplier))
        .filter(Quotation.review_status == "validated")
        .all()
    )

    qty = payload.required_quantity
    options: list[SimulationOption] = []

    if not quotes:
        # Infeasible case
        options.append(
            SimulationOption(
                scenario_type="infeasible",
                title="No Validated Quotes",
                supplier_name="None",
                allocated_quantity=0.0,
                unit_price=0.0,
                delivery_fee=0.0,
                total_cost=0.0,
                delivery_days=0.0,
                residual_shortage_days=10.0,
                explanation="No validated supplier quotes available for this medicine.",
                feasibility_status="infeasible",
            )
        )
        return SimulationResponse(
            medicine_id=med.id,
            medicine_name=med.name,
            required_quantity=qty,
            options=options,
            quotes_evaluated_count=0,
        )

    # 1. Evaluate lowest landed cost: price * qty + delivery_fee
    sorted_by_price = sorted(quotes, key=lambda q: (q.price or 0.0) * qty + (q.delivery_fee or 0.0))
    cheapest = sorted_by_price[0]
    cheapest_cost = (cheapest.price or 0.0) * qty + (cheapest.delivery_fee or 0.0)

    # 2. Evaluate fastest delivery
    sorted_by_speed = sorted(quotes, key=lambda q: q.delivery_days or 999.0)
    fastest = sorted_by_speed[0]
    fastest_cost = (fastest.price or 0.0) * qty + (fastest.delivery_fee or 0.0)

    # Option 1: Fastest Delivery (Recommended)
    options.append(
        SimulationOption(
            scenario_type="fastest",
            title="Fastest Delivery (Recommended)",
            supplier_name=fastest.supplier.name if fastest.supplier else "Primary Distributor",
            allocated_quantity=qty,
            unit_price=round(fastest.price or 0.0, 2),
            delivery_fee=round(fastest.delivery_fee or 0.0, 2),
            total_cost=round(fastest_cost, 2),
            delivery_days=fastest.delivery_days or 3.0,
            residual_shortage_days=max(0.0, (fastest.delivery_days or 3.0) - 3.0),
            explanation=f"Delivers in {fastest.delivery_days} days. Landed cost PKR {fastest_cost:,.2f}.",
            feasibility_status="feasible" if fastest_cost <= payload.budget_limit else "warning",
        )
    )

    # Option 2: Lowest Cost (if different from fastest)
    if cheapest.id != fastest.id:
        savings = fastest_cost - cheapest_cost
        options.append(
            SimulationOption(
                scenario_type="cheapest",
                title="Lowest Landed Cost",
                supplier_name=cheapest.supplier.name if cheapest.supplier else "Budget Distributor",
                allocated_quantity=qty,
                unit_price=round(cheapest.price or 0.0, 2),
                delivery_fee=round(cheapest.delivery_fee or 0.0, 2),
                total_cost=round(cheapest_cost, 2),
                delivery_days=cheapest.delivery_days or 5.0,
                residual_shortage_days=max(0.0, (cheapest.delivery_days or 5.0) - 3.0),
                explanation=f"Saves PKR {savings:,.2f}, with {cheapest.delivery_days}-day lead time.",
                feasibility_status="feasible" if cheapest_cost <= payload.budget_limit else "warning",
            )
        )

    # Option 3: Split Order if 2 or more suppliers
    if len(quotes) >= 2:
        q1 = round(qty * 0.6)
        q2 = qty - q1
        split_cost = ((fastest.price or 0.0) * q1 + (fastest.delivery_fee or 0.0)) + (
            (cheapest.price or 0.0) * q2 + (cheapest.delivery_fee or 0.0)
        )
        avg_unit_price = split_cost / qty
        sup1 = fastest.supplier.name if fastest.supplier else "Supplier A"
        sup2 = cheapest.supplier.name if cheapest.supplier else "Supplier B"

        options.append(
            SimulationOption(
                scenario_type="split_order",
                title="Split Order (Risk Mitigation)",
                supplier_name=f"{sup1} ({int(q1)}) + {sup2} ({int(q2)})",
                allocated_quantity=qty,
                unit_price=round(avg_unit_price, 2),
                delivery_fee=round((fastest.delivery_fee or 0.0) + (cheapest.delivery_fee or 0.0), 2),
                total_cost=round(split_cost, 2),
                delivery_days=fastest.delivery_days or 2.0,
                residual_shortage_days=0.0,
                explanation=f"Secures emergency {int(q1)} units quickly from {sup1}, balancing bulk cost with {sup2}.",
                feasibility_status="feasible" if split_cost <= payload.budget_limit else "warning",
            )
        )

    # Log audit event for simulation run
    audit = AuditEvent(
        entity_type="procurement_simulator",
        entity_id=med.id,
        event_type="simulation_executed",
        actor="Pharmacist (Web User)",
        payload=json.dumps({"quantity": qty, "budget": payload.budget_limit, "options_count": len(options)}),
    )
    db.add(audit)
    db.commit()

    return SimulationResponse(
        medicine_id=med.id,
        medicine_name=med.name,
        required_quantity=qty,
        options=options,
        quotes_evaluated_count=len(quotes),
    )
