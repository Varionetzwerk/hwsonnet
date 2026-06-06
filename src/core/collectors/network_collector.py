"""Network interface information collector."""

from __future__ import annotations

import re
import socket
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import psutil

from src.utils.logger import logger


@dataclass
class NetworkInterface:
    name: str = ""
    mac: str = "N/A"
    ipv4: str = "N/A"
    ipv6: str = "N/A"
    speed_mbps: int = 0
    is_up: bool = False
    is_wireless: bool = False
    ssid: str = "N/A"
    signal_dbm: Optional[int] = None
    bytes_sent: int = 0
    bytes_recv: int = 0
    send_rate_bytes: float = 0.0
    recv_rate_bytes: float = 0.0


@dataclass
class NetworkInfo:
    interfaces: list[NetworkInterface] = field(default_factory=list)
    public_ip: str = "N/A"
    hostname: str = "N/A"


class NetworkCollector:
    """Collects network interface data via psutil and system tools."""

    def __init__(self) -> None:
        self._prev_io: dict[str, tuple[int, int]] = {}
        try:
            self._hostname = socket.gethostname()
        except Exception:
            self._hostname = "unknown"

    def collect_static(self) -> NetworkInfo:
        info = NetworkInfo()
        info.hostname = self._hostname
        info.interfaces = self._collect_interfaces()
        return info

    def collect_dynamic(self, info: NetworkInfo) -> None:
        try:
            counters = psutil.net_io_counters(pernic=True)
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()

            existing = {iface.name: iface for iface in info.interfaces}
            seen = set()

            for name, counter in counters.items():
                if name == "lo":
                    continue
                seen.add(name)
                if name not in existing:
                    iface = NetworkInterface(name=name)
                    info.interfaces.append(iface)
                    existing[name] = iface
                iface = existing[name]

                if name in self._prev_io:
                    ps, pr = self._prev_io[name]
                    iface.send_rate_bytes = max(0, counter.bytes_sent - ps)
                    iface.recv_rate_bytes = max(0, counter.bytes_recv - pr)
                self._prev_io[name] = (counter.bytes_sent, counter.bytes_recv)
                iface.bytes_sent = counter.bytes_sent
                iface.bytes_recv = counter.bytes_recv

                if name in stats:
                    iface.is_up = stats[name].isup
                    iface.speed_mbps = stats[name].speed

                if name in addrs:
                    for addr in addrs[name]:
                        if addr.family == socket.AF_INET:
                            iface.ipv4 = addr.address
                        elif addr.family == socket.AF_INET6:
                            iface.ipv6 = addr.address.split("%")[0]

                if iface.is_wireless:
                    self._update_wifi(iface)

            # Remove gone interfaces
            info.interfaces = [i for i in info.interfaces if i.name in seen]
        except Exception as exc:
            logger.debug("Network dynamic error: %s", exc)

    # ------------------------------------------------------------------ #

    def _collect_interfaces(self) -> list[NetworkInterface]:
        interfaces: list[NetworkInterface] = []
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()

            for name, addr_list in addrs.items():
                if name == "lo":
                    continue
                iface = NetworkInterface(name=name)
                for addr in addr_list:
                    if addr.family == socket.AF_PACKET:
                        iface.mac = addr.address
                    elif addr.family == socket.AF_INET:
                        iface.ipv4 = addr.address
                    elif addr.family == socket.AF_INET6:
                        iface.ipv6 = addr.address.split("%")[0]
                if name in stats:
                    iface.is_up = stats[name].isup
                    iface.speed_mbps = stats[name].speed
                iface.is_wireless = self._is_wireless(name)
                if iface.is_wireless:
                    self._update_wifi(iface)
                interfaces.append(iface)
        except Exception as exc:
            logger.warning("Interface collect error: %s", exc)
        return interfaces

    def _is_wireless(self, name: str) -> bool:
        return Path(f"/sys/class/net/{name}/wireless").exists()

    def _update_wifi(self, iface: NetworkInterface) -> None:
        try:
            out = subprocess.check_output(
                ["iwconfig", iface.name],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            for line in out.splitlines():
                if "ESSID:" in line:
                    ssid = line.split("ESSID:")[-1].strip().strip('"')
                    iface.ssid = ssid if ssid != "off/any" else "N/A"
                if "Signal level=" in line:
                    m = re.search(r"Signal level=(-?\d+)", line)
                    if m:
                        iface.signal_dbm = int(m.group(1))
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
