"""Global dark theme stylesheet and color palette for HWSonnet."""

from __future__ import annotations

# ── Color palette ──────────────────────────────────────────────────────────── #
BG        = "#0a0e14"
SURFACE   = "#0f1520"
SURFACE_2 = "#151d2e"
SURFACE_3 = "#1a2438"
BORDER    = "#1e2d45"
BORDER_LIGHT = "#2a3f5f"

TEXT       = "#e8eef8"
TEXT_SUB   = "#7a91b0"
TEXT_MUTED = "#4a5f7a"

BLUE   = "#4d9eff"
GREEN  = "#2ea84c"
YELLOW = "#e8a020"
ORANGE = "#e06030"
RED    = "#e84545"
PURPLE = "#a87aff"
TEAL   = "#20c0a0"
CYAN   = "#20b8d0"

ACCENT     = BLUE
ACCENT_DIM = "#1a5fa0"

SIDEBAR_W           = 220
SIDEBAR_W_COLLAPSED = 60


def get_stylesheet() -> str:
    return f"""
/* ── Base ─────────────────────────────────────────────────────────────── */
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Inter", "SF Pro Display", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
    border: none;
    outline: none;
}}
QMainWindow, QDialog {{
    background-color: {BG};
}}

/* ── Scroll ────────────────────────────────────────────────────────────── */
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_LIGHT};
    min-height: 24px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{ background: {TEXT_MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER_LIGHT};
    min-width: 24px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal:hover {{ background: {TEXT_MUTED}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Labels ────────────────────────────────────────────────────────────── */
QLabel {{ background: transparent; color: {TEXT}; }}

/* ── Buttons ───────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 7px 18px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {ACCENT_DIM};
    border-color: {ACCENT};
    color: white;
}}
QPushButton:pressed {{
    background-color: {ACCENT};
    color: white;
}}
QPushButton[class="primary"] {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #1e6fcc, stop:1 #1455a0);
    border: 1px solid #2a7add;
    color: white;
    font-weight: 600;
}}
QPushButton[class="primary"]:hover {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #2a7add, stop:1 #1a5fbb);
}}

/* ── Line Edit ─────────────────────────────────────────────────────────── */
QLineEdit {{
    background-color: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px 14px;
    selection-background-color: {ACCENT_DIM};
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}

/* ── ComboBox ──────────────────────────────────────────────────────────── */
QComboBox {{
    background-color: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 5px 12px;
    min-width: 80px;
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background-color: {SURFACE_3};
    color: {TEXT};
    border: 1px solid {BORDER_LIGHT};
    selection-background-color: {ACCENT_DIM};
    selection-color: white;
    border-radius: 8px;
}}

/* ── Progress Bar ──────────────────────────────────────────────────────── */
QProgressBar {{
    background-color: {SURFACE_3};
    border: none;
    border-radius: 4px;
    height: 8px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {ACCENT}, stop:1 #6ab8ff);
    border-radius: 4px;
}}
QProgressBar[class="green"]::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {GREEN}, stop:1 #50d870);
}}
QProgressBar[class="yellow"]::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {YELLOW}, stop:1 #f0c050);
}}
QProgressBar[class="red"]::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {RED}, stop:1 #ff6060);
}}
QProgressBar[class="purple"]::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {PURPLE}, stop:1 #c8a0ff);
}}

/* ── Tab Widget ────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 10px;
    background-color: {SURFACE};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {TEXT_SUB};
    padding: 9px 20px;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 400;
}}
QTabBar::tab:selected {{ color: {ACCENT}; border-bottom: 2px solid {ACCENT}; }}
QTabBar::tab:hover {{ color: {TEXT}; }}

/* ── Table ─────────────────────────────────────────────────────────────── */
QTableWidget {{
    background-color: {SURFACE};
    gridline-color: {BORDER};
    border: 1px solid {BORDER};
    border-radius: 10px;
    selection-background-color: {ACCENT_DIM};
    selection-color: white;
    alternate-background-color: {SURFACE_2};
}}
QTableWidget::item {{ padding: 7px 12px; border: none; }}
QHeaderView::section {{
    background-color: {SURFACE_2};
    color: {TEXT_SUB};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 7px 12px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* ── Tooltip ───────────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {SURFACE_3};
    color: {TEXT};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
}}

/* ── Menu ──────────────────────────────────────────────────────────────── */
QMenuBar {{
    background-color: {SURFACE};
    color: {TEXT_SUB};
    border-bottom: 1px solid {BORDER};
    padding: 2px 4px;
}}
QMenuBar::item {{ padding: 4px 10px; border-radius: 4px; }}
QMenuBar::item:selected {{ background: {ACCENT_DIM}; color: white; }}
QMenu {{
    background-color: {SURFACE_3};
    color: {TEXT};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 10px;
    padding: 6px 4px;
}}
QMenu::item {{ padding: 7px 22px; border-radius: 6px; margin: 1px 4px; }}
QMenu::item:selected {{ background-color: {ACCENT_DIM}; color: white; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 10px; }}

/* ── Splitter ──────────────────────────────────────────────────────────── */
QSplitter::handle {{ background-color: {BORDER}; }}
QSplitter::handle:horizontal {{ width: 1px; }}

/* ── Status Bar ────────────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {SURFACE};
    color: {TEXT_MUTED};
    border-top: 1px solid {BORDER};
    font-size: 11px;
    padding: 0 8px;
}}
QStatusBar QLabel {{ color: {TEXT_MUTED}; background: transparent; }}
"""
