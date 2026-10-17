from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.config import settings

router = APIRouter(prefix="/system", tags=["System & Health"])


@router.get("/health")
def health_check(db: Annotated[Session, Depends(get_db)]):
    """
    Comprehensive system health check evaluating database connectivity,
    server operational state, and active Gmail API integration mode.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "gmail_mode": settings.GMAIL_MODE,
        "app_env": settings.APP_ENV,
        "version": settings.APP_VERSION,
    }


# Standalone lightweight health ping endpoint for load balancers
ping_router = APIRouter(tags=["Health"])

@ping_router.get("/health")
def ping():
    return {"status": "ok", "service": settings.APP_NAME}
