import sys
import os
import base64
from pathlib import Path
from .db_utils import migrate_sqlite

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tests.utils.vocode_mocks import install as install_vocode

install_vocode()


from server.app import create_app  # noqa: E402
from server.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

os.environ.setdefault("SECRET_KEY", "x")
os.environ.setdefault("BASE_URL", "http://localhost")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "token")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())


def test_dashboard_oauth_flow(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    db = migrate_sqlite(monkeypatch, tmp_path)
    db.create_user("admin", "pass", role="admin")
    transcript_dir = tmp_path / "transcripts"
    transcript_dir.mkdir()
    transcript_path = transcript_dir / "test.txt"
    transcript_path.write_text("hello world")
    db.save_call_summary("abc", "111", "222", str(transcript_path), "summary", "crit")
    key = db.create_api_key("tester")

    app = create_app(Config())
    client = TestClient(app)

    resp = client.get("/v1/dashboard", headers={"X-API-Key": key})
    assert resp.status_code == 302
    assert "/v1/login/oauth" in resp.headers["Location"]

    monkeypatch.setenv("OAUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("OAUTH_AUTH_URL", "https://auth.example/authorize")

    resp = client.get("/v1/login/oauth", headers={"X-API-Key": key})
    assert resp.status_code == 302
    assert resp.headers["Location"].startswith("https://auth.example/authorize")
    from urllib.parse import urlparse, parse_qs

    state = parse_qs(urlparse(resp.headers["Location"]).query)["state"][0]

    resp = client.get(
        f"/v1/oauth/callback?state={state}&user=admin", headers={"X-API-Key": key}
    )
    assert resp.status_code == 302

    resp = client.get("/v1/dashboard", headers={"X-API-Key": key})
    assert resp.status_code == 200

    resp = client.get("/v1/dashboard?q=111", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert b"111" in resp.content

    resp = client.get("/v1/dashboard/1", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert b"hello world" in resp.content


def test_oauth_callback_validation(monkeypatch, tmp_path) -> None:
    from server.app import create_app
    from server.config import Config

    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

    db_module = migrate_sqlite(monkeypatch, tmp_path)
    app = create_app(Config())
    client = TestClient(app)
    key = db_module.create_api_key("tester")

    resp = client.get("/v1/oauth/callback", headers={"X-API-Key": key})
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_request"


def test_dashboard_prefix_search_with_formatted_number(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv(
        "TOKEN_ENCRYPTION_KEY",
        base64.b64encode(b"0" * 16).decode(),
    )
    db = migrate_sqlite(monkeypatch, tmp_path)
    db.create_user("admin", "pass", role="admin")
    transcript_dir = tmp_path / "transcripts"
    transcript_dir.mkdir()
    transcript_path = transcript_dir / "t.txt"
    transcript_path.write_text("hi")
    db.save_call_summary(
        "sid1",
        "+12345678900",
        "999",
        str(transcript_path),
        "summary",
        "crit",
    )
    key = db.create_api_key("tester")

    app = create_app(Config())
    client = TestClient(app)

    resp = client.get("/v1/dashboard", headers={"X-API-Key": key})
    assert resp.status_code == 302

    monkeypatch.setenv("OAUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("OAUTH_AUTH_URL", "https://auth.example/authorize")
    from urllib.parse import urlparse, parse_qs

    state = parse_qs(
        urlparse(
            client.get("/v1/login/oauth", headers={"X-API-Key": key}).headers[
                "Location"
            ]
        ).query
    )["state"][0]

    client.get(
        f"/v1/oauth/callback?state={state}&user=admin", headers={"X-API-Key": key}
    )

    resp = client.get("/v1/dashboard?q=+1-234-567", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert b"+12345678900" in resp.content
