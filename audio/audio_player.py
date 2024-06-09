import pyaudio
import wave
import queue
import threading
import logging
from audio.audio_utils import get_vb_audio_device_index
from config.config import config

logger = logging.getLogger(__name__)


class AudioPlayer:
    """
    Class to handle audio playback. Uses a separate thread to play audio streams from a queue.
    """

    def __init__(self):
        self.playback_queue = queue.PriorityQueue()
        self.player_thread = None
        self.pyaudio_instance = pyaudio.PyAudio()
        self.sequence_number = 0
        self.is_playing = False
        self.channels = config.getint("audio", "channels")
        self.sample_rate = config.getint("audio", "sample_rate")

    def start_player(self):
        if not self.is_playing:
            self.pyaudio_instance = pyaudio.PyAudio()
            self.is_playing = True
            self.player_thread = threading.Thread(target=self.playback_worker, daemon=True)
            self.player_thread.start()
            logger.info("Audio player started.")

    def stop_player(self):
        if self.is_playing:
            self.is_playing = False
            # Ensure to finish playback of all audio in the queue
            self.player_thread.join()  # Wait until the playback worker has processed all items
            logger.info("Audio player stopped.")

    def playback_worker(self):
        """
        Worker function to play audio streams from the queue.
        """
        while self.is_playing or not self.playback_queue.empty():
            item = self.playback_queue.get()
            if item is None:  # Check for the sentinel value to stop processing
                break
            seq, (audio_stream, output_device) = item
            if audio_stream is None:
                break
            self.play_audio_stream(audio_stream, output_device)
            self.playback_queue.task_done()
        self.cleanup()

    def enqueue_audio(self, audio_stream, output_device=None, sequence=None):
        """
        Enqueue an audio stream for playback.
        """
        if output_device is None:
            output_device = get_vb_audio_device_index()
        if sequence is None:
            sequence = self.generate_sequence()
        self.playback_queue.put((sequence, (audio_stream, output_device)))
        logger.debug(f"Enqueued audio for playback, sequence number: {sequence}")

    def generate_sequence(self):
        """
        Generate a sequence number for the audio stream.
        """
        with threading.Lock():
            self.sequence_number += 1
            return self.sequence_number

    def play_audio_stream(self, audio_stream, output_device):
        """
        Play an audio stream using PyAudio.
        """
        try:
            logger.info(f"Playing audio stream...")
            stream = self.pyaudio_instance.open(format=pyaudio.paInt16, channels=self.channels, rate=self.sample_rate,
                                                output=True, output_device_index=output_device)
            wave_file = wave.open(audio_stream, 'rb')
            data = wave_file.readframes(1024)
            while data:
                stream.write(data)
                data = wave_file.readframes(1024)
            stream.stop_stream()
            stream.close()
            logger.info("Audio playback complete.")
        except Exception as e:
            logger.error(f"Error during audio playback: {str(e)}")

    def cleanup(self):
        self.pyaudio_instance.terminate()
        logger.debug("Audio playback resources cleaned up.")
