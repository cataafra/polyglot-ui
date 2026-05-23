import logging
from logging.handlers import RotatingFileHandler

from polyglot_tkinter_app.paths import ensure_runtime_dirs
from polyglot_tkinter_app.settings.models import AppSettings


def setup_logger(settings: AppSettings) -> None:
    ensure_runtime_dirs()

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if settings.general.debug else logging.INFO)
    root.handlers.clear()

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    root.addHandler(console)

    if settings.general.save_logs:
        file_handler = RotatingFileHandler(
            settings.general.log_file,
            maxBytes=10_485_760,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
