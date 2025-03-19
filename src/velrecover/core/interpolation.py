"""Interpolation algorithms for velocity analysis."""

import numpy as np
import cv2
from scipy.interpolate import RBFInterpolator
import seisio

def interpolate_velocity_data(text_file_path, segy_file_path, status_callback=None, cancel_check=None):
    """Perform 2D interpolation of velocity data."""
    if cancel_check and cancel_check():
        return {'cancelled': True}
    
    if status_callback:
        status_callback(5, "Loading SEGY file...")
    
    try:
        # Load SEGY file
        sio = seisio.input(segy_file_path)
        nsamples = sio.nsamples
        ntraces = sio.ntraces
        dt = sio.vsi  # Microseconds
        delay = sio.delay
        
        # Calculate TWT range
        TWT_begin = delay
        TWT_end = (nsamples - 1) * (dt/1000)
        TWT_range = np.arange(0, TWT_end + 1, 4)
        CDP_range = np.arange(ntraces)
        
        if status_callback:
            status_callback(10, f"Processing {len(CDP_range)} CDPs and {len(TWT_range)} TWTs...")
        
        if cancel_check and cancel_check():
            return {'cancelled': True}
        
        # Load text file data
        if status_callback:
            status_callback(20, "Loading velocity data from text file...")
        
        with open(text_file_path, 'r') as f:
            first_lines = [f.readline() for _ in range(3)]
        
        # Auto-detect if it's tab-delimited
        has_tabs = any('\t' in line for line in first_lines)
        delimiter = '\t' if has_tabs else None  # None will make loadtxt split on any whitespace
        
        # Load data with appropriate delimiter
        data = np.loadtxt(text_file_path, delimiter=delimiter, skiprows=1)
        CDP, TWT, VEL = data[:, 0], data[:, 1], data[:, 2]
        
        if cancel_check and cancel_check():
            return {'cancelled': True}
        
        # Create interpolation grid
        if status_callback:
            status_callback(30, "Creating interpolation grid...")
        
        CDP_grid, TWT_grid = np.meshgrid(CDP_range, TWT_range)
        
        if cancel_check and cancel_check():
            return {'cancelled': True}
        
        # Perform RBF interpolation
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
        
        if cancel_check and cancel_check():
            return {'cancelled': True}
        
        # Return results
        return {
            'CDP': CDP,
            'TWT': TWT, 
            'VEL': VEL,
            'CDP_grid': CDP_grid,
            'TWT_grid': TWT_grid,
            'VEL_grid': VEL_grid,
            'ntraces': ntraces,
            'cancelled': False
        }
        
    except Exception as e:
        return {'error': str(e), 'cancelled': False}

def apply_gaussian_blur(vel_grid, blur_value):
    """Apply Gaussian blur to velocity grid."""
    # Ensure blur value is odd and at least 3
    kernel_size = blur_value * 10 + 1
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    # Apply Gaussian blur
    return cv2.GaussianBlur(vel_grid, (kernel_size, kernel_size), 0)
