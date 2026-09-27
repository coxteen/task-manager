import customtkinter as ctk
from system_metrics import SystemMetricsService


class StorageTab:
    """Componentă UI pentru vizualizarea spațiului de stocare pe partiții."""

    def __init__(self, parent_frame: ctk.CTkFrame, metrics_service: SystemMetricsService):
        self.frame = parent_frame
        self.metrics_service = metrics_service

        self._init_layout()
        self._populate_disks()

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

    def _populate_disks(self):
        disks = self.metrics_service.get_disk_metrics()

        if not disks:
            empty_label = ctk.CTkLabel(
                self.scrollable_frame,
                text="No accessible storage devices found.",
                font=ctk.CTkFont(size=16)
            )
            empty_label.pack(pady=20)
            return

        for disk in disks:
            card = ctk.CTkFrame(self.scrollable_frame, corner_radius=8)
            card.pack(fill="x", padx=10, pady=8)

            card_title = ctk.CTkLabel(
                card,
                text=f"{disk.device} ({disk.mountpoint}) - {disk.fstype.upper()}",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            card_title.pack(anchor="w", padx=15, pady=(10, 4))

            bar = ctk.CTkProgressBar(card, height=10)
            bar.set(disk.percent / 100.0)
            bar.pack(fill="x", padx=15, pady=5)

            stats_text = (
                f"Used: {disk.used_gb:.1f} GB  |  "
                f"Free: {disk.free_gb:.1f} GB  |  "
                f"Total: {disk.total_gb:.1f} GB  ({disk.percent}%)"
            )
            stats_label = ctk.CTkLabel(
                card,
                text=stats_text,
                font=ctk.CTkFont(size=13),
                text_color="#a0a0a0"
            )
            stats_label.pack(anchor="w", padx=15, pady=(2, 10))


def create_storage_tab(frame: ctk.CTkFrame, metrics_service: SystemMetricsService) -> StorageTab:
    return StorageTab(frame, metrics_service)