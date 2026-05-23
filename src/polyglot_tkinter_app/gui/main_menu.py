from __future__ import annotations

import logging
import threading
import tkinter as tk
import webbrowser
from tkinter import PhotoImage, ttk
from typing import Any

from polyglot_tkinter_app.api.client import TranslationClient
from polyglot_tkinter_app.api.models import HealthStatus, TranslationResponse
from polyglot_tkinter_app.audio.devices import AudioDevice, AudioDeviceRegistry
from polyglot_tkinter_app.audio.playback import AudioPlayer
from polyglot_tkinter_app.gui.styles import center_window, color_title_bar, set_theme, setup_styles, toggle_theme
from polyglot_tkinter_app.languages import TARGET_LANGUAGES
from polyglot_tkinter_app.orchestration.translation_flow import TranslationFlow
from polyglot_tkinter_app.paths import asset_path
from polyglot_tkinter_app.settings.models import AppSettings, RuntimeState

logger = logging.getLogger(__name__)

BACK_ICON = "\u2190"
SERVER_ONLINE_ICON = "\u2705"
SERVER_OFFLINE_ICON = "\u274c"


class MainMenu:
    def __init__(
        self,
        *,
        root: tk.Tk,
        settings: AppSettings,
        runtime: RuntimeState,
        client: TranslationClient,
        health: HealthStatus,
    ):
        self.root = root
        self.settings = settings
        self.runtime = runtime
        self.client = client
        self.health = health
        self.registry = AudioDeviceRegistry()
        self.input_devices: list[AudioDevice] = self._safe_devices(self.registry.list_input_devices)
        self.output_devices: list[AudioDevice] = self._safe_devices(self.registry.list_output_devices)
        self.event_rows: list[str] = []

        self._select_initial_devices()
        self.flow = TranslationFlow(
            runtime=runtime,
            client=client,
            player=AudioPlayer(),
            on_translation_completed=self._threadsafe_translation_completed,
            on_translation_failed=self._threadsafe_translation_failed,
            on_status_changed=self._threadsafe_status,
        )

        self.recording = tk.BooleanVar(value=False)
        self.mode_var = tk.StringVar(value=self.runtime.ui_mode.title())
        self.input_var = tk.StringVar(value=self._device_label(self.runtime.input_device))
        self.output_var = tk.StringVar(value=self._device_label(self.runtime.output_device))
        self.language_var = tk.StringVar(value="English")
        self.voice_var = tk.StringVar(value="Voice 1")
        self.backend_var = tk.StringVar(value=self.runtime.backend_profile)
        self.cache_var = tk.BooleanVar(value=self.runtime.semantic_cache_enabled)
        self.strategy_var = tk.StringVar(value=self.runtime.cache_strategy)
        self.domain_var = tk.StringVar(value=self.runtime.domain)
        self.privacy_var = tk.StringVar(value=self.runtime.privacy_level)

        self.logo = None
        self.record_icon = None
        self.main_frame = None
        self.info_frame = None
        self.demo_panel = None
        self.status_label = None
        self.server_status = None
        self.record_button = None
        self.metric_labels: dict[str, ttk.Label] = {}
        self.event_log = None
        self.session_label = None
        self.email_entry = None
        self.subject_entry = None
        self.message_text = None
        self.tray_icon_image = None
        self.tray_icon = None
        self.tray_thread = None

        self._setup_window()
        self._setup_ui()
        self._apply_mode()

    def _setup_window(self) -> None:
        self.root.title(self.settings.gui.title)
        try:
            self.root.iconbitmap(asset_path("polyglot-icon.ico"))
        except Exception:
            pass
        width, height = self._window_size(self.settings.gui.main_window_size)
        center_window(self.root, width, height)
        self.root.minsize(800, 500)
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self._hide_window_to_tray)
        self.root.after(100, self.root.deiconify)

    def _setup_ui(self) -> None:
        set_theme(self.settings)
        setup_styles()
        color_title_bar(self.root, self.settings)

        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(column=0, row=0, sticky=tk.NSEW)
        self.info_frame = ttk.Frame(self.root, padding="20")
        self.info_frame.grid(column=0, row=0, sticky=tk.NSEW)
        self.info_frame.grid_remove()

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.info_frame.columnconfigure(0, weight=1)

        self._setup_header()
        self._setup_settings()
        self._setup_demo_panel()
        self._setup_record_button()
        self._setup_status_bar()
        self._setup_info_page()

    def _setup_header(self) -> None:
        header = ttk.Frame(self.main_frame)
        header.grid(column=0, row=0, columnspan=2, sticky=tk.EW)
        header.columnconfigure(1, weight=1)

        self.logo = PhotoImage(file=asset_path("polyglot-logo.png")).subsample(4)
        ttk.Label(header, image=self.logo).grid(column=0, row=0, sticky=tk.W, pady=10)
        ttk.Label(header, text="Dashboard", font=("", 24)).grid(column=1, row=0, sticky=tk.W, padx=(20, 0), pady=10)

        controls = ttk.Frame(header)
        controls.grid(column=2, row=0, sticky=tk.E)
        ttk.Button(controls, text="\U0001F3A8", command=lambda: toggle_theme(self.root, self.settings)).grid(
            column=0, row=0, padx=(0, 8)
        )
        ttk.Button(controls, text="i", command=self._open_info, padding=(14, 3)).grid(column=1, row=0, padx=(0, 8))
        ttk.Radiobutton(
            controls,
            text="User",
            value="User",
            variable=self.mode_var,
            command=self._on_mode_changed,
        ).grid(column=2, row=0, padx=(8, 2))
        ttk.Radiobutton(
            controls,
            text="Demo",
            value="Demo",
            variable=self.mode_var,
            command=self._on_mode_changed,
        ).grid(column=3, row=0, padx=(2, 0))

    def _setup_settings(self) -> None:
        settings_frame = ttk.Frame(self.main_frame)
        settings_frame.grid(column=0, row=1, columnspan=2, sticky=tk.NSEW)
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.columnconfigure(1, weight=1)

        ttk.Label(settings_frame, text="Settings", font=("", 16)).grid(column=0, row=0, sticky=tk.W, pady=(28, 10))

        ttk.Label(settings_frame, text="Select Input Device:").grid(column=0, row=1, sticky=tk.W, padx=(0, 10), pady=8)
        input_menu = ttk.Combobox(
            settings_frame,
            textvariable=self.input_var,
            values=[self._device_label(device) for device in self.input_devices],
            state="readonly",
            width=30,
            style="Custom.TCombobox",
        )
        input_menu.grid(column=0, row=2, sticky=tk.EW, padx=(0, 10))
        input_menu.bind("<<ComboboxSelected>>", self._on_input_selected)
        input_menu.bind("<MouseWheel>", lambda event: "break")

        ttk.Label(settings_frame, text="Select Language:").grid(column=0, row=3, sticky=tk.W, padx=(0, 10), pady=8)
        language_menu = ttk.Combobox(
            settings_frame,
            textvariable=self.language_var,
            values=list(TARGET_LANGUAGES.keys()),
            state="readonly",
            width=30,
            style="Custom.TCombobox",
        )
        language_menu.grid(column=0, row=4, sticky=tk.EW, padx=(0, 10))
        language_menu.bind("<<ComboboxSelected>>", self._on_language_selected)
        language_menu.bind("<MouseWheel>", lambda event: "break")

        ttk.Label(settings_frame, text="Select Voice - experimental:").grid(
            column=1, row=1, sticky=tk.W, padx=(10, 0), pady=8
        )
        voice_menu = ttk.Combobox(
            settings_frame,
            textvariable=self.voice_var,
            values=("Voice 1", "Voice 2", "Voice 3"),
            state="readonly",
            width=30,
            style="Custom.TCombobox",
        )
        voice_menu.grid(column=1, row=2, sticky=tk.EW, padx=(10, 0))
        voice_menu.bind("<<ComboboxSelected>>", self._on_voice_selected)
        voice_menu.bind("<MouseWheel>", lambda event: "break")

    def _setup_demo_panel(self) -> None:
        self.demo_panel = ttk.LabelFrame(self.main_frame, text="Demo Controls", padding="12")
        self.demo_panel.grid(column=0, row=2, columnspan=2, sticky=tk.NSEW, pady=(22, 0))
        self.demo_panel.columnconfigure(0, weight=1)
        self.demo_panel.columnconfigure(1, weight=1)
        self.demo_panel.columnconfigure(2, weight=1)

        ttk.Label(self.demo_panel, text="Backend").grid(column=0, row=0, sticky=tk.W, padx=(0, 8))
        backend_menu = ttk.Combobox(
            self.demo_panel,
            textvariable=self.backend_var,
            values=list(self.settings.api.profiles.keys()),
            state="readonly",
            style="Custom.TCombobox",
        )
        backend_menu.grid(column=0, row=1, sticky=tk.EW, padx=(0, 8), pady=(4, 10))
        backend_menu.bind("<<ComboboxSelected>>", self._on_backend_selected)

        ttk.Label(self.demo_panel, text="Output Device").grid(column=1, row=0, sticky=tk.W, padx=8)
        output_menu = ttk.Combobox(
            self.demo_panel,
            textvariable=self.output_var,
            values=[self._device_label(device) for device in self.output_devices],
            state="readonly",
            style="Custom.TCombobox",
        )
        output_menu.grid(column=1, row=1, sticky=tk.EW, padx=8, pady=(4, 10))
        output_menu.bind("<<ComboboxSelected>>", self._on_output_selected)

        cache_check = ttk.Checkbutton(
            self.demo_panel,
            text="Semantic Cache",
            variable=self.cache_var,
            command=self._on_cache_changed,
        )
        cache_check.grid(column=2, row=1, sticky=tk.W, padx=(8, 0), pady=(4, 10))

        ttk.Label(self.demo_panel, text="Strategy").grid(column=0, row=2, sticky=tk.W, padx=(0, 8))
        strategy_menu = ttk.Combobox(
            self.demo_panel,
            textvariable=self.strategy_var,
            values=("exact", "semantic", "context"),
            state="readonly",
            style="Custom.TCombobox",
        )
        strategy_menu.grid(column=0, row=3, sticky=tk.EW, padx=(0, 8), pady=(4, 10))
        strategy_menu.bind("<<ComboboxSelected>>", self._on_strategy_selected)

        ttk.Label(self.demo_panel, text="Domain").grid(column=1, row=2, sticky=tk.W, padx=8)
        domain_entry = ttk.Entry(self.demo_panel, textvariable=self.domain_var)
        domain_entry.grid(column=1, row=3, sticky=tk.EW, padx=8, pady=(4, 10))
        domain_entry.bind("<FocusOut>", self._on_domain_changed)
        domain_entry.bind("<Return>", self._on_domain_changed)

        ttk.Label(self.demo_panel, text="Privacy").grid(column=2, row=2, sticky=tk.W, padx=(8, 0))
        privacy_menu = ttk.Combobox(
            self.demo_panel,
            textvariable=self.privacy_var,
            values=("transient", "session", "private", "persistent"),
            state="readonly",
            style="Custom.TCombobox",
        )
        privacy_menu.grid(column=2, row=3, sticky=tk.EW, padx=(8, 0), pady=(4, 10))
        privacy_menu.bind("<<ComboboxSelected>>", self._on_privacy_selected)

        metrics = ttk.Frame(self.demo_panel)
        metrics.grid(column=0, row=4, columnspan=2, sticky=tk.NSEW, pady=(8, 0), padx=(0, 8))
        metrics.columnconfigure(1, weight=1)
        ttk.Label(metrics, text="Last Translation", style="Accent.TLabel").grid(column=0, row=0, columnspan=2, sticky=tk.W)
        for index, key in enumerate(("Cache", "Strategy", "Similarity", "Lookup", "Inference", "Total", "Decision")):
            ttk.Label(metrics, text=f"{key}:").grid(column=0, row=index + 1, sticky=tk.W, pady=1)
            label = ttk.Label(metrics, text="-", style="Metrics.TLabel")
            label.grid(column=1, row=index + 1, sticky=tk.W, pady=1)
            self.metric_labels[key] = label

        actions = ttk.Frame(self.demo_panel)
        actions.grid(column=2, row=4, sticky=tk.NSEW, pady=(8, 0), padx=(8, 0))
        actions.columnconfigure(0, weight=1)
        self.session_label = ttk.Label(actions, text=f"Session: {self.runtime.session_id[:8]}")
        self.session_label.grid(column=0, row=0, sticky=tk.W, pady=(0, 8))
        ttk.Button(actions, text="Reset Session", command=self._reset_session).grid(column=0, row=1, sticky=tk.EW, pady=3)
        ttk.Button(actions, text="Resend Last Input", command=self._resend_last_input).grid(
            column=0, row=2, sticky=tk.EW, pady=3
        )
        ttk.Button(actions, text="Replay Last Output", command=self._replay_last_output).grid(
            column=0, row=3, sticky=tk.EW, pady=3
        )

        self.event_log = tk.Listbox(self.demo_panel, height=4, activestyle="none")
        self.event_log.grid(column=0, row=5, columnspan=3, sticky=tk.EW, pady=(12, 0))

    def _setup_record_button(self) -> None:
        self.record_icon = PhotoImage(file=asset_path("record-icon.png")).subsample(2)
        self.record_button = ttk.Button(
            self.main_frame,
            text="  Start Recording",
            command=self._toggle_recording,
            style="Recording.TButton",
            image=self.record_icon,
            compound=tk.LEFT,
        )
        self.record_button.grid(column=0, row=3, columnspan=2, sticky=tk.NSEW, pady=(24, 0))

    def _setup_status_bar(self) -> None:
        status_frame = ttk.Frame(self.main_frame)
        status_frame.grid(column=0, row=4, columnspan=2, sticky=tk.NSEW)
        status_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(1, weight=1)

        self.status_label = ttk.Label(status_frame, text="Ready", anchor=tk.W)
        self.status_label.grid(column=0, row=0, sticky=tk.W, pady=(10, 0))

        server_text = self._server_status_text()
        self.server_status = ttk.Label(status_frame, text=server_text, anchor=tk.E)
        self.server_status.grid(column=1, row=0, sticky=tk.E, pady=(10, 0))

    def _setup_info_page(self) -> None:
        frame = self.info_frame
        frame.columnconfigure(0, weight=1)

        title_frame = ttk.Frame(frame)
        title_frame.grid(column=0, row=0, sticky=tk.W, padx=0, pady=(25, 0))

        ttk.Button(title_frame, text=BACK_ICON, command=self._show_main_menu).grid(
            column=0, row=0, sticky=tk.W, padx=0, pady=(0, 12)
        )
        ttk.Label(title_frame, text="Information & Help", font=("", 24)).grid(
            column=1, row=0, sticky=tk.SW, padx=(20, 0), pady=(0, 10)
        )

        ttk.Label(frame, text="Polyglot, version 2.0 - speech-to-speech translation client").grid(
            column=0, row=1, sticky=tk.W, padx=0, pady=(10, 10)
        )

        ttk.Label(frame, text="Demo Mode", font=("", 16)).grid(column=0, row=2, sticky=tk.W, padx=0, pady=(30, 10))
        ttk.Label(
            frame,
            text=(
                "Use Demo Mode to select speaker output, toggle semantic cache, "
                "inspect cache hits, and compare lookup/inference time."
            ),
            wraplength=720,
            justify=tk.LEFT,
        ).grid(column=0, row=3, sticky=tk.W, padx=0, pady=(0, 10))

        ttk.Label(frame, text="Connect with me", font=("", 16)).grid(
            column=0, row=4, sticky=tk.W, padx=0, pady=(30, 10)
        )
        social_frame = ttk.Frame(frame)
        social_frame.grid(column=0, row=5, sticky=tk.W, padx=0, pady=(10, 10))
        ttk.Button(
            social_frame,
            text="LinkedIn",
            command=lambda: webbrowser.open("https://www.linkedin.com/in/cataafra/"),
        ).grid(column=0, row=0, sticky=tk.W, padx=(0, 5))
        ttk.Button(
            social_frame,
            text="GitHub",
            command=lambda: webbrowser.open("https://github.com/cataafra"),
        ).grid(column=1, row=0, sticky=tk.W, padx=5)

        email_frame = ttk.Frame(frame)
        email_frame.grid(column=0, row=6, sticky=tk.EW, pady=20)
        email_frame.columnconfigure(0, weight=1)

        ttk.Label(email_frame, text="Having issues?", font=("", 16)).grid(
            column=0, row=0, sticky=tk.W, padx=0, pady=(0, 10)
        )
        self.email_entry = ttk.Entry(email_frame)
        self.email_entry.grid(column=0, row=1, sticky=tk.EW)
        self.email_entry.insert(0, "Email address")

        self.subject_entry = ttk.Entry(email_frame)
        self.subject_entry.grid(column=0, row=2, sticky=tk.EW, pady=(10, 10))
        self.subject_entry.insert(0, "Subject")

        self.message_text = tk.Text(email_frame, height=3)
        self.message_text.grid(column=0, row=3, sticky=tk.EW)

        ttk.Button(email_frame, text="Send us an email", command=self._send_email).grid(
            column=0, row=4, sticky=tk.E, pady=(10, 0)
        )

    def _toggle_recording(self) -> None:
        if not self.recording.get():
            self.recording.set(True)
            self.record_button.config(text="  Stop Recording")
            self._sync_runtime_from_ui()
            threading.Thread(target=self.flow.start, daemon=True).start()
        else:
            self.recording.set(False)
            self.record_button.config(text="  Start Recording")
            threading.Thread(target=self.flow.stop, daemon=True).start()

    def _sync_runtime_from_ui(self) -> None:
        self.runtime.target_language = TARGET_LANGUAGES.get(self.language_var.get(), "eng")
        self.runtime.speaker_id = str(("Voice 1", "Voice 2", "Voice 3").index(self.voice_var.get()))
        self.runtime.semantic_cache_enabled = self.cache_var.get()
        self.runtime.cache_strategy = self.strategy_var.get()
        self.runtime.domain = self.domain_var.get().strip() or "demo"
        self.runtime.privacy_level = self.privacy_var.get()
        self.flow.update_runtime(self.runtime)

    def _apply_mode(self) -> None:
        self.runtime.ui_mode = self.mode_var.get().lower()
        if self.runtime.demo_enabled:
            if self.demo_panel:
                self.demo_panel.grid()
            self._select_default_demo_output()
        else:
            if self.demo_panel:
                self.demo_panel.grid_remove()
            self._select_default_user_output()
        self.output_var.set(self._device_label(self.runtime.output_device))
        self.flow.update_runtime(self.runtime)
        self._resize_for_mode()

    def _on_mode_changed(self) -> None:
        self._apply_mode()
        logger.info("mode_changed mode=%s", self.runtime.ui_mode)
        self._add_event(f"Mode: {self.runtime.ui_mode}")

    def _on_input_selected(self, event=None) -> None:
        self.runtime.input_device = self._find_device(self.input_devices, self.input_var.get())
        self.flow.update_runtime(self.runtime)
        logger.info("settings_changed input_device=%s", self.input_var.get())

    def _on_output_selected(self, event=None) -> None:
        self.runtime.output_device = self._find_device(self.output_devices, self.output_var.get())
        self.flow.update_runtime(self.runtime)
        logger.info("settings_changed output_device=%s", self.output_var.get())

    def _on_language_selected(self, event=None) -> None:
        self.runtime.target_language = TARGET_LANGUAGES.get(self.language_var.get(), "eng")
        logger.info("settings_changed target_language=%s", self.runtime.target_language)

    def _on_voice_selected(self, event=None) -> None:
        self.runtime.speaker_id = str(("Voice 1", "Voice 2", "Voice 3").index(self.voice_var.get()))
        logger.info("settings_changed speaker_id=%s", self.runtime.speaker_id)

    def _on_backend_selected(self, event=None) -> None:
        self.runtime.backend_profile = self.backend_var.get()
        logger.info("settings_changed backend_profile=%s", self.runtime.backend_profile)

    def _on_cache_changed(self) -> None:
        self.runtime.semantic_cache_enabled = self.cache_var.get()
        logger.info("settings_changed semantic_cache=%s", self.runtime.semantic_cache_enabled)

    def _on_strategy_selected(self, event=None) -> None:
        self.runtime.cache_strategy = self.strategy_var.get()
        logger.info("settings_changed cache_strategy=%s", self.runtime.cache_strategy)

    def _on_domain_changed(self, event=None) -> None:
        self.runtime.domain = self.domain_var.get().strip() or "demo"
        self.domain_var.set(self.runtime.domain)
        logger.info("settings_changed domain=%s", self.runtime.domain)

    def _on_privacy_selected(self, event=None) -> None:
        self.runtime.privacy_level = self.privacy_var.get()
        logger.info("settings_changed privacy_level=%s", self.runtime.privacy_level)

    def _reset_session(self) -> None:
        session_id = self.runtime.reset_session()
        self.session_label.config(text=f"Session: {session_id[:8]}")
        logger.info("session_reset session=%s", session_id)
        self._add_event("Session reset")

    def _resend_last_input(self) -> None:
        self._sync_runtime_from_ui()
        if self.flow.resend_last_input():
            self._add_event("Resent last input")

    def _replay_last_output(self) -> None:
        if self.flow.replay_last_output():
            self._add_event("Replayed last output")

    def _threadsafe_translation_completed(self, response: TranslationResponse) -> None:
        self.root.after(0, lambda: self._on_translation_completed(response))

    def _threadsafe_translation_failed(self, error: Exception) -> None:
        self.root.after(0, lambda: self._on_translation_failed(error))

    def _threadsafe_status(self, message: str) -> None:
        self.root.after(0, lambda: self.status_label.config(text=message))

    def _on_translation_completed(self, response: TranslationResponse) -> None:
        self.status_label.config(text="Translated audio received.")
        self.metric_labels["Cache"].config(text=response.cache_status.upper())
        self.metric_labels["Strategy"].config(text=response.cache_strategy)
        self.metric_labels["Similarity"].config(text=self._format_float(response.similarity, digits=3))
        self.metric_labels["Lookup"].config(text=self._format_seconds(response.lookup_time))
        self.metric_labels["Inference"].config(text=self._format_seconds(response.inference_time))
        self.metric_labels["Total"].config(text=self._format_seconds(response.total_time))
        self.metric_labels["Decision"].config(text=response.decision or "-")
        self._add_event(
            f"{response.cache_status.upper()} | lookup {self._format_seconds(response.lookup_time)} | "
            f"inference {self._format_seconds(response.inference_time)}"
        )

    def _on_translation_failed(self, error: Exception) -> None:
        self.status_label.config(text=f"Translation failed: {error}")
        self._add_event("Translation failed")

    def _add_event(self, text: str) -> None:
        self.event_rows.append(text)
        self.event_rows = self.event_rows[-6:]
        if self.event_log is not None:
            self.event_log.delete(0, tk.END)
            for row in self.event_rows:
                self.event_log.insert(tk.END, row)

    def _select_initial_devices(self) -> None:
        self.runtime.input_device = self._safe_default(self.registry.get_default_input_device)
        if self.runtime.demo_enabled:
            self._select_default_demo_output()
        else:
            self._select_default_user_output()

    def _select_default_user_output(self) -> None:
        self.runtime.output_device = self._safe_default(self.registry.find_virtual_cable_output)
        if self.runtime.output_device is None:
            self.runtime.output_device = self._safe_default(self.registry.get_default_output_device)
            logger.warning("vb_audio_cable_missing fallback=default_output")

    def _select_default_demo_output(self) -> None:
        self.runtime.output_device = self._safe_default(self.registry.get_default_output_device)

    def _safe_devices(self, provider) -> list[AudioDevice]:
        try:
            return provider()
        except Exception as exc:
            logger.warning("audio_device_discovery_failed error=%s", exc)
            return []

    def _safe_default(self, provider) -> AudioDevice | None:
        try:
            return provider()
        except Exception as exc:
            logger.warning("audio_default_device_failed error=%s", exc)
            return None

    def _find_device(self, devices: list[AudioDevice], label: str) -> AudioDevice | None:
        for device in devices:
            if self._device_label(device) == label:
                return device
        return None

    def _device_label(self, device: AudioDevice | None) -> str:
        if device is None:
            return "No device available"
        return f"{device.name} [{device.index}]"

    def _window_size(self, value: str) -> tuple[int, int]:
        width, height = value.split("x")
        return int(width), int(height)

    def _format_seconds(self, value: float | None) -> str:
        if value is None:
            return "-"
        return f"{value:.2f}s"

    def _format_float(self, value: float | None, *, digits: int) -> str:
        if value is None:
            return "-"
        return f"{value:.{digits}f}"

    def _server_status_text(self) -> str:
        icon = SERVER_ONLINE_ICON if self.health.online else SERVER_OFFLINE_ICON
        state = "Online" if self.health.online else "Offline"
        text = f"{icon} Server {state}"
        if self.health.semantic_memory_enabled:
            text += " | Memory On"
        return text

    def _resize_for_mode(self) -> None:
        base_width, base_height = self._window_size(self.settings.gui.main_window_size)
        if self.runtime.demo_enabled:
            width = max(base_width, 980)
            height = max(base_height, 920)
            self.root.minsize(900, 920)
        else:
            width = base_width
            height = base_height
            self.root.minsize(800, 500)
        center_window(self.root, width, height)

    def _close(self) -> None:
        try:
            self.flow.shutdown()
        finally:
            self._stop_tray_icon()
            self.root.destroy()

    def _hide_window_to_tray(self) -> None:
        self.root.withdraw()
        self._create_tray_icon()

    def _create_tray_icon(self) -> None:
        if self.tray_icon is not None:
            return
        try:
            from PIL import Image
            from pystray import Icon, Menu, MenuItem
        except Exception as exc:
            logger.warning("tray_icon_unavailable error=%s", exc)
            self._close()
            return

        self.tray_icon_image = Image.open(asset_path("polyglot-icon.ico"))
        self.tray_icon = Icon(
            "Polyglot App",
            self.tray_icon_image,
            "Polyglot App",
            menu=Menu(
                MenuItem("Launch Dashboard", self._tray_show_window, default=True),
                MenuItem(self._tray_recording_label, self._tray_toggle_recording),
                MenuItem("Quit Polyglot", self._tray_quit),
            ),
        )

        if hasattr(self.tray_icon, "run_detached"):
            self.tray_icon.run_detached()
        else:
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()

    def _tray_recording_label(self, item: Any = None) -> str:
        return "Stop Recording" if self.recording.get() else "Start Recording"

    def _tray_show_window(self, icon: Any = None, item: Any = None) -> None:
        self.root.after(0, self._show_from_tray)

    def _tray_toggle_recording(self, icon: Any = None, item: Any = None) -> None:
        self.root.after(0, self._toggle_recording)

    def _tray_quit(self, icon: Any = None, item: Any = None) -> None:
        self.root.after(0, self._close)

    def _show_from_tray(self) -> None:
        self._stop_tray_icon()
        self.root.deiconify()
        self.root.lift()

    def _stop_tray_icon(self) -> None:
        if self.tray_icon is None:
            return
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.tray_icon = None
        self.tray_icon_image = None

    def _open_info(self) -> None:
        self.main_frame.grid_remove()
        self.info_frame.grid()

    def _show_main_menu(self) -> None:
        self.info_frame.grid_remove()
        self.main_frame.grid()

    def _send_email(self) -> None:
        subject = self.subject_entry.get() if self.subject_entry else ""
        body = self.message_text.get("1.0", tk.END) if self.message_text else ""
        body = body.replace(" ", "%20").replace("\n", "%0A")
        subject = subject.replace(" ", "%20")
        webbrowser.open(f"mailto:support@polyglot.com?subject={subject}&body={body}")
        if self.subject_entry:
            self.subject_entry.delete(0, tk.END)
        if self.message_text:
            self.message_text.delete("1.0", tk.END)
