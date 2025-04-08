"""Linear interpolation models for velocity analysis."""

import numpy as np
from scipy.optimize import curve_fit

from .base import calculate_r2, run_interpolation

def linear_model(twt, v0, k):
    """Linear velocity model: V = V₀ + k·TWT"""
    return v0 + k * twt

def custom_linear_interpolate(CDP, TWT, VEL, CDP_grid, TWT_grid, CDP_range, TWT_range, 
                             status_callback, cancel_check, v0, k):
    """Custom linear model implementation."""
    if status_callback:
        status_callback(40, "Applying custom linear model...")
        
    # Generate the velocity grid using the specified parameters
    VEL_grid = np.zeros_like(CDP_grid, dtype=float)
    
    # Apply the linear model to each point
    for i in range(VEL_grid.shape[1]):  # For each CDP
        VEL_grid[:, i] = linear_model(TWT_range, v0, k)
        
        if status_callback and i % max(1, VEL_grid.shape[1]//10) == 0:
            progress = 40 + (i / VEL_grid.shape[1] * 50)
            status_callback(int(progress), f"Processing CDP {i+1}/{VEL_grid.shape[1]}")
        
        if cancel_check and cancel_check():
            return {'VEL_grid': None, 'model_type': None}
    
    # Calculate R² for the provided model
    predicted = linear_model(TWT, v0, k)
    r2 = calculate_r2(VEL, predicted)
    
    if status_callback:
        status_callback(95, f"Completed linear model with R² = {r2:.4f}")
    
    # Generate model description
    model_description = f"Custom Linear: V = {v0:.1f} + {k:.4f}·TWT (R² = {r2:.4f})"
    
    return {
        'VEL_grid': VEL_grid,
        'model_type': model_description,
        'model_params': {
            'type': 'linear',
            'v0': v0,
            'k': k,
            'r2': r2
        }
    }

def best_linear_interpolate(CDP, TWT, VEL, CDP_grid, TWT_grid, CDP_range, TWT_range, 
                           status_callback, cancel_check):
    """Best fit linear model implementation."""
    if status_callback:
        status_callback(40, "Calculating best fit linear regression model...")
        
    # Fit linear model to all velocity data using regression
    try:
        # Initial parameter guess
        p0 = [1500, 0.5]  # Initial guess: v0=1500, k=0.5
        params, _ = curve_fit(linear_model, TWT, VEL, p0=p0)
        v0, k = params
        
        # Calculate R^2 for the regression
        predicted = linear_model(TWT, v0, k)
        r2 = calculate_r2(VEL, predicted)
        
        if status_callback:
            status_callback(60, f"Found best fit linear regression: V = {v0:.1f} + {k:.4f}·TWT (R² = {r2:.4f})")
            
        # Generate the velocity grid using the regression parameters
        VEL_grid = np.zeros_like(CDP_grid, dtype=float)
        
        # Apply the model to each CDP
        for i in range(VEL_grid.shape[1]):
            VEL_grid[:, i] = linear_model(TWT_range, v0, k)
            
            if status_callback and i % max(1, VEL_grid.shape[1]//10) == 0:
                progress = 60 + (i / VEL_grid.shape[1] * 30)
                status_callback(int(progress), f"Processing CDP {i+1}/{VEL_grid.shape[1]}")
            
            if cancel_check and cancel_check():
                return {'VEL_grid': None, 'model_type': None}
                
    except Exception as fit_error:
        return {'error': f"Failed to fit linear model: {str(fit_error)}"}
        
    # Return results
    model_description = f"Linear Regression: V = {v0:.1f} + {k:.4f}·TWT (R² = {r2:.4f})"
    return {
        'VEL_grid': VEL_grid,
        'model_type': model_description,
        'model_params': {
            'type': 'linear',
            'v0': v0,
            'k': k,
            'r2': r2
        }
    }

def custom_linear_model(text_file_path=None, segy_file_path=None, v0=1500, k=0.5, 
                       status_callback=None, cancel_check=None, **kwargs):
    """
    Apply a custom V₀+kt model with user-provided parameters.
    
    Args:
        text_file_path: Path to velocity data file (optional if cdp, twt, vel provided)
        segy_file_path: Path to SEGY file
        v0: Initial velocity parameter
        k: Velocity gradient parameter
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
        custom_linear_interpolate,
        additional_args=[v0, k],
        status_callback=status_callback, 
        cancel_check=cancel_check,
        cdp=cdp, twt=twt, vel=vel,
        console=console
    )

def best_linear_fit(text_file_path=None, segy_file_path=None, 
                   status_callback=None, cancel_check=None, **kwargs):
    """
    Find the best linear velocity model (V₀+kt) that fits all data.
    
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
        best_linear_interpolate,
        status_callback=status_callback, 
        cancel_check=cancel_check,
        cdp=cdp, twt=twt, vel=vel,
        console=console
    )
