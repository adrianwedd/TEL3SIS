import base64
from tests.db_utils import migrate_sqlite
from tests.utils.vocode_mocks import install as install_vocode

install_vocode()

from server.app import create_app  # noqa: E402
from server.settings import Settings  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def setup(monkeypatch, tmp_path):
    db = migrate_sqlite(monkeypatch, tmp_path)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv(
        "TOKEN_ENCRYPTION_KEY",
        base64.b64encode(b"0" * 16).decode(),
    )
    return db


def test_search_api(monkeypatch, tmp_path):
    db = setup(monkeypatch, tmp_path)
    t1 = tmp_path / "t1.txt"
    t2 = tmp_path / "t2.txt"
    t1.write_text("hello world")
    t2.write_text("goodbye")
    db.save_call_summary("a", "111", "222", str(t1), "greet", None)
    db.save_call_summary("b", "333", "444", str(t2), "farewell", None)
    key = db.create_api_key("tester")

    app = create_app(Settings())
    client = TestClient(app)
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

    resp = client.get("/v1/search?q=hello", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["call_sid"] == "a"

    resp = client.get("/v1/search?q=farewell", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["call_sid"] == "b"
