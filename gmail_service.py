"""
gmail_service.py
Secure Gmail Integration using Google OAuth 2.0 with App Password / Mock fallback.

Features:
- Connects securely to Gmail using Google OAuth 2.0 (credentials.json -> token.json).
- Automatic token refresh via google.auth.
- Sends emails (for daily reports and status notifications).
- Reads and queries inbox messages (for application confirmations, interview invites, rejections).
- Fallback to SMTP/IMAP or Mock Mode for offline testing/development.
"""

import os
import io
import base64
import json
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

BASE_DIR = Path(__file__).parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailService:
    """Manages Gmail OAuth 2.0 connectivity and email operations."""

    def __init__(self):
        self._service = None
        self._user_email = None

    def get_connection_status(self) -> Dict[str, Any]:
        """Check if Gmail is connected via OAuth 2.0, App Password, or Mock."""
        # 1. Check OAuth2 token
        if TOKEN_FILE.exists():
            try:
                from google.oauth2.credentials import Credentials
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
                if creds and (creds.valid or creds.refresh_token):
                    return {
                        "connected": True,
                        "auth_type": "OAuth 2.0",
                        "email": self._get_profile_email() or "Google User",
                        "expires_at": creds.expiry.isoformat() if creds.expiry else None,
                        "has_refresh_token": bool(creds.refresh_token),
                        "status": "Active & Authenticated"
                    }
            except Exception as e:
                pass

        # 2. Check App Password / SMTP
        gmail_user = os.getenv("GMAIL_USER")
        gmail_app_pw = os.getenv("GMAIL_APP_PASSWORD")
        if gmail_user and gmail_app_pw:
            return {
                "connected": True,
                "auth_type": "App Password (SMTP/IMAP)",
                "email": gmail_user,
                "status": "Active (App Password)"
            }

        # 3. Check credentials.json readiness
        has_credentials_json = CREDENTIALS_FILE.exists()
        return {
            "connected": False,
            "auth_type": "None",
            "has_credentials_template": has_credentials_json,
            "status": "Not Connected",
            "message": "To connect Gmail, provide credentials.json or run the OAuth 2.0 authorization flow."
        }

    def _get_profile_email(self) -> str:
        """Helper to get user's email from profile_config.json if available."""
        try:
            profile_path = BASE_DIR / "profile_config.json"
            if profile_path.exists():
                with open(profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("email", "")
        except Exception:
            pass
        return ""

    def get_auth_url(self, redirect_uri: str = "http://localhost:5000/api/gmail/oauth-callback") -> str:
        """Generate Google OAuth 2.0 authorization URL."""
        if not CREDENTIALS_FILE.exists():
            # Return demo/mock instructions if credentials.json is not present
            raise FileNotFoundError(
                f"credentials.json not found at {CREDENTIALS_FILE}. "
                "Download OAuth 2.0 Client credentials from Google Cloud Console."
            )

        import google_auth_oauthlib.flow
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )
        return auth_url

    def exchange_code_for_token(self, code: str, redirect_uri: str = "http://localhost:5000/api/gmail/oauth-callback") -> Dict[str, Any]:
        """Exchange authorization code for tokens and save to token.json."""
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(f"credentials.json not found at {CREDENTIALS_FILE}.")

        import google_auth_oauthlib.flow
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        flow.fetch_token(code=code)
        creds = flow.credentials

        with open(TOKEN_FILE, "w", encoding="utf-8") as token_f:
            token_f.write(creds.to_json())

        self._service = None
        return {"status": "authenticated", "message": "Gmail OAuth 2.0 token saved successfully."}

    def get_service(self):
        """Build and return an authorized Gmail API service."""
        if self._service:
            return self._service

        if TOKEN_FILE.exists():
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    with open(TOKEN_FILE, "w", encoding="utf-8") as token_f:
                        token_f.write(creds.to_json())
                except Exception as err:
                    print(f"[gmail_service] Token refresh error: {err}")

            if creds and creds.valid:
                self._service = build("gmail", "v1", credentials=creds)
                return self._service

        return None

    def send_email(self, to: str, subject: str, html_body: str, text_body: Optional[str] = None) -> Dict[str, Any]:
        """Send an email using Gmail API or SMTP fallback."""
        from candidate_profile import sanitize_email
        to = sanitize_email(to)
        service = self.get_service()

        if service:
            message = MIMEMultipart("alternative")
            message["to"] = to
            message["subject"] = subject

            if text_body:
                message.attach(MIMEText(text_body, "plain"))
            if html_body:
                message.attach(MIMEText(html_body, "html"))

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            sent = service.users().messages().send(
                userId="me",
                body={"raw": raw_message}
            ).execute()

            return {
                "status": "sent",
                "method": "Gmail API (OAuth2)",
                "message_id": sent.get("id"),
                "to": to,
                "subject": subject,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Fallback to SMTP with App Password if configured
        gmail_user = os.getenv("GMAIL_USER")
        gmail_app_pw = os.getenv("GMAIL_APP_PASSWORD")
        if gmail_user and gmail_app_pw:
            import smtplib
            msg = MIMEMultipart("alternative")
            msg["From"] = gmail_user
            msg["To"] = to
            msg["Subject"] = subject
            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(gmail_user, gmail_app_pw)
                server.sendmail(gmail_user, [to], msg.as_string())

            return {
                "status": "sent",
                "method": "SMTP SSL",
                "to": to,
                "subject": subject,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Safe local mock fallback for testing without credentials
        return {
            "status": "mock_sent",
            "method": "Simulated Delivery",
            "to": to,
            "subject": subject,
            "body_snippet": (text_body or html_body)[:120],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "Email logged in local test mode. Connect Gmail OAuth 2.0 to deliver to live inboxes."
        }

    def fetch_recent_emails(self, query: str = "subject:(application OR interview OR status)", max_results: int = 20) -> List[Dict[str, Any]]:
        """Fetch matching emails from user's Gmail inbox."""
        service = self.get_service()
        emails = []

        if service:
            try:
                results = service.users().messages().list(
                    userId="me",
                    q=query,
                    maxResults=max_results
                ).execute()

                messages = results.get("messages", [])
                for msg_ref in messages:
                    msg = service.users().messages().get(
                        userId="me",
                        id=msg_ref["id"],
                        format="full"
                    ).execute()

                    payload = msg.get("payload", {})
                    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}

                    subject = headers.get("subject", "")
                    sender = headers.get("from", "")
                    date_str = headers.get("date", "")
                    snippet = msg.get("snippet", "")

                    body = self._extract_body(payload) or snippet

                    emails.append({
                        "id": msg["id"],
                        "thread_id": msg.get("threadId"),
                        "subject": subject,
                        "sender": sender,
                        "date": date_str,
                        "snippet": snippet,
                        "body": body
                    })
            except Exception as e:
                print(f"[gmail_service] Error querying Gmail API: {e}")

        return emails

    def _extract_body(self, payload: dict) -> str:
        """Helper to extract text or HTML body from a Gmail payload."""
        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                data = part.get("body", {}).get("data")
                if data:
                    decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    if mime_type == "text/plain":
                        return decoded
                    elif mime_type == "text/html":
                        return decoded
        elif "body" in payload and "data" in payload["body"]:
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        return ""


# Singleton instance
gmail_client = GmailService()

