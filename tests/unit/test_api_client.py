from polyglot_tkinter_app.api.client import TranslationClient
from polyglot_tkinter_app.api.models import TranslationRequest
from polyglot_tkinter_app.settings.loader import load_settings
from polyglot_tkinter_app.settings.models import RuntimeState


class FakeResponse:
    def __init__(self, status_code=200, payload=None, content=b"wav", headers=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.content = content
        self.headers = headers or {}
        self.text = text

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self):
        self.last_post = None

    def get(self, url, **kwargs):
        return FakeResponse(
            payload={
                "status": True,
                "model_loaded": True,
                "processor_loaded": True,
                "device": "cpu",
                "semantic_memory": {"enabled": True, "mode": "audio"},
            }
        )

    def post(self, url, **kwargs):
        self.last_post = (url, kwargs)
        return FakeResponse(
            content=b"translated",
            headers={
                "X-Polyglot-Cache": "hit",
                "X-Polyglot-Cache-Strategy": "exact",
                "X-Polyglot-Similarity": "1.000000",
                "X-Polyglot-Lookup-Time": "0.0500",
                "X-Polyglot-Inference-Time": "0.0000",
                "X-Polyglot-Decision": "exact audio fingerprint match",
                "X-Polyglot-Translation-Id": "abc",
            },
        )


def test_health_parses_semantic_memory_status():
    runtime = RuntimeState.from_settings(load_settings("missing-config.json"))
    client = TranslationClient(runtime, session=FakeSession())

    health = client.health()

    assert health.online is True
    assert health.model_loaded is True
    assert health.processor_loaded is True
    assert health.semantic_memory_enabled is True
    assert health.semantic_memory_mode == "audio"


def test_translate_builds_request_and_parses_cache_headers():
    runtime = RuntimeState.from_settings(load_settings("missing-config.json"))
    session = FakeSession()
    client = TranslationClient(runtime, session=session)

    response = client.translate(
        TranslationRequest(
            audio_bytes=b"wav",
            target_language="ron",
            speaker_id="0",
            session_id="session-a",
            domain="demo",
            use_semantic_cache=True,
            cache_strategy="context",
        )
    )

    url, kwargs = session.last_post
    assert url == "https://localhost/process_memory/"
    assert kwargs["data"]["language"] == "ron"
    assert kwargs["data"]["session_id"] == "session-a"
    assert kwargs["data"]["use_semantic_cache"] == "true"
    assert response.audio_bytes == b"translated"
    assert response.cache_status == "hit"
    assert response.cache_strategy == "exact"
    assert response.similarity == 1.0
    assert response.lookup_time == 0.05
    assert response.inference_time == 0.0
    assert response.decision == "exact audio fingerprint match"
