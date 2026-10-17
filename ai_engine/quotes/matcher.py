from typing import Any
from ai_engine.quotes.schemas import SupplierQuote

def match_quote_to_request(
    quote: SupplierQuote,
    request: dict[str, Any],
) -> dict[str, Any]:
    """
    Compare a parsed supplier quote against the original request.

    Missing fields are treated as unverified, not as matches.
    A mismatch prevents automatic eligibility.
    """
    fields = [
        "medicine_name",
        "strength",
        "dosage_form",
        "pack_size",
    ]

    matches: dict[str, bool | None] = {}
    mismatches: list[str] = []
    unverified: list[str] = []

    for field in fields:
        quoted_value = getattr(quote, field, None)
        requested_value = request.get(field)

        if not requested_value or not quoted_value:
            matches[field] = None
            unverified.append(field)
            continue

        # Conservative normalization: ignore case and extra whitespace,
        # but do not assume different strengths or pack sizes are equivalent.
        normalized_quote = " ".join(str(quoted_value).casefold().split())
        normalized_request = " ".join(str(requested_value).casefold().split())

        is_match = normalized_quote == normalized_request
        matches[field] = is_match

        if not is_match:
            mismatches.append(field)

    required_quantity = request.get("required_quantity")
    quoted_quantity = quote.quoted_quantity
    moq = quote.minimum_order_quantity

    quantity_warnings: list[str] = []

    if required_quantity is None:
        quantity_warnings.append("required_quantity_missing")
    elif quoted_quantity is None:
        quantity_warnings.append("quoted_quantity_missing")
    elif quoted_quantity < required_quantity:
        quantity_warnings.append("quoted_quantity_below_requirement")

    if required_quantity is not None and moq is not None:
        if moq > required_quantity:
            quantity_warnings.append("moq_exceeds_required_quantity")

    eligible_for_comparison = (
        not mismatches
        and not unverified
        and not quantity_warnings
    )

    return {
        "matches": matches,
        "mismatches": mismatches,
        "unverified_fields": unverified,
        "quantity_warnings": quantity_warnings,
        "eligible_for_comparison": eligible_for_comparison,
    }
