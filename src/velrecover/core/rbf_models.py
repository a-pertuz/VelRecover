"""RBF interpolation models for velocity analysis."""

import numpy as np
from scipy.interpolate import RBFInterpolator

from .base import run_interpolation

def rbf_interpolate(vel_traces, vel_twts, vel_values, vel_traces_grid, vel_twts_grid, 
                   trace_range, twt_range, status_callback, cancel_check):
    """RBF interpolation implementation."""
    if status_callback:
        status_callback(40, "Performing RBF interpolation... This may take a moment...")
    
    rbf_interpolator = RBFInterpolator(
        np.column_stack((vel_traces, vel_twts)), 
        vel_values, 
        kernel='linear', 
        smoothing=10
    )
    
    if status_callback:
        status_callback(60, "Applying interpolation to the grid...")
    
    vel_values_grid = rbf_interpolator(
        np.column_stack((vel_traces_grid.ravel(), vel_twts_grid.ravel()))
    ).reshape(vel_traces_grid.shape)
    
    # Ensure physically reasonable velocities (no negatives)
    vel_values_grid = np.maximum(vel_values_grid, 1000)
    
    return {
        'vel_values_grid': vel_values_grid,
        'vel_traces_grid': vel_traces_grid,
        'vel_twts_grid': vel_twts_grid,
        'vel_traces': vel_traces,
        'vel_twts': vel_twts,
        'vel_values': vel_values,
        'model_type': 'RBF Interpolation'
    }

def interpolate_velocity_data_rbf(text_file_path=None, segy_file_path=None, 
                                 status_callback=None, cancel_check=None, **kwargs):
    """
    Perform 2D interpolation of velocity data using RBF.
    
    Args:
        text_file_path: Path to velocity data file (optional if vel_traces, vel_twts, vel_values provided)
        segy_file_path: Path to SEGY file
        status_callback: Function for updating progress
        cancel_check: Function for checking if operation should be cancelled
        **kwargs: Additional parameters (vel_traces, vel_twts, vel_values can be passed here)
    
    Returns:
        dict: Result with interpolated velocity grid and metadata
    """
    # Extract velocity data from kwargs if provided
    vel_traces = kwargs.get('vel_traces')
    vel_twts = kwargs.get('vel_twts')
    vel_values = kwargs.get('vel_values')
    console = kwargs.get('console')
    
    return run_interpolation(
        text_file_path, segy_file_path, 
        rbf_interpolate,
        status_callback=status_callback, 
        cancel_check=cancel_check,
        vel_traces=vel_traces, vel_twts=vel_twts, vel_values=vel_values,
        console=console
    )
