from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import init_db
from backend.api import (
    health_router,
    ping_router,
    inventory_router,
    suppliers_router,
    risk_router,
    quotes_router,
    procurement_router,
    orders_router,
    audit_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for database initialization and cleanup."""
    init_db()
    yield


app = FastAPI(
    title="MediProcure AI — API Gateway",
    description=(
        "Healthcare procurement decision-support backend for independent pharmacies. "
        "Deterministic shortage risk engine, Gmail quotation agent, and procurement simulator."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under standard prefix /api
app.include_router(ping_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(suppliers_router, prefix="/api")
app.include_router(risk_router, prefix="/api")
app.include_router(quotes_router, prefix="/api")
app.include_router(procurement_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(audit_router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": "/docs",
        "health": "/api/system/health",
    }
