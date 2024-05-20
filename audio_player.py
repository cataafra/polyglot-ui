import pyaudio
import wave
import queue
import threading
from utils.audio_utils import get_vb_audio_device_index


class AudioPlayer:
    def __init__(self):
        self.playback_queue = queue.PriorityQueue()
        self.player_thread = threading.Thread(target=self.playback_worker, daemon=True)
        self.player_thread.start()

    def playback_worker(self):
        """ Continuously play audio files from the queue in the order they were enqueued. """
        p = pyaudio.PyAudio()
        last_sequence = 0
        buffer = {}

        while True:
            seq, (wav_path, output_device) = self.playback_queue.get()
            # Wait for the correct sequence if necessary
            while seq > last_sequence + 1:
                buffer[seq] = (wav_path, output_device)
                seq, (wav_path, output_device) = self.playback_queue.get()

            self.play_audio_file(wav_path, output_device, p)
            last_sequence = seq

            # Check buffer for the next item
            if last_sequence + 1 in buffer:
                wav_path, output_device = buffer.pop(last_sequence + 1)
                self.play_audio_file(wav_path, output_device, p)
                last_sequence += 1

            self.playback_queue.task_done()

    def enqueue_audio(self, wav_path, output_device=None, sequence=None):
        """ Add an audio file to the playback queue. """
        if output_device is None:
            output_device = get_vb_audio_device_index()
        if sequence is None:
            sequence = self.generate_sequence()  # Implement this method based on timestamp or an incrementing counter
        self.playback_queue.put((sequence, (wav_path, output_device)))

    def play_audio_file(self, wav_path, output_device, pyaudio_instance):
        """ Play an audio file with the specified output device. """
        wf = wave.open(wav_path, 'rb')
        stream = pyaudio_instance.open(format=pyaudio_instance.get_format_from_width(wf.getsampwidth()),
                                       channels=wf.getnchannels(),
                                       rate=wf.getframerate(),
                                       output=True,
                                       output_device_index=output_device)
        chunk = 1024
        data = wf.readframes(chunk)
        while data:
            stream.write(data)
            data = wf.readframes(chunk)
        stream.stop_stream()
        stream.close()
        wf.close()

    def close_player(self):
        """ Gracefully close the PyAudio instance and stop the thread. """
        self.playback_queue.join()  # Ensure all queued audio has been played
        self.player_thread.join()
