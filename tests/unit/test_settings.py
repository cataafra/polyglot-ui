from polyglot_tkinter_app.settings.loader import load_settings
from polyglot_tkinter_app.settings.models import RuntimeState


def test_load_settings_accepts_booleans_and_profiles(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        """
        {
          "general": {"debug": "true", "save_logs": "false"},
          "api": {
            "profile": "local",
            "profiles": {
              "local": {"base_url": "https://localhost/", "verify_ssl": "false"}
            }
          },
          "semantic_cache": {
            "enabled": "true",
            "strategy": "context",
            "source_language": "ron",
            "use_transcript_memory": "true"
          }
        }
        """,
        encoding="utf-8",
    )

    settings = load_settings(config_path)

    assert settings.general.debug is True
    assert settings.general.save_logs is False
    assert settings.api.active_profile("local").base_url == "https://localhost/"
    assert settings.api.active_profile("local").verify_ssl is False
    assert settings.semantic_cache.enabled is True
    assert settings.semantic_cache.source_language == "ron"
    assert settings.semantic_cache.use_transcript_memory is True


def test_runtime_updates_and_resets_session():
    settings = load_settings("missing-config.json")
    runtime = RuntimeState.from_settings(settings)
    original_session = runtime.session_id

    runtime.update_demo_options(
        backend_profile="aws",
        semantic_cache_enabled=False,
        cache_strategy="exact",
        domain="legal",
        privacy_level="private",
        target_language="ron",
        speaker_id="2",
        source_language="ron",
        use_transcript_memory=True,
    )
    runtime.reset_session()

    assert runtime.backend_profile == "aws"
    assert runtime.semantic_cache_enabled is False
    assert runtime.cache_strategy == "exact"
    assert runtime.domain == "legal"
    assert runtime.privacy_level == "private"
    assert runtime.target_language == "ron"
    assert runtime.speaker_id == "2"
    assert runtime.source_language == "ron"
    assert runtime.use_transcript_memory is True
    assert runtime.session_id != original_session
