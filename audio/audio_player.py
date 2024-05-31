import pyaudio
import wave
import queue
import threading
from audio.audio_utils import get_vb_audio_device_index


class AudioPlayer:
    """
    Class to handle audio playback. Uses a separate thread to play audio streams from a queue.
    """
    def __init__(self):
        self.playback_queue = queue.PriorityQueue()
        self.player_thread = threading.Thread(target=self.playback_worker, daemon=True)
        self.player_thread.start()
        self.pyaudio_instance = pyaudio.PyAudio()
        self.sequence_number = 0

    def playback_worker(self):
        """
        Worker function to play audio streams from the queue.
        """
        while True:
            seq, (audio_stream, output_device) = self.playback_queue.get()
            self.play_audio_stream(audio_stream, output_device)
            self.playback_queue.task_done()

    def enqueue_audio(self, audio_stream, output_device=None, sequence=None):
        """
        Enqueue an audio stream for playback.
        """
        if output_device is None:
            output_device = get_vb_audio_device_index()
        if sequence is None:
            sequence = self.generate_sequence()
        self.playback_queue.put((sequence, (audio_stream, output_device)))

    def generate_sequence(self):
        """
        Generate a sequence number for the audio stream.
        """
        with threading.Lock():
            self.sequence_number += 1
            return self.sequence_number

    def play_audio_stream(self, audio_stream, output_device):
        """
        Play an audio stream.
        """
        stream = self.pyaudio_instance.open(format=pyaudio.paInt16, channels=1, rate=16000,
                                            output=True, output_device_index=output_device)
        wave_file = wave.open(audio_stream, 'rb')
        data = wave_file.readframes(1024)
        while data:
            stream.write(data)
            data = wave_file.readframes(1024)
        stream.stop_stream()
        stream.close()

    def close_player(self):
        """
        Safely close the audio player by joining the playback queue and player thread.
        """
        self.playback_queue.join()
        self.player_thread.join()
        self.pyaudio_instance.terminate()
