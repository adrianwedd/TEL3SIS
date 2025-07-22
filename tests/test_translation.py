from tools.translation import translate_text


class DummyTranslator:
    def __init__(self, **_: object) -> None:
        pass

    def translate(self, text: str) -> str:  # noqa: D401
        return text.upper()


def test_translate_text(monkeypatch):
    monkeypatch.setattr("tools.translation.GoogleTranslator", DummyTranslator)
    result = translate_text("hello", "fr")
    assert result == "HELLO"


def test_translate_failure(monkeypatch):
    class FailTranslator:
        def __init__(self, **_: object) -> None:
            pass

        def translate(self, _text: str) -> str:
            raise RuntimeError("boom")

    monkeypatch.setattr("tools.translation.GoogleTranslator", FailTranslator)
    result = translate_text("hi", "de")
    assert "unable" in result.lower() or "sorry" in result.lower()
