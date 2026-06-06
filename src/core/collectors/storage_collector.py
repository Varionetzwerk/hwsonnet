"""Storage device information collector."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import psutil

from src.utils.logger import logger


@dataclass
class DiskDevice:
    name: str = ""
    model: str = "Unknown"
    serial: str = "N/A"
    size_bytes: int = 0
    disk_type: str = "Unknown"   # SSD / HDD / NVMe
    rotation_rate: str = "N/A"
    temperature: Optional[float] = None
    smart_status: str = "N/A"
    read_speed_bytes: float = 0.0
    write_speed_bytes: float = 0.0


@dataclass
class Partition:
    device: str = ""
    mountpoint: str = ""
    fstype: str = ""
    total_bytes: int = 0
    used_bytes: int = 0
    free_bytes: int = 0
    percent_used: float = 0.0


@dataclass
class StorageInfo:
    devices: list[DiskDevice] = field(default_factory=list)
    partitions: list[Partition] = field(default_factory=list)


class StorageCollector:
    """Collects storage information via lsblk, psutil, and smartctl."""

    def __init__(self) -> None:
        self._prev_io: dict[str, tuple[int, int]] = {}

    def collect_static(self) -> StorageInfo:
        info = StorageInfo()
        info.devices = self._collect_devices()
        info.partitions = self._collect_partitions()
        return info

    def collect_dynamic(self, info: StorageInfo) -> None:
        try:
            counters = psutil.disk_io_counters(perdisk=True)
            for device in info.devices:
                dev_name = device.name.replace("/dev/", "")
                if dev_name in counters:
                    cur = counters[dev_name]
                    if dev_name in self._prev_io:
                        prev = self._prev_io[dev_name]
                        device.read_speed_bytes = cur.read_bytes - prev[0]
                        device.write_speed_bytes = cur.write_bytes - prev[1]
                    self._prev_io[dev_name] = (cur.read_bytes, cur.write_bytes)
        except Exception as exc:
            logger.debug("Storage dynamic error: %s", exc)

        info.partitions = self._collect_partitions()

    # ------------------------------------------------------------------ #

    def _collect_devices(self) -> list[DiskDevice]:
        devices = []
        try:
            out = subprocess.check_output(
                ["lsblk", "-d", "-o", "NAME,MODEL,SIZE,ROTA,TYPE,SERIAL", "--bytes", "--noheadings"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
            for line in out.strip().splitlines():
                parts = line.split(None, 5)
                if len(parts) < 4:
                    continue
                dtype = parts[4] if len(parts) > 4 else "disk"
                if dtype not in ("disk", "nvme"):
                    continue
                dev = DiskDevice()
                dev.name = f"/dev/{parts[0]}"
                dev.model = parts[1] if len(parts) > 1 else "Unknown"
                try:
                    dev.size_bytes = int(parts[2]) if len(parts) > 2 else 0
                except ValueError:
                    pass
                rota = parts[3] if len(parts) > 3 else "1"
                dev.serial = parts[5].strip() if len(parts) > 5 else "N/A"

                if "nvme" in parts[0]:
                    dev.disk_type = "NVMe"
                elif rota == "0":
                    dev.disk_type = "SSD"
                else:
                    dev.disk_type = "HDD"

                self._try_smart(dev)
                devices.append(dev)
        except (FileNotFoundError, subprocess.SubprocessError, OSError) as exc:
            logger.debug("lsblk error: %s", exc)
            devices = self._fallback_devices()
        return devices

    def _fallback_devices(self) -> list[DiskDevice]:
        devices = []
        for part in psutil.disk_partitions():
            if part.fstype in ("squashfs", "tmpfs", "devtmpfs", ""):
                continue
            dev = DiskDevice()
            dev.name = part.device
            try:
                usage = psutil.disk_usage(part.mountpoint)
                dev.size_bytes = usage.total
            except (PermissionError, OSError):
                pass
            devices.append(dev)
        return devices

    def _try_smart(self, dev: DiskDevice) -> None:
        try:
            out = subprocess.check_output(
                ["smartctl", "-i", "-H", dev.name],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            for line in out.splitlines():
                if "SMART overall-health" in line:
                    dev.smart_status = "PASSED" if "PASSED" in line else "FAILED"
                if "Temperature_Celsius" in line or "Temperature:" in line:
                    nums = re.findall(r"\d+", line)
                    if nums:
                        dev.temperature = float(nums[-1])
                if "Rotation Rate" in line:
                    dev.rotation_rate = line.split(":", 1)[-1].strip()
        except Exception:
            pass

    def _collect_partitions(self) -> list[Partition]:
        partitions = []
        skip_fs = {"squashfs", "tmpfs", "devtmpfs", "proc", "sysfs", "devpts", "cgroup", ""}
        try:
            for p in psutil.disk_partitions():
                if p.fstype in skip_fs:
                    continue
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                except (PermissionError, OSError):
                    continue
                part = Partition(
                    device=p.device,
                    mountpoint=p.mountpoint,
                    fstype=p.fstype,
                    total_bytes=usage.total,
                    used_bytes=usage.used,
                    free_bytes=usage.free,
                    percent_used=usage.percent,
                )
                partitions.append(part)
        except Exception as exc:
            logger.debug("Partition collect error: %s", exc)
        return partitions
