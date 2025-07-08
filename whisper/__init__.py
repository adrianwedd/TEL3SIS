class DummyModel:
    def transcribe(self, path: str):
        return {"text": ""}


def load_model(name: str = "base"):
    return DummyModel()
