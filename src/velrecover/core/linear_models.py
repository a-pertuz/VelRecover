"""Linear interpolation models for velocity analysis."""

import numpy as np
from scipy.optimize import curve_fit

from .base import calculate_r2, run_interpolation

def linear_model(twt, v0, k):
    """Linear velocity model: V = V₀ + k·TWT"""
    return v0 + k * twt

def custom_linear_interpolate(vel_traces, vel_twts, vel_values, vel_traces_grid, vel_twts_grid, 
                             trace_range, twt_range, status_callback, cancel_check, v0, k):
    """Custom linear model implementation."""
    if status_callback:
        status_callback(40, "Applying custom linear model...")
        
    # Generate the velocity grid using the specified parameters
    vel_values_grid = np.zeros_like(vel_traces_grid, dtype=float)
    
    # Apply the linear model to each point
    for i in range(vel_values_grid.shape[1]):  # For each trace
        vel_values_grid[:, i] = linear_model(twt_range, v0, k)
        
        if status_callback and i % max(1, vel_values_grid.shape[1]//10) == 0:
            progress = 40 + (i / vel_values_grid.shape[1] * 50)
            status_callback(int(progress), f"Processing trace {i+1}/{vel_values_grid.shape[1]}")
        
        if cancel_check and cancel_check():
            return {'vel_values_grid': None, 'model_type': None}
    
    # Calculate R² for the provided model
    predicted = linear_model(vel_twts, v0, k)
    r2 = calculate_r2(vel_values, predicted)
    
    if status_callback:
        status_callback(95, f"Completed linear model with R² = {r2:.4f}")
    
    # Generate model description
    model_description = f"Custom Linear: V = {v0:.1f} + {k:.4f}·TWT (R² = {r2:.4f})"
    
    return {
        'vel_values_grid': vel_values_grid,
        'vel_traces_grid': vel_traces_grid,
        'vel_twts_grid': vel_twts_grid,
        'vel_traces': vel_traces,
        'vel_twts': vel_twts,
        'vel_values': vel_values,
        'model_type': model_description,
        'model_params': {
            'type': 'linear',
            'v0': v0,
            'k': k,
            'r2': r2
        }
    }

def best_linear_interpolate(vel_traces, vel_twts, vel_values, vel_traces_grid, vel_twts_grid, 
                           trace_range, twt_range, status_callback, cancel_check):
    """Best fit linear model implementation."""
    if status_callback:
        status_callback(40, "Calculating best fit linear regression model...")
        
    # Fit linear model to all velocity data using regression
    try:
        # Initial parameter guess
        p0 = [1500, 0.5]  # Initial guess: v0=1500, k=0.5
        params, _ = curve_fit(linear_model, vel_twts, vel_values, p0=p0)
        v0, k = params
        
        # Calculate R^2 for the regression
        predicted = linear_model(vel_twts, v0, k)
        r2 = calculate_r2(vel_values, predicted)
        
        if status_callback:
            status_callback(60, f"Found best fit linear regression: V = {v0:.1f} + {k:.4f}·TWT (R² = {r2:.4f})")
            
        # Generate the velocity grid using the regression parameters
        vel_values_grid = np.zeros_like(vel_traces_grid, dtype=float)
        
        # Apply the model to each trace
        for i in range(vel_values_grid.shape[1]):
            vel_values_grid[:, i] = linear_model(twt_range, v0, k)
            
            if status_callback and i % max(1, vel_values_grid.shape[1]//10) == 0:
                progress = 60 + (i / vel_values_grid.shape[1] * 30)
                status_callback(int(progress), f"Processing trace {i+1}/{vel_values_grid.shape[1]}")
            
            if cancel_check and cancel_check():
                return {'vel_values_grid': None, 'model_type': None}
                
    except Exception as fit_error:
        return {'error': f"Failed to fit linear model: {str(fit_error)}"}
        
    # Return results
    model_description = f"Linear Regression: V = {v0:.1f} + {k:.4f}·TWT (R² = {r2:.4f})"
    return {
        'vel_values_grid': vel_values_grid,
        'vel_traces_grid': vel_traces_grid,
        'vel_twts_grid': vel_twts_grid,
        'vel_traces': vel_traces,
        'vel_twts': vel_twts,
        'vel_values': vel_values,
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
        text_file_path: Path to velocity data file (optional if vel_traces, vel_twts, vel_values provided)
        segy_file_path: Path to SEGY file
        v0: Initial velocity parameter
        k: Velocity gradient parameter
        status_callback: Function for updating progress
        cancel_check: Function for checking if operation should be cancelled
        **kwargs: Additional parameters (vel_traces, vel_twts, vel_values can be passed here)
        
    Returns:
        dict: Result with interpolated velocity grid and metadata
    """
    # Extract data from kwargs if provided
    vel_traces = kwargs.get('vel_traces')
    vel_twts = kwargs.get('vel_twts')
    vel_values = kwargs.get('vel_values')
    console = kwargs.get('console')
    
    return run_interpolation(
        text_file_path, segy_file_path, 
        custom_linear_interpolate,
        additional_args=[v0, k],
        status_callback=status_callback, 
        cancel_check=cancel_check,
        vel_traces=vel_traces, vel_twts=vel_twts, vel_values=vel_values,
        console=console
    )

def best_linear_fit(text_file_path=None, segy_file_path=None, 
                   status_callback=None, cancel_check=None, **kwargs):
    """
    Find the best linear velocity model (V₀+kt) that fits all data.
    
    Args:
        text_file_path: Path to velocity data file (optional if vel_traces, vel_twts, vel_values provided)
        segy_file_path: Path to SEGY file
        status_callback: Function for updating progress
        cancel_check: Function for checking if operation should be cancelled
        **kwargs: Additional parameters (vel_traces, vel_twts, vel_values can be passed here)
        
    Returns:
        dict: Result with interpolated velocity grid and metadata
    """
    # Extract data from kwargs if provided
    vel_traces = kwargs.get('vel_traces')
    vel_twts = kwargs.get('vel_twts')
    vel_values = kwargs.get('vel_values')
    console = kwargs.get('console')
    
    return run_interpolation(
        text_file_path, segy_file_path, 
        best_linear_interpolate,
        status_callback=status_callback, 
        cancel_check=cancel_check,
        vel_traces=vel_traces, vel_twts=vel_twts, vel_values=vel_values,
        console=console
    )
