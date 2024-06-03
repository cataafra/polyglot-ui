import queue
import threading

import pytest
from unittest.mock import patch, MagicMock
from audio.audio_player import AudioPlayer


def test_initialization():
    with patch('pyaudio.PyAudio') as mock_pyaudio:
        player = AudioPlayer()
        mock_pyaudio.assert_called_once()
        assert isinstance(player.playback_queue, queue.PriorityQueue)
        assert not player.is_playing


def test_start_stop_player():
    with patch('pyaudio.PyAudio') as mock_pyaudio, \
            patch('threading.Thread.start') as mock_thread_start:
        player = AudioPlayer()
        player.start_player()
        assert player.is_playing
        mock_thread_start.assert_called_once()
        mock_pyaudio.assert_called()

    with patch('threading.Thread.join'), \
            patch('logging.Logger.info') as mock_logger_info:
        player.stop_player()
        assert not player.is_playing
        mock_logger_info.assert_any_call("Audio player stopped.")


def test_enqueue_audio_and_playback_worker():
    player = AudioPlayer()
    with patch.object(player, 'play_audio_stream') as mock_play_audio_stream, \
            patch('audio.audio_player.get_vb_audio_device_index') as mock_get_device_index:
        mock_get_device_index.return_value = 1
        audio_stream = MagicMock()

        # Enqueue an audio stream with a specific output device
        player.enqueue_audio(audio_stream, output_device=1)

        # Manually add a sentinel value to allow the loop to exit properly
        player.playback_queue.put((999, (None, None)))  # High sequence number to ensure it's processed last

        # Start the playback worker in a separate thread
        player.is_playing = True  # Ensure the player is "playing" to enter the loop
        thread = threading.Thread(target=player.playback_worker)
        thread.start()

        # Wait for the queue to empty which means the sentinel has been processed
        while not player.playback_queue.empty():
            pass

        # Ensure the player stops after processing
        player.is_playing = False
        thread.join(timeout=1)  # Attempt to join the thread with a timeout

        assert not thread.is_alive(), "Thread should have terminated"
        assert player.playback_queue.empty(), "Playback queue should be empty after processing"
        mock_play_audio_stream.assert_called_once_with(audio_stream, 1)

        # Cleanup to ensure no side effects for other tests
        player.cleanup()


def test_play_audio_stream_error_handling():
    player = AudioPlayer()
    with patch('pyaudio.PyAudio.open', side_effect=Exception("Test Error")), \
            patch('logging.Logger.error') as mock_logger_error:
        player.play_audio_stream("fake_stream", 1)
        mock_logger_error.assert_called_with("Error during audio playback: Test Error")


def test_cleanup():
    player = AudioPlayer()
    with patch('pyaudio.PyAudio.terminate'), \
         patch('logging.Logger.debug') as mock_logger_debug:
        player.cleanup()
        mock_logger_debug.assert_called_with("Audio playback resources cleaned up.")