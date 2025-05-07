"""Entry point for the VelRecover application."""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import QFile, QTextStream

from .ui.main_window import VelRecover

def main():
    """Run the VelRecover application."""
    # Initialize application
    app = QApplication(sys.argv)
    
    # Load and apply stylesheet (if available)
    style_file_path = os.path.join(os.path.dirname(__file__), "ui", "theme.qss")
    if os.path.exists(style_file_path):
        style_file = QFile(style_file_path)
        if style_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stream = QTextStream(style_file)
            app.setStyleSheet(stream.readAll())
            style_file.close()
        else:
            print("Warning: Could not load stylesheet")
    
    # Set default font if no stylesheet
    app.setStyle("windowsvista")
    app.setFont(QFont("Segoe UI", 10))

    # Create main window
    window = VelRecover()
    window.setWindowTitle('VelRecover')
    
    # Position window on screen
    screen = QApplication.primaryScreen().geometry()
    screen_width = min(screen.width(), 1920)
    screen_height = min(screen.height(), 1080)    
    pos_x = int(screen_width * 0.05)
    pos_y = int(screen_height * 0.05)
    window_width = int(screen_width * 0.9)
    window_height = int(screen_height * 0.85)
    window.setGeometry(pos_x, pos_y, window_width, window_height)
    
    # Show window
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
