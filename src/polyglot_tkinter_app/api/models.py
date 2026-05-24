from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HealthStatus:
    online: bool
    model_loaded: bool = False
    processor_loaded: bool = False
    semantic_memory_enabled: bool = False
    semantic_memory_mode: str = "unknown"
    device: str = "unknown"
    message: str = ""


@dataclass(frozen=True)
class TranslationRequest:
    audio_bytes: bytes
    target_language: str
    speaker_id: str
    session_id: str
    source_language: str = "auto"
    domain: str = "demo"
    privacy_level: str = "transient"
    use_semantic_cache: bool = True
    cache_strategy: str = "context"
    use_transcript_memory: bool = True


@dataclass(frozen=True)
class TranslationResponse:
    audio_bytes: bytes
    cache_status: str = "unknown"
    cache_strategy: str = "unknown"
    similarity: float | None = None
    text_similarity: float | None = None
    lookup_time: float | None = None
    transcript_time: float | None = None
    inference_time: float | None = None
    total_time: float | None = None
    cache_layer: str = "unknown"
    source_transcript: str = ""
    normalized_source_text: str = ""
    decision: str = ""
    translation_id: str = ""
    raw_headers: dict[str, str] = field(default_factory=dict)
