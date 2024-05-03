import tkinter as tk
from tkinter import ttk
import sv_ttk


class PolyglotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Polyglot App")
        self.root.geometry("600x400")  # Set window size
        self.root.resizable(True, True)  # Allow window resizing

        # Set the theme
        sv_ttk.set_theme("dark")

        # Main frame with padding for better spacing
        frame = ttk.Frame(self.root, padding="20")
        frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        frame.columnconfigure(1, weight=1)  # Make the second column expandable
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Recorder on/off button, full width at the top
        self.recording = tk.BooleanVar(value=False)
        self.record_button = ttk.Button(frame, text="⦿︎ Start Recording", command=self.toggle_recording)
        self.record_button.grid(column=0, row=0, columnspan=3, sticky=tk.EW, padx=20, pady=10)

        # Device selection
        ttk.Label(frame, text="Select Input Device:").grid(column=0, row=1, sticky=tk.W, padx=20, pady=10)
        self.device_var = tk.StringVar(value="Device 1")
        self.device_menu = ttk.Combobox(frame, textvariable=self.device_var, state="readonly", width=30)
        self.device_menu.grid(column=1, row=1, sticky=tk.EW, padx=20)
        self.device_menu['values'] = ('Device 1', 'Device 2', 'Device 3')

        # Language selection
        ttk.Label(frame, text="Select Language:").grid(column=0, row=2, sticky=tk.W, padx=20, pady=10)
        self.language_var = tk.StringVar(value="English")
        self.language_menu = ttk.Combobox(frame, textvariable=self.language_var, state="readonly", width=30)
        self.language_menu.grid(column=1, row=2, sticky=tk.EW, padx=20)
        self.language_menu['values'] = ('English', 'Spanish', 'French')

        # Voice selection (experimental)
        ttk.Label(frame, text="Select Voice:").grid(column=0, row=3, sticky=tk.W, padx=20, pady=10)
        self.voice_var = tk.StringVar(value="Voice 1")
        self.voice_menu = ttk.Combobox(frame, textvariable=self.voice_var, state="readonly", width=30)
        self.voice_menu.grid(column=1, row=3, sticky=tk.EW, padx=20)
        self.voice_menu['values'] = ('Voice 1', 'Voice 2')

        # Status bar, centered
        self.status = ttk.Label(frame, text="Ready", relief=tk.SUNKEN, anchor=tk.CENTER)
        self.status.grid(column=0, row=4, columnspan=3, sticky=tk.EW, padx=20, pady=20)

    def toggle_recording(self):
        is_recording = self.recording.get()
        self.recording.set(not is_recording)
        if is_recording:
            self.record_button.config(text="⦿︎ Start Recording")
            self.status.config(text="Recording Stopped.")
        else:
            self.record_button.config(text="⦿︎ Stop Recording")
            self.status.config(text="Recording...")


if __name__ == "__main__":
    root = tk.Tk()
    app = PolyglotGUI(root)
    root.mainloop()
