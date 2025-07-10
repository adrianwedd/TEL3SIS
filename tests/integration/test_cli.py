import sys
from pathlib import Path
import types

sys.path.append(str(Path(__file__).resolve().parents[2]))
import tests.test_health as _  # noqa: F401

sys.modules.setdefault(
    "scripts.dev_test_call", types.ModuleType("scripts.dev_test_call")
)
sys.modules.setdefault("scripts.red_team", types.ModuleType("scripts.red_team"))
sys.modules["scripts.red_team"].load_prompts = lambda *a, **k: []
sys.modules["scripts.red_team"].run_red_team = lambda *a, **k: []
sys.modules["scripts.red_team"].summarize_results = lambda *a, **k: ""

from click.testing import CliRunner  # noqa: E402
from tel3sis.cli import cli  # noqa: E402


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "TEL3SIS" in result.output


def test_cli_warmup(monkeypatch):
    monkeypatch.setattr("scripts.warmup_whisper.load_model", lambda m="base": None)
    runner = CliRunner()
    result = runner.invoke(cli, ["warmup", "--model", "tiny"])
    assert result.exit_code == 0


def test_cli_manage_api_key(monkeypatch):
    monkeypatch.setattr("scripts.manage.db.init_db", lambda: None)
    monkeypatch.setattr("scripts.manage.db.create_api_key", lambda owner: "abc")
    runner = CliRunner()
    result = runner.invoke(cli, ["manage", "generate-api-key", "tester"])
    assert result.exit_code == 0
    assert "abc" in result.output


def test_cli_manage_delete_user(monkeypatch):
    calls = {}

    monkeypatch.setattr("scripts.manage.db.init_db", lambda: None)
    monkeypatch.setattr(
        "scripts.manage.db.delete_user", lambda u: calls.setdefault("user", u) or True
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["manage", "delete-user", "bob"])

    assert result.exit_code == 0
    assert calls["user"] == "bob"
