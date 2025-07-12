import time
import os
import base64
from pathlib import Path
import pytest
from .db_utils import migrate_sqlite


from server.latency_logging import log_stt
from tests.utils.vocode_mocks import install as install_vocode

install_vocode()


os.environ.setdefault("SECRET_KEY", "x")
os.environ.setdefault("BASE_URL", "http://localhost")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "token")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())


from server.app import create_app  # noqa: E402
from server.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def test_metrics_endpoint(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    os.environ.setdefault("SECRET_KEY", "x")
    os.environ.setdefault("BASE_URL", "http://localhost")
    os.environ.setdefault("TWILIO_ACCOUNT_SID", "sid")
    os.environ.setdefault("TWILIO_AUTH_TOKEN", "token")
    os.environ.setdefault("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    app = create_app(Config())
    client = TestClient(app)
    db = migrate_sqlite(monkeypatch, tmp_path)
    key = db.create_api_key("tester")

    @log_stt
    def dummy() -> str:
        time.sleep(0.01)
        return "ok"

    dummy()

    resp = client.get("/v1/metrics", headers={"X-API-Key": key})
    body = resp.text
    assert "stt_latency_seconds" in body
