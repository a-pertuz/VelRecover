"""Visualization components for SEGY seismic data."""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, 
    QLabel, QSlider, QSpinBox, QPushButton, QGroupBox, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, Signal

import seisio
import seisplot
import numpy as np
import os

from .custom_picks import CustomPicksManager
from ..utils.console_utils import info_message, warning_message, success_message

class PercAdjustmentWidget(QWidget):
    """Widget for adjusting percentile clipping of seismic display."""
    
    valueChanged = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setMaximumHeight(50)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Slider for percentile adjustment
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(50)
        self.slider.setMaximum(100)
        self.slider.setValue(95)
        self.slider.setTracking(True)
        
        # Spinbox for precise percentile value
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(50)
        self.spinbox.setMaximum(100)
        self.spinbox.setValue(95)
        
        # Update button
        self.update_btn = QPushButton("Update")
        self.update_btn.setToolTip("Update display with new percentile value")
        
        # Add widgets to layout
        layout.addWidget(QLabel("Percentile:"))
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.spinbox)
        layout.addWidget(self.update_btn)
        
        # Connect signals
        self.slider.valueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)
        self.update_btn.clicked.connect(self._emit_value_changed)
    
    def _emit_value_changed(self):
        """Emit the value changed signal with the current percentile value."""
        self.valueChanged.emit(self.spinbox.value())
    
    def get_perc(self):
        """Get the current percentile value."""
        return self.spinbox.value()

class SegyDisplayWindow(QDialog):
    """Window for displaying SEGY seismic data."""
    
    def __init__(self, segy_file_path, parent=None, console=None, cdp=None, twt=None, vel=None, 
                 cdp_grid=None, twt_grid=None, vel_grid=None, model_type=None):
        super().__init__(parent)
        self.console = console
        self.parent = parent
        self.segy_file_path = segy_file_path
        self.setWindowTitle(f"SEGY Viewer - {segy_file_path}")
        
        # Store velocity pick data
        self.velocity_cdp = cdp
        self.velocity_twt = twt
        self.velocity_vel = vel
        self.has_velocity_picks = cdp is not None and twt is not None and vel is not None
        
        # Store interpolated velocity grid
        self.cdp_grid = cdp_grid
        self.twt_grid = twt_grid
        self.vel_grid = vel_grid
        self.model_type = model_type
        self.has_velocity_grid = cdp_grid is not None and twt_grid is not None and vel_grid is not None
        
        # Initialize custom picks manager
        self.text_file_path = None
        if hasattr(parent, 'velocity_data') and parent.velocity_data.text_file_path:
            self.text_file_path = parent.velocity_data.text_file_path
        
        # Initialize custom picks manager
        self.custom_picks_manager = CustomPicksManager(self, console)
        
        # Initialize with existing picks if available
        if self.has_velocity_picks:
            self.custom_picks_manager.initialize_from_existing(cdp, twt, vel, self.text_file_path)
        
        # Initialize colorbar attribute
        self.colorbar = None
        self.velocity_mappable = None
        
        # Initialize custom picks mode flag
        self.custom_picks_mode = False
        
        # Don't automatically delete when closed
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        # Set size and position
        screen = QApplication.primaryScreen().geometry()
        screen_width = min(screen.width(), 1920)
        screen_height = min(screen.height(), 1080)
        pos_x = int(screen_width * 0.3 + 10)
        pos_y = int(screen_height * 0.05)
        window_width = int(screen_width * 0.65)
        window_height = int(screen_height * 0.85)
        self.setGeometry(pos_x, pos_y, window_width, window_height)
        
        # Setup UI
        self.setup_ui()
        
        # Load and display SEGY
        self.load_and_display_segy()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Create controls layout
        controls_group = QGroupBox("Display Controls")
        controls_layout = QVBoxLayout()
        
        # Add percentile adjustment widget
        self.perc_widget = PercAdjustmentWidget()
        self.perc_widget.valueChanged.connect(self.update_display)
        controls_layout.addWidget(self.perc_widget)
        
        # Create custom pick controls
        custom_pick_layout = QHBoxLayout()
        self.custom_pick_label = QLabel("Custom Pick Mode: OFF")
        
        # Add save and exit custom pick mode button
        self.save_exit_button = QPushButton("Save and Exit Custom Pick Mode")
        self.save_exit_button.setToolTip("Save custom picks to a file and exit custom pick mode")
        self.save_exit_button.setEnabled(False)
        self.save_exit_button.clicked.connect(self.save_and_exit_custom_picks_mode)
        
        # Add cancel button for custom pick mode
        self.cancel_button = QPushButton("Cancel Custom Pick Mode")
        self.cancel_button.setToolTip("Exit custom pick mode without saving changes")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_custom_picks_mode)
        
        # Add delete pick button
        self.delete_pick_button = QPushButton("Delete Pick")
        self.delete_pick_button.setEnabled(False)
        self.delete_pick_button.setToolTip("Click this, then click on a pick to delete it")
        self.delete_pick_button.clicked.connect(self.toggle_delete_mode)
        
        custom_pick_layout.addWidget(self.custom_pick_label)
        custom_pick_layout.addWidget(self.save_exit_button)
        custom_pick_layout.addWidget(self.cancel_button)
        custom_pick_layout.addWidget(self.delete_pick_button)
        
        # Add layout to controls
        controls_layout.addLayout(custom_pick_layout)
        controls_group.setLayout(controls_layout)
        
        # Add canvas and controls to main layout
        layout.addWidget(self.canvas, 1)
        layout.addWidget(self.toolbar)
        layout.addWidget(controls_group)
        
        # Connect mouse click event
        self.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Initialize delete mode flag
        self.delete_mode = False
    
    def enable_custom_picks_mode(self, enable=True):
        """Enable or disable custom picks mode."""
        self.custom_picks_mode = enable
        self.custom_picks_manager.enable_custom_picks_mode(enable)
        
        status_text = "ON" if enable else "OFF"
        self.custom_pick_label.setText(f"Custom Pick Mode: {status_text}")
        
        # Enable buttons for custom pick mode
        self.save_exit_button.setEnabled(enable)
        self.cancel_button.setEnabled(enable)
        self.delete_pick_button.setEnabled(enable and self.custom_picks_manager.has_picks)
        
        # Reset delete mode if disabling
        if not enable:
            self.delete_mode = False
            self.delete_pick_button.setText("Delete Pick")
        
        # Update display to highlight custom picks if any
        self.update_display()
        
    def on_click(self, event):
        """Handle mouse click events on the canvas."""
        if self.custom_picks_manager.handle_click(event, self.delete_mode, self._sample_index_to_twt):
            # Update delete button state
            self.delete_pick_button.setEnabled(self.custom_picks_mode and self.custom_picks_manager.has_picks)
            
            # Update velocity data based on custom picks
            cdp, twt, vel = self.custom_picks_manager.get_picks()
            self.velocity_cdp = cdp
            self.velocity_twt = twt
            self.velocity_vel = vel
            self.has_velocity_picks = len(cdp) > 0
            
            # Update the display
            self.update_display()
    
    def _sample_index_to_twt(self, sample_index):
        """Convert sample index to TWT (ms) for SEGY display."""
        if not hasattr(self, 'delay') or not hasattr(self, 'dt_ms'):
            # If we don't have SEGY timing info, return original value
            return sample_index
        
        # Convert sample index to TWT: twt = sample_index * dt_ms + delay
        twt = sample_index * self.dt_ms + self.delay
        
        return twt
    
    def save_and_exit_custom_picks_mode(self):
        """Save custom picks to a file and exit custom pick mode."""
        if not self.custom_picks_mode:
            return
            
        # Save custom picks using CustomPicksManager
        success, file_path = self.custom_picks_manager.save_custom_picks()
        
        if success and file_path and self.parent:
            # If successful, automatically load the file through the parent
            if hasattr(self.parent, 'load_text_file_path'):
                info_message(self.console, f"Custom picks saved successfully. Loading for interpolation.")
                self.parent.load_text_file_path(file_path)
                
                # Automatically reload the SEGY file to ensure everything is properly synchronized
                if hasattr(self.parent, 'velocity_data') and self.parent.velocity_data.segy_file_path:
                    segy_path = self.parent.velocity_data.segy_file_path
                    info_message(self.console, "Reloading SEGY file to ensure data synchronization")
                    self.parent.load_segy_file_path(segy_path)
                
        # Exit custom pick mode regardless of save success
        if success or QMessageBox.question(self, 
                                        "Exit Pick Mode", 
                                        "Save failed. Exit custom pick mode anyway?",
                                        QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.enable_custom_picks_mode(False)
    
    def cancel_custom_picks_mode(self):
        """Exit custom pick mode without saving changes."""
        if not self.custom_picks_mode:
            return
            
        # Ask for confirmation if there are unsaved changes
        if self.custom_picks_manager.has_picks:
            reply = QMessageBox.question(
                self,
                "Cancel Custom Picks",
                "Exit custom pick mode without saving changes?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        # Reset to original picks
        self.custom_picks_manager.reset()
        
        # Update velocity data with original picks
        cdp, twt, vel = self.custom_picks_manager.get_picks()
        self.velocity_cdp = cdp
        self.velocity_twt = twt
        self.velocity_vel = vel
        self.has_velocity_picks = len(cdp) > 0
        
        # Exit custom pick mode
        self.enable_custom_picks_mode(False)
        
        info_message(self.console, "Custom pick mode cancelled, changes discarded")
    
    def overlay_velocity_picks(self, vmin=None, vmax=None):
        """Overlay velocity picks as colored circles on the SEGY display."""
        if not hasattr(self, 'ax') or not self.has_velocity_picks:
            return
        
        # Use CustomPicksManager to overlay picks
        return self.custom_picks_manager.overlay_velocity_picks(self.ax, vmin, vmax)
    
    def toggle_delete_mode(self):
        """Toggle delete pick mode."""
        if not self.custom_picks_mode:
            return
        
        self.delete_mode = not self.delete_mode
        self.delete_pick_button.setText("Cancel Delete" if self.delete_mode else "Delete Pick")
        
        info_message(self.console, "Delete pick mode enabled - click a pick to delete it" if self.delete_mode else "Delete pick mode disabled")
    
    def load_and_display_segy(self):
        """Load SEGY data and display it."""
        info_message(self.console, f"Loading SEGY file for visualization: {self.segy_file_path}")
        try:
            sio = seisio.input(self.segy_file_path)
            self.nsamples = sio.nsamples
            self.ntraces = sio.ntraces
            self.dt_ms = sio.vsi / 1000.0
            self.delay = sio.delay
            self.dataset = sio.read_all_traces()
            self.seismic_data = self.dataset["data"]
            self.update_display(self.perc_widget.get_perc())
            success_message(self.console, f"SEGY data loaded: {self.ntraces} traces, {self.nsamples} samples")
        except Exception as e:
            warning_message(self.console, f"Error loading SEGY file: {str(e)}")
            self.ax.clear()
            self.ax.text(0.5, 0.5, f"Error loading SEGY file:\n{str(e)}", 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
    
    def update_display(self, perc=95):
        """Update the display with the current percentile value."""
        if perc is not None:
            self.perc = perc
        if hasattr(self, 'seismic_data') and self.seismic_data is not None:
            self.ax.clear()
            if hasattr(self, 'colorbar') and self.colorbar is not None:
                try:
                    self.colorbar.remove()
                except (AttributeError, KeyError, ValueError):
                    self.fig.clear()
                    self.ax = self.fig.add_subplot(111)
                finally:
                    self.colorbar = None
            seisplot.plot(self.seismic_data, 
                        perc=self.perc, 
                        haxis="tracf", 
                        hlabel="Trace Number",
                        vlabel="Time (ms)",
                        colormap='gray',
                        ax=self.ax
                        )  
            vmin, vmax = None, None
            if self.has_velocity_picks:
                vmin = np.min(self.velocity_vel)
                vmax = np.max(self.velocity_vel)
            if self.has_velocity_grid:
                grid_vmin = np.min(self.vel_grid)
                grid_vmax = np.max(self.vel_grid)
                if vmin is None or grid_vmin < vmin:
                    vmin = grid_vmin
                if vmax is None or grid_vmax > vmax:
                    vmax = grid_vmax
            if self.has_velocity_grid:
                self.overlay_velocity_grid(vmin, vmax)
            if self.has_velocity_picks:
                self.overlay_velocity_picks(vmin, vmax)
            if (self.has_velocity_grid or self.has_velocity_picks) and hasattr(self, 'velocity_mappable') and self.velocity_mappable is not None:
                self.colorbar = self.fig.colorbar(self.velocity_mappable, ax=self.ax, label='Velocity (m/s)')
                self.colorbar.ax.tick_params(labelsize=8)
                self.colorbar.ax.invert_yaxis()
            if self.model_type:
                self.ax.set_title(f'SEGY Display with {self.model_type}')
            else:
                self.ax.set_title(f'SEGY Display - {os.path.basename(self.segy_file_path)}')
            self.fig.tight_layout()
            self.canvas.draw()
        info_message(self.console, f"Updated SEGY display with {perc}% clip")
    
    def overlay_velocity_grid(self, vmin=None, vmax=None):
        """Overlay interpolated velocity grid as a transparent color map."""
        if not self.has_velocity_grid:
            return
        try:
            sample_twt_grid = np.zeros_like(self.twt_grid)
            for i in range(self.twt_grid.shape[0]):
                for j in range(self.twt_grid.shape[1]):
                    sample_twt_grid[i, j] = self._twt_to_sample_index(self.twt_grid[i, j])
            contour = self.ax.contourf(
                self.cdp_grid, 
                sample_twt_grid,   
                self.vel_grid,
                levels=100,          
                cmap='jet',          
                vmin=vmin,           
                vmax=vmax,           
                alpha=0.5,           
                zorder=5             
            )
            self.velocity_mappable = contour
            info_message(self.console, f"Displayed interpolated velocity model")
        except Exception as e:
            warning_message(self.console, f"Error displaying velocity grid: {str(e)}")

    def _twt_to_sample_index(self, twt):
        """Convert TWT (ms) to sample index for SEGY display."""
        if not hasattr(self, 'delay') or not hasattr(self, 'dt_ms'):
            return twt
        return (twt - self.delay) / self.dt_ms

    def update_velocity_model(self, cdp_grid, twt_grid, vel_grid, model_type=None):
        """Update the velocity model and redraw the display."""
        self.cdp_grid = cdp_grid
        self.twt_grid = twt_grid
        self.vel_grid = vel_grid
        self.model_type = model_type
        self.has_velocity_grid = cdp_grid is not None and twt_grid is not None and vel_grid is not None
        self.update_display(self.perc)

