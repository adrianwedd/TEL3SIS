import sys
import os
import base64
from pathlib import Path
from .db_utils import migrate_sqlite

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tests.utils.vocode_mocks import install as install_vocode

install_vocode()


from server.app import create_app  # noqa: E402
from server.settings import Settings  # noqa: E402
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
    db.save_call_summary(
        "abc", "111", "222", str(transcript_path), "summary", "crit", 0.4
    )
    key = db.create_api_key("tester")

    app = create_app(Settings())
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
    assert b"0.40" in resp.content


def test_oauth_callback_validation(monkeypatch, tmp_path) -> None:
    from server.app import create_app
    from server.settings import Settings

    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

    db_module = migrate_sqlite(monkeypatch, tmp_path)
    app = create_app(Settings())
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
        0.5,
    )
    key = db.create_api_key("tester")

    app = create_app(Settings())
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


def test_admin_actions(monkeypatch, tmp_path):
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
    db.create_user("alice", "pass", role="user")
    transcript_dir = tmp_path / "trans"
    transcript_dir.mkdir()
    transcript = transcript_dir / "t.txt"
    transcript.write_text("hi")
    with db.get_session() as session:
        call = db.Call(
            call_sid="sid1",
            from_number="111",
            to_number="222",
            transcript_path=str(transcript),
            summary="s",
            self_critique=None,
        )
        session.add(call)
        session.commit()
        call_id = call.id
    key = db.create_api_key("tester")
    monkeypatch.setenv("OAUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("OAUTH_AUTH_URL", "https://auth.example/authorize")
    app = create_app(Settings())
    client = TestClient(app)
    from urllib.parse import urlparse, parse_qs

    def login(user: str) -> None:
        state = parse_qs(
            urlparse(
                client.get("/v1/login/oauth", headers={"X-API-Key": key}).headers[
                    "Location"
                ]
            ).query
        )["state"][0]
        client.get(
            f"/v1/oauth/callback?state={state}&user={user}", headers={"X-API-Key": key}
        )

    calls: list[tuple[str, int]] = []
    monkeypatch.setattr(
        "server.app.delete_call_record.delay", lambda cid: calls.append(("delete", cid))
    )
    monkeypatch.setattr(
        "server.app.reprocess_call.delay", lambda cid: calls.append(("reprocess", cid))
    )

    login("admin")
    resp = client.post(f"/v1/dashboard/{call_id}/reprocess", headers={"X-API-Key": key})
    assert resp.status_code == 303
    resp = client.post(f"/v1/dashboard/{call_id}/delete", headers={"X-API-Key": key})
    assert resp.status_code == 303
    assert ("reprocess", call_id) in calls
    assert ("delete", call_id) in calls

    client = TestClient(app)
    login("alice")
    resp = client.post(f"/v1/dashboard/{call_id}/delete", headers={"X-API-Key": key})
    assert resp.status_code == 403
