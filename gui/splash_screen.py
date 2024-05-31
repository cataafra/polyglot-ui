import threading
import tkinter as tk
from tkinter import ttk, PhotoImage

from gui.styles import set_theme, setup_styles, center_window
from gui.main_menu import MainMenu
from audio.audio_processor import AudioProcessor
from network.request_handler import send_request_for_connection_test


class SplashScreen(tk.Tk):
    """
    Splash screen for the application. This screen is displayed while the application is connecting to the server.
    """

    def __init__(self, debug=False):
        super().__init__()

        # Set debug mode - skip server connection check
        self.debug = debug

        # Setup window
        set_theme()
        setup_styles()
        self.geometry("400x400")
        self.resizable(False, False)
        self.overrideredirect(True)
        center_window(self, 400, 400)

        # Initialize UI elements
        self.logo = None
        self.status_label = None
        self.progress = None
        self.retry_button = None

        # Setup UI
        self.setup_ui()

        # Initialize audio processor
        self.audio_processor = None

        # Check server connection
        threading.Thread(target=self.check_server_connection, daemon=True).start()

    def setup_ui(self):
        """ Set up the UI elements for the splash screen. """
        # Create a frame with padding
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill='both', expand=True)

        # Add the elements to the frame
        self.logo = PhotoImage(file="assets/polyglot-logo.png").subsample(2)

        logo_label = ttk.Label(frame, image=self.logo)
        logo_label.pack(pady=5, anchor=tk.S, expand=True)

        self.status_label = ttk.Label(frame, text="Connecting to server...")
        self.status_label.pack(pady=10, anchor=tk.CENTER, expand=True)

        self.progress = ttk.Progressbar(frame, orient='horizontal', length=200)
        self.progress.pack(pady=10, anchor='n', expand=True)
        self.progress.start(25)

        self.retry_button = ttk.Button(frame, text="Try Again", command=self.retry_connection)

    def retry_connection(self):
        """ Retry the connection to the server. On a separate thread."""
        self.status_label.config(text="Attempting to connect to the server...")
        self.retry_button.pack_forget()
        self.progress.pack(pady=10, anchor='n', expand=True)
        self.progress.start(25)
        threading.Thread(target=self.check_server_connection, daemon=True).start()

    def check_server_connection(self):
        """ Check the connection to the server."""
        if self.debug or send_request_for_connection_test():
            self.after(1000, self.on_success)
            self.audio_processor = AudioProcessor(0, "en")
        else:
            self.after(1000, self.on_fail)

    def on_success(self):
        """ Handle a successful connection to the server. Launch the main menu."""
        self.progress.stop()
        self.status_label.config(text="Connection successful!")
        self.launch_main_menu()

    def on_fail(self):
        """ Handle a failed connection to the server. Display an error message and a retry button."""
        self.progress.stop()
        self.status_label.config(text="Connection failed. Please try again.")
        self.progress.pack_forget()
        self.retry_button.pack(pady=0, anchor='n', expand=True)

    def launch_main_menu(self):
        """ Launch the main menu. """
        self.destroy()
        root = tk.Tk()
        root.withdraw()
        app = MainMenu(root, self.audio_processor)
        self.after(1000, root.mainloop)
