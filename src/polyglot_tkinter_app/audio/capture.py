from __future__ import annotations

import logging
import threading
from typing import Callable

from polyglot_tkinter_app.audio.devices import AudioDevice

logger = logging.getLogger(__name__)


class AudioCapture:
    def __init__(self, *, input_device: AudioDevice, sample_rate: int, frame_duration_ms: int):
        self.input_device = input_device
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.blocksize = int(sample_rate * frame_duration_ms / 1000)

    def run(self, on_frame: Callable[[bytes], None], stop_event: threading.Event) -> None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("sounddevice is required for audio capture") from exc

        def callback(indata, frames, time_info, status) -> None:
            if status and getattr(status, "input_overflow", False):
                logger.warning("audio_input_overflow")
            on_frame(indata[:, 0].tobytes())

        logger.info("recording_started device=%s", self.input_device.name)
        try:
            with sd.InputStream(
                callback=callback,
                device=self.input_device.index,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.blocksize,
                dtype="int16",
            ):
                while not stop_event.is_set():
                    sd.sleep(100)
        finally:
            logger.info("recording_stopped")
