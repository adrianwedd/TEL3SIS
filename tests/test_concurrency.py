import asyncio
import base64
import sys
import time
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
import httpx
import pytest

import tests.test_api_key_auth  # noqa: F401
from .db_utils import migrate_sqlite
from server import fast_app as server_app


def test_concurrent_call_performance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    db = migrate_sqlite(monkeypatch, tmp_path)
    key = db.create_api_key("tester")

    class DummyStateManager:
        def create_session(self, *a: object, **k: object) -> None:  # pragma: no cover
            pass

        def is_escalation_required(self, *_: object) -> bool:
            return False

        def get_summary(self, *_: object) -> str:
            return ""

    monkeypatch.setattr(server_app, "StateManager", lambda: DummyStateManager())

    async def delayed_route(**_: object):
        await asyncio.sleep(0.2)
        return types.SimpleNamespace(body=b"", status_code=200, media_type="text/plain")

    class DummyServer:
        def __init__(self, *_: object, **__: object) -> None:  # pragma: no cover
            pass

        def create_inbound_route(self, *_: object, **__: object):
            return delayed_route

    monkeypatch.setattr(server_app, "TelephonyServer", DummyServer)
    monkeypatch.setattr(
        server_app,
        "build_core_agent",
        lambda *_, **__: types.SimpleNamespace(agent=None),
    )
    monkeypatch.setattr(
        server_app, "echo", types.SimpleNamespace(delay=lambda *_, **__: None)
    )

    app = server_app.create_app()

    async def run_test() -> tuple[float, float]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:

            async def make_call(i: int) -> None:
                resp = await client.post(
                    "/v1/inbound_call",
                    data={
                        "CallSid": f"CA{i}",
                        "From": "+12025550000",
                        "To": "+12025550001",
                    },
                    headers={"X-API-Key": key},
                )
                assert resp.status_code == 200

            start = time.perf_counter()
            for i in range(3):
                await make_call(i)
            sequential = time.perf_counter() - start

            start = time.perf_counter()
            await asyncio.gather(*(make_call(i) for i in range(3, 6)))
            concurrent = time.perf_counter() - start

            return sequential, concurrent

    sequential, concurrent = asyncio.run(run_test())
    assert concurrent < sequential
