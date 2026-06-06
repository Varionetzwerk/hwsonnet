"""Collapsible sidebar navigation widget — polished dark design."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QSize
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QLinearGradient, QBrush, QFont,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QSizePolicy,
)

from src.ui.styles.dark_theme import (
    BG, SURFACE, SURFACE_2, SURFACE_3, BORDER, BORDER_LIGHT,
    TEXT, TEXT_SUB, TEXT_MUTED, ACCENT, ACCENT_DIM,
    SIDEBAR_W, SIDEBAR_W_COLLAPSED,
)

NAV_ITEMS = [
    ("overview", "•", "Overview"),
    ("cpu",      "•", "CPU"),
    ("gpu",      "•", "GPU"),
    ("ram",      "•", "RAM"),
    ("storage",  "•", "Storage"),
    ("network",  "•", "Network"),
    ("sensors",  "•", "Sensors"),
    ("system",   "•", "System"),
]


class _NavButton(QWidget):
    """Custom-drawn navigation button with hover/active states."""

    clicked = pyqtSignal()

    def __init__(
        self,
        page_id: str,
        icon: str,
        label: str,
        collapsed: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._page_id = page_id
        self._icon = icon
        self._label = label
        self._collapsed = collapsed
        self._active = False
        self._hover = False

        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setToolTip("" if not collapsed else label)

    @property
    def page_id(self) -> str:
        return self._page_id

    def set_active(self, active: bool) -> None:
        self._active = active
        self.update()

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self.setToolTip(self._label if collapsed else "")
        self.update()

    # ── Events ───────────────────────────────────────────────────────── #

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    # ── Paint ────────────────────────────────────────────────────────── #

    def paintEvent(self, event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = self.width(), self.height()
        accent = QColor(ACCENT)

        # Background fill
        if self._active:
            bg = QColor(ACCENT)
            bg.setAlpha(20)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(bg)
            p.drawRoundedRect(QRectF(4, 2, w - 8, h - 4), 8, 8)
        elif self._hover:
            bg = QColor(SURFACE_3)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(bg)
            p.drawRoundedRect(QRectF(4, 2, w - 8, h - 4), 8, 8)

        # Left indicator bar
        if self._active:
            bar_h = 24
            bar_y = (h - bar_h) / 2
            grad = QLinearGradient(0, bar_y, 0, bar_y + bar_h)
            c0 = QColor(accent); c0.setAlpha(0)
            c1 = QColor(accent); c1.setAlpha(255)
            c2 = QColor(accent); c2.setAlpha(0)
            grad.setColorAt(0.0, c0)
            grad.setColorAt(0.5, c1)
            grad.setColorAt(1.0, c2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(QRectF(0, bar_y, 3, bar_h), 1.5, 1.5)

        # Icon
        icon_col = QColor(ACCENT) if self._active else (
            QColor(TEXT_SUB) if not self._hover else QColor(TEXT)
        )
        p.setPen(QPen(icon_col))
        font = QFont()
        font.setPointSizeF(16)
        p.setFont(font)

        if self._collapsed:
            p.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, self._icon)
        else:
            p.drawText(QRectF(18, 0, 20, h),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       self._icon)
            # Label
            lbl_col = QColor(ACCENT) if self._active else (
                QColor(TEXT) if self._hover else QColor(TEXT_SUB)
            )
            p.setPen(QPen(lbl_col))
            font.setPointSizeF(13)
            font.setBold(self._active)
            p.setFont(font)
            p.drawText(QRectF(48, 0, w - 56, h),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       self._label)


class Sidebar(QWidget):
    """Collapsible left sidebar with logo and navigation buttons."""

    page_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._collapsed = False
        self._buttons: list[_NavButton] = []
        self._build_ui()
        self._set_width(SIDEBAR_W)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo / header
        self._header = _LogoHeader()
        layout.addWidget(self._header)

        # Nav buttons
        nav_wrap = QWidget()
        nav_wrap.setStyleSheet("background: transparent;")
        self._nav_layout = QVBoxLayout(nav_wrap)
        self._nav_layout.setContentsMargins(0, 8, 0, 8)
        self._nav_layout.setSpacing(2)

        for page_id, icon, label in NAV_ITEMS:
            btn = _NavButton(page_id, icon, label, self._collapsed)
            btn.clicked.connect(lambda pid=page_id: self._on_nav_click(pid))
            self._nav_layout.addWidget(btn)
            self._buttons.append(btn)

        self._nav_layout.addStretch()
        layout.addWidget(nav_wrap, 1)

        # Collapse toggle
        self._toggle = _CollapseButton()
        self._toggle.clicked.connect(self.toggle_collapse)
        layout.addWidget(self._toggle)

        # Activate first button
        if self._buttons:
            self._buttons[0].set_active(True)

    def _on_nav_click(self, page_id: str) -> None:
        self._set_active(page_id)
        self.page_changed.emit(page_id)

    def select_page(self, page_id: str) -> None:
        """Update visual selection without emitting the signal."""
        self._set_active(page_id)

    def _set_active(self, page_id: str) -> None:
        for btn in self._buttons:
            btn.set_active(btn.page_id == page_id)

    def toggle_collapse(self) -> None:
        self._collapsed = not self._collapsed
        self._set_width(SIDEBAR_W_COLLAPSED if self._collapsed else SIDEBAR_W)
        self._header.set_collapsed(self._collapsed)
        self._toggle.set_collapsed(self._collapsed)
        for btn in self._buttons:
            btn.set_collapsed(self._collapsed)

    def _set_width(self, w: int) -> None:
        self.setFixedWidth(w)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        p = QPainter(self)
        # Gradient sidebar background
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, QColor("#0a0f1a"))
        grad.setColorAt(1.0, QColor(SURFACE))
        p.fillRect(self.rect(), QBrush(grad))
        # Right border
        p.setPen(QPen(QColor(BORDER), 1))
        p.drawLine(self.width() - 1, 0, self.width() - 1, self.height())


class _LogoHeader(QWidget):
    """Sidebar logo / title area."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._collapsed = False
        self.setFixedHeight(64)

    def set_collapsed(self, c: bool) -> None:
        self._collapsed = c
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = self.width(), self.height()

        # Bottom border
        p.setPen(QPen(QColor(BORDER), 1))
        p.drawLine(0, h - 1, w, h - 1)

        p.setPen(QPen(QColor(ACCENT)))
        font = QFont()
        font.setBold(True)
        if self._collapsed:
            font.setPointSizeF(15)
            p.setFont(font)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "HW")
        else:
            font.setPointSizeF(16)
            p.setFont(font)
            p.drawText(QRectF(22, 0, w - 30, h),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       "HWSonnet")


class _CollapseButton(QWidget):
    """Bottom collapse/expand toggle."""

    clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._collapsed = False
        self._hover = False
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def set_collapsed(self, c: bool) -> None:
        self._collapsed = c
        self.update()

    def enterEvent(self, e) -> None:
        self._hover = True
        self.update()

    def leaveEvent(self, e) -> None:
        self._hover = False
        self.update()

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Top border
        p.setPen(QPen(QColor(BORDER), 1))
        p.drawLine(0, 0, w, 0)

        col = QColor(TEXT_SUB) if not self._hover else QColor(TEXT)
        p.setPen(QPen(col))
        font = QFont()
        font.setPointSizeF(13)
        p.setFont(font)
        arrow = "▶" if self._collapsed else "◀"
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, arrow)
