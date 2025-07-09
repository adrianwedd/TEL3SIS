import base64
import sys
from pathlib import Path

import fakeredis
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import Flask

sys.path.append(str(Path(__file__).resolve().parents[1]))

from server.state_manager import StateManager
from server.dashboard_bp import bp, socketio


def _make_manager(monkeypatch):
    key = AESGCM.generate_key(bit_length=128)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(key).decode())
    monkeypatch.setenv("VECTOR_DB_PATH", "vectors")
    manager = StateManager(url="redis://localhost:6379/0")
    manager._redis = fakeredis.FakeRedis(decode_responses=True)
    return manager


def _make_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "x"
    app.register_blueprint(bp)
    socketio.init_app(app, async_mode="threading")
    return app


def test_streaming(monkeypatch):
    manager = _make_manager(monkeypatch)
    app = _make_app()
    client = socketio.test_client(app)
    client.emit("join", {"call_sid": "c1"})
    manager.create_session("c1", {"init": "1"})
    manager.append_history("c1", "user", "hello")
    received = client.get_received()
    assert received
    evt = received[0]
    assert evt["name"] == "transcript_line"
    assert evt["args"][0]["text"] == "hello"
