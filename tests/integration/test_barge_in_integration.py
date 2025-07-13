import asyncio
import threading
import pytest

from tests.test_barge_in import _make_manager, DummySynthesizer, DummyTranscriber
from tel3sis import BargeInController, enable_barge_in, handle_barge_in


class DummyConversation:
    def __init__(self):
        self.synthesizer = DummySynthesizer()
        self.transcriber = DummyTranscriber()
        self.interrupted = False

    async def send_speech_to_output(self, *args, **kwargs):
        await asyncio.sleep(0.2)

    def broadcast_interrupt(self):
        self.interrupted = True


@pytest.mark.asyncio
async def test_barge_in_stops_playback(monkeypatch):
    manager = _make_manager(monkeypatch)
    manager.create_session("c3", {"init": "1"})
    convo = DummyConversation()
    ctrl = BargeInController(convo.synthesizer, convo.transcriber, manager, "c3")
    enable_barge_in(convo, ctrl)

    task = asyncio.create_task(
        convo.send_speech_to_output("hi", object(), threading.Event(), 0.1)
    )
    await asyncio.sleep(0.05)
    handle_barge_in(convo, ctrl, b"hello")
    await task

    assert convo.interrupted is True
    assert convo.synthesizer.stopped is True
    assert convo.transcriber.restarted is True
