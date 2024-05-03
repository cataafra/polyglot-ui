import sounddevice as sd
import webrtcvad
import numpy as np
import threading
import queue
import logging

from request_handler import send_request_for_processing

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')


class AudioProcessor:
    def __init__(self, device=None, vad_aggressiveness=3, samplerate=16000, frame_duration=30, playback_callback=None):
        self.device = device
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.samplerate = samplerate
        self.frame_duration = frame_duration
        self.blocksize = int(self.samplerate * self.frame_duration / 1000)
        self.audio_queue = queue.Queue()
        self.processing_thread = threading.Thread(target=self.process_audio, daemon=True)
        self.processing_thread.start()
        self.buffer = np.array([], dtype=np.int16)
        self.pause_counter = 0
        self.playback_callback = playback_callback

        logging.info("AudioRecorder initialized")

    def process_audio(self):
        while True:
            audio_data = self.audio_queue.get()
            print(f"Processing audio data of length {len(audio_data)}")
            send_request_for_processing(audio_data, "eng", self.playback_callback)
            self.audio_queue.task_done()

    def _callback(self, indata, frames, time, status):
        if status and status.input_overflow:
            logging.warning("Input overflow detected")

        if self.vad.is_speech(indata.tobytes(), self.samplerate):
            self.buffer = np.append(self.buffer, indata[:, 0])
        else:
            self.pause_counter += 1
            if self.pause_counter >= self.samplerate // self.blocksize:
                if len(self.buffer) > 0:
                    logging.debug("Speech ended, adding audio data to queue for processing")
                    self.audio_queue.put(self.buffer.tobytes())
                    self.buffer = np.array([], dtype=np.int16)
                self.pause_counter = 0

    def record_audio_vad(self):
        logging.info("Starting audio recording... Press Ctrl+C to stop.")
        with sd.InputStream(callback=self._callback, device=self.device, channels=1, samplerate=self.samplerate,
                            blocksize=self.blocksize, dtype='int16'):
            while True:
                sd.sleep(100)
