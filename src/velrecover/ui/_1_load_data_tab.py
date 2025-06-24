"""Load Data tab for VelRecover application."""

import os
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSizePolicy, QFileDialog, QComboBox, QGroupBox,
    QSplitter
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from ..utils.visualization_utils import SeismicDisplayManager
from ..utils.velocity_distribution import VelocityDistributionWindow, plot_velocity_distribution
from ..utils.console_utils import (
    section_header, success_message, error_message, 
    warning_message, info_message, progress_message,
    summary_statistics
)
class SimpleNavigationToolbar(NavigationToolbar):
    """Simplified navigation toolbar with only Home, Pan and Zoom tools."""
    
    # Define which tools to keep
    toolitems = [t for t in NavigationToolbar.toolitems if t[0] in ('Home', 'Pan', 'Zoom', 'Save')]
    
    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)

class LoadDataTab(QWidget):
    """Tab for loading velocity data from various formats."""
    
    # Signal when data is loaded
    dataLoaded = Signal(str, object)
    # Signal to proceed to next step
    proceedRequested = Signal()
    
    def __init__(self, console=None, work_dir=None, parent=None):
        super().__init__(parent)
        self.setObjectName("load_data_tab")
        self.console = console
        self.work_dir = work_dir
        
        # Initialize state variables
        self.segy_file_path = None
        self.velocity_file_path = None
        self.segy_metadata = None
        
        # Create matplotlib figure for SEGY display
        self.figure = Figure(figsize=(8, 6), constrained_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Create seismic display manager
        self.display_manager = SeismicDisplayManager(self.ax, self.console)
        
        # Initialize velocity distribution window
        self.vel_dist_window = None
        
        # Set up the user interface
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Tab header
        header = QLabel("Load Data")
        header.setObjectName("tab_header")
        layout.addWidget(header)

        
        # Instruction text
        instruction = QLabel("Load velocity data and SEG-Y files. Both files are required before proceeding to the next step.")
        instruction.setObjectName("description_label")
        instruction.setWordWrap(True)
        layout.addWidget(instruction)

        # Create top section with load buttons
        buttons_section = QHBoxLayout()
        
        # SEGY file loading
        segy_group = QGroupBox("SEGY File")
        segy_layout = QVBoxLayout(segy_group)
        
        self.segy_path_label = QLabel("No file selected")
        segy_layout.addWidget(self.segy_path_label)
        
        segy_button = QPushButton("Load SEGY File")
        segy_button.clicked.connect(self._load_segy_file)
        segy_layout.addWidget(segy_button)
        
        buttons_section.addWidget(segy_group)
        
        # Velocity file loading
        velocity_group = QGroupBox("Velocity Model")
        velocity_layout = QVBoxLayout(velocity_group)
        
        self.velocity_path_label = QLabel("No file selected")
        velocity_layout.addWidget(self.velocity_path_label)
        
        velocity_button = QPushButton("Load Velocity File")
        velocity_button.clicked.connect(self._load_velocity_file)
        velocity_layout.addWidget(velocity_button)
        
        buttons_section.addWidget(velocity_group)
        layout.addLayout(buttons_section)
        
        # SEGY Display section
        display_group = QGroupBox("SEGY Display")
        display_layout = QVBoxLayout(display_group)
        
        # Add the matplotlib canvas
        display_layout.addWidget(self.canvas)
        
        # Add navigation toolbar
        toolbar = SimpleNavigationToolbar(self.canvas, self)
        display_layout.addWidget(toolbar)
        
        layout.addWidget(display_group, 1)  # Give it a stretch factor of 1
        
        # Actions
        action_layout = QHBoxLayout()
        
        # Add velocity distribution button
        self.dist_button = QPushButton("Show Velocity Distribution")
        self.dist_button.setObjectName("dist_button")
        self.dist_button.setEnabled(False)
        self.dist_button.clicked.connect(self._show_velocity_distribution)
        action_layout.addWidget(self.dist_button)
        
        action_layout.addStretch()
        
        self.next_button = QPushButton("Next")
        self.next_button.setObjectName("primary_button")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self._proceed_to_next)
        action_layout.addWidget(self.next_button)
        
        layout.addLayout(action_layout)
    
    def _load_segy_file(self):
        """Open a file dialog to select and load a SEGY file."""
        file_filter = "SEGY Files (*.segy *.sgy);;All Files (*.*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select SEGY File", 
            os.path.join(self.work_dir, "SEGY"), 
            file_filter
        )
        
        if file_path:
            try:
                # Store the file path
                self.segy_file_path = file_path
                self.segy_path_label.setText(os.path.basename(file_path))
                
                # Load the SEGY data using the display manager
                self.segy_metadata = self.display_manager.load_segy(file_path)
                
                # Update console with info
                if self.console:
                    section_header(self.console, "SEGY Data Loaded")
                    info_message(self.console, f"File: {os.path.basename(file_path)}")
                    info_message(self.console, f"Dimensions: {self.segy_metadata['ntraces']} traces x {self.segy_metadata['nsamples']} samples")
                    info_message(self.console, f"Sample rate: {self.segy_metadata['dt_ms']} ms")
                
                # Display the data
                self.display_manager.display()
                self.canvas.draw()
                
                # Check if we can enable the next button
                self._check_next_button()
                
            except Exception as e:
                self.segy_file_path = None
                self.segy_path_label.setText("Error loading file")
                if self.console:
                    error_message(self.console, f"Failed to load SEGY file: {str(e)}")
    
    def _load_velocity_file(self):
        """Open a file dialog to select and load a velocity data file."""
        file_filter = "Text Files (*.txt *.dat *.csv *.tsv);;All Files (*.*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Velocity File", 
            os.path.join(self.work_dir, "VELS", "RAW"), 
            file_filter
        )
        
        if file_path:
            try:
                # Store the file path
                self.velocity_file_path = file_path
                self.velocity_path_label.setText(os.path.basename(file_path))
                
                # Parse the velocity file
                vel_traces, vel_twts, vel_values = self._parse_velocity_file(file_path)
                
                # Load the velocity data into the display manager
                self.display_manager.load_velocity_picks(vel_traces, vel_twts, vel_values)
                
                # Update console with info
                if self.console:
                    section_header(self.console, "Velocity Data Loaded")
                    info_message(self.console, f"File: {os.path.basename(file_path)}")
                    info_message(self.console, f"Number of picks: {len(vel_traces)}")
                
                # Update the display
                self.display_manager.display()
                self.canvas.draw()
                
                # Check if we can enable the next button
                self._check_next_button()
                
            except Exception as e:
                self.velocity_file_path = None
                self.velocity_path_label.setText("Error loading file")
                if self.console:
                    error_message(self.console, f"Failed to load velocity file: {str(e)}")
    
    def _parse_velocity_file(self, file_path):
        """ Parse the velocity file with three columns: trace, twt, velocity"""
        try:
            # Load the velocity data
            # Try to auto-detect delimiter from common formats
            with open(file_path, 'r') as f:
                # Read first line to detect delimiter and check if it's a header
                first_line = f.readline().strip()
                has_header = False
                
                # Check if first line contains non-numeric characters (likely a header)
                if any(not c.isdigit() and c not in '.-+\t, ;' for c in first_line):
                    has_header = True
                
                if '\t' in first_line:
                    delimiter = '\t'  # Tab-delimited
                elif ',' in first_line:
                    delimiter = ','   # Comma-delimited
                elif ';' in first_line:
                    delimiter = ';'   # Semicolon-delimited
                else:
                    delimiter = None  # Let numpy try to figure it out (space-delimited)
            
            # Load the data using numpy, skip header row if detected
            data = np.loadtxt(file_path, delimiter=delimiter, skiprows=1 if has_header else 0)
            
            # Check if the file has three columns
            if data.shape[1] < 3:
                raise ValueError("Velocity file must have at least three columns: trace, twt, velocity")
            
            # Extract the columns
            vel_traces = data[:, 0]  # First column: trace number
            vel_twts = data[:, 1]    # Second column: two-way time
            vel_values = data[:, 2]  # Third column: velocity value
            
            if self.console:
                success_message(self.console, f"Velocity data parsed successfully: {len(vel_traces)} picks")
                
            return vel_traces, vel_twts, vel_values
                
        except Exception as e:
            if self.console:
                error_message(self.console, f"Error parsing velocity file: {str(e)}")
            raise
    
    def _check_next_button(self):
        """Check if both files are loaded and enable the next button if they are."""
        if self.segy_file_path and self.velocity_file_path:
            self.next_button.setEnabled(True)
            self.dist_button.setEnabled(True)  # Also enable distribution button
            if self.console:
                success_message(self.console, "Both files loaded. Click 'Next' to proceed.")
        else:
            self.next_button.setEnabled(False)
            self.dist_button.setEnabled(False)
            
    def _show_velocity_distribution(self):
        """Show velocity distribution in a separate window."""
        if not self.velocity_file_path:
            return
        
        try:
            # Get velocity data
            vel_traces, vel_twts, vel_values = self._parse_velocity_file(self.velocity_file_path)
            
            # Create the distribution window if it doesn't exist
            if self.vel_dist_window is None:
                self.vel_dist_window = VelocityDistributionWindow(self, self.console)
            
            # Show the window
            self.vel_dist_window.show()
            self.vel_dist_window.raise_()
            
            # Plot the distribution
            plot_velocity_distribution(
                self.vel_dist_window.scatter_canvas, 
                vel_traces, vel_twts, vel_values, 
                console=self.console
            )
            
            if self.console:
                info_message(self.console, "Velocity distribution window displayed")
                
        except Exception as e:
            error_message(self.console, f"Failed to show velocity distribution: {str(e)}")
            import traceback
            error_message(self.console, traceback.format_exc())
    
    def reset(self):
        """Reset the tab to its initial state."""
        self.segy_file_path = None
        self.velocity_file_path = None
        self.segy_metadata = None
        self.segy_path_label.setText("No file selected")
        self.velocity_path_label.setText("No file selected")
        self.next_button.setEnabled(False)
        
        # Clear the display manager
        self.display_manager.clear()
        self.canvas.draw()
    
    def _proceed_to_next(self):
        """Prepare data and send it to the next tab before proceeding."""
        if not self.segy_file_path or not self.velocity_file_path:
            return
        
        # Get velocity data
        vel_traces, vel_twts, vel_values = self._parse_velocity_file(self.velocity_file_path)
        
        # Prepare data dictionary to pass to the Edit tab
        velocity_data = {
            "segy_file_path": self.segy_file_path,
            "velocity_file_path": self.velocity_file_path,
            "segy_metadata": self.segy_metadata,
            "vel_traces": vel_traces,
            "vel_twts": vel_twts,
            "vel_values": vel_values
        }
        
        # Emit the data loaded signal first
        self.dataLoaded.emit(self.velocity_file_path, velocity_data)
        
        # Then emit the proceed signal
        self.proceedRequested.emit()