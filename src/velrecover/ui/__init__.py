"""User interface components for VelRecover."""

# UI components
from .widgets import ProgressStatusBar
from .dialogs import (
    FirstRunDialog, 
    AboutDialog, 
    HelpDialog, 
    ModelSelectionDialog, 
    CustomLinearModelDialog
)

# Distribution visualization
from .distribution_display import (
    VelocityDistributionWindow,
    plot_velocity_distribution
)

# SEGY visualization
from .segy_display import SegyDisplayWindow

__all__ = [
    # UI components
    'ProgressStatusBar', 
    'FirstRunDialog', 'AboutDialog', 'HelpDialog',
    'ModelSelectionDialog', 'CustomLinearModelDialog',
    
    # Distribution visualization
    'VelocityDistributionWindow', 'plot_velocity_distribution',
    
    # SEGY visualization
    'SegyDisplayWindow'
]