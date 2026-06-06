"""GPU information collector — supports NVIDIA, AMD and Intel GPUs."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.utils.logger import logger


@dataclass
class GPUInfo:
    name: str = "Unknown"
    vendor: str = "Unknown"
    vram_total_mb: float = 0.0
    vram_used_mb: float = 0.0
    temperature: Optional[float] = None
    driver_version: str = "N/A"
    utilization: float = 0.0
    power_draw_w: Optional[float] = None
    power_limit_w: Optional[float] = None
    clock_gpu_mhz: Optional[float] = None
    clock_mem_mhz: Optional[float] = None
    pcie_gen: str = "N/A"
    pcie_width: str = "N/A"
    opengl_version: str = "N/A"
    vulkan_version: str = "N/A"


class GPUCollector:
    """Collects GPU hardware information from multiple backends."""

    def __init__(self) -> None:
        self._amd_card: Optional[Path] = None
        self._backend: str = self._detect_backend()
        logger.info("GPU backend: %s", self._backend)

    def collect_static(self) -> GPUInfo:
        info = GPUInfo()
        if self._backend == "nvidia":
            self._collect_nvidia(info)
        elif self._backend == "amd":
            self._collect_amd(info)
        elif self._backend == "intel":
            self._collect_intel(info)
        self._collect_opengl(info)
        return info

    def collect_dynamic(self, info: GPUInfo) -> None:
        if self._backend == "nvidia":
            self._collect_nvidia(info)
        elif self._backend == "amd":
            self._collect_amd_dynamic(info)

    # ------------------------------------------------------------------ #

    def _detect_backend(self) -> str:
        try:
            subprocess.check_output(
                ["nvidia-smi", "-L"], stderr=subprocess.DEVNULL, timeout=3
            )
            return "nvidia"
        except (FileNotFoundError, subprocess.SubprocessError):
            pass

        for card in sorted(Path("/sys/class/drm").glob("card?")):
            vendor_file = card / "device" / "vendor"
            if vendor_file.exists():
                vendor_id = vendor_file.read_text().strip()
                if vendor_id == "0x1002":
                    self._amd_card = card
                    return "amd"
                if vendor_id == "0x8086":
                    return "intel"
        return "unknown"

    def _collect_nvidia(self, info: GPUInfo) -> None:
        fields = [
            "name",
            "memory.total",
            "memory.used",
            "temperature.gpu",
            "driver_version",
            "utilization.gpu",
            "power.draw",
            "power.limit",
            "clocks.current.graphics",
            "clocks.current.memory",
            "pcie.link.gen.current",
            "pcie.link.width.current",
        ]
        query = ",".join(fields)
        try:
            out = subprocess.check_output(
                ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            parts = [p.strip() for p in out.strip().split(",")]
            info.vendor = "NVIDIA"
            info.name = parts[0] if len(parts) > 0 else "N/A"
            info.vram_total_mb = float(parts[1]) if len(parts) > 1 and parts[1] != "N/A" else 0.0
            info.vram_used_mb = float(parts[2]) if len(parts) > 2 and parts[2] != "N/A" else 0.0
            info.temperature = float(parts[3]) if len(parts) > 3 and parts[3] != "N/A" else None
            info.driver_version = parts[4] if len(parts) > 4 else "N/A"
            info.utilization = float(parts[5]) if len(parts) > 5 and parts[5] != "N/A" else 0.0
            if len(parts) > 6 and parts[6] not in ("N/A", "[N/A]"):
                info.power_draw_w = float(parts[6])
            if len(parts) > 7 and parts[7] not in ("N/A", "[N/A]"):
                info.power_limit_w = float(parts[7])
            if len(parts) > 8 and parts[8] != "N/A":
                info.clock_gpu_mhz = float(parts[8])
            if len(parts) > 9 and parts[9] != "N/A":
                info.clock_mem_mhz = float(parts[9])
            info.pcie_gen = parts[10] if len(parts) > 10 else "N/A"
            info.pcie_width = f"x{parts[11]}" if len(parts) > 11 else "N/A"
        except (FileNotFoundError, subprocess.SubprocessError, ValueError, OSError) as exc:
            logger.debug("nvidia-smi error: %s", exc)

    def _collect_amd(self, info: GPUInfo) -> None:
        info.vendor = "AMD"
        card = self._amd_card
        if card is None:
            return
        dev = card / "device"

        product = dev / "product_name"
        if product.exists():
            info.name = product.read_text().strip()
        else:
            try:
                out = subprocess.check_output(
                    ["lspci", "-v"], text=True, stderr=subprocess.DEVNULL, timeout=5
                )
                for line in out.splitlines():
                    if "VGA" in line or "Display" in line:
                        info.name = line.split(":")[-1].strip()
                        break
            except Exception:
                pass

        vram_total = dev / "mem_info_vram_total"
        if vram_total.exists():
            info.vram_total_mb = int(vram_total.read_text().strip()) / 1024 / 1024

        self._collect_amd_dynamic(info)

    def _collect_amd_dynamic(self, info: GPUInfo) -> None:
        card = self._amd_card
        if card is None:
            return
        dev = card / "device"

        busy = dev / "gpu_busy_percent"
        if busy.exists():
            try:
                info.utilization = float(busy.read_text().strip())
            except ValueError:
                pass
        vram_used = dev / "mem_info_vram_used"
        if vram_used.exists():
            try:
                info.vram_used_mb = int(vram_used.read_text().strip()) / 1024 / 1024
            except ValueError:
                pass

        self._read_amd_temperature(info)

    def _read_amd_temperature(self, info: GPUInfo) -> None:
        try:
            import psutil
            for hw_name, entries in psutil.sensors_temperatures().items():
                if "amdgpu" in hw_name or "radeon" in hw_name:
                    info.temperature = entries[0].current
                    break
        except Exception:
            pass

    def _collect_intel(self, info: GPUInfo) -> None:
        info.vendor = "Intel"
        try:
            out = subprocess.check_output(
                ["lspci"], text=True, stderr=subprocess.DEVNULL, timeout=5
            )
            for line in out.splitlines():
                if "Intel" in line and ("VGA" in line or "Display" in line or "Graphics" in line):
                    info.name = line.split(":")[-1].strip()
                    break
        except Exception:
            pass

    def _collect_opengl(self, info: GPUInfo) -> None:
        try:
            out = subprocess.check_output(
                ["glxinfo", "-B"], text=True, stderr=subprocess.DEVNULL, timeout=5
            )
            for line in out.splitlines():
                if "OpenGL version string" in line:
                    info.opengl_version = line.split(":", 1)[-1].strip()[:40]
                    break
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
