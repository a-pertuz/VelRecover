"""Module for velocity distribution visualization."""

import numpy as np
import matplotlib.pyplot as plt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QApplication
from PySide6.QtCore import Qt
from scipy import stats
from scipy.optimize import curve_fit

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from ..utils.console_utils import info_message, warning_message, success_message, summary_statistics

class VelScatterCanvas(FigureCanvas):
    """Canvas for displaying velocity scatter plots."""
    
    def __init__(self, parent=None, fc='none'):
        """Initialize canvas with a figure."""
        from matplotlib.figure import Figure
        fig = Figure(facecolor=fc)
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

class VelocityDistributionWindow(QDialog):
    """Window for displaying velocity distribution."""
    
    def __init__(self, parent=None, console=None):
        """Initialize velocity distribution window."""
        super().__init__(parent)
        self.console = console
        self.setWindowTitle("Distribution of Velocities")
        
        # Don't automatically delete the window when closed
        # This allows the window to be hidden and shown again
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        # Set dialog to close when the main window closes
        if parent:
            self.setWindowFlags(self.windowFlags() | Qt.Dialog)
        
        screen = QApplication.primaryScreen().geometry()
        screen_width = min(screen.width(), 1920)
        screen_height = min(screen.height(), 1080)
        pos_x = int(screen_width * 0.35 + 10)
        pos_y = int(screen_height * 0.1)
        window_width= int(screen_width * 0.35)
        window_height = int(screen_height * 0.6)
        self.setGeometry(pos_x, pos_y, window_width, window_height)
    
        layout = QVBoxLayout(self)
        
        # Create canvas and toolbar
        self.scatter_canvas = VelScatterCanvas(self)
        self.scatter_toolbar = NavigationToolbar(self.scatter_canvas, self)
        
        # Add figure first, then toolbar below it
        layout.addWidget(self.scatter_canvas)
        layout.addWidget(self.scatter_toolbar)
        
        if self.console:
            info_message(self.console, "Velocity Distribution window initialized")
            info_message(self.console, f"Window dimensions: {window_width}x{window_height} at position ({pos_x}, {pos_y})")

def plot_velocity_distribution(canvas, cdp, twt, vel, console=None, window_size=None, regression_params=None):
    """Plot velocity distribution in the given canvas."""
    if console:
        info_message(console, "Generating velocity distribution plot...")
    
    # Clear the figure completely to avoid artifacts
    canvas.figure.clear()
    canvas.ax = canvas.figure.add_subplot(111)

    # Get unique CDP values and assign random colors
    unique_cdps = np.unique(cdp)
    np.random.seed(42) 
    colors = np.random.random((len(unique_cdps), 3))  

    hsv_colors = plt.matplotlib.colors.rgb_to_hsv(colors)
    hsv_colors[:, 1] = 0.7 + 0.3 * np.random.random(len(unique_cdps))  # Saturation 0.7-1.0
    hsv_colors[:, 2] = 0.7 + 0.3 * np.random.random(len(unique_cdps))  # Value 0.7-1.0
    colors = plt.matplotlib.colors.hsv_to_rgb(hsv_colors)

    colors = np.hstack((colors, np.ones((len(unique_cdps), 1))))  

    # Plot scatter for each CDP
    for cdp_val, color in zip(unique_cdps, colors):
        mask = cdp == cdp_val
        velocities = vel[mask]
        twts = twt[mask]
        
        # Plot the scatter points with connected lines
        canvas.ax.plot(
            velocities, 
            twts, 
            color=color, 
            label=f'{int(cdp_val)}',
            marker='.',  
            markersize=8,
            linestyle='-',  
            linewidth=0.2,  
            alpha=0.5,
            zorder=10
        )

    # Calculate regression parameters if not provided
    if regression_params is None:
        regression_params = {}
        
        try:
            # Calculate linear regression (V = v0 + k*TWT)
            # For regression, we need to reorganize our model from V = v0 + k*TWT to TWT = (V - v0)/k
            # This means using vel as x and twt as y, then converting the parameters
            if len(twt) > 2:  # Need at least 3 points for meaningful regression
                # First approach: Linear regression where V = v0 + k*TWT
                slope, intercept, r_value, p_value, std_err = stats.linregress(twt, vel)
                
                linear_params = {
                    'v0': intercept,
                    'k': slope,
                    'r2': r_value**2
                }
                regression_params['linear'] = linear_params
                
                if console:
                    info_message(console, f"Linear regression: V = {intercept:.1f} + {slope:.3f}·TWT (R²: {r_value**2:.3f})")
            
            # Calculate logarithmic regression (V = v0 + k*ln(TWT))
            if len(twt) > 2 and np.all(twt > 0):  # Need positive values for log
                # Define logarithmic function: V = v0 + k*ln(TWT)
                def log_func(x, v0, k):
                    return v0 + k * np.log(x)
                
                # Fit the function to our data
                try:
                    popt, pcov = curve_fit(log_func, twt, vel)
                    v0, k = popt
                    
                    # Calculate R² for logarithmic fit
                    residuals = vel - log_func(twt, v0, k)
                    ss_res = np.sum(residuals**2)
                    ss_tot = np.sum((vel - np.mean(vel))**2)
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                    
                    log_params = {
                        'v0': v0,
                        'k': k,
                        'r2': r_squared
                    }
                    regression_params['logarithmic'] = log_params
                    
                    if console:
                        info_message(console, f"Logarithmic regression: V = {v0:.1f} + {k:.1f}·ln(TWT) (R²: {r_squared:.3f})")
                except:
                    if console:
                        warning_message(console, "Could not fit logarithmic regression. Skipping.")
        except Exception as e:
            if console:
                warning_message(console, f"Error calculating regression parameters: {str(e)}")

    # Add regression lines if parameters are available
    if regression_params:
        # Range for velocity values
        vel_range = max(vel) - min(vel)
        vel_min = min(vel) - vel_range * 0.05
        vel_max = max(vel) + vel_range * 0.05
        vel_points = np.linspace(vel_min, vel_max, 100)
        
        # Linear regression
        if 'linear' in regression_params:
            linear_params = regression_params['linear']
            v0 = linear_params['v0']
            k = linear_params['k']
            r2 = linear_params.get('r2', 0)
            
            # Calculate TWT values for each velocity point using the inverse of the linear model
            twt_linear = [(v - v0) / k if k != 0 else 0 for v in vel_points]
            
            valid_mask = np.logical_and(np.array(twt_linear) >= 0, np.array(twt_linear) <= max(twt) * 1.1)
            if np.any(valid_mask):

                canvas.ax.plot(
                    np.array(vel_points)[valid_mask], 
                    np.array(twt_linear)[valid_mask], 
                    'r-', 
                    linewidth=2.5, 
                    label='Linear',  
                    zorder=15
                )
                
                # Add formula as text annotation
                formula_text = f'Linear: V = {v0:.1f} + {k:.3f}·TWT (R²: {r2:.3f})'
                canvas.ax.text(
                    0.02, 0.02,  # Position at bottom left
                    formula_text,
                    transform=canvas.ax.transAxes,  # Use axis coordinates
                    fontsize=9,
                    color='red',
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=3)
                )

        # Logarithmic regression
        if 'logarithmic' in regression_params:
            log_params = regression_params['logarithmic']
            v0 = log_params['v0']
            k = log_params['k']
            r2 = log_params.get('r2', 0)
            
            # Calculate TWT values for each velocity point using the inverse of the logarithmic model
            twt_log = [np.exp((v - v0) / k) if k != 0 else 0 for v in vel_points]
            
            valid_mask = np.logical_and(np.array(twt_log) >= 0, np.array(twt_log) <= max(twt) * 1.1)
            if np.any(valid_mask):

                canvas.ax.plot(
                    np.array(vel_points)[valid_mask], 
                    np.array(twt_log)[valid_mask], 
                    'g-', 
                    linewidth=2, 
                    label='Logarithmic', 
                    zorder=15
                )
                
                formula_text = f'Log: V = {v0:.1f} + {k:.1f}·ln(TWT) (R²: {r2:.3f})'
                canvas.ax.text(
                    0.02, 0.08,  
                    formula_text,
                    transform=canvas.ax.transAxes,  
                    fontsize=9,
                    color='green',
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=3)
                )

    # Add moving average trend line 
    if len(vel) > 5:  # Only if we have sufficient data points
        # Sort all points by TWT
        sorted_indices = np.argsort(twt)
        twt_sorted = twt[sorted_indices]
        vel_sorted = vel[sorted_indices]
        
        # Default window size if not provided
        if window_size is None:
            window_size = max(5, len(vel) // 10)  # At least 5 points or 10% of data
            
        # Compute moving average
        ma_vel = []
        ma_twt = []
        
        # Use a sliding window to compute moving average
        for i in range(len(twt_sorted) - window_size + 1):
            window_vel = vel_sorted[i:i + window_size]
            window_twt = twt_sorted[i:i + window_size]
            ma_vel.append(np.mean(window_vel))
            ma_twt.append(np.mean(window_twt))
        
        # Plot the moving average trend line
        canvas.ax.plot(
            ma_vel, 
            ma_twt, 
            'k--',  
            linewidth=1.5,
            label=f'Moving Average',
            zorder=20
        )

    canvas.ax.set_xlabel('Velocity (m/s)', fontsize=10, fontweight='bold')
    canvas.ax.set_ylabel('TWT (ms)', fontsize=10, fontweight='bold')
    canvas.ax.set_title('Velocity Distribution by CDP', fontsize=12, fontweight='bold')

    vel_range = max(vel) - min(vel)
    twt_range = max(twt) - min(twt)
    
    canvas.ax.set_xlim(min(vel) - vel_range*0.05, max(vel) + vel_range*0.05)
    canvas.ax.set_ylim(0, max(twt) * 1.05)
    canvas.ax.invert_yaxis()  

    handles, labels = [], []
    for handle, label in zip(*canvas.ax.get_legend_handles_labels()):
        if label not in ['Linear', 'Logarithmic', 'Moving Average']:
            continue
        handles.append(handle)
        labels.append(label)
    
    if handles:  # Only create legend if we have items
        canvas.ax.legend(handles, labels, loc='upper left', 
                        bbox_to_anchor=(0.01, 0.3),
                        frameon=True, fancybox=True, fontsize=9)
    
    
    # Add grid for better readability
    canvas.ax.grid(True, linestyle='--', alpha=0.3)
    
    # Apply tight layout before drawing
    canvas.figure.tight_layout()
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