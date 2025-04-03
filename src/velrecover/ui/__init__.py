"""User interface components for SEGYRecover."""

from .widgets import ProgressStatusBar
from ..core.visualization import (VelocityAnalysisWindow, SmoothedVelocityAnalysisWindow, 
                               VelocityDistributionWindow, display_velocity_analysis, plot_velocity_distribution)
from ..core.interpolation import interpolate_velocity_data, apply_gaussian_blur
from ..utils.save_functions import (save_velocity_text_data, save_velocity_binary_data)