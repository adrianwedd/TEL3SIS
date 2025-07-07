from __future__ import annotations

import pytest
import xml.etree.ElementTree as ET

from server.handoff import dial_twiml


def test_dial_twiml(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ESCALATION_PHONE_NUMBER", "+1234567890")
    xml = dial_twiml("+15551234567")
    root = ET.fromstring(xml)
    dial = root.find("Dial")
    assert dial is not None
    assert dial.text == "+1234567890"
    assert dial.attrib["callerId"] == "+15551234567"


def test_dial_twiml_no_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ESCALATION_PHONE_NUMBER", raising=False)
    with pytest.raises(RuntimeError):
        dial_twiml()
