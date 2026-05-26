"""Storage / Disk information page."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QGridLayout, QFrame, QProgressBar, QSizePolicy,
)

from src.core.collectors.storage_collector import StorageInfo, DiskDevice, Partition
from src.ui.styles.dark_theme import (
    TEXT, TEXT_SUB, ACCENT, GREEN, YELLOW, RED, PURPLE, SURFACE, BORDER, SURFACE_2
)
from src.ui.widgets.info_card import InfoCard, KeyValueCard
from src.ui.widgets.live_chart import LiveChart
from src.utils.format import format_bytes, format_speed


class DiskCard(QWidget):
    """Card displaying info for a single disk device."""

    def __init__(self, device: DiskDevice, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from PyQt6.QtGui import QPainter, QPen
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        type_chip = QLabel(device.disk_type)
        type_color = {"NVMe": "#58a6ff", "SSD": "#3fb950", "HDD": "#d29922"}.get(
            device.disk_type, "#8b949e"
        )
        type_chip.setStyleSheet(
            f"background: {type_color}22; color: {type_color}; border: 1px solid {type_color}55;"
            "border-radius: 8px; padding: 1px 8px; font-size: 10px; font-weight: 600;"
        )
        type_chip.setFixedHeight(20)

        name_l = QLabel(f"<b>{device.model}</b>  <span style='color:{TEXT_SUB}; font-size:11px'>{device.name}</span>")
        name_l.setStyleSheet("background: transparent;")
        hdr.addWidget(name_l)
        hdr.addStretch()
        hdr.addWidget(type_chip)
        layout.addLayout(hdr)

        # Size / SMART
        info_row = QHBoxLayout()
        size_l = QLabel(format_bytes(device.size_bytes))
        size_l.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: 700; background: transparent;")
        info_row.addWidget(size_l)

        if device.smart_status:
            smart_color = GREEN if device.smart_status == "PASSED" else RED
            smart_l = QLabel(f"SMART: {device.smart_status}")
            smart_l.setStyleSheet(
                f"color: {smart_color}; font-size: 11px; background: transparent;"
            )
            info_row.addWidget(smart_l)

        if device.temperature is not None:
            temp_l = QLabel(f"  {device.temperature:.0f}°C")
            temp_l.setStyleSheet(f"color: {RED}; font-size: 11px; background: transparent;")
            info_row.addWidget(temp_l)

        info_row.addStretch()

        # Speed
        self._speed_label = QLabel("")
        self._speed_label.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11px; background: transparent;")
        info_row.addWidget(self._speed_label)
        layout.addLayout(info_row)

    def update_speeds(self, read: float, write: float) -> None:
        if read > 0 or write > 0:
            self._speed_label.setText(
                f"▲ {format_speed(write)}  ▼ {format_speed(read)}"
            )

    def paintEvent(self, event) -> None:
        from PyQt6.QtGui import QPainter, QPen
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(0, 0, -1, -1)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(SURFACE))
        p.drawRoundedRect(rect, 12, 12)
        p.setPen(QPen(QColor(BORDER), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, 12, 12)


class PartitionBar(QWidget):
    """Visual bar showing partition usage."""

    def __init__(self, part: Partition, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(4)

        hdr = QHBoxLayout()
        mp_l = QLabel(f"<b>{part.mountpoint}</b>  <span style='color:{TEXT_SUB};font-size:11px'>({part.device}  {part.fstype})</span>")
        mp_l.setStyleSheet("background: transparent;")
        hdr.addWidget(mp_l)
        hdr.addStretch()
        used_l = QLabel(f"{format_bytes(part.used_bytes)} / {format_bytes(part.total_bytes)}")
        used_l.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11px; background: transparent;")
        hdr.addWidget(used_l)
        layout.addLayout(hdr)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(part.percent_used))
        bar.setFixedHeight(8)
        bar.setTextVisible(False)
        color = GREEN if part.percent_used < 70 else (YELLOW if part.percent_used < 90 else RED)
        bar.setStyleSheet(
            f"QProgressBar {{ background: #21262d; border: none; border-radius: 4px; }}"
            f"QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}"
        )
        layout.addWidget(bar)

        free_l = QLabel(f"Free: {format_bytes(part.free_bytes)}  ({100 - part.percent_used:.1f}%)")
        free_l.setStyleSheet(f"color: {TEXT_SUB}; font-size: 10px; background: transparent;")
        layout.addWidget(free_l)

    def paintEvent(self, event) -> None:
        from PyQt6.QtGui import QPainter, QPen
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(0, 0, -1, -1)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(SURFACE))
        p.drawRoundedRect(rect, 10, 10)
        p.setPen(QPen(QColor(BORDER), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, 10, 10)


class StoragePage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._disk_cards: dict[str, DiskCard] = {}
        self._part_bars: list[PartitionBar] = []
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
        self._layout = QVBoxLayout(content)
        self._layout.setContentsMargins(24, 20, 24, 24)
        self._layout.setSpacing(20)

        title = QLabel("Storage")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        self._layout.addWidget(title)

        # Live speed chart
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)
        self._chart_read = LiveChart(GREEN, "Read Speed", "/s", 500 * 1024 * 1024, max_points=60)
        self._chart_read.setMinimumHeight(120)
        self._chart_write = LiveChart(YELLOW, "Write Speed", "/s", 500 * 1024 * 1024, max_points=60)
        self._chart_write.setMinimumHeight(120)
        charts_row.addWidget(self._chart_read)
        charts_row.addWidget(self._chart_write)
        self._layout.addLayout(charts_row)

        self._disks_label = QLabel("Devices")
        self._disks_label.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {TEXT};")
        self._layout.addWidget(self._disks_label)

        self._disks_container = QWidget()
        self._disks_vlayout = QVBoxLayout(self._disks_container)
        self._disks_vlayout.setSpacing(10)
        self._disks_vlayout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._disks_container)

        self._parts_label = QLabel("Partitions")
        self._parts_label.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {TEXT};")
        self._layout.addWidget(self._parts_label)

        self._parts_container = QWidget()
        self._parts_vlayout = QVBoxLayout(self._parts_container)
        self._parts_vlayout.setSpacing(8)
        self._parts_vlayout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._parts_container)
        self._layout.addStretch()

    def update_data(self, info: StorageInfo) -> None:
        # Disk devices
        current_names = {d.name for d in info.devices}
        for name in list(self._disk_cards.keys()):
            if name not in current_names:
                card = self._disk_cards.pop(name)
                card.deleteLater()

        total_read = 0.0
        total_write = 0.0
        for device in info.devices:
            if device.name not in self._disk_cards:
                card = DiskCard(device, self._disks_container)
                self._disks_vlayout.addWidget(card)
                self._disk_cards[device.name] = card
            else:
                self._disk_cards[device.name].update_speeds(
                    device.read_speed_bytes, device.write_speed_bytes
                )
            total_read += device.read_speed_bytes
            total_write += device.write_speed_bytes

        self._chart_read.add_value(total_read)
        self._chart_write.add_value(total_write)

        # Partitions — rebuild
        for w in self._part_bars:
            w.deleteLater()
        self._part_bars.clear()
        for part in info.partitions:
            bar = PartitionBar(part, self._parts_container)
            self._parts_vlayout.addWidget(bar)
            self._part_bars.append(bar)
