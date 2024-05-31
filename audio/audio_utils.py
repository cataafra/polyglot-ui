import pyaudio


def list_input_devices():
    """
    List all input devices across all APIs.
    """
    p = pyaudio.PyAudio()
    input_devices = []
    num_devices = p.get_device_count()

    for i in range(num_devices):
        dev_info = p.get_device_info_by_index(i)
        if dev_info.get('maxInputChannels') > 0:
            input_devices.append(dev_info)

    p.terminate()
    return input_devices


def get_default_input_device():
    """
    Get the default input device.
    """
    p = pyaudio.PyAudio()
    default_device_index = p.get_default_input_device_info()['index']
    default_device = p.get_device_info_by_index(int(default_device_index))
    p.terminate()
    return default_device


def get_vb_audio_device_index():
    """
    Get the VB Audio Cable device.
    """
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if "CABLE Input" in dev['name']:
            p.terminate()
            return i
    p.terminate()
    return None
