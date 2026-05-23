import os
from pathlib import Path

import pytest

from polyglot_tkinter_app.api.client import TranslationClient
from polyglot_tkinter_app.api.models import TranslationRequest
from polyglot_tkinter_app.settings.loader import load_settings
from polyglot_tkinter_app.settings.models import RuntimeState


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("POLYGLOT_RUN_INTEGRATION") != "1",
    reason="set POLYGLOT_RUN_INTEGRATION=1 with the Docker backend running",
)
def test_local_backend_cache_hit_after_repeat_request():
    runtime = RuntimeState.from_settings(load_settings("config.json"))
    runtime.backend_profile = "local"
    client = TranslationClient(runtime)
    sample = Path(__file__).parents[1] / "performance" / "sample2.wav"
    audio_bytes = sample.read_bytes()

    first = client.translate(
        TranslationRequest(
            audio_bytes=audio_bytes,
            target_language="ron",
            speaker_id="0",
            session_id="tkinter-integration-cache",
            domain="demo",
            privacy_level="transient",
            use_semantic_cache=True,
            cache_strategy="context",
        )
    )
    second = client.translate(
        TranslationRequest(
            audio_bytes=audio_bytes,
            target_language="ron",
            speaker_id="0",
            session_id="tkinter-integration-cache",
            domain="demo",
            privacy_level="transient",
            use_semantic_cache=True,
            cache_strategy="context",
        )
    )

    assert first.cache_status in {"miss", "hit"}
    assert second.cache_status == "hit"
    assert second.inference_time == 0.0
