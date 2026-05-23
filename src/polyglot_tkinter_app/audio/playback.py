from __future__ import annotations

import logging
import queue
import threading
import wave
from io import BytesIO
from typing import Any

from polyglot_tkinter_app.audio.devices import AudioDevice

logger = logging.getLogger(__name__)


class AudioPlayer:
    def __init__(self) -> None:
        self._queue: queue.PriorityQueue[tuple[int, tuple[bytes | None, AudioDevice | None]]] = queue.PriorityQueue()
        self._sequence = 0
        self._sequence_lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._is_running = False
        self._pyaudio_instance: Any | None = None

    def start(self) -> None:
        if self._is_running:
            return
        pyaudio = _load_pyaudio()
        self._pyaudio_instance = pyaudio.PyAudio()
        self._is_running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        logger.info("playback_started")

    def enqueue(self, audio_bytes: bytes, output_device: AudioDevice | None = None) -> None:
        if not self._is_running:
            self.start()
        self._queue.put((self._next_sequence(), (audio_bytes, output_device)))

    def stop(self) -> None:
        if not self._is_running:
            return
        self._is_running = False
        self._queue.put((self._next_sequence(), (None, None)))
        if self._thread:
            self._thread.join(timeout=5)
        self._cleanup()
        logger.info("playback_stopped")

    def _worker(self) -> None:
        while True:
            _, (audio_bytes, output_device) = self._queue.get()
            try:
                if audio_bytes is None:
                    return
                self._play_audio_bytes(audio_bytes, output_device)
            finally:
                self._queue.task_done()

    def _play_audio_bytes(self, audio_bytes: bytes, output_device: AudioDevice | None) -> None:
        if self._pyaudio_instance is None:
            return

        try:
            with wave.open(BytesIO(audio_bytes), "rb") as wav_file:
                stream = self._pyaudio_instance.open(
                    format=self._pyaudio_instance.get_format_from_width(wav_file.getsampwidth()),
                    channels=wav_file.getnchannels(),
                    rate=wav_file.getframerate(),
                    output=True,
                    output_device_index=output_device.index if output_device else None,
                )
                logger.info(
                    "playback_started device=%s rate=%s channels=%s",
                    output_device.name if output_device else "default",
                    wav_file.getframerate(),
                    wav_file.getnchannels(),
                )
                data = wav_file.readframes(1024)
                while data:
                    stream.write(data)
                    data = wav_file.readframes(1024)
                stream.stop_stream()
                stream.close()
                logger.info("playback_completed")
        except Exception as exc:
            logger.error("playback_failed error=%s", exc)

    def _next_sequence(self) -> int:
        with self._sequence_lock:
            self._sequence += 1
            return self._sequence

    def _cleanup(self) -> None:
        if self._pyaudio_instance is not None:
            self._pyaudio_instance.terminate()
            self._pyaudio_instance = None


def _load_pyaudio() -> Any:
    try:
        import pyaudio

        return pyaudio
    except ImportError as exc:
        raise RuntimeError("PyAudio is required for audio playback") from exc
