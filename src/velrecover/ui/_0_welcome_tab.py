"""Welcome tab for VelRecover application."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QHBoxLayout, QFrame, QSizePolicy
)

class WelcomeTab(QWidget):
    """Welcome tab providing an overview of VelRecover."""
    
    # Signal to start a new velocity field
    newVelocityRequested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("welcome_tab")
        
        # Set up the user interface
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Welcome header
        header = QLabel("Welcome to VelRecover")
        header.setObjectName("welcome_header")
        layout.addWidget(header)

        # Instruction text
        instruction = QLabel("VelRecover helps you load, edit, interpolate, and save velocity fields.")
        instruction.setObjectName("description_label")
        instruction.setWordWrap(True)
        layout.addWidget(instruction)
        
        # Workflow section
        workflow_container = QFrame()
        workflow_container.setObjectName("workflow_container")
        workflow_layout = QVBoxLayout(workflow_container)
        
        workflow_header = QLabel("Workflow")
        workflow_header.setObjectName("section_header")
        workflow_layout.addWidget(workflow_header)
        
        workflow_steps = [
            "1. Load velocity data from SEGY files or text formats",
            "2. Edit and clean velocity data",
            "3. Apply interpolation methods to create complete velocity fields",
            "4. Save results to your preferred format"
        ]
        
        for step in workflow_steps:
            step_label = QLabel(step)
            step_label.setWordWrap(True)
            workflow_layout.addWidget(step_label)
        
        layout.addWidget(workflow_container)
        
        # Get started button
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 20, 0, 0)
        
        start_button = QPushButton("Start New Velocity Field")
        start_button.setObjectName("primary_button")
        start_button.clicked.connect(self.newVelocityRequested.emit)
        button_layout.addWidget(start_button)
        button_layout.addStretch()
        
        layout.addWidget(button_container)
        
        # Add stretch to push content to the top
        layout.addStretch()