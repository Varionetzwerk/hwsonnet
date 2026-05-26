"""Application bootstrap — sets up QApplication and applies global theme."""

from __future__ import annotations

import sys

from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtWidgets import QApplication

from src.ui.styles.dark_theme import BG, TEXT, SURFACE, BORDER, get_stylesheet
from src.utils.logger import logger


def create_app(argv: list[str] | None = None) -> QApplication:
    if argv is None:
        argv = sys.argv

    QCoreApplication.setOrganizationName("HWSonnet")
    QCoreApplication.setApplicationName("HWSonnet")
    QCoreApplication.setApplicationVersion("1.0.0")

    app = QApplication(argv)
    app.setStyle("Fusion")

    # Base palette — overridden by stylesheet, but provides fallback colours
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(BORDER))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#58a6ff"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    app.setStyleSheet(get_stylesheet())

    font = QFont("Inter", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    logger.info("QApplication initialized")
    return app
