from tools.safety import safety_check


class DummyCompletion:
    def __init__(self, verdict: str) -> None:
        self.verdict = verdict

    def create(self, **_: str) -> dict:
        return {"choices": [{"message": {"content": self.verdict}}]}


class DummyClient:
    def __init__(self, verdict: str) -> None:
        self.chat = type("Chat", (), {"completions": DummyCompletion(verdict)})()


def test_safety_check_safe() -> None:
    assert safety_check("hello", client=DummyClient("SAFE"))


def test_safety_check_unsafe() -> None:
    assert not safety_check("bad", client=DummyClient("UNSAFE"))


def test_safety_check_heuristic() -> None:
    assert not safety_check("I want to kill", client=None)
