import json
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth import require_api_key_strict
from backend.models.entities import AuditEvent
from backend.schemas.procurement import AuditEventResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail & Governance"])


@router.get(
    "/logs",
    response_model=list[AuditEventResponse],
    dependencies=[Depends(require_api_key_strict)],
)
def list_audit_logs(
    db: Annotated[Session, Depends(get_db)],
    entity_type: str | None = Query(default=None, description="Filter by entity type"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Retrieves chronological immutable audit logs with optional filtering."""
    query = db.query(AuditEvent)
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)

    events = query.order_by(AuditEvent.timestamp.desc()).limit(limit).all()
    results = []
    for e in events:
        parsed_payload = None
        if e.payload:
            try:
                parsed_payload = json.loads(e.payload)
            except Exception:
                parsed_payload = {"raw": e.payload}

        results.append(
            AuditEventResponse(
                id=e.id,
                entity_type=e.entity_type,
                entity_id=e.entity_id,
                event_type=e.event_type,
                actor=e.actor,
                timestamp=e.timestamp,
                payload=parsed_payload,
            )
        )
    return results
