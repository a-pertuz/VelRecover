"""Dialogs for the velrecover application."""

__version__ = "1.1.0"

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QRadioButton, QButtonGroup,
    QFileDialog, QScrollArea, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QDialogButtonBox

class FirstRunDialog(QDialog):
    """Dialog shown on first run to configure application settings."""
    
    def __init__(self, parent=None, default_location=None):
        """Initialize the dialog with the default storage location."""
        super().__init__(parent)
        self.selected_location = default_location
        self.custom_location = None
        
        self.setWindowTitle("Welcome to velrecover")
        self.resize(600, 400)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Welcome heading
        welcome_label = QLabel("Welcome to velrecover!", self)
        welcome_label.setFont(QFont("Arial", 18, QFont.Bold))
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Description
        description = QLabel(
            "Choose where you'd like to store your data files.\n"
            "You can change this later in the application settings.\n", 
            self
        )
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        layout.addSpacing(20)
        
        # Location options group
        location_group = QGroupBox("Data Storage Location", self)
        location_layout = QVBoxLayout()
        
        # Radio button group
        self.location_btn_group = QButtonGroup(self)
        
        # Default location option (from appdirs)
        self.default_radio = QRadioButton("Default location (system-managed)", self)
        self.default_radio.setToolTip(f"Store in: {self.selected_location}")
        self.location_btn_group.addButton(self.default_radio, 1)
        location_layout.addWidget(self.default_radio)
        
        # Documents folder option
        documents_path = os.path.join(os.path.expanduser("~"), "Documents", "velrecover")
        self.documents_radio = QRadioButton(f"Documents folder: {documents_path}", self)
        self.location_btn_group.addButton(self.documents_radio, 2)
        location_layout.addWidget(self.documents_radio)
        
        # Custom location option
        custom_layout = QHBoxLayout()
        self.custom_radio = QRadioButton("Custom location: " , self)
        self.location_btn_group.addButton(self.custom_radio, 3)
        custom_layout.addWidget(self.custom_radio)
        
        self.browse_btn = QPushButton("Browse...", self)
        self.browse_btn.clicked.connect(self.browse_location)
        custom_layout.addWidget(self.browse_btn)
        
        location_layout.addLayout(custom_layout)
        
        # Selected path display
        self.path_label = QLabel("", self)
        location_layout.addWidget(self.path_label)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.continue_btn = QPushButton("Continue", self)
        self.continue_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.continue_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Set default selection
        self.default_radio.setChecked(True)
        self.location_btn_group.buttonClicked.connect(self.update_selection)
    
    def browse_location(self):
        """Open file dialog to select custom location."""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Directory for velrecover Data",
            os.path.expanduser("~")
        )
        
        if (directory):
            self.custom_location = os.path.join(directory, "velrecover")
            self.path_label.setText(f"Selected: {self.custom_location}")
            self.custom_radio.setChecked(True)
            self.update_selection(self.custom_radio)
    
    def update_selection(self, button):
        """Update the selected location based on radio button choice."""
        if button == self.default_radio:
            self.selected_location = self.selected_location
        elif button == self.documents_radio:
            self.selected_location = os.path.join(os.path.expanduser("~"), "Documents", "velrecover")
        elif button == self.custom_radio and self.custom_location:
            self.selected_location = self.custom_location
    
    def get_selected_location(self):
        """Return the user's selected location."""
        return self.selected_location

class AboutDialog(QDialog):
    """Dialog displaying information about the application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("About velrecover")
        
        # Calculate window size and position
        screen = QApplication.primaryScreen().geometry()
        screen_width = min(screen.width(), 1920)
        screen_height = min(screen.height(), 1080)
        window_width = int(screen_width * 0.3)
        window_height = int(screen_height * 0.5)
        pos_x = (screen_width - window_width) // 2
        pos_y = (screen_height - window_height) // 2
        self.setGeometry(pos_x, pos_y, window_width, window_height)
        
        layout = QVBoxLayout(self)
        
        # App title
        title = QLabel("velrecover")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        
        # Version and copyright info
        __version__ = "0.6.5"
        version = QLabel(f"Version {__version__}")
        version.setAlignment(Qt.AlignCenter)
        
        copyright = QLabel("© 2025 Alejandro Pertuz")
        copyright.setAlignment(Qt.AlignCenter)
        
        # Description text
        description = QLabel(
            "A tool for interpolating 2D seismic velocity data from sparse velocity analysis found in images of seismic sections."
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        
        # License info
        license_info = QLabel("Released under the GPL-3.0 License")
        license_info.setAlignment(Qt.AlignCenter)
        
        # Add all widgets to layout
        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(copyright)
        layout.addSpacing(10)
        layout.addWidget(description)
        layout.addSpacing(20)
        layout.addWidget(license_info)
        
        # Add OK button at bottom
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

class HelpDialog(QDialog):
    """Help dialog with information about the application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How to Use velrecover")    
        screen = QApplication.primaryScreen().geometry()
        screen_width = min(screen.width(), 1920)
        screen_height = min(screen.height(), 1080)
        pos_x = int(screen_width * 0.45 + 20)
        pos_y = int(screen_height * 0.15)
        window_width= int(screen_width * 0.3)
        window_height = int(screen_height * 0.85)
        self.setGeometry(pos_x, pos_y, window_width, window_height)          
        # Create scroll area
        scroll = QWidget()
        scroll_layout = QVBoxLayout(scroll)
        
        # Add content
        msg = """
        <h2>velrecover Tutorial</h2>
        
        <p><b>velrecover</b> is a tool for interpolating 2D seismic velocity data from sparse velocity analysis.</p>

        <h2>Visualization Controls</h2>
        <p>The application provides a set of tools to navigate and interact with the velocity data:</p>
        <h3>Navigation Toolbar</h3>
        <ul>
            <li>🏠 <b>Home:</b> Reset view to original display</li>
            <li>⬅️ <b>Back:</b> Previous view</li>
            <li>➡️ <b>Forward:</b> Next view</li>
            <li>✋ <b>Pan:</b> Left click and drag to move around</li>
            <li>🔍 <b>Zoom:</b> Left click and drag to zoom into a rectangular region</li>
            <li>⚙️ <b>Configure:</b> Configure plot settings</li>
            <li>💾 <b>Save:</b> Save the figure</li>
        </ul>
        
        <h2>velrecover Workflow</h2>
        <p>The application follows a step-by-step process to interpolate velocity data:</p>

        <h3>Step 1: Load Velocity Data</h3>
        <ul>
            <li>Click "Load Data" to select a velocity text file (*.dat *.txt *.tsv *.csv)</li>
            <li>The program expects a 3-column format: CDP, TWT, Velocity</li>
        </ul>

        <h3>Step 2: Load SEGY File</h3>
        <ul>
            <li>Click "Load SEGY" to select a seismic file (.sgy, .segy)</li>
            <li>The seismic section provides context for velocity analysis</li>
            <li>The SEGY file should correspond to the same seismic line as your velocity data</li>
        </ul>

        <h3>Step 3: Interpolate and Visualize</h3>
        <ul>
            <li>Click the "Interpolate" button to process the data</li>
            <li>View the results immediately in the visualization panel</li>
            <li>The interpolated velocity model will be displayed as a color-coded map</li>
            <li>Original velocity picks are shown as control points</li>
        </ul>

        <h3>Step 4: Apply Smoothing</h3>
        <ul>
            <li>Use the "Gaussian Smooth" option if the interpolated model needs smoothing</li>
        </ul>

        <h3>Step 5: Save Results</h3>
        <ul>
            <li>Click "Save Data" to export the interpolated velocity model</li>
            <li>Choose from available formats:
                <ul>
                    <li>Text file (.txt) - saves X, Y coordinates from SEGY file and CDP, TWT, VEL values </li>
                    <li>Binary file (.bin) - saves velocity data in a grid (TWT,CDP) in float 32 format, suitable for migration in Seismic Unix </li>
                </ul>
            </li>
            <li>Select a destination folder for your output files</li>
        </ul>

        <h3>Step 3: Run Interpolation</h3>
        <ul>
            <li>Click "Interpolate" to process the data</li>
            <li>The interpolation algorithm will fill gaps between sparse velocity picks</li>
        </ul>

        <h3>Step 4: Visualize Results</h3>
        <ul>
            <li>View the interpolated velocity model as:
                <ul>
                    <li>Color-coded velocity map</li>
                    <li>Contour lines of equal velocity</li>
                    <li>3D surface plot</li>
                </ul>
            </li>
            <li>Compare with original velocity picks</li>
            <li>Adjust display properties (color map, scaling, etc.)</li>
        </ul>

        <h3>Step 5: Export Results</h3>
        <ul>
            <li>Save interpolated velocity model in various formats:
                <ul>
                    <li>2D velocity file (.vel)</li>
                    <li>ASCII table</li>
                    <li>Image file (PNG, JPG)</li>
                </ul>
            </li>
            <li>Export statistics and quality metrics</li>
        </ul>

        <h3>File Structure</h3>
        <ul>
            <li><b>VELS/RAW/</b>: Store input raw velocity files</li>
            <li><b>VELS/2D/</b>: Store interpolated 2D velocity models</li>
            <li><b>SEGY/</b>: Store associated SEGY files for context</li>
        </ul>
        
        """
        
        # Create text label with HTML content
        text = QLabel(msg)
        text.setWordWrap(True)
        text.setTextFormat(Qt.RichText)
        scroll_layout.addWidget(text)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll)
        scroll_area.setWidgetResizable(True)
        
        # Create main layout
        layout = QVBoxLayout(self)
        layout.addWidget(scroll_area)
        
        # Add OK button at bottom
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)