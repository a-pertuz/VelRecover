"""Welcome tab for VelRecover application."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QHBoxLayout, QFrame, QSizePolicy, QSpacerItem
)
from .help_dialogs import AboutDialog, HelpDialog

from .. import __version__

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
        
        # Header section with logo placeholder and buttons
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        
        # Title and version in center
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        
        header = QLabel("VelRecover")
        header.setObjectName("title_label")
        header.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(header)
        
        version = QLabel(f"Version {__version__}")
        version.setObjectName("version_label")
        version.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(version)
        
        header_layout.addWidget(title_container, 1)  # 1 = stretch factor
        
        # Info button section
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setSpacing(8)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # Help button
        help_button = QPushButton("Help")
        help_button.setObjectName("help_button")
        help_button.setFixedSize(100, 32)
        help_button.clicked.connect(self._show_help)
        info_layout.addWidget(help_button)
        
        # About button
        about_button = QPushButton("About")
        about_button.setObjectName("about_button")
        about_button.setFixedSize(100, 32)
        about_button.clicked.connect(self._show_about)
        info_layout.addWidget(about_button)
        
        header_layout.addWidget(info_container)
        layout.addWidget(header_container)
        
        # Description text
        instruction = QLabel("VelRecover helps you load, edit, interpolate, and save velocity models from sparse velocity picks often found in seismic section paper copies.")
        instruction.setObjectName("description_label")
        instruction.setWordWrap(True)
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setContentsMargins(0, 10, 0, 10)
        layout.addWidget(instruction)

        # Features section
        features_frame = QFrame()
        features_frame.setObjectName("features_frame")
        features_layout = QVBoxLayout(features_frame)
        
        features_title = QLabel("Key Features:")
        features_title.setObjectName("section_label")
        features_layout.addWidget(features_title)
        
        features_label = QLabel(
            "• Import velocity data from SEGY files or text formats\n"
            "• Interactive velocity field editing and cleaning\n"
            "• Multiple interpolation methods for data completion\n"
            "• Visualization of velocity field data\n"
            "• Export to various industry-standard formats"
        )
        features_label.setObjectName("features_label")        
        features_layout.addWidget(features_label)

        layout.addWidget(features_frame)

        # Quick start and workflow hints
        workflow_container = QFrame()
        workflow_container.setObjectName("workflow_container")
        workflow_layout = QVBoxLayout(workflow_container)

        workflow_title = QLabel("Quick Start:")
        workflow_title.setObjectName("section_label")
        workflow_layout.addWidget(workflow_title)
        
        workflow_text = QLabel(
            "1. Load velocity data from SEGY files or text formats\n"
            "2. Edit and clean velocity data\n"
            "3. Apply interpolation methods to create complete velocity fields\n"
            "4. Save results to your preferred format"
        )
        workflow_text.setObjectName("workflow_steps")
        workflow_layout.addWidget(workflow_text)
        
        layout.addWidget(workflow_container)
        
        # Get started button with centered layout
        button_container = QWidget()
        button_container.setObjectName("button_container")
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 20, 0, 0)
        
        # Add spacer to push button to center
        button_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        start_button = QPushButton("Start New Velocity Field")
        start_button.setObjectName("primary_button")
        start_button.setMinimumWidth(200)
        start_button.setMinimumHeight(50)
        start_button.clicked.connect(self.newVelocityRequested.emit)
        button_layout.addWidget(start_button)
        
        # Add spacer to push button to center
        button_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        layout.addWidget(button_container)
        
        # Add stretch to push content to the top
        layout.addStretch()
    
    def _show_help(self):
        """Show the help dialog."""
        help_dialog = HelpDialog(self)
        help_dialog.exec()
    
    def _show_about(self):
        """Show the about dialog."""
        about_dialog = AboutDialog(self)
        about_dialog.exec()