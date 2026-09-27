import customtkinter as ctk


def create_main_window(title: str = "System Monitor", width: int = 1200, height: int = 700) -> ctk.CTk:
    """
    Inițializează și configurează fereastra principală a aplicației.
    """
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    window = ctk.CTk()
    window.title(title)
    window.geometry(f"{width}x{height}")
    window.minsize(900, 600)

    window.resizable(True, True)

    return window