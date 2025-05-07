"""RBF interpolation models for velocity analysis."""

import numpy as np
from scipy.interpolate import RBFInterpolator

from .base import run_interpolation

def rbf_interpolate(vel_traces, vel_twts, vel_values, vel_traces_grid, vel_twts_grid, 
                   trace_range, twt_range):
    """RBF interpolation implementation."""
    
    rbf_interpolator = RBFInterpolator(
        np.column_stack((vel_traces, vel_twts)), 
        vel_values, 
        kernel='linear', 
        smoothing=10
    )
    
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

def interpolate_velocity_data_rbf(vel_traces, vel_twts, vel_values, twt_range, trace_range, 
                                 ntraces, nsamples, console=None):
    """
    Perform 2D interpolation of velocity data using RBF.
    Uses already loaded velocity data instead of reloading from files.
    """
    return run_interpolation(
        vel_traces, vel_twts, vel_values,
        rbf_interpolate, twt_range, trace_range,
        ntraces, nsamples, console=console
    )
