"""Utility functions for sending email and SMS notifications."""
from __future__ import annotations

from pathlib import Path
import re

from logging_config import logger
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import requests

from server.settings import Settings
from server.metrics import record_external_api, twilio_sms_latency
from util import call_with_retries

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
    cfg = Settings()
    api_key = cfg.sendgrid_api_key
    from_email = cfg.sendgrid_from_email
    to_email = to_email or cfg.notify_email

    if cfg.use_fake_services:
        with record_external_api("sendgrid"):
            logger.bind(email=to_email).info("email_mock_sent")
        return

    if not api_key or not from_email or not to_email:
        logger.bind(email=to_email).warning("sendgrid_not_configured")
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
        with record_external_api("sendgrid"):
            call_with_retries(SendGridAPIClient(api_key).send, message, timeout=10)
        logger.bind(email=to_email).info("email_sent")
    except Exception as exc:  # noqa: BLE001
        logger.bind(email=to_email, error=str(exc)).error("email_failed")


def send_sms(to_phone: str, from_phone: str, body: str) -> None:
    """Send an SMS via Twilio."""
    cfg = Settings()
    account_sid = cfg.twilio_account_sid
    auth_token = cfg.twilio_auth_token
    if cfg.use_fake_services:
        with record_external_api("twilio"), twilio_sms_latency.time():
            logger.bind(to=to_phone).info("sms_mock_sent")
        return
    if not account_sid or not auth_token:
        logger.bind(to=to_phone).warning("twilio_not_configured")
        return
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    data = {"To": to_phone, "From": from_phone, "Body": body}
    try:
        with record_external_api("twilio"), twilio_sms_latency.time():
            resp = call_with_retries(
                requests.post,
                url,
                data=data,
                auth=(account_sid, auth_token),
                timeout=5,
            )
            resp.raise_for_status()
        logger.bind(to=to_phone).info("sms_sent")
    except Exception as exc:  # noqa: BLE001
        logger.bind(to=to_phone, error=str(exc)).error("sms_failed")
