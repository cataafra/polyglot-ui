from __future__ import annotations

import logging
import time
from io import BytesIO
from typing import Any

import requests
import urllib3

from polyglot_tkinter_app.api.models import HealthStatus, TranslationRequest, TranslationResponse
from polyglot_tkinter_app.settings.models import RuntimeState

logger = logging.getLogger(__name__)


class TranslationClientError(RuntimeError):
    pass


class TranslationClient:
    def __init__(self, runtime: RuntimeState, session: Any | None = None):
        self.runtime = runtime
        self.session = session or requests.Session()

    def health(self) -> HealthStatus:
        url = self._url(self.runtime.settings.api.health_endpoint)
        self._disable_warnings_if_needed()
        try:
            response = self.session.get(
                url,
                verify=self.runtime.verify_ssl,
                timeout=self.runtime.timeout_seconds,
            )
            if response.status_code != 200:
                return HealthStatus(online=False, message=f"HTTP {response.status_code}")

            payload = response.json()
            semantic = payload.get("semantic_memory", {}) or {}
            return HealthStatus(
                online=bool(payload.get("status", True)),
                model_loaded=bool(payload.get("model_loaded", False)),
                processor_loaded=bool(payload.get("processor_loaded", False)),
                semantic_memory_enabled=bool(semantic.get("enabled", False)),
                semantic_memory_mode=str(semantic.get("mode", "unknown")),
                device=str(payload.get("device", "unknown")),
                message=str(payload.get("message", "")),
            )
        except Exception as exc:
            logger.warning("server_health_checked online=false error=%s", exc)
            return HealthStatus(online=False, message=str(exc))

    def translate(self, request: TranslationRequest) -> TranslationResponse:
        url = self._url(self.runtime.settings.api.process_endpoint)
        files = {"file": ("audio.wav", BytesIO(request.audio_bytes), "audio/wav")}
        data = {
            "language": request.target_language,
            "speaker_id": str(request.speaker_id),
            "session_id": request.session_id,
            "source_language": request.source_language,
            "domain": request.domain,
            "privacy_level": request.privacy_level,
            "use_semantic_cache": str(request.use_semantic_cache).lower(),
            "cache_strategy": request.cache_strategy,
        }

        self._disable_warnings_if_needed()
        started = time.perf_counter()
        response = self.session.post(
            url,
            files=files,
            data=data,
            verify=self.runtime.verify_ssl,
            timeout=self.runtime.timeout_seconds,
        )
        total_time = time.perf_counter() - started

        if response.status_code != 200:
            raise TranslationClientError(f"translation failed: HTTP {response.status_code}: {response.text}")

        headers = {key: value for key, value in response.headers.items() if key.lower().startswith("x-polyglot-")}
        return TranslationResponse(
            audio_bytes=response.content,
            cache_status=_header(headers, "X-Polyglot-Cache", "unknown"),
            cache_strategy=_header(headers, "X-Polyglot-Cache-Strategy", request.cache_strategy),
            similarity=_float_or_none(_header(headers, "X-Polyglot-Similarity")),
            lookup_time=_float_or_none(_header(headers, "X-Polyglot-Lookup-Time")),
            inference_time=_float_or_none(_header(headers, "X-Polyglot-Inference-Time")),
            total_time=total_time,
            decision=_header(headers, "X-Polyglot-Decision", ""),
            translation_id=_header(headers, "X-Polyglot-Translation-Id", ""),
            raw_headers=headers,
        )

    def _url(self, endpoint: str) -> str:
        return self.runtime.base_url + endpoint.lstrip("/")

    def _disable_warnings_if_needed(self) -> None:
        if not self.runtime.verify_ssl:
            urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)


def _float_or_none(value: str | None) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _header(headers: dict[str, str], name: str, default: str | None = None) -> str | None:
    wanted = name.lower()
    for key, value in headers.items():
        if key.lower() == wanted:
            return value
    return default
