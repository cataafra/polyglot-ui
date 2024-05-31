import threading
import tkinter as tk
from tkinter import ttk, PhotoImage
import sv_ttk

from audio_processor import AudioProcessor
from screens.main_menu import MainMenu
from utils.request_handler import send_request_for_connection_test


class SplashScreen(tk.Tk):
    def __init__(self, debug=False):
        super().__init__()
        self.title("Connecting...")
        self.geometry("400x400")
        self.resizable(True, True)
        sv_ttk.set_theme("dark")

        # Remove window toolbar
        self.overrideredirect(True)

        # Center window on screen
        window_size = 400
        position_right = int(self.winfo_screenwidth() / 2 - window_size / 2)
        position_down = int(self.winfo_screenheight() / 2 - window_size / 2)
        self.geometry("+{}+{}".format(position_right, position_down))

        # Create a frame with padding
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill='both', expand=True)

        self.logo = PhotoImage(file="assets/polyglot-logo.png").subsample(2)

        logo_label = ttk.Label(frame, image=self.logo)
        logo_label.pack(pady=5, anchor=tk.S, expand=True)

        self.status_label = ttk.Label(frame, text="Connecting to server...")
        self.status_label.pack(pady=10, anchor=tk.CENTER, expand=True)

        self.progress = ttk.Progressbar(frame, orient='horizontal', length=200)
        self.progress.pack(pady=10, anchor='n', expand=True)
        self.progress.start(25)

        self.retry_button = ttk.Button(frame, text="Try Again", command=self.retry_connection)

        self.audio_processor = None

        if debug:
            self.launch_main_menu()
        else:
            threading.Thread(target=self.check_server_connection, daemon=True).start()

    def retry_connection(self):
        self.status_label.config(text="Attempting to connect to the server...")
        self.retry_button.pack_forget()
        self.progress.pack(pady=10, anchor='n', expand=True)
        self.progress.start(25)
        threading.Thread(target=self.check_server_connection, daemon=True).start()

    def check_server_connection(self):
        if send_request_for_connection_test():
            self.after(1000, self.on_success)
            self.audio_processor = AudioProcessor(0, "en")
        else:
            self.after(1000, self.on_fail)

    def on_success(self):
        self.progress.stop()
        self.status_label.config(text="Connection successful!")
        self.launch_main_menu()

    def on_fail(self):
        self.progress.stop()
        self.status_label.config(text="Connection failed. Please try again.")
        self.progress.pack_forget()
        self.retry_button.pack(pady=0, anchor='n', expand=True)

    def launch_main_menu(self):
        self.destroy()
        root = tk.Tk()
        root.withdraw()
        app = MainMenu(root, self.audio_processor)
        self.after(1000, root.mainloop)