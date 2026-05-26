"""Live rolling chart widget — smooth Catmull-Rom curves, QPainter-only."""

from __future__ import annotations

from collections import deque
from typing import Optional

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush,
    QPainterPath, QLinearGradient, QFont, QRadialGradient,
)
from PyQt6.QtWidgets import QWidget, QSizePolicy

from src.ui.styles.dark_theme import SURFACE_2, SURFACE_3, BORDER, TEXT, TEXT_SUB, TEXT_MUTED


def _catmull_path(points: list[QPointF]) -> QPainterPath:
    """Catmull-Rom spline through all points — smooth, no overshooting."""
    path = QPainterPath()
    n = len(points)
    if n < 2:
        return path
    path.moveTo(points[0])
    if n == 2:
        path.lineTo(points[1])
        return path
    for i in range(1, n):
        p0 = points[max(0, i - 2)]
        p1 = points[i - 1]
        p2 = points[i]
        p3 = points[min(n - 1, i + 1)]
        cp1 = QPointF(p1.x() + (p2.x() - p0.x()) / 6.0,
                      p1.y() + (p2.y() - p0.y()) / 6.0)
        cp2 = QPointF(p2.x() - (p3.x() - p1.x()) / 6.0,
                      p2.y() - (p3.y() - p1.y()) / 6.0)
        path.cubicTo(cp1, cp2, p2)
    return path


class LiveChart(QWidget):
    """Smooth filled rolling line chart with Catmull-Rom interpolation."""

    def __init__(
        self,
        color: str = "#4d9eff",
        title: str = "",
        y_label: str = "%",
        y_max: float = 100.0,
        max_points: int = 60,
        show_grid: bool = True,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self._title = title
        self._y_label = y_label
        self._y_max = y_max
        self._max_points = max_points
        self._show_grid = show_grid
        self._data: deque[float] = deque([0.0] * max_points, maxlen=max_points)

        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    # ── Public API ───────────────────────────────────────────────────── #

    def add_value(self, value: float) -> None:
        self._data.append(max(0.0, min(self._y_max, value)))
        self.update()

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def clear(self) -> None:
        self._data = deque([0.0] * self._max_points, maxlen=self._max_points)
        self.update()

    # ── Paint ────────────────────────────────────────────────────────── #

    def paintEvent(self, event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = self.width(), self.height()
        has_title = bool(self._title)
        pad_t = 30 if has_title else 14
        pad_b = 32
        pad_l = 36
        pad_r = 10

        cw = w - pad_l - pad_r
        ch = h - pad_t - pad_b

        # ── Background ──────────────────────────────────────────────── #
        bg = QColor(SURFACE_2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(self.rect(), 12, 12)

        # Border
        p.setPen(QPen(QColor(BORDER), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 12, 12)

        # ── Grid ────────────────────────────────────────────────────── #
        if self._show_grid and ch > 0:
            grid_col = QColor(BORDER)
            grid_col.setAlpha(60)
            p.setPen(QPen(grid_col, 1, Qt.PenStyle.DotLine))
            for i in range(1, 4):
                y = int(pad_t + ch * i / 4)
                p.drawLine(pad_l, y, pad_l + cw, y)

            # Y-axis labels
            p.setPen(QPen(QColor(TEXT_MUTED)))
            font = QFont()
            font.setPointSizeF(8)
            p.setFont(font)
            for i in range(0, 5):
                val = self._y_max * (4 - i) / 4
                y = int(pad_t + ch * i / 4)
                lbl = f"{int(val)}" if self._y_max <= 1000 else f"{val/1024:.0f}k"
                p.drawText(QRectF(0, y - 8, pad_l - 4, 16),
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, lbl)

        data_list = list(self._data)
        n = len(data_list)
        if n < 2 or cw <= 0 or ch <= 0:
            self._draw_title_and_value(p, w, [], 0.0)
            return

        # ── Points ──────────────────────────────────────────────────── #
        def pt(i: int, v: float) -> QPointF:
            x = pad_l + (i / (n - 1)) * cw
            y = pad_t + (1.0 - v / self._y_max) * ch
            return QPointF(x, y)

        points = [pt(i, v) for i, v in enumerate(data_list)]

        # ── Smooth line path ─────────────────────────────────────────── #
        line_path = _catmull_path(points)

        # ── Fill ────────────────────────────────────────────────────── #
        fill_path = QPainterPath(line_path)
        fill_path.lineTo(points[-1].x(), pad_t + ch)
        fill_path.lineTo(pad_l, pad_t + ch)
        fill_path.closeSubpath()

        grad = QLinearGradient(0, pad_t, 0, pad_t + ch)
        top_c = QColor(self._color)
        top_c.setAlpha(80)
        bot_c = QColor(self._color)
        bot_c.setAlpha(4)
        grad.setColorAt(0.0, top_c)
        grad.setColorAt(1.0, bot_c)
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(fill_path, QBrush(grad))

        # ── Line ────────────────────────────────────────────────────── #
        pen = QPen(self._color, 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.drawPath(line_path)

        # ── End-point dot with glow ──────────────────────────────────── #
        last = points[-1]
        glow_c = QColor(self._color)
        glow_c.setAlpha(40)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(glow_c)
        p.drawEllipse(last, 7, 7)
        p.setBrush(QColor(SURFACE_2))
        p.setPen(QPen(self._color, 2))
        p.drawEllipse(last, 3.5, 3.5)

        # ── Time axis ────────────────────────────────────────────────── #
        p.setPen(QPen(QColor(TEXT_MUTED)))
        font = QFont()
        font.setPointSizeF(8)
        p.setFont(font)
        for secs in (60, 45, 30, 15, 0):
            idx = int(secs / 60 * (n - 1))
            x = pad_l + ((n - 1 - idx) / (n - 1)) * cw
            lbl = f"-{secs}s" if secs > 0 else "now"
            p.drawText(QRectF(x - 20, pad_t + ch + 6, 40, 16),
                       Qt.AlignmentFlag.AlignCenter, lbl)

        self._draw_title_and_value(p, w, data_list, data_list[-1])

    def _draw_title_and_value(
        self, p: QPainter, w: int, data: list, current: float
    ) -> None:
        # Title (top-left)
        if self._title:
            p.setPen(QPen(QColor(TEXT_SUB)))
            font = QFont()
            font.setPointSizeF(10)
            p.setFont(font)
            p.drawText(QRectF(12, 6, w - 120, 22),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       self._title)

        # Current value (top-right)
        if data:
            p.setPen(QPen(self._color))
            font = QFont()
            font.setPointSizeF(11)
            font.setBold(True)
            p.setFont(font)
            p.drawText(QRectF(w - 90, 6, 82, 22),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       f"{current:.1f}{self._y_label}")


class MultiLineChart(QWidget):
    """Chart with multiple color-coded data series."""

    def __init__(
        self,
        series: list[tuple[str, str]],
        y_max: float = 100.0,
        max_points: int = 60,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._y_max = y_max
        self._max_points = max_points
        self._series = series
        self._data: list[deque[float]] = [
            deque([0.0] * max_points, maxlen=max_points) for _ in series
        ]
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def add_values(self, values: list[float]) -> None:
        for i, v in enumerate(values):
            if i < len(self._data):
                self._data[i].append(max(0.0, min(self._y_max, v)))
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        pad_t, pad_b, pad_l, pad_r = 14, 28, 8, 8
        legend_h = 24
        cw = w - pad_l - pad_r
        ch = h - pad_t - pad_b - legend_h

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(SURFACE_2))
        p.drawRoundedRect(self.rect(), 12, 12)
        p.setPen(QPen(QColor(BORDER), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 12, 12)

        if ch <= 0 or cw <= 0:
            return

        for idx, (label, color) in enumerate(self._series):
            data = list(self._data[idx])
            n = len(data)
            if n < 2:
                continue
            col = QColor(color)
            col.setAlpha(200)

            def pt(i: int, v: float) -> QPointF:
                x = pad_l + (i / (n - 1)) * cw
                y = pad_t + (1.0 - v / self._y_max) * ch
                return QPointF(x, y)

            points = [pt(i, v) for i, v in enumerate(data)]
            path = _catmull_path(points)
            p.setPen(QPen(col, 1.5,
                          Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap))
            p.drawPath(path)

        # Legend
        ly = h - legend_h
        x_off = 12
        font = QFont()
        font.setPointSizeF(9)
        p.setFont(font)
        for label, color in self._series:
            col = QColor(color)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(col)
            p.drawEllipse(x_off, ly + 8, 8, 8)
            p.setPen(QPen(QColor(TEXT_SUB)))
            p.drawText(int(x_off + 12), int(ly + 17), label)
            x_off += len(label) * 7 + 28
