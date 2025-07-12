from flask import Flask
from flask_login import LoginManager, login_user, UserMixin

from .db_utils import migrate_sqlite

from server.dashboard_bp import bp, analytics as analytics_view


class DummyUser(UserMixin):
    def __init__(self, role: str) -> None:
        self.id = 1
        self.role = role


def test_dashboard_analytics(monkeypatch, tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    db = migrate_sqlite(monkeypatch, tmp_path)
    db.create_user("admin", "pass", role="admin")
    tdir = tmp_path / "transcripts"
    tdir.mkdir()
    a = tdir / "a.txt"
    b = tdir / "b.txt"
    a.write_text("weather info")
    b.write_text("calendar event")
    db.save_call_summary("sid1", "111", "222", str(a), "used weather", None)
    db.save_call_summary("sid2", "333", "444", str(b), "checked calendar", None)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "x"
    app.register_blueprint(bp)
    login_manager = LoginManager(app)

    @login_manager.user_loader
    def load_user(user_id: str):  # pragma: no cover - unused
        return DummyUser("admin")

    with app.test_request_context("/v1/dashboard/analytics"):
        login_user(DummyUser("admin"))
        html = analytics_view()

    assert "weather" in html
    assert "calendar" in html
