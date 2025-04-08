"""RBF interpolation models for velocity analysis."""

import numpy as np
from scipy.interpolate import RBFInterpolator

from .base import run_interpolation

def rbf_interpolate(CDP, TWT, VEL, CDP_grid, TWT_grid, CDP_range, TWT_range, 
                    status_callback, cancel_check):
    """RBF interpolation implementation."""
    if status_callback:
        status_callback(40, "Performing RBF interpolation... This may take a moment...")
    
    rbf_interpolator = RBFInterpolator(
        np.column_stack((CDP, TWT)), 
        VEL, 
        kernel='linear', 
        smoothing=10
    )
    
    if status_callback:
        status_callback(60, "Applying interpolation to the grid...")
    
    VEL_grid = rbf_interpolator(
        np.column_stack((CDP_grid.ravel(), TWT_grid.ravel()))
    ).reshape(CDP_grid.shape)
    
    # Ensure physically reasonable velocities (no negatives)
    VEL_grid = np.maximum(VEL_grid, 1000)
    
    return {
        'VEL_grid': VEL_grid,
        'model_type': 'RBF Interpolation'
    }

def interpolate_velocity_data_rbf(text_file_path=None, segy_file_path=None, 
                                 status_callback=None, cancel_check=None, **kwargs):
    """
    Perform 2D interpolation of velocity data using RBF.
    
    Args:
        text_file_path: Path to velocity data file (optional if cdp, twt, vel provided)
        segy_file_path: Path to SEGY file
        status_callback: Function for updating progress
        cancel_check: Function for checking if operation should be cancelled
        **kwargs: Additional parameters (cdp, twt, vel can be passed here)
    
    Returns:
        dict: Result with interpolated velocity grid and metadata
    """
    # Extract CDP, TWT, VEL from kwargs if provided
    cdp = kwargs.get('cdp')
    twt = kwargs.get('twt')
    vel = kwargs.get('vel')
    console = kwargs.get('console')
    
    return run_interpolation(
        text_file_path, segy_file_path, 
        rbf_interpolate,
        status_callback=status_callback, 
        cancel_check=cancel_check,
        cdp=cdp, twt=twt, vel=vel,
        console=console
    )
