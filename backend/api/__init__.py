from backend.api.health import router as health_router, ping_router
from backend.api.inventory import router as inventory_router
from backend.api.suppliers import router as suppliers_router
from backend.api.risk import router as risk_router
from backend.api.quotes import router as quotes_router
from backend.api.procurement import router as procurement_router
from backend.api.orders import router as orders_router
from backend.api.audit import router as audit_router
from backend.api.sales import router as sales_router

__all__ = [
    "health_router",
    "ping_router",
    "inventory_router",
    "suppliers_router",
    "risk_router",
    "quotes_router",
    "procurement_router",
    "orders_router",
    "audit_router",
    "sales_router",
]
