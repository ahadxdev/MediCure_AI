
from datetime import date

from ai_engine.quotes.schemas import SupplierQuote


def validate_quote(
    quote: SupplierQuote,
    as_of: date | None = None,
) -> SupplierQuote:
    """
    Validate basic quote fields and expiry.

    as_of is injectable for deterministic tests.
    Missing validity is a warning; expired or ambiguous validity
    requires review. This does not verify supplier authenticity.
    """
    today = as_of or date.today()

    quote.missing_fields = []
    quote.warning_flags = []

    required_fields = [
        "supplier_name",
        "medicine_name",
        "strength",
        "dosage_form",
        "pack_size",
        "price",
        "price_unit",
        "currency",
        "quoted_quantity",
        "delivery_days",
    ]

    for field in required_fields:
        if getattr(quote, field) is None:
            quote.missing_fields.append(field)

    if quote.price is not None and quote.price <= 0:
        quote.warning_flags.append("invalid_price")

    if quote.delivery_fee is not None and quote.delivery_fee < 0:
        quote.warning_flags.append("invalid_delivery_fee")

    if (
        quote.minimum_order_quantity is not None
        and quote.quoted_quantity is not None
        and quote.minimum_order_quantity > quote.quoted_quantity
    ):
        quote.warning_flags.append("quoted_quantity_below_moq")

    if not quote.valid_until:
        quote.warning_flags.append("validity_not_provided")
    else:
        try:
            expiry_date = date.fromisoformat(quote.valid_until.strip())
            if expiry_date < today:
                quote.warning_flags.append("quote_expired")
        except (ValueError, AttributeError):
            quote.warning_flags.append("validity_date_unrecognized")

    if quote.delivery_days is None:
        quote.warning_flags.append("delivery_time_unknown")

    blocking_flags = {
        "invalid_price",
        "invalid_delivery_fee",
        "quoted_quantity_below_moq",
        "quote_expired",
        "validity_date_unrecognized",
    }

    if quote.missing_fields or any(
        flag in blocking_flags for flag in quote.warning_flags
    ):
        quote.review_status = "needs_review"
    else:
        quote.review_status = "validated"

    return quote
