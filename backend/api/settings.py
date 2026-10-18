from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth import require_api_key
from backend.database import get_db
from backend.models.entities import AppSetting
from backend.schemas.procurement import AppSettingsResponse, AppSettingsUpdate

router = APIRouter(prefix="/settings", tags=["Application Settings"])
DEFAULTS = {
    "dispensary_name": "Shifa Central Pharmacy",
    "dispensary_city": "Islamabad",
    "reorder_threshold_days": "4",
}


def _read(db: Session) -> AppSettingsResponse:
    values = DEFAULTS.copy()
    for item in db.query(AppSetting).filter(AppSetting.key.in_(DEFAULTS)).all():
        values[item.key] = item.value
    return AppSettingsResponse(
        dispensary_name=values["dispensary_name"],
        dispensary_city=values["dispensary_city"],
        reorder_threshold_days=float(values["reorder_threshold_days"]),
    )


@router.get("", response_model=AppSettingsResponse)
def get_settings(db: Annotated[Session, Depends(get_db)]):
    return _read(db)


@router.put("", response_model=AppSettingsResponse, dependencies=[Depends(require_api_key)])
def update_settings(payload: AppSettingsUpdate, db: Annotated[Session, Depends(get_db)]):
    for key, value in payload.model_dump().items():
        item = db.get(AppSetting, key)
        if item is None:
            db.add(AppSetting(key=key, value=str(value)))
        else:
            item.value = str(value)
    db.commit()
    return _read(db)

