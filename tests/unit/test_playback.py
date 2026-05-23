import time

from polyglot_tkinter_app.audio.playback import AudioPlayer


def test_stop_without_start_returns_immediately():
    player = AudioPlayer()
    start = time.perf_counter()

    player.stop()

    assert time.perf_counter() - start < 0.5
