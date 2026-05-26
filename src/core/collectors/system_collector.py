"""System / OS information collector."""

from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psutil

from src.utils.logger import logger


@dataclass
class SystemInfo:
    hostname: str = "Unknown"
    username: str = "Unknown"
    os_name: str = "Unknown"
    os_version: str = "Unknown"
    os_id: str = "Unknown"
    kernel: str = "Unknown"
    architecture: str = "Unknown"
    desktop_environment: str = "N/A"
    window_manager: str = "N/A"
    shell: str = "N/A"
    uptime_seconds: float = 0.0
    boot_time: float = 0.0
    process_count: int = 0
    thread_count: int = 0
    # Mainboard
    board_vendor: str = "N/A"
    board_name: str = "N/A"
    board_version: str = "N/A"
    bios_vendor: str = "N/A"
    bios_version: str = "N/A"
    bios_date: str = "N/A"
    chassis_type: str = "N/A"
    # Python
    python_version: str = platform.python_version()
    # Packages
    pacman_packages: int = 0
    flatpak_packages: int = 0


class SystemCollector:
    """Collects OS, kernel, desktop and mainboard information."""

    def collect_static(self) -> SystemInfo:
        info = SystemInfo()
        self._read_os_release(info)
        self._read_kernel(info)
        self._read_user_env(info)
        self._read_dmi(info)
        self._count_packages(info)
        return info

    def collect_dynamic(self, info: SystemInfo) -> None:
        try:
            info.uptime_seconds = psutil.time.time() - psutil.boot_time()
            info.process_count = len(psutil.pids())
            info.thread_count = sum(
                p.num_threads()
                for p in psutil.process_iter(["num_threads"])
                if p.info["num_threads"]
            )
        except Exception as exc:
            logger.debug("System dynamic error: %s", exc)

    # ------------------------------------------------------------------ #

    def _read_os_release(self, info: SystemInfo) -> None:
        try:
            kv: dict[str, str] = {}
            for line in Path("/etc/os-release").read_text().splitlines():
                if "=" in line:
                    k, _, v = line.partition("=")
                    kv[k.strip()] = v.strip().strip('"')
            info.os_name = kv.get("PRETTY_NAME", kv.get("NAME", "Unknown"))
            info.os_version = kv.get("VERSION", kv.get("VERSION_ID", ""))
            info.os_id = kv.get("ID", "unknown")
        except OSError:
            info.os_name = platform.system()

    def _read_kernel(self, info: SystemInfo) -> None:
        info.kernel = platform.release()
        info.architecture = platform.machine()
        try:
            info.hostname = platform.node()
        except Exception:
            pass
        info.boot_time = psutil.boot_time()
        import time
        info.uptime_seconds = time.time() - info.boot_time

    def _read_user_env(self, info: SystemInfo) -> None:
        info.username = os.environ.get("USER", os.environ.get("LOGNAME", "unknown"))
        info.shell = Path(os.environ.get("SHELL", "/bin/bash")).name

        de_keys = ("XDG_CURRENT_DESKTOP", "DESKTOP_SESSION", "XDG_SESSION_DESKTOP")
        for key in de_keys:
            val = os.environ.get(key, "")
            if val:
                info.desktop_environment = val
                break

        wm_keys = ("GDMSESSION", "WAYLAND_DISPLAY", "DISPLAY")
        if os.environ.get("WAYLAND_DISPLAY"):
            info.window_manager = "Wayland"
        elif os.environ.get("DISPLAY"):
            info.window_manager = "X11"

        if not info.desktop_environment:
            info.desktop_environment = self._detect_de_from_proc()

    def _detect_de_from_proc(self) -> str:
        de_procs = {
            "gnome-shell": "GNOME",
            "plasmashell": "KDE Plasma",
            "xfce4-session": "XFCE",
            "cinnamon": "Cinnamon",
            "mate-session": "MATE",
            "lxqt-session": "LXQt",
            "i3": "i3",
            "sway": "Sway",
            "hyprland": "Hyprland",
            "openbox": "Openbox",
        }
        try:
            for proc in psutil.process_iter(["name"]):
                name = proc.info.get("name", "").lower()
                if name in de_procs:
                    return de_procs[name]
        except Exception:
            pass
        return "N/A"

    def _read_dmi(self, info: SystemInfo) -> None:
        dmi_map = {
            "board_vendor": "/sys/class/dmi/id/board_vendor",
            "board_name": "/sys/class/dmi/id/board_name",
            "board_version": "/sys/class/dmi/id/board_version",
            "bios_vendor": "/sys/class/dmi/id/bios_vendor",
            "bios_version": "/sys/class/dmi/id/bios_version",
            "bios_date": "/sys/class/dmi/id/bios_date",
            "chassis_type": "/sys/class/dmi/id/chassis_type",
        }
        for attr, path in dmi_map.items():
            try:
                val = Path(path).read_text().strip()
                setattr(info, attr, val or "N/A")
            except OSError:
                pass

    def _count_packages(self, info: SystemInfo) -> None:
        try:
            out = subprocess.check_output(
                ["pacman", "-Q"], text=True, stderr=subprocess.DEVNULL, timeout=10
            )
            info.pacman_packages = len(out.strip().splitlines())
        except Exception:
            pass
        try:
            out = subprocess.check_output(
                ["flatpak", "list"], text=True, stderr=subprocess.DEVNULL, timeout=5
            )
            info.flatpak_packages = len(
                [l for l in out.strip().splitlines() if l.strip()]
            )
        except Exception:
            pass
