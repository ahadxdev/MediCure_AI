
from collections.abc import Iterable, Mapping
from typing import Any


def deduplicate_quotes(
    quotes: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """
    Deduplicate quote records using Gmail message IDs.

    Records without message IDs are retained but flagged because
    they cannot be safely deduplicated using this function alone.
    """
    seen_message_ids: set[str] = set()
    unique_quotes: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for quote in quotes:
        record = dict(quote)
        message_id = record.get("message_id")

        if not message_id:
            warnings.append({
                "record": record,
                "warning": "message_id_missing_deduplication_unverified",
            })
            unique_quotes.append(record)
            continue

        normalized_id = str(message_id).strip()

        if normalized_id in seen_message_ids:
            duplicates.append({
                "message_id": normalized_id,
                "record": record,
            })
            continue

        seen_message_ids.add(normalized_id)
        unique_quotes.append(record)

    return {
        "unique_quotes": unique_quotes,
        "duplicates": duplicates,
        "warnings": warnings,
    }
