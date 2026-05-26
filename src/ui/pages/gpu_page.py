"""GPU information page."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QGridLayout, QFrame,
)

from src.core.collectors.gpu_collector import GPUInfo
from src.ui.styles.dark_theme import TEXT, TEXT_SUB, ACCENT, GREEN, YELLOW, RED, PURPLE
from src.ui.widgets.info_card import InfoCard, KeyValueCard
from src.ui.widgets.live_chart import LiveChart
from src.ui.widgets.gauge_widget import GaugeWidget
from src.utils.format import format_bytes, format_temp


class GPUPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
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

        title = QLabel("GPU")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        layout.addWidget(title)

        # Gauges
        gauges_row = QHBoxLayout()
        gauges_row.setSpacing(16)
        self._gauge_util = GaugeWidget("Utilization", "%", 100.0, GREEN)
        self._gauge_util.setFixedSize(160, 160)
        self._gauge_temp = GaugeWidget("Temperature", "°C", 110.0, RED)
        self._gauge_temp.setFixedSize(160, 160)
        self._gauge_vram = GaugeWidget("VRAM", "%", 100.0, PURPLE)
        self._gauge_vram.setFixedSize(160, 160)
        gauges_row.addWidget(self._gauge_util)
        gauges_row.addWidget(self._gauge_temp)
        gauges_row.addWidget(self._gauge_vram)
        gauges_row.addStretch()
        layout.addLayout(gauges_row)

        # Info cards
        grid = QGridLayout()
        grid.setSpacing(12)
        self._card_name = InfoCard("GPU Name", "—", icon="🖥", accent=ACCENT)
        self._card_vram = InfoCard("VRAM Total", "—", icon="▣", accent=PURPLE)
        self._card_driver = InfoCard("Driver Version", "—", icon="◉", accent=GREEN)
        self._card_temp = InfoCard("Temperature", "—", icon="◈", accent=RED)
        self._card_power = InfoCard("Power Draw", "—", icon="⚡", accent=YELLOW)
        self._card_clock = InfoCard("GPU Clock", "—", icon="◎", accent=ACCENT)

        grid.addWidget(self._card_name, 0, 0, 1, 2)
        grid.addWidget(self._card_vram, 0, 2)
        grid.addWidget(self._card_driver, 0, 3)
        grid.addWidget(self._card_temp, 1, 0)
        grid.addWidget(self._card_power, 1, 1)
        grid.addWidget(self._card_clock, 1, 2)
        layout.addLayout(grid)

        # Live charts
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)
        self._chart_util = LiveChart(GREEN, "GPU Utilization", "%", 100.0)
        self._chart_util.setMinimumHeight(140)
        self._chart_vram = LiveChart(PURPLE, "VRAM Usage", "%", 100.0)
        self._chart_vram.setMinimumHeight(140)
        charts_row.addWidget(self._chart_util)
        charts_row.addWidget(self._chart_vram)
        layout.addLayout(charts_row)

        # Details table
        self._detail_card = KeyValueCard("GPU Details", [
            ("GPU Name", "—"),
            ("Vendor", "—"),
            ("VRAM Total", "—"),
            ("VRAM Used", "—"),
            ("Driver Version", "—"),
            ("GPU Clock", "—"),
            ("Memory Clock", "—"),
            ("PCIe Gen", "—"),
            ("PCIe Width", "—"),
            ("OpenGL Version", "—"),
            ("Power Draw", "—"),
            ("Power Limit", "—"),
        ])
        layout.addWidget(self._detail_card)
        layout.addStretch()

    def update_data(self, info: GPUInfo) -> None:
        self._gauge_util.set_value(info.utilization)
        if info.temperature is not None:
            self._gauge_temp.set_value(info.temperature)
        vram_pct = (info.vram_used_mb / info.vram_total_mb * 100) if info.vram_total_mb else 0
        self._gauge_vram.set_value(vram_pct)

        self._card_name.set_value(info.name)
        self._card_vram.set_value(f"{info.vram_total_mb:.0f} MB")
        self._card_driver.set_value(info.driver_version)
        temp_str = format_temp(info.temperature) if info.temperature is not None else "N/A"
        self._card_temp.set_value(temp_str)
        power_str = f"{info.power_draw_w:.1f} W" if info.power_draw_w is not None else "N/A"
        self._card_power.set_value(power_str)
        clock_str = f"{info.clock_gpu_mhz:.0f} MHz" if info.clock_gpu_mhz else "N/A"
        self._card_clock.set_value(clock_str)

        self._chart_util.add_value(info.utilization)
        self._chart_vram.add_value(vram_pct)

        self._detail_card.update_row("GPU Name", info.name)
        self._detail_card.update_row("Vendor", info.vendor)
        self._detail_card.update_row("VRAM Total", f"{info.vram_total_mb:.0f} MB")
        self._detail_card.update_row("VRAM Used", f"{info.vram_used_mb:.0f} MB")
        self._detail_card.update_row("Driver Version", info.driver_version)
        self._detail_card.update_row("GPU Clock", clock_str)
        mem_clock = f"{info.clock_mem_mhz:.0f} MHz" if info.clock_mem_mhz else "N/A"
        self._detail_card.update_row("Memory Clock", mem_clock)
        self._detail_card.update_row("PCIe Gen", info.pcie_gen)
        self._detail_card.update_row("PCIe Width", info.pcie_width)
        self._detail_card.update_row("OpenGL Version", info.opengl_version)
        self._detail_card.update_row("Power Draw", power_str)
        limit_str = f"{info.power_limit_w:.1f} W" if info.power_limit_w else "N/A"
        self._detail_card.update_row("Power Limit", limit_str)
