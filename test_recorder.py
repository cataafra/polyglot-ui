import logging
from audio_processor import AudioProcessor
from audio_player import play_audio, get_vb_audio_device

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    output_device = get_vb_audio_device()
    if output_device is not None:
        logging.info(f"Using output device: {output_device}")
    else:
        logging.error("No suitable output device found. Check if Virtual Audio Cable is installed and selected.")
        return

    # Initialize the AudioProcessor with a callback to play audio through the specified device
    recorder = AudioProcessor(playback_callback=lambda file_path: play_audio(file_path, output_device))
    if not recorder.is_online:
        logging.error("AudioProcessor failed to initialize.")
        return

    try:
        recorder.record_audio_vad()
    except KeyboardInterrupt:
        logging.info("Recording stopped by user.")
    except Exception as e:
        logging.error(f"An error occurred during recording: {e}")


if __name__ == '__main__':
    main()
