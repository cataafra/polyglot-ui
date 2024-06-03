from unittest.mock import patch, MagicMock
import pytest
from audio.audio_utils import list_input_devices, get_default_input_device, get_vb_audio_device_index


def test_list_input_devices():
    with patch('pyaudio.PyAudio') as mock_pyaudio:
        mock_pyaudio_instance = MagicMock()
        mock_pyaudio.return_value = mock_pyaudio_instance
        mock_pyaudio_instance.get_device_count.return_value = 2
        mock_pyaudio_instance.get_device_info_by_index.side_effect = [
            {'maxInputChannels': 1, 'name': 'Input Device 1'},
            {'maxInputChannels': 0, 'name': 'Output Device 1'}
        ]

        devices = list_input_devices()

        assert len(devices) == 1
        assert devices[0]['name'] == 'Input Device 1'
        mock_pyaudio_instance.terminate.assert_called_once()


def test_get_default_input_device():
    with patch('pyaudio.PyAudio') as mock_pyaudio:
        mock_pyaudio_instance = MagicMock()
        mock_pyaudio.return_value = mock_pyaudio_instance
        mock_pyaudio_instance.get_default_input_device_info.return_value = {'index': 0}
        mock_pyaudio_instance.get_device_info_by_index.return_value = {'name': 'Default Input Device'}

        default_device = get_default_input_device()

        assert default_device['name'] == 'Default Input Device'
        mock_pyaudio_instance.terminate.assert_called_once()


def test_get_vb_audio_device_index():
    with patch('pyaudio.PyAudio') as mock_pyaudio:
        mock_pyaudio_instance = MagicMock()
        mock_pyaudio.return_value = mock_pyaudio_instance
        mock_pyaudio_instance.get_device_count.return_value = 3
        mock_pyaudio_instance.get_device_info_by_index.side_effect = [
            {'name': 'Other Device'},
            {'name': 'CABLE Input (VB-Audio Virtual Cable)'},
            {'name': 'Another Device'}
        ]

        vb_index = get_vb_audio_device_index()

        assert vb_index == 1
        mock_pyaudio_instance.terminate.assert_called_once()
