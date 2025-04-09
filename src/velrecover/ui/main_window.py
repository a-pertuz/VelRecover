"""Main window for the VelRecover application."""

import os
from PySide6.QtGui import QFont, QIntValidator, QAction
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QStyle, QFileDialog, QMessageBox, 
    QWidget, QTextEdit, QMainWindow, QDialog, QApplication, QInputDialog
)

from .widgets import ProgressStatusBar
from .dialogs import FirstRunDialog, AboutDialog, HelpDialog, ModelSelectionDialog, CustomLinearModelDialog, CustomLogarithmicModelDialog
from .distribution_display import VelocityDistributionWindow, plot_velocity_distribution
from .segy_display import SegyDisplayWindow

from ..utils.interpolation_utils import calculate_regression_params

from ..utils import (
    initialize_log_file, close_log_file, section_header, 
    success_message, error_message, info_message, 
    warning_message, summary_statistics,
    VelocityData, load_text_data, load_segy_file,
    interpolate, apply_smoothing,
    initialize_directories, copy_tutorial_files, copy_data_between_directories,
    save_velocity_text_data, save_velocity_binary_data
)

class VelRecover2D(QMainWindow):
    """Main window for the 2D velocity interpolation application."""
    
    def __init__(self, config, parent=None):
        """Initialize the main window."""
        super().__init__(parent)
        
        # Store configuration
        self.config = config
        
        # Create and set central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Initialize main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(15, 10, 15, 15)  # Left, top, right, bottom
        
        # Create console widget first so it can be used for logging
        self.setup_console()
        
        # Initialize logger with existing console utils
        self.initialize_logging()
        
        # Initialize velocity data
        self.velocity_data = VelocityData()
        
        # Initialize visualization windows
        self.distribution_window = None
        self.segy_viewer = None
        
        # Initialize application
        section_header(self.console, "Application Initialization")
        info_message(self.console, "Starting VelRecover2D")
        self.init_application()
        
    def initialize_logging(self):
        """Initialize the logging system."""
        # Create log directory
        log_dir = self.config.log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize log file
        log_file_path = initialize_log_file(self.config.work_dir)
        if log_file_path:
            success_message(self.console, f"Log file created: {log_file_path}")
        else:
            warning_message(self.console, "Failed to create log file")
        
        # Connect application exit event to log file closing
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self.cleanup)
    
    def cleanup(self):
        """Clean up resources before application exit."""
        info_message(self.console, "Closing application and finalizing logs")
        close_log_file()
        
    def init_application(self):
        """Initialize the application."""
        # Create required directories
        created_dirs = initialize_directories(self.config)
        for directory in created_dirs:
            info_message(self.console, f"Created directory: {directory}")
        
        # Check for first run
        if not os.path.exists(self.config.config_path):
            self.show_first_run_dialog()
        
        # Create menu bar and UI
        self.create_menu_bar()
        self.setup_ui_VR2D()
        
        success_message(self.console, "Application initialization complete")
    
    def show_first_run_dialog(self):
        """Show first run dialog."""
        dialog = FirstRunDialog(self, self.config.work_dir)
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            new_dir = dialog.get_selected_location()
            self.config.work_dir = new_dir
            info_message(self.console, f"User selected directory: {new_dir}")
            
            # Copy tutorial files
            result = copy_tutorial_files(self.config.work_dir, self.console)
            if result:
                success_message(self.console, "Example files copied successfully")
            else:
                warning_message(self.console, "Failed to copy example files")
        else:
            info_message(self.console, f"Using default directory: {self.config.work_dir}")
    
    def setup_console(self):
        """Set up the console output widget."""
        
        # Create console widget
        self.console = QTextEdit(self.central_widget)
        self.console.setStyleSheet("font-family: 'Consolas', 'Courier New'; font-size: 9pt;")
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QTextEdit.WidgetWidth) 
        self.console.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    
    def create_menu_bar(self):
        """Create the menu bar with file and help menus."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        # Set directory action
        set_dir_action = QAction("Set Data Directory", self)
        set_dir_action.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        set_dir_action.setShortcut("Ctrl+D")
        set_dir_action.triggered.connect(self.set_working_directory)
        file_menu.addAction(set_dir_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        # How To action
        how_to_action = QAction("HOW TO", self)
        how_to_action.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxQuestion))
        how_to_action.setShortcut("F1")
        how_to_action.triggered.connect(self.how_to)
        help_menu.addAction(how_to_action)
        
        help_menu.addSeparator()
        about_action = QAction("About", self)
        about_action.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        help_menu.addSeparator()
    
    def set_working_directory(self):
        """Let the user choose a new working directory for data storage."""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Directory for VelRecover Data",
            self.config.work_dir
        )
        
        if directory:
            # Store the old directory for potential data copying
            old_working_dir = self.config.work_dir
            
            # Update configuration
            self.config.work_dir = directory
            info_message(self.console, f"Working directory changed to: {directory}")
            
            # Ask if user wants to copy data from previous directory
            if os.path.exists(old_working_dir) and old_working_dir != directory:
                reply = QMessageBox.question(
                    self,
                    "Copy Existing Data",
                    f"Do you want to copy existing data from\n{old_working_dir}\nto the new location?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.copy_data(old_working_dir, directory)
    
    def copy_data(self, source_dir, target_dir):
        """Copy data from old directory to new directory."""
        self.status_bar.start("Copying data files...", 100)
        info_message(self.console, "Starting data copy process...")
        
        result = copy_data_between_directories(source_dir, target_dir, self.status_bar.update)
        
        if result['success']:
            success_message(self.console, "Data copied successfully to new location")
        else:
            error_message(self.console, f"Error copying data: {result.get('error', 'Unknown error')}")
            QMessageBox.warning(self, "Copy Error", f"Error copying data: {result.get('error', 'Unknown error')}")
        
        self.status_bar.finish()

    def setup_ui_VR2D(self):
        """Set up the user interface."""
        # Variables y configuraciones iniciales
        self.image_path = None
        self.points = []
        
        # Clear existing widgets if any
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        
        # Title with smaller font
        title_label = QLabel("VelRecover", self.central_widget)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))  
        title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(title_label)
        self.main_layout.addSpacing(10)
        
        # ===== LOAD FILES GROUP =====
        files_group = QGroupBox("Load Files")
        files_layout = QVBoxLayout()
        
        # Load text file button
        load_text_file_button = QPushButton("Load Text File", self)
        load_text_file_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        load_text_file_button.setToolTip(
            "Load velocity data from a text file.\n"
            "Expected format: CDP TWT(ms) Velocity(m/s)\n"
            "Supported file types: .dat, .txt, .tsv, .csv"
        )
        load_text_file_button.clicked.connect(self.load_text_file)
        files_layout.addWidget(load_text_file_button)
        
        # Load SEGY file button
        self.load_segy_file_button = QPushButton("Load SEGY File", self)
        self.load_segy_file_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.load_segy_file_button.setToolTip(
            "Load SEGY seismic data file.\n"
            "This provides spatial context for your velocity data.\n"
            "Supported file types: .sgy, .segy"
        )
        self.load_segy_file_button.clicked.connect(self.load_segy_file)
        self.load_segy_file_button.setEnabled(False)
        files_layout.addWidget(self.load_segy_file_button)
        
        files_group.setLayout(files_layout)
        self.main_layout.addWidget(files_group)
        
        # ===== PROCESSING GROUP =====
        processing_group = QGroupBox("Processing")
        processing_layout = QVBoxLayout()
        
        # Time shift button
        self.timeshift_button = QPushButton("Apply Time Shift", self)
        self.timeshift_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowUp))
        self.timeshift_button.setToolTip(
            "Add or subtract a constant time value to all TWT values.\n"
            "Useful for aligning velocity data with SEGY when there's a time offset."
        )
        self.timeshift_button.clicked.connect(self.apply_timeshift)
        self.timeshift_button.setEnabled(False)
        processing_layout.addWidget(self.timeshift_button)
        
        # Add custom picks button
        self.add_custom_picks_button = QPushButton("Add Custom Picks", self)
        self.add_custom_picks_button.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.add_custom_picks_button.setToolTip(
            "Enter custom pick mode to add, edit, or delete velocity picks directly on the SEGY display.\n"
            "Custom picks can be saved as a new velocity file."
        )
        self.add_custom_picks_button.clicked.connect(self.enable_custom_picks)
        self.add_custom_picks_button.setEnabled(False)
        processing_layout.addWidget(self.add_custom_picks_button)
        
        # Interpolate button
        self.interpolate2D_button = QPushButton("Interpolate", self)
        self.interpolate2D_button.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.interpolate2D_button.setToolTip(
            "Run velocity interpolation to create a continuous velocity model from discrete picks.\n"
            "Multiple interpolation methods are available for different geological scenarios."
        )
        self.interpolate2D_button.clicked.connect(self.interpolation_2d)
        self.interpolate2D_button.setEnabled(False)
        processing_layout.addWidget(self.interpolate2D_button)
        
        processing_group.setLayout(processing_layout)
        self.main_layout.addWidget(processing_group)
        
        # ===== SAVE GROUP =====
        save_group = QGroupBox("Save Results")
        save_layout = QVBoxLayout()
        
        # Save data buttons
        self.save_data_button = QPushButton("Save Data as TXT", self)
        self.save_data_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.save_data_button.setToolTip(
            "Save interpolated velocity data as a text file.\n"
            "Format: CDP TWT(ms) Velocity(m/s)\n"
            "This format is human-readable and can be imported into other software."
        )
        self.save_data_button.clicked.connect(self.save_vel2D_data_txt)
        self.save_data_button.setEnabled(False)
        save_layout.addWidget(self.save_data_button)
        
        self.save_data_bin_button = QPushButton("Save Data as BIN", self)
        self.save_data_bin_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.save_data_bin_button.setToolTip(
            "Save interpolated velocity data as a binary file.\n"
            "Format: 32-bit floating-point binary grid data\n"
            "This format is compatible with Seismic Unix and other processing software."
        )
        self.save_data_bin_button.clicked.connect(self.save_vel2D_data_bin)
        self.save_data_bin_button.setEnabled(False)
        save_layout.addWidget(self.save_data_bin_button)
        
        save_group.setLayout(save_layout)
        self.main_layout.addWidget(save_group)
        
        # Gaussian Blur section
        blur_group = QGroupBox("Smoothing")
        blur_layout = QVBoxLayout()
        
        # Blur value input
        blur_value_layout = QHBoxLayout()
        blur_value_label = QLabel("Gaussian Blur Value (1-100):", self)
        self.blur_value_input = QLineEdit(self)
        self.blur_value_input.setValidator(QIntValidator())
        self.blur_value_input.setText("1")
        self.blur_value_input.setToolTip(
            "Set the Gaussian blur kernel size.\n"
            "Higher values create smoother velocity models.\n"
            "Recommended range: 1-20 for typical data."
        )
        blur_value_layout.addWidget(blur_value_label)
        blur_value_layout.addWidget(self.blur_value_input)
        blur_layout.addLayout(blur_value_layout)
        
        # Apply button
        self.apply_blur_button = QPushButton("Apply Gaussian Blur", self)
        self.apply_blur_button.setToolTip(
            "Apply Gaussian blur smoothing to the velocity model.\n"
            "This reduces noise and creates a more geologically realistic model.\n"
            "You can apply multiple passes with different values."
        )
        self.apply_blur_button.clicked.connect(self.apply_gaussian_blur)
        self.apply_blur_button.setEnabled(False)
        blur_layout.addWidget(self.apply_blur_button)
        
        blur_group.setLayout(blur_layout)
        self.main_layout.addWidget(blur_group)
        
        # Status bar with progress
        self.status_bar = ProgressStatusBar(self)
        self.main_layout.addWidget(self.status_bar)
        
        # Add console section
        console_group = QGroupBox("Console Output")
        console_layout = QVBoxLayout()
        console_layout.addWidget(self.console)
        console_group.setLayout(console_layout)
        self.main_layout.addWidget(console_group)
        
        # Reset button below console
        reset_button = QPushButton("Restart Process", self)
        reset_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        reset_button.setToolTip(
            "Clear all loaded data and reset the application to its initial state.\n"
            "Warning: All unsaved data will be lost!"
        )
        reset_button.clicked.connect(self.restart_process)
        self.main_layout.addWidget(reset_button)
        
        # Add initial status message showing working directory
        self.console.append(f"Working directory: {self.config.work_dir}")

    def apply_timeshift(self):
        """Apply a time shift to the TWT values in the velocity data."""
        if not self.velocity_data.has_data():
            QMessageBox.warning(self, "Warning", "No velocity data available. Please load a text file first.")
            return
        
        # Prompt for time shift value
        time_shift, ok = QInputDialog.getDouble(
            self, 
            "Time Shift", 
            "Enter time shift value (ms):",
            200.0,   # Default value
            -10000.0, # Min value
            10000.0,  # Max value
            1        # Decimal places
        )
        
        if not ok:
            return  # User cancelled
        
        # Apply the time shift
        info_message(self.console, f"Applying {time_shift} ms time shift to velocity data...")
        
        try:
            original_twt = self.velocity_data.twt.copy()
            
            # Apply the shift
            self.velocity_data.twt = self.velocity_data.twt + time_shift
            
            # Recalculate regression parameters after time shift
            self.velocity_data.regression_params = calculate_regression_params(
                self.velocity_data.twt, self.velocity_data.vel
            )
            
            # Update visualization
            self.show_velocity_distribution()
            
            # If SEGY viewer is open, update it too
            if hasattr(self, 'segy_viewer') and self.segy_viewer is not None:
                try:
                    # Update both the underlying data and the custom picks manager's data
                    self.segy_viewer.velocity_twt = self.velocity_data.twt.copy()
                    self.segy_viewer.custom_picks_manager.initialize_from_existing(
                        self.velocity_data.cdp, 
                        self.velocity_data.twt, 
                        self.velocity_data.vel, 
                        self.velocity_data.text_file_path
                    )
                    self.segy_viewer.update_display()
                except Exception as e:
                    warning_message(self.console, f"Error updating SEGY display after time shift: {str(e)}")
            
            success_message(self.console, f"Successfully applied {time_shift} ms time shift")
        except Exception as e:
            error_message(self.console, f"Error applying time shift: {str(e)}")
            
            # Restore original TWT values in case of error
            if hasattr(self.velocity_data, 'twt') and original_twt is not None:
                self.velocity_data.twt = original_twt

    def load_text_file(self):
        """Open a file dialog to select a text file."""
        section_header(self.console, "Loading Text File")
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Text File",
            self.config.raw_vels_dir,
            "Text Files (*.dat *.txt *.tsv *.csv)",
            options=options
        )
        
        if file_path:
            info_message(self.console, f"Selected text file: {file_path}")
            
            # Use the interpolation utilities to load the data
            result = load_text_data(file_path)
            if result['success']:
                self.velocity_data = result['data']
                self.load_segy_file_button.setEnabled(True)
                
                # Update the distribution window
                self.show_velocity_distribution()
                
                # Log statistics about the loaded data
                summary_statistics(self.console, result['stats'])
                success_message(self.console, f"Successfully loaded {result['stats']['points']} velocity points")
            else:
                error_message(self.console, f"Error loading text file: {result.get('error', 'Unknown error')}")
                QMessageBox.critical(self, "Error", f"Failed to load text file: {result.get('error', 'Unknown error')}")

    def load_segy_file(self):
        """Open a file dialog to select a SEGY file."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SEGY File",
            self.config.segy_dir,
            "SEGY Files (*.sgy *.segy)",
            options=options
        )
        
        if file_path:
            result = load_segy_file(self.velocity_data, file_path)
            
            if result['success']:
                info_message(self.console, f"SEGY file loaded: {file_path}")
                self.interpolate2D_button.setEnabled(True)
                self.timeshift_button.setEnabled(True)  # Enable timeshift button
                self.add_custom_picks_button.setEnabled(True)  # Enable custom picks button
                
                # Automatically display the SEGY file
                self.show_segy_viewer()
            else:
                error_message(self.console, f"Error loading SEGY file: {result.get('error', 'Unknown error')}")

    def show_segy_viewer(self):
        """Show the SEGY viewer window."""
        if not self.velocity_data.has_segy():
            QMessageBox.warning(self, "Warning", "No SEGY file loaded. Please load a SEGY file first.")
            return
        
        # Create parameters for SEGY display
        velocity_data_available = self.velocity_data.has_data()
        velocity_grid_available = self.velocity_data.has_interpolation()
        
        # If viewer already exists, raise it instead of creating new one
        if hasattr(self, 'segy_viewer') and self.segy_viewer is not None:
            try:
                # Update the viewer with current data
                if velocity_grid_available:
                    self.segy_viewer.update_velocity_model(
                        self.velocity_data.cdp_grid,
                        self.velocity_data.twt_grid,
                        self.velocity_data.output_vel_grid,
                        self.velocity_data.model_type
                    )
                
                # Bring window to front
                self.segy_viewer.show()
                self.segy_viewer.raise_()
                self.segy_viewer.activateWindow()
                return
            except Exception:
                # If update fails, create a new viewer
                pass
        
        # Create and store SEGY viewer reference
        self.segy_viewer = SegyDisplayWindow(
            self.velocity_data.segy_file_path,
            parent=self,
            console=self.console,
            cdp=self.velocity_data.cdp if velocity_data_available else None,
            twt=self.velocity_data.twt if velocity_data_available else None,
            vel=self.velocity_data.vel if velocity_data_available else None,
            cdp_grid=self.velocity_data.cdp_grid if velocity_grid_available else None,
            twt_grid=self.velocity_data.twt_grid if velocity_grid_available else None,
            vel_grid=self.velocity_data.output_vel_grid if velocity_grid_available else None,
            model_type=self.velocity_data.model_type if velocity_grid_available else None
        )
        
        self.segy_viewer.show()
        self.segy_viewer.raise_()
        self.segy_viewer.activateWindow()
    
    def interpolation_2d(self):
        """Perform 2D interpolation of velocity data and show the results automatically."""
        import time
        from datetime import timedelta
                   
        # Check if we're already interpolated and provide warning if needed
        already_interpolated = self.velocity_data.has_interpolation()
        
        # Show interpolation method selection dialog
        method_dialog = ModelSelectionDialog(self, already_interpolated)
        result = method_dialog.exec()
        
        if result != QDialog.Accepted:
            info_message(self.console, "Interpolation cancelled by user")
            return
        
        # Get selected method
        method_type = method_dialog.get_selected_method()
        info_message(self.console, f"Selected interpolation method: {method_type}")
        
        # Parameters for interpolation
        params = {}
        # If custom linear model selected, show dialog for parameters
        if method_type == "custom_linear":
            custom_dialog = CustomLinearModelDialog(self)
            if custom_dialog.exec() != QDialog.Accepted:
                info_message(self.console, "Custom linear model cancelled")
                return
            
            # Get parameters from dialog
            v0, k = custom_dialog.get_parameters()
            params = {'v0': float(v0), 'k': float(k)}
            # Use formatting that preserves small values without scientific notation
            if k < 0.01:
                info_message(self.console, f"Custom linear model parameters: V₀={v0:.1f}, k={k:.6f}")
            else:
                info_message(self.console, f"Custom linear model parameters: V₀={v0:.1f}, k={k:.4f}")
        
        # If custom logarithmic model selected, show dialog for parameters
        elif method_type == "custom_log":
            custom_dialog = CustomLogarithmicModelDialog(self)
            if custom_dialog.exec() != QDialog.Accepted:
                info_message(self.console, "Custom logarithmic model cancelled")
                return
            
            # Get parameters from dialog
            v0, k = custom_dialog.get_parameters()
            params = {'v0': float(v0), 'k': float(k)}
            info_message(self.console, f"Custom logarithmic model parameters: V₀={v0:.1f}, k={k:.1f}")
        
        # Start progress and tracking time
        self.status_bar.start("Starting interpolation process...", 100)
        section_header(self.console, "Interpolation")
        info_message(self.console, f"Starting interpolation with {method_type} method...")
        
        start_time = time.time()
        last_update_time = start_time
        update_interval = 0.5  # seconds between progress updates
        
        # Create a progress callback that includes time estimation
        def progress_callback(percent, message=""):
            nonlocal last_update_time
            current_time = time.time()
            
            # Only update status bar at reasonable intervals to avoid UI slowdown
            if current_time - last_update_time >= update_interval or percent >= 100:
                elapsed_time = current_time - start_time
                
                # Only show time estimate if we're at least 5% through the process
                estimated_message = ""
                if percent > 5 and percent < 100:
                    # Estimate total time based on progress so far
                    estimated_total = elapsed_time * 100 / percent
                    estimated_remaining = estimated_total - elapsed_time
                    
                    # Format as MM:SS
                    time_remaining = str(timedelta(seconds=int(estimated_remaining))).split('.')[0]
                    estimated_message = f" (Est. remaining: {time_remaining})"
                
                update_message = f"{message}{estimated_message}" if message else f"Interpolating...{estimated_message}"
                self.status_bar.update(percent, update_message)
                last_update_time = current_time
        
        try:
            result = interpolate(
                self.velocity_data,
                method_type,
                console=self.console,
                status_callback=progress_callback,
                cancel_check=self.status_bar.wasCanceled,
                **params,
            )
            
            if result.get('cancelled'):
                warning_message(self.console, "Interpolation cancelled by user")
                self.status_bar.finish()
                return
            
            if not result['success']:
                error_message(self.console, f"Error during interpolation: {result.get('error', 'Unknown error')}")
                
                # Enhanced error handling with specific advice based on error type
                error_msg = result.get('error', '').lower()
                if 'memory' in error_msg:
                    QMessageBox.critical(self, "Memory Error", 
                                        "The system ran out of memory during interpolation. Try:\n"
                                        "1. Close other applications to free memory\n"
                                        "2. Use a smaller dataset or lower resolution\n"
                                        "3. Try a different interpolation method")
                elif 'singular matrix' in error_msg or 'linalg' in error_msg:
                    QMessageBox.critical(self, "Numerical Error", 
                                        "A numerical error occurred during interpolation. Try:\n"
                                        "1. Check your velocity data for anomalous values\n"
                                        "2. Try a different interpolation method\n"
                                        "3. Ensure your data points aren't too closely spaced")
                else:
                    QMessageBox.critical(self, "Interpolation Error", 
                                        f"Error during interpolation: {result.get('error', 'Unknown error')}\n\n"
                                        "Try using a different interpolation method or check your data.")
                
                self.status_bar.finish()
                return
                
            # Calculate and display elapsed time
            elapsed_time = time.time() - start_time
            time_str = str(timedelta(seconds=int(elapsed_time))).split('.')[0]
                
            self.status_bar.update(100, f"Interpolation completed successfully in {time_str}")
            success_message(self.console, f"Interpolation completed successfully in {time_str} using {self.velocity_data.model_type} method")
            
            # Show additional statistics
            summary_statistics(self.console, result['stats'])
            
            # Enable buttons for further processing
            self.save_data_button.setEnabled(True)
            self.save_data_bin_button.setEnabled(True)
            self.apply_blur_button.setEnabled(True)
            
            # Update SEGY display if open or create new one
            if hasattr(self, 'segy_viewer') and self.segy_viewer is not None:
                try:
                    self.segy_viewer.update_velocity_model(
                        self.velocity_data.cdp_grid,
                        self.velocity_data.twt_grid,
                        self.velocity_data.output_vel_grid,
                        self.velocity_data.model_type
                    )
                except Exception as e:
                    warning_message(self.console, f"Error updating SEGY viewer: {str(e)}")
                    # If fails, create a new viewer
                    self.show_segy_viewer()
            else:
                # Show SEGY viewer with interpolated data
                self.show_segy_viewer()
        
        except Exception as e:
            error_message(self.console, f"Unexpected error during interpolation: {str(e)}")
            QMessageBox.critical(self, "Unexpected Error", 
                               f"An unexpected error occurred:\n{str(e)}\n\n"
                               "This has been logged and the application will continue running.")
        finally:
            self.status_bar.finish()
    
    def apply_gaussian_blur(self):
        """Apply Gaussian blur to the interpolated velocity data."""
        
        blur_value = int(self.blur_value_input.text())
        
        result = apply_smoothing(self.velocity_data, blur_value)
        
        if not result['success']:
            error_message(self.console, f"Error applying blur: {result.get('error', 'Unknown error')}")
            return
        
        info_message(self.console, f"Applied Gaussian blur with value {blur_value}")
        
        # Update SEGY display if open
        if hasattr(self, 'segy_viewer') and self.segy_viewer is not None:
            try:
                self.segy_viewer.update_velocity_model(
                    self.velocity_data.cdp_grid,
                    self.velocity_data.twt_grid,
                    self.velocity_data.output_vel_grid,
                    f"{self.velocity_data.model_type} with Blur {blur_value}"
                )
            except:
                pass
    
    def save_vel2D_data_txt(self):
        """Save the velocity data to a .dat file."""
        vel_data = self.velocity_data
        
        result = save_velocity_text_data(
            self.config,
            vel_data.segy_file_path,
            vel_data.cdp_grid,
            vel_data.twt_grid,
            vel_data.output_vel_grid
        )
        
        if result['success']:
            success_message(self.console, f"Data saved to: {result['path']}")
        else:
            error_message(self.console, f"Failed to save data: {result.get('error', 'Unknown error')}")
            QMessageBox.critical(self, "Error", f"Failed to save data: {result.get('error', 'Unknown error')}")
    
    def save_vel2D_data_bin(self):
        """Save the velocity data to a binary file."""
        vel_data = self.velocity_data
        
        result = save_velocity_binary_data(
            self.config,
            vel_data.segy_file_path,
            vel_data.output_vel_grid
        )
        
        if result['success']:
            success_message(self.console, f"Data saved to: {result['path']}")
        else:
            error_message(self.console, f"Failed to save data: {result.get('error', 'Unknown error')}")
            QMessageBox.critical(self, "Error", f"Failed to save data: {result.get('error', 'Unknown error')}")
    
    def show_velocity_distribution(self):
        """Show the velocity distribution window."""
        if not self.velocity_data.has_data():
            QMessageBox.warning(self, "Warning", "No velocity data available. Please load a text file first.")
            return
            
        vel_data = self.velocity_data
        
        # Create window if it doesn't exist or recreate if it was closed
        if not hasattr(self, 'distribution_window') or self.distribution_window is None:
            self.distribution_window = VelocityDistributionWindow(parent=self, console=self.console)
            
        # Plot the velocity data
        plot_velocity_distribution(
            self.distribution_window.scatter_canvas,
            vel_data.cdp,
            vel_data.twt,
            vel_data.vel,
            console=self.console,
            regression_params=vel_data.regression_params
        )
        
        # Show and bring to front
        self.distribution_window.show()
        self.distribution_window.raise_()
        self.distribution_window.activateWindow()
    
    def show_about_dialog(self):
        """Show the About dialog."""
        about_dialog = AboutDialog(self)
        about_dialog.show()

    def how_to(self):
        """Show help dialog with information about the application."""
        help_dialog = HelpDialog(self)
        help_dialog.show()
    
    def restart_process(self):
        """Restart the application by resetting state and closing windows."""
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Restart Process",
            "Are you sure you want to restart?\nAll unsaved data will be lost.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Close popup windows if they exist
            if hasattr(self, 'distribution_window') and self.distribution_window:
                try:
                    self.distribution_window.hide()
                except:
                    pass
            
            # Close SEGY viewer if open
            if hasattr(self, 'segy_viewer') and self.segy_viewer:
                try:
                    self.segy_viewer.hide()
                    self.segy_viewer = None
                except:
                    pass
            
            # Reset velocity data
            self.velocity_data.reset()
            
            # Reset UI state
            self.load_segy_file_button.setEnabled(False)
            self.interpolate2D_button.setEnabled(False)
            self.save_data_button.setEnabled(False)
            self.save_data_bin_button.setEnabled(False)
            self.apply_blur_button.setEnabled(False)
            self.timeshift_button.setEnabled(False)  # Disable timeshift button
            
            # Reset blur value input
            self.blur_value_input.setText("1")
            
            # Clear console
            self.console.clear()
            info_message(self.console, f"Application reset to initial state.")
            info_message(self.console, f"Working directory: {self.config.work_dir}")
            
            # Clear status bar
            self.status_bar.showMessage("")
            self.status_bar.finish()
    
    def enable_custom_picks(self):
        """Enable custom picks mode in the SEGY viewer."""
        if not self.velocity_data.has_segy():
            QMessageBox.warning(self, "Warning", "No SEGY file loaded. Please load a SEGY file first.")
            return
            
        if not hasattr(self, 'segy_viewer') or self.segy_viewer is None:
            # Create the SEGY viewer if it doesn't exist
            self.show_segy_viewer()
            
        # Enable custom picks mode in the SEGY viewer
        self.segy_viewer.enable_custom_picks_mode(True)
        
        # Show instructions
        QMessageBox.information(
            self,
            "Custom Picks Mode",
            "Custom picks mode is now enabled.\n\n"
            "Click on the SEGY display to add new velocity picks.\n"
            "Click on an existing pick to modify its velocity value.\n"
            "When finished, click 'Save Custom Picks' to save your changes."
        )
        
        # Ensure the SEGY viewer is visible and in front
        self.segy_viewer.show()
        self.segy_viewer.raise_()
        self.segy_viewer.activateWindow()
    
    def load_text_file_path(self, file_path):
        """Load a text file from a specific path."""
        info_message(self.console, f"Loading text file: {file_path}")
        
        # Store the current SEGY file path before loading new data
        current_segy_file_path = None
        if hasattr(self.velocity_data, 'segy_file_path'):
            current_segy_file_path = self.velocity_data.segy_file_path
        
        # Use the interpolation utilities to load the data
        result = load_text_data(file_path)
        if result['success']:
            self.velocity_data = result['data']
            
            # Explicitly ensure the text_file_path is set
            self.velocity_data.text_file_path = file_path
            
            # Restore the SEGY file path if it was previously set
            if current_segy_file_path:
                self.velocity_data.segy_file_path = current_segy_file_path
                
                # If SEGY file was previously loaded, reload its dimensions
                try:
                    import seisio
                    sio = seisio.input(current_segy_file_path)
                    self.velocity_data.set_segy_dimensions(
                        nsamples=sio.nsamples,
                        ntraces=sio.ntraces,
                        dt_ms=sio.vsi / 1000.0,
                        delay=sio.delay
                    )
                except Exception as e:
                    warning_message(self.console, f"Could not reload SEGY dimensions: {str(e)}")
            
            self.load_segy_file_button.setEnabled(True)
            
            # Update the distribution window
            self.show_velocity_distribution()
            
            # Log statistics about the loaded data
            summary_statistics(self.console, result['stats'])
            success_message(self.console, f"Successfully loaded {result['stats']['points']} velocity picks")
            
            # If SEGY viewer is open, update it with the new picks
            if hasattr(self, 'segy_viewer') and self.segy_viewer is not None:
                try:
                    self.segy_viewer.velocity_cdp = self.velocity_data.cdp
                    self.segy_viewer.velocity_twt = self.velocity_data.twt
                    self.segy_viewer.velocity_vel = self.velocity_data.vel
                    self.segy_viewer.has_velocity_picks = True
                    self.segy_viewer.text_file_path = file_path  # Also update in the viewer
                    self.segy_viewer.update_display()
                except Exception as e:
                    warning_message(self.console, f"Error updating SEGY display: {str(e)}")
            
            # Enable the appropriate buttons
            self.add_custom_picks_button.setEnabled(True)
            # If we had a SEGY file loaded before, enable all SEGY-dependent buttons
            if current_segy_file_path:
                self.interpolate2D_button.setEnabled(True)
                self.timeshift_button.setEnabled(True)
        else:
            error_message(self.console, f"Error loading text file: {result.get('error', 'Unknown error')}")
            QMessageBox.critical(self, "Error", f"Failed to load text file: {result.get('error', 'Unknown error')}")

    def load_segy_file_path(self, file_path):
        """Load a SEGY file from a specific path."""
        if not file_path or not os.path.exists(file_path):
            error_message(self.console, f"SEGY file not found: {file_path}")
            return
            
        info_message(self.console, f"Loading SEGY file: {file_path}")
        
        result = load_segy_file(self.velocity_data, file_path)
        
        if result['success']:
            info_message(self.console, f"SEGY file loaded: {file_path}")
            self.interpolate2D_button.setEnabled(True)
            self.timeshift_button.setEnabled(True)
            self.add_custom_picks_button.setEnabled(True)
            
            # Refresh the SEGY viewer if open, or create a new one
            if hasattr(self, 'segy_viewer') and self.segy_viewer is not None:
                self.show_segy_viewer()
            else:
                self.show_segy_viewer()
        else:
            error_message(self.console, f"Error loading SEGY file: {result.get('error', 'Unknown error')}")
