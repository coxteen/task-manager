import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Optional, List
import psutil

try:
    import wmi
    import pythoncom
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False


@dataclass(frozen=True)
class CpuMetrics:
    total_percent: float
    per_cpu_percent: List[float]
    frequency_mhz: Optional[float]
    logical_cores: int
    physical_cores: int


@dataclass(frozen=True)
class RamMetrics:
    total_bytes: int
    used_bytes: int
    available_bytes: int
    percent: float

    @property
    def total_gb(self) -> float:
        return self.total_bytes / (1024 ** 3)

    @property
    def used_gb(self) -> float:
        return self.used_bytes / (1024 ** 3)

    @property
    def available_gb(self) -> float:
        return self.available_bytes / (1024 ** 3)


@dataclass(frozen=True)
class DiskPartitionMetrics:
    device: str
    mountpoint: str
    fstype: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float

    @property
    def total_gb(self) -> float:
        return self.total_bytes / (1024 ** 3)

    @property
    def used_gb(self) -> float:
        return self.used_bytes / (1024 ** 3)

    @property
    def free_gb(self) -> float:
        return self.free_bytes / (1024 ** 3)


@dataclass(frozen=True)
class GpuMetrics:
    name: str
    utilization_percent: float
    temperature_celsius: Optional[float]
    memory_used_mb: Optional[float]
    memory_total_mb: Optional[float]
    backend_info: str
    is_available: bool = True
    error_message: Optional[str] = None


class SystemMetricsService:
    """
    Serviciu thread-safe care colectează metricile pe un thread de fundal dedicat.
    Interfața grafică consumă valorile instantaneu din memorie (fără latență I/O sau WMI).
    """

    def __init__(self):
        self._running = True
        self._lock = threading.Lock()
        self.nvidia_smi_path = self._locate_nvidia_smi()

        self._current_cpu = CpuMetrics(0.0, [], None, psutil.cpu_count(logical=True) or 1, psutil.cpu_count(logical=False) or 1)
        self._current_ram = RamMetrics(0, 0, 0, 0.0)
        self._current_disks: List[DiskPartitionMetrics] = []
        self._current_gpu = GpuMetrics("Detecting...", 0.0, None, None, None, "Initializing", True)

        self._worker_thread = threading.Thread(target=self._background_collector_loop, daemon=True)
        self._worker_thread.start()

    def stop(self):
        """Oprește colectarea în fundal."""
        self._running = False

    def _locate_nvidia_smi(self) -> Optional[str]:
        in_path = shutil.which("nvidia-smi")
        if in_path:
            return in_path

        candidates = [
            r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe",
            r"C:\Windows\System32\nvidia-smi.exe",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def _background_collector_loop(self):
        wmi_obj = None
        generic_gpu_name = "Generic Video Adapter"
        if WMI_AVAILABLE:
            try:
                pythoncom.CoInitialize()
                wmi_obj = wmi.WMI()
                controllers = wmi_obj.Win32_VideoController()
                if controllers:
                    generic_gpu_name = controllers[0].Name.strip()
            except Exception:
                wmi_obj = None

        psutil.cpu_percent(interval=None)

        while self._running:
            start_time = time.time()

            freq = psutil.cpu_freq()
            cpu = CpuMetrics(
                total_percent=psutil.cpu_percent(interval=None),
                per_cpu_percent=psutil.cpu_percent(interval=None, percpu=True),
                frequency_mhz=freq.current if freq else None,
                logical_cores=psutil.cpu_count(logical=True) or 1,
                physical_cores=psutil.cpu_count(logical=False) or 1,
            )

            vmem = psutil.virtual_memory()
            ram = RamMetrics(
                total_bytes=vmem.total,
                used_bytes=vmem.used,
                available_bytes=vmem.available,
                percent=vmem.percent,
            )

            disks = []
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disks.append(
                        DiskPartitionMetrics(
                            device=part.device,
                            mountpoint=part.mountpoint,
                            fstype=part.fstype,
                            total_bytes=usage.total,
                            used_bytes=usage.used,
                            free_bytes=usage.free,
                            percent=usage.percent,
                        )
                    )
                except (PermissionError, OSError):
                    continue

            gpu = self._collect_gpu_metrics(wmi_obj, generic_gpu_name)

            with self._lock:
                self._current_cpu = cpu
                self._current_ram = ram
                self._current_disks = disks
                self._current_gpu = gpu

            elapsed = time.time() - start_time
            sleep_duration = max(0.1, 1.0 - elapsed)
            time.sleep(sleep_duration)

        if WMI_AVAILABLE:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

    def _collect_gpu_metrics(self, wmi_obj, generic_gpu_name: str) -> GpuMetrics:
        if self.nvidia_smi_path:
            try:
                cmd = [
                    self.nvidia_smi_path,
                    "--query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=1.0)
                lines = result.stdout.strip().splitlines()
                if lines:
                    parts = [p.strip() for p in lines[0].split(",")]
                    return GpuMetrics(
                        name=parts[0],
                        utilization_percent=float(parts[1]),
                        temperature_celsius=float(parts[2]),
                        memory_used_mb=float(parts[3]),
                        memory_total_mb=float(parts[4]),
                        backend_info="Nvidia Driver (SMI)",
                        is_available=True,
                    )
            except Exception:
                pass

        if wmi_obj:
            try:
                engines = wmi_obj.Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine()
                total_usage = sum(float(e.UtilizationPercentage) for e in engines if hasattr(e, "UtilizationPercentage"))
                return GpuMetrics(
                    name=generic_gpu_name,
                    utilization_percent=min(max(total_usage, 0.0), 100.0),
                    temperature_celsius=None,
                    memory_used_mb=None,
                    memory_total_mb=None,
                    backend_info="Windows Performance Counter",
                    is_available=True,
                )
            except Exception as ex:
                return GpuMetrics(
                    name=generic_gpu_name,
                    utilization_percent=0.0,
                    temperature_celsius=None,
                    memory_used_mb=None,
                    memory_total_mb=None,
                    backend_info="WMI",
                    is_available=True,
                    error_message=str(ex),
                )

        return GpuMetrics(
            name="Generic GPU",
            utilization_percent=0.0,
            temperature_celsius=None,
            memory_used_mb=None,
            memory_total_mb=None,
            backend_info="Unavailable",
            is_available=False,
            error_message="WMI not available",
        )

    def get_cpu_metrics(self) -> CpuMetrics:
        with self._lock:
            return self._current_cpu

    def get_ram_metrics(self) -> RamMetrics:
        with self._lock:
            return self._current_ram

    def get_disk_metrics(self) -> List[DiskPartitionMetrics]:
        with self._lock:
            return self._current_disks

    def get_gpu_metrics(self) -> GpuMetrics:
        with self._lock:
            return self._current_gpu