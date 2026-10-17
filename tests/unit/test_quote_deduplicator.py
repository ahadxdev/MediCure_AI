
from ai_engine.quotes.deduplicator import deduplicate_quotes


def test_duplicate_message_is_removed():
    quotes = [
        {"message_id": "msg-1", "price": 120},
        {"message_id": "msg-1", "price": 120},
        {"message_id": "msg-2", "price": 135},
    ]

    result = deduplicate_quotes(quotes)

    assert len(result["unique_quotes"]) == 2
    assert len(result["duplicates"]) == 1
    assert result["duplicates"][0]["message_id"] == "msg-1"


def test_different_replies_in_same_thread_are_kept():
    quotes = [
        {"message_id": "msg-1", "thread_id": "thread-1", "price": 120},
        {"message_id": "msg-2", "thread_id": "thread-1", "price": 125},
    ]

    result = deduplicate_quotes(quotes)

    assert len(result["unique_quotes"]) == 2
    assert result["duplicates"] == []


def test_missing_message_id_is_flagged():
    quotes = [
        {"thread_id": "thread-1", "price": 120},
    ]

    result = deduplicate_quotes(quotes)

    assert len(result["unique_quotes"]) == 1
    assert len(result["warnings"]) == 1
    assert (
        result["warnings"][0]["warning"]
        == "message_id_missing_deduplication_unverified"
    )


def test_message_id_with_whitespace_is_normalized():
    quotes = [
        {"message_id": " msg-1 ", "price": 120},
        {"message_id": "msg-1", "price": 120},
    ]

    result = deduplicate_quotes(quotes)

    assert len(result["unique_quotes"]) == 1
    assert len(result["duplicates"]) == 1
