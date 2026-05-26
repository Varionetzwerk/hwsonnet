"""Network information page."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QSizePolicy,
)

from src.core.collectors.network_collector import NetworkInfo, NetworkInterface
from src.ui.styles.dark_theme import (
    TEXT, TEXT_SUB, ACCENT, GREEN, YELLOW, RED, ORANGE, SURFACE, BORDER
)
from src.ui.widgets.live_chart import MultiLineChart, LiveChart
from src.utils.format import format_bytes, format_speed


class InterfaceCard(QWidget):
    """Card showing status and stats for one network interface."""

    def __init__(self, iface: NetworkInterface, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        # Header
        hdr = QHBoxLayout()
        name_l = QLabel(f"<b>{iface.name}</b>")
        name_l.setStyleSheet("background: transparent; font-size: 15px;")
        hdr.addWidget(name_l)

        status_color = GREEN if iface.is_up else "#484f58"
        status_l = QLabel("● UP" if iface.is_up else "● DOWN")
        status_l.setStyleSheet(f"color: {status_color}; font-size: 11px; background: transparent;")
        hdr.addWidget(status_l)

        if iface.is_wireless:
            wifi_l = QLabel("📶 WiFi")
            wifi_l.setStyleSheet(f"color: {ACCENT}; font-size: 11px; background: transparent;")
            hdr.addWidget(wifi_l)

        hdr.addStretch()
        speed_chip = QLabel(f"{iface.speed_mbps} Mbps" if iface.speed_mbps else "")
        speed_chip.setStyleSheet(
            f"background: {ACCENT}22; color: {ACCENT}; border: 1px solid {ACCENT}55;"
            "border-radius: 8px; padding: 1px 8px; font-size: 10px; background: transparent;"
        )
        hdr.addWidget(speed_chip)
        layout.addLayout(hdr)

        # Info rows
        rows = [
            ("MAC", iface.mac),
            ("IPv4", iface.ipv4),
            ("IPv6", iface.ipv6[:36] + "…" if len(iface.ipv6) > 36 else iface.ipv6),
        ]
        if iface.is_wireless and iface.ssid != "N/A":
            rows.append(("SSID", iface.ssid))
            if iface.signal_dbm is not None:
                rows.append(("Signal", f"{iface.signal_dbm} dBm"))

        for k, v in rows:
            row = QHBoxLayout()
            kl = QLabel(k + ":")
            kl.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11px; background: transparent;")
            kl.setFixedWidth(44)
            vl = QLabel(v)
            vl.setStyleSheet(f"color: {TEXT}; font-size: 11px; background: transparent;")
            vl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(kl)
            row.addWidget(vl)
            row.addStretch()
            layout.addLayout(row)

        # Transfer row
        self._tx_label = QLabel("")
        self._tx_label.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11px; background: transparent;")
        layout.addWidget(self._tx_label)

        self._rate_label = QLabel("")
        self._rate_label.setStyleSheet(f"color: {ACCENT}; font-size: 12px; font-weight: 600; background: transparent;")
        layout.addWidget(self._rate_label)

    def refresh(self, iface: NetworkInterface) -> None:
        self._tx_label.setText(
            f"↑ {format_bytes(iface.bytes_sent)}   ↓ {format_bytes(iface.bytes_recv)}"
        )
        if iface.send_rate_bytes > 0 or iface.recv_rate_bytes > 0:
            self._rate_label.setText(
                f"▲ {format_speed(iface.send_rate_bytes)}   ▼ {format_speed(iface.recv_rate_bytes)}"
            )

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(0, 0, -1, -1)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(SURFACE))
        p.drawRoundedRect(rect, 12, 12)
        p.setPen(QPen(QColor(BORDER), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, 12, 12)


class NetworkPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._iface_cards: dict[str, InterfaceCard] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(20)

        title = QLabel("Network")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        layout.addWidget(title)

        self._hostname_label = QLabel("")
        self._hostname_label.setStyleSheet(f"color: {TEXT_SUB}; font-size: 13px;")
        layout.addWidget(self._hostname_label)

        # Live bandwidth chart
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)
        self._chart_tx = LiveChart(ORANGE, "Upload (TX)", "B/s", 100 * 1024 * 1024)
        self._chart_tx.setMinimumHeight(120)
        self._chart_rx = LiveChart(ACCENT, "Download (RX)", "B/s", 100 * 1024 * 1024)
        self._chart_rx.setMinimumHeight(120)
        charts_row.addWidget(self._chart_tx)
        charts_row.addWidget(self._chart_rx)
        layout.addLayout(charts_row)

        ifaces_label = QLabel("Interfaces")
        ifaces_label.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {TEXT};")
        layout.addWidget(ifaces_label)

        self._ifaces_container = QWidget()
        self._ifaces_vlayout = QVBoxLayout(self._ifaces_container)
        self._ifaces_vlayout.setSpacing(10)
        self._ifaces_vlayout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ifaces_container)
        layout.addStretch()

    def update_data(self, info: NetworkInfo) -> None:
        self._hostname_label.setText(f"Hostname: {info.hostname}")

        total_tx = 0.0
        total_rx = 0.0

        current_names = {i.name for i in info.interfaces}
        for name in list(self._iface_cards.keys()):
            if name not in current_names:
                card = self._iface_cards.pop(name)
                card.deleteLater()

        for iface in info.interfaces:
            if iface.name not in self._iface_cards:
                card = InterfaceCard(iface, self._ifaces_container)
                self._ifaces_vlayout.addWidget(card)
                self._iface_cards[iface.name] = card
            else:
                self._iface_cards[iface.name].refresh(iface)
            total_tx += iface.send_rate_bytes
            total_rx += iface.recv_rate_bytes

        self._chart_tx.add_value(total_tx)
        self._chart_rx.add_value(total_rx)
