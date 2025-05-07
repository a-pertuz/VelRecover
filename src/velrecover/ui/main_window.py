"""Main window for VelRecover application."""
import matplotlib
matplotlib.use('QtAgg')
import os
import json
import subprocess
from PySide6.QtGui import QFont, QAction
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QStatusBar, QProgressBar, QVBoxLayout, QLabel, 
    QPushButton, QMessageBox, QWidget, QTextEdit, QStyle, QDialog, 
    QFileDialog, QMainWindow, QSplitter, QHBoxLayout
)

import appdirs

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

# Import the dialogs and resource utilities
from .help_dialogs import AboutDialog, FirstRunDialog
from ..utils.resource_utils import copy_tutorial_files
from ..utils.console_utils import (
    section_header, success_message, error_message, 
    warning_message, info_message, progress_message,
    summary_statistics, initialize_log_file, close_log_file
)

# Imports for the tabbed interface
from .navigation_panel import NavigationPanel
from .tab_container import TabContainer
from ._0_welcome_tab import WelcomeTab
from ._1_load_data_tab import LoadDataTab
from ._2_edit_tab import EditTab
from ._3_interpolate_tab import InterpolateTab

class ProgressStatusBar(QStatusBar):
    """Status bar with integrated progress bar."""

    def __init__(self, parent=None):
        """Initialize the progress status bar.""" 
        super().__init__(parent)
        self.setObjectName("status_bar")
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(15)
        self.progress_bar.setMaximumWidth(200)
        
        # Create cancel button
        self.cancel_button = QPushButton()
        self.cancel_button.setObjectName("cancel_button")
        self.cancel_button.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel)
        
        # Add widgets to status bar
        self.addPermanentWidget(self.progress_bar)
        self.addPermanentWidget(self.cancel_button)
        
        self._canceled = False
        
    def start(self, title, maximum):
        self._canceled = False
        self.showMessage(title)
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.cancel_button.setVisible(True)
        QApplication.processEvents()
        
    def update(self, value, message=None):
        if message:
            self.showMessage(message)
        self.progress_bar.setValue(value)
        QApplication.processEvents()
        
    def finish(self):
        self.clearMessage()
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
    
    def wasCanceled(self):
        """Check if the operation was canceled."""
        return self._canceled
    
    def cancel(self):
        """Cancel the current operation."""
        self._canceled = True

class VelRecover(QMainWindow):
    """Main application widget for VelRecover."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("main_window")
        
        # Make window dimensions consistent with bigger size for the tabbed UI
        self.setMinimumSize(1200, 800)
        
        # Get appropriate directories for user data and config
        self.app_name = "VelRecover"
        self.user_data_dir = appdirs.user_data_dir(self.app_name)
        self.user_config_dir = appdirs.user_config_dir(self.app_name)
        
        # Ensure config directory exists
        os.makedirs(self.user_config_dir, exist_ok=True)
        self.config_path = os.path.join(self.user_config_dir, 'config.json')
        
        self.load_config()
        
        # Initialize state variables for velocity data
        self.velocity_data = None
        self.velocity_file_path = None
        self.interpolated_data = None
        
        self.create_required_folders()

        # Initialize the central widget with a horizontal layout
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        self.setCentralWidget(self.central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.create_menu_bar()
        
        # Create navigation panel and add to main layout
        self.navigation_panel = NavigationPanel()
        self.navigation_panel.setObjectName("navigation_panel")
        self.navigation_panel.navigationChanged.connect(self.handle_navigation_change)
        main_layout.addWidget(self.navigation_panel)
        
        # Create container for main content (tabs + console)
        content_container = QWidget()
        content_container.setObjectName("content_container")
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(0)
        
        # Create tab container
        self.tab_container = TabContainer()
        self.tab_container.setObjectName("tab_container")
        content_layout.addWidget(self.tab_container, 1)  # 1 = stretch factor
        
        # Create and add console
        self.console = QTextEdit()
        self.console.setObjectName("console")  
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.console.setMinimumWidth(300)
        self.console.setMaximumWidth(400)
        content_layout.addWidget(self.console)
        
        # Add content container to main layout
        main_layout.addWidget(content_container, 1)  # 1 = stretch factor
        
        # Create the progress bar as the main window's status bar
        self.progress = ProgressStatusBar()
        self.setStatusBar(self.progress)
        
        # Initialize tabs
        self.initialize_tabs()
        
        # Initialize log file
        self.log_path = initialize_log_file(self.work_dir)
        
        # Show initial message in console
        section_header(self.console, "Welcome to VelRecover")
        info_message(self.console, "Application initialized")
        info_message(self.console, f"Data directory: {self.work_dir}")
        if self.log_path:
            info_message(self.console, f"Log file created at: {self.log_path}")
        success_message(self.console, "Application ready")
        
        # Initialize with the welcome tab
        self.navigation_panel.set_active("welcome")
        self.tab_container.switch_to("welcome")
        
        # Disable tabs that require prior steps
        self.navigation_panel.enable_tabs_until("welcome")
    
    def handle_navigation_change(self, identifier):
        """Handle navigation changes from the side panel."""
        self.tab_container.switch_to(identifier)
    
    def initialize_tabs(self):
        """Initialize all the tab content."""
        # Welcome tab
        welcome_tab = WelcomeTab()
        welcome_tab.newVelocityRequested.connect(self.start_new_velocity_field)
        self.tab_container.add_tab("welcome", welcome_tab)
        
        # Load Data tab
        load_data_tab = LoadDataTab(self.console, self.work_dir)
        load_data_tab.dataLoaded.connect(self.handle_data_loaded)
        load_data_tab.proceedRequested.connect(lambda: self.proceed_to_tab("edit"))
        self.tab_container.add_tab("load_data", load_data_tab)
        
        # Edit tab
        edit_tab = EditTab(self.console, self.work_dir)
        edit_tab.editingCompleted.connect(self.handle_editing_completed)
        edit_tab.proceedRequested.connect(lambda: self.proceed_to_tab("interpolate"))
        self.tab_container.add_tab("edit", edit_tab)
        
        # Interpolate tab
        interpolate_tab = InterpolateTab(self.console, self.work_dir)
        interpolate_tab.interpolationCompleted.connect(self.handle_interpolation_completed)
        interpolate_tab.proceedRequested.connect(lambda: self.proceed_to_tab("save"))
        self.tab_container.add_tab("interpolate", interpolate_tab)
        

    
    def start_new_velocity_field(self):
        """Start a new velocity field processing workflow."""
        # Reset state
        self.velocity_data = None
        self.velocity_file_path = None
        self.interpolated_data = None
        
        # Reset all tabs
        for tab_id in ["load_data", "edit", "interpolate"]:
            widget = self.tab_container.widget(self.tab_container.tab_indices[tab_id])
            if hasattr(widget, "reset"):
                widget.reset()
        
        # Switch to load data tab and enable only this step
        self.proceed_to_tab("load_data")
        self.navigation_panel.enable_tabs_until("load_data")
        
        # Clear console and show message
        self.console.clear()
        section_header(self.console, "New Velocity Field")
        info_message(self.console, "Starting new velocity field workflow")
        info_message(self.console, "Please load velocity data")
    
    def proceed_to_tab(self, tab_id):
        """Switch to specified tab and update navigation."""
        self.tab_container.switch_to(tab_id)
        self.navigation_panel.set_active(tab_id)
        
        # Special handling for specific tabs
        if tab_id == "edit" and self.velocity_data is not None:
            # Update edit tab with loaded data
            edit_tab = self.tab_container.widget(self.tab_container.tab_indices["edit"])
            if hasattr(edit_tab, "update_with_data"):
                edit_tab.update_with_data(self.velocity_data)
        
        elif tab_id == "interpolate" and self.velocity_data is not None:
            # Update interpolate tab with processed data
            interpolate_tab = self.tab_container.widget(self.tab_container.tab_indices["interpolate"])
            if hasattr(interpolate_tab, "update_with_data"):
                interpolate_tab.update_with_data(self.velocity_data)
        
        elif tab_id == "save" and self.interpolated_data is not None:
            # Update save tab with interpolated data
            save_tab = self.tab_container.widget(self.tab_container.tab_indices["save"])
            if hasattr(save_tab, "update_with_data"):
                save_tab.update_with_data(self.interpolated_data)
    
    def handle_data_loaded(self, file_path, data):
        """Handle signal from LoadDataTab when data is loaded."""
        self.velocity_file_path = file_path
        self.velocity_data = data
        
        # Log to console
        success_message(self.console, f"Loaded velocity data from: {file_path}")
        
        # Enable navigation to next step
        self.navigation_panel.enable_tabs_until("edit")
    
    def handle_editing_completed(self, edited_data):
        """Handle signal from EditTab when editing is complete."""
        self.velocity_data = edited_data
        
        # Log to console
        success_message(self.console, "Velocity data editing completed")
        
        # Enable navigation to next step
        self.navigation_panel.enable_tabs_until("interpolate")
    
    def handle_interpolation_completed(self, interpolated_data):
        """Handle signal from InterpolateTab when interpolation is complete."""
        self.interpolated_data = interpolated_data
        
        # Log to console
        success_message(self.console, "Velocity field interpolation completed")
        
        # Enable navigation to next step
        self.navigation_panel.enable_tabs_until("save")
    
    
    def create_menu_bar(self):
        """Create the menu bar with file and help menus."""
        menu_bar = self.menuBar()
        menu_bar.setObjectName("menu_bar")
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        # Set directory action
        set_dir_action = QAction("Set Data Directory", self)
        set_dir_action.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        set_dir_action.setShortcut("Ctrl+D")
        set_dir_action.triggered.connect(self.set_base_directory)
        file_menu.addAction(set_dir_action)
        
        # Open directory action
        open_dir_action = QAction("Open Data Directory", self)
        open_dir_action.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        open_dir_action.setShortcut("Ctrl+O")
        open_dir_action.triggered.connect(self.open_work_directory)
        file_menu.addAction(open_dir_action)
        
        # Exit action
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def open_work_directory(self):
        """Open the current work directory in the file explorer."""
        try:
            if os.path.exists(self.work_dir):
                if os.name == 'nt':  # Windows
                    os.startfile(self.work_dir)
                elif os.name == 'posix':  # macOS and Linux
                    if os.uname().sysname == 'Darwin':  # macOS
                        subprocess.run(['open', self.work_dir])
                    else:  # Linux
                        subprocess.run(['xdg-open', self.work_dir])
                info_message(self.console, f"Opened data directory: {self.work_dir}")
            else:
                warning_message(self.console, f"Directory not found: {self.work_dir}")
                QMessageBox.warning(self, "Directory Not Found", 
                                   f"The directory {self.work_dir} does not exist.")
        except Exception as e:
            error_message(self.console, f"Could not open directory: {str(e)}")
            QMessageBox.warning(self, "Error", f"Could not open directory: {str(e)}")

    def load_config(self):
        """Load configuration from file or create default."""
        # Default location from appdirs
        default_base_dir = os.path.join(self.user_data_dir, 'data')
        
        # Check if this is first run (config file doesn't exist)
        is_first_run = not os.path.exists(self.config_path)
        
        if is_first_run:
            # Show first run dialog
            dialog = FirstRunDialog(self, default_base_dir)
            result = dialog.exec()
            
            if result == QDialog.Accepted:
                base_dir = dialog.get_selected_location()
            else:
                # Use default if dialog was canceled
                base_dir = default_base_dir
                
            # Create a new config file
            config = {'base_dir': base_dir}
        else:
            # Load existing config
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    base_dir = config.get('base_dir', default_base_dir)
            except Exception as e:
                base_dir = default_base_dir
                config = {'base_dir': base_dir}
                print(f"Error loading config: {e}")
            
        # Set work_dir to base_dir
        self.base_dir = base_dir
        self.work_dir = base_dir
        
        # Create base directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)
        
        self.create_required_folders()
        
        # Copy example files from the installed package to the user's data directory on first run
        if is_first_run:
            try:
                copy_tutorial_files(self.base_dir)
                print(f"Example files copied to: {self.base_dir}")
            except Exception as e:
                print(f"Error copying example files: {e}")
        
        # Save config to ensure it's created even on first run
        self.save_config()

    def save_config(self):
        """Save configuration to file."""
        config = {
            'base_dir': self.base_dir
        }
        try:
            # Ensure the config directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            if hasattr(self, 'console'):
                self.console.append(f"Error saving configuration: {str(e)}")
            else:
                print(f"Error saving configuration: {str(e)}")
             
    def set_base_directory(self):
        """Let the user choose the base directory for data storage."""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Base Directory for Data Storage",
            self.base_dir
        )
        
        if directory:
            old_work_dir = self.work_dir
            self.base_dir = directory
            self.work_dir = directory
            self.save_config()
            
            # Update UI with path
            self.console.append(f"Data directory changed to: {self.work_dir}")
            
            # Create required folders in new directory
            self.create_required_folders()
                
            # Ask if user wants to copy existing data if we had a previous directory
            if os.path.exists(old_work_dir) and old_work_dir != self.work_dir:
                reply = QMessageBox.question(
                    self, 
                    "Copy Existing Data",
                    f"Do you want to copy existing data from\n{old_work_dir}\nto the new location?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.copy_data(old_work_dir, self.work_dir)

    def copy_data(self, source_dir, target_dir):
        """Copy data from old directory to new directory."""
        import shutil
        try:
            folders = ['SEGY', 'VELS']
            for folder in folders:
                src_folder = os.path.join(source_dir, folder)
                dst_folder = os.path.join(target_dir, folder)
                
                if os.path.exists(src_folder):
                    # Create target folder if it doesn't exist
                    os.makedirs(dst_folder, exist_ok=True)
                    
                    # Copy all files from source to target
                    for item in os.listdir(src_folder):
                        src_item = os.path.join(src_folder, item)
                        dst_item = os.path.join(dst_folder, item)
                        if os.path.isfile(src_item):
                            shutil.copy2(src_item, dst_item)
                        elif os.path.isdir(src_item):
                            shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
            
            self.console.append("Data copied successfully to new location")
        except Exception as e:
            self.console.append(f"Error copying data: {str(e)}")
            QMessageBox.warning(self, "Copy Error", f"Error copying data: {str(e)}")

    def show_about_dialog(self):
        """Show the About dialog."""
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def create_required_folders(self):
        """Create the necessary folder structure for the application."""
        # Main folders needed for the application
        required_folders = [
            'SEGY', 
            'VELS', 
            'VELS/RAW', 
            'VELS/INTERPOLATED/TXT',
            'VELS/INTERPOLATED/BIN', 
            'VELS/CUSTOM'
        ]
        
        # Create each folder in the script directory
        for folder in required_folders:
            folder_path = os.path.join(self.work_dir, folder)
            try:
                os.makedirs(folder_path, exist_ok=True)
                if hasattr(self, 'console'):
                    self.console.append(f"Folder created: {folder_path}")
            except Exception as e:
                if hasattr(self, 'console'):
                    self.console.append(f"Error creating folder {folder_path}: {str(e)}")
                else:
                    print(f"Error creating folder {folder_path}: {str(e)}")

    def closeEvent(self, event):
        """Handle application close event."""
        # Close log file properly
        close_log_file()
        
        # Continue with regular close event
        event.accept()