
from ai_engine.gmail.client import get_gmail_service


def main():
    service = get_gmail_service()

    # Verify the Gmail API client can be created.
    # This does not send an email or read account data.
    print("Gmail OAuth credentials loaded.")
    print("Gmail API client created successfully.")


if __name__ == "__main__":
    main()
