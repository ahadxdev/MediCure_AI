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


def test_parse_html_supplier_quote_from_table_email():
    email = """
    <html><body><table>
      <tr><td>Medicine</td><td>Paracetamol</td></tr>
      <tr><td>Strength</td><td>500 mg</td></tr>
      <tr><td>Form</td><td>Tablets</td></tr>
      <tr><td>Pack</td><td>100 tablets</td></tr>
      <tr><td>Price</td><td>PKR 120 per box</td></tr>
      <tr><td>Quantity</td><td>10</td></tr>
      <tr><td>MOQ</td><td>5</td></tr>
      <tr><td>Delivery</td><td>2 business days</td></tr>
      <tr><td>Payment</td><td>Cash on delivery</td></tr>
    </table></body></html>
    """

    quote = parse_quote_email(
        email,
        metadata={"supplier_name": "HTML Supplier"},
    )
    validated = validate_quote(quote)

    assert quote.medicine_name == "Paracetamol"
    assert quote.price == 120
    assert quote.currency == "PKR"
    assert quote.price_unit == "box"
    assert quote.quoted_quantity == 10
    assert quote.delivery_days == 2
    assert validated.review_status == "validated"


def test_parse_natural_language_supplier_reply():
    email = """
    Dear team,
    Thank you for your RFQ. We can supply Panadol Extra 500 mg tablets.
    Pack size: 100 tablets
    Our best price is PKR 160 per strip.
    Available quantity: 50
    MOQ: 20
    Lead time: 4 business days
    Valid until: 2026-12-31
    """

    quote = parse_quote_email(email, metadata={"supplier_name": "Wholesale Pharma"})
    validated = validate_quote(quote)

    assert quote.medicine_name.startswith("Panadol Extra")
    assert quote.strength == "500 mg"
    assert quote.dosage_form == "tablets"
    assert quote.price == 160
    assert quote.currency == "PKR"
    assert quote.price_unit == "strip"
    assert quote.quoted_quantity == 50
    assert quote.delivery_days == 4
    assert validated.review_status == "validated"
