from collections import deque
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from system_metrics import SystemMetricsService


class CpuTab:
    def __init__(self, parent_frame: ctk.CTkFrame, metrics_service: SystemMetricsService):
        self.frame = parent_frame
        self.metrics_service = metrics_service
        self._after_id = None

        self.history_length = 60
        self.history = deque([0.0] * self.history_length, maxlen=self.history_length)

        self._init_layout()
        self._init_graph()
        self._schedule_update()

    def _init_layout(self):
        self.frame.grid_columnconfigure(0, weight=0, minsize=260)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        self.info_panel = ctk.CTkFrame(self.frame, corner_radius=10)
        self.info_panel.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        title_label = ctk.CTkLabel(
            self.info_panel,
            text="CPU Monitor",
            font=ctk.CTkFont(family="Helvetica", size=26, weight="bold")
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 10))

        self.usage_label = ctk.CTkLabel(
            self.info_panel,
            text="Utilization: -- %",
            font=ctk.CTkFont(family="Helvetica", size=18)
        )
        self.usage_label.pack(anchor="w", padx=20, pady=8)

        self.cores_label = ctk.CTkLabel(
            self.info_panel,
            text="Cores: --",
            font=ctk.CTkFont(family="Helvetica", size=14)
        )
        self.cores_label.pack(anchor="w", padx=20, pady=5)

        self.freq_label = ctk.CTkLabel(
            self.info_panel,
            text="Frequency: -- MHz",
            font=ctk.CTkFont(family="Helvetica", size=14)
        )
        self.freq_label.pack(anchor="w", padx=20, pady=5)

    def _init_graph(self):
        self.graph_container = ctk.CTkFrame(self.frame, corner_radius=10)
        self.graph_container.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)

        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.fig.patch.set_facecolor("#242424")
        self.ax.set_facecolor("#1f1f1f")

        self.line, = self.ax.plot(
            range(self.history_length),
            list(self.history),
            color="#3a7ebf",
            linewidth=2,
            label="CPU %"
        )

        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, self.history_length - 1)
        self.ax.tick_params(colors="#a0a0a0", labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color("#404040")
        self.ax.grid(True, linestyle="--", alpha=0.3, color="#606060")
        self.ax.set_ylabel("Utilization (%)", color="#d0d0d0", fontsize=10)
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

    def _update_metrics(self):
        metrics = self.metrics_service.get_cpu_metrics()

        self.usage_label.configure(text=f"Utilization: {metrics.total_percent:.1f}%")
        self.cores_label.configure(
            text=f"Cores: {metrics.physical_cores} Physical / {metrics.logical_cores} Logical"
        )
        freq_text = f"{metrics.frequency_mhz:.0f} MHz" if metrics.frequency_mhz else "N/A"
        self.freq_label.configure(text=f"Frequency: {freq_text}")

        self.history.append(metrics.total_percent)
        self.line.set_ydata(list(self.history))
        self.canvas.draw_idle()

    def cleanup(self):
        if self._after_id:
            try:
                self.frame.after_cancel(self._after_id)
            except Exception:
                pass


def create_cpu_tab(frame: ctk.CTkFrame, metrics_service: SystemMetricsService) -> CpuTab:
    return CpuTab(frame, metrics_service)