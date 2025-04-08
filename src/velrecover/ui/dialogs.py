"""Dialogs for the velrecover application."""

__version__ = "1.1.0"

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QRadioButton, QButtonGroup,
    QFileDialog, QScrollArea, QWidget, QDialogButtonBox, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QDoubleValidator
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QMessageBox

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

class CustomLinearModelDialog(QDialog):
    """Dialog for entering custom linear velocity model parameters."""
    
    def __init__(self, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        
        # Set dialog properties
        self.setWindowTitle("Custom Linear Model Parameters")
        self.setMinimumWidth(350)
        self.setModal(True)
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Add title
        title = QLabel("Enter Linear Model Parameters")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Add explanation
        description = QLabel(
            "Enter parameters for the linear velocity model:\nV = V₀ + k·TWT"
        )
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        layout.addSpacing(10)
        
        # Parameters form
        form_layout = QVBoxLayout()
        
        # V₀ parameter
        v0_layout = QHBoxLayout()
        v0_label = QLabel("V₀ (initial velocity in m/s):", self)
        self.v0_input = QLineEdit(self)
        self.v0_input.setText("1500")  # Default value
        self.v0_input.setValidator(QDoubleValidator(0, 10000, 2))
        v0_layout.addWidget(v0_label)
        v0_layout.addWidget(self.v0_input)
        form_layout.addLayout(v0_layout)
        
        # k parameter
        k_layout = QHBoxLayout()
        k_label = QLabel("k (velocity gradient):", self)
        self.k_input = QLineEdit(self)
        self.k_input.setText("0.5")  # Default value
        
        # Use a double validator with 6 decimals to allow small values
        k_validator = QDoubleValidator(0.0, 100.0, 6)
        k_validator.setNotation(QDoubleValidator.StandardNotation)  # Force standard notation
        self.k_input.setValidator(k_validator)
        
        k_layout.addWidget(k_label)
        k_layout.addWidget(self.k_input)
        form_layout.addLayout(k_layout)
        
        layout.addLayout(form_layout)
        
        # Add explanation of parameters
        explanation = QLabel(
            "• V₀: Initial velocity at zero TWT (typically 1500-2000 m/s)\n"
            "• k: Velocity gradient (typically 0.2-1.0)\n"
            "  Small k values (e.g., 0.01) produce a gentle slope"
        )
        explanation.setStyleSheet("font-size: 10px; color: #555;")
        layout.addWidget(explanation)
        
        layout.addSpacing(10)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_parameters(self):
        """Return the entered parameters."""
        try:
            v0 = float(self.v0_input.text())
            k = float(self.k_input.text())
            return v0, k
        except ValueError:
            return 1500, 0.5  # Default values in case of parse error

class CustomLogarithmicModelDialog(QDialog):
    """Dialog for entering custom logarithmic velocity model parameters."""
    
    def __init__(self, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        
        # Set dialog properties
        self.setWindowTitle("Custom Logarithmic Model Parameters")
        self.setMinimumWidth(350)
        self.setModal(True)
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Add title
        title = QLabel("Enter Logarithmic Model Parameters")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Add explanation
        description = QLabel(
            "Enter parameters for the logarithmic velocity model:\nV = V₀ + k·ln(TWT)"
        )
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        layout.addSpacing(10)
        
        # Parameters form
        form_layout = QVBoxLayout()
        
        # V₀ parameter
        v0_layout = QHBoxLayout()
        v0_label = QLabel("V₀ (initial velocity in m/s):", self)
        self.v0_input = QLineEdit(self)
        self.v0_input.setText("1500")  # Default value
        self.v0_input.setValidator(QDoubleValidator(0, 10000, 2))
        v0_layout.addWidget(v0_label)
        v0_layout.addWidget(self.v0_input)
        form_layout.addLayout(v0_layout)
        
        # k parameter
        k_layout = QHBoxLayout()
        k_label = QLabel("k (logarithmic scaling factor):", self)
        self.k_input = QLineEdit(self)
        self.k_input.setText("1000")  # Default value
        
        # Use a double validator with 1 decimal places
        k_validator = QDoubleValidator(0.0, 10000.0, 1)
        k_validator.setNotation(QDoubleValidator.StandardNotation)  # Force standard notation
        self.k_input.setValidator(k_validator)
        
        k_layout.addWidget(k_label)
        k_layout.addWidget(self.k_input)
        form_layout.addLayout(k_layout)
        
        layout.addLayout(form_layout)
        
        # Add explanation of parameters
        explanation = QLabel(
            "• V₀: Initial velocity at theoretical zero TWT (typically 1500-2000 m/s)\n"
            "• k: Logarithmic scaling factor (typically 500-2000)\n"
            "  Higher k values produce steeper velocity increases with depth"
        )
        explanation.setStyleSheet("font-size: 10px; color: #555;")
        layout.addWidget(explanation)
        
        layout.addSpacing(10)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_parameters(self):
        """Return the entered parameters."""
        try:
            v0 = float(self.v0_input.text())
            k = float(self.k_input.text())
            return v0, k
        except ValueError:
            return 1500, 1000  # Default values in case of parse error

class ModelSelectionDialog(QDialog):
    """Dialog for selecting the interpolation method for velocity data."""
    
    def __init__(self, parent=None, already_interpolated=False):
        """Initialize the dialog with interpolation method selection options."""
        super().__init__(parent)
        
        # Set dialog properties
        self.setWindowTitle("Select Interpolation Method")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        # Track if data was already interpolated
        self.already_interpolated = already_interpolated
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Add title
        title = QLabel("Select Interpolation Method")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Add description
        if self.already_interpolated:
            description = QLabel(
                "Your data has already been interpolated. Running a new interpolation\n"
                "will replace the current results. Are you sure you want to continue?"
            )
            description.setStyleSheet("color: #E03C31;")  # Red color
        else:
            description = QLabel(
                "Select the interpolation method to use for velocity modeling.\n"
                "Different methods have different characteristics and trade-offs."
            )
        
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        layout.addSpacing(10)
        
        # Create radio button group for all methods
        self.method_btn_group = QButtonGroup(self)
        
        # FIRST CATEGORY: Interpolation Methods group
        interp_group = QGroupBox("Interpolation Methods")
        interp_layout = QVBoxLayout()
        
        # RBF interpolation option (default)
        self.rbf_radio = QRadioButton("Radial Basis Function (RBF)", self)
        self.rbf_radio.setToolTip("Smooth interpolation that passes through all data points")
        self.method_btn_group.addButton(self.rbf_radio, 1)
        interp_layout.addWidget(self.rbf_radio)
        
        # Two-step interpolation option
        self.two_step_radio = QRadioButton("Two-Step Interpolation", self)
        self.two_step_radio.setToolTip("First extrapolate each CDP using RBF, then interpolate between CDPs")
        self.method_btn_group.addButton(self.two_step_radio, 6)
        interp_layout.addWidget(self.two_step_radio)
        
        interp_group.setLayout(interp_layout)
        layout.addWidget(interp_group)
        
        # SECOND CATEGORY: Build New Model group
        model_group = QGroupBox("Build New Model")
        model_layout = QVBoxLayout()
        
        # Custom linear model option
        self.custom_linear_radio = QRadioButton("Custom Linear Model (V = V₀ + k·TWT)", self)
        self.custom_linear_radio.setToolTip("Apply a linear velocity model with custom parameters")
        self.method_btn_group.addButton(self.custom_linear_radio, 2)
        model_layout.addWidget(self.custom_linear_radio)
        
        # Best fit linear model option
        self.best_linear_radio = QRadioButton("Best Fit Linear Model (V = V₀ + k·TWT)", self)
        self.best_linear_radio.setToolTip("Find the best linear model that fits all data points")
        self.method_btn_group.addButton(self.best_linear_radio, 3)
        model_layout.addWidget(self.best_linear_radio)
        
        # Custom logarithmic model option
        self.custom_log_radio = QRadioButton("Custom Logarithmic Model (V = V₀ + k·ln(TWT))", self)
        self.custom_log_radio.setToolTip("Apply a logarithmic velocity model with custom parameters")
        self.method_btn_group.addButton(self.custom_log_radio, 4)
        model_layout.addWidget(self.custom_log_radio)
        
        # Best fit logarithmic model option
        self.best_log_radio = QRadioButton("Best Fit Logarithmic Model (V = V₀ + k·ln(TWT))", self)
        self.best_log_radio.setToolTip("Find the best logarithmic model that fits all data points")
        self.method_btn_group.addButton(self.best_log_radio, 5)
        model_layout.addWidget(self.best_log_radio)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Add explanation
        explanation = QLabel(
            "Method characteristics:\n"
            "• Interpolation Methods: Generate a model that preserves velocity pick values\n"
            "  - RBF: Classic smooth interpolation preserving all data points\n"
            "  - Two-Step: Extrapolate per CDP then interpolate between CDPs\n\n"
            "• Build New Model: Create a new velocity trend based on mathematical functions\n"
            "  - Custom Linear: Manually specify V₀ and k parameters\n"
            "  - Best Fit Linear: Find optimal V₀ and k parameters with best R² fit\n"
            "  - Custom Logarithmic: Manually specify V₀ and k parameters for logarithmic model\n"
            "  - Best Fit Logarithmic: Find optimal logarithmic curve with best R² fit"
        )
        explanation.setStyleSheet("font-size: 10px; color: #555;")
        layout.addWidget(explanation)
        
        layout.addSpacing(10)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set default selection
        self.rbf_radio.setChecked(True)
    
    def get_selected_method(self):
        """Return the selected interpolation method."""
        if self.rbf_radio.isChecked():
            return "rbf"
        elif self.custom_linear_radio.isChecked():
            return "custom_linear"
        elif self.best_linear_radio.isChecked():
            return "best_linear"
        elif self.custom_log_radio.isChecked():
            return "custom_log"
        elif self.best_log_radio.isChecked():
            return "best_log"
        elif self.two_step_radio.isChecked():
            return "two_step"
        else:
            return "rbf"  # Default

