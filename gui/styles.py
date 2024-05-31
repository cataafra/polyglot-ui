# gui/styles.py
import sv_ttk
from tkinter import ttk
from ctypes import windll, byref, sizeof, c_int

from gui.colors import colors


def set_theme():
    """ Set the global theme for the application. """
    sv_ttk.set_theme("dark")


def toggle_theme():
    """ Toggle the global theme for the application. """
    sv_ttk.toggle_theme()


def get_theme():
    """ Get the current theme for the application. """
    return sv_ttk.get_theme()


def setup_styles():
    """ Configure custom styles for the application. """
    style = ttk.Style()

    # Custom style for combobox
    style.configure("Custom.TCombobox", padding=10, fieldrelief="flat", fieldbackground="white", foreground="black")
    style.map("Custom.TCombobox", fieldbackground=[("readonly", "white")])

    # Custom style for recording button
    style.configure("Recording.TButton", font=('', 18), foreground="white", background="red",
                    borderwidth=2, relief="raised", padding=10)
    style.map("Recording.TButton", background=[("active", "blue"), ("disabled", "grey")])


def center_window(root, width, height):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    root.geometry(f'{width}x{height}+{x}+{y}')


def color_title_bar(root):
    def convert_color(color_code):
        """ Convert color code to a format that can be used by the application."""
        formatted_color = color_code[1:].upper()
        return int(f'0x00{formatted_color}', 16)

    current_theme = get_theme()
    color = convert_color(colors["background"][current_theme])
    text_color = convert_color(colors["text"][current_theme])

    try:
        hwnd = windll.user32.GetParent(root.winfo_id())
        title_bar_color = color
        title_text_color = text_color
        windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, byref(c_int(title_bar_color)), sizeof(c_int))
        windll.dwmapi.DwmSetWindowAttribute(hwnd, 36, byref(c_int(title_text_color)), sizeof(c_int))
    except Exception as e:
        print(f"Failed to color title bar: {e}")
        pass
