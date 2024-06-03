import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from audio.audio_processor import AudioProcessor, logger
from audio.audio_player import AudioPlayer
import sounddevice as sd
import queue
import threading


@pytest.fixture
def audio_processor(mocker):
    # Set up the processor with mocks for external dependencies
    mocker.patch('audio.audio_processor.config.getint',
                 side_effect=lambda x, y: 16000 if y == "sample_rate" else (10 if y == "frame_duration_ms" else 3))
    mocker.patch('audio.audio_processor.webrtcvad.Vad')
    return AudioProcessor(input_device={'index': 1}, language='en', speaker_id=0)


def test_initialization(audio_processor):
    # Test initialization of the audio processor to ensure correct setup
    assert audio_processor.samplerate == 16000
    assert audio_processor.frame_duration == 10
    assert isinstance(audio_processor.audio_player, AudioPlayer)
    assert isinstance(audio_processor.audio_queue, queue.Queue)
    assert audio_processor.buffer.size == 0


def test_process_audio(audio_processor, mocker):
    # Test the processing of audio data including network interaction and queuing
    mocker.patch.object(audio_processor.audio_player, 'enqueue_audio')
    mock_send_request = mocker.patch('audio.audio_processor.send_request_for_processing', return_value=MagicMock())

    # Set up the environment for the test
    audio_processor.audio_queue.put(b'some audio data')
    audio_processor.audio_queue.put(None)

    # Ensure the processing thread executes and terminates properly
    processing_thread = threading.Thread(target=audio_processor.process_audio)
    processing_thread.start()
    processing_thread.join(timeout=5)

    assert not processing_thread.is_alive()
    mock_send_request.assert_called_once_with(b'some audio data', 'en', 0)
    audio_processor.audio_player.enqueue_audio.assert_called_once()


def test_callback(audio_processor, mocker):
    # Test the VAD callback to ensure audio data is handled correctly based on speech detection
    mocker.patch('audio.audio_processor.webrtcvad.Vad.is_speech', return_value=True)
    indata = np.zeros((audio_processor.blocksize, 1), dtype=np.int16)
    audio_processor._callback(indata, len(indata), time=None, status=sd.CallbackFlags())
    assert np.array_equal(audio_processor.buffer, indata[:, 0])


def test_start_recording(audio_processor, mocker):
    # Test the start recording process including external dependencies like audio input and player
    mocker.patch('sounddevice.InputStream', autospec=True)
    mock_record_audio_vad = mocker.patch.object(audio_processor, 'record_audio_vad')
    mocker.patch.object(audio_processor.audio_player, 'start_player')

    audio_processor.start_recording()

    mock_record_audio_vad.assert_called_once()
    assert audio_processor.is_recording
    audio_processor.audio_player.start_player.assert_called_once()


def test_stop_recording(audio_processor, mocker):
    # Test the stop recording functionality to ensure proper cleanup and state management
    mocked_thread = mocker.Mock()
    audio_processor.processing_thread = mocked_thread
    mocker.patch.object(audio_processor.audio_player, 'stop_player')

    audio_processor.stop_recording()

    assert not audio_processor.is_recording
    sentinel = audio_processor.audio_queue.get_nowait()
    assert sentinel is None
    mocked_thread.join.assert_called_once()
    audio_processor.audio_player.stop_player.assert_called_once()


def test_getters(audio_processor):
    assert audio_processor.get_input_device() == {'index': 1}
    assert audio_processor.get_language() == 'en'
    assert audio_processor.get_speaker_id() == 0


@pytest.mark.parametrize("method, attribute, value", [
    ("set_input_device", "input_device", {'index': 2}),
    ("set_language", "language", 'fr'),
    ("set_speaker_id", "speaker_id", 1)
])
def test_setters(audio_processor, method, attribute, value):
    # Test setter methods to ensure they correctly update processor attributes
    getattr(audio_processor, method)(value)
    assert getattr(audio_processor, attribute) == value
