
from ai_engine.risk.shortage_risk import assess_shortage_risk

result = assess_shortage_risk(
    usable_stock=15,
    avg_daily_demand=5,
    supplier_lead_time_days=6,
    incoming_shipments=[],
)

for key, value in result.items():
    print(f"{key}: {value}")
