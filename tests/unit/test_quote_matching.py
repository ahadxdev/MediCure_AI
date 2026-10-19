
from ai_engine.quotes.agent import process_supplier_reply


REQUEST = {
    "medicine_name": "Paracetamol",
    "strength": "500 mg",
    "dosage_form": "Tablet",
    "pack_size": "100 tablets",
    "required_quantity": 10,
}


def test_matching_quote_is_ready_for_comparison():
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

    result = process_supplier_reply(
        email,
        REQUEST,
        {"supplier_name": "Demo Supplier", "message_id": "msg-001"},
    )

    assert result["match_result"]["mismatches"] == []
    assert result["ready_for_comparison"] is True
    assert result["requires_human_review"] is False


def test_wrong_strength_is_not_eligible():
    email = """
    Medicine: Paracetamol
    Strength: 650 mg
    Form: Tablet
    Pack: 100 tablets
    Price: PKR 120 / box
    Quantity: 10
    MOQ: 5
    Delivery: 2 days
    """

    result = process_supplier_reply(email, REQUEST)

    assert "strength" in result["match_result"]["mismatches"]
    assert result["ready_for_comparison"] is False
    assert result["requires_human_review"] is True


def test_missing_pack_size_requires_review():
    email = """
    Medicine: Paracetamol
    Strength: 500 mg
    Form: Tablet
    Price: PKR 120 / box
    Quantity: 10
    MOQ: 5
    Delivery: 2 days
    """

    result = process_supplier_reply(email, REQUEST)

    assert "pack_size" in result["match_result"]["unverified_fields"]
    assert result["ready_for_comparison"] is False
    assert result["requires_human_review"] is True


def test_matching_ignores_strength_and_form_repeated_in_product_name():
    email = """
    Medicine: Panadol 500mg Tablets
    Strength: 500 mg
    Form: Tablets
    Pack: 100 tablets
    Price: PKR 120 / box
    Quantity: 10
    MOQ: 5
    Delivery time: within 3 to 5 working days
    Valid through: 31/12/2099
    """
    request = {
        **REQUEST,
        "medicine_name": "Panadol 500mg Tablets",
    }

    result = process_supplier_reply(email, request)

    assert result["match_result"]["mismatches"] == []
    assert result["match_result"]["unverified_fields"] == []
    assert "delivery_time_unknown" not in result["warnings"]
    assert "validity_date_unrecognized" not in result["warnings"]
