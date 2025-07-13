from __future__ import annotations

from xml.etree.ElementTree import Element, tostring

from .settings import Settings


__all__ = ["dial_twiml"]


def dial_twiml(from_number: str | None = None) -> str:
    """Return TwiML for dialing the escalation phone number."""
    phone = Settings().escalation_phone_number
    if not phone:
        raise RuntimeError("ESCALATION_PHONE_NUMBER not set")

    response = Element("Response")
    dial = Element("Dial")
    if from_number:
        dial.set("callerId", from_number)
    dial.text = phone
    response.append(dial)
    return tostring(response, encoding="unicode")
