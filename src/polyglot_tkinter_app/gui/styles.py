from __future__ import annotations

from ctypes import byref, c_int, sizeof
from tkinter import ttk

from polyglot_tkinter_app.settings.models import AppSettings

try:
    from ctypes import windll
except ImportError:  # pragma: no cover - Windows-only cosmetic hook
    windll = None


def set_theme(settings: AppSettings) -> None:
    try:
        import sv_ttk

        sv_ttk.set_theme(settings.gui.default_theme)
    except Exception:
        pass


def toggle_theme(root, settings: AppSettings) -> None:
    try:
        import sv_ttk

        sv_ttk.toggle_theme()
    except Exception:
        pass
    color_title_bar(root, settings)
    setup_styles()


def get_theme() -> str:
    try:
        import sv_ttk

        return sv_ttk.get_theme()
    except Exception:
        return "dark"


def setup_styles() -> None:
    style = ttk.Style()
    style.configure("Custom.TCombobox", padding=10, fieldrelief="flat")
    style.configure("Recording.TButton", font=("", 18), borderwidth=2, relief="raised", padding=10)
    style.configure("Accent.TLabel", font=("", 12, "bold"))
    style.configure("Metrics.TLabel", font=("", 10))


def center_window(root, width: int, height: int) -> None:
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    root.geometry(f"{width}x{height}+{x}+{y}")


def color_title_bar(root, settings: AppSettings) -> None:
    colors = settings.gui.colors
    current_theme = get_theme()
    background = colors.get("background", {}).get(current_theme, "#1c1c1c")
    text = colors.get("text", {}).get(current_theme, "#ffffff")
    try:
        if windll is None:
            return
        hwnd = windll.user32.GetParent(root.winfo_id())
        windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, byref(c_int(_windows_color(background))), sizeof(c_int))
        windll.dwmapi.DwmSetWindowAttribute(hwnd, 36, byref(c_int(_windows_color(text))), sizeof(c_int))
    except Exception:
        pass


def _windows_color(color_code: str) -> int:
    return int(f"0x00{color_code[1:].upper()}", 16)
