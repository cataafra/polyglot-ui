import wave
from io import BytesIO
import requests
import logging
from datetime import datetime

BASE_URL = 'http://localhost:8000/'


def send_request_for_connection_test():
    url = BASE_URL + "health/"
    try:
        response = requests.get(url)

        if response.status_code == 200 and response.json()["status"]:
            logging.info("Connection test successful")
            return True
        else:
            logging.error(f"Connection test failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        logging.error("Failed to connect to server. Please check if the server is running.")
        return False


def send_request_for_processing(audio_data, language, speaker_id, save_to_disk=False):
    url = BASE_URL + 'process/'
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

    response = requests.post(url, files=files, data=data)
    if response.status_code == 200:
        logging.info("Audio processed successfully.")

        if save_to_disk:
            output_filename = f'C:/Users/afrca/Desktop/School/Licenta/polyglot-tkinter-app/responses/response_{timestamp}.wav'
            with open(output_filename, "wb") as out_f:
                out_f.write(response.content)

        # Return the response content for further processing or direct playback
        return BytesIO(response.content)
    else:
        logging.error(f"Failed to process audio: {response.status_code} - {response.text}")
        return None
