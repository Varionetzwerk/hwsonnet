#!/usr/bin/env python3
"""HWSonnet — Modern hardware information tool for Linux.

Usage:
    python main.py
"""

import sys
import os

# Ensure the project root is on the Python path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.ui.main_window import MainWindow
from src.utils.logger import logger


def main() -> int:
    app = create_app(sys.argv)

    window = MainWindow()
    window.show()

    logger.info("HWSonnet started")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
