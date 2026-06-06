"""Main application window — assembles sidebar, pages and workers."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QStatusBar, QLabel, QFileDialog,
    QMessageBox, QPushButton, QMenuBar,
)

from src.core.collectors.cpu_collector import CPUCollector
from src.core.collectors.gpu_collector import GPUCollector
from src.core.collectors.ram_collector import RAMCollector
from src.core.collectors.storage_collector import StorageCollector
from src.core.collectors.network_collector import NetworkCollector
from src.core.collectors.sensors_collector import SensorsCollector
from src.core.collectors.system_collector import SystemCollector
from src.core.workers import StaticWorker, AllDataWorker
from src.ui.sidebar import Sidebar
from src.ui.pages.overview_page import OverviewPage
from src.ui.pages.cpu_page import CPUPage
from src.ui.pages.gpu_page import GPUPage
from src.ui.pages.ram_page import RAMPage
from src.ui.pages.storage_page import StoragePage
from src.ui.pages.network_page import NetworkPage
from src.ui.pages.sensors_page import SensorsPage
from src.ui.pages.system_page import SystemPage
from src.ui.styles.dark_theme import BG, SURFACE, BORDER, TEXT_SUB, ACCENT
from src.utils.export import export_json, export_txt, export_pdf
from src.utils.logger import logger


class _ToolbarButton(QPushButton):
    """Small accent-bordered button for the toolbar strip."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SUB};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 3px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: white;
                border-color: {ACCENT};
                background: {ACCENT}22;
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class _WindowButton(QPushButton):
    """Minimize / maximize / close button for the custom title bar."""

    def __init__(self, glyph: str, danger: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(glyph, parent)
        self.setFixedSize(44, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        hover_bg = "#e81123" if danger else SURFACE
        hover_fg = "white"
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SUB};
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                color: {hover_fg};
            }}
        """)


class _TitleBar(QWidget):
    """Custom frameless-window title bar: menu, title, window controls."""

    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self._win = window
        self.setFixedHeight(40)
        self.setStyleSheet(
            f"background: {SURFACE}; border-bottom: 1px solid {BORDER};"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 8, 0)
        lay.setSpacing(8)

        self.menubar = QMenuBar()
        self.menubar.setStyleSheet(
            f"QMenuBar {{ background: transparent; border: none; color: {TEXT_SUB}; }}"
            f"QMenuBar::item {{ padding: 4px 10px; border-radius: 4px; }}"
            f"QMenuBar::item:selected {{ background: {ACCENT}33; color: white; }}"
        )
        lay.addWidget(self.menubar)

        lay.addStretch()
        title = QLabel("HWSonnet — System Information")
        title.setStyleSheet(
            f"color: {TEXT_SUB}; font-size: 12px; font-weight: 600; background: transparent;"
        )
        lay.addWidget(title)
        lay.addStretch()

        self._btn_min = _WindowButton("–")
        self._btn_max = _WindowButton("☐")
        self._btn_close = _WindowButton("✕", danger=True)
        self._btn_min.clicked.connect(window.showMinimized)
        self._btn_max.clicked.connect(self.toggle_max_restore)
        self._btn_close.clicked.connect(window.close)
        for btn in (self._btn_min, self._btn_max, self._btn_close):
            lay.addWidget(btn)

    def toggle_max_restore(self) -> None:
        if self._win.isMaximized():
            self._win.showNormal()
            self._btn_max.setText("☐")
        else:
            self._win.showMaximized()
            self._btn_max.setText("❐")

    # ── Drag to move (uses compositor — works on Wayland & X11) ────────── #

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self._win.windowHandle()
            if handle is not None:
                handle.startSystemMove()

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_max_restore()


class MainWindow(QMainWindow):
    """HWSonnet main application window."""

    _PAGE_LABELS: dict[str, str] = {
        "overview": "Overview",
        "cpu": "CPU",
        "gpu": "GPU",
        "ram": "RAM",
        "storage": "Storage",
        "network": "Network",
        "sensors": "Sensors",
        "system": "System",
    }

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("HWSonnet — System Information")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)

        self._collectors = {
            "cpu": CPUCollector(),
            "gpu": GPUCollector(),
            "ram": RAMCollector(),
            "storage": StorageCollector(),
            "network": NetworkCollector(),
            "sensors": SensorsCollector(),
            "system": SystemCollector(),
        }
        self._data: dict[str, Any] = {}
        self._static_workers: list[StaticWorker] = []
        self._dynamic_worker: AllDataWorker | None = None
        self._pending_static = 0

        self._build_ui()
        self._build_menu()
        self._start_static_collection()

    # ── UI ────────────────────────────────────────────────────────────── #

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Custom title bar (frameless window chrome)
        self._titlebar = _TitleBar(self)
        outer.addWidget(self._titlebar)

        body = QWidget()
        root = QHBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        outer.addWidget(body, 1)

        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._switch_page)
        root.addWidget(self._sidebar)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        # Toolbar strip
        toolbar = QWidget()
        toolbar.setFixedHeight(48)
        toolbar.setStyleSheet(
            f"background: {SURFACE}; border-bottom: 1px solid {BORDER};"
        )
        tbar = QHBoxLayout(toolbar)
        tbar.setContentsMargins(16, 8, 16, 8)
        tbar.setSpacing(10)

        self._page_title_label = QLabel("Overview")
        self._page_title_label.setStyleSheet(
            f"font-size: 15px; font-weight: 600; color: {TEXT_SUB}; background: transparent;"
        )
        tbar.addWidget(self._page_title_label)
        tbar.addStretch()

        self._status_indicator = QLabel("⟳ Loading…")
        self._status_indicator.setStyleSheet(
            f"color: {ACCENT}; font-size: 12px; background: transparent;"
        )
        tbar.addWidget(self._status_indicator)

        for label, fmt in (("JSON", "json"), ("TXT", "txt"), ("PDF", "pdf")):
            btn = _ToolbarButton(f"Export {label}")
            btn.clicked.connect(lambda checked, f=fmt: self._export(f))
            tbar.addWidget(btn)

        right.addWidget(toolbar)

        # Page stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {BG};")

        self._pages: dict[str, QWidget] = {
            "overview": OverviewPage(),
            "cpu": CPUPage(),
            "gpu": GPUPage(),
            "ram": RAMPage(),
            "storage": StoragePage(),
            "network": NetworkPage(),
            "sensors": SensorsPage(),
            "system": SystemPage(),
        }
        for page in self._pages.values():
            self._stack.addWidget(page)

        right.addWidget(self._stack, 1)
        root.addLayout(right, 1)

        # Status bar
        sb = QStatusBar()
        sb.setStyleSheet(f"background: {SURFACE}; color: {TEXT_SUB}; font-size: 11px;")
        sb.setSizeGripEnabled(True)  # allows resizing the frameless window
        self.setStatusBar(sb)
        sb.addWidget(QLabel("HWSonnet v1.0  ·  optimized for Arch Linux"))
        self._update_time_label = QLabel("")
        sb.addPermanentWidget(self._update_time_label)

    def _build_menu(self) -> None:
        mb = self._titlebar.menubar

        file_menu = mb.addMenu("&File")
        for label, shortcut, fmt in (
            ("Export as &JSON…", "Ctrl+S", "json"),
            ("Export as &TXT…", "", "txt"),
            ("Export as &PDF…", "", "pdf"),
        ):
            act = QAction(label, self)
            if shortcut:
                act.setShortcut(QKeySequence(shortcut))
            act.triggered.connect(lambda checked, f=fmt: self._export(f))
            file_menu.addAction(act)

        file_menu.addSeparator()
        act_quit = QAction("&Quit", self)
        act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        view_menu = mb.addMenu("&View")
        for page_id, label in self._PAGE_LABELS.items():
            act = QAction(label, self)
            act.triggered.connect(lambda checked, pid=page_id: self._switch_page(pid))
            view_menu.addAction(act)

        help_menu = mb.addMenu("&Help")
        act_about = QAction("About &HWSonnet", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    # ── Navigation ────────────────────────────────────────────────────── #

    def _switch_page(self, page_id: str) -> None:
        page = self._pages.get(page_id)
        if page:
            self._stack.setCurrentWidget(page)
        self._page_title_label.setText(self._PAGE_LABELS.get(page_id, page_id.title()))
        self._sidebar.select_page(page_id)

    # ── Data collection ───────────────────────────────────────────────── #

    def _start_static_collection(self) -> None:
        tasks = [
            ("cpu", self._collectors["cpu"].collect_static),
            ("gpu", self._collectors["gpu"].collect_static),
            ("ram", self._collectors["ram"].collect_static),
            ("storage", self._collectors["storage"].collect_static),
            ("network", self._collectors["network"].collect_static),
            ("sensors", self._collectors["sensors"].collect_static),
            ("system", self._collectors["system"].collect_static),
        ]
        self._pending_static = len(tasks)

        for name, fn in tasks:
            worker = StaticWorker(fn)
            worker.finished.connect(
                lambda result, n=name: self._on_static_ready(n, result)
            )
            worker.error.connect(
                lambda err, n=name: logger.error("%s static error: %s", n, err)
            )
            self._static_workers.append(worker)
            worker.start()

    def _on_static_ready(self, name: str, result: Any) -> None:
        self._data[name] = result
        self._pending_static -= 1
        logger.info("Static data ready: %s", name)
        self._dispatch_update(name, result)

        if self._pending_static == 0:
            self._status_indicator.setText("● Active")
            self._status_indicator.setStyleSheet(
                "color: #3fb950; font-size: 12px; background: transparent;"
            )
            self._start_dynamic_updates()

    def _start_dynamic_updates(self) -> None:
        collectors_map = {
            name: (self._data[name], getattr(self._collectors[name], "collect_dynamic"))
            for name in self._data
        }
        self._dynamic_worker = AllDataWorker(collectors_map, interval_ms=1500)
        self._dynamic_worker.snapshot_ready.connect(self._on_snapshot)
        self._dynamic_worker.start()

    def _on_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._data.update(snapshot)
        self._update_time_label.setText(
            f"Updated: {datetime.datetime.now().strftime('%H:%M:%S')}"
        )
        for name, data in snapshot.items():
            self._dispatch_update(name, data)

    def _dispatch_update(self, name: str, data: Any) -> None:
        try:
            if name == "cpu":
                self._pages["cpu"].update_data(data)
                self._pages["overview"].update_cpu(data)
            elif name == "gpu":
                self._pages["gpu"].update_data(data)
                self._pages["overview"].update_gpu(data)
            elif name == "ram":
                self._pages["ram"].update_data(data)
                self._pages["overview"].update_ram(data)
            elif name == "storage":
                self._pages["storage"].update_data(data)
            elif name == "network":
                self._pages["network"].update_data(data)
                self._pages["overview"].update_network(data)
            elif name == "sensors":
                self._pages["sensors"].update_data(data)
            elif name == "system":
                self._pages["system"].update_data(data)
                self._pages["overview"].update_system(data)
        except Exception as exc:
            logger.debug("Dispatch error for %s: %s", name, exc)

    # ── Export ────────────────────────────────────────────────────────── #

    def _export(self, fmt: str) -> None:
        filters = {
            "json": "JSON Files (*.json)",
            "txt": "Text Files (*.txt)",
            "pdf": "PDF Files (*.pdf)",
        }
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            f"Export as {fmt.upper()}",
            str(Path.home() / f"hwsonnet_report.{fmt}"),
            filters.get(fmt, "All Files (*)"),
        )
        if not path_str:
            return
        path = Path(path_str)
        flat = self._flatten_data()

        ok = {"json": export_json, "txt": export_txt, "pdf": export_pdf}[fmt](flat, path)
        msg = f"Exported to:\n{path}" if ok else "Export failed — see log."
        QMessageBox.information(self, "Export", msg)

    def _flatten_data(self) -> dict[str, Any]:
        import dataclasses
        result: dict[str, Any] = {}
        for name, obj in self._data.items():
            try:
                result[name] = dataclasses.asdict(obj)
            except TypeError:
                result[name] = str(obj)
        return result

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About HWSonnet",
            "<b>HWSonnet v1.0</b><br><br>"
            "Modern hardware information tool for Linux.<br>"
            "Built with Python 3 + PyQt6.<br><br>"
            "Optimized for Arch Linux.",
        )

    # ── Cleanup ───────────────────────────────────────────────────────── #

    def closeEvent(self, event) -> None:
        if self._dynamic_worker:
            self._dynamic_worker.stop()
        for w in self._static_workers:
            w.wait(2000)
        event.accept()
