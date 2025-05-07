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


class HelpDialog(QDialog):
    """Help dialog with information about the application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How to Use VelRecover")    
        
        # Fix window sizing and positioning
        screen = QApplication.primaryScreen().geometry()
        screen_width = min(screen.width(), 1920)
        screen_height = min(screen.height(), 1080)
        window_width = int(screen_width * 0.4)  # Slightly wider for better readability
        window_height = int(screen_height * 0.75)  # Not too tall
        pos_x = (screen_width - window_width) // 2
        pos_y = (screen_height - window_height) // 2
        self.setGeometry(pos_x, pos_y, window_width, window_height)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("VelRecover Help Guide")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(title)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        
        main_layout.addWidget(header_container)
        main_layout.addWidget(separator)
        
        # Create scroll area with custom styling
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Content widget with styled sections
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(5, 10, 15, 10)  # Adjusted for scrollbar
        
        # Introduction section
        intro_frame = self._create_section_frame()
        intro_layout = QVBoxLayout(intro_frame)
        
        intro_title = QLabel("Introduction")
        intro_title.setFont(QFont("Arial", 14, QFont.Bold))
        intro_layout.addWidget(intro_title)
        
        intro_text = QLabel(
            "<p><b>VelRecover</b> is a tool designed to load, edit, interpolate, "
            "and save velocity fields. This guide will help you use the application effectively.</p>"
        )
        intro_text.setTextFormat(Qt.RichText)
        intro_text.setWordWrap(True)
        intro_layout.addWidget(intro_text)
        
        content_layout.addWidget(intro_frame)
        
        # Navigation section
        nav_frame = self._create_section_frame()
        nav_layout = QVBoxLayout(nav_frame)
        
        nav_title = QLabel("Navigation Controls")
        nav_title.setFont(QFont("Arial", 14, QFont.Bold))
        nav_layout.addWidget(nav_title)
        
        nav_text = QLabel(
            "<p>The application provides navigation tools in each tab:</p>"
            "<h4 style='margin-top: 10px; margin-bottom: 6px;'>Navigation Panel</h4>"
            "<p>Use the left-side navigation panel to switch between the main workflow stages.</p>"
            "<h4 style='margin-top: 10px; margin-bottom: 6px;'>Visualization Toolbar</h4>"
            "<ul style='margin-top: 0px;'>"
            "<li>🏠 <b>Home:</b> Reset view to original display</li>"
            "<li>✋ <b>Pan:</b> Left click and drag to move around</li>"
            "<li>🔍 <b>Zoom:</b> Left click and drag to zoom into a rectangular region</li>"
            "<li>💾 <b>Save:</b> Save the figure</li>"
            "</ul>"
            "<p>In edit mode, you can click on the canvas to add, edit, or delete velocity points.</p>"
        )
        nav_text.setTextFormat(Qt.RichText)
        nav_text.setWordWrap(True)
        nav_layout.addWidget(nav_text)
        
        content_layout.addWidget(nav_frame)
        
        # Workflow section
        workflow_frame = self._create_section_frame()
        workflow_layout = QVBoxLayout(workflow_frame)
        
        workflow_title = QLabel("VelRecover Workflow")
        workflow_title.setFont(QFont("Arial", 14, QFont.Bold))
        workflow_layout.addWidget(workflow_title)
        
        workflow_text = QLabel(
            "<p>The application follows a step-by-step process through a series of tabs:</p>"
            
            "<h4 style='margin-top: 15px; margin-bottom: 6px;'>Welcome Tab</h4>"
            "<ul style='margin-top: 0px;'>"
            "<li>Overview of VelRecover features</li>"
            "<li>Click \"Start New Velocity Field\" to begin</li>"
            "<li>Access help and about information</li>"
            "</ul>"
            
            "<h4 style='margin-top: 15px; margin-bottom: 6px;'>1. Load Data Tab</h4>"
            "<ul style='margin-top: 0px;'>"
            "<li>Load both a SEGY file and a velocity data file</li>"
            "<li>The SEGY file provides the seismic data context</li>"
            "<li>The velocity file contains the actual velocity picks</li>"
            "<li>Preview the imported data on the display</li>"
            "<li>Click \"Show Velocity Distribution\" to analyze velocity trends</li>"
            "<li>Click \"Next\" to proceed to the Edit tab</li>"
            "</ul>"
            
            "<h4 style='margin-top: 15px; margin-bottom: 6px;'>2. Edit Tab</h4>"
            "<ul style='margin-top: 0px;'>"
            "<li>View and modify velocity field points</li>"
            "<li>Time Shift: Apply time shift to all velocity picks</li>"
            "<li>Custom Velocity Picks:</li>"
            "<ul>"
            "<li><b>New:</b> Add new velocity picks by clicking on the display</li>"
            "<li><b>Edit:</b> Modify existing velocity values</li>"
            "<li><b>Delete:</b> Remove unwanted velocity picks</li>"
            "</ul>"
            "<li>History: Use Undo/Redo buttons to manage your edits</li>"
            "<li>Click \"Save Edits\" to save your changes</li>"
            "<li>Or \"Continue Without Edits\" to proceed without saving</li>"
            "<li>Click \"Next\" to go to the Interpolation tab</li>"
            "</ul>"
            
            "<h4 style='margin-top: 15px; margin-bottom: 6px;'>3. Interpolation Tab</h4>"
            "<ul style='margin-top: 0px;'>"
            "<li>Choose from multiple interpolation methods:</li>"
            "<ul>"
            "<li>Linear Best Fit</li>"
            "<li>Linear Custom</li>"
            "<li>Logarithmic Best Fit</li>"
            "<li>Logarithmic Custom</li>"
            "<li>RBF Interpolation</li>"
            "<li>Two-Step Method</li>"
            "</ul>"
            "<li>Configure method-specific parameters</li>"
            "<li>Optional: Apply Gaussian Blur for smoothing</li>"
            "<li>Click \"Run Interpolation\" to execute the selected method</li>"
            "<li>Click \"Reset\" to undo interpolation and try a different method</li>"
            "<li>View velocity distribution with the \"Show Velocity Distribution\" button</li>"
            "<li>Save interpolation results in Text or Binary format</li>"
            "</ul>"
        )
        workflow_text.setTextFormat(Qt.RichText)
        workflow_text.setWordWrap(True)
        workflow_layout.addWidget(workflow_text)
        
        content_layout.addWidget(workflow_frame)
        
        # File Structure section
        file_frame = self._create_section_frame()
        file_layout = QVBoxLayout(file_frame)
        
        file_title = QLabel("File Structure")
        file_title.setFont(QFont("Arial", 14, QFont.Bold))
        file_layout.addWidget(file_title)
        
        file_text = QLabel(
            "<p>VelRecover organizes data in the following folders:</p>"
            "<ul>"
            "<li><b>SEGY/</b>: Store SEGY seismic data files</li>"
            "<li><b>VELS/</b>: Root folder for velocity data</li>"
            "<ul>"
            "<li><b>VELS/RAW/</b>: Original velocity data files</li>"
            "<li><b>VELS/CUSTOM/</b>: Edited velocity files</li>"
            "<li><b>VELS/INTERPOLATED/TXT/</b>: Text format interpolation results</li>"
            "<li><b>VELS/INTERPOLATED/BIN/</b>: Binary format interpolation results</li>"
            "</ul>"
            "</ul>"
            "<p>You can change the data directory in File > Set Data Directory.</p>"
        )
        file_text.setTextFormat(Qt.RichText)
        file_text.setWordWrap(True)
        file_layout.addWidget(file_text)
        
        content_layout.addWidget(file_frame)
        
        # Data Formats section
        format_frame = self._create_section_frame()
        format_layout = QVBoxLayout(format_frame)
        
        format_title = QLabel("Data Formats")
        format_title.setFont(QFont("Arial", 14, QFont.Bold))
        format_layout.addWidget(format_title)
        
        format_text = QLabel(
            "<p><b>Input Formats:</b></p>"
            "<ul>"
            "<li>SEGY files (.segy, .sgy): Standard seismic data format</li>"
            "<li>Velocity data (.dat, .txt): Tab, comma, or space-delimited text files with columns for trace, time, and velocity</li>"
            "</ul>"
            "<p><b>Output Formats:</b></p>"
            "<ul>"
            "<li>Text format (.dat): Delimited text files for interoperability</li>"
            "<li>Binary format (.bin): Compact binary storage of velocity data</li>"
            "</ul>"
        )
        format_text.setTextFormat(Qt.RichText)
        format_text.setWordWrap(True)
        format_layout.addWidget(format_text)
        
        content_layout.addWidget(format_frame)
        
        # Add spacer at the bottom
        content_layout.addStretch()
        
        # Set the content widget in the scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area, 1)  # 1 = stretch factor
        
        # Button section
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.setFixedSize(100, 32)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        main_layout.addWidget(button_container)
    
    def _create_section_frame(self, bg_color="#ffffff"):
        """Create a styled frame for a help section."""
        frame = QFrame()
        return frame