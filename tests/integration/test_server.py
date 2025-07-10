import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from tests.test_health import setup_app


def test_metrics_endpoint(monkeypatch, tmp_path):
    client, key = setup_app(monkeypatch, tmp_path)
    resp = client.get("/v1/metrics", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert b"python_info" in resp.content
