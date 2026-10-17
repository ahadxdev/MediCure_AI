
from ai_engine.gmail.client import send_email


def main():
    recipient = input("Apna test inbox Gmail address enter karo: ").strip()

    confirm = input(
        f"Is test email ko {recipient} par send karna hai? (yes/no): "
    ).strip().lower()

    if confirm != "yes":
        print("Cancelled. No email sent.")
        return

    result = send_email(
        to=[recipient],
        subject="MediProcure AI - Gmail Integration Test",
        body=(
            "This is a controlled test email from MediProcure AI.\n\n"
            "Purpose: verify Gmail API sending integration.\n"
            "This is not a medicine quotation or purchase order."
        ),
    )

    print("Gmail API send request successful.")
    print("Message ID:", result["message_id"])
    print("Thread ID:", result["thread_id"])


if __name__ == "__main__":
    main()
