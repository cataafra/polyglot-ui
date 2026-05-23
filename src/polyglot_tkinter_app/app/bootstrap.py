import logging

from polyglot_tkinter_app.api.client import TranslationClient
from polyglot_tkinter_app.gui.splash_screen import SplashScreen
from polyglot_tkinter_app.logging_config import setup_logger
from polyglot_tkinter_app.paths import ensure_runtime_dirs
from polyglot_tkinter_app.settings import RuntimeState, load_settings

logger = logging.getLogger(__name__)


def run() -> None:
    settings = load_settings("config.json")
    ensure_runtime_dirs()
    setup_logger(settings)
    logger.info("app_started")

    runtime = RuntimeState.from_settings(settings)
    client = TranslationClient(runtime)
    app = SplashScreen(settings=settings, runtime=runtime, client=client)
    app.mainloop()
