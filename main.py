import sys
import customtkinter as ctk
from window_factory import create_main_window
from system_metrics import SystemMetricsService
import cpu_tab
import gpu_tab
import ram_tab
import storage_tab
import theme_tab


class TaskManagerApp:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.metrics_service = SystemMetricsService()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(expand=True, fill="both", padx=10, pady=10)

        self.tab_cpu = self.tabview.add("CPU")
        self.tab_gpu = self.tabview.add("GPU")
        self.tab_ram = self.tabview.add("RAM")
        self.tab_storage = self.tabview.add("Storage")
        self.tab_theme = self.tabview.add("Theme")

        self.cpu_view = cpu_tab.create_cpu_tab(self.tab_cpu, self.metrics_service)
        self.gpu_view = gpu_tab.create_gpu_tab(self.tab_gpu, self.metrics_service)
        self.ram_view = ram_tab.create_ram_tab(self.tab_ram, self.metrics_service)
        self.storage_view = storage_tab.create_storage_tab(self.tab_storage, self.metrics_service)
        self.theme_view = theme_tab.create_theme_tab(self.tab_theme)

    def on_closing(self):
        for view in (self.cpu_view, self.gpu_view, self.ram_view):
            if hasattr(view, "cleanup"):
                view.cleanup()

        try:
            self.metrics_service.stop()
        except Exception:
            pass

        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

        sys.exit(0)


def main():
    root = create_main_window()
    app = TaskManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()