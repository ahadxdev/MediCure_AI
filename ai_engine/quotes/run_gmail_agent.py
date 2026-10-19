import argparse
from email.utils import parseaddr

from ai_engine.gmail.client import extract_pdf_text, fetch_supplier_replies
from ai_engine.quotes.agent import process_supplier_reply
from ai_engine.quotes.deduplicator import deduplicate_quotes


def main():
    parser = argparse.ArgumentParser(
        description="MediProcure AI supplier reply agent"
    )
    parser.add_argument(
        "--medicine", required=True, help="Expected medicine name"
    )
    parser.add_argument("--strength", required=True)
    parser.add_argument("--form", required=True, dest="dosage_form")
    parser.add_argument("--pack", required=True, dest="pack_size")
    parser.add_argument(
        "--quantity", required=True, type=float, dest="required_quantity"
    )
    parser.add_argument(
        "--query",
        default="in:inbox newer_than:30d {quote quotation RFQ}",
        help="Gmail search query",
    )
    args = parser.parse_args()

    request = {
        "medicine_name": args.medicine,
        "strength": args.strength,
        "dosage_form": args.dosage_form,
        "pack_size": args.pack_size,
        "required_quantity": args.required_quantity,
    }

    print("\n=== MediProcure AI: Supplier Reply Agent ===")
    print(f"Medicine requested: {args.medicine}")
    print("Fetching matching Gmail messages...")

    emails = fetch_supplier_replies(args.query)

    if not emails:
        print("No matching messages found.")
        print("Check your Gmail search query and inbox.")
        return

    print(f"Messages fetched: {len(emails)}")

    processed = []

    for email in emails:
        sender_name, sender_email = parseaddr(email["from"])
        supplier_name = sender_name or sender_email or None
        email_text = email["body"]
        for attachment in email.get("attachments", []):
            email_text += "\n" + extract_pdf_text(attachment["data"])

        result = process_supplier_reply(
            email_text=email_text,
            request=request,
            metadata={
                "supplier_name": supplier_name,
                "request_id": None,
                "thread_id": email["thread_id"],
                "message_id": email["message_id"],
            },
        )

        processed.append({
            "message_id": email["message_id"],
            "subject": email["subject"],
            "sender": email["from"],
            "date": email["date"],
            "result": result,
        })

    dedupe_result = deduplicate_quotes(processed)

    print(f"Unique messages: {len(dedupe_result['unique_quotes'])}")
    print(f"Duplicate messages: {len(dedupe_result['duplicates'])}")

    for item in dedupe_result["unique_quotes"]:
        result = item["result"]
        quote = result["quote"]

        print("\n" + "=" * 55)
        print(f"From: {item['sender']}")
        print(f"Subject: {item['subject']}")
        print(f"Date: {item['date']}")
        print(f"Medicine in reply: {quote.get('medicine_name')}")
        print(
            "Price: "
            f"{quote.get('currency') or ''} "
            f"{quote.get('price')} / {quote.get('price_unit') or 'unit unspecified'}"
        )
        print(f"Quoted quantity: {quote.get('quoted_quantity')}")
        print(f"Delivery days: {quote.get('delivery_days')}")
        print(f"Review status: {quote.get('review_status')}")
        print(
            "Ready for comparison: "
            f"{result['ready_for_comparison']}"
        )
        print(
            "Human review required: "
            f"{result['requires_human_review']}"
        )

        if result["warnings"]:
            print("Warnings:", ", ".join(result["warnings"]))

        if result["match_result"]["mismatches"]:
            print(
                "Request mismatches:",
                result["match_result"]["mismatches"],
            )

        if not item["result"]["quote"].get("message_id"):
            print("Warning: source message ID is missing.")

    print("\nNo purchase orders were created.")
    print("Supplier claims and delivery promises remain unverified.")


if __name__ == "__main__":
    main()