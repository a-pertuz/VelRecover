"""Utility functions for VelRecover."""

from .console_utils import (
    initialize_log_file, close_log_file, section_header,
    success_message, error_message, info_message,
    warning_message, summary_statistics
)

from .io_utils import (
    initialize_directories, copy_tutorial_files, copy_data_between_directories,
    save_velocity_text_data, save_velocity_binary_data
)

from ..core.gauss_blur import apply_gaussian_blur

# Import VelocityData class
from .VelocityData import VelocityData

# Import interpolation utilities
from .interpolation_utils import (
    load_text_data, load_segy_file,
    interpolate, apply_smoothing, calculate_regression_params
)

__all__ = [
    # Console utilities
    'initialize_log_file', 'close_log_file', 'section_header',
    'success_message', 'error_message', 'info_message',
    'warning_message', 'summary_statistics',
    
    # I/O utilities
    'initialize_directories', 'copy_tutorial_files', 'copy_data_between_directories',
    'save_velocity_text_data', 'save_velocity_binary_data',
    
    # General utilities
    'apply_gaussian_blur',
    
    # VelocityData class
    'VelocityData',
    
    # Interpolation utilities
    'load_text_data', 'load_segy_file',
    'interpolate', 'apply_smoothing', 'calculate_regression_params'
]
