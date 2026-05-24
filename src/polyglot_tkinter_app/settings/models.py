from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class GeneralSettings:
    debug: bool = True
    save_logs: bool = True
    log_file: str = "logs/polyglot.log"


@dataclass(frozen=True)
class ApiProfile:
    base_url: str
    verify_ssl: bool


@dataclass(frozen=True)
class ApiSettings:
    profile: str = "local"
    profiles: dict[str, ApiProfile] = field(default_factory=dict)
    health_endpoint: str = "health/"
    process_endpoint: str = "process_memory/"
    timeout_seconds: float = 120.0

    def active_profile(self, profile_name: str | None = None) -> ApiProfile:
        name = profile_name or self.profile
        if name not in self.profiles:
            name = "local"
        return self.profiles[name]


@dataclass(frozen=True)
class SemanticCacheSettings:
    enabled: bool = True
    source_language: str = "ron"
    use_transcript_memory: bool = True
    domain: str = "demo"
    privacy_level: str = "transient"
    strategy: str = "context"


@dataclass(frozen=True)
class AudioSettings:
    sample_rate: int = 16000
    channels: int = 1
    frame_duration_ms: int = 30
    vad_aggressiveness: int = 3


@dataclass(frozen=True)
class DemoSettings:
    enabled: bool = False
    output_mode: str = "speakers"
    save_artifacts: bool = True


@dataclass(frozen=True)
class GuiSettings:
    main_window_size: str = "900x660"
    splash_window_size: str = "400x400"
    title: str = "Polyglot App"
    default_theme: str = "dark"
    colors: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AppSettings:
    general: GeneralSettings
    api: ApiSettings
    semantic_cache: SemanticCacheSettings
    audio: AudioSettings
    demo: DemoSettings
    gui: GuiSettings


@dataclass
class RuntimeState:
    settings: AppSettings
    ui_mode: str = "user"
    backend_profile: str = "local"
    semantic_cache_enabled: bool = True
    cache_strategy: str = "context"
    source_language: str = "auto"
    use_transcript_memory: bool = True
    domain: str = "demo"
    privacy_level: str = "transient"
    session_id: str = field(default_factory=lambda: str(uuid4()))
    target_language: str = "eng"
    speaker_id: str = "0"
    input_device: Any | None = None
    output_device: Any | None = None

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "RuntimeState":
        return cls(
            settings=settings,
            ui_mode="demo" if settings.demo.enabled else "user",
            backend_profile=settings.api.profile,
            semantic_cache_enabled=settings.semantic_cache.enabled,
            cache_strategy=settings.semantic_cache.strategy,
            source_language=settings.semantic_cache.source_language,
            use_transcript_memory=settings.semantic_cache.use_transcript_memory,
            domain=settings.semantic_cache.domain,
            privacy_level=settings.semantic_cache.privacy_level,
        )

    @property
    def api_profile(self) -> ApiProfile:
        return self.settings.api.active_profile(self.backend_profile)

    @property
    def base_url(self) -> str:
        return self.api_profile.base_url.rstrip("/") + "/"

    @property
    def verify_ssl(self) -> bool:
        return self.api_profile.verify_ssl

    @property
    def timeout_seconds(self) -> float:
        return self.settings.api.timeout_seconds

    @property
    def demo_enabled(self) -> bool:
        return self.ui_mode == "demo"

    def update_demo_options(
        self,
        *,
        backend_profile: str | None = None,
        semantic_cache_enabled: bool | None = None,
        cache_strategy: str | None = None,
        domain: str | None = None,
        privacy_level: str | None = None,
        output_device: Any | None = None,
        target_language: str | None = None,
        speaker_id: str | None = None,
        source_language: str | None = None,
        use_transcript_memory: bool | None = None,
    ) -> None:
        if backend_profile is not None:
            self.backend_profile = backend_profile
        if semantic_cache_enabled is not None:
            self.semantic_cache_enabled = semantic_cache_enabled
        if cache_strategy is not None:
            self.cache_strategy = cache_strategy
        if domain is not None:
            self.domain = domain
        if privacy_level is not None:
            self.privacy_level = privacy_level
        if output_device is not None:
            self.output_device = output_device
        if target_language is not None:
            self.target_language = target_language
        if speaker_id is not None:
            self.speaker_id = speaker_id
        if source_language is not None:
            self.source_language = source_language
        if use_transcript_memory is not None:
            self.use_transcript_memory = use_transcript_memory

    def reset_session(self) -> str:
        self.session_id = str(uuid4())
        return self.session_id
