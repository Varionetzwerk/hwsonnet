"""Circular gauge and mini bar gauge widgets."""

from __future__ import annotations

import math
from typing import Optional

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush,
    QConicalGradient, QFont, QLinearGradient, QRadialGradient,
)
from PyQt6.QtWidgets import QWidget, QSizePolicy

from src.ui.styles.dark_theme import (
    SURFACE_2, SURFACE_3, BORDER, TEXT, TEXT_SUB, TEXT_MUTED,
    GREEN, YELLOW, ORANGE, RED, BG,
)


def _value_color(ratio: float) -> str:
    if ratio < 0.5:
        return GREEN
    if ratio < 0.75:
        return YELLOW
    if ratio < 0.9:
        return ORANGE
    return RED


class GaugeWidget(QWidget):
    """Circular speedometer-style gauge with glow arc and tick marks."""

    # Arc starts at 7 o'clock (225°) and sweeps 270° clockwise
    _START = 225   # degrees (Qt coordinate: CCW from 3 o'clock)
    _SPAN  = 270

    def __init__(
        self,
        title: str = "",
        unit: str = "%",
        max_value: float = 100.0,
        color: str = "#4d9eff",
        style: str = "full",
        card: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._unit = unit
        self._max = max_value
        self._color = QColor(color)
        self._value: float = 0.0
        self._style = style   # "full" (270° dial) or "semi" (180° arc)
        self._card = card     # draw rounded card background

        self.setMinimumSize(130, 130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    # ── Public ───────────────────────────────────────────────────────── #

    def set_value(self, v: float) -> None:
        self._value = max(0.0, min(self._max, v))
        self.update()

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def set_auto_color(self) -> None:
        self._color = QColor(_value_color(self._value / self._max))
        self.update()

    # ── Paint ────────────────────────────────────────────────────────── #

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        if self._card:
            rect = QRectF(self.rect().adjusted(0, 0, -1, -1))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(SURFACE_2))
            painter.drawRoundedRect(rect, 14, 14)
            border = QColor(BORDER)
            border.setAlpha(140)
            painter.setPen(QPen(border, 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, 14, 14)

        if self._style == "semi":
            self._paint_semi(painter)
            return

        w, h = self.width(), self.height()
        size = min(w, h)
        cx, cy = w / 2, h / 2

        thickness = max(9, size // 9)
        margin = thickness / 2 + 4
        r = size / 2 - margin
        arc_rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)

        ratio = self._value / self._max if self._max else 0.0
        sweep = ratio * self._SPAN

        # ── Track ring ──────────────────────────────────────────────── #
        track_col = QColor(SURFACE_3)
        painter.setPen(QPen(track_col, thickness, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap))
        painter.drawArc(arc_rect,
                        int(self._START * 16),
                        int(-self._SPAN * 16))

        # ── Tick marks ──────────────────────────────────────────────── #
        tick_col = QColor(BORDER)
        tick_col.setAlpha(120)
        painter.setPen(QPen(tick_col, 1.5))
        n_ticks = 10
        for i in range(n_ticks + 1):
            angle_deg = self._START - (i / n_ticks) * self._SPAN
            angle_rad = math.radians(angle_deg)
            r_out = r - thickness / 2 - 2
            r_in  = r_out - 5
            x1 = cx + r_out * math.cos(angle_rad)
            y1 = cy - r_out * math.sin(angle_rad)
            x2 = cx + r_in  * math.cos(angle_rad)
            y2 = cy - r_in  * math.sin(angle_rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        if sweep > 0:
            # ── Outer glow layers ────────────────────────────────────── #
            for glow_i in range(3, 0, -1):
                glow_c = QColor(self._color)
                glow_c.setAlpha(14 * glow_i)
                painter.setPen(QPen(glow_c,
                                    thickness + glow_i * 4,
                                    Qt.PenStyle.SolidLine,
                                    Qt.PenCapStyle.RoundCap))
                painter.drawArc(arc_rect,
                                int(self._START * 16),
                                int(-sweep * 16))

            # ── Main value arc ───────────────────────────────────────── #
            painter.setPen(QPen(self._color, thickness,
                                Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap))
            painter.drawArc(arc_rect,
                            int(self._START * 16),
                            int(-sweep * 16))

            # ── Tip dot ──────────────────────────────────────────────── #
            tip_angle_rad = math.radians(self._START - sweep)
            tip_x = cx + r * math.cos(tip_angle_rad)
            tip_y = cy - r * math.sin(tip_angle_rad)
            tip_r = thickness / 2
            tip_glow = QColor(self._color)
            tip_glow.setAlpha(60)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(tip_glow)
            painter.drawEllipse(QPointF(tip_x, tip_y), tip_r + 3, tip_r + 3)
            painter.setBrush(self._color)
            painter.drawEllipse(QPointF(tip_x, tip_y), tip_r, tip_r)

        # ── Center: value text ────────────────────────────────────────── #
        val_str = (f"{self._value:.0f}"
                   if self._unit in ("%", "°C", "RPM")
                   else f"{self._value:.1f}")

        # Large value
        painter.setPen(QPen(QColor(TEXT)))
        font = QFont()
        font.setPointSizeF(max(9, size / 6.5))
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, -0.5)
        painter.setFont(font)
        painter.drawText(
            QRectF(cx - size / 2, cy - size / 4.5, size, size / 3.5),
            Qt.AlignmentFlag.AlignCenter, val_str,
        )

        # Unit
        painter.setPen(QPen(QColor(TEXT_SUB)))
        font.setPointSizeF(max(7, size / 11))
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(
            QRectF(cx - size / 2, cy + size / 8, size, size / 5),
            Qt.AlignmentFlag.AlignCenter, self._unit,
        )

        # Title at bottom
        if self._title:
            painter.setPen(QPen(QColor(TEXT_MUTED)))
            font.setPointSizeF(max(7.5, size / 13))
            painter.setFont(font)
            painter.drawText(
                QRectF(0, h - 26, w, 22),
                Qt.AlignmentFlag.AlignCenter, self._title,
            )

    # ── Semicircle (180°) variant ─────────────────────────────────────── #

    def _paint_semi(self, painter: QPainter) -> None:
        w, h = self.width(), self.height()
        pad = 22
        label_h = 24 if self._title else 0

        baseline = (h - label_h) * 0.66
        r = min((w - 2 * pad) / 2, baseline - pad)
        if r <= 0:
            return
        cx = w / 2
        cy = baseline
        arc_rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
        thickness = max(10, int(r / 4.5))

        ratio = self._value / self._max if self._max else 0.0
        start = 180
        span = 180
        sweep = ratio * span

        # Track (top half, left→right over the top)
        painter.setPen(QPen(QColor(SURFACE_3), thickness,
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(arc_rect, start * 16, int(-span * 16))

        if sweep > 0:
            for glow_i in range(3, 0, -1):
                glow_c = QColor(self._color)
                glow_c.setAlpha(12 * glow_i)
                painter.setPen(QPen(glow_c, thickness + glow_i * 4,
                                    Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawArc(arc_rect, start * 16, int(-sweep * 16))

            painter.setPen(QPen(self._color, thickness,
                                Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(arc_rect, start * 16, int(-sweep * 16))

            tip_rad = math.radians(start - sweep)
            tip_x = cx + r * math.cos(tip_rad)
            tip_y = cy - r * math.sin(tip_rad)
            tip_r = thickness / 2
            glow = QColor(self._color)
            glow.setAlpha(70)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(tip_x, tip_y), tip_r + 3, tip_r + 3)
            painter.setBrush(self._color)
            painter.drawEllipse(QPointF(tip_x, tip_y), tip_r, tip_r)

        # Center value (number + unit inline, e.g. "42%", "58°C")
        if self._unit == "%":
            val_str = f"{self._value:.0f}%"
        elif self._unit == "°C":
            val_str = f"{self._value:.0f}°C"
        else:
            val_str = f"{self._value:.0f}{self._unit}"

        painter.setPen(QPen(QColor(TEXT)))
        font = QFont()
        font.setPointSizeF(max(13, r / 2.6))
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, -0.5)
        painter.setFont(font)
        painter.drawText(
            QRectF(cx - r, cy - r * 0.72, 2 * r, r * 0.78),
            Qt.AlignmentFlag.AlignCenter, val_str,
        )

        # Label below the arc
        if self._title:
            painter.setPen(QPen(QColor(TEXT_SUB)))
            font.setPointSizeF(11)
            font.setBold(False)
            painter.setFont(font)
            painter.drawText(
                QRectF(0, cy + 6, w, h - cy - 6),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._title,
            )


class MiniGauge(QWidget):
    """Compact horizontal bar gauge for per-core usage display."""

    def __init__(
        self,
        label: str = "",
        color: str = "#4d9eff",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._label = label
        self._color = QColor(color)
        self._value: float = 0.0
        self.setFixedHeight(26)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_value(self, v: float) -> None:
        self._value = max(0.0, min(100.0, v))
        self.update()

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = self.width(), self.height()
        label_w = 68
        val_w = 52
        bar_x = label_w + 8
        bar_w = w - bar_x - val_w - 4
        bar_h = 8
        bar_y = (h - bar_h) // 2

        # Label
        p.setPen(QPen(QColor(TEXT_MUTED)))
        font = QFont()
        font.setPointSizeF(9.5)
        p.setFont(font)
        p.drawText(QRectF(0, 0, label_w, h),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   self._label)

        # Track
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(SURFACE_3))
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 4, 4)

        # Fill with gradient
        fill_w = bar_w * self._value / 100.0
        if fill_w > 0:
            col = QColor(_value_color(self._value / 100.0))
            grad = QLinearGradient(bar_x, 0, bar_x + fill_w, 0)
            grad.setColorAt(0.0, col.darker(110))
            grad.setColorAt(1.0, col)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 4, 4)

        # Value
        col_text = QColor(_value_color(self._value / 100.0))
        p.setPen(QPen(col_text))
        font.setPointSizeF(9.5)
        font.setBold(True)
        p.setFont(font)
        p.drawText(
            QRectF(bar_x + bar_w + 6, 0, val_w - 6, h),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            f"{self._value:.1f}%",
        )
