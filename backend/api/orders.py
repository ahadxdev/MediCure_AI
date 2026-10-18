import json
import random
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db
from backend.models.entities import PurchaseOrder, AuditEvent, Medicine, Quotation, QuotationRequest
from backend.schemas.procurement import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderAction,
)

router = APIRouter(prefix="/orders", tags=["Purchase Orders & Human Sign-off"])


@router.get("", response_model=list[PurchaseOrderResponse])
def list_purchase_orders(db: Annotated[Session, Depends(get_db)]):
    """Retrieves all purchase orders with supplier and medicine details."""
    orders = (
        db.query(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.quotation)
            .joinedload(Quotation.request)
            .joinedload(QuotationRequest.medicine),
            joinedload(PurchaseOrder.quotation).joinedload(Quotation.supplier),
        )
        .order_by(PurchaseOrder.created_at.desc())
        .all()
    )
    results = []
    for o in orders:
        results.append(
            PurchaseOrderResponse(
                id=o.id,
                po_number=o.po_number,
                quotation_id=o.quotation_id,
                medicine_name=o.medicine_name or (
                    o.quotation.request.medicine.name
                    if o.quotation and o.quotation.request and o.quotation.request.medicine
                    else None
                ),
                pack_size=(
                    o.quotation.request.medicine.pack_size
                    if o.quotation and o.quotation.request and o.quotation.request.medicine
                    else None
                ),
                supplier_name=o.supplier_name or (
                    o.quotation.supplier.name if o.quotation and o.quotation.supplier else None
                ),
                quantity=o.quantity,
                unit_price=o.unit_price,
                delivery_fee=o.delivery_fee,
                total_amount=o.total_amount,
                status=o.status,
                approved_by=o.approved_by,
                approved_at=o.approved_at,
                created_at=o.created_at,
                delivery_estimate_days=o.delivery_estimate_days,
            )
        )
    return results


@router.post("", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create_draft_purchase_order(payload: PurchaseOrderCreate, db: Annotated[Session, Depends(get_db)]):
    """Creates a new Purchase Order in draft status awaiting human sign-off."""
    med = db.query(Medicine).filter(Medicine.id == payload.medicine_id).first()
    if med is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine '{payload.medicine_id}' not found",
        )
    po_number = f"PO-2026-{random.randint(1000, 9999)}"

    po = PurchaseOrder(
        quotation_id=payload.quotation_id,
        po_number=po_number,
        supplier_name=payload.supplier_name,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        delivery_fee=payload.delivery_fee,
        delivery_estimate_days=payload.delivery_estimate_days,
        total_amount=payload.total_amount,
        status="awaiting_approval",
    )
    db.add(po)
    db.flush()

    po.medicine_name = med.name
    db.flush()

    # Log audit event
    audit = AuditEvent(
        entity_type="purchase_order",
        entity_id=po.id,
        event_type="po_draft_created",
        actor="ProcurementEngine",
        payload=json.dumps({"po_number": po_number, "total_amount": payload.total_amount, "supplier": payload.supplier_name}),
    )
    db.add(audit)
    db.commit()
    db.refresh(po)

    return PurchaseOrderResponse(
        id=po.id,
        po_number=po.po_number,
        quotation_id=po.quotation_id,
        medicine_name=po.medicine_name,
        pack_size=med.pack_size,
        supplier_name=po.supplier_name,
        quantity=po.quantity,
        unit_price=po.unit_price,
        delivery_fee=po.delivery_fee,
        total_amount=po.total_amount,
        status=po.status,
        created_at=po.created_at,
        delivery_estimate_days=po.delivery_estimate_days,
    )


@router.post("/{order_id}/sign-off", response_model=PurchaseOrderResponse)
def sign_off_purchase_order(
    order_id: str,
    action: PurchaseOrderAction,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Mandatory Human Sign-off Gate: Approves or rejects a purchase order.
    No PO can be committed without explicit user action.
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Purchase order '{order_id}' not found")

    if po.status in ("approved", "dispatched", "rejected"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Order is already in state '{po.status}'")

    if action.approved:
        po.status = "approved"
        po.approved_by = action.actor_name
        po.approved_at = datetime.now(timezone.utc)
        event_type = "purchase_order_approved"
    else:
        po.status = "rejected"
        event_type = "purchase_order_rejected"

    audit = AuditEvent(
        entity_type="purchase_order",
        entity_id=po.id,
        event_type=event_type,
        actor=action.actor_name,
        payload=json.dumps({"po_number": po.po_number, "notes": action.notes}),
    )
    db.add(audit)
    db.commit()
    db.refresh(po)

    return PurchaseOrderResponse(
        id=po.id,
        po_number=po.po_number,
        quotation_id=po.quotation_id,
        medicine_name=po.medicine_name,
        supplier_name=po.supplier_name,
        quantity=po.quantity,
        unit_price=po.unit_price,
        delivery_fee=po.delivery_fee,
        total_amount=po.total_amount,
        status=po.status,
        approved_by=po.approved_by,
        approved_at=po.approved_at,
        created_at=po.created_at,
        delivery_estimate_days=po.delivery_estimate_days,
    )
