
from datetime import date

from ai_engine.quotes.parser import parse_quote_email
from ai_engine.quotes.validator import validate_quote


def make_quote(valid_until: str | None):
    email = """
    Medicine: Paracetamol
    Strength: 500 mg
    Form: Tablet
    Pack: 100 tablets
    Price: PKR 120 / box
    Quantity: 10
    MOQ: 5
    Delivery: 2 days
    """

    if valid_until:
        email += f"\nValid until: {valid_until}\n"

    return parse_quote_email(
        email,
        metadata={"supplier_name": "Demo Supplier"},
    )


def test_expired_quote_requires_review():
    quote = make_quote("2026-10-16")

    result = validate_quote(quote, as_of=date(2026, 10, 17))

    assert "quote_expired" in result.warning_flags
    assert result.review_status == "needs_review"


def test_quote_valid_through_expiry_date():
    quote = make_quote("2026-10-17")

    result = validate_quote(quote, as_of=date(2026, 10, 17))

    assert "quote_expired" not in result.warning_flags
    assert result.review_status == "validated"


def test_missing_validity_is_flagged():
    quote = make_quote(None)

    result = validate_quote(quote, as_of=date(2026, 10, 17))

    assert "validity_not_provided" in result.warning_flags
    assert result.review_status == "validated"


def test_unrecognized_validity_requires_review():
    quote = make_quote("next Tuesday")

    result = validate_quote(quote, as_of=date(2026, 10, 17))

    assert "validity_date_unrecognized" in result.warning_flags
    assert result.review_status == "needs_review"
