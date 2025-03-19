"""Entry point for the VelRecover application."""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from .ui.main_window import VelRecover2D

def main():
    """Run the SEGYRecover application."""
    app = QApplication(sys.argv)
    app.setStyle("windowsvista")
    app.setFont(QFont("Segoe UI", 10))

    window = VelRecover2D()
    window.setWindowTitle('VelRecover')
    screen = QApplication.primaryScreen().geometry()
    screen_width = min(screen.width(), 1920)
    screen_height = min(screen.height(), 1080)
    pos_x = int(screen_width * 0.05)
    pos_y = int(screen_height * 0.05)
    window_width= int(screen_width * 0.25)
    window_height = int(screen_height * 0.9)
    window.setGeometry(pos_x, pos_y, window_width, window_height)
    
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
