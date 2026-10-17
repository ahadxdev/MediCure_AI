from typing import Any
from ai_engine.risk.shortage_risk import assess_shortage_risk
from backend.schemas.risk import RiskAssessmentRequest, RiskAssessmentResponse


def evaluate_risk(request: RiskAssessmentRequest) -> RiskAssessmentResponse:
    """
    Evaluates shortage risk deterministically using the core math engine.
    Converts Pydantic request models into the engine parameter format,
    runs deterministic simulation, and returns a validated response schema.
    """
    shipments = [
        {"quantity": s.quantity, "days_until_arrival": s.days_until_arrival}
        for s in request.incoming_shipments
    ]
    
    raw_result: dict[str, Any] = assess_shortage_risk(
        usable_stock=request.usable_stock,
        avg_daily_demand=request.avg_daily_demand,
        supplier_lead_time_days=request.supplier_lead_time_days,
        incoming_shipments=shipments,
    )
    
    return RiskAssessmentResponse(**raw_result)
