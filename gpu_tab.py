from collections import deque
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from system_metrics import SystemMetricsService


class GpuTab:
    def __init__(self, parent_frame: ctk.CTkFrame, metrics_service: SystemMetricsService):
        self.frame = parent_frame
        self.metrics_service = metrics_service
        self._after_id = None

        self.history_length = 60
        self.util_history = deque([0.0] * self.history_length, maxlen=self.history_length)
        self.temp_history = deque([0.0] * self.history_length, maxlen=self.history_length)

        self._init_layout()
        self._init_graph()
        self._schedule_update()

    def _init_layout(self):
        self.frame.grid_columnconfigure(0, weight=0, minsize=300)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        self.info_panel = ctk.CTkFrame(self.frame, corner_radius=10)
        self.info_panel.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        title_label = ctk.CTkLabel(
            self.info_panel,
            text="GPU Monitor",
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold")
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 10))

        self.name_label = ctk.CTkLabel(
            self.info_panel,
            text="Device: Checking...",
            font=ctk.CTkFont(family="Helvetica", size=14, weight="bold"),
            wraplength=260,
            justify="left"
        )
        self.name_label.pack(anchor="w", padx=20, pady=5)

        self.util_label = ctk.CTkLabel(
            self.info_panel,
            text="Utilization: -- %",
            font=ctk.CTkFont(family="Helvetica", size=16)
        )
        self.util_label.pack(anchor="w", padx=20, pady=5)

        self.temp_label = ctk.CTkLabel(
            self.info_panel,
            text="Temperature: -- °C",
            font=ctk.CTkFont(family="Helvetica", size=14)
        )
        self.temp_label.pack(anchor="w", padx=20, pady=5)

        self.mem_label = ctk.CTkLabel(
            self.info_panel,
            text="VRAM: -- / -- MB",
            font=ctk.CTkFont(family="Helvetica", size=14)
        )
        self.mem_label.pack(anchor="w", padx=20, pady=5)

        self.status_label = ctk.CTkLabel(
            self.info_panel,
            text="",
            font=ctk.CTkFont(family="Helvetica", size=12),
            text_color="#e06c75",
            wraplength=260,
            justify="left"
        )
        self.status_label.pack(anchor="w", padx=20, pady=(15, 5))

    def _init_graph(self):
        self.graph_container = ctk.CTkFrame(self.frame, corner_radius=10)
        self.graph_container.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)

        self.fig, (self.ax_util, self.ax_temp) = plt.subplots(2, 1, figsize=(6, 5), dpi=100)
        self.fig.patch.set_facecolor("#242424")

        for ax, color, title in zip(
            (self.ax_util, self.ax_temp),
            ("#d19a66", "#e06c75"),
            ("GPU Utilization (%)", "Temperature (°C)")
        ):
            ax.set_facecolor("#1f1f1f")
            ax.set_ylim(0, 100)
            ax.set_xlim(0, self.history_length - 1)
            ax.tick_params(colors="#a0a0a0", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#404040")
            ax.grid(True, linestyle="--", alpha=0.3, color="#606060")
            ax.set_ylabel(title, color="#d0d0d0", fontsize=9)

        self.line_util, = self.ax_util.plot(
            range(self.history_length), list(self.util_history), color="#e5c07b", linewidth=2
        )
        self.line_temp, = self.ax_temp.plot(
            range(self.history_length), list(self.temp_history), color="#e06c75", linewidth=2
        )

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
        gpu = self.metrics_service.get_gpu_metrics()

        if not gpu.is_available:
            self.name_label.configure(text=gpu.name)
            self.util_label.configure(text="Utilization: N/A")
            self.temp_label.configure(text="Temperature: N/A")
            self.mem_label.configure(text="VRAM: N/A")
            self.status_label.configure(text=f"Status: {gpu.error_message}")
            return

        self.name_label.configure(text=gpu.name)
        self.status_label.configure(text=f"Source: {gpu.backend_info}", text_color="#98c379")
        self.util_label.configure(text=f"Utilization: {gpu.utilization_percent:.1f}%")

        if gpu.temperature_celsius is not None:
            self.temp_label.configure(text=f"Temperature: {gpu.temperature_celsius:.1f} °C")
            self.temp_history.append(gpu.temperature_celsius)
        else:
            self.temp_label.configure(text="Temperature: N/A (OS Generic)")
            self.temp_history.append(0.0)

        if gpu.memory_used_mb is not None and gpu.memory_total_mb is not None:
            self.mem_label.configure(
                text=f"VRAM: {gpu.memory_used_mb:.0f} / {gpu.memory_total_mb:.0f} MB"
            )
        else:
            self.mem_label.configure(text="VRAM: Shared / Dynamic")

        self.util_history.append(gpu.utilization_percent)

        self.line_util.set_ydata(list(self.util_history))
        self.line_temp.set_ydata(list(self.temp_history))
        self.canvas.draw_idle()

    def cleanup(self):
        if self._after_id:
            try:
                self.frame.after_cancel(self._after_id)
            except Exception:
                pass


def create_gpu_tab(frame: ctk.CTkFrame, metrics_service: SystemMetricsService) -> GpuTab:
    return GpuTab(frame, metrics_service)