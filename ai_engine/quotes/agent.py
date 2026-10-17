from typing import Any

from ai_engine.quotes.parser import parse_quote_email
from ai_engine.quotes.validator import validate_quote
from ai_engine.quotes.matcher import match_quote_to_request


def process_supplier_reply(
    email_text: str,
    request: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Process one supplier reply.

    This function does not send emails, place orders, or claim that
    the supplier's stock or delivery promise has been verified.
    """
    quote = parse_quote_email(
        email_text=email_text,
        metadata=metadata,
    )

    quote = validate_quote(quote)

    match_result = match_quote_to_request(
        quote=quote,
        request=request,
    )

    warnings = list(quote.warning_flags)

    if match_result["mismatches"]:
        warnings.append("request_mismatch")

    if match_result["unverified_fields"]:
        warnings.append("request_match_unverified")

    if match_result["quantity_warnings"]:
        warnings.extend(match_result["quantity_warnings"])

    ready_for_comparison = (
        quote.review_status == "validated"
        and match_result["eligible_for_comparison"]
    )

    return {
        "quote": quote.model_dump(),
        "match_result": match_result,
        "warnings": sorted(set(warnings)),
        "ready_for_comparison": ready_for_comparison,
        "requires_human_review": not ready_for_comparison,
        "source": {
            "request_id": (metadata or {}).get("request_id"),
            "thread_id": (metadata or {}).get("thread_id"),
            "message_id": (metadata or {}).get("message_id"),
        },
    }
