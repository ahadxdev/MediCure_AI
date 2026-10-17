from backend.api.health import router as health_router, ping_router
from backend.api.inventory import router as inventory_router
from backend.api.risk import router as risk_router

__all__ = [
    "health_router",
    "ping_router",
    "inventory_router",
    "risk_router",
]
