"""RAM / Memory information collector."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import psutil

from src.utils.logger import logger


@dataclass
class RAMInfo:
    total_bytes: int = 0
    available_bytes: int = 0
    used_bytes: int = 0
    cached_bytes: int = 0
    buffers_bytes: int = 0
    shared_bytes: int = 0
    percent_used: float = 0.0
    swap_total_bytes: int = 0
    swap_used_bytes: int = 0
    swap_percent: float = 0.0
    # From /proc/meminfo
    mem_type: str = "N/A"
    speed_mt: str = "N/A"
    channels: str = "N/A"
    slots_used: int = 0
    slots_total: int = 0


class RAMCollector:
    """Collects memory information from /proc/meminfo and psutil."""

    def collect_static(self) -> RAMInfo:
        info = RAMInfo()
        self._read_meminfo(info)
        self._try_dmidecode(info)
        return info

    def collect_dynamic(self, info: RAMInfo) -> None:
        try:
            mem = psutil.virtual_memory()
            info.total_bytes = mem.total
            info.available_bytes = mem.available
            info.used_bytes = mem.used
            info.cached_bytes = getattr(mem, "cached", 0)
            info.buffers_bytes = getattr(mem, "buffers", 0)
            info.shared_bytes = getattr(mem, "shared", 0)
            info.percent_used = mem.percent

            swap = psutil.swap_memory()
            info.swap_total_bytes = swap.total
            info.swap_used_bytes = swap.used
            info.swap_percent = swap.percent
        except Exception as exc:
            logger.debug("RAM dynamic collect error: %s", exc)

    # ------------------------------------------------------------------ #

    def _read_meminfo(self, info: RAMInfo) -> None:
        try:
            kv: dict[str, int] = {}
            for line in Path("/proc/meminfo").read_text().splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    nums = re.findall(r"\d+", v)
                    kv[k.strip()] = int(nums[0]) * 1024 if nums else 0

            info.total_bytes = kv.get("MemTotal", 0)
            info.available_bytes = kv.get("MemAvailable", 0)
            info.cached_bytes = kv.get("Cached", 0)
            info.buffers_bytes = kv.get("Buffers", 0)
            info.shared_bytes = kv.get("Shmem", 0)
            info.used_bytes = info.total_bytes - info.available_bytes
            if info.total_bytes:
                info.percent_used = info.used_bytes / info.total_bytes * 100
        except OSError as exc:
            logger.warning("Cannot read /proc/meminfo: %s", exc)

    def _try_dmidecode(self, info: RAMInfo) -> None:
        """Try to read RAM specs via dmidecode (requires root or setuid)."""
        try:
            import subprocess
            out = subprocess.check_output(
                ["dmidecode", "-t", "17"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            speeds, types = [], set()
            slots_used = 0
            slots_total = 0
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("Type:") and "No Module" not in line:
                    typ = line.split(":", 1)[-1].strip()
                    if typ not in ("Unknown", "Other"):
                        types.add(typ)
                if line.startswith("Speed:") and "Unknown" not in line:
                    nums = re.findall(r"\d+", line)
                    if nums:
                        speeds.append(int(nums[0]))
                if "Size:" in line and "No Module" not in line and "Unknown" not in line:
                    slots_total += 1
                    if "MB" in line or "GB" in line:
                        slots_used += 1
            if types:
                info.mem_type = " / ".join(sorted(types))
            if speeds:
                info.speed_mt = f"{max(speeds)} MT/s"
            info.slots_used = slots_used
            info.slots_total = slots_total
        except Exception:
            pass
