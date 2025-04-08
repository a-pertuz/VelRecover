"""Custom widgets for SEGYRecover application."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QStatusBar, 
    QProgressBar, QPushButton, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QStyle

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class VelScatterCanvas(FigureCanvas):
    """Canvas for displaying velocity scatter plots."""
    
    def __init__(self, parent=None, fc='none'):
        """Initialize canvas with a figure."""
        fig = Figure(facecolor=fc)
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

class ProgressStatusBar(QWidget):
    """Status bar with integrated progress bar and cancel button."""
    
    def __init__(self, parent=None):
        """Initialize the status bar."""
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(15)
        self.progress_bar.setMaximumWidth(200)
        
        # Create cancel button
        self.cancel_button = QPushButton()
        self.cancel_button.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel)
        
        # Add widgets to status bar
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.status_bar.addPermanentWidget(self.cancel_button)
        
        self.layout.addWidget(self.status_bar)
        self._canceled = False
        
    def start(self, title, maximum):
        """Start a progress operation with the given title and maximum value."""
        self._canceled = False
        self.status_bar.showMessage(title)
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.cancel_button.setVisible(True)
        QApplication.processEvents()
        
    def update(self, value, message=None):
        """Update progress bar with new value and optional message."""
        if message:
            self.status_bar.showMessage(message)
        self.progress_bar.setValue(value)
        QApplication.processEvents()
        
    def finish(self):
        """Complete the progress operation."""
        self.status_bar.clearMessage()
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        
    def cancel(self):
        """Cancel the current operation."""
        self._canceled = True
        
    def wasCanceled(self):
        """Check if the operation was cancelled."""
        return self._canceled
    
    def showMessage(self, message):
        """Show a message in the status bar."""
        self.status_bar.showMessage(message)
