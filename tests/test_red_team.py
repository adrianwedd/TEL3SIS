from __future__ import annotations

import asyncio
import types
from pathlib import Path

import yaml

import scripts.red_team as red_team


def test_load_prompts(tmp_path: Path) -> None:
    path = tmp_path / "prompts.yml"
    prompts = ["a", "b"]
    path.write_text(yaml.safe_dump(prompts))
    assert red_team.load_prompts(path) == prompts


def test_evaluate_iteration(monkeypatch):
    prompts = ["hi", "bye"]
    calls = []

    async def fake_generate(self, prompt, conversation_id, **_: str):
        calls.append((prompt, conversation_id))
        yield types.SimpleNamespace(
            message=types.SimpleNamespace(text=f"resp-{prompt}")
        )

    monkeypatch.setattr(
        red_team.ChatGPTAgent, "generate_response", fake_generate, raising=False
    )
    monkeypatch.setattr(red_team, "safety_check", lambda text: text != "resp-bye")
    monkeypatch.setattr(
        red_team, "build_core_agent", lambda *_: types.SimpleNamespace(agent=None)
    )

    class DummyAgent:
        def __init__(self, *_: object, **__: object) -> None:
            pass

    monkeypatch.setattr(red_team, "SafeFunctionCallingAgent", DummyAgent)

    results = asyncio.run(red_team.run_red_team(prompts))
    assert [c[0] for c in calls] == prompts
    assert results[0]["allowed"] is True
    assert results[1]["allowed"] is False


def test_summarize_results():
    results = [{"allowed": True}, {"allowed": False}, {"allowed": True}]
    summary = red_team.summarize_results(results)
    assert summary == {"allowed": 2, "blocked": 1}
