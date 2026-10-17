
import re
from typing import Any

from ai_engine.quotes.schemas import SupplierQuote


def _extract(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _extract_number(value: str | None) -> float | None:
    if not value:
        return None

    # Remove commas used as thousands separators.
    cleaned = value.replace(",", "")
    match = re.search(r"\d+(?:\.\d+)?", cleaned)

    return float(match.group()) if match else None


def parse_quote_email(
    email_text: str,
    metadata: dict[str, Any] | None = None,
) -> SupplierQuote:
    """
    Extract explicitly labelled quotation fields from supplier email text.

    metadata may contain supplier_name, request_id, thread_id and message_id.
    Missing or ambiguous information should be reviewed, not guessed.
    """
    metadata = metadata or {}

    fields = {
        "medicine_name": _extract(
            r"^\s*(?:medicine|product|item)\s*:\s*(.+?)\s*$",
            email_text,
        ),
        "strength": _extract(
            r"^\s*strength\s*:\s*(.+?)\s*$", email_text
        ),
        "dosage_form": _extract(
            r"^\s*(?:dosage\s*)?form\s*:\s*(.+?)\s*$", email_text
        ),
        "pack_size": _extract(
            r"^\s*(?:pack(?:\s*size)?|package)\s*:\s*(.+?)\s*$",
            email_text,
        ),
        "price_raw": _extract(
            r"^\s*(?:unit\s*)?price\s*:\s*(.+?)\s*$", email_text
        ),
        "quoted_quantity_raw": _extract(
            r"^\s*(?:quoted\s*)?quantity\s*:\s*([\d,.]+)",
            email_text,
        ),
        "minimum_order_quantity_raw": _extract(
            r"^\s*(?:minimum\s*order\s*quantity|moq)\s*:\s*([\d,.]+)",
            email_text,
        ),
        "delivery_days_raw": _extract(
            r"^\s*(?:delivery|lead\s*time)\s*:\s*([\d,.]+)\s*"
            r"(?:business\s*)?days?\b",
            email_text,
        ),
        "delivery_fee_raw": _extract(
            r"^\s*(?:delivery\s*fee|shipping\s*fee|freight)\s*:\s*(.+?)\s*$",
            email_text,
        ),
        "payment_terms": _extract(
            r"^\s*(?:payment\s*terms|payment)\s*:\s*(.+?)\s*$",
            email_text,
        ),
        "valid_until": _extract(
            r"^\s*(?:valid\s*until|validity|quote\s*expires)\s*:\s*(.+?)\s*$",
            email_text,
        ),
    }

    price_raw = fields.pop("price_raw")
    quantity_raw = fields.pop("quoted_quantity_raw")
    moq_raw = fields.pop("minimum_order_quantity_raw")
    delivery_raw = fields.pop("delivery_days_raw")
    fee_raw = fields.pop("delivery_fee_raw")

    price = None
    price_unit = None
    currency = None

    if price_raw:
        price = _extract_number(price_raw)

        currency_match = re.search(
            r"\b(PKR|Rs\.?|USD|EUR|GBP)\b",
            price_raw,
            flags=re.IGNORECASE,
        )
        if currency_match:
            token = currency_match.group(1).upper()
            currency = "PKR" if token.startswith("RS") else token

        unit_match = re.search(
            r"/\s*(box|pack|strip|tablet|bottle|piece|unit)\b",
            price_raw,
            flags=re.IGNORECASE,
        )
        if unit_match:
            price_unit = unit_match.group(1).lower()

    delivery_fee = _extract_number(fee_raw)
    if fee_raw and re.search(r"\b(free|included|no charge)\b", fee_raw, re.I):
        delivery_fee = 0.0

    quote = SupplierQuote(
        supplier_name=metadata.get("supplier_name"),
        request_id=metadata.get("request_id"),
        thread_id=metadata.get("thread_id"),
        message_id=metadata.get("message_id"),
        medicine_name=fields["medicine_name"],
        strength=fields["strength"],
        dosage_form=fields["dosage_form"],
        pack_size=fields["pack_size"],
        price=price,
        price_unit=price_unit,
        currency=currency,
        quoted_quantity=_extract_number(quantity_raw),
        minimum_order_quantity=_extract_number(moq_raw),
        delivery_days=_extract_number(delivery_raw),
        delivery_fee=delivery_fee,
        payment_terms=fields["payment_terms"],
        valid_until=fields["valid_until"],
    )

    return quote
