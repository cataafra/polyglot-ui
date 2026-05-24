from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from typing import Callable

from polyglot_tkinter_app.api.client import TranslationClient
from polyglot_tkinter_app.api.models import TranslationRequest, TranslationResponse
from polyglot_tkinter_app.audio.capture import AudioCapture
from polyglot_tkinter_app.audio.playback import AudioPlayer
from polyglot_tkinter_app.audio.vad import SpeechSegmenter
from polyglot_tkinter_app.audio.wav_io import pcm_to_wav_bytes
from polyglot_tkinter_app.paths import HEADERS_DIR, OUTPUTS_DIR
from polyglot_tkinter_app.settings.models import RuntimeState

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TranslationWork:
    wav_bytes: bytes
    reason: str


class TranslationFlow:
    def __init__(
        self,
        *,
        runtime: RuntimeState,
        client: TranslationClient,
        player: AudioPlayer,
        on_translation_completed: Callable[[TranslationResponse], None] | None = None,
        on_translation_failed: Callable[[Exception], None] | None = None,
        on_status_changed: Callable[[str], None] | None = None,
    ):
        self.runtime = runtime
        self.client = client
        self.player = player
        self.on_translation_completed = on_translation_completed
        self.on_translation_failed = on_translation_failed
        self.on_status_changed = on_status_changed
        self._stop_event = threading.Event()
        self._shutdown_event = threading.Event()
        self._work_queue: Queue[TranslationWork | None] = Queue()
        self._capture_thread: threading.Thread | None = None
        self._worker_thread: threading.Thread | None = None
        self._worker_lock = threading.Lock()
        self._segmenter: SpeechSegmenter | None = None
        self._running = False
        self.last_input_wav_bytes: bytes | None = None
        self.last_output_wav_bytes: bytes | None = None

    def start(self) -> None:
        if self._shutdown_event.is_set():
            return
        if self._running:
            return
        if self.runtime.input_device is None:
            self._status("No input device selected.")
            return

        self._running = True
        self._stop_event.clear()
        self.player.start()
        self._segmenter = SpeechSegmenter(
            sample_rate=self.runtime.settings.audio.sample_rate,
            frame_duration_ms=self.runtime.settings.audio.frame_duration_ms,
            aggressiveness=self.runtime.settings.audio.vad_aggressiveness,
        )
        self._ensure_worker()
        self._capture_thread = threading.Thread(target=self._run_capture, daemon=True)
        self._capture_thread.start()
        self._status("Recording...")

    def stop(self) -> None:
        was_running = self._running
        self._running = False
        self._stop_event.set()
        if was_running and self._segmenter:
            final_segment = self._segmenter.flush()
            if final_segment:
                self._submit_pcm(final_segment, reason="flush")
        if self._capture_thread:
            self._capture_thread.join(timeout=5)
        if self._worker_thread and self._worker_thread.is_alive():
            self._work_queue.put(None)
            self._worker_thread.join()
        else:
            self._discard_pending_work()
        self.player.stop()
        self._status("Recording stopped.")

    def shutdown(self) -> None:
        self._shutdown_event.set()
        self._running = False
        self._stop_event.set()
        self._discard_pending_work()
        if self._worker_thread and self._worker_thread.is_alive():
            self._work_queue.put(None)
        if self._capture_thread:
            self._capture_thread.join(timeout=5)
        if self._worker_thread:
            self._worker_thread.join(timeout=0.25)
        self.player.stop()

    def update_runtime(self, runtime: RuntimeState) -> None:
        self.runtime = runtime

    def submit_wav(self, wav_bytes: bytes, *, reason: str = "manual") -> None:
        if self._shutdown_event.is_set():
            return
        self.player.start()
        self._ensure_worker()
        self.last_input_wav_bytes = wav_bytes
        self._save_latest_input(wav_bytes)
        self._work_queue.put(TranslationWork(wav_bytes=wav_bytes, reason=reason))

    def resend_last_input(self) -> bool:
        if self._shutdown_event.is_set():
            return False
        if not self.last_input_wav_bytes:
            self._status("No input captured yet.")
            return False
        self.submit_wav(self.last_input_wav_bytes, reason="resend")
        return True

    def replay_last_output(self) -> bool:
        if self._shutdown_event.is_set():
            return False
        if not self.last_output_wav_bytes:
            self._status("No translated output yet.")
            return False
        self.player.enqueue(self.last_output_wav_bytes, self.runtime.output_device)
        self._status("Replaying last output.")
        return True

    def _run_capture(self) -> None:
        capture = AudioCapture(
            input_device=self.runtime.input_device,
            sample_rate=self.runtime.settings.audio.sample_rate,
            frame_duration_ms=self.runtime.settings.audio.frame_duration_ms,
        )
        try:
            capture.run(self._handle_frame, self._stop_event)
        except Exception as exc:
            self._fail(exc)

    def _handle_frame(self, frame_bytes: bytes) -> None:
        if not self._segmenter:
            return
        segment = self._segmenter.accept_frame(frame_bytes)
        if segment:
            self._submit_pcm(segment, reason="live")

    def _submit_pcm(self, pcm_bytes: bytes, *, reason: str) -> None:
        wav_bytes = pcm_to_wav_bytes(
            pcm_bytes,
            sample_rate=self.runtime.settings.audio.sample_rate,
            channels=self.runtime.settings.audio.channels,
        )
        self.submit_wav(wav_bytes, reason=reason)

    def _process_work(self) -> None:
        while True:
            work = self._work_queue.get()
            try:
                if work is None:
                    return
                self._translate(work)
            finally:
                self._work_queue.task_done()

    def _translate(self, work: TranslationWork) -> None:
        logger.info(
            "translation_requested reason=%s cache_enabled=%s strategy=%s session=%s",
            work.reason,
            self.runtime.semantic_cache_enabled,
            self.runtime.cache_strategy,
            self.runtime.session_id,
        )
        try:
            response = self.client.translate(
                TranslationRequest(
                    audio_bytes=work.wav_bytes,
                    target_language=self.runtime.target_language,
                    speaker_id=self.runtime.speaker_id,
                    session_id=self.runtime.session_id,
                    source_language=self.runtime.source_language,
                    domain=self.runtime.domain,
                    privacy_level=self.runtime.privacy_level,
                    use_semantic_cache=self.runtime.semantic_cache_enabled,
                    cache_strategy=self.runtime.cache_strategy,
                    use_transcript_memory=self.runtime.use_transcript_memory,
                )
            )
            if self._shutdown_event.is_set():
                logger.info("translation_dropped_after_shutdown reason=%s", work.reason)
                return
            self.last_output_wav_bytes = response.audio_bytes
            self._save_latest_output(response)
            self.player.enqueue(response.audio_bytes, self.runtime.output_device)
            logger.info(
                'translation_completed cache=%s layer=%s strategy=%s similarity=%s text_similarity=%s '
                'lookup=%ss transcript=%ss inference=%ss total=%ss decision="%s"',
                response.cache_status,
                response.cache_layer,
                response.cache_strategy,
                _fmt(response.similarity),
                _fmt(response.text_similarity),
                _fmt(response.lookup_time),
                _fmt(response.transcript_time),
                _fmt(response.inference_time),
                _fmt(response.total_time),
                response.decision,
            )
            if self.on_translation_completed:
                self.on_translation_completed(response)
        except Exception as exc:
            self._fail(exc)

    def _ensure_worker(self) -> None:
        if self._shutdown_event.is_set():
            return
        with self._worker_lock:
            if self._worker_thread and self._worker_thread.is_alive():
                return
            self._worker_thread = threading.Thread(target=self._process_work, daemon=True)
            self._worker_thread.start()

    def _status(self, message: str) -> None:
        if self._shutdown_event.is_set():
            return
        if self.on_status_changed:
            self.on_status_changed(message)

    def _fail(self, exc: Exception) -> None:
        logger.error("translation_failed error=%s", exc)
        if self._shutdown_event.is_set():
            return
        if self.on_translation_failed:
            self.on_translation_failed(exc)

    def _discard_pending_work(self) -> None:
        while True:
            try:
                self._work_queue.get_nowait()
            except Empty:
                return
            else:
                self._work_queue.task_done()

    def _save_latest_input(self, wav_bytes: bytes) -> None:
        if not (self.runtime.demo_enabled and self.runtime.settings.demo.save_artifacts):
            return
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUTS_DIR / "latest-input.wav").write_bytes(wav_bytes)

    def _save_latest_output(self, response: TranslationResponse) -> None:
        if not (self.runtime.demo_enabled and self.runtime.settings.demo.save_artifacts):
            return
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        HEADERS_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUTS_DIR / "latest-output.wav").write_bytes(response.audio_bytes)
        _write_json(HEADERS_DIR / "latest-response.json", response.raw_headers)


def _write_json(path: Path, payload: dict[str, str]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _fmt(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.4f}"
