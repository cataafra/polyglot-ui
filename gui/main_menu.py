import threading
import tkinter as tk
import webbrowser
from PIL import Image
from pystray import Icon, MenuItem, Menu
from tkinter import ttk, PhotoImage

from gui.styles import center_window, color_title_bar, set_theme, setup_styles, toggle_theme
from audio.audio_utils import list_input_devices, get_default_input_device
from utils.constants import TARGET_LANGUAGES
from config.config import config


class MainMenu:
    def __init__(self, root, audio_processor):
        self.root = root
        self.root.title("Polyglot App")
        self.root.iconbitmap("assets/polyglot-icon.ico")

        (width, height) = config.get("gui", "main_menu")["window_size"].split("x")
        width, height = int(width), int(height)

        center_window(self.root, width, height)  # Center window on the screen
        self.root.minsize(0, height)
        self.root.resizable(True, True)  # Allow window resizing
        self.root.after(100, self.root.deiconify)  # Display the window after setup

        # Initialize tray icon variables
        self.tray_icon_image = None
        self.tray_menu = None
        self.tray_icon = None

        # Initialize key variables
        self.recording = None
        self.record_button = None
        self.device_var = None
        self.device_menu = None
        self.language_var = None
        self.language_menu = None
        self.voice_var = None
        self.voice_menu = None
        self.status = None
        self.logo = PhotoImage(file="assets/polyglot-logo.png").subsample(4)
        self.record_icon = None
        self.email_entry = None
        self.subject_entry = None
        self.message_text = None

        # Set up both the main menu and info page
        self.main_frame = None
        self.info_frame = None
        self.setup_ui()

        # Initialize the processing-related variables
        self.server_status = None
        self.processor = audio_processor
        audio_processor.set_input_device(get_default_input_device())
        audio_processor.set_language(TARGET_LANGUAGES.get("English"))
        audio_processor.set_speaker_id("0")

    def setup_ui(self):
        # Set the theme
        set_theme()

        # Set up custom styles
        setup_styles()

        # Customize title bar color
        color_title_bar(self.root)

        # Minimize to tray instead of closing
        self.root.protocol('WM_DELETE_WINDOW', self.hide_window_to_tray)  # Override the close button

        # Tray icon setup
        self.tray_icon_image = Image.open("assets/polyglot-icon.ico")
        self.tray_menu = Menu(
            MenuItem('Launch Dashboard', self.show_from_tray, default=True),
            MenuItem(f'Start Recording', self.start_recording) if not self.recording
            else MenuItem(f'Stop Recording', self.stop_recording),
            MenuItem('Quit Polyglot', self.exit_from_tray))

        # Initialize frame for the main menu
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(column=0, row=0, sticky=tk.NSEW)

        # Initialize frame for the info page
        self.info_frame = ttk.Frame(self.root, padding="20")
        self.info_frame.grid(column=0, row=0, sticky=tk.NSEW)
        self.info_frame.grid_remove()

        # Set up the main menu
        self.setup_main_menu()

        # Set up the info page
        self.setup_info_page()

    def setup_main_menu(self):
        # Main frame setup with padding
        frame = self.main_frame
        frame.columnconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Top frame with logo and title
        title_frame = ttk.Frame(frame)
        title_frame.grid(column=0, row=0, sticky=tk.NSEW)

        # Logo
        logo_label = ttk.Label(title_frame, image=self.logo)
        logo_label.grid(column=0, row=0, sticky=tk.W, padx=0, pady=10)
        logo_label.image = self.logo

        # Title
        title_label = ttk.Label(title_frame, text="Dashboard", font=("", 24))
        title_label.grid(column=1, row=0, sticky=tk.SW, padx=(20, 0), pady=10)

        # Icon buttons
        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(column=1, row=0, sticky=tk.SW)

        # Theme icon
        settings_button = ttk.Button(buttons_frame, text="\U0001F3A8", command=lambda: self.toggle_theme())
        settings_button.grid(column=0, row=0, sticky=tk.E, padx=0, pady=10)

        # Info icon
        info_button = ttk.Button(buttons_frame, text="ℹ", command=self.open_info, padding=(14, 3))
        info_button.grid(column=1, row=0, sticky=tk.E, padx=(10, 0), pady=10)

        # Settings frame
        settings_frame = ttk.Frame(frame)
        settings_frame.grid(column=0, row=1, columnspan=2, sticky=tk.NSEW)
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=0)

        # Settings label
        settings_label = ttk.Label(settings_frame, text="Settings", font=("", 16))
        settings_label.grid(column=0, row=0, sticky=tk.W, padx=0, pady=(30, 10))

        # Device selection
        ttk.Label(settings_frame, text="Select Input Device:").grid(column=0, row=1,
                                                                    sticky=tk.W, padx=(0, 10),
                                                                    pady=10)
        self.device_var = tk.StringVar(value=get_default_input_device().get('name'))
        self.device_menu = ttk.Combobox(settings_frame, textvariable=self.device_var, state="readonly", width=30,
                                        style='Custom.TCombobox')
        self.device_menu.grid(column=0, row=2, sticky=tk.EW, padx=(0, 10))
        self.device_menu['values'] = [dev.get('name') for dev in list_input_devices()]
        self.device_menu.bind('<<ComboboxSelected>>', self.on_device_select)
        self.device_menu.bind("<MouseWheel>", lambda e: "break")

        # Language selection
        ttk.Label(settings_frame, text="Select Language:").grid(column=0, row=3, sticky=tk.W,
                                                                padx=(0, 10), pady=10)
        self.language_var = tk.StringVar(value="English")
        self.language_menu = ttk.Combobox(settings_frame, textvariable=self.language_var, state="readonly", width=30,
                                          style='Custom.TCombobox')
        self.language_menu.grid(column=0, row=4, sticky=tk.EW, padx=(0, 10))
        self.language_menu['values'] = list(TARGET_LANGUAGES.keys())
        self.language_menu.bind('<<ComboboxSelected>>', self.on_language_select)
        self.language_menu.bind("<MouseWheel>", lambda e: "break")

        # Voice selection (experimental)
        ttk.Label(settings_frame, text="Select Voice - experimental:").grid(column=1, row=1,
                                                                            sticky=tk.W,
                                                                            padx=(10, 0),
                                                                            pady=10)
        self.voice_var = tk.StringVar(value="Voice 1")
        self.voice_menu = ttk.Combobox(settings_frame, textvariable=self.voice_var, state="readonly", width=30,
                                       style='Custom.TCombobox')
        self.voice_menu.grid(column=1, row=2, sticky=tk.EW, padx=(10, 0))
        self.voice_menu['values'] = ('Voice 1', 'Voice 2', 'Voice 3')
        self.voice_menu.bind('<<ComboboxSelected>>', self.on_voice_select)
        self.voice_menu.bind("<MouseWheel>", lambda e: "break")

        # Recorder on/off button
        self.recording = tk.BooleanVar(value=False)

        self.record_icon = PhotoImage(file="assets/record-icon.png").subsample(2)
        self.record_button = ttk.Button(frame, text="  Start Recording", command=self.toggle_recording,
                                        style="Recording.TButton", image=self.record_icon, compound=tk.LEFT)
        self.record_button.grid(column=0, row=2, columnspan=2, sticky=tk.NSEW, pady=(70, 0))

        # Status bar frame
        status_frame = ttk.Frame(frame)
        status_frame.grid(column=0, row=3, columnspan=2, sticky=tk.NSEW, padx=0, pady=0)
        status_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(1, weight=1)
        status_frame.rowconfigure(0, weight=1)

        self.status = ttk.Label(status_frame, text="Ready", anchor=tk.W)
        self.status.grid(column=0, row=1, columnspan=1, sticky=tk.W, pady=(10, 20))

        self.server_status = ttk.Label(status_frame, text="✅ Server Online", anchor=tk.E)
        self.server_status.grid(column=1, row=1, columnspan=1, sticky=tk.E, pady=(10, 20))

    def setup_info_page(self):
        def on_entry_focus_in(entry):
            if entry.get() == "Email address" or entry.get() == "Subject":
                entry.configure(state='normal')
                entry.delete(0, 'end')

        def on_entry_focus_out(entry, placeholder):
            if entry.get() == "":
                entry.insert(0, placeholder)
                entry.configure(state='disabled')


        frame = self.info_frame

        # Configure the grid for the info frame
        frame.columnconfigure(0, weight=1)

        # Title bar with logo and title
        title_frame = ttk.Frame(frame)
        title_frame.grid(column=0, row=0, sticky=tk.W, padx=0, pady=(25, 0))

        back_button = ttk.Button(title_frame, text="←", command=self.show_main_menu)
        back_button.grid(column=0, row=0, sticky=tk.W, padx=0, pady=(0, 12))

        title_label = ttk.Label(title_frame, text="Information & Help", font=("", 24))
        title_label.grid(column=2, row=0, sticky=tk.SW, padx=(20, 0), pady=(0, 10))

        # Info text
        info_text = ttk.Label(frame, text="Polyglot, version 1.0 - developed with ♥ by @cataafra")
        info_text.grid(column=0, row=1, sticky=tk.W, padx=0, pady=(10, 10))

        # Subtitle for social media section
        social_media_subtitle = ttk.Label(frame, text="Connect with me", font=("", 16))
        social_media_subtitle.grid(column=0, row=2, sticky=tk.W, padx=0, pady=(30, 10))

        # Social media buttons
        social_media_frame = ttk.Frame(frame)
        social_media_frame.grid(column=0, row=3, sticky=tk.W, padx=0, pady=(10, 10))

        linkedin_button = ttk.Button(social_media_frame, text="LinkedIn",
                                     command=lambda: webbrowser.open("https://www.linkedin.com/in/cataafra/"))
        linkedin_button.grid(column=1, row=1, sticky=tk.W, padx=(0, 5))

        github_button = ttk.Button(social_media_frame, text="GitHub",
                                   command=lambda: webbrowser.open("https://github.com/cataafra"))
        github_button.grid(column=2, row=1, sticky=tk.W, padx=5)

        # Email section
        email_frame = ttk.Frame(frame)
        email_frame.grid(column=0, row=4, sticky=tk.EW, pady=20)
        email_frame.columnconfigure(0, weight=1)

        # Email subtitle
        email_subtitle = ttk.Label(email_frame, text="Having issues?", font=("", 16))
        email_subtitle.grid(column=0, row=0, sticky=tk.W, padx=0, pady=(0, 10))

        # Email entry fields
        self.email_entry = ttk.Entry(email_frame)
        self.email_entry.grid(column=0, row=1, sticky=tk.EW)
        self.email_entry.insert(0, "Email address")
        self.email_entry.configure(state='disabled')
        self.email_entry.bind("<Button-1>", lambda e: on_entry_focus_in(self.email_entry))
        self.email_entry.bind("<FocusOut>", lambda e: on_entry_focus_out(self.email_entry, "Email address"))

        self.subject_entry = ttk.Entry(email_frame)
        self.subject_entry.grid(column=0, row=2, sticky=tk.EW, pady=(10, 10))
        self.subject_entry.insert(0, "Subject")
        self.subject_entry.configure(state='disabled')
        self.subject_entry.bind("<Button-1>", lambda e: on_entry_focus_in(self.subject_entry))
        self.subject_entry.bind("<FocusOut>", lambda e: on_entry_focus_out(self.subject_entry, "Subject"))

        self.message_text = tk.Text(email_frame, height=3)
        self.message_text.grid(column=0, row=3, sticky=tk.EW)

        send_button = ttk.Button(email_frame, text="Send us an email ▶", command=self.send_email)
        send_button.grid(column=0, row=4, sticky=tk.E, pady=(10, 0))

    def open_info(self):
        self.main_frame.grid_remove()
        self.info_frame.grid()

    def show_main_menu(self):
        self.info_frame.grid_remove()
        self.main_frame.grid()

    def toggle_theme(self):
        self.root.iconify()
        toggle_theme(self.root)
        self.root.deiconify()

    def toggle_recording(self):
        if not self.recording.get():
            self.recording.set(True)
            self.record_button.config(text="  Stop Recording")
            self.status.config(text="Recording...")
            threading.Thread(target=self.start_recording, daemon=True).start()
        else:
            self.recording.set(False)
            self.record_button.config(text="  Start Recording")
            self.status.config(text="Recording Stopped.")
            threading.Thread(target=self.stop_recording, daemon=True).start()

    def start_recording(self):
        self.processor.start_recording()

    def stop_recording(self):
        self.processor.stop_recording()

    def update_processor_settings(self, setting_type, selected_option):
        if setting_type == 'device':
            input_devices = list_input_devices()
            changed = False
            for device in input_devices:
                if selected_option == device.get('name'):
                    self.processor.set_input_device(device)
                    changed = True
            if not changed:
                self.processor.set_input_device(get_default_input_device())

        elif setting_type == 'language':
            self.processor.set_language(TARGET_LANGUAGES.get(selected_option))

        elif setting_type == 'voice':
            self.processor.set_speaker_id(str(self.voice_menu['values'].index(selected_option)))

    def on_device_select(self, event):
        selected_device = self.device_var.get()
        self.update_processor_settings('device', selected_device)
        event.widget.select_clear()

    def on_language_select(self, event):
        selected_language = self.language_var.get()
        self.update_processor_settings('language', selected_language)
        event.widget.select_clear()

    def on_voice_select(self, event):
        selected_voice = self.voice_var.get()
        self.update_processor_settings('voice', selected_voice)
        event.widget.select_clear()

    def create_trey_icon(self):
        self.tray_icon = Icon('Polyglot App', self.tray_icon_image, 'Polyglot App', menu=self.tray_menu)
        self.tray_icon.icon.left_click = self.show_from_tray

    def hide_window_to_tray(self):
        self.root.withdraw()  # Hide the Tkinter window
        self.create_trey_icon()
        self.tray_icon.run()

    def show_from_tray(self, icon=None, item=None):
        self.tray_icon.stop()
        self.root.after(0, self.root.deiconify)  # Show the window

    def exit_from_tray(self, icon=None, item=None):
        self.tray_icon.stop()
        self.root.destroy()  # Finally close the application

    def send_email(self):
        """Function to send an email."""
        subject = self.subject_entry.get()
        body = self.message_text.get("1.0", tk.END)
        # Replace spaces with '%20' and new lines with '%0A' for URL encoding
        body = body.replace(' ', '%20').replace('\n', '%0A')

        # Set your recipient email address here
        recipient_email = "support@example.com"

        # Create the mailto URL
        url = f"mailto:{recipient_email}?subject={subject}&body={body}"
        webbrowser.open(url)

        # Clear fields after composing
        self.subject_entry.delete(0, tk.END)
        self.message_text.delete("1.0", tk.END)

    def disable_focus_on_click(self, event):
        try:
            event.widget.select_clear()
        except AttributeError:
            pass
        self.root.focus_set()