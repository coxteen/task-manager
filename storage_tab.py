import customtkinter as ctk
from system_metrics import SystemMetricsService


class StorageTab:
    """Componentă UI pentru vizualizarea spațiului de stocare pe partiții."""

    def __init__(self, parent_frame: ctk.CTkFrame, metrics_service: SystemMetricsService):
        self.frame = parent_frame
        self.metrics_service = metrics_service
        self._cards = {}
        self._after_id = None

        self._init_layout()
        self._schedule_update()

    def _init_layout(self):
        header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))

        title = ctk.CTkLabel(
            header_frame,
            text="Storage Devices & Partitions",
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold")
        )
        title.pack(anchor="w")

        self.scrollable_frame = ctk.CTkScrollableFrame(self.frame, corner_radius=10)
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="Detecting storage devices...",
            font=ctk.CTkFont(size=15),
            text_color="#909090"
        )
        self.status_label.pack(pady=20)

    def _schedule_update(self):
        try:
            if not self.frame.winfo_exists():
                return
            self._update_disks()
            self._after_id = self.frame.after(2000, self._schedule_update)
        except Exception:
            pass

    def _update_disks(self):
        disks = self.metrics_service.get_disk_metrics()

        if not disks:
            return

        if self.status_label.winfo_exists():
            self.status_label.pack_forget()

        for disk in disks:
            card_key = disk.device

            if card_key not in self._cards:
                card = ctk.CTkFrame(self.scrollable_frame, corner_radius=8)
                card.pack(fill="x", padx=10, pady=8)

                title_lbl = ctk.CTkLabel(
                    card,
                    text=f"{disk.device} ({disk.mountpoint}) - {disk.fstype.upper()}",
                    font=ctk.CTkFont(size=16, weight="bold")
                )
                title_lbl.pack(anchor="w", padx=15, pady=(10, 4))

                progress_bar = ctk.CTkProgressBar(card, height=10)
                progress_bar.pack(fill="x", padx=15, pady=5)

                stats_lbl = ctk.CTkLabel(
                    card,
                    text="",
                    font=ctk.CTkFont(size=13),
                    text_color="#a0a0a0"
                )
                stats_lbl.pack(anchor="w", padx=15, pady=(2, 10))

                self._cards[card_key] = {
                    "progress_bar": progress_bar,
                    "stats_lbl": stats_lbl
                }

            widgets = self._cards[card_key]
            widgets["progress_bar"].set(disk.percent / 100.0)

            stats_text = (
                f"Used: {disk.used_gb:.1f} GB  |  "
                f"Free: {disk.free_gb:.1f} GB  |  "
                f"Total: {disk.total_gb:.1f} GB  ({disk.percent}%)"
            )
            widgets["stats_lbl"].configure(text=stats_text)

    def cleanup(self):
        if self._after_id:
            try:
                self.frame.after_cancel(self._after_id)
            except Exception:
                pass


def create_storage_tab(frame: ctk.CTkFrame, metrics_service: SystemMetricsService) -> StorageTab:
    return StorageTab(frame, metrics_service)