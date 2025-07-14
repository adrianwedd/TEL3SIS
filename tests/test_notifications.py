from __future__ import annotations

import requests

from tools.notifications import send_email, send_sms
from server.metrics import twilio_sms_latency


def test_send_email_failure(monkeypatch, tmp_path):
    path = tmp_path / "t.txt"
    path.write_text("hi")

    class DummyClient:
        def __init__(self, api_key: str):  # noqa: ANN001
            pass

        def send(self, message):  # noqa: ANN001
            raise Exception("boom")

    monkeypatch.setattr("tools.notifications.SendGridAPIClient", DummyClient)
    # Should not raise
    send_email(str(path), "user@test")


def test_send_sms_failure(monkeypatch):
    def fake_post(*args, **kwargs):  # noqa: ANN001, ARG001
        raise requests.RequestException("boom")

    monkeypatch.setattr(requests, "post", fake_post)
    # Should not raise
    send_sms("+1", "+2", "hi")


def test_sms_latency_metric(monkeypatch):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")

    class DummyResp:
        status_code = 200

        def raise_for_status(self) -> None:
            pass

    monkeypatch.setattr(requests, "post", lambda *a, **k: DummyResp())

    before = [
        s.value
        for s in twilio_sms_latency.collect()[0].samples
        if s.name.endswith("_count")
    ][0]
    send_sms("+1", "+2", "hi")
    after = [
        s.value
        for s in twilio_sms_latency.collect()[0].samples
        if s.name.endswith("_count")
    ][0]

    assert after == before + 1
