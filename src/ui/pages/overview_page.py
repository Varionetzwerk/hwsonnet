"""Overview dashboard — shows key metrics from all subsystems at a glance."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QGridLayout, QSizePolicy,
)

from src.ui.styles.dark_theme import (
    TEXT, TEXT_SUB, ACCENT, GREEN, YELLOW, RED, PURPLE, ORANGE, SURFACE, BORDER
)
from src.ui.widgets.info_card import InfoCard
from src.ui.widgets.live_chart import LiveChart
from src.ui.widgets.gauge_widget import GaugeWidget
from src.utils.format import format_bytes, format_freq_mhz, format_temp, format_uptime, format_speed


class OverviewPage(QWidget):
    """Dashboard with live gauges and mini-charts for all major subsystems."""

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

        # ── Page header ──────────────────────────────────────────────── #
        hdr = QHBoxLayout()
        title = QLabel("Overview")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        hdr.addWidget(title)
        hdr.addStretch()
        self._os_badge = QLabel("")
        self._os_badge.setStyleSheet(
            f"color: {TEXT_SUB}; font-size: 12px;"
        )
        hdr.addWidget(self._os_badge)
        layout.addLayout(hdr)

        # ── Gauges row ───────────────────────────────────────────────── #
        gauges_row = QHBoxLayout()
        gauges_row.setSpacing(16)

        self._gauge_cpu = GaugeWidget("CPU", "%", 100.0, ACCENT)
        self._gauge_cpu.setFixedSize(150, 150)
        gauges_row.addWidget(self._gauge_cpu)

        self._gauge_gpu = GaugeWidget("GPU", "%", 100.0, GREEN)
        self._gauge_gpu.setFixedSize(150, 150)
        gauges_row.addWidget(self._gauge_gpu)

        self._gauge_ram = GaugeWidget("RAM", "%", 100.0, PURPLE)
        self._gauge_ram.setFixedSize(150, 150)
        gauges_row.addWidget(self._gauge_ram)

        self._gauge_cpu_temp = GaugeWidget("CPU Temp", "°C", 105.0, RED)
        self._gauge_cpu_temp.setFixedSize(150, 150)
        gauges_row.addWidget(self._gauge_cpu_temp)

        gauges_row.addStretch()
        layout.addLayout(gauges_row)

        # ── Info cards ───────────────────────────────────────────────── #
        cards = QGridLayout()
        cards.setSpacing(12)

        self._card_cpu_name = InfoCard("CPU", "—", accent=ACCENT)
        self._card_gpu_name = InfoCard("GPU", "—", accent=GREEN)
        self._card_ram_total = InfoCard("Total RAM", "—", accent=PURPLE)
        self._card_cpu_freq = InfoCard("CPU Frequency", "—", accent=YELLOW)
        self._card_uptime = InfoCard("Uptime", "—", accent=ORANGE)
        self._card_os = InfoCard("OS", "—", accent=ACCENT)
        self._card_net_rx = InfoCard("Net Download", "—", accent=ACCENT)
        self._card_net_tx = InfoCard("Net Upload", "—", accent=ORANGE)

        cards.addWidget(self._card_cpu_name, 0, 0, 1, 2)
        cards.addWidget(self._card_gpu_name, 0, 2, 1, 2)
        cards.addWidget(self._card_ram_total, 1, 0)
        cards.addWidget(self._card_cpu_freq, 1, 1)
        cards.addWidget(self._card_uptime, 1, 2)
        cards.addWidget(self._card_os, 1, 3)
        cards.addWidget(self._card_net_rx, 2, 0)
        cards.addWidget(self._card_net_tx, 2, 1)
        layout.addLayout(cards)

        # ── Live mini-charts grid ─────────────────────────────────────── #
        charts_grid = QGridLayout()
        charts_grid.setSpacing(12)

        self._chart_cpu = LiveChart(ACCENT, "CPU Usage", "%", 100.0, max_points=60)
        self._chart_cpu.setMinimumHeight(130)

        self._chart_ram = LiveChart(PURPLE, "RAM Usage", "%", 100.0, max_points=60)
        self._chart_ram.setMinimumHeight(130)

        self._chart_gpu = LiveChart(GREEN, "GPU Usage", "%", 100.0, max_points=60)
        self._chart_gpu.setMinimumHeight(130)

        self._chart_net = LiveChart(ORANGE, "Network RX", "B/s", 100 * 1024 * 1024, max_points=60)
        self._chart_net.setMinimumHeight(130)

        charts_grid.addWidget(self._chart_cpu, 0, 0)
        charts_grid.addWidget(self._chart_ram, 0, 1)
        charts_grid.addWidget(self._chart_gpu, 1, 0)
        charts_grid.addWidget(self._chart_net, 1, 1)
        layout.addLayout(charts_grid)
        layout.addStretch()

    # ── Update methods called from main window ────────────────────────── #

    def update_cpu(self, info) -> None:
        self._gauge_cpu.set_value(info.usage_total)
        self._chart_cpu.add_value(info.usage_total)
        self._card_cpu_name.set_value(info.name)
        self._card_cpu_freq.set_value(format_freq_mhz(info.current_frequency_mhz))
        if info.temperature is not None:
            self._gauge_cpu_temp.set_value(info.temperature)

    def update_gpu(self, info) -> None:
        self._gauge_gpu.set_value(info.utilization)
        self._chart_gpu.add_value(info.utilization)
        self._card_gpu_name.set_value(info.name)

    def update_ram(self, info) -> None:
        self._gauge_ram.set_value(info.percent_used)
        self._chart_ram.add_value(info.percent_used)
        self._card_ram_total.set_value(format_bytes(info.total_bytes))

    def update_network(self, info) -> None:
        total_rx = sum(i.recv_rate_bytes for i in info.interfaces)
        total_tx = sum(i.send_rate_bytes for i in info.interfaces)
        self._chart_net.add_value(total_rx)
        self._card_net_rx.set_value(format_speed(total_rx))
        self._card_net_tx.set_value(format_speed(total_tx))

    def update_system(self, info) -> None:
        self._card_uptime.set_value(format_uptime(info.uptime_seconds))
        self._card_os.set_value(info.os_name)
        self._os_badge.setText(f"{info.hostname}  ·  {info.kernel}")
