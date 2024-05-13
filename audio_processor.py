import sounddevice as sd
import webrtcvad
import numpy as np
import threading
import queue
import logging

import utils.request_handler as rh

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')


class AudioProcessor:
    def __init__(self, input_device=None, language=None, speaker_id=0, vad_aggressiveness=3, playback_callback=None):
        # Check if the server is running
        if not rh.send_request_for_connection_test():
            logging.error("Connection test failed. Please check if the server is running.")
            self.is_online = True
            return

        # Set the online status
        self.is_online = True

        # Basic audio processing setup
        self.input_device = input_device
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.samplerate = 16000
        self.frame_duration = 30
        self.blocksize = int(self.samplerate * self.frame_duration / 1000)
        self.audio_queue = queue.Queue()
        self.buffer = np.array([], dtype=np.int16)
        self.pause_counter = 0
        self.playback_callback = playback_callback

        # Start the audio processing thread
        self.processing_thread = threading.Thread(target=self.process_audio, daemon=True)
        self.processing_thread.start()

        # Set the target language for translation
        self.language = language

        # Set the speaker ID for the audio
        self.speaker_id = speaker_id

        logging.info("AudioRecorder initialized")

    def process_audio(self):
        """
        Process audio data from the audio queue and send it to the server for processing.
        """
        while True:
            audio_data = self.audio_queue.get()
            print(f"Processing audio data of length {len(audio_data)}")
            rh.send_request_for_processing(audio_data, self.language, self.playback_callback)
            self.audio_queue.task_done()

    def _callback(self, indata, frames, time, status):
        """
        Callback function for the audio input stream.
        :param indata: waveform data from the input stream
        :param frames: frame count
        :param time: time
        :param status: input status
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
        Start recording audio using the VAD.
        """
        logging.info("Starting audio recording... Press Ctrl+C to stop.")
        with sd.InputStream(callback=self._callback, device=self.input_device, channels=1, samplerate=self.samplerate,
                            blocksize=self.blocksize, dtype='int16'):
            while True:
                sd.sleep(100)

    def start_recording(self):
        """
        Start recording audio using the VAD. Used for the GUI.
        """
        if not self.is_online:
            logging.error("AudioProcessor is not online.")
            return

        if not self.language:
            logging.error("Language not set.")
            return

        if not self.input_device:
            logging.error("Input device not set.")
            return

        self.audio_queue.queue.clear()
        self.buffer = np.array([], dtype=np.int16)
        self.pause_counter = 0
        self.record_audio_vad()

    def stop_recording(self):
        """
        Stop recording audio. Used for the GUI.
        """
        self.audio_queue.join()
        logging.info("Recording stopped.")
        return self.buffer.tobytes()

    # Getters and setters
    def get_input_device(self):
        return self.input_device

    def set_input_device(self, input_device):
        self.input_device = input_device

    def get_language(self):
        return self.language

    def set_language(self, language):
        self.language = language
