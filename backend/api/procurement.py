import json
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db
from backend.auth import require_api_key
from backend.models.entities import Medicine, Quotation, QuotationRequest, Supplier, AuditEvent
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
    _: Annotated[str, Depends(require_api_key)],
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
        .join(QuotationRequest, Quotation.request_id == QuotationRequest.id)
        .filter(Quotation.review_status == "validated")
        .filter(QuotationRequest.medicine_id == med.id)
        .filter(Quotation.supplier.has(Supplier.is_verified.is_(True)))
        .all()
    )

    qty = payload.required_quantity * (1 + payload.demand_surge_percent / 100)
    qty = float(round(qty, 2))
    quotes = [
        quote
        for quote in quotes
        if quote.price is not None
        and quote.quoted_quantity is not None
        and quote.quoted_quantity >= max(qty, quote.minimum_order_quantity or 0)
    ]
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
    cheapest_qty = max(qty, cheapest.minimum_order_quantity or 0.0)
    cheapest_cost = (cheapest.price or 0.0) * cheapest_qty + (cheapest.delivery_fee or 0.0)

    # 2. Evaluate fastest delivery
    sorted_by_speed = sorted(quotes, key=lambda q: q.delivery_days if q.delivery_days is not None else 999.0)
    fastest = sorted_by_speed[0]
    fastest_qty = max(qty, fastest.minimum_order_quantity or 0.0)
    fastest_cost = (fastest.price or 0.0) * fastest_qty + (fastest.delivery_fee or 0.0)

    # Option 1: Fastest Delivery (Recommended)
    options.append(
        SimulationOption(
            scenario_type="fastest",
            title="Fastest Delivery (Recommended)",
            supplier_name=fastest.supplier.name if fastest.supplier else fastest.supplier_name or "Unknown supplier",
            allocated_quantity=fastest_qty,
            unit_price=round(fastest.price or 0.0, 2),
            delivery_fee=round(fastest.delivery_fee or 0.0, 2),
            total_cost=round(fastest_cost, 2),
            delivery_days=(fastest.delivery_days or 0.0) + payload.supplier_delay_days,
            residual_shortage_days=max(0.0, ((fastest.delivery_days or 0.0) + payload.supplier_delay_days) - 3.0),
            explanation=f"Delivers in {(fastest.delivery_days or 0.0) + payload.supplier_delay_days:g} days. Landed cost PKR {fastest_cost:,.2f}.",
            feasibility_status=(
                "feasible"
                if fastest_cost <= payload.budget_limit
                and (fastest.delivery_days is not None and fastest.delivery_days + payload.supplier_delay_days <= payload.max_delivery_days)
                else "warning"
            ),
        )
    )

    # Option 2: Lowest Cost (if different from fastest)
    if cheapest.id != fastest.id:
        savings = fastest_cost - cheapest_cost
        options.append(
            SimulationOption(
                scenario_type="cheapest",
                title="Lowest Landed Cost",
                supplier_name=cheapest.supplier.name if cheapest.supplier else cheapest.supplier_name or "Unknown supplier",
                allocated_quantity=cheapest_qty,
                unit_price=round(cheapest.price or 0.0, 2),
                delivery_fee=round(cheapest.delivery_fee or 0.0, 2),
                total_cost=round(cheapest_cost, 2),
                delivery_days=(cheapest.delivery_days or 0.0) + payload.supplier_delay_days,
                residual_shortage_days=max(0.0, ((cheapest.delivery_days or 0.0) + payload.supplier_delay_days) - 3.0),
                explanation=f"Saves PKR {savings:,.2f}, with {(cheapest.delivery_days or 0.0) + payload.supplier_delay_days:g}-day lead time.",
                feasibility_status=(
                    "feasible"
                    if cheapest_cost <= payload.budget_limit
                    and (cheapest.delivery_days is not None and cheapest.delivery_days + payload.supplier_delay_days <= payload.max_delivery_days)
                    else "warning"
                ),
            )
        )

    # Option 3: Split Order if 2 or more suppliers
    q1 = qty * 0.6
    q2 = qty - q1
    if (
        len(quotes) >= 2
        and fastest.id != cheapest.id
        and fastest.quoted_quantity is not None
        and cheapest.quoted_quantity is not None
        and fastest.quoted_quantity >= max(q1, fastest.minimum_order_quantity or 0)
        and cheapest.quoted_quantity >= max(q2, cheapest.minimum_order_quantity or 0)
        and (fastest.minimum_order_quantity is None or fastest.minimum_order_quantity <= q1)
        and (cheapest.minimum_order_quantity is None or cheapest.minimum_order_quantity <= q2)
    ):
        split_cost = ((fastest.price or 0.0) * q1 + (fastest.delivery_fee or 0.0)) + (
            (cheapest.price or 0.0) * q2 + (cheapest.delivery_fee or 0.0)
        )
        avg_unit_price = split_cost / qty
        sup1 = fastest.supplier.name if fastest.supplier else fastest.supplier_name or "Unknown supplier"
        sup2 = cheapest.supplier.name if cheapest.supplier else cheapest.supplier_name or "Unknown supplier"

        options.append(
            SimulationOption(
                scenario_type="split_order",
                title="Split Order (Risk Mitigation)",
                supplier_name=f"{sup1} ({q1:g}) + {sup2} ({q2:g})",
                allocated_quantity=qty,
                unit_price=round(avg_unit_price, 2),
                delivery_fee=round((fastest.delivery_fee or 0.0) + (cheapest.delivery_fee or 0.0), 2),
                total_cost=round(split_cost, 2),
                delivery_days=fastest.delivery_days if fastest.delivery_days is not None else 0.0,
                residual_shortage_days=0.0,
                explanation=f"Secures emergency {q1:g} units quickly from {sup1}, balancing cost with {sup2}.",
                feasibility_status=(
                    "feasible"
                    if split_cost <= payload.budget_limit
                    and fastest.delivery_days is not None
                    and fastest.delivery_days + payload.supplier_delay_days <= payload.max_delivery_days
                    else "warning"
                ),
                allocations=[{"supplier_name": sup1, "quantity": q1, "unit_price": fastest.price or 0.0, "delivery_fee": fastest.delivery_fee or 0.0}, {"supplier_name": sup2, "quantity": q2, "unit_price": cheapest.price or 0.0, "delivery_fee": cheapest.delivery_fee or 0.0}],
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
