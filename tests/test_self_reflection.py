from server.self_reflection import generate_self_critique


class DummyChat:
    def __init__(self, text: str) -> None:
        self._text = text

    def create(self, **_: str):
        return {"choices": [{"message": {"content": self._text}}]}


class DummyClient:
    def __init__(self, text: str) -> None:
        self.chat = type("Chat", (), {"completions": DummyChat(text)})()


def test_generate_self_critique() -> None:
    result = generate_self_critique("hi", client=DummyClient("All good."))
    assert "good" in result.lower()
