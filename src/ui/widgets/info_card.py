"""InfoCard and KeyValueCard — polished display cards."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QLinearGradient, QBrush, QFont,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy,
)

from src.ui.styles.dark_theme import (
    SURFACE, SURFACE_2, SURFACE_3, BORDER, BORDER_LIGHT,
    TEXT, TEXT_SUB, TEXT_MUTED, ACCENT,
)


class InfoCard(QWidget):
    """A rounded card displaying a title, large value and optional subtitle."""

    def __init__(
        self,
        title: str = "",
        value: str = "—",
        subtitle: str = "",
        accent: str = ACCENT,
        icon: str = "",
        value_color: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._accent = QColor(accent)
        self._hover = False

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(88)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(3)

        # Header row
        hdr = QHBoxLayout()
        hdr.setSpacing(7)
        if icon:
            ic = QLabel(icon)
            ic.setStyleSheet(
                f"color: {accent}; font-size: 14px; background: transparent;"
            )
            hdr.addWidget(ic)
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 600; "
            "letter-spacing: 0.8px; background: transparent;"
        )
        hdr.addWidget(self._title_label)
        hdr.addStretch()
        layout.addLayout(hdr)

        # Value
        self._value_label = QLabel(value)
        self._value_label.setStyleSheet(
            f"color: {value_color or TEXT}; font-size: 20px; font-weight: 700; "
            "background: transparent; letter-spacing: -0.3px;"
        )
        layout.addWidget(self._value_label)

        # Subtitle
        self._subtitle_label = QLabel(subtitle)
        self._subtitle_label.setStyleSheet(
            f"color: {TEXT_SUB}; font-size: 10px; background: transparent;"
        )
        self._subtitle_label.setVisible(bool(subtitle))
        layout.addWidget(self._subtitle_label)

    # ── API ──────────────────────────────────────────────────────────── #

    def set_value(self, v: str) -> None:
        self._value_label.setText(v)

    def set_subtitle(self, s: str) -> None:
        self._subtitle_label.setText(s)
        self._subtitle_label.setVisible(bool(s))

    def set_accent(self, color: str) -> None:
        self._accent = QColor(color)
        self.update()

    # ── Paint ────────────────────────────────────────────────────────── #

    def paintEvent(self, event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(0, 0, -1, -1)
        r = 12

        # Background with subtle accent tint
        bg = QColor(SURFACE)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(rect, r, r)

        # Accent tint overlay (very subtle)
        tint = QColor(self._accent)
        tint.setAlpha(10 if not self._hover else 18)
        p.setBrush(tint)
        p.drawRoundedRect(rect, r, r)

        # Border
        border_col = QColor(self._accent) if self._hover else QColor(BORDER)
        border_col.setAlpha(120 if not self._hover else 200)
        p.setPen(QPen(border_col, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, r, r)

        # Left accent bar
        bar = QRectF(0, 10, 3, rect.height() - 20)
        p.setPen(Qt.PenStyle.NoPen)
        grad = QLinearGradient(0, bar.top(), 0, bar.bottom())
        c0 = QColor(self._accent)
        c0.setAlpha(0)
        c1 = QColor(self._accent)
        c1.setAlpha(220)
        c2 = QColor(self._accent)
        c2.setAlpha(0)
        grad.setColorAt(0.0, c0)
        grad.setColorAt(0.5, c1)
        grad.setColorAt(1.0, c2)
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(bar, 1.5, 1.5)

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()


class KeyValueCard(QWidget):
    """Card with a title and a vertical list of key→value property rows."""

    def __init__(
        self,
        title: str = "",
        rows: list[tuple[str, str]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(0)

        if title:
            hdr = QLabel(title.upper())
            hdr.setStyleSheet(
                f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 700; "
                "letter-spacing: 1px; background: transparent; padding-bottom: 10px;"
            )
            layout.addWidget(hdr)

        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(0)
        layout.addLayout(self._rows_layout)

        self._row_labels: dict[str, QLabel] = {}
        if rows:
            for i, (k, v) in enumerate(rows):
                self._add_row_widget(k, v, i % 2 == 1)

    def _add_row_widget(self, key: str, value: str, alt: bool) -> None:
        container = QWidget()
        container.setStyleSheet(
            f"background: {'rgba(26,36,56,0.5)' if alt else 'transparent'}; "
            "border-radius: 4px;"
        )
        container.setFixedHeight(28)
        row = QHBoxLayout(container)
        row.setContentsMargins(6, 0, 6, 0)
        row.setSpacing(8)

        kl = QLabel(key)
        kl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
        kl.setFixedWidth(170)

        vl = QLabel(value)
        vl.setStyleSheet(
            f"color: {TEXT}; font-size: 12px; font-weight: 500; background: transparent;"
        )
        vl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        row.addWidget(kl)
        row.addWidget(vl, 1)
        self._rows_layout.addWidget(container)
        self._row_labels[key] = vl

    def add_row(self, key: str, value: str) -> None:
        n = len(self._row_labels)
        self._add_row_widget(key, value, n % 2 == 1)

    def update_row(self, key: str, value: str) -> None:
        if key in self._row_labels:
            self._row_labels[key].setText(value)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(0, 0, -1, -1)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(SURFACE))
        p.drawRoundedRect(rect, 12, 12)
        p.setPen(QPen(QColor(BORDER), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, 12, 12)
