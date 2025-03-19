"""Main window for the src application."""

import os
import numpy as np
import pandas as pd
import appdirs
import json
import sys
from PySide6.QtGui import QFont, QIntValidator, QAction
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QStyle, QFileDialog, QMessageBox, 
    QWidget, QTextEdit, QMainWindow, QDialog
)

from .widgets import ProgressStatusBar
from .dialogs import FirstRunDialog, AboutDialog, HelpDialog
from ..core.visualization import VelocityAnalysisWindow, VelocityDistributionWindow, display_velocity_analysis, plot_velocity_distribution
from ..core.interpolation import interpolate_velocity_data, apply_gaussian_blur
from ..utils.save_functions import (save_velocity_text_data, save_velocity_binary_data)
from ..utils.resource_utils import copy_tutorial_files
from ..utils.console_utils import (initialize_log_file, close_log_file, section_header,
                                  success_message, error_message, info_message,
                                  warning_message, summary_statistics)

class VelRecover2D(QMainWindow):
    """Main window for the 2D velocity interpolation application."""
    
    def __init__(self, parent=None):
        """Initialize the main window."""
        super().__init__(parent)
        # Create and set central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create console widget first so it can be used for logging
        self.setup_console()
        
        self.analysis_window = VelocityAnalysisWindow(console=self.console)
        self.distribution_window = VelocityDistributionWindow(console=self.console)
        
        # Get appropriate directories for user data and config
        self.app_name = "velrecover"
        self.user_data_dir = appdirs.user_data_dir(self.app_name)
        self.user_config_dir = appdirs.user_config_dir(self.app_name)
        
        # Ensure config directory exists
        os.makedirs(self.user_config_dir, exist_ok=True)
        self.config_path = os.path.join(self.user_config_dir, 'config.json')
        
        # Initialize GUI components
        section_header(self.console, "Application Initialization")
        info_message(self.console, f"Starting VelRecover2D")
        
        self.load_config()
        
        self.init_logging()

        self.create_menu_bar()
        
        self.setup_ui_VR2D()
        
        success_message(self.console, "Application initialization complete")
    
    def setup_console(self):
        """Set up the console output widget."""
        # Create console group box
        self.console_groupbox = QGroupBox("CONSOLE OUTPUT", self)
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.console_groupbox.setFont(font)
        
        self.console_layout = QVBoxLayout()
        self.console = QTextEdit(self)
        self.console.setReadOnly(True)
        self.console_layout.addWidget(self.console)
        self.console_groupbox.setLayout(self.console_layout)
    
    def init_logging(self):
        """Initialize the logging system."""
        # Create log directory
        log_dir = os.path.join(self.work_dir, "LOG")
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize log file
        log_file_path = initialize_log_file(self.work_dir)
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

    def load_config(self):
        """Load configuration from file or create default."""
        section_header(self.console, "Configuration")
        
        # Default location from appdirs
        default_base_dir = os.path.join(self.user_data_dir, 'data')
        
        is_first_run = not os.path.exists(self.config_path)
        
        if is_first_run:
            info_message(self.console, "First run detected, showing setup dialog")
            dialog = FirstRunDialog(self, default_base_dir)
            result = dialog.exec()
            
            if result == QDialog.Accepted:
                base_dir = dialog.get_selected_location()
                info_message(self.console, f"User selected directory: {base_dir}")
            else:
                base_dir = default_base_dir
                info_message(self.console, f"Using default directory: {base_dir}")
                
            config = {'base_dir': base_dir}
        else:
            # Load existing config
            try:
                info_message(self.console, f"Loading configuration from {self.config_path}")
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    base_dir = config.get('base_dir', default_base_dir)
                success_message(self.console, "Configuration loaded successfully")
            except Exception as e:
                base_dir = default_base_dir
                config = {'base_dir': base_dir}
                error_message(self.console, f"Error loading config: {e}")
                warning_message(self.console, f"Using default directory: {base_dir}")
            

        self.work_dir = base_dir

        # Initialize directory attributes
        self.vels_dir = os.path.join(self.work_dir, "VELS", "2D")
        self.raw_vels_dir = os.path.join(self.work_dir, "VELS", "RAW")
        self.segy_dir = os.path.join(self.work_dir, "SEGY")

        # Create base directory if it doesn't exist
        os.makedirs(self.work_dir, exist_ok=True)
        
        # Create required folders and copy tutorial files (only on first run)
        self.create_required_folders()
        
        # Copy example files from the installed package to the user's data directory on first run
        if is_first_run:
            info_message(self.console, "First run: Copying tutorial files")
            try:
                success = copy_tutorial_files(self.work_dir, self.console)
                if success:
                    success_message(self.console, f"Example files copied to: {self.work_dir}")
                else:
                    warning_message(self.console, "Some example files could not be copied")
            except Exception as e:
                error_message(self.console, f"Error copying example files: {e}")
        
        # Save config to ensure it's created even on first run
        self.save_config()
        
        # Log directory structure
        self.log_directory_structure()
    
    def log_directory_structure(self):
        """Log the current directory structure."""
        info_message(self.console, "Directory structure:")
        info_message(self.console, f"  • Work directory: {self.work_dir}")
        info_message(self.console, f"  • VELS directory: {self.vels_dir}")
        info_message(self.console, f"  • RAW VELS directory: {self.raw_vels_dir}")
        info_message(self.console, f"  • SEGY directory: {self.segy_dir}")
        info_message(self.console, f"  • LOG directory: {os.path.join(self.work_dir, 'LOG')}")

    def save_config(self):
        """Save configuration to file."""
        config = {
            'base_dir': self.work_dir
        }
        try:
            # Ensure the config directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f)
            success_message(self.console, f"Configuration saved to {self.config_path}")
        except Exception as e:
            error_message(self.console, f"Error saving configuration: {str(e)}")

    def create_required_folders(self):
        """Create the necessary folder structure for the application."""
        section_header(self.console, "Creating folder structure")
        # Main folders needed for the application
        required_folders = [
            'SEGY', 
            os.path.join('VELS', '2D'), 
            os.path.join('VELS', 'RAW'),
            'LOG'  # Add LOG folder to required folders
        ]
        
        # Create each folder in the script directory
        for folder in required_folders:
            folder_path = os.path.join(self.work_dir, folder)
            try:
                os.makedirs(folder_path, exist_ok=True)
                success_message(self.console, f"Created directory: {folder_path}")
            except Exception as e:
                error_message(self.console, f"Failed to create directory {folder_path}: {e}")

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

    def set_working_directory(self):
        """Let the user choose a new working directory for data storage."""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Directory for src Data",
            self.work_dir
        )
        
        if directory:
            # Store the old directory for potential data copying
            old_working_dir = self.work_dir
            
            self.work_dir = directory
            
            # Update paths
            self.vels_dir = os.path.join(self.work_dir, "VELS", "2D")
            self.raw_vels_dir = os.path.join(self.work_dir, "VELS", "RAW")
            self.segy_dir = os.path.join(self.work_dir, "SEGY")
            
            # Create directories
            os.makedirs(self.vels_dir, exist_ok=True)
            os.makedirs(self.raw_vels_dir, exist_ok=True)
            os.makedirs(self.segy_dir, exist_ok=True)
            
            # Update console with new directory
            self.console.append(f"Working directory changed to: {self.work_dir}")
            
            # Ask if user wants to copy data from previous directory
            if os.path.exists(old_working_dir) and old_working_dir != self.work_dir:
                reply = QMessageBox.question(
                    self,
                    "Copy Existing Data",
                    f"Do you want to copy existing data from\n{old_working_dir}\nto the new location?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.copy_data(old_working_dir, self.work_dir)
    
    def copy_data(self, source_dir, target_dir):
        """Copy data from old directory to new directory."""
        import shutil
        try:
            # Show progress
            self.status_bar.start("Copying data files...", 100)
            self.console.append("Starting data copy process...")
            
            folders = ['VELS', 'SEGY']
            processed = 0
            
            for folder in folders:
                src_folder = os.path.join(source_dir, folder)
                dst_folder = os.path.join(target_dir, folder)
                
                if os.path.exists(src_folder):
                    # Create target folder if it doesn't exist
                    os.makedirs(dst_folder, exist_ok=True)
                    
                    # Get list of all files to copy
                    all_files = []
                    for root, dirs, files in os.walk(src_folder):
                        for file in files:
                            src_file = os.path.join(root, file)
                            # Create relative path
                            rel_path = os.path.relpath(src_file, src_folder)
                            dst_file = os.path.join(dst_folder, rel_path)
                            # Make sure destination directory exists
                            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                            all_files.append((src_file, dst_file))
                    
                    # Copy files with progress updates
                    total_files = len(all_files)
                    for i, (src_file, dst_file) in enumerate(all_files):
                        shutil.copy2(src_file, dst_file)
                        progress = int((i + 1) / total_files * 50) + processed
                        self.status_bar.update(progress, f"Copying {os.path.basename(src_file)}...")
                
                processed += 50  # Each folder is 50% of the progress
            
            self.status_bar.finish()
            self.console.append("Data copied successfully to new location")
        except Exception as e:
            self.status_bar.finish()
            self.console.append(f"Error copying data: {str(e)}")
            QMessageBox.warning(self, "Copy Error", f"Error copying data: {str(e)}")
    
    def setup_ui_VR2D(self):
        """Set up the user interface."""
        # Variables y configuraciones iniciales
        self.image_path = None
        self.points = []

        # Main layout for the central widget
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 15)  # Left, top, right, bottom
        
        # Title with smaller font
        title_label = QLabel("VelRecover", self.central_widget)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))  
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        main_layout.addSpacing(10)

        # Create controls layout
        controls_layout = QVBoxLayout()
        
        # Load text file button
        load_text_file_button = QPushButton("Load Text File", self)
        load_text_file_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        load_text_file_button.clicked.connect(self.load_text_file)
        controls_layout.addWidget(load_text_file_button)

        # Load SEGY file button
        self.load_segy_file_button = QPushButton("Load SEGY File", self)
        self.load_segy_file_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.load_segy_file_button.clicked.connect(self.load_segy_file)
        self.load_segy_file_button.setEnabled(False)
        controls_layout.addWidget(self.load_segy_file_button)

        # Interpolate button
        self.interpolate2D_button = QPushButton("Interpolate", self)
        self.interpolate2D_button.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.interpolate2D_button.clicked.connect(self.interpolation_2d)
        self.interpolate2D_button.setEnabled(False)
        controls_layout.addWidget(self.interpolate2D_button)

        # Save data buttons
        self.save_data_button = QPushButton("Save Data as TXT", self)
        self.save_data_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.save_data_button.clicked.connect(self.save_vel2D_data_txt)
        self.save_data_button.setEnabled(False)
        controls_layout.addWidget(self.save_data_button)

        self.save_data_bin_button = QPushButton("Save Data as BIN", self)
        self.save_data_bin_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.save_data_bin_button.clicked.connect(self.save_vel2D_data_bin)
        self.save_data_bin_button.setEnabled(False)
        controls_layout.addWidget(self.save_data_bin_button)

        # Show distribution window button
        self.show_distribution_button = QPushButton("Show Velocity Distribution", self)
        self.show_distribution_button.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.show_distribution_button.clicked.connect(self.show_velocity_distribution)
        self.show_distribution_button.setEnabled(False)
        controls_layout.addWidget(self.show_distribution_button)

        # Reset button
        reset_button = QPushButton("Restart", self)
        reset_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        reset_button.clicked.connect(self.restart_process)
        controls_layout.addWidget(reset_button)

        # Add controls layout to main layout
        controls_widget = QWidget()
        controls_widget.setLayout(controls_layout)
        main_layout.addWidget(controls_widget)

        # Gaussian Blur section
        blur_layout = QVBoxLayout()

        # Section title
        blur_title = QLabel("Gaussian Blur", self)
        blur_title.setFont(QFont("Arial", 10, QFont.Bold))
        blur_layout.addWidget(blur_title)
        
        # Blur value input
        blur_value_layout = QHBoxLayout()
        blur_value_label = QLabel("Enter Gaussian Blur Value (1-100):", self)
        self.blur_value_input = QLineEdit(self)
        self.blur_value_input.setValidator(QIntValidator())
        self.blur_value_input.setText("1")  
        blur_value_layout.addWidget(blur_value_label)
        blur_value_layout.addWidget(self.blur_value_input)
        blur_layout.addLayout(blur_value_layout)

        # Apply button
        self.apply_blur_button = QPushButton("Apply Gaussian Blur", self)
        self.apply_blur_button.clicked.connect(self.apply_gaussian_blur)
        self.apply_blur_button.setEnabled(False)
        blur_layout.addWidget(self.apply_blur_button)

        # Add blur layout to main layout
        blur_widget = QWidget()
        blur_widget.setLayout(blur_layout)
        main_layout.addWidget(blur_widget)
        
        # Status bar with progress
        self.status_bar = ProgressStatusBar(self)
        main_layout.addWidget(self.status_bar)

        main_layout.addSpacing(8)  

        console_label = QLabel("CONSOLE OUTPUT", self.central_widget)
        console_label.setFont(QFont("Arial", 10, QFont.Bold))
        main_layout.addWidget(console_label)

        self.console = QTextEdit(self.central_widget)
        self.console.setStyleSheet("font-family: 'Consolas', 'Courier New'; font-size: 9pt;")
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QTextEdit.WidgetWidth) 
        self.console.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_layout.addWidget(self.console)

        main_layout.addSpacing(10)

        # Set the main layout to the central widget
        self.central_widget.setLayout(main_layout)
        
        # Add initial status message showing working directory
        self.console.append(f"Working directory: {self.work_dir}")

    def interpolation_2d(self):
        """Perform 2D interpolation of velocity data and show the results automatically."""
        
        self.is_interpolating = True
        self.interpolate2D_button.setEnabled(False)
        
        self.status_bar.start("Starting interpolation process...", 100)
        self.console.append("Starting interpolation process...")
        
        try:
            # Interpolate data
            result = interpolate_velocity_data(
                self.text_file_path, 
                self.segy_file_path,
                status_callback=self.status_bar.update,
                cancel_check=self.status_bar.wasCanceled
            )
            
            if result['cancelled']:
                self._finalize_interpolation(cancelled=True)
                return
                
            # Store the results
            self.CDP = result['CDP']
            self.TWT = result['TWT']
            self.VEL = result['VEL']
            self.CDP_grid = result['CDP_grid']
            self.TWT_grid = result['TWT_grid']
            self.VEL_grid = result['VEL_grid']
            self.ntraces = result['ntraces']
            self.output_2D_grid = self.VEL_grid
            
            # Display the results
            self.display_velocity_analysis()
            
            self.status_bar.update(100, "Interpolation completed successfully")
            self._finalize_interpolation()
            
        except Exception as e:
            self.console.append(f"Error during interpolation: {str(e)}")
            self.status_bar.showMessage("Error during interpolation")
            self._finalize_interpolation(error=True)
    
    def display_velocity_analysis(self):
        """Display the interpolated velocity data in the analysis window."""
        
        self.status_bar.update(90, "Creating visualization...")
        display_velocity_analysis(
            self.analysis_window.vels_figure, 
            self.CDP_grid, 
            self.TWT_grid, 
            self.VEL_grid,
            self.CDP,
            self.TWT,
            self.VEL,
            self.ntraces
        )
        
        # Show the window
        self.analysis_window.show()
        self.analysis_window.raise_()
        self.analysis_window.activateWindow()
    
    def _finalize_interpolation(self, cancelled=False, error=False):
        """Clean up after interpolation process."""
        self.is_interpolating = False
        self.interpolate2D_button.setEnabled(True)
        
        if cancelled:
            self.status_bar.showMessage("Interpolation cancelled")
            self.console.append("Interpolation process was cancelled by the user")
        elif error:
            pass  # Error message already displayed
        else:
            self.save_data_button.setEnabled(True)
            self.save_data_bin_button.setEnabled(True)
            self.apply_blur_button.setEnabled(True)
            self.console.append("Interpolation completed. You can now apply Gaussian blur or save the data.")
        
        self.status_bar.finish()
    
    def apply_gaussian_blur(self):
        """Apply Gaussian blur to the interpolated velocity data."""
        
        blur_value = int(self.blur_value_input.text())
        self.output_2D_grid = apply_gaussian_blur(self.VEL_grid, blur_value)
        
        # Update visualization
        display_velocity_analysis(
            self.analysis_window.vels_figure, 
            self.CDP_grid, 
            self.TWT_grid, 
            self.output_2D_grid,
            self.CDP,
            self.TWT,
            self.VEL,
            self.ntraces,
            clear_figure=True
        )
    
    def save_vel2D_data_txt(self):
        """Save the velocity data to a .dat file."""        
        result = save_velocity_text_data(
            self.segy_file_path,
            self.CDP_grid,
            self.TWT_grid,
            self.output_2D_grid,
            self.vels_dir
        )
        
        if result['success']:
            self.console.append(f"Data saved to: {result['path']}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to save data: {result['error']}")
    
    def save_vel2D_data_bin(self):
        """Save the velocity data to a binary file."""
        
        result = save_velocity_binary_data(
            self.segy_file_path,
            self.output_2D_grid,
            self.vels_dir
        )
        
        if result['success']:
            self.console.append(f"Data saved to: {result['path']}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to save data: {result['error']}")
    
    def load_segy_file(self):
        """Open a file dialog to select a SEGY file."""
        
        options = QFileDialog.Options()
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SEGY File",
            os.path.join(self.work_dir, "SEGY"),
            "SEGY Files (*.sgy *.segy)",
            options=options
        )
        
        if file_path:
            self.segy_file_path = file_path
            self.console.append(f"SEGY file loaded: {file_path}")
            self.interpolate2D_button.setEnabled(True)
    
    def load_text_file(self):
        """Open a file dialog to select a text file."""
        section_header(self.console, "Loading Text File")
        
        options = QFileDialog.Options()
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Text File",
            os.path.join(self.work_dir, "VELS", "RAW"),
            "Text Files (*.dat *.txt *.tsv *.csv)",
            options=options
        )
        
        if file_path:
            self.text_file_path = file_path
            info_message(self.console, f"Selected text file: {file_path}")
            
            try:
                # First, read the first few lines to detect the delimiter
                with open(file_path, 'r') as f:
                    first_lines = [f.readline() for _ in range(3)]
                
                # Try to determine if it's tab or space delimited
                has_tabs = any('\t' in line for line in first_lines)
                delimiter = '\t' if has_tabs else None  # None will make loadtxt split on any whitespace
                
                info_message(self.console, f"Detected delimiter: {'tab' if has_tabs else 'whitespace'}")
                
                # Load the data with the appropriate delimiter
                data = np.loadtxt(file_path, delimiter=delimiter, skiprows=1)
                
                # Check if we have enough columns
                if data.shape[1] < 3:
                    raise ValueError(f"Expected at least 3 columns (CDP, TWT, VEL), but found {data.shape[1]}")
                
                data = {
                    'CDP': data[:, 0],
                    'TWT': data[:, 1],
                    'VEL': data[:, 2]
                }
            except Exception as e:
                error_message(self.console, f"Error loading text file: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to load text file: {str(e)}")
                return

            if data:
                self.CDP, self.TWT, self.VEL = data['CDP'], data['TWT'], data['VEL']
                self.load_segy_file_button.setEnabled(True)
                self.plot_velocity_distribution()
                self.show_distribution_button.setEnabled(True)
                
                # Log statistics about the loaded data
                stats = {
                    "Number of velocity points": len(self.CDP),
                    "CDP range": f"{min(self.CDP):.0f} - {max(self.CDP):.0f}",
                    "TWT range (ms)": f"{min(self.TWT):.1f} - {max(self.TWT):.1f}",
                    "Velocity range (m/s)": f"{min(self.VEL):.1f} - {max(self.VEL):.1f}"
                }
                summary_statistics(self.console, stats)
                success_message(self.console, f"Successfully loaded {len(self.CDP)} velocity points")
    
    def plot_velocity_distribution(self):
        """Plot velocity distribution in the distribution window."""
        
        if hasattr(self, 'CDP') and len(self.CDP) > 0:
            plot_velocity_distribution(
                self.distribution_window.scatter_canvas,
                self.CDP,
                self.TWT,
                self.VEL
            )
    
    def show_velocity_distribution(self):
        """Show the velocity distribution window."""
        if hasattr(self, 'VEL') and len(self.VEL) > 0:
            self.distribution_window.show()
            self.distribution_window.raise_()
            self.distribution_window.activateWindow()
        else:
            QMessageBox.warning(self, "Warning", "No velocity data available. Please load a text file first.")
    
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
            # Close all popup windows
            self.analysis_window.hide()
            self.distribution_window.hide()
            
            # Call the existing reset method
            self.reset()
    
    def reset(self):
        """Reset the application to its initial state."""
        # Clear data
        self.points = []
        self.CDP = []
        self.TWT = []
        self.VEL = []
        self.text_file_path = None
        self.segy_file_path = None
        
        # Reset figures
        if hasattr(self, 'output_2D_grid'):
            del self.output_2D_grid
            
        # Reset analysis window
        if hasattr(self.analysis_window, 'vels_figure'):
            self.analysis_window.vels_figure.ax.clear()
            self.analysis_window.vels_figure.draw()
            
        # Reset distribution window
        if hasattr(self.distribution_window, 'scatter_canvas'):
            self.distribution_window.scatter_canvas.ax.clear()
            self.distribution_window.scatter_canvas.draw()
        
        # Hide windows
        self.analysis_window.hide()
        self.distribution_window.hide()
        
        # Disable buttons
        self.load_segy_file_button.setEnabled(False)
        self.interpolate2D_button.setEnabled(False)
        self.save_data_button.setEnabled(False)
        self.save_data_bin_button.setEnabled(False)
        self.apply_blur_button.setEnabled(False)
        self.show_distribution_button.setEnabled(False)
        
        # Reset blur value input
        self.blur_value_input.setText("1")
        
        # Clear console
        self.console.clear()
        self.console.append(f"Application reset to initial state.")
        self.console.append(f"Working directory: {self.work_dir}")
        
        # Clear status bar
        self.status_bar.showMessage("")
        self.status_bar.finish()
