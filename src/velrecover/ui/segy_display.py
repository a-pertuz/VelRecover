"""Visualization components for SEGY seismic data."""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, 
    QLabel, QSlider, QSpinBox, QPushButton, QGroupBox, QApplication
)
from PySide6.QtCore import Qt, Signal

import seisio
import seisplot
import numpy as np
import os

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
        
        # Initialize colorbar attribute
        self.colorbar = None
        self.velocity_mappable = None
        
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
        
        self.perc_widget = PercAdjustmentWidget()
        self.perc_widget.valueChanged.connect(self.update_display)
        
        controls_group = QGroupBox("Display Controls")
        controls_layout = QVBoxLayout()
        controls_layout.addWidget(self.perc_widget)
        controls_group.setLayout(controls_layout)
        
        layout.addWidget(self.canvas, 1)
        layout.addWidget(self.toolbar)
        layout.addWidget(controls_group)
    
    def load_and_display_segy(self):
        """Load SEGY data and display it."""
        info_message(self.console, f"Loading SEGY file for visualization: {self.segy_file_path}")
        
        try:
            # Load SEGY file
            sio = seisio.input(self.segy_file_path)
            self.nsamples = sio.nsamples
            self.ntraces = sio.ntraces
            self.dt_ms = sio.vsi / 1000.0  # Convert microseconds to milliseconds
            self.delay = sio.delay
            self.dataset = sio.read_all_traces()
            self.seismic_data = self.dataset["data"]
            
            # Display the data
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
            
            # Safely remove any existing colorbars
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
            
            # Determine velocity range for consistent color scale
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
            
            # Overlay interpolated velocity grid if available
            if self.has_velocity_grid:
                self.overlay_velocity_grid(vmin, vmax)
            
            # Overlay velocity picks if available (on top of everything)
            if self.has_velocity_picks:
                self.overlay_velocity_picks(vmin, vmax)
            
            # Add a single colorbar if we have any velocity data
            if (self.has_velocity_grid or self.has_velocity_picks) and hasattr(self, 'velocity_mappable') and self.velocity_mappable is not None:
                self.colorbar = self.fig.colorbar(self.velocity_mappable, ax=self.ax, label='Velocity (m/s)')
                self.colorbar.ax.tick_params(labelsize=8)
                
            if self.model_type:
                self.ax.set_title(f'SEGY Display with {self.model_type}')
            else:
                self.ax.set_title(f'SEGY Display - {os.path.basename(self.segy_file_path)}')
                        
            self.fig.tight_layout()
            self.canvas.draw()
        
        info_message(self.console, f"Updated SEGY display with {perc}% clip")
    
    def overlay_velocity_picks(self, vmin=None, vmax=None):
        """Overlay velocity picks as colored circles on the SEGY display."""
        if not hasattr(self, 'ax') or not self.has_velocity_picks:
            return
        
        try:
            sample_indices = self._twt_to_sample_index(self.velocity_twt)
            
            scatter = self.ax.scatter(
                self.velocity_cdp,  # X values (CDP/trace)
                sample_indices,    # Y values (converted to sample index)
                c=self.velocity_vel,  # Color based on velocity
                cmap='jet',         # Colormap
                vmin=vmin,          # Min velocity for color scaling
                vmax=vmax,          # Max velocity for color scaling
                s=60,               # Increased size for better visibility
                alpha=0.9,          # Increased opacity
                edgecolors='black', # Border color
                linewidths=0.8,     # Increased border width
                zorder=20           # Highest zorder to ensure visibility on top
            )
            
            # Store mappable for colorbar
            self.velocity_mappable = scatter
            
            info_message(self.console, f"Overlaid {len(self.velocity_cdp)} velocity picks on SEGY display")
            
        except Exception as e:
            warning_message(self.console, f"Error overlaying velocity picks: {str(e)}")

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
                sample_twt_grid,   # Converted Y values to sample indices
                self.vel_grid,
                levels=100,          # Many levels for continuous appearance
                cmap='jet',          # Colormap
                vmin=vmin,           # Min velocity for color scaling
                vmax=vmax,           # Max velocity for color scaling
                alpha=0.5,           # Transparency
                zorder=5             # Middle layer
            )
            
            # Store mappable for colorbar (will override if velocity picks are also displayed)
            self.velocity_mappable = contour
            
            info_message(self.console, f"Displayed interpolated velocity model")
            
        except Exception as e:
            warning_message(self.console, f"Error displaying velocity grid: {str(e)}")

    def _twt_to_sample_index(self, twt):
        """Convert TWT (ms) to sample index for SEGY display."""

        if not hasattr(self, 'delay') or not hasattr(self, 'dt_ms'):
            # If we don't have SEGY timing info, return original value
            return twt
        
        # Convert TWT to sample index: sample_index = (twt - delay) / dt_ms
        sample_index = (twt - self.delay) / self.dt_ms
        
        return sample_index

    def update_velocity_model(self, cdp_grid, twt_grid, vel_grid, model_type=None):
        """Update the velocity model and redraw the display."""

        self.cdp_grid = cdp_grid
        self.twt_grid = twt_grid
        self.vel_grid = vel_grid
        self.model_type = model_type
        self.has_velocity_grid = cdp_grid is not None and twt_grid is not None and vel_grid is not None
        
        # Update the display
        self.update_display(self.perc)

