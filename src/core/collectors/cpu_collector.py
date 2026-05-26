"""CPU information collector — reads from /proc, /sys, lscpu and psutil."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import psutil

from src.utils.logger import logger


@dataclass
class CPUInfo:
    name: str = "Unknown"
    vendor: str = "Unknown"
    architecture: str = "Unknown"
    cores_physical: int = 0
    cores_logical: int = 0
    base_frequency_mhz: float = 0.0
    max_frequency_mhz: float = 0.0
    current_frequency_mhz: float = 0.0
    cache_l1d: str = "N/A"
    cache_l1i: str = "N/A"
    cache_l2: str = "N/A"
    cache_l3: str = "N/A"
    flags: list[str] = field(default_factory=list)
    temperature: Optional[float] = None
    usage_total: float = 0.0
    usage_per_core: list[float] = field(default_factory=list)
    stepping: str = "N/A"
    family: str = "N/A"
    model_id: str = "N/A"
    microcode: str = "N/A"
    virtualization: str = "N/A"
    numa_nodes: int = 1


class CPUCollector:
    """Collects CPU hardware information."""

    def collect_static(self) -> CPUInfo:
        info = CPUInfo()
        self._read_proc_cpuinfo(info)
        self._read_lscpu(info)
        info.cores_physical = psutil.cpu_count(logical=False) or 0
        info.cores_logical = psutil.cpu_count(logical=True) or 0
        freq = psutil.cpu_freq()
        if freq:
            info.base_frequency_mhz = freq.min or freq.current
            info.max_frequency_mhz = freq.max or freq.current
        return info

    def collect_dynamic(self, info: CPUInfo) -> None:
        try:
            freq = psutil.cpu_freq()
            if freq:
                info.current_frequency_mhz = freq.current
            info.usage_total = psutil.cpu_percent(interval=None)
            info.usage_per_core = psutil.cpu_percent(interval=None, percpu=True)
        except Exception as exc:
            logger.debug("CPU dynamic collect error: %s", exc)

        info.temperature = self._read_temperature()

    # ------------------------------------------------------------------ #

    def _read_proc_cpuinfo(self, info: CPUInfo) -> None:
        try:
            text = Path("/proc/cpuinfo").read_text()
            kv: dict[str, str] = {}
            for line in text.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    kv[k.strip()] = v.strip()
            info.name = kv.get("model name", "Unknown")
            info.vendor = kv.get("vendor_id", "Unknown")
            info.stepping = kv.get("stepping", "N/A")
            info.family = kv.get("cpu family", "N/A")
            info.model_id = kv.get("model", "N/A")
            info.microcode = kv.get("microcode", "N/A")
            flags_raw = kv.get("flags", "")
            info.flags = flags_raw.split()[:20]  # keep first 20
        except OSError as exc:
            logger.warning("Cannot read /proc/cpuinfo: %s", exc)

    def _read_lscpu(self, info: CPUInfo) -> None:
        try:
            out = subprocess.check_output(
                ["lscpu"], text=True, stderr=subprocess.DEVNULL, timeout=5
            )
            kv: dict[str, str] = {}
            for line in out.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    kv[k.strip()] = v.strip()

            info.architecture = kv.get("Architecture", info.architecture)
            info.virtualization = kv.get("Virtualization", "N/A")
            info.numa_nodes = int(kv.get("NUMA node(s)", "1"))

            for key, attr in (
                ("L1d cache", "cache_l1d"),
                ("L1i cache", "cache_l1i"),
                ("L2 cache", "cache_l2"),
                ("L3 cache", "cache_l3"),
            ):
                if key in kv:
                    setattr(info, attr, kv[key])

            # Parse max MHz from lscpu if psutil didn't get it
            if "CPU max MHz" in kv:
                try:
                    info.max_frequency_mhz = float(kv["CPU max MHz"].replace(",", "."))
                except ValueError:
                    pass
            if "CPU min MHz" in kv:
                try:
                    info.base_frequency_mhz = float(kv["CPU min MHz"].replace(",", "."))
                except ValueError:
                    pass
        except (FileNotFoundError, subprocess.SubprocessError, OSError) as exc:
            logger.debug("lscpu unavailable: %s", exc)

    def _read_temperature(self) -> Optional[float]:
        try:
            temps = psutil.sensors_temperatures()
            for sensor_name in ("coretemp", "k10temp", "zenpower", "cpu_thermal"):
                if sensor_name in temps:
                    entries = temps[sensor_name]
                    for entry in entries:
                        label = entry.label.lower()
                        if any(k in label for k in ("package", "tdie", "tctl", "input")):
                            return entry.current
                    if entries:
                        return entries[0].current
        except Exception as exc:
            logger.debug("Temperature read error: %s", exc)
        return None
