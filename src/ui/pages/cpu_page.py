"""CPU information page."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QGridLayout, QSizePolicy, QFrame,
)

from src.core.collectors.cpu_collector import CPUInfo
from src.ui.styles.dark_theme import (
    TEXT, TEXT_SUB, ACCENT, GREEN, YELLOW, RED, PURPLE, SURFACE, BORDER
)
from src.ui.widgets.info_card import InfoCard, KeyValueCard
from src.ui.widgets.live_chart import LiveChart, MultiLineChart
from src.ui.widgets.gauge_widget import GaugeWidget, MiniGauge
from src.utils.format import format_freq_mhz, format_temp, format_percent


class CPUPage(QWidget):
    """Full CPU information and live monitoring page."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._core_gauges: list[MiniGauge] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(20)

        # ── Page title ───────────────────────────────────────────────── #
        title = QLabel("CPU")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        layout.addWidget(title)

        # ── Top row: gauges + static info ────────────────────────────── #
        top = QHBoxLayout()
        top.setSpacing(16)

        self._gauge_usage = GaugeWidget("Usage", "%", 100.0, ACCENT)
        self._gauge_usage.setFixedSize(160, 160)
        top.addWidget(self._gauge_usage)

        self._gauge_temp = GaugeWidget("Temp", "°C", 105.0, RED)
        self._gauge_temp.setFixedSize(160, 160)
        top.addWidget(self._gauge_temp)

        self._gauge_freq = GaugeWidget("Freq", "GHz", 5.0, GREEN)
        self._gauge_freq.setFixedSize(160, 160)
        top.addWidget(self._gauge_freq)

        top.addStretch()
        layout.addLayout(top)

        # ── Info cards row ───────────────────────────────────────────── #
        cards_grid = QGridLayout()
        cards_grid.setSpacing(12)

        self._card_name = InfoCard("Processor", "—", icon="⬛", accent=ACCENT)
        self._card_cores = InfoCard("Cores / Threads", "—", icon="⬡", accent=GREEN)
        self._card_freq = InfoCard("Current Freq.", "—", icon="◉", accent=YELLOW)
        self._card_temp = InfoCard("Temperature", "—", icon="◈", accent=RED)
        self._card_arch = InfoCard("Architecture", "—", icon="◆", accent=PURPLE)
        self._card_cache = InfoCard("L3 Cache", "—", icon="▣", accent="#39d353")

        cards_grid.addWidget(self._card_name, 0, 0, 1, 2)
        cards_grid.addWidget(self._card_cores, 0, 2)
        cards_grid.addWidget(self._card_freq, 0, 3)
        cards_grid.addWidget(self._card_temp, 1, 0)
        cards_grid.addWidget(self._card_arch, 1, 1)
        cards_grid.addWidget(self._card_cache, 1, 2)
        layout.addLayout(cards_grid)

        # ── Live usage chart ─────────────────────────────────────────── #
        self._chart_usage = LiveChart(ACCENT, "CPU Total Usage", "%", 100.0)
        self._chart_usage.setMinimumHeight(150)
        layout.addWidget(self._chart_usage)

        # ── Per-core bars ────────────────────────────────────────────── #
        cores_label = QLabel("Per-Core Usage")
        cores_label.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {TEXT};")
        layout.addWidget(cores_label)

        self._cores_container = QWidget()
        self._cores_layout = QGridLayout(self._cores_container)
        self._cores_layout.setSpacing(8)
        layout.addWidget(self._cores_container)

        # ── Detailed info table ──────────────────────────────────────── #
        self._detail_card = KeyValueCard("CPU Details", [
            ("Model Name", "—"),
            ("Vendor", "—"),
            ("Architecture", "—"),
            ("Physical Cores", "—"),
            ("Logical CPUs", "—"),
            ("Base Frequency", "—"),
            ("Max Frequency", "—"),
            ("L1d Cache", "—"),
            ("L1i Cache", "—"),
            ("L2 Cache", "—"),
            ("L3 Cache", "—"),
            ("Stepping", "—"),
            ("Virtualization", "—"),
            ("NUMA Nodes", "—"),
        ])
        layout.addWidget(self._detail_card)
        layout.addStretch()

    def update_data(self, info: CPUInfo) -> None:
        # Gauges
        self._gauge_usage.set_value(info.usage_total)
        if info.temperature is not None:
            self._gauge_temp.set_value(info.temperature)
        if info.current_frequency_mhz:
            ghz = info.current_frequency_mhz / 1000
            self._gauge_freq.set_value(ghz)

        # Cards
        self._card_name.set_value(info.name)
        self._card_cores.set_value(f"{info.cores_physical}C / {info.cores_logical}T")
        self._card_freq.set_value(format_freq_mhz(info.current_frequency_mhz))
        temp_str = format_temp(info.temperature) if info.temperature is not None else "N/A"
        self._card_temp.set_value(temp_str)
        self._card_arch.set_value(info.architecture)
        self._card_cache.set_value(info.cache_l3)

        # Chart
        self._chart_usage.add_value(info.usage_total)

        # Per-core bars
        if info.usage_per_core:
            self._update_core_bars(info.usage_per_core)

        # Details
        self._detail_card.update_row("Model Name", info.name)
        self._detail_card.update_row("Vendor", info.vendor)
        self._detail_card.update_row("Architecture", info.architecture)
        self._detail_card.update_row("Physical Cores", str(info.cores_physical))
        self._detail_card.update_row("Logical CPUs", str(info.cores_logical))
        self._detail_card.update_row("Base Frequency", format_freq_mhz(info.base_frequency_mhz))
        self._detail_card.update_row("Max Frequency", format_freq_mhz(info.max_frequency_mhz))
        self._detail_card.update_row("L1d Cache", info.cache_l1d)
        self._detail_card.update_row("L1i Cache", info.cache_l1i)
        self._detail_card.update_row("L2 Cache", info.cache_l2)
        self._detail_card.update_row("L3 Cache", info.cache_l3)
        self._detail_card.update_row("Stepping", info.stepping)
        self._detail_card.update_row("Virtualization", info.virtualization)
        self._detail_card.update_row("NUMA Nodes", str(info.numa_nodes))

    def _update_core_bars(self, usages: list[float]) -> None:
        n = len(usages)
        if len(self._core_gauges) != n:
            # Rebuild core bars
            for i in reversed(range(self._cores_layout.count())):
                w = self._cores_layout.itemAt(i).widget()
                if w:
                    w.deleteLater()
            self._core_gauges.clear()
            cols = 2
            for i, usage in enumerate(usages):
                bar = MiniGauge(f"Core {i}", ACCENT)
                bar.set_value(usage)
                self._cores_layout.addWidget(bar, i // cols, i % cols)
                self._core_gauges.append(bar)
        else:
            for bar, usage in zip(self._core_gauges, usages):
                bar.set_value(usage)
                # Dynamic color
                from src.ui.styles.dark_theme import GREEN, YELLOW, RED
                if usage < 50:
                    bar.set_color(GREEN)
                elif usage < 80:
                    bar.set_color(YELLOW)
                else:
                    bar.set_color(RED)
