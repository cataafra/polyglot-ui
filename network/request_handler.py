import wave
from io import BytesIO
import requests
import urllib3
import logging
from datetime import datetime

from config.config import config

# Set up logging
logger = logging.getLogger(__name__)

is_debug = config.getboolean("general", "debug")
BASE_URL = config.get("api", "base_url_local") if is_debug \
    else config.get("api", "base_url")


def send_request_for_connection_test():
    """ Check if the server is running and can be reached."""
    url = BASE_URL + config.get("api", "health_endpoint")
    logger.info("Testing connection to server...")
    try:
        urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(url, verify=False)

        if response.status_code == 200 and response.json()["status"]:
            logger.info("Connection test successful")
            return True
        else:
            logger.error(f"Connection test failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to server. Please check if the server is running.")
        return False


def send_request_for_processing(audio_data, language, speaker_id):
    """ Send audio data to the server for processing and return the response."""
    url = BASE_URL + config.get("api", "process_endpoint")
    save_to_disk = config.getboolean("audio", "save_to_disk")
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    # Prepare the in-memory WAV file
    buffer = BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_data)
    buffer.seek(0)  # Rewind the buffer to the start

    files = {'file': ('audio.wav', buffer, 'audio/wav')}
    data = {'language': language, 'speaker_id': str(speaker_id)}

    urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, files=files, data=data, verify=False)
    if response.status_code == 200:
        logger.info("Translated audio successfully received.")

        if save_to_disk:
            output_filename = f'C:/Users/afrca/Desktop/School/Licenta/polyglot-tkinter-app/responses/response_{timestamp}.wav'
            with open(output_filename, "wb") as out_f:
                out_f.write(response.content)

        # Return the response content for further processing or direct playback
        return BytesIO(response.content)
    else:
        logger.error(f"Failed to process audio: {response.status_code} - {response.text}")
        return None
