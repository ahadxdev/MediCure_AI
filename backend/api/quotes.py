import json
import re
from email.utils import parseaddr
from typing import Annotated
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db
from backend.auth import require_api_key, require_api_key_strict
from backend.models.entities import (
    Medicine,
    Supplier,
    QuotationRequest,
    Quotation,
    AuditEvent,
    InventoryRecord,
    SalesRecord,
    QuotationRequestRecipient,
)
from backend.schemas.procurement import (
    QuotationRequestCreate,
    QuotationRequestResponse,
    QuotationApprovalRequest,
    QuotationResponse,
    QuoteParseRequest,
    QuoteInboxSyncRequest,
    QuoteInboxSyncResponse,
)
from ai_engine.gmail.client import fetch_supplier_replies, extract_pdf_text
from ai_engine.agent.graph import build_agent, prepare_quote_request, resume_agent
from ai_engine.quotes.agent import process_supplier_reply
from ai_engine.quotes.parser import parse_quote_email
from ai_engine.quotes.validator import validate_quote
from backend.config import settings

router = APIRouter(prefix="/quotes", tags=["Quotations & Supplier Messaging"])


def _agent_state_for_request(rfq: QuotationRequest, db: Session) -> dict:
    medicine = rfq.medicine
    if medicine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")

    recipient_ids = [item.supplier_id for item in rfq.recipients]
    suppliers = db.query(Supplier).filter(
        Supplier.is_verified.is_(True), Supplier.id.in_(recipient_ids)
    ).order_by(Supplier.name.asc()).all() if recipient_ids else []
    if not suppliers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verified suppliers are available for this RFQ",
        )

    inventory = (
        db.query(InventoryRecord)
        .filter(InventoryRecord.medicine_id == medicine.id)
        .first()
    )
    cutoff = date.today() - timedelta(days=30)
    sales = (
        db.query(
            func.sum(SalesRecord.quantity_dispensed),
            func.count(func.distinct(SalesRecord.sale_date)),
        )
        .filter(SalesRecord.medicine_id == medicine.id, SalesRecord.sale_date >= cutoff)
        .first()
    )
    avg_demand = (sales[0] or 0.0) / max(1, sales[1] or 0)
    lead_times = [
        supplier.default_lead_time_days
        for supplier in suppliers
        if supplier.default_lead_time_days is not None
    ]

    return {
        "request_id": rfq.id,
        "medicine_name": medicine.name,
        "strength": medicine.strength,
        "dosage_form": medicine.dosage_form,
        "pack_size": medicine.pack_size,
        "usable_stock": inventory.usable_stock if inventory else 0.0,
        "avg_daily_demand": avg_demand,
        "supplier_lead_time_days": min(lead_times) if lead_times else None,
        "required_quantity": rfq.required_quantity,
        "delivery_location": rfq.delivery_location or "",
        "required_by_date": str(rfq.required_by_date or date.today()),
        "supplier_emails": [supplier.email for supplier in suppliers],
        "force_rfq": True,
    }


@router.get(
    "/requests",
    response_model=list[QuotationRequestResponse],
    dependencies=[Depends(require_api_key_strict)],
)
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
                supplier_ids=[item.supplier_id for item in r.recipients],
            )
        )
    return results


@router.post("/requests", response_model=QuotationRequestResponse, status_code=status.HTTP_201_CREATED)
def create_quotation_request(payload: QuotationRequestCreate, db: Annotated[Session, Depends(get_db)], _: Annotated[str, Depends(require_api_key)]):
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

    supplier_query = db.query(Supplier).filter(Supplier.is_verified.is_(True))
    suppliers = supplier_query.filter(Supplier.id.in_(payload.supplier_ids)).all() if payload.supplier_ids else supplier_query.all()
    if not suppliers:
        raise HTTPException(status_code=400, detail="At least one verified supplier must be selected")
    if payload.supplier_ids and len(suppliers) != len(set(payload.supplier_ids)):
        raise HTTPException(status_code=400, detail="One or more selected suppliers are invalid or unverified")
    for supplier in suppliers:
        db.add(QuotationRequestRecipient(request_id=rfq.id, supplier_id=supplier.id))

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
        supplier_ids=[supplier.id for supplier in suppliers],
    )


@router.get(
    "/requests/{request_id}/draft",
    dependencies=[Depends(require_api_key_strict)],
)
def get_quotation_email_draft(
    request_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    """Prepares a supplier email for review without sending or changing request state."""
    rfq = db.query(QuotationRequest).filter(QuotationRequest.id == request_id).first()
    if rfq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")
    state = _agent_state_for_request(rfq, db)
    draft = prepare_quote_request(state)["email_draft"]
    return {**draft, "mode": settings.GMAIL_MODE}


@router.post("/requests/{request_id}/approve-and-send", status_code=status.HTTP_200_OK)
def approve_and_send_quotation(
    request_id: str,
    action: QuotationApprovalRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(require_api_key)],
):
    """
    Human-in-the-Loop Gate: Outbound RFQ emails are dispatched ONLY upon explicit human approval.
    Dispatches via Gmail or simulated dispatcher based on configuration.
    """
    rfq = db.query(QuotationRequest).filter(QuotationRequest.id == request_id).first()
    if not rfq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"RFQ '{request_id}' not found")

    if rfq.status in {"sent", "approved", "simulated", "partially_sent"}:
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

    agent_state = _agent_state_for_request(rfq, db)
    graph = build_agent()
    graph_config = {"configurable": {"thread_id": f"rfq-{rfq.id}"}}
    graph.invoke(agent_state, config=graph_config)
    result = resume_agent(graph, approved=True, config=graph_config)
    email_status = result.get("email_status", "send_failed")
    sent_recipients = [
        message.get("recipient")
        for message in result.get("gmail_messages", [])
        if message.get("status") in {"sent", "simulated"}
    ]
    mode = "LIVE" if settings.GMAIL_MODE == "LIVE" else "SIMULATED"
    if email_status == "sent":
        rfq.status = "sent"
    elif email_status == "partially_sent":
        rfq.status = "partially_sent"
    elif email_status == "simulated":
        rfq.status = "simulated"

    audit = AuditEvent(
        entity_type="quotation_request",
        entity_id=rfq.id,
        event_type=f"rfq_{email_status}",
        actor="Pharmacist",
        payload=json.dumps({
            "delivery_location": rfq.delivery_location,
            "mode": mode,
            "recipients": sent_recipients,
            "error": result.get("email_error"),
        }),
    )
    db.add(audit)
    db.commit()

    if email_status == "send_failed":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result.get("email_error") or "Email dispatch failed. The RFQ remains pending approval.",
        )

    return {
        "status": email_status,
        "mode": mode,
        "request_id": rfq.id,
        "recipients": sent_recipients,
        "error": result.get("email_error"),
        "message": (
            "RFQ email sent through Gmail"
            if email_status == "sent"
            else "RFQ approved in simulated mode; no email was sent"
            if email_status == "simulated"
            else "RFQ was partially sent; review the audit details before retrying"
        ),
    }


@router.get(
    "/inbox",
    response_model=list[QuotationResponse],
    dependencies=[Depends(require_api_key_strict)],
)
def list_quotation_inbox(db: Annotated[Session, Depends(get_db)]):
    """Retrieves all parsed and validated supplier quotations."""
    quotes = db.query(Quotation).options(joinedload(Quotation.supplier), joinedload(Quotation.request)).order_by(Quotation.created_at.desc()).all()
    results = []
    for q in quotes:
        flags = json.loads(q.warning_flags) if q.warning_flags else []
        med_name = (
            q.request.medicine.name
            if q.request and q.request.medicine
            else q.medicine_name
        )
        results.append(
            QuotationResponse(
                id=q.id,
                request_id=q.request_id,
                supplier_id=q.supplier_id,
                supplier_name=q.supplier.name if q.supplier else q.supplier_name,
                medicine_id=q.request.medicine_id if q.request else None,
                medicine_name=med_name,
                source_email=q.source_email,
                source_thread_id=q.source_thread_id,
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
def parse_and_validate_quotation(payload: QuoteParseRequest, db: Annotated[Session, Depends(get_db)], _: Annotated[str, Depends(require_api_key)]):
    """Parses raw supplier quote text using deterministic regex and runs anomaly validator."""
    request = (
        db.query(QuotationRequest).filter(QuotationRequest.id == payload.request_id).first()
        if payload.request_id
        else None
    )
    if payload.request_id and request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation request not found")

    supplier = (
        db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()
        if payload.supplier_id
        else None
    )
    if payload.supplier_id and supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    parsed_quote = parse_quote_email(
        payload.raw_email_text,
        metadata={
            "request_id": payload.request_id,
            "supplier_name": supplier.name if supplier else None,
            "medicine_name": request.medicine.name if request and request.medicine else None,
        },
    )
    validated = validate_quote(parsed_quote)
    warning_flags = list(validated.warning_flags)
    review_status = validated.review_status
    if not supplier or not supplier.is_verified:
        warning_flags.append("supplier_unverified")
        review_status = "needs_review"

    quote = Quotation(
        request_id=payload.request_id,
        supplier_id=payload.supplier_id,
        supplier_name=supplier.name if supplier else None,
        medicine_name=request.medicine.name if request and request.medicine else validated.medicine_name,
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
        review_status=review_status,
        warning_flags=json.dumps(sorted(set(warning_flags))),
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)

    return QuotationResponse(
        id=quote.id,
        request_id=quote.request_id,
        supplier_id=quote.supplier_id,
        supplier_name=supplier.name if supplier else quote.supplier_name,
        medicine_id=request.medicine_id if request else None,
        medicine_name=request.medicine.name if request and request.medicine else quote.medicine_name,
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
        warning_flags=sorted(set(warning_flags)),
        created_at=quote.created_at,
    )


@router.post("/inbox/sync", response_model=QuoteInboxSyncResponse)
def sync_supplier_reply_inbox(
    payload: QuoteInboxSyncRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(require_api_key)],
):
    """Pulls new Gmail supplier replies, parses them, and stores valid quote records."""
    try:
        if settings.GMAIL_MODE == "LIVE":
            emails = fetch_supplier_replies(payload.query, max_results=payload.max_results)
        else:
            # Deterministic, explicitly simulated replies make the offline demo
            # exercise the same parser/deduplication path as LIVE Gmail.
            emails = []
            active_requests = db.query(QuotationRequest).filter(
                QuotationRequest.status.in_(("sent", "simulated", "partially_sent"))
            ).all()
            for request in active_requests:
                medicine = request.medicine
                for recipient in request.recipients:
                    supplier = recipient.supplier
                    if not supplier or not medicine:
                        continue
                    emails.append({
                        "message_id": f"simulated-{request.id}-{supplier.id}",
                        "thread_id": f"simulated-thread-{request.id}",
                        "from": f"{supplier.name} <{supplier.email}>",
                        "subject": f"Re: RFQ {request.id} - {medicine.name}",
                        "body": (
                            f"Medicine: {medicine.name}\nStrength: {medicine.strength}\n"
                            f"Form: {medicine.dosage_form}\nPack: {medicine.pack_size}\n"
                            f"Price: PKR 480 / pack\nQuantity: {max(request.required_quantity, 40)}\n"
                            f"MOQ: 10\nDelivery: {supplier.default_lead_time_days or 3:g} days\n"
                            "Payment terms: Simulated COD\nValid until: 2099-12-31\n"
                        ),
                    })
    except (FileNotFoundError, ValueError, GoogleAuthError, HttpError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    scanned = 0
    imported = 0
    duplicates = 0
    ignored = 0

    for email in emails:
        scanned += 1
        source_message_id = email.get("message_id")
        if not source_message_id:
            ignored += 1
            continue

        existing = db.query(Quotation).filter(Quotation.source_message_id == source_message_id).first()
        if existing:
            duplicates += 1
            continue

        sender_name, sender_email = parseaddr(email.get("from", ""))
        supplier_name = sender_name or sender_email or "Unknown Supplier"

        matched_request = None
        active_requests = (
            db.query(QuotationRequest)
            .filter(QuotationRequest.status.in_(("sent", "simulated", "partially_sent")))
            .all()
        )
        reference = re.search(
            r"\bRFQ[\s:#-]+([A-Za-z0-9-]+)",
            email.get("subject", ""),
            flags=re.IGNORECASE,
        )
        if reference:
            matched_request = next(
                (request for request in active_requests if request.id == reference.group(1)),
                None,
            )
        if not matched_request:
            ignored += 1
            continue

        email_text = email.get("body", "")
        attachment_warnings = []
        for attachment in email.get("attachments", []):
            try:
                email_text += "\n" + extract_pdf_text(attachment["data"])
            except (ValueError, RuntimeError) as exc:
                attachment_warnings.append(f"attachment_not_processed:{attachment.get('filename', 'unknown')}")
        result = process_supplier_reply(
            email_text=email_text,
            request={
                "medicine_name": matched_request.medicine.name if matched_request.medicine else None,
                "strength": matched_request.medicine.strength if matched_request.medicine else None,
                "dosage_form": matched_request.medicine.dosage_form if matched_request.medicine else None,
                "pack_size": matched_request.medicine.pack_size if matched_request.medicine else None,
                "required_quantity": matched_request.required_quantity,
            },
            metadata={
                "request_id": matched_request.id,
                "thread_id": email.get("thread_id"),
                "message_id": source_message_id,
                "supplier_name": supplier_name,
            },
        )

        quote_data = result.get("quote", {})
        if not email.get("body", "").strip():
            ignored += 1
            continue

        normalized_email = sender_email.strip().lower()
        supplier = (
            db.query(Supplier)
            .filter(func.lower(Supplier.email) == normalized_email)
            .first()
            if normalized_email
            else None
        )
        if supplier is None and "@" in normalized_email:
            supplier = Supplier(
                name=supplier_name,
                email=normalized_email,
                phone=None,
                address=None,
                is_verified=False,
            )
            db.add(supplier)
            db.flush()

        warning_flags = list(result.get("warnings", [])) + attachment_warnings
        if not supplier or not supplier.is_verified:
            warning_flags.append("supplier_unverified")
        review_status = quote_data.get("review_status") or "needs_review"
        if not result.get("ready_for_comparison") or not supplier or not supplier.is_verified:
            review_status = "needs_review"

        quote = Quotation(
            request_id=matched_request.id,
            supplier_id=supplier.id if supplier else None,
            supplier_name=supplier_name,
            medicine_name=quote_data.get("medicine_name"),
            source_message_id=source_message_id,
            source_thread_id=email.get("thread_id"),
            source_email=sender_email,
            raw_email_body=email.get("body", ""),
            price=quote_data.get("price"),
            currency=quote_data.get("currency") or "PKR",
            price_unit=quote_data.get("price_unit"),
            quoted_quantity=quote_data.get("quoted_quantity"),
            minimum_order_quantity=quote_data.get("minimum_order_quantity"),
            delivery_days=quote_data.get("delivery_days"),
            delivery_fee=quote_data.get("delivery_fee") or 0.0,
            payment_terms=quote_data.get("payment_terms"),
            valid_until=quote_data.get("valid_until"),
            review_status=review_status,
            warning_flags=json.dumps(sorted(set(warning_flags))),
        )
        db.add(quote)
        try:
            db.commit()
            imported += 1
        except IntegrityError:
            db.rollback()
            duplicates += 1

    return QuoteInboxSyncResponse(
        scanned=scanned,
        imported=imported,
        duplicates=duplicates,
        ignored=ignored,
        mode=settings.GMAIL_MODE,
    )
