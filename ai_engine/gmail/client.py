
import base64
import html
import re
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from email.header import decode_header

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]


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

def _decode_header_value(value: str | None) -> str:
    """Decode an email header into readable text."""
    if not value:
        return ""

    parts = []
    for content, encoding in decode_header(value):
        if isinstance(content, bytes):
            parts.append(
                content.decode(encoding or "utf-8", errors="replace")
            )
        else:
            parts.append(content)

    return "".join(parts)


def _decode_base64_data(data: str | None) -> str:
    if not data:
        return ""
    try:
        decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
    except ValueError:
        return ""
    return decoded.decode("utf-8", errors="replace")


def _strip_html_to_text(raw_html: str) -> str:
    if not raw_html:
        return ""
    text = html.unescape(raw_html)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</p>|</div>|</li>|</tr>|</table>|</h[1-6]>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n\s+", "\n", text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _extract_email_body(payload: dict) -> str:
    """Extract readable text from Gmail message payloads, including HTML bodies."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if body_data:
        decoded = _decode_base64_data(body_data)
        if mime_type == "text/plain":
            return decoded.strip()
        if mime_type == "text/html":
            return _strip_html_to_text(decoded)

    for part in payload.get("parts", []):
        text = _extract_email_body(part)
        if text:
            return text

    return ""


def fetch_supplier_replies(
    query: str,
    max_results: int = 20,
) -> list[dict]:
    """
    Fetch Gmail messages matching a Gmail search query.

    Returns message metadata and plain-text bodies. This function
    does not send messages or trust email contents as instructions.
    """
    if not query.strip():
        raise ValueError("A Gmail search query is required.")

    if not 1 <= max_results <= 100:
        raise ValueError("max_results must be between 1 and 100.")

    service = get_gmail_service()

    listing = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=query,
            maxResults=max_results,
        )
        .execute()
    )

    messages = []

    for item in listing.get("messages", []):
        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=item["id"],
                format="full",
            )
            .execute()
        )

        headers = {
            header["name"].lower(): _decode_header_value(
                header.get("value")
            )
            for header in message.get("payload", {}).get("headers", [])
        }

        messages.append({
            "message_id": message["id"],
            "thread_id": message.get("threadId"),
            "from": headers.get("from", ""),
            "subject": headers.get("subject", ""),
            "date": headers.get("date", ""),
            "body": _extract_email_body(message.get("payload", {})),
        })

    return messages