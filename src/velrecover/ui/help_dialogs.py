import os
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QRadioButton, QButtonGroup, QFileDialog,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QApplication,
    QPushButton, QGroupBox, QScrollArea, QWidget, QDialog, QDialogButtonBox,
    QFrame
)

from .. import __version__


class AboutDialog(QDialog):
    """Dialog displaying information about the application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About VelRecover")
        
        # Fix window sizing and positioning
        screen = QApplication.primaryScreen().geometry()
        screen_width = min(screen.width(), 1920)
        screen_height = min(screen.height(), 1080)
        window_width = int(screen_width * 0.3)
        window_height = int(screen_height * 0.4)  # Smaller height
        pos_x = (screen_width - window_width) // 2
        pos_y = (screen_height - window_height) // 2
        self.setGeometry(pos_x, pos_y, window_width, window_height)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # App logo placeholder
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        # Title with better styling
        title = QLabel("VelRecover")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        
        # Version and copyright info with better styling
        version_label = QLabel(f"Version {__version__}")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        copyright = QLabel("© 2025")
        copyright.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Description text with better styling
        description = QLabel(
            "A Python tool for loading, editing, interpolating,\n"
            "and saving velocity fields."
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # License info with styled frame
        license_frame = QFrame()
        license_layout = QVBoxLayout(license_frame)
        
        license_info = QLabel("Released under the MIT License")
        license_info.setAlignment(Qt.AlignCenter)
        license_layout.addWidget(license_info)
        
        layout.addWidget(license_frame)
        layout.addStretch()
        
        # Button styling
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class FirstRunDialog(QDialog):
    """Dialog shown on first run to configure application settings."""
    
    def __init__(self, parent=None, default_location=None):
        super().__init__(parent)
        self.selected_location = default_location
        self.custom_location = None
        
        self.setWindowTitle("Welcome to VelRecover")
        screen = QApplication.primaryScreen().geometry()
        screen_width = min(screen.width(), 1920)
        screen_height = min(screen.height(), 1080)
        window_width = int(screen_width * 0.3)
        window_height = int(screen_height * 0.45)  # Slightly taller for better spacing
        pos_x = (screen_width - window_width) // 2
        pos_y = (screen_height - window_height) // 2
        self.setGeometry(pos_x, pos_y, window_width, window_height)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Welcome heading with improved styling
        welcome_label = QLabel("Welcome to VelRecover!", self)
        welcome_label.setFont(QFont("Arial", 20, QFont.Bold))
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Description with improved styling
        description = QLabel(
            "Choose where you'd like to store your data files.\n"
            "You can change this later in the application settings.", 
            self
        )
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        
        # Separator line for visual organization
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Location options group with improved styling
        location_group = QGroupBox("Data Storage Location", self)
        location_layout = QVBoxLayout(location_group)
        location_layout.setSpacing(12)
        
        # Radio button group with improved styling
        self.location_btn_group = QButtonGroup(self)
        
        # Default location option (from appdirs)
        self.default_radio = QRadioButton("Default location (system-managed)", self)
        self.default_radio.setToolTip(f"Store in: {self.selected_location}")
        self.location_btn_group.addButton(self.default_radio, 1)
        location_layout.addWidget(self.default_radio)
        
        # Documents folder option
        documents_path = os.path.join(os.path.expanduser("~"), "Documents", "VelRecover")
        self.documents_radio = QRadioButton(f"Documents folder: {documents_path}", self)
        self.location_btn_group.addButton(self.documents_radio, 2)
        location_layout.addWidget(self.documents_radio)
        
        # Custom location option
        custom_layout = QHBoxLayout()
        self.custom_radio = QRadioButton("Custom location:", self)
        self.location_btn_group.addButton(self.custom_radio, 3)
        custom_layout.addWidget(self.custom_radio)
        
        self.browse_btn = QPushButton("Browse...", self)
        self.browse_btn.setFixedWidth(100)
        self.browse_btn.clicked.connect(self.browse_location)
        custom_layout.addWidget(self.browse_btn)
        
        location_layout.addLayout(custom_layout)
        
        # Selected path display with styled frame
        path_frame = QFrame()
        path_layout = QVBoxLayout(path_frame)
        path_layout.setContentsMargins(8, 8, 8, 8)
        
        self.path_label = QLabel("No custom location selected", self)
        self.path_label.setWordWrap(True)
        path_layout.addWidget(self.path_label)
        
        location_layout.addWidget(path_frame)
        layout.addWidget(location_group)
        
        # Info text with styled frame
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        
        info_text = QLabel(
            "After selecting a location, the application will create necessary folders to store "
            "your velocity data, models, and export files.", 
            self
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_frame)
        
        # Add spacer
        layout.addStretch()
        
        # Buttons with improved styling
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.continue_btn = QPushButton("Continue", self)
        self.continue_btn.setFixedSize(120, 36)
        self.continue_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.continue_btn)
        
        layout.addLayout(button_layout)
        
        # Set default selection
        self.default_radio.setChecked(True)
        self.location_btn_group.buttonClicked.connect(self.update_selection)
    
    def browse_location(self):
        """Open file dialog to select custom location."""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Directory for VelRecover Data",
            os.path.expanduser("~")
        )
        
        if directory:
            self.custom_location = os.path.join(directory, "VelRecover")
            self.path_label.setText(f"Selected: {self.custom_location}")
            self.custom_radio.setChecked(True)
            self.update_selection(self.custom_radio)
    
    def update_selection(self, button):
        """Update the selected location based on radio button choice."""
        if button == self.default_radio:
            self.selected_location = self.selected_location
            self.path_label.setText("Using system default location")
        elif button == self.documents_radio:
            self.selected_location = os.path.join(os.path.expanduser("~"), "Documents", "VelRecover")
            self.path_label.setText(f"Selected: {self.selected_location}")
        elif button == self.custom_radio and self.custom_location:
            self.selected_location = self.custom_location
            self.path_label.setText(f"Selected: {self.custom_location}")
    
    def get_selected_location(self):
        """Return the user's selected location."""
        return self.selected_location