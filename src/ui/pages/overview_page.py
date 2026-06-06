"""Overview — shows the key metrics of all subsystems at a glance."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
)

from src.ui.styles.dark_theme import TEXT, ACCENT, GREEN, RED, PURPLE, YELLOW
from src.ui.widgets.info_card import InfoCard
from src.ui.widgets.live_chart import LiveChart
from src.ui.widgets.gauge_widget import GaugeWidget
from src.utils.format import format_bytes, format_uptime


class OverviewPage(QWidget):
    """Dashboard with semicircle gauges, summary cards and a live chart."""

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
        layout.setContentsMargins(32, 24, 32, 28)
        layout.setSpacing(22)

        # ── Title (centered) ─────────────────────────────────────────── #
        title = QLabel("Overview")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {TEXT};")
        layout.addWidget(title)

        # ── Gauge cards ──────────────────────────────────────────────── #
        gauges_row = QHBoxLayout()
        gauges_row.setSpacing(16)

        self._gauge_cpu = GaugeWidget("CPU", "%", 100.0, ACCENT, style="semi", card=True)
        self._gauge_gpu = GaugeWidget("GPU", "%", 100.0, GREEN, style="semi", card=True)
        self._gauge_ram = GaugeWidget("RAM", "%", 100.0, PURPLE, style="semi", card=True)
        self._gauge_temp = GaugeWidget("Temp.", "°C", 105.0, RED, style="semi", card=True)

        for gauge in (self._gauge_cpu, self._gauge_gpu, self._gauge_ram, self._gauge_temp):
            gauge.setMinimumHeight(150)
            gauges_row.addWidget(gauge, 1)
        layout.addLayout(gauges_row)

        # ── Summary cards ────────────────────────────────────────────── #
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self._card_cpu = InfoCard("PROCESSOR", "—", accent=ACCENT, value_color=ACCENT)
        self._card_ram = InfoCard("MEMORY", "—", accent=PURPLE)
        self._card_uptime = InfoCard("UPTIME", "—", accent=YELLOW, value_color=YELLOW)

        for card in (self._card_cpu, self._card_ram, self._card_uptime):
            cards_row.addWidget(card, 1)
        layout.addLayout(cards_row)

        # ── Live chart ───────────────────────────────────────────────── #
        self._chart_cpu = LiveChart(ACCENT, "CPU Usage", "%", 100.0, max_points=60)
        self._chart_cpu.setMinimumHeight(170)
        layout.addWidget(self._chart_cpu)

        layout.addStretch()

    # ── Update methods (called by the main window) ────────────────────── #

    def update_cpu(self, info) -> None:
        self._gauge_cpu.set_value(info.usage_total)
        self._chart_cpu.add_value(info.usage_total)
        self._card_cpu.set_value(info.name)
        if info.temperature is not None:
            self._gauge_temp.set_value(info.temperature)

    def update_gpu(self, info) -> None:
        self._gauge_gpu.set_value(info.utilization)

    def update_ram(self, info) -> None:
        self._gauge_ram.set_value(info.percent_used)
        self._card_ram.set_value(format_bytes(info.total_bytes))

    def update_network(self, info) -> None:
        # Not shown in the compact overview layout.
        pass

    def update_system(self, info) -> None:
        self._card_uptime.set_value(format_uptime(info.uptime_seconds))
