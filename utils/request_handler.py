import requests
import logging
import os
from datetime import datetime
import wave

BASE_URL = 'http://localhost:80/'


def send_request_for_connection_test():
    url = BASE_URL
    try:
        response = requests.get(url)

        if response.status_code == 200:
            logging.info("Connection test successful")
            return True
        else:
            logging.error(f"Connection test failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        logging.error("Failed to connect to server. Please check if the server is running.")
        return False



def send_request_for_processing(audio_data, language, callback=None):
    url = BASE_URL + 'process/'

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = os.path.abspath(f'temp_sample_{timestamp}.wav')
    output_filename = os.path.abspath(
        f'C:/Users/afrca/Desktop/School/Licenta/polyglot-tkinter-app/responses/response_{timestamp}.wav')

    try:
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_data)
        logging.info(f"Written temp audio file {filename}")

        with open(filename, 'rb') as f:
            files = {'file': f}
            data = {'language': language}
            response = requests.post(url=url, files=files, data=data)
            if response.status_code == 200:
                with open(output_filename, "wb") as out_f:
                    out_f.write(response.content)
                    out_f.flush()
                    os.fsync(out_f.fileno())
                logging.info(f"Processed audio response saved to {output_filename}")
                if callback:
                    callback(output_filename)
            else:
                logging.error(f"Failed to process audio: {response.status_code} - {response.text}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
            logging.debug(f"Temporary file {filename} removed")
