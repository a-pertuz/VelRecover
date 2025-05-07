"""Tab container for VelRecover application."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QStackedWidget

class TabContainer(QStackedWidget):
    """Container for tab content that shows one tab at a time."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tab_container")
        
        # Dictionary to store tab indices by identifier
        self.tab_indices = {}
    
    def add_tab(self, identifier, widget):
        """Add a new tab to the container with the given identifier."""
        # Add the widget to the stacked widget
        index = self.addWidget(widget)
        
        # Store the index for later reference
        self.tab_indices[identifier] = index
        
        return index
    
    def switch_to(self, identifier):
        """Switch to the tab with the given identifier."""
        if identifier in self.tab_indices:
            self.setCurrentIndex(self.tab_indices[identifier])
            return True
        return False