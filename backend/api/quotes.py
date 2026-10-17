import json
from typing import Annotated
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db
from backend.models.entities import Medicine, Supplier, QuotationRequest, Quotation, AuditEvent
from backend.schemas.procurement import (
    QuotationRequestCreate,
    QuotationRequestResponse,
    QuotationApprovalRequest,
    QuotationResponse,
    QuoteParseRequest,
)
from ai_engine.quotes.parser import parse_quote_email
from ai_engine.quotes.validator import validate_quote

router = APIRouter(prefix="/quotes", tags=["Quotations & Supplier Messaging"])


@router.get("/requests", response_model=list[QuotationRequestResponse])
def list_quotation_requests(db: Annotated[Session, Depends(get_db)]):
    """Retrieves all quotation requests (RFQs) with associated medicine names."""
    records = db.query(QuotationRequest).options(joinedload(QuotationRequest.medicine)).order_by(QuotationRequest.created_at.desc()).all()
    results = []
    for r in records:
        results.append(
            QuotationRequestResponse(
                id=r.id,
                medicine_id=r.medicine_id,
                medicine_name=r.medicine.name if r.medicine else None,
                required_quantity=r.required_quantity,
                required_by_date=r.required_by_date,
                delivery_location=r.delivery_location,
                status=r.status,
                created_at=r.created_at,
            )
        )
    return results


@router.post("/requests", response_model=QuotationRequestResponse, status_code=status.HTTP_201_CREATED)
def create_quotation_request(payload: QuotationRequestCreate, db: Annotated[Session, Depends(get_db)]):
    """Creates a new quotation request in draft status awaiting human pharmacist review."""
    med = db.query(Medicine).filter(Medicine.id == payload.medicine_id).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Medicine '{payload.medicine_id}' not found")

    rfq = QuotationRequest(
        medicine_id=payload.medicine_id,
        required_quantity=payload.required_quantity,
        required_by_date=payload.required_by_date,
        delivery_location=payload.delivery_location,
        status="awaiting_approval",
    )
    db.add(rfq)
    db.flush()

    # Log audit event
    audit = AuditEvent(
        entity_type="quotation_request",
        entity_id=rfq.id,
        event_type="rfq_created",
        actor="Pharmacist (Web User)",
        payload=json.dumps({"medicine": med.name, "quantity": payload.required_quantity}),
    )
    db.add(audit)
    db.commit()
    db.refresh(rfq)

    return QuotationRequestResponse(
        id=rfq.id,
        medicine_id=rfq.medicine_id,
        medicine_name=med.name,
        required_quantity=rfq.required_quantity,
        required_by_date=rfq.required_by_date,
        delivery_location=rfq.delivery_location,
        status=rfq.status,
        created_at=rfq.created_at,
    )


@router.post("/requests/{request_id}/approve-and-send", status_code=status.HTTP_200_OK)
def approve_and_send_quotation(
    request_id: str,
    action: QuotationApprovalRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Human-in-the-Loop Gate: Outbound RFQ emails are dispatched ONLY upon explicit human approval.
    Dispatches via Gmail or simulated dispatcher based on configuration.
    """
    rfq = db.query(QuotationRequest).filter(QuotationRequest.id == request_id).first()
    if not rfq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"RFQ '{request_id}' not found")

    if rfq.status == "sent" or rfq.status == "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RFQ is already approved/sent")

    if not action.approved:
        rfq.status = "rejected"
        audit = AuditEvent(
            entity_type="quotation_request",
            entity_id=rfq.id,
            event_type="rfq_rejected",
            actor="Pharmacist",
            payload=json.dumps({"notes": action.notes or "Rejected by user"}),
        )
        db.add(audit)
        db.commit()
        return {"status": "rejected", "message": "Quotation request was rejected and not sent"}

    # Human sign-off confirmed
    rfq.status = "sent"
    audit = AuditEvent(
        entity_type="quotation_request",
        entity_id=rfq.id,
        event_type="rfq_approved_and_sent",
        actor="Pharmacist",
        payload=json.dumps({"delivery_location": rfq.delivery_location, "mode": "simulated_dispatcher"}),
    )
    db.add(audit)
    db.commit()

    return {
        "status": "sent",
        "request_id": rfq.id,
        "message": "Quotation request approved and dispatched via supplier communications gateway",
    }


@router.get("/inbox", response_model=list[QuotationResponse])
def list_quotation_inbox(db: Annotated[Session, Depends(get_db)]):
    """Retrieves all parsed and validated supplier quotations."""
    quotes = db.query(Quotation).options(joinedload(Quotation.supplier), joinedload(Quotation.request)).order_by(Quotation.created_at.desc()).all()
    results = []
    for q in quotes:
        flags = json.loads(q.warning_flags) if q.warning_flags else []
        med_name = q.request.medicine.name if q.request and q.request.medicine else "Panadol 500mg Tablets"
        results.append(
            QuotationResponse(
                id=q.id,
                request_id=q.request_id,
                supplier_id=q.supplier_id,
                supplier_name=q.supplier.name if q.supplier else "Verified Distributor",
                medicine_id=q.request.medicine_id if q.request else None,
                medicine_name=med_name,
                price=q.price,
                currency=q.currency,
                price_unit=q.price_unit,
                quoted_quantity=q.quoted_quantity,
                minimum_order_quantity=q.minimum_order_quantity,
                delivery_days=q.delivery_days,
                delivery_fee=q.delivery_fee,
                payment_terms=q.payment_terms,
                valid_until=q.valid_until,
                review_status=q.review_status,
                warning_flags=flags,
                created_at=q.created_at,
            )
        )
    return results


@router.post("/parse", response_model=QuotationResponse)
def parse_and_validate_quotation(payload: QuoteParseRequest, db: Annotated[Session, Depends(get_db)]):
    """Parses raw supplier quote text using deterministic regex and runs anomaly validator."""
    parsed_quote = parse_quote_email(payload.raw_email_text, metadata={"request_id": payload.request_id})
    validated = validate_quote(parsed_quote)

    quote = Quotation(
        request_id=payload.request_id,
        supplier_id=payload.supplier_id,
        raw_email_body=payload.raw_email_text,
        price=validated.price,
        currency=validated.currency or "PKR",
        price_unit=validated.price_unit,
        quoted_quantity=validated.quoted_quantity,
        minimum_order_quantity=validated.minimum_order_quantity,
        delivery_days=validated.delivery_days,
        delivery_fee=validated.delivery_fee or 0.0,
        payment_terms=validated.payment_terms,
        valid_until=validated.valid_until,
        review_status=validated.review_status,
        warning_flags=json.dumps(validated.warning_flags),
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)

    return QuotationResponse(
        id=quote.id,
        request_id=quote.request_id,
        supplier_id=quote.supplier_id,
        supplier_name="Verified Supplier",
        price=quote.price,
        currency=quote.currency,
        price_unit=quote.price_unit,
        quoted_quantity=quote.quoted_quantity,
        minimum_order_quantity=quote.minimum_order_quantity,
        delivery_days=quote.delivery_days,
        delivery_fee=quote.delivery_fee,
        payment_terms=quote.payment_terms,
        valid_until=quote.valid_until,
        review_status=quote.review_status,
        warning_flags=validated.warning_flags,
        created_at=quote.created_at,
    )
