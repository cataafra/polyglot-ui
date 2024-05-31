import sounddevice as sd
import webrtcvad
import numpy as np
import threading
import queue
import logging

import utils.request_handler as rh

from audio_player import AudioPlayer

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')


class AudioProcessor:
    def __init__(self, input_device=None, language='en', speaker_id=0, vad_aggressiveness=3):
        self.audio_player = AudioPlayer()
        self.input_device = input_device
        self.language = language
        self.speaker_id = speaker_id
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.pause_counter = 0
        self.samplerate = 16000
        self.frame_duration = 30
        self.blocksize = int(self.samplerate * self.frame_duration / 1000)
        self.audio_queue = queue.Queue()
        self.buffer = np.array([], dtype=np.int16)
        self.processing_thread = threading.Thread(target=self.process_audio, daemon=True)
        self.processing_thread.start()

        logging.info("AudioRecorder initialized")

    def process_audio(self):
        while True:
            audio_data = self.audio_queue.get()
            audio_stream = rh.send_request_for_processing(audio_data, self.language, self.speaker_id)
            if audio_stream:
                self.audio_player.enqueue_audio(audio_stream)
            self.audio_queue.task_done()

    def _callback(self, indata, frames, time, status):
        """
        Callback function for the audio input stream.
        """
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
        """
        Start recording audio using VAD.
        """
        logging.info(f"Starting audio recording... Press Ctrl+C to stop.")
        logging.debug(
            f"Using device: {self.input_device['name']} with {self.input_device['maxInputChannels']} input channels")
        try:
            with sd.InputStream(callback=self._callback, device=self.input_device["index"],
                                channels=1,
                                samplerate=self.samplerate,
                                blocksize=self.blocksize, dtype='int16'):
                while True:
                    sd.sleep(100)
        except Exception as e:
            logging.error(f"Failed to start audio stream: {str(e)}")

    def start_recording(self):
        """
        Start recording audio, checks for device and language settings.
        """
        if not self.language or not self.input_device:
            logging.error("AudioProcessor configuration incomplete.")
            return

        self.record_audio_vad()

    def stop_recording(self):
        """
        Stop recording and clean up the audio queue.
        """
        self.audio_queue.join()  # Ensure all processing is completed
        logging.info("Recording stopped.")

    # Getters and setters
    def get_input_device(self):
        return self.input_device

    def set_input_device(self, input_device):
        print(f"Setting input device to {input_device}")
        self.input_device = input_device

    def get_language(self):
        return self.language

    def set_language(self, language):
        print(f"Setting language to {language}")
        self.language = language

    def get_speaker_id(self):
        return self.speaker_id

    def set_speaker_id(self, speaker_id):
        print(f"Setting speaker ID to {speaker_id}")
        self.speaker_id = speaker_id
