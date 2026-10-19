import json
import re
from datetime import date
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_
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


def _normalize_medicine_name(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").casefold())


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

    candidate_quotes = (
        db.query(Quotation)
        .options(joinedload(Quotation.supplier), joinedload(Quotation.request))
        .outerjoin(QuotationRequest, Quotation.request_id == QuotationRequest.id)
        .filter(Quotation.review_status == "validated")
        .filter(
            or_(
                QuotationRequest.medicine_id == med.id,
                and_(
                    Quotation.request_id.is_(None),
                    Quotation.medicine_name.isnot(None),
                ),
            )
        )
        .filter(Quotation.supplier.has(Supplier.is_verified.is_(True)))
        .all()
    )
    all_quotes = [
        quote
        for quote in candidate_quotes
        if (
            quote.request_id is not None
            or _normalize_medicine_name(quote.medicine_name)
            == _normalize_medicine_name(med.name)
        )
    ]

    qty = payload.required_quantity * (1 + payload.demand_surge_percent / 100)
    qty = float(round(qty, 2))
    today = date.today()
    quotes = []
    for quote in all_quotes:
        if (
            quote.price is None
            or quote.price <= 0
            or (quote.currency or "").strip().upper() != "PKR"
            or quote.delivery_fee is None
            or quote.quoted_quantity is None
            or quote.delivery_days is None
            or quote.delivery_days < 0
        ):
            continue
        if quote.valid_until:
            try:
                if date.fromisoformat(quote.valid_until) < today:
                    continue
            except ValueError:
                continue
        quotes.append(quote)

    def order_quantity(quote: Quotation, requested: float) -> float:
        return max(requested, quote.minimum_order_quantity or 0.0)

    def can_supply(quote: Quotation, requested: float) -> bool:
        return quote.quoted_quantity >= order_quantity(quote, requested)

    def adjusted_delivery(quote: Quotation) -> float:
        return quote.delivery_days + payload.supplier_delay_days

    def feasibility(cost: float, delivery_days: float) -> str:
        return (
            "feasible"
            if cost <= payload.budget_limit and delivery_days <= payload.max_delivery_days
            else "warning"
        )

    single_order_quotes = [quote for quote in quotes if can_supply(quote, qty)]
    options: list[SimulationOption] = []

    if single_order_quotes:
        cheapest = min(
            single_order_quotes,
            key=lambda quote: quote.price * order_quantity(quote, qty) + (quote.delivery_fee or 0.0),
        )
        fastest = min(single_order_quotes, key=lambda quote: quote.delivery_days)

        cheapest_qty = order_quantity(cheapest, qty)
        cheapest_cost = cheapest.price * cheapest_qty + (cheapest.delivery_fee or 0.0)
        fastest_qty = order_quantity(fastest, qty)
        fastest_cost = fastest.price * fastest_qty + (fastest.delivery_fee or 0.0)

        options.append(
            SimulationOption(
                scenario_type="fastest",
                title="Fastest Delivery",
                supplier_name=fastest.supplier.name if fastest.supplier else fastest.supplier_name or "Unknown supplier",
                allocated_quantity=fastest_qty,
                unit_price=round(fastest.price, 2),
                delivery_fee=round(fastest.delivery_fee or 0.0, 2),
                total_cost=round(fastest_cost, 2),
                delivery_days=adjusted_delivery(fastest),
                residual_shortage_days=max(0.0, adjusted_delivery(fastest) - payload.max_delivery_days),
                explanation=f"Delivers in {adjusted_delivery(fastest):g} days. Landed cost PKR {fastest_cost:,.2f}.",
                feasibility_status=feasibility(fastest_cost, adjusted_delivery(fastest)),
            )
        )

        if cheapest.id != fastest.id:
            options.append(
                SimulationOption(
                    scenario_type="cheapest",
                    title="Lowest Landed Cost",
                    supplier_name=cheapest.supplier.name if cheapest.supplier else cheapest.supplier_name or "Unknown supplier",
                    allocated_quantity=cheapest_qty,
                    unit_price=round(cheapest.price, 2),
                    delivery_fee=round(cheapest.delivery_fee or 0.0, 2),
                    total_cost=round(cheapest_cost, 2),
                    delivery_days=adjusted_delivery(cheapest),
                    residual_shortage_days=max(0.0, adjusted_delivery(cheapest) - payload.max_delivery_days),
                    explanation=f"Saves PKR {fastest_cost - cheapest_cost:,.2f}, with {adjusted_delivery(cheapest):g}-day lead time.",
                    feasibility_status=feasibility(cheapest_cost, adjusted_delivery(cheapest)),
                )
            )

    q1 = round(qty * 0.6, 2)
    q2 = round(qty - q1, 2)
    split_pair = None
    if q1 > 0 and q2 > 0:
        split_pair = min(
            (
                (fastest, cheapest)
                for fastest in quotes
                if can_supply(fastest, q1)
                for cheapest in quotes
                if cheapest.id != fastest.id and can_supply(cheapest, q2)
            ),
            key=lambda pair: (
                pair[0].delivery_days,
                pair[1].price * order_quantity(pair[1], q2) + (pair[1].delivery_fee or 0.0),
            ),
            default=None,
        )

    if split_pair is not None:
        split_fastest, split_cheapest = split_pair
        split_q1 = order_quantity(split_fastest, q1)
        split_q2 = order_quantity(split_cheapest, q2)
        split_cost = (
            split_fastest.price * split_q1
            + (split_fastest.delivery_fee or 0.0)
            + split_cheapest.price * split_q2
            + (split_cheapest.delivery_fee or 0.0)
        )
        split_delivery = max(
            split_fastest.delivery_days,
            split_cheapest.delivery_days,
        ) + payload.supplier_delay_days
        sup1 = split_fastest.supplier.name if split_fastest.supplier else split_fastest.supplier_name or "Unknown supplier"
        sup2 = split_cheapest.supplier.name if split_cheapest.supplier else split_cheapest.supplier_name or "Unknown supplier"
        options.append(
            SimulationOption(
                scenario_type="split_order",
                title="Split Order (Risk Mitigation)",
                supplier_name=f"{sup1} ({split_q1:g}) + {sup2} ({split_q2:g})",
                allocated_quantity=split_q1 + split_q2,
                unit_price=round(
                    (
                        split_fastest.price * split_q1
                        + split_cheapest.price * split_q2
                    )
                    / (split_q1 + split_q2),
                    2,
                ),
                delivery_fee=round((split_fastest.delivery_fee or 0.0) + (split_cheapest.delivery_fee or 0.0), 2),
                total_cost=round(split_cost, 2),
                delivery_days=split_delivery,
                residual_shortage_days=max(0.0, split_delivery - payload.max_delivery_days),
                explanation=f"Splits {split_q1:g} packs from {sup1} and {split_q2:g} from {sup2}. Full order arrives in {split_delivery:g} days.",
                feasibility_status=feasibility(split_cost, split_delivery),
                allocations=[
                    {
                        "supplier_name": sup1,
                        "quantity": split_q1,
                        "unit_price": split_fastest.price,
                        "delivery_fee": split_fastest.delivery_fee or 0.0,
                        "delivery_days": adjusted_delivery(split_fastest),
                    },
                    {
                        "supplier_name": sup2,
                        "quantity": split_q2,
                        "unit_price": split_cheapest.price,
                        "delivery_fee": split_cheapest.delivery_fee or 0.0,
                        "delivery_days": adjusted_delivery(split_cheapest),
                    },
                ],
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
