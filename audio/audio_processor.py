import sounddevice as sd
import webrtcvad
import numpy as np
import threading
import queue
import logging

from network.request_handler import send_request_for_processing
from config.config import config

from audio.audio_player import AudioPlayer

# Set up logging
logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Audio processor class for recording audio and sending it to the server for processing.
    """
    def __init__(self, input_device=None, language='en', speaker_id=0):
        logger.info("Initializing AudioProcessor...")

        self.audio_player = AudioPlayer()

        self.input_device = input_device

        self.language = language
        self.speaker_id = speaker_id

        self.vad = webrtcvad.Vad(config.getint("audio", "vad_aggressiveness"))
        self.pause_counter = 0

        self.samplerate = config.getint("audio", "sample_rate")
        self.frame_duration = config.getint("audio", "frame_duration_ms")
        self.blocksize = int(self.samplerate * self.frame_duration / 1000)

        self.audio_queue = queue.Queue()
        self.buffer = np.array([], dtype=np.int16)

        self.processing_thread = None
        self.is_recording = False

        logger.info("AudioProcessor successfully initialized.")

    def process_audio(self):
        """
        Process audio data from the audio queue.
        """
        while True:
            audio_data = self.audio_queue.get()
            if audio_data is None:
                return
            audio_stream = send_request_for_processing(audio_data, self.language, self.speaker_id)
            if audio_stream:
                self.audio_player.enqueue_audio(audio_stream)
            self.audio_queue.task_done()

    def _callback(self, indata, frames, time, status):
        """
        Callback function for the audio input stream.
        """
        if status and status.input_overflow:
            logger.warning("Input overflow detected")

        if self.vad.is_speech(indata.tobytes(), self.samplerate):
            self.buffer = np.append(self.buffer, indata[:, 0])
        else:
            self.pause_counter += 1
            if self.pause_counter >= self.samplerate // self.blocksize:
                if len(self.buffer) > 0:
                    logger.info("Speech ended, adding audio data to queue for processing.")
                    self.audio_queue.put(self.buffer.tobytes())
                    self.buffer = np.array([], dtype=np.int16)
                self.pause_counter = 0

    def record_audio(self):
        """
        Start recording audio using Sounddevice.
        """
        logger.info(f"Starting audio recording...")
        try:
            with sd.InputStream(callback=self._callback, device=self.input_device["index"],
                                channels=1,
                                samplerate=self.samplerate,
                                blocksize=self.blocksize, dtype='int16'):
                while self.is_recording:
                    sd.sleep(100)
        except Exception as e:
            logger.error(f"Failed to start audio stream: {str(e)}")

    def start_recording(self):
        """
        Start recording audio, checks for device and language settings.
        """
        if not self.language or not self.input_device:
            logger.error("Cannot start recording. AudioProcessor configuration incomplete.")
            return

        self.is_recording = True
        self.audio_player.start_player()
        self.processing_thread = threading.Thread(target=self.process_audio, daemon=True)
        self.processing_thread.start()
        self.record_audio()

    def stop_recording(self):
        """
        Stop recording and clean up the audio queue.
        """
        self.is_recording = False
        self.audio_queue.put(None)
        self.processing_thread.join()
        self.audio_player.stop_player()
        logger.info("Recording stopped.")

    # Getters and setters
    def get_input_device(self):
        """
        Get the input device.
        """
        return self.input_device

    def set_input_device(self, input_device):
        """
        Set the input device.
        """
        logger.info(f"Setting input device to {input_device['name']}")
        self.input_device = input_device

    def get_language(self):
        """
        Get the language.
        """
        return self.language

    def set_language(self, language):
        """
        Set the language.
        """
        logger.info(f"Setting language to {language}")
        self.language = language

    def get_speaker_id(self):
        """
        Get the speaker ID.
        """
        return self.speaker_id

    def set_speaker_id(self, speaker_id):
        """
        Set the speaker ID.
        """
        logger.info(f"Setting speaker ID to {speaker_id}")
        self.speaker_id = speaker_id
