"""System / OS / Mainboard information page."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QGridLayout,
)

from src.core.collectors.system_collector import SystemInfo
from src.ui.styles.dark_theme import TEXT, TEXT_SUB, ACCENT, GREEN, YELLOW, PURPLE, ORANGE
from src.ui.widgets.info_card import InfoCard, KeyValueCard
from src.utils.format import format_uptime


class SystemPage(QWidget):
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

        title = QLabel("System")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        layout.addWidget(title)

        # Summary cards
        grid = QGridLayout()
        grid.setSpacing(12)

        self._card_os = InfoCard("Operating System", "—", icon="🐧", accent=ACCENT)
        self._card_kernel = InfoCard("Kernel", "—", icon="◈", accent=GREEN)
        self._card_uptime = InfoCard("Uptime", "—", icon="⏱", accent=YELLOW)
        self._card_de = InfoCard("Desktop", "—", icon="◉", accent=PURPLE)
        self._card_packages = InfoCard("Packages", "—", icon="◆", accent=ORANGE)
        self._card_procs = InfoCard("Processes", "—", icon="▣", accent=ACCENT)

        grid.addWidget(self._card_os, 0, 0, 1, 2)
        grid.addWidget(self._card_kernel, 0, 2)
        grid.addWidget(self._card_uptime, 0, 3)
        grid.addWidget(self._card_de, 1, 0)
        grid.addWidget(self._card_packages, 1, 1)
        grid.addWidget(self._card_procs, 1, 2)
        layout.addLayout(grid)

        # System details
        self._sys_card = KeyValueCard("System Information", [
            ("Hostname", "—"),
            ("Username", "—"),
            ("OS", "—"),
            ("OS Version", "—"),
            ("Kernel", "—"),
            ("Architecture", "—"),
            ("Uptime", "—"),
            ("Shell", "—"),
            ("Desktop Environment", "—"),
            ("Window Manager", "—"),
            ("Processes", "—"),
            ("Python Version", "—"),
        ])
        layout.addWidget(self._sys_card)

        # Mainboard details
        self._board_card = KeyValueCard("Mainboard / BIOS", [
            ("Board Vendor", "—"),
            ("Board Name", "—"),
            ("Board Version", "—"),
            ("BIOS Vendor", "—"),
            ("BIOS Version", "—"),
            ("BIOS Date", "—"),
            ("Chassis Type", "—"),
        ])
        layout.addWidget(self._board_card)

        # Packages
        self._pkg_card = KeyValueCard("Package Managers", [
            ("pacman (Arch)", "—"),
            ("Flatpak", "—"),
        ])
        layout.addWidget(self._pkg_card)
        layout.addStretch()

    def update_data(self, info: SystemInfo) -> None:
        # Summary cards
        self._card_os.set_value(info.os_name)
        self._card_kernel.set_value(info.kernel)
        self._card_uptime.set_value(format_uptime(info.uptime_seconds))
        self._card_de.set_value(info.desktop_environment)
        pkgs = info.pacman_packages + info.flatpak_packages
        self._card_packages.set_value(str(pkgs) if pkgs else "N/A")
        self._card_procs.set_value(str(info.process_count))

        # System info
        self._sys_card.update_row("Hostname", info.hostname)
        self._sys_card.update_row("Username", info.username)
        self._sys_card.update_row("OS", info.os_name)
        self._sys_card.update_row("OS Version", info.os_version)
        self._sys_card.update_row("Kernel", info.kernel)
        self._sys_card.update_row("Architecture", info.architecture)
        self._sys_card.update_row("Uptime", format_uptime(info.uptime_seconds))
        self._sys_card.update_row("Shell", info.shell)
        self._sys_card.update_row("Desktop Environment", info.desktop_environment)
        self._sys_card.update_row("Window Manager", info.window_manager)
        self._sys_card.update_row("Processes", str(info.process_count))
        self._sys_card.update_row("Python Version", info.python_version)

        # Board
        self._board_card.update_row("Board Vendor", info.board_vendor)
        self._board_card.update_row("Board Name", info.board_name)
        self._board_card.update_row("Board Version", info.board_version)
        self._board_card.update_row("BIOS Vendor", info.bios_vendor)
        self._board_card.update_row("BIOS Version", info.bios_version)
        self._board_card.update_row("BIOS Date", info.bios_date)
        self._board_card.update_row("Chassis Type", info.chassis_type)

        # Packages
        self._pkg_card.update_row("pacman (Arch)", str(info.pacman_packages) if info.pacman_packages else "N/A")
        self._pkg_card.update_row("Flatpak", str(info.flatpak_packages) if info.flatpak_packages else "N/A")
