
from ai_engine.quotes.schemas import SupplierQuote


def validate_quote(quote: SupplierQuote) -> SupplierQuote:
    """
    Flag incomplete or questionable quotes.
    Never silently fill missing values or approve a purchase.
    """
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

    if quote.valid_until is None:
        quote.warning_flags.append("validity_not_provided")

    if quote.delivery_days is None:
        quote.warning_flags.append("delivery_time_unknown")

    if quote.missing_fields or quote.warning_flags:
        quote.review_status = "needs_review"
    else:
        quote.review_status = "validated"

    return quote
