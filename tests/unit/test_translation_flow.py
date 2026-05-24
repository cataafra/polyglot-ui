import logging
import threading

from polyglot_tkinter_app.api.models import TranslationResponse
from polyglot_tkinter_app.orchestration.translation_flow import TranslationFlow
from polyglot_tkinter_app.settings.loader import load_settings
from polyglot_tkinter_app.settings.models import RuntimeState


class FakeClient:
    def __init__(self):
        self.requests = []

    def translate(self, request):
        self.requests.append(request)
        return TranslationResponse(
            audio_bytes=b"translated",
            cache_status="hit",
            cache_strategy="exact",
            similarity=1.0,
            text_similarity=1.0,
            lookup_time=0.01,
            transcript_time=0.03,
            inference_time=0.0,
            total_time=0.02,
            cache_layer="text_exact",
            source_transcript="Câine!",
            normalized_source_text="caine",
            decision="normalized transcript match",
        )


class BlockingClient:
    def __init__(self):
        self.started = threading.Event()
        self.release = threading.Event()
        self.requests = []

    def translate(self, request):
        self.requests.append(request)
        self.started.set()
        self.release.wait(timeout=2)
        return TranslationResponse(
            audio_bytes=b"translated-after-shutdown",
            cache_status="miss",
            cache_strategy="context",
        )


class FakePlayer:
    def __init__(self):
        self.enqueued = []
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def enqueue(self, audio_bytes, output_device=None):
        self.enqueued.append((audio_bytes, output_device))

    def stop(self):
        self.stopped = True


def test_translation_flow_submits_wav_and_emits_response(caplog):
    caplog.set_level(logging.INFO, logger="polyglot_tkinter_app.orchestration.translation_flow")
    runtime = RuntimeState.from_settings(load_settings("missing-config.json"))
    runtime.target_language = "ron"
    runtime.source_language = "ron"
    runtime.use_transcript_memory = True
    client = FakeClient()
    player = FakePlayer()
    completed = []
    done = threading.Event()

    flow = TranslationFlow(
        runtime=runtime,
        client=client,
        player=player,
        on_translation_completed=lambda response: (completed.append(response), done.set()),
    )

    flow.submit_wav(b"wav", reason="test")
    assert done.wait(timeout=2)
    flow.stop()

    assert client.requests[0].target_language == "ron"
    assert client.requests[0].source_language == "ron"
    assert client.requests[0].use_transcript_memory is True
    assert client.requests[0].cache_strategy == "context"
    assert completed[0].cache_status == "hit"
    assert completed[0].cache_layer == "text_exact"
    assert player.enqueued[0][0] == b"translated"
    assert "Câine!" not in caplog.text
    assert "caine" not in caplog.text
    assert "transcript=0.0300s" in caplog.text


def test_translation_flow_resend_and_replay_use_cached_bytes():
    runtime = RuntimeState.from_settings(load_settings("missing-config.json"))
    client = FakeClient()
    player = FakePlayer()
    done = threading.Event()

    flow = TranslationFlow(
        runtime=runtime,
        client=client,
        player=player,
        on_translation_completed=lambda response: done.set(),
    )
    flow.last_input_wav_bytes = b"last-input"

    assert flow.resend_last_input() is True
    assert done.wait(timeout=2)
    assert client.requests[0].audio_bytes == b"last-input"

    flow.last_output_wav_bytes = b"last-output"
    assert flow.replay_last_output() is True
    flow.stop()

    assert (b"last-output", None) in player.enqueued


def test_translation_flow_drops_late_response_after_shutdown():
    runtime = RuntimeState.from_settings(load_settings("missing-config.json"))
    client = BlockingClient()
    player = FakePlayer()
    completed = []

    flow = TranslationFlow(
        runtime=runtime,
        client=client,
        player=player,
        on_translation_completed=lambda response: completed.append(response),
    )

    flow.submit_wav(b"wav", reason="test")
    assert client.started.wait(timeout=2)

    flow.shutdown()
    assert completed == []
    assert player.enqueued == []

    client.release.set()
    flow._worker_thread.join(timeout=2)

    assert completed == []
    assert player.enqueued == []
