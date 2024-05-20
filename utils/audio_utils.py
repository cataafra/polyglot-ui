import pyaudio


def get_api_info():
    """
    Get the API info and index for the Windows WASAPI audio API.
    """
    p = pyaudio.PyAudio()
    api_info, api_index = None, 0
    for i in range(p.get_host_api_count()):
        current_api_info = p.get_host_api_info_by_index(i)
        if i == 0:
            api_info = current_api_info
        elif current_api_info['name'] == 'Windows WASAPI':
            api_info, api_index = current_api_info, i
            break
    p.terminate()
    return api_info, api_index


def list_input_devices():
    """
    List all input devices.
    """
    p = pyaudio.PyAudio()
    api_info, api_index = get_api_info()
    num_devices = api_info.get('deviceCount')
    input_devices = []

    for i in range(num_devices):
        dev_info = p.get_device_info_by_host_api_device_index(api_index, i)
        if dev_info.get('maxInputChannels') > 0:
            input_devices.append(dev_info)
    p.terminate()
    return input_devices


def get_default_input_device():
    """
    Get the default input device.
    """
    api_info, api_index = get_api_info()
    p = pyaudio.PyAudio()

    default_device = None
    num_devices = api_info['deviceCount']
    for i in range(num_devices):
        dev_info = p.get_device_info_by_host_api_device_index(api_index, i)
        if dev_info['maxInputChannels'] > 0:
            if dev_info['structVersion'] == p.get_default_input_device_info()['structVersion']:
                default_device = dev_info
                break
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
            return i
    p.terminate()
    return None