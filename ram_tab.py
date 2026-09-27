from collections import deque
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from system_metrics import SystemMetricsService


class RamTab:
    """Componentă UI pentru monitorizarea memoriei RAM."""

    def __init__(self, parent_frame: ctk.CTkFrame, metrics_service: SystemMetricsService):
        self.frame = parent_frame
        self.metrics_service = metrics_service

        self.history_length = 60
        self.history = deque([0.0] * self.history_length, maxlen=self.history_length)

        self._init_layout()
        self._init_graph()
        self._schedule_update()

    def _init_layout(self):
        self.frame.grid_columnconfigure(0, weight=0, minsize=280)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        self.info_panel = ctk.CTkFrame(self.frame, corner_radius=10)
        self.info_panel.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        title_label = ctk.CTkLabel(
            self.info_panel,
            text="Memory (RAM)",
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold")
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 15))

        self.usage_label = ctk.CTkLabel(
            self.info_panel,
            text="Usage: -- %",
            font=ctk.CTkFont(family="Helvetica", size=18)
        )
        self.usage_label.pack(anchor="w", padx=20, pady=5)

        self.progress_bar = ctk.CTkProgressBar(self.info_panel, height=12)
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=20, pady=(5, 15))

        self.used_label = ctk.CTkLabel(
            self.info_panel,
            text="Used: -- GB",
            font=ctk.CTkFont(family="Helvetica", size=14)
        )
        self.used_label.pack(anchor="w", padx=20, pady=5)

        self.available_label = ctk.CTkLabel(
            self.info_panel,
            text="Available: -- GB",
            font=ctk.CTkFont(family="Helvetica", size=14)
        )
        self.available_label.pack(anchor="w", padx=20, pady=5)

        self.total_label = ctk.CTkLabel(
            self.info_panel,
            text="Total: -- GB",
            font=ctk.CTkFont(family="Helvetica", size=14)
        )
        self.total_label.pack(anchor="w", padx=20, pady=5)

    def _init_graph(self):
        self.graph_container = ctk.CTkFrame(self.frame, corner_radius=10)
        self.graph_container.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)

        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.fig.patch.set_facecolor("#242424")
        self.ax.set_facecolor("#1f1f1f")

        self.line, = self.ax.plot(
            range(self.history_length),
            list(self.history),
            color="#2fa572",
            linewidth=2,
            label="RAM %"
        )

        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, self.history_length - 1)
        self.ax.tick_params(colors="#a0a0a0", labelsize=9)
        self.ax.spines["bottom"].set_color("#404040")
        self.ax.spines["top"].set_color("#404040")
        self.ax.spines["right"].set_color("#404040")
        self.ax.spines["left"].set_color("#404040")
        self.ax.grid(True, linestyle="--", alpha=0.3, color="#606060")
        self.ax.set_ylabel("Memory Usage (%)", color="#d0d0d0", fontsize=10)
        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_container)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _schedule_update(self):
        try:
            if not self.frame.winfo_exists():
                return
            self._update_metrics()
            self._after_id = self.frame.after(1000, self._schedule_update)
        except Exception:
            pass

    def cleanup(self):
        if hasattr(self, "_after_id"):
            try:
                self.frame.after_cancel(self._after_id)
            except Exception:
                pass

    def _update_metrics(self):
        metrics = self.metrics_service.get_ram_metrics()

        self.usage_label.configure(text=f"Usage: {metrics.percent:.1f}%")
        self.progress_bar.set(metrics.percent / 100.0)
        self.used_label.configure(text=f"Used: {metrics.used_gb:.2f} GB")
        self.available_label.configure(text=f"Available: {metrics.available_gb:.2f} GB")
        self.total_label.configure(text=f"Total: {metrics.total_gb:.2f} GB")

        self.history.append(metrics.percent)
        self.line.set_ydata(list(self.history))
        self.canvas.draw_idle()


def create_ram_tab(frame: ctk.CTkFrame, metrics_service: SystemMetricsService) -> RamTab:
    return RamTab(frame, metrics_service)