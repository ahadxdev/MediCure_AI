from ai_engine.quotes.parser import parse_quote_email
from ai_engine.quotes.validator import validate_quote


def test_parse_complete_labelled_quote():
    email = """
    Medicine: Paracetamol
    Strength: 500 mg
    Form: Tablet
    Pack: 100 tablets
    Price: PKR 120 / box
    Quantity: 10
    MOQ: 5
    Delivery: 2 days
    Delivery fee: PKR 200
    Payment terms: Cash on delivery
    Valid until: 2026-10-20
    """

    quote = parse_quote_email(
        email,
        metadata={
            "supplier_name": "Demo Supplier",
            "request_id": "REQ-001",
            "thread_id": "thread-001",
            "message_id": "message-001",
        },
    )

    assert quote.medicine_name == "Paracetamol"
    assert quote.price == 120
    assert quote.currency == "PKR"
    assert quote.price_unit == "box"
    assert quote.quoted_quantity == 10
    assert quote.delivery_days == 2
    assert quote.thread_id == "thread-001"

    validated = validate_quote(quote)

    assert validated.review_status == "validated"
    assert validated.missing_fields == []


def test_missing_fields_require_review():
    quote = parse_quote_email(
        "Hello, we can supply the requested product.",
        metadata={"supplier_name": "Demo Supplier"},
    )

    validated = validate_quote(quote)

    assert validated.review_status == "needs_review"
    assert "price" in validated.missing_fields
    assert "medicine_name" in validated.missing_fields


def test_moq_warning():
    email = """
    Medicine: Paracetamol
    Strength: 500 mg
    Form: Tablet
    Pack: 100 tablets
    Price: PKR 120 / box
    Quantity: 3
    MOQ: 5
    Delivery: 2 days
    """

    quote = parse_quote_email(
        email,
        metadata={"supplier_name": "Demo Supplier"},
    )
    validated = validate_quote(quote)

    assert "quoted_quantity_below_moq" in validated.warning_flags
    assert validated.review_status == "needs_review"
