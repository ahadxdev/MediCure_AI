
import html
import re
from datetime import datetime
from typing import Any

from ai_engine.quotes.schemas import SupplierQuote


def _strip_html(value: str) -> str:
    if not value:
        return ""

    cleaned = html.unescape(value)
    cleaned = re.sub(r"(?is)<script.*?>.*?</script>", " ", cleaned)
    cleaned = re.sub(r"(?is)<style.*?>.*?</style>", " ", cleaned)
    cleaned = re.sub(r"(?is)<br\s*/?>", "\n", cleaned)
    cleaned = re.sub(r"(?is)</p>|</div>|</li>|</tr>|</table>|</h[1-6]>", "\n", cleaned)
    cleaned = re.sub(r"(?is)<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"&nbsp;", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n+", "\n", cleaned)
    return cleaned.strip()


def _extract(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _extract_number(value: str | None) -> float | None:
    if not value:
        return None

    cleaned = value.replace(",", "")
    match = re.search(r"\d+(?:\.\d+)?", cleaned)
    return float(match.group()) if match else None


def _normalize_validity_date(value: str | None) -> str | None:
    if not value:
        return None

    candidate = value.strip()
    candidate = re.sub(r"(?i)^(?:valid\s*(?:until|till|through)|until|quote\s*validity|validity)\s*[:\-]?\s*", "", candidate)
    candidate = re.sub(r"(?i)\b(?:valid\s*(?:until|till|through)|until|till|through)\s*\*?\s*(?:until\s+)?", "", candidate)
    candidate = re.sub(r"^[*•\-\s]+", "", candidate)
    candidate = candidate.strip(" \t\r\n-:;,.|/*")
    if not candidate:
        return None

    formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d %Y",
        "%b %d %Y",
    )
    candidates = [candidate]
    date_match = re.search(
        r"\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4}|"
        r"\d{1,2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})\b",
        candidate,
    )
    if date_match:
        candidates.append(date_match.group())

    for date_candidate in candidates:
        cleaned = date_candidate.strip(" \t\r\n-:;,.|/*")
        for date_format in formats:
            try:
                return datetime.strptime(cleaned, date_format).date().isoformat()
            except ValueError:
                continue
    return candidate


def _delivery_days(value: str | None) -> float | None:
    if not value:
        return None
    range_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:-|to|–)\s*(\d+(?:\.\d+)?)",
        value,
        flags=re.IGNORECASE,
    )
    if range_match:
        return float(range_match.group(2))
    return _extract_number(value)


def _fallback_line(text: str, keywords: list[str]) -> str | None:
    for line in text.splitlines():
        candidate = line.strip(" \t\r\n-:;,.|/")
        if not candidate:
            continue

        match = re.search(
            r"(?:we\s+can\s+supply|available\s+item|offered\s+item|product\s+name|item\s+name|medicine\s*[:\-])\s*(.+)",
            candidate,
            flags=re.IGNORECASE,
        )
        if match:
            candidate = match.group(1).strip()

        candidate = re.sub(
            r"^(?:dear\s+team|hello|hi|thank\s+you\s+for\s+your\s+rfq|our\s+best\s+price\s+is)\s*[:\-]?\s*",
            "",
            candidate,
            flags=re.IGNORECASE,
        )
        candidate = candidate.strip(" \t\r\n-:;,.|/")
        if not candidate:
            continue
        lower = candidate.lower()
        if any(keyword in lower for keyword in keywords):
            return candidate.strip()
    return None


def _clean_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    cleaned = re.sub(r"(?i)^(?:target\s+product|product|medicine|item)\s*[:\-]\s*", "", cleaned)
    cleaned = re.sub(r"^(?:size|qty|quantity|available\s+quantity)\s*[:\-]?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(?i)\b(?:until|valid\s*(?:until|till|through)|payment\s*within)\s*\*?\s*", "", cleaned)
    cleaned = re.sub(r"\*\s*\*", "", cleaned)
    cleaned = cleaned.strip(" \t\r\n-:;,.|/*")
    placeholders = {
        "the requested product",
        "requested product",
        "the product",
        "product",
        "generic product",
        "not stated",
        "not specified",
        "n/a",
        "unknown",
    }
    if cleaned.lower() in placeholders:
        return None
    return cleaned or None


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
    text = _strip_html(email_text or "")
    text = re.sub(r"(?im)^\s*(?:quotation\s+anomaly\s+detected|delivery_time_unknown|request_match_unverified|request_mismatch|validity_date_unrecognized)\s*$", "", text)
    text = re.sub(r"(?im)^\s*[•*-]\s*(?:delivery_time_unknown|request_match_unverified|request_mismatch|validity_date_unrecognized)\s*$", "", text)
    text = re.sub(r"(?m)^\s*[•*-]\s*", "\n", text)
    text = re.sub(r"(?<!\w)\*{1,2}([^*\n]+)\*{1,2}(?!\w)", r"\1", text)
    text = re.sub(
        r"(?im)(^|[,;|•])\s*(medicine|strength|form|pack(?:\s*size)?|price|quantity|moq|delivery|payment|validity|lead\s*time|available\s+quantity)\b(?!\s+(?:terms|fee|time)\b)(?=\s+[A-Za-z0-9])",
        r"\1\n\2:",
        text,
    )
    text = re.sub(r"\n\s*\n+", "\n", text)

    fields = {
        "medicine_name": _extract(
            r"(?im)^\s*(?:medicine|product|target\s+product|item(?:\s+name)?)\s*[:\-]\s*(.+?)(?=\s*\n\s*(?:strength|form|pack|quantity|price|moq|delivery|payment|valid|lead)\b|$)",
            text,
        )
        or _extract(
            r"(?im)^\s*(?:medicine|product|target\s+product|item(?:\s+name)?)\s*[:\-]\s*(.+?)\s*$",
            text,
        )
        or _extract(
            r"(?im)(?:we\s+can\s+supply|offering|offer(?:ing)?\s+.*?\b(?:medicine|product|target\s+product)\s*[:\-])\s*(.+?)(?=\s*\n\s*(?:pack|price|quantity|moq|lead|delivery|valid)\b|$)",
            text,
        )
        or _fallback_line(
            text,
            [
                "tablet",
                "capsule",
                "syrup",
                "suspension",
                "injection",
                "drops",
                "powder",
            ],
        ),
        "strength": _extract(
            r"(?im)^\s*strength\s*[:\-]\s*(.+?)(?=\s*\n\s*(?:form|pack|quantity|price|moq|delivery|payment|valid|lead)\b|$)",
            text,
        )
        or _extract(r"(?im)\b(\d+(?:\.\d+)??\s*(?:mg|mcg|g|ml))\b", text),
        "dosage_form": _extract(
            r"(?im)^\s*(?:dosage\s*)?form\s*[:\-]\s*(.+?)(?=\s*\n\s*(?:strength|pack|quantity|price|moq|delivery|payment|valid|lead)\b|$)",
            text,
        )
        or _extract(r"(?im)\b(tablets?|capsules?|syrup|suspension|injection|drops|powder|oral)\b", text),
        "pack_size": _extract(
            r"(?im)^\s*(?:pack(?:\s*size)?|package|packing)\s*[:\-]\s*(.+?)(?=\s*\n\s*(?:medicine|strength|form|quantity|price|moq|delivery|payment|valid|lead)\b|$)",
            text,
        )
        or _extract(r"(?im)^\s*(?:pack(?:\s*size)?|package|packing)\s*[:\-]\s*(.+?)\s*$", text),
        "price_raw": _extract(
            r"(?im)^\s*(?:our\s+best\s+)?(?:unit\s+price|quoted\s+price|offer\s+price|price)\s*(?:is\s*)?[:\-]?\s*(.+?)(?=\s*\n\s*(?:quantity|moq|delivery|payment|valid|lead|terms)\b|$)",
            text,
        )
        or _extract(r"(?im)\b(?:price|unit price|offer price)\s*[:\-]?\s*(?:PKR|Rs\.?|USD|EUR|GBP)?\s*([\d,]+(?:\.\d+)?)\s*(?:per\s*(?:box|pack|strip|tablet|bottle|piece|unit|carton)|/\s*(?:box|pack|strip|tablet|bottle|piece|unit|carton))?", text),
        "quoted_quantity_raw": _extract(
            r"(?im)^\s*(?:quoted\s+|available\s+|offer(?:ed)?\s+)?quantity\s*[:\-]?\s*([\d,.]+)",
            text,
        )
        or _extract(r"(?im)\b(?:quantity|qty)\s*[:\-]?\s*([\d,.]+)\b", text),
        "minimum_order_quantity_raw": _extract(
            r"(?im)^\s*(?:minimum\s*order\s*quantity|moq|minimum\s*qty)\s*[:\-]?\s*([\d,.]+)",
            text,
        )
        or _extract(r"(?im)\bMOQ\s*[:\-]?\s*([\d,.]+)\b", text),
        "delivery_days_raw": _extract(
            r"(?im)^\s*(?:delivery(?:\s*time)?|lead\s*time|dispatch|shipping\s*time)\s*(?:is\s*|within\s*|in\s*)?[:\-]?\s*(?:within\s*|in\s*)?([\d,.]+(?:\s*(?:-|to|–)\s*[\d,.]+)?)\s*(?:(?:business|working)\s*)?days?\b",
            text,
        )
        or _extract(r"(?im)\b(?:delivery(?:\s*time)?|lead\s*time|dispatch|shipping\s*time)\s*(?:is\s*|within\s*|in\s*)?[:\-]?\s*(?:within\s*|in\s*)?([\d,.]+(?:\s*(?:-|to|–)\s*[\d,.]+)?)\s*(?:(?:business|working)\s*)?days?\b", text),
        "delivery_fee_raw": _extract(
            r"(?im)^\s*(?:delivery\s*fee|shipping\s*fee|freight|transport\s*fee)\s*[:\-]?\s*(.+?)(?=\s*\n\s*(?:payment|terms|valid|lead|quantity|price)\b|$)",
            text,
        )
        or _extract(r"(?im)\b(?:delivery\s*fee|shipping\s*fee|freight|transport\s*fee)\s*[:\-]?\s*(.+?)\s*$", text),
        "payment_terms": _extract(
            r"(?im)^\s*(?:payment\s*terms|payment)\s*[:\-]\s*(.+?)(?=\s*\n\s*(?:valid|delivery|price|moq|quantity|lead)\b|$)",
            text,
        )
        or _extract(r"(?im)\b(?:payment\s*terms|payment)\s*[:\-]?\s*(.+?)\s*$", text),
        "valid_until": _extract(
            r"(?im)^\s*(?:valid\s*(?:until|till|through)|validity|quote\s*expires|quote\s*validity)\s*[:\-]?\s*(.+?)(?=\s*\n\s*(?:terms|delivery|price|quantity|moq|payment)\b|$)",
            text,
        )
        or _extract(r"(?im)(?:valid\s*(?:until|till|through)|validity|quote\s*expires|quote\s*validity)\s*[:\-]?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4}|[A-Za-z]+\s+\d{1,2},?\s*\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})", text)
        or _extract(r"(?im)\b(?:valid\s*(?:until|till|through)|validity|quote\s*expires|quote\s*validity)\s*[:\-]?\s*(.+?)\s*$", text),
    }

    if not fields["medicine_name"]:
        fields["medicine_name"] = _fallback_line(
            text,
            [
                "panadol",
                "paracetamol",
                "amoxicillin",
                "ibuprofen",
                "ciprofloxacin",
                "augmentin",
                "metformin",
                "cetirizine",
                "cetirizine 10mg",
            ],
        )

    if fields["medicine_name"]:
        fields["medicine_name"] = re.sub(
            r"(?i)^(?:we\s+can\s+supply\s+|our\s+best\s+price\s+is\s+|available\s+item\s+|product\s+name\s+|medicine\s+name\s+)",
            "",
            fields["medicine_name"],
        ).strip()

    fields["medicine_name"] = _clean_value(fields["medicine_name"])
    fields["strength"] = _clean_value(fields["strength"])
    fields["dosage_form"] = _clean_value(fields["dosage_form"])
    fields["pack_size"] = _clean_value(fields["pack_size"])
    fields["payment_terms"] = _clean_value(fields["payment_terms"])
    fields["valid_until"] = _clean_value(fields["valid_until"])

    if not fields["strength"]:
        strength_match = re.search(r"(?im)\b(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml))\b", text)
        if strength_match:
            fields["strength"] = strength_match.group(1)

    if not fields["dosage_form"]:
        dosage_form_match = re.search(r"(?im)\b(tablets?|capsules?|syrup|suspension|injection|drops|powder|oral)\b", text)
        if dosage_form_match:
            fields["dosage_form"] = dosage_form_match.group(1)

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
            r"(?:/\s*|per\s+)(box|pack|strip|tablet|bottle|piece|unit|carton|capsule|vial|sachet)\b",
            price_raw,
            flags=re.IGNORECASE,
        )
        if unit_match:
            price_unit = unit_match.group(1).lower()

    delivery_fee = _extract_number(fee_raw)
    if fee_raw and re.search(r"\b(free|included|no charge)\b", fee_raw, re.I):
        delivery_fee = 0.0

    valid_until = _normalize_validity_date(fields["valid_until"])

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
        delivery_days=_delivery_days(delivery_raw),
        delivery_fee=delivery_fee,
        payment_terms=fields["payment_terms"],
        valid_until=valid_until,
    )

    if not quote.valid_until and quote.payment_terms:
        date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", quote.payment_terms)
        if date_match:
            quote.valid_until = date_match.group(1)

    return quote
