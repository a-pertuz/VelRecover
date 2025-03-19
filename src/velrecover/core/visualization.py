"""Visualization components for SEGYRecover velocity analysis."""

import numpy as np
import matplotlib.pyplot as plt
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from ..ui.widgets import VelsFigureCanvas, VelScatterCanvas
from ..utils.console_utils import (info_message, success_message, 
                           warning_message, summary_statistics)

class VelocityAnalysisWindow(QMainWindow):
    """Window for displaying velocity analysis results."""
    
    def __init__(self, parent=None, console=None):
        """Initialize velocity analysis window."""
        super().__init__(parent)
        self.console = console
        self.setWindowTitle("Velocity Analysis")
        screen = QApplication.primaryScreen().geometry()
        screen_width = min(screen.width(), 1920)
        screen_height = min(screen.height(), 1080)
        pos_x = int(screen_width * 0.35 + 10)
        pos_y = int(screen_height * 0.05)
        window_width= int(screen_width * 0.6)
        window_height = int(screen_height * 0.9)
        self.setGeometry(pos_x, pos_y, window_width, window_height)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create canvas and toolbar
        self.vels_figure = VelsFigureCanvas(self)
        self.vels_toolbar = NavigationToolbar(self.vels_figure, self)
        
        layout.addWidget(self.vels_toolbar)
        layout.addWidget(self.vels_figure)
        
        if self.console:
            info_message(self.console, "Velocity Analysis window initialized")
            info_message(self.console, f"Window dimensions: {window_width}x{window_height} at position ({pos_x}, {pos_y})")

class VelocityDistributionWindow(QMainWindow):
    """Window for displaying velocity distribution."""
    
    def __init__(self, parent=None, console=None):
        """Initialize velocity distribution window."""
        super().__init__(parent)
        self.console = console
        self.setWindowTitle("Distribution of Velocities")
        screen = QApplication.primaryScreen().geometry()
        screen_width = min(screen.width(), 1920)
        screen_height = min(screen.height(), 1080)
        pos_x = int(screen_width * 0.35 + 10)
        pos_y = int(screen_height * 0.1)
        window_width= int(screen_width * 0.4)
        window_height = int(screen_height * 0.6)
        self.setGeometry(pos_x, pos_y, window_width, window_height)
    
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create canvas and toolbar
        self.scatter_canvas = VelScatterCanvas(self)
        self.scatter_toolbar = NavigationToolbar(self.scatter_canvas, self)
        
        layout.addWidget(self.scatter_toolbar)
        layout.addWidget(self.scatter_canvas)
        
        if self.console:
            info_message(self.console, "Velocity Distribution window initialized")
            info_message(self.console, f"Window dimensions: {window_width}x{window_height} at position ({pos_x}, {pos_y})")

def display_velocity_analysis(canvas, cdp_grid, twt_grid, vel_grid, cdp, twt, vel, ntraces, clear_figure=False, console=None):
    """Display velocity analysis in the given canvas."""
    if console:
        info_message(console, "Generating velocity analysis display...")
        info_message(console, f"Grid shape: CDP={cdp_grid.shape}, TWT={twt_grid.shape}, Velocity={vel_grid.shape}")
        info_message(console, f"Data points: {len(cdp)} CDPs with velocity range [{min(vel):.0f}, {max(vel):.0f}] m/s")
    
    if clear_figure:
        canvas.figure.clear()
        canvas.ax = canvas.figure.add_subplot(111)
    else:
        canvas.ax.clear()
    
    # Draw contour plot
    contour = canvas.ax.contourf(cdp_grid, twt_grid, vel_grid, levels=100, cmap='rainbow')

    # Add labels with velocity values
    for i, label_vel in enumerate(vel):
        canvas.ax.annotate(f'{label_vel:.0f}', (cdp[i], twt[i]), va='center', ha='center', fontsize='8')

    # Add colorbar
    cbar = canvas.figure.colorbar(contour, ax=canvas.ax, orientation='vertical', extend='both', label='Velocity (m/s)')
    cbar.ax.invert_yaxis()  # Invert the direction of the ticks

    # Set axis limits and labels
    canvas.ax.set_xlim(-50, ntraces + 50)
    canvas.ax.set_xticks(range(0, ntraces, 50))
    canvas.ax.set_xticks(list(canvas.ax.get_xticks()) + [ntraces])

    canvas.ax.set_xlabel('CDP')
    canvas.ax.set_ylabel('TWT (ms)')
    canvas.ax.set_title('Interpolated Velocity Analysis')
    canvas.ax.invert_yaxis()
    canvas.draw()
    
    if console:
        success_message(console, "Velocity analysis display generated successfully")
        
        # Log statistics
        stats = {
            "CDP Range": f"{int(min(cdp))} to {int(max(cdp))}",
            "TWT Range (ms)": f"{min(twt):.1f} to {max(twt):.1f}",
            "Velocity Range (m/s)": f"{min(vel):.1f} to {max(vel):.1f}",
            "Number of picks": len(cdp),
            "Number of traces": ntraces
        }
        summary_statistics(console, stats)

def plot_velocity_distribution(canvas, cdp, twt, vel, console=None):
    """Plot velocity distribution in the given canvas."""
    if console:
        info_message(console, "Generating velocity distribution plot...")
    
    canvas.ax.clear()

    # Check if the data is not empty
    if len(vel) == 0 or len(twt) == 0:
        if console:
            warning_message(console, "No velocity data to display")
        return

    # Get unique CDP values and assign colors
    unique_cdps = np.unique(cdp)
    colors = plt.cm.rainbow(np.linspace(0, 1, len(unique_cdps)))
    
    if console:
        info_message(console, f"Plotting {len(vel)} velocity points across {len(unique_cdps)} CDPs")

    # Plot scatter for each CDP
    for cdp_val, color in zip(unique_cdps, colors):
        mask = cdp == cdp_val
        velocities = vel[mask]
        twts = twt[mask]
        
        # Plot the scatter points
        canvas.ax.scatter(velocities, twts, color=color, label=f'{int(cdp_val)}')

        # Plot dashed line connecting the points
        sorted_indices = np.argsort(velocities)  # Ensure the points are plotted in order of velocity
        canvas.ax.plot(
            velocities[sorted_indices],
            twts[sorted_indices],
            color=color,
            linestyle='--',
            alpha=0.2
        )

    # Set labels and title
    canvas.ax.set_xlabel('Velocity (m/s)')
    canvas.ax.set_ylabel('TWT (ms)')
    canvas.ax.set_title('Velocity Distribution by CDP')

    # Set aspect ratio and axis limits
    canvas.ax.set_aspect(2)
    canvas.ax.set_xlim(min(vel) * 0.9, max(vel) * 1.1)
    canvas.ax.set_ylim(0, max(twt) * 1.1)

    # Add legend
    canvas.ax.legend(title='CDP', loc='upper left', bbox_to_anchor=(1.05, 1), borderaxespad=0.)
    
    # Adjust layout and redraw
    canvas.figure.tight_layout(pad=5.0)
    canvas.draw()
    
    if console:
        success_message(console, "Velocity distribution plot generated successfully")
        
        vel_stats = {
            "CDP Count": len(unique_cdps),
            "Min Velocity": f"{min(vel):.1f} m/s",
            "Max Velocity": f"{max(vel):.1f} m/s",
            "Avg Velocity": f"{np.mean(vel):.1f} m/s",
            "Min TWT": f"{min(twt):.1f} ms",
            "Max TWT": f"{max(twt):.1f} ms"
        }
        summary_statistics(console, vel_stats)
