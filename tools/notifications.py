from __future__ import annotations

import os
from pathlib import Path

from loguru import logger
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

__all__ = ["send_email"]


def send_email(transcript_path: str, to_email: str | None = None) -> None:
    """Send the transcript file via SendGrid email."""
    api_key = os.environ.get("SENDGRID_API_KEY")
    from_email = os.environ.get("SENDGRID_FROM_EMAIL")
    to_email = to_email or os.environ.get("NOTIFY_EMAIL")

    if not api_key or not from_email or not to_email:
        logger.warning("SendGrid not configured; skipping email notification")
        return

    text = Path(transcript_path).read_text()
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
