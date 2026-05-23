from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SpeechSegmenter:
    def __init__(self, *, sample_rate: int, frame_duration_ms: int, aggressiveness: int):
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self._vad = _load_webrtcvad().Vad(aggressiveness)
        self._buffer: list[bytes] = []
        self._silence_frames = 0
        self._flush_after_silence = max(1, int(1000 / frame_duration_ms))

    def accept_frame(self, frame_bytes: bytes) -> bytes | None:
        if self._vad.is_speech(frame_bytes, self.sample_rate):
            self._buffer.append(frame_bytes)
            self._silence_frames = 0
            return None

        if not self._buffer:
            return None

        self._silence_frames += 1
        if self._silence_frames < self._flush_after_silence:
            return None

        segment = b"".join(self._buffer)
        self._buffer.clear()
        self._silence_frames = 0
        logger.info("speech_segment_detected bytes=%s", len(segment))
        return segment

    def flush(self) -> bytes | None:
        if not self._buffer:
            return None
        segment = b"".join(self._buffer)
        self._buffer.clear()
        self._silence_frames = 0
        return segment


def _load_webrtcvad() -> Any:
    try:
        import webrtcvad

        return webrtcvad
    except ImportError as exc:
        raise RuntimeError("webrtcvad is required for speech segmentation") from exc
