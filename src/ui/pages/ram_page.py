"""RAM / Memory information page."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QGridLayout, QFrame,
)

from src.core.collectors.ram_collector import RAMInfo
from src.ui.styles.dark_theme import TEXT, ACCENT, GREEN, YELLOW, RED, PURPLE, ORANGE
from src.ui.widgets.info_card import InfoCard, KeyValueCard
from src.ui.widgets.live_chart import LiveChart
from src.ui.widgets.gauge_widget import GaugeWidget
from src.utils.format import format_bytes, format_percent


class RAMPage(QWidget):
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

        title = QLabel("RAM")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        layout.addWidget(title)

        # Gauges
        gauges_row = QHBoxLayout()
        gauges_row.setSpacing(16)
        self._gauge_ram = GaugeWidget("RAM Usage", "%", 100.0, PURPLE)
        self._gauge_ram.setFixedSize(160, 160)
        self._gauge_swap = GaugeWidget("Swap Usage", "%", 100.0, ORANGE)
        self._gauge_swap.setFixedSize(160, 160)
        gauges_row.addWidget(self._gauge_ram)
        gauges_row.addWidget(self._gauge_swap)
        gauges_row.addStretch()
        layout.addLayout(gauges_row)

        # Info cards
        grid = QGridLayout()
        grid.setSpacing(12)
        self._card_total = InfoCard("Total RAM", "—", icon="▣", accent=PURPLE)
        self._card_used = InfoCard("Used RAM", "—", icon="▪", accent=RED)
        self._card_avail = InfoCard("Available", "—", icon="▫", accent=GREEN)
        self._card_cached = InfoCard("Cached", "—", icon="◈", accent=ACCENT)
        self._card_swap_total = InfoCard("Swap Total", "—", icon="⊟", accent=ORANGE)
        self._card_swap_used = InfoCard("Swap Used", "—", icon="⊠", accent=YELLOW)

        grid.addWidget(self._card_total, 0, 0)
        grid.addWidget(self._card_used, 0, 1)
        grid.addWidget(self._card_avail, 0, 2)
        grid.addWidget(self._card_cached, 0, 3)
        grid.addWidget(self._card_swap_total, 1, 0)
        grid.addWidget(self._card_swap_used, 1, 1)
        layout.addLayout(grid)

        # Live chart
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)
        self._chart_ram = LiveChart(PURPLE, "RAM Usage", "%", 100.0)
        self._chart_ram.setMinimumHeight(140)
        self._chart_swap = LiveChart(ORANGE, "Swap Usage", "%", 100.0)
        self._chart_swap.setMinimumHeight(140)
        charts_row.addWidget(self._chart_ram, 2)
        charts_row.addWidget(self._chart_swap, 1)
        layout.addLayout(charts_row)

        # Details
        self._detail_card = KeyValueCard("Memory Details", [
            ("Total RAM", "—"),
            ("Used RAM", "—"),
            ("Available RAM", "—"),
            ("Cached", "—"),
            ("Buffers", "—"),
            ("Shared", "—"),
            ("Usage Percent", "—"),
            ("Swap Total", "—"),
            ("Swap Used", "—"),
            ("Swap Percent", "—"),
            ("RAM Type", "—"),
            ("Speed", "—"),
            ("Slots Used", "—"),
        ])
        layout.addWidget(self._detail_card)
        layout.addStretch()

    def update_data(self, info: RAMInfo) -> None:
        self._gauge_ram.set_value(info.percent_used)
        self._gauge_swap.set_value(info.swap_percent)

        self._card_total.set_value(format_bytes(info.total_bytes))
        self._card_used.set_value(format_bytes(info.used_bytes))
        self._card_avail.set_value(format_bytes(info.available_bytes))
        self._card_cached.set_value(format_bytes(info.cached_bytes))
        self._card_swap_total.set_value(format_bytes(info.swap_total_bytes))
        self._card_swap_used.set_value(format_bytes(info.swap_used_bytes))

        self._chart_ram.add_value(info.percent_used)
        self._chart_swap.add_value(info.swap_percent)

        self._detail_card.update_row("Total RAM", format_bytes(info.total_bytes))
        self._detail_card.update_row("Used RAM", format_bytes(info.used_bytes))
        self._detail_card.update_row("Available RAM", format_bytes(info.available_bytes))
        self._detail_card.update_row("Cached", format_bytes(info.cached_bytes))
        self._detail_card.update_row("Buffers", format_bytes(info.buffers_bytes))
        self._detail_card.update_row("Shared", format_bytes(info.shared_bytes))
        self._detail_card.update_row("Usage Percent", format_percent(info.percent_used))
        self._detail_card.update_row("Swap Total", format_bytes(info.swap_total_bytes))
        self._detail_card.update_row("Swap Used", format_bytes(info.swap_used_bytes))
        self._detail_card.update_row("Swap Percent", format_percent(info.swap_percent))
        self._detail_card.update_row("RAM Type", info.mem_type)
        self._detail_card.update_row("Speed", info.speed_mt)
        slots = f"{info.slots_used}/{info.slots_total}" if info.slots_total else "N/A"
        self._detail_card.update_row("Slots Used", slots)
