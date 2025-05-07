"""Interpolation tab for VelRecover application."""

import os
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QSplitter, QComboBox, QSpinBox, QDoubleSpinBox,
    QFrame, QFormLayout, QRadioButton, QButtonGroup, QSlider,
    QCheckBox, QFileDialog
)
from PySide6.QtGui import QIcon
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from ..utils.console_utils import info_message, warning_message, error_message, success_message
from ..utils.visualization_utils import SeismicDisplayManager
from ..utils.velocity_export import save_velocity_text_data, save_velocity_binary_data
from ..utils.velocity_distribution import VelocityDistributionWindow, plot_velocity_distribution
from ..core.linear_models import custom_linear_model, best_linear_fit
from ..core.logarithmic_models import custom_logarithmic_model, best_logarithmic_fit
from ..core.rbf_models import interpolate_velocity_data_rbf
from ..core.two_step import two_step_interpolation
from ..core.gauss_blur import apply_gaussian_blur


class SimpleNavigationToolbar(NavigationToolbar):
    """Simplified navigation toolbar with only Home, Pan and Zoom tools."""
    
    # Define which tools to keep
    toolitems = [t for t in NavigationToolbar.toolitems if t[0] in ('Home', 'Pan', 'Zoom', 'Save')]
    
    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)


class InterpolateTab(QWidget):
    """Tab for interpolating velocity data."""
    
    # Signals
    interpolationCompleted = Signal(dict)  # Interpolated data
    proceedRequested = Signal()
    
    def __init__(self, console, work_dir, parent=None):
        super().__init__(parent)
        self.setObjectName("interpolate_tab")
        self.console = console
        self.work_dir = work_dir
        
        # Data storage
        self.velocity_data = None
        self.interpolated_data = None
        self.current_method = "linear"
        self.blur_enabled = False
        self.blur_value = 2.5  # Default blur value
        
        # Create a single canvas for both input display and results
        self.figure = Figure(constrained_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setObjectName("velocity_canvas")
        self.ax = self.figure.add_subplot(111)
        
        # Display manager for SEGY and velocity data
        self.display_manager = SeismicDisplayManager(self.ax, self.console)
        
        # Reference to the colorbar for interpolation results
        self.velocity_colorbar = None
        self.interpolation_overlay = None
        
        # Initialize velocity distribution window
        self.vel_dist_window = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the tab's user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header section
        header = QLabel("Velocity Interpolation")
        header.setObjectName("tab_header")
        layout.addWidget(header)
        
        # Instruction text
        instruction = QLabel(
            "Interpolate the velocity picks using one of the available methods. "
            "Select a method and configure its parameters before running the interpolation."
        )
        instruction.setObjectName("description_label")
        instruction.setWordWrap(True)
        layout.addWidget(instruction)
        
        # Method selection and configuration
        method_group = self._create_method_selection()
        method_group.setFixedHeight(200)  # Fix the height of the method group box
        layout.addWidget(method_group)
        
        # Main content area with visualization
        display_group = QGroupBox("Velocity Model Visualization")
        display_group.setObjectName("display_group")
        display_layout = QVBoxLayout(display_group)
        display_layout.setContentsMargins(15, 15, 15, 15)
        
        # Add status label to show current display state
        self.status_label = QLabel("Displaying velocity picks")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        display_layout.addWidget(self.status_label)
        
        # Add canvas
        display_layout.addWidget(self.canvas, 1)
        
        # Add navigation toolbar
        toolbar = SimpleNavigationToolbar(self.canvas, self)
        toolbar.setObjectName("nav_toolbar")
        display_layout.addWidget(toolbar)
        
        layout.addWidget(display_group, 1)  # 1 = stretch factor
        
        # Button section at the bottom
        button_container = QWidget()
        button_container.setObjectName("button_container")
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 5, 10, 5)
        button_layout.setSpacing(10)

        # Distribution button
        self.dist_button = QPushButton("Show Velocity Distribution")
        self.dist_button.setObjectName("dist_button")
        self.dist_button.setMinimumWidth(180)
        self.dist_button.setFixedHeight(36)
        self.dist_button.clicked.connect(self._show_velocity_distribution)
        button_layout.addWidget(self.dist_button)
        
        # Run interpolation button
        self.run_button = QPushButton("Run Interpolation")
        self.run_button.setObjectName("run_button")
        self.run_button.setMinimumWidth(150)
        self.run_button.setFixedHeight(36)
        self.run_button.clicked.connect(self.run_interpolation)
        button_layout.addWidget(self.run_button)
        
        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("reset_button")
        self.reset_button.setMinimumWidth(100)
        self.reset_button.setFixedHeight(36)
        self.reset_button.clicked.connect(self.reset_interpolation)
        self.reset_button.setEnabled(False)
        button_layout.addWidget(self.reset_button)
        


        button_layout.addStretch()

        # Save as Text button
        self.save_txt_button = QPushButton("Save as Text")
        self.save_txt_button.setObjectName("save_txt_button")
        self.save_txt_button.setMinimumWidth(120)
        self.save_txt_button.setFixedHeight(36)
        self.save_txt_button.setEnabled(False)
        self.save_txt_button.clicked.connect(lambda: self._save_velocity_data("text"))
        button_layout.addWidget(self.save_txt_button)
        
        # Save as Binary button
        self.save_bin_button = QPushButton("Save as Binary")
        self.save_bin_button.setObjectName("save_bin_button")
        self.save_bin_button.setMinimumWidth(120)
        self.save_bin_button.setFixedHeight(36)
        self.save_bin_button.setEnabled(False)
        self.save_bin_button.clicked.connect(lambda: self._save_velocity_data("binary"))
        button_layout.addWidget(self.save_bin_button)
        
        layout.addWidget(button_container)
    
    def _create_method_selection(self):
        """Create method selection and configuration panel."""
        group_box = QGroupBox("Interpolation Method")
        group_box.setObjectName("method_selection_group")
        group_box.setMaximumHeight(150)
        
        # Main layout for the group box
        main_layout = QVBoxLayout(group_box)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Top section with dropdown on left, params in middle, blur on right
        top_layout = QHBoxLayout()
        
        # Left side - dropdown and description
        dropdown_layout = QVBoxLayout()
        
        # Method dropdown menu
        self.method_dropdown = QComboBox()
        self.method_dropdown.setObjectName("method_dropdown")
        self.method_dropdown.setMinimumWidth(200)
        
        methods = [
            ("Linear Best Fit", "linear_best"),
            ("Linear Custom", "linear_custom"),
            ("Logarithmic Best Fit", "log_best"),
            ("Logarithmic Custom", "log_custom"),
            ("RBF Interpolation", "rbf"),
            ("Two-Step Method", "two_step")
        ]
        
        for label, method_id in methods:
            self.method_dropdown.addItem(label, method_id)
        
        self.method_dropdown.currentIndexChanged.connect(self._on_method_changed)
        dropdown_layout.addWidget(self.method_dropdown)
        
        # Add description label below dropdown
        self.method_description = QLabel()
        self.method_description.setObjectName("method_description")
        self.method_description.setWordWrap(True)
        self.method_description.setStyleSheet("font-style: italic; color: #555;")
        dropdown_layout.addWidget(self.method_description)
        
        # Add to top layout with stretch to keep left-aligned
        dropdown_layout.addStretch()
        top_layout.addLayout(dropdown_layout, 1)  # Give it stretch factor of 1
        
        # Parameters container (middle)
        self.params_container = QFrame()
        self.params_container.setObjectName("params_container")
        self.params_layout = QVBoxLayout(self.params_container)
        self.params_layout.setContentsMargins(0, 0, 0, 0)
        self.params_layout.setAlignment(Qt.AlignTop)  # Align to top
        top_layout.addWidget(self.params_container, 2)  # Stretch factor of 2
        
        # Gaussian blur options (right side)
        blur_container = QFrame()
        blur_container.setObjectName("blur_container")
        blur_layout = QVBoxLayout(blur_container)
        blur_layout.setContentsMargins(0, 0, 0, 0)
        
        # Checkbox
        self.blur_checkbox = QCheckBox("Apply Gaussian Blur")
        self.blur_checkbox.setObjectName("blur_checkbox")
        self.blur_checkbox.toggled.connect(self._on_blur_toggled)
        blur_layout.addWidget(self.blur_checkbox)
        
        # Blur controls
        blur_strength_label = QLabel("Blur Strength:")
        blur_strength_label.setObjectName("blur_strength_label")
        blur_layout.addWidget(blur_strength_label)
        
        self.blur_slider = QSlider(Qt.Horizontal)
        self.blur_slider.setObjectName("blur_slider")
        self.blur_slider.setMinimum(0)
        self.blur_slider.setMaximum(100)
        self.blur_slider.setValue(5)  # Default value
        self.blur_slider.setEnabled(False)
        self.blur_slider.valueChanged.connect(self._on_blur_value_changed)
        self.blur_slider.setMinimumWidth(150)
        blur_layout.addWidget(self.blur_slider)
        
        self.blur_value_label = QLabel("2.5")
        self.blur_value_label.setObjectName("blur_value_label")
        self.blur_value_label.setFixedWidth(30)
        blur_layout.addWidget(self.blur_value_label)
        
        # Add stretch to push everything to the top
        blur_layout.addStretch()        
        top_layout.addWidget(blur_container, 1)  
        
        main_layout.addLayout(top_layout)       

        # Initialize method description and parameters
        self._update_method_description()
        self._create_method_params()
        
        return group_box
    
    def _update_method_description(self):
        """Update the description text based on the selected method."""
        method = self._get_selected_method()
        
        descriptions = {
            "linear_best": "Fits a best linear velocity model to the data points using least squares regression.",
            "linear_custom": "Creates a linear velocity model with custom initial velocity and gradient parameters.",
            "log_best": "Fits a best logarithmic velocity model to the data points using non-linear regression.",
            "log_custom": "Creates a logarithmic velocity model with custom base velocity and coefficient parameters.",
            "rbf": "Uses Radial Basis Function interpolation for a smooth model that honors all data points.",
            "two_step": "First interpolates each trace with velocity picks using RBF interpolation, then completes the model using nearest neighbour and smooths the results."
        }
        
        self.method_description.setText(descriptions.get(method, ""))
    
    def _on_method_changed(self):
        """Handle method selection change."""
        self._update_method_description()
        self._create_method_params()
    
    def _create_method_params(self):
        """Create parameter interfaces for each interpolation method."""
        # Clear any existing widgets
        for i in reversed(range(self.params_layout.count())):
            widget = self.params_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Get selected method
        selected_method = self._get_selected_method()
        
        if selected_method in ["linear_best", "log_best", "rbf"]:
            # These methods don't need parameters
            label = QLabel(f"No configuration needed for {self._get_method_display_name(selected_method)}.")
            label.setObjectName("no_params_label")
            self.params_layout.addWidget(label)
            
        elif selected_method == "linear_custom":
            params_frame = QFrame()
            params_layout = QFormLayout(params_frame)
            
            # V0 parameter (initial velocity)
            self.v0_linear = QDoubleSpinBox()
            self.v0_linear.setRange(1000, 10000)
            self.v0_linear.setValue(1500)
            self.v0_linear.setSuffix(" m/s")
            self.v0_linear.setObjectName("v0_linear")
            params_layout.addRow("Initial Velocity (V₀):", self.v0_linear)
            
            # k parameter (velocity gradient)
            self.k_linear = QDoubleSpinBox()
            self.k_linear.setRange(0.1, 10)
            self.k_linear.setValue(0.5)
            self.k_linear.setSingleStep(0.1)
            self.k_linear.setObjectName("k_linear")
            params_layout.addRow("Velocity Gradient (k):", self.k_linear)
            
            self.params_layout.addWidget(params_frame)
            
        elif selected_method == "log_custom":
            params_frame = QFrame()
            params_layout = QFormLayout(params_frame)
            
            # V0 parameter (base velocity)
            self.v0_log = QDoubleSpinBox()
            self.v0_log.setRange(1000, 10000)
            self.v0_log.setValue(1500)
            self.v0_log.setSuffix(" m/s")
            self.v0_log.setObjectName("v0_log")
            params_layout.addRow("Base Velocity (V₀):", self.v0_log)
            
            # k parameter (logarithmic factor)
            self.k_log = QDoubleSpinBox()
            self.k_log.setRange(500, 3000)
            self.k_log.setValue(1000)
            self.k_log.setSingleStep(50)
            self.k_log.setObjectName("k_log")
            params_layout.addRow("Logarithmic Factor (k):", self.k_log)
            
            self.params_layout.addWidget(params_frame)
            
        elif selected_method == "two_step":
            params_frame = QFrame()
            params_layout = QFormLayout(params_frame)
            
            # Blur value for two-step method
            self.blur_two_step = QDoubleSpinBox()
            self.blur_two_step.setRange(1, 10)
            self.blur_two_step.setValue(2.5)
            self.blur_two_step.setSingleStep(0.5)
            self.blur_two_step.setObjectName("blur_two_step")
            params_layout.addRow("Smoothing Factor:", self.blur_two_step)
            
            self.params_layout.addWidget(params_frame)
    
    def _get_selected_method(self):
        """Get the currently selected interpolation method."""
        return self.method_dropdown.currentData()
    
    def _get_method_display_name(self, method_id):
        """Get a display name for the method ID."""
        method_names = {
            "linear_best": "Linear Best Fit",
            "linear_custom": "Custom Linear Model",
            "log_best": "Logarithmic Best Fit",
            "log_custom": "Custom Logarithmic Model",
            "rbf": "RBF Interpolation",
            "two_step": "Two-Step Method"
        }
        return method_names.get(method_id, method_id)
    
    def _on_blur_toggled(self, checked):
        """Handle blur checkbox toggle."""
        self.blur_enabled = checked
        self.blur_slider.setEnabled(checked)
    
    def _on_blur_value_changed(self, value):
        """Handle blur slider value change."""
        self.blur_value = value 
        self.blur_value_label.setText(f"{self.blur_value:.1f}")
    
    def update_with_data(self, velocity_data):
        """Update the tab with velocity data."""
        self.velocity_data = velocity_data
        self.interpolated_data = None
        
        # Reset UI state
        self.reset_button.setEnabled(False)
        self.save_txt_button.setEnabled(False)
        self.save_bin_button.setEnabled(False)
        
        # Display the velocity data
        self._display_velocity_data()
    
    def _display_velocity_data(self):
        """Display the velocity picks data."""
        if self.velocity_data is None:
            return
        
        # Clear the plot and any previous results
        self.ax.clear()
        
        # Properly handle colorbar removal to avoid errors
        if self.velocity_colorbar is not None:
            try:
                self.velocity_colorbar.remove()
            except (KeyError, AttributeError):
                # Handle the case where colorbar removal fails
                pass
            self.velocity_colorbar = None
            
        self.interpolation_overlay = None
        
        # Extract velocity data using the edit tab's field names
        vel_traces = self.velocity_data.get('vel_traces', [])
        vel_twts = self.velocity_data.get('vel_twts', [])
        vel_values = self.velocity_data.get('vel_values', [])

        self.vel_min = np.min(vel_values)
        self.vel_max = np.max(vel_values)

        
        # Load SEGY file which will always be available
        segy_file_path = self.velocity_data.get('segy_file_path')
        
        # Load SEGY data - the display manager will store the dimensions
        self.segy_metadata = self.display_manager.load_segy(segy_file_path)
        
        # Display SEGY with velocity picks but without colorbar
        self.display_manager.load_velocity_picks(vel_traces, vel_twts, vel_values, 
                                               color_range=(self.vel_min, self.vel_max))
        self.display_manager.display(show_colorbar=False)
        
        # Store SEGY dimensions for velocity model resampling
        self.ntraces = self.segy_metadata.get('ntraces')
        self.nsamples = self.segy_metadata.get('nsamples')
        self.dt_ms = self.segy_metadata.get('dt_ms')
        self.delay = self.segy_metadata.get('delay')
        
        # Create a dummy mappable for the colorbar
        sm = plt.cm.ScalarMappable(cmap='jet', norm=plt.Normalize(vmin=self.vel_min, vmax=self.vel_max))
        sm.set_array([])
        
        # Add a single colorbar
        self.velocity_colorbar = self.figure.colorbar(sm, ax=self.ax)
        self.velocity_colorbar.set_label('Velocity (m/s)')
        
        self.status_label.setText("Displaying SEGY with velocity picks")
        
        # Draw the figure
        self.canvas.draw()
    
    def _display_interpolation_result(self):
        """Display the interpolation result overlay."""
        if self.interpolated_data is None:
            return
        
        # Extract the velocity grid and coordinate grids
        vel_values_grid = self.interpolated_data.get('vel_values_grid')
        vel_traces_grid = self.interpolated_data.get('vel_traces_grid')
        vel_twts_grid = self.interpolated_data.get('vel_twts_grid')
        
        if vel_values_grid is None or vel_traces_grid is None or vel_twts_grid is None:
            error_message(self.console, "Interpolation failed: missing grid data")
            return
        
        # Remove existing overlay if any
        if self.interpolation_overlay is not None:
            try:
                self.interpolation_overlay.remove()
            except (KeyError, AttributeError):
                pass
        
        # Use the stored velocity range from original velocity picks for consistent coloring
        vmin = self.vel_min
        vmax = self.vel_max
        
        # Get the SEGY axes limits to make sure our overlay matches exactly
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        
        # Add interpolation as an overlay with transparency, using exact SEGY limits
        self.interpolation_overlay = self.ax.imshow(
            vel_values_grid, cmap='jet', aspect='auto',
            extent=[x_min, x_max, y_min, y_max],
            alpha=0.7,  # Semi-transparent overlay
            vmin=vmin, vmax=vmax,  # Use consistent color range
            zorder=5  # Make sure it's above SEGY but below picks
        )
        
        info_message(self.console, f"Displayed interpolation overlay with axis limits: x=[{x_min}, {x_max}], y=[{y_min}, {y_max}]")
        
        # Update or add colorbar - we don't need a new one since we already have one
        # with the same color scale, but we'll update it to reflect the overlay
        if self.velocity_colorbar is not None:
            try:
                self.velocity_colorbar.update_normal(self.interpolation_overlay)
            except (KeyError, AttributeError):
                # If updating fails, create a new one
                try:
                    self.velocity_colorbar.remove()
                except (KeyError, AttributeError):
                    pass
                self.velocity_colorbar = self.figure.colorbar(self.interpolation_overlay, ax=self.ax)
                self.velocity_colorbar.set_label('Velocity (m/s)')
        
        # Update title and status
        method_name = self._get_method_display_name(self._get_selected_method())
        model_type = self.interpolated_data.get('model_type', method_name)
        self.ax.set_title(f'Interpolated Velocity Model: {model_type}')
        self.status_label.setText(f"Displaying interpolation result: {model_type}")
        
        # Draw the figure
        self.canvas.draw()
    
    def run_interpolation(self):
        """Run the selected interpolation method."""
        if self.velocity_data is None:
            warning_message(self.console, "No velocity data available for interpolation")
            return
        
        # Get selected method
        method = self._get_selected_method()
        info_message(self.console, f"Running interpolation using {self._get_method_display_name(method)}...")
        
        # Extract velocity data using the edit tab's field names
        vel_traces = self.velocity_data.get('vel_traces', [])
        vel_twts = self.velocity_data.get('vel_twts', [])
        vel_values = self.velocity_data.get('vel_values', [])
        
        # Check if we have valid data
        if len(vel_traces) == 0 or len(vel_twts) == 0 or len(vel_values) == 0:
            error_message(self.console, "Velocity data is empty. Cannot perform interpolation.")
            return
        
        # Extract trace and TWT range
        trace_range = (np.min(vel_traces), np.max(vel_traces))
        twt_range = (np.min(vel_twts), np.max(vel_twts))
        
        # Run the appropriate interpolation method
        try:
            if method == "linear_best":
                result = best_linear_fit(
                    vel_traces=vel_traces, vel_twts=vel_twts, vel_values=vel_values,
                    segy_file_path=self.velocity_data.get('segy_file_path'),
                    console=self.console
                )
            
            elif method == "linear_custom":
                v0 = self.v0_linear.value()
                k = self.k_linear.value()
                result = custom_linear_model(
                    vel_traces=vel_traces, vel_twts=vel_twts, vel_values=vel_values,
                    segy_file_path=self.velocity_data.get('segy_file_path'),
                    v0=v0, k=k,
                    console=self.console
                )
            
            elif method == "log_best":
                result = best_logarithmic_fit(
                    vel_traces=vel_traces, vel_twts=vel_twts, vel_values=vel_values,
                    segy_file_path=self.velocity_data.get('segy_file_path'),
                    console=self.console
                )
            
            elif method == "log_custom":
                v0 = self.v0_log.value()
                k = self.k_log.value()
                result = custom_logarithmic_model(
                    vel_traces=vel_traces, vel_twts=vel_twts, vel_values=vel_values,
                    segy_file_path=self.velocity_data.get('segy_file_path'),
                    v0=v0, k=k,
                    console=self.console
                )
            
            elif method == "rbf":
                result = interpolate_velocity_data_rbf(
                    vel_traces=vel_traces, vel_twts=vel_twts, vel_values=vel_values,
                    segy_file_path=self.velocity_data.get('segy_file_path'),
                    console=self.console
                )
            
            elif method == "two_step":
                blur_value = self.blur_two_step.value()
                
                # Use SEGY dimensions for interpolation
                info_message(self.console, f"Using SEGY dimensions: {self.ntraces} traces × {self.nsamples} samples")
                
                # Get the grid directly from the two-step method
                vel_traces_grid, vel_twts_grid, vel_values_grid = two_step_interpolation(
                    vel_traces=vel_traces, vel_twts=vel_twts, vel_values=vel_values,
                    trace_range=trace_range, twt_range=twt_range,
                    ntraces=self.ntraces, nsamples=self.nsamples,
                    dt_ms=self.dt_ms, delay=self.delay,
                    blur_value=blur_value,
                    console=self.console
                )
                
                # Create a result dictionary similar to other methods
                result = {
                    'vel_traces': vel_traces,
                    'vel_twts': vel_twts,
                    'vel_values': vel_values,
                    'vel_traces_grid': vel_traces_grid,
                    'vel_twts_grid': vel_twts_grid,
                    'vel_values_grid': vel_values_grid,
                    'model_type': 'Two-Step Interpolation'
                }
            
            else:
                error_message(self.console, f"Unknown interpolation method: {method}")
                return
            
            # Apply Gaussian blur if enabled
            if self.blur_enabled and 'vel_values_grid' in result:
                info_message(self.console, f"Applying Gaussian blur with strength {self.blur_value}")
                result['vel_values_grid'] = apply_gaussian_blur(result['vel_values_grid'], self.blur_value)
                # Update model type
                if 'model_type' in result:
                    result['model_type'] = f"{result['model_type']} + Blur"
            
            # Ensure the velocity grid matches the SEGY dimensions
            grid_shape = result['vel_values_grid'].shape
            
            # Check if resampling is needed
            if grid_shape[0] != self.nsamples or grid_shape[1] != self.ntraces:
                info_message(self.console, f"Resampling velocity grid from {grid_shape} to {(self.nsamples, self.ntraces)}")
                
                # Create new grid with SEGY dimensions
                from scipy.interpolate import RegularGridInterpolator
                
                # Extract original grid coordinates
                orig_twts = np.linspace(np.min(result['vel_twts_grid']), np.max(result['vel_twts_grid']), grid_shape[0])
                orig_traces = np.linspace(np.min(result['vel_traces_grid']), np.max(result['vel_traces_grid']), grid_shape[1])
                
                # Create interpolator from original grid
                interp_func = RegularGridInterpolator(
                    (orig_twts, orig_traces), 
                    result['vel_values_grid'],
                    bounds_error=False,
                    fill_value=None
                )
                
                # Create target grid with SEGY dimensions
                new_twts = np.linspace(self.delay, self.delay + (self.nsamples-1) * self.dt_ms, self.nsamples)
                
                trace_min = np.min(result['vel_traces_grid'])
                trace_max = np.max(result['vel_traces_grid'])
                new_traces = np.linspace(trace_min, trace_max, self.ntraces)
                
                # Create points to interpolate
                new_twts_grid, new_traces_grid = np.meshgrid(new_twts, new_traces, indexing='ij')
                points = np.column_stack((new_twts_grid.ravel(), new_traces_grid.ravel()))
                
                # Perform interpolation
                new_values = interp_func(points).reshape(self.nsamples, self.ntraces)
                
                # Update result with resampled grid
                result['vel_values_grid'] = new_values
                result['vel_twts_grid'] = new_twts_grid
                result['vel_traces_grid'] = new_traces_grid
                
                info_message(self.console, "Resampling complete")
            
            # Store the result
            self.interpolated_data = result
            
            # Display the result
            self._display_interpolation_result()
            
            # Update UI state
            self.reset_button.setEnabled(True)
            # Enable save buttons now that we have interpolation results
            self.save_txt_button.setEnabled(True)
            self.save_bin_button.setEnabled(True)
            # Signal that interpolation is complete
            self.interpolationCompleted.emit(result)
            
            success_message(self.console, "Interpolation completed successfully")
            
        except Exception as e:
            error_message(self.console, f"Interpolation failed: {str(e)}")
            import traceback
            error_message(self.console, traceback.format_exc())
    
    def reset_interpolation(self):
        """Reset the interpolation results and return to input data view."""
        self.interpolated_data = None
        
        # Remove the interpolation overlay
        if self.interpolation_overlay is not None:
            self.interpolation_overlay.remove()
            self.interpolation_overlay = None
        
        # Restore original display
        self._display_velocity_data()
        
        # Update UI state
        self.reset_button.setEnabled(False)
        self.save_txt_button.setEnabled(False)
        self.save_bin_button.setEnabled(False)
        
        info_message(self.console, "Interpolation results reset")
    
    def save_interpolation(self):
        """Save the interpolation results."""
        if self.interpolated_data is None:
            warning_message(self.console, "No interpolation results to save")
            return
            
        # Create save options dialog
        save_dialog = QWidget(self)
        save_dialog.setWindowTitle("Save Options")
        save_dialog.setFixedSize(400, 180)
        save_dialog_layout = QVBoxLayout(save_dialog)
        save_dialog_layout.setContentsMargins(20, 20, 20, 20)
        save_dialog_layout.setSpacing(15)
        
        # Text explaining save options
        info_label = QLabel("Choose a format to save the interpolated velocity data:")
        info_label.setWordWrap(True)
        save_dialog_layout.addWidget(info_label)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Save as text button
        save_txt_button = QPushButton("Save as Text (.dat)")
        save_txt_button.setFixedHeight(36)
        save_txt_button.clicked.connect(lambda: self._save_velocity_data("text"))
        buttons_layout.addWidget(save_txt_button)
        
        # Save as binary button
        save_bin_button = QPushButton("Save as Binary (.bin)")
        save_bin_button.setFixedHeight(36)
        save_bin_button.clicked.connect(lambda: self._save_velocity_data("binary"))
        buttons_layout.addWidget(save_bin_button)
        
        save_dialog_layout.addLayout(buttons_layout)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedHeight(36)
        cancel_button.clicked.connect(save_dialog.close)
        save_dialog_layout.addWidget(cancel_button)
        
        save_dialog.show()
    
    def _save_velocity_data(self, format_type):
        """Save velocity data in the specified format."""
        if self.interpolated_data is None:
            warning_message(self.console, "No interpolation results available to save")
            return
            
        # Create base directory for velocity files
        vels_dir = os.path.join(self.work_dir, "VELS")
        
        # Create specific subdirectory based on format type
        if format_type == "text":
            output_dir = os.path.join(vels_dir, "INTERPOLATED", "TXT")
        elif format_type == "binary":
            output_dir = os.path.join(vels_dir, "INTERPOLATED", "BIN")
        else:
            output_dir = vels_dir
        
        # Create the directory structure if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a simple config object with the needed path
        config = type('SimpleConfig', (), {'vels_dir': output_dir})
        
        # Get SEGY file path from velocity data
        segy_file_path = self.velocity_data.get('segy_file_path', "")
        
        # Extract grids from interpolated data
        vel_grid = self.interpolated_data.get('vel_values_grid')
        cdp_grid = self.interpolated_data.get('vel_traces_grid') 
        twt_grid = self.interpolated_data.get('vel_twts_grid')
        
        try:
            if format_type == "text":
                # Save as text file
                result = save_velocity_text_data(config, segy_file_path, cdp_grid, twt_grid, vel_grid)
                if result['success'] == True:
                    success_message(self.console, f"Velocity data saved as text file to: {result['path']}")
                else:
                    error_message(self.console, f"Failed to save velocity text file: {result.get('error', 'Unknown error')}")
            
            elif format_type == "binary":
                # Save as binary file
                result = save_velocity_binary_data(config, segy_file_path, vel_grid)
                if result['success'] == True:
                    success_message(self.console, f"Velocity data saved as binary file to: {result['path']}")
                else:
                    error_message(self.console, f"Failed to save velocity binary file: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            error_message(self.console, f"Error saving velocity data: {str(e)}")
            import traceback
            error_message(self.console, traceback.format_exc())                     

    def _show_velocity_distribution(self):
        """Show velocity distribution in a separate window."""
        if self.velocity_data is None:
            warning_message(self.console, "No velocity data available to display")
            return
        
        try:
            # Determine which velocity data to use
            if self.interpolated_data is not None:
                # Show distribution for the interpolated data
                title_suffix = "Interpolated Data"
                # If we have interpolated data with a full grid, we need to sample it
                # to get reasonable points for the distribution plot
                if ('vel_traces_grid' in self.interpolated_data and 
                    'vel_twts_grid' in self.interpolated_data and 
                    'vel_values_grid' in self.interpolated_data):
                    
                    # Sample the grid to get representative points
                    grid_shape = self.interpolated_data['vel_values_grid'].shape
                    sample_factor = max(1, grid_shape[0] * grid_shape[1] // 5000)  # Limit to ~5000 points
                    
                    # Sample the grid at regular intervals
                    trace_grid_flat = self.interpolated_data['vel_traces_grid'].flatten()[::sample_factor]
                    twt_grid_flat = self.interpolated_data['vel_twts_grid'].flatten()[::sample_factor]
                    vel_grid_flat = self.interpolated_data['vel_values_grid'].flatten()[::sample_factor]
                    
                    vel_traces = trace_grid_flat
                    vel_twts = twt_grid_flat
                    vel_values = vel_grid_flat
                else:
                    # Use the original picks from the interpolated result
                    vel_traces = self.interpolated_data.get('vel_traces', [])
                    vel_twts = self.interpolated_data.get('vel_twts', [])
                    vel_values = self.interpolated_data.get('vel_values', [])
                
                # Get regression parameters if available
                regression_params = {}
                if 'linear_params' in self.interpolated_data:
                    regression_params['linear'] = self.interpolated_data['linear_params']
                if 'log_params' in self.interpolated_data:
                    regression_params['logarithmic'] = self.interpolated_data['log_params']

            else:
                # Show distribution for the original input data
                title_suffix = "Original Data"
                vel_traces = self.velocity_data.get('vel_traces', [])
                vel_twts = self.velocity_data.get('vel_twts', [])
                vel_values = self.velocity_data.get('vel_values', [])
                regression_params = None
            
            # Create the distribution window if it doesn't exist
            if self.vel_dist_window is None:
                self.vel_dist_window = VelocityDistributionWindow(self, self.console)
            
            # Update the window title to indicate which data is displayed
            self.vel_dist_window.setWindowTitle(f"Distribution of Velocities - {title_suffix}")
            
            # Show the window
            self.vel_dist_window.show()
            self.vel_dist_window.raise_()
            
            # Plot the distribution
            plot_velocity_distribution(
                self.vel_dist_window.scatter_canvas, 
                vel_traces, vel_twts, vel_values, 
                console=self.console,
                regression_params=regression_params
            )
            
            if self.console:
                info_message(self.console, f"Velocity distribution window displayed for {title_suffix}")
                
        except Exception as e:
            error_message(self.console, f"Failed to show velocity distribution: {str(e)}")
            import traceback
            error_message(self.console, traceback.format_exc())