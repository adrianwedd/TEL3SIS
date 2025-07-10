from __future__ import annotations

import requests

from tools.notifications import send_email, send_sms


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
