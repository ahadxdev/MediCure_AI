
import base64
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_gmail_service():
    """Authenticate the user and return a Gmail API client."""
    creds = None

    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Missing OAuth credentials: {CREDENTIALS_FILE}"
        )

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            str(TOKEN_FILE), SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json())
        TOKEN_FILE.chmod(0o600)

    return build(
        "gmail",
        "v1",
        credentials=creds,
        cache_discovery=False,
    )


def send_email(to: list[str], subject: str, body: str) -> dict:
    """Send an email. Call only after explicit human approval."""
    if not to or any(
        not isinstance(address, str)
        or "@" not in address
        or address.endswith(".invalid")
        for address in to
    ):
        raise ValueError("Provide valid, real recipient email addresses.")

    if not subject.strip() or not body.strip():
        raise ValueError("Email subject and body cannot be empty.")

    message = EmailMessage()
    message["To"] = ", ".join(to)
    message["Subject"] = subject
    message.set_content(body)

    encoded = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("utf-8")

    result = (
        get_gmail_service()
        .users()
        .messages()
        .send(userId="me", body={"raw": encoded})
        .execute()
    )

    return {
        "message_id": result["id"],
        "thread_id": result["threadId"],
        "status": "sent",
    }
