"""Sensors page — temperatures, fans, battery."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QGridLayout, QSizePolicy, QProgressBar,
)

from src.core.collectors.sensors_collector import SensorsInfo, TempSensor, FanSensor
from src.ui.styles.dark_theme import TEXT, TEXT_SUB, GREEN, YELLOW, RED, ORANGE, ACCENT, SURFACE, BORDER
from src.utils.format import format_temp


def _temp_color(t: float, high: float | None, crit: float | None) -> str:
    if crit and t >= crit * 0.95:
        return RED
    if high and t >= high * 0.85:
        return ORANGE
    if t >= 70:
        return YELLOW
    return GREEN


class TempBar(QWidget):
    """Single temperature sensor row with colored progress bar."""

    def __init__(self, sensor: TempSensor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        # Label
        label = QLabel(f"{sensor.chip} / {sensor.label}" if sensor.label else sensor.chip)
        label.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11px; background: transparent;")
        label.setFixedWidth(180)
        layout.addWidget(label)

        # Bar
        self._bar = QProgressBar()
        self._bar.setRange(0, 110)
        self._bar.setValue(int(sensor.current))
        self._bar.setFixedHeight(8)
        self._bar.setTextVisible(False)
        layout.addWidget(self._bar, 1)

        # Value
        self._val_label = QLabel(format_temp(sensor.current))
        color = _temp_color(sensor.current, sensor.high, sensor.critical)
        self._val_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600; background: transparent;")
        self._val_label.setFixedWidth(70)
        self._val_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._val_label)

        self._update_bar_color(sensor.current, sensor.high, sensor.critical)

    def update_value(self, temp: float, high: float | None, crit: float | None) -> None:
        self._bar.setValue(int(temp))
        color = _temp_color(temp, high, crit)
        self._val_label.setText(format_temp(temp))
        self._val_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600; background: transparent;")
        self._update_bar_color(temp, high, crit)

    def _update_bar_color(self, temp: float, high: float | None, crit: float | None) -> None:
        color = _temp_color(temp, high, crit)
        self._bar.setStyleSheet(
            f"QProgressBar {{ background: #21262d; border: none; border-radius: 4px; }}"
            f"QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}"
        )


class FanRow(QWidget):
    """Single fan sensor row."""

    def __init__(self, sensor: FanSensor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(36)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(12)

        label = QLabel(f"{sensor.chip} / {sensor.label}")
        label.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11px; background: transparent;")
        layout.addWidget(label)
        layout.addStretch()

        self._rpm_l = QLabel(f"{sensor.rpm:,} RPM")
        self._rpm_l.setStyleSheet(f"color: {ACCENT}; font-size: 13px; font-weight: 600; background: transparent;")
        layout.addWidget(self._rpm_l)

    def update_rpm(self, rpm: int) -> None:
        self._rpm_l.setText(f"{rpm:,} RPM")


class SensorsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._temp_bars: list[TempBar] = []
        self._fan_rows: list[FanRow] = []
        self._temp_sensors: list[TempSensor] = []
        self._fan_sensors: list[FanSensor] = []
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

        title = QLabel("Sensors")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        layout.addWidget(title)

        # Temps section
        temp_hdr = QLabel("Temperatures")
        temp_hdr.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {TEXT};")
        layout.addWidget(temp_hdr)

        self._temps_container = QWidget()
        self._temps_vlayout = QVBoxLayout(self._temps_container)
        self._temps_vlayout.setSpacing(4)
        self._temps_vlayout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._temps_container)

        # Fans section
        fan_hdr = QLabel("Fans")
        fan_hdr.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {TEXT};")
        layout.addWidget(fan_hdr)

        self._fans_container = QWidget()
        self._fans_vlayout = QVBoxLayout(self._fans_container)
        self._fans_vlayout.setSpacing(4)
        self._fans_vlayout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._fans_container)

        # Battery section
        self._battery_label = QLabel("Battery")
        self._battery_label.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {TEXT};")
        self._battery_label.setVisible(False)
        layout.addWidget(self._battery_label)

        self._battery_info = QLabel("")
        self._battery_info.setStyleSheet(f"color: {TEXT_SUB}; font-size: 13px;")
        self._battery_info.setVisible(False)
        layout.addWidget(self._battery_info)

        self._no_sensors_label = QLabel(
            "No sensors detected.\nInstall lm_sensors and run 'sudo sensors-detect'."
        )
        self._no_sensors_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_sensors_label.setStyleSheet(f"color: {TEXT_SUB}; font-size: 14px;")
        self._no_sensors_label.setVisible(False)
        layout.addWidget(self._no_sensors_label)
        layout.addStretch()

    def update_data(self, info: SensorsInfo) -> None:
        has_data = bool(info.temperatures or info.fans)
        self._no_sensors_label.setVisible(not has_data)

        # Temperatures
        if len(info.temperatures) != len(self._temp_bars):
            for w in self._temp_bars:
                w.deleteLater()
            self._temp_bars.clear()
            for s in info.temperatures:
                bar = TempBar(s, self._temps_container)
                self._temps_vlayout.addWidget(bar)
                self._temp_bars.append(bar)
        else:
            for bar, s in zip(self._temp_bars, info.temperatures):
                bar.update_value(s.current, s.high, s.critical)

        # Fans
        if len(info.fans) != len(self._fan_rows):
            for w in self._fan_rows:
                w.deleteLater()
            self._fan_rows.clear()
            for s in info.fans:
                row = FanRow(s, self._fans_container)
                self._fans_vlayout.addWidget(row)
                self._fan_rows.append(row)
        else:
            for row, s in zip(self._fan_rows, info.fans):
                row.update_rpm(s.rpm)

        # Battery
        if info.battery:
            self._battery_label.setVisible(True)
            self._battery_info.setVisible(True)
            bat = info.battery
            time_str = ""
            if bat.seconds_left:
                h, m = divmod(int(bat.seconds_left) // 60, 60)
                time_str = f"  ·  {h}h {m}m remaining"
            color = GREEN if bat.percent > 50 else (YELLOW if bat.percent > 20 else RED)
            self._battery_info.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 600;")
            self._battery_info.setText(
                f"{bat.percent:.0f}%  {bat.status}{time_str}"
            )
