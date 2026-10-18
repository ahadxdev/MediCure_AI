from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import require_api_key
from backend.services.demo_sales import add_demo_sales_data

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("/demo-data")
def create_demo_sales_data(db: Annotated[Session, Depends(get_db)], _: Annotated[str, Depends(require_api_key)]) -> dict:
    """Adds clearly marked, idempotent synthetic sales for registered catalog medicines."""
    return add_demo_sales_data(db)
