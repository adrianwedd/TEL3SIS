from __future__ import annotations

import os
from pathlib import Path
import re

from loguru import logger
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import requests

__all__ = ["send_email", "send_sms", "sanitize_transcript"]


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{7,}\d")


def sanitize_transcript(text: str) -> str:
    """Remove phone numbers and email addresses from ``text``."""

    text = _EMAIL_RE.sub("[REDACTED]", text)
    text = _PHONE_RE.sub("[REDACTED]", text)
    return text


def send_email(transcript_path: str, to_email: str | None = None) -> None:
    """Send the transcript file via SendGrid email."""
    api_key = os.environ.get("SENDGRID_API_KEY")
    from_email = os.environ.get("SENDGRID_FROM_EMAIL")
    to_email = to_email or os.environ.get("NOTIFY_EMAIL")

    if not api_key or not from_email or not to_email:
        logger.warning("SendGrid not configured; skipping email notification")
        return

    text = Path(transcript_path).read_text()
    text = sanitize_transcript(text)
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject="TEL3SIS Call Transcript",
        plain_text_content=text,
    )
    try:
        SendGridAPIClient(api_key).send(message)
        logger.info("Sent transcript email to %s", to_email)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send transcript email: %s", exc)


def send_sms(to_phone: str, from_phone: str, body: str) -> None:
    """Send an SMS via Twilio."""
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        logger.warning("Twilio not configured; skipping SMS notification")
        return
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    data = {"To": to_phone, "From": from_phone, "Body": body}
    try:
        resp = requests.post(url, data=data, auth=(account_sid, auth_token), timeout=5)
        resp.raise_for_status()
        logger.info("Sent SMS to %s", to_phone)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send SMS: %s", exc)
