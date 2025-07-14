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


def test_cli_backup(monkeypatch):
    called = {}
    monkeypatch.setattr(
        "server.tasks.backup_data.delay",
        lambda upload_to_s3=None: called.setdefault("s3", upload_to_s3),
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["backup", "--s3"])
    assert result.exit_code == 0
    assert called["s3"] is True


def test_cli_restore(monkeypatch):
    called = {}
    monkeypatch.setattr(
        "server.tasks.restore_data.delay",
        lambda archive: called.setdefault("archive", archive),
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["restore", "file.tar.gz"])
    assert result.exit_code == 0
    assert called["archive"] == "file.tar.gz"
