import customtkinter as ctk


class ThemeTab:
    """Componentă UI pentru gestionarea aspectului vizual (Light/Dark/System)."""

    def __init__(self, parent_frame: ctk.CTkFrame):
        self.frame = parent_frame
        self._init_layout()

    def _init_layout(self):
        center_card = ctk.CTkFrame(self.frame, corner_radius=12)
        center_card.pack(expand=True, padx=40, pady=40)

        title = ctk.CTkLabel(
            center_card,
            text="Appearance Settings",
            font=ctk.CTkFont(family="Helvetica", size=22, weight="bold")
        )
        title.pack(padx=40, pady=(30, 10))

        subtitle = ctk.CTkLabel(
            center_card,
            text="Choose your preferred color theme:",
            font=ctk.CTkFont(size=14),
            text_color="#909090"
        )
        subtitle.pack(padx=40, pady=(0, 20))

        btn_dark = ctk.CTkButton(
            center_card,
            text="Dark Mode",
            width=200,
            height=38,
            command=lambda: ctk.set_appearance_mode("dark")
        )
        btn_dark.pack(padx=40, pady=8)

        btn_light = ctk.CTkButton(
            center_card,
            text="Light Mode",
            width=200,
            height=38,
            fg_color="#4f6378",
            hover_color="#3d4f61",
            command=lambda: ctk.set_appearance_mode("light")
        )
        btn_light.pack(padx=40, pady=8)

        btn_system = ctk.CTkButton(
            center_card,
            text="Sync with System",
            width=200,
            height=38,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            command=lambda: ctk.set_appearance_mode("system")
        )
        btn_system.pack(padx=40, pady=(8, 30))


def create_theme_tab(frame: ctk.CTkFrame) -> ThemeTab:
    return ThemeTab(frame)