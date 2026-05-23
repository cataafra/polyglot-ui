from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import PhotoImage, ttk

from polyglot_tkinter_app.api.client import TranslationClient
from polyglot_tkinter_app.api.models import HealthStatus
from polyglot_tkinter_app.gui.main_menu import MainMenu
from polyglot_tkinter_app.gui.styles import center_window, set_theme, setup_styles
from polyglot_tkinter_app.paths import asset_path
from polyglot_tkinter_app.settings.models import AppSettings, RuntimeState

logger = logging.getLogger(__name__)


class SplashScreen(tk.Tk):
    def __init__(self, *, settings: AppSettings, runtime: RuntimeState, client: TranslationClient):
        super().__init__()
        self.settings = settings
        self.runtime = runtime
        self.client = client
        self.health = HealthStatus(online=False)

        set_theme(settings)
        setup_styles()
        width, height = self._window_size()
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.overrideredirect(True)
        center_window(self, width, height)

        self.logo = None
        self.status_label = None
        self.progress = None
        self.retry_button = None
        self.continue_button = None
        self._setup_ui()

        threading.Thread(target=self._check_server_connection, daemon=True).start()

    def _setup_ui(self) -> None:
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        self.logo = PhotoImage(file=asset_path("polyglot-logo.png")).subsample(2)
        ttk.Label(frame, image=self.logo).pack(pady=5, anchor=tk.S, expand=True)

        self.status_label = ttk.Label(frame, text="Connecting to server...")
        self.status_label.pack(pady=10, anchor=tk.CENTER, expand=True)

        self.progress = ttk.Progressbar(frame, orient="horizontal", length=200)
        self.progress.pack(pady=10, anchor="n", expand=True)
        self.progress.start(25)

        self.retry_button = ttk.Button(frame, text="Try Again", command=self._retry_connection)
        self.continue_button = ttk.Button(frame, text="Continue Offline", command=self._launch_main_menu)

    def _retry_connection(self) -> None:
        self.status_label.config(text="Attempting to connect to the server...")
        self.retry_button.pack_forget()
        self.continue_button.pack_forget()
        self.progress.pack(pady=10, anchor="n", expand=True)
        self.progress.start(25)
        threading.Thread(target=self._check_server_connection, daemon=True).start()

    def _check_server_connection(self) -> None:
        self.health = self.client.health()
        logger.info(
            "server_health_checked online=%s memory=%s mode=%s",
            self.health.online,
            self.health.semantic_memory_enabled,
            self.health.semantic_memory_mode,
        )
        if self.health.online or self.settings.general.debug:
            self.after(400, self._on_success)
        else:
            self.after(400, self._on_fail)

    def _on_success(self) -> None:
        self.progress.stop()
        if self.health.online:
            self.status_label.config(text="Connection successful.")
        else:
            self.status_label.config(text="Server offline. Launching in debug mode.")
        self.after(400, self._launch_main_menu)

    def _on_fail(self) -> None:
        self.progress.stop()
        self.status_label.config(text="Connection failed. Please try again.")
        self.progress.pack_forget()
        self.retry_button.pack(pady=(0, 8), anchor="n", expand=True)
        self.continue_button.pack(pady=0, anchor="n", expand=True)

    def _launch_main_menu(self) -> None:
        self.destroy()
        root = tk.Tk()
        root.withdraw()
        MainMenu(root=root, settings=self.settings, runtime=self.runtime, client=self.client, health=self.health)
        root.mainloop()

    def _window_size(self) -> tuple[int, int]:
        width, height = self.settings.gui.splash_window_size.split("x")
        return int(width), int(height)
