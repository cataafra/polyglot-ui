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
                "details": {
                    "model_loaded": True,
                    "processor_loaded": True,
                    "device": "cpu",
                    "semantic_memory": {"enabled": True, "mode": "audio+transcript"},
                },
            }
        )

    def post(self, url, **kwargs):
        self.last_post = (url, kwargs)
        return FakeResponse(
            content=b"translated",
            headers={
                "X-Polyglot-Cache": "hit",
                "X-Polyglot-Cache-Strategy": "exact",
                "X-Polyglot-Cache-Layer": "text_exact",
                "X-Polyglot-Similarity": "1.000000",
                "X-Polyglot-Text-Similarity": "1.000000",
                "X-Polyglot-Lookup-Time": "0.0500",
                "X-Polyglot-Transcript-Time": "0.2500",
                "X-Polyglot-Inference-Time": "0.0000",
                "X-Polyglot-Decision": "normalized transcript match",
                "X-Polyglot-Translation-Id": "abc",
                "X-Polyglot-Source-Transcript": "C%C3%A2ine%21",
                "X-Polyglot-Normalized-Text": "caine",
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
    assert health.semantic_memory_mode == "audio+transcript"


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
            source_language="ron",
            domain="demo",
            use_semantic_cache=True,
            cache_strategy="context",
            use_transcript_memory=True,
        )
    )

    url, kwargs = session.last_post
    assert url == "https://localhost/process_memory/"
    assert kwargs["data"]["language"] == "ron"
    assert kwargs["data"]["session_id"] == "session-a"
    assert kwargs["data"]["source_language"] == "ron"
    assert kwargs["data"]["use_semantic_cache"] == "true"
    assert kwargs["data"]["use_transcript_memory"] == "true"
    assert response.audio_bytes == b"translated"
    assert response.cache_status == "hit"
    assert response.cache_strategy == "exact"
    assert response.cache_layer == "text_exact"
    assert response.similarity == 1.0
    assert response.text_similarity == 1.0
    assert response.lookup_time == 0.05
    assert response.transcript_time == 0.25
    assert response.inference_time == 0.0
    assert response.source_transcript == "Câine!"
    assert response.normalized_source_text == "caine"
    assert response.decision == "normalized transcript match"
