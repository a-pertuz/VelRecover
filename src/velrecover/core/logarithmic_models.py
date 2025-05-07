"""Logarithmic interpolation models for velocity analysis."""

import numpy as np
from scipy.optimize import curve_fit

from .base import calculate_r2, run_interpolation

def logarithmic_model(twt, v0, k):
    """Logarithmic velocity model: V = V₀ + k·ln(TWT)
    
    Uses a minimum velocity of 1000 m/s to ensure physical validity.
    """
    # Avoid taking ln(0), use a small offset
    with np.errstate(divide='ignore', invalid='ignore'):
        result = v0 + k * np.log(np.maximum(twt, 0.001))  
    
    # Ensure velocity is always positive - physical constraint for seismic velocities
    # Use typical water velocity (1000 m/s) as minimum
    return np.maximum(result, 1000)

def custom_logarithmic_interpolate(vel_traces, vel_twts, vel_values, vel_traces_grid, vel_twts_grid, 
                                 trace_range, twt_range, status_callback, cancel_check, v0, k):
    """Custom logarithmic model implementation."""
    if status_callback:
        status_callback(40, "Applying custom logarithmic model...")
        
    # Generate the velocity grid using the specified parameters
    vel_values_grid = np.zeros_like(vel_traces_grid, dtype=float)
    
    # Apply the logarithmic model to each point
    for i in range(vel_values_grid.shape[1]):  # For each trace
        vel_values_grid[:, i] = logarithmic_model(twt_range, v0, k)
        
        if status_callback and i % max(1, vel_values_grid.shape[1]//10) == 0:
            progress = 40 + (i / vel_values_grid.shape[1] * 50)
            status_callback(int(progress), f"Processing trace {i+1}/{vel_values_grid.shape[1]}")
        
        if cancel_check and cancel_check():
            return {'vel_values_grid': None, 'model_type': None}
    
    # Calculate R² for the provided model
    # Filter out invalid values for log calculation
    valid_indices = vel_twts > 0
    twt_valid = vel_twts[valid_indices]
    vel_valid = vel_values[valid_indices]
    
    if len(twt_valid) > 0:
        predicted = logarithmic_model(twt_valid, v0, k)
        r2 = calculate_r2(vel_valid, predicted)
    else:
        r2 = 0.0
    
    if status_callback:
        status_callback(95, f"Completed logarithmic model with R² = {r2:.4f}")
    
    # Generate model description
    model_description = f"Custom Logarithmic: V = {v0:.1f} + {k:.1f}·ln(TWT) (R² = {r2:.4f})"
    
    return {
        'vel_values_grid': vel_values_grid,
        'vel_traces_grid': vel_traces_grid,
        'vel_twts_grid': vel_twts_grid,
        'vel_traces': vel_traces,
        'vel_twts': vel_twts,
        'vel_values': vel_values,
        'model_type': model_description,
        'model_params': {
            'type': 'logarithmic',
            'v0': v0,
            'k': k,
            'r2': r2
        }
    }

def custom_logarithmic_model(text_file_path=None, segy_file_path=None, v0=1500, k=1000, 
                           status_callback=None, cancel_check=None, **kwargs):
    """
    Apply a custom V₀+k·ln(t) model with user-provided parameters.
    
    Args:
        text_file_path: Path to velocity data file (optional if vel_traces, vel_twts, vel_values provided)
        segy_file_path: Path to SEGY file
        v0: Initial velocity parameter
        k: Logarithmic scaling parameter
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
        custom_logarithmic_interpolate,
        additional_args=[v0, k],
        status_callback=status_callback, 
        cancel_check=cancel_check,
        vel_traces=vel_traces, vel_twts=vel_twts, vel_values=vel_values,
        console=console
    )

def best_logarithmic_interpolate(vel_traces, vel_twts, vel_values, vel_traces_grid, vel_twts_grid, 
                               trace_range, twt_range, status_callback, cancel_check):
    """Best fit logarithmic model implementation."""
    if status_callback:
        status_callback(40, "Calculating best fit logarithmic regression model...")
        
    # Fit logarithmic model to all velocity data
    try:
        # Remove any zero TWT values to avoid log(0)
        valid_indices = vel_twts > 0
        twt_valid = vel_twts[valid_indices]
        vel_valid = vel_values[valid_indices]
        
        # Initial parameter guess
        p0 = [1500, 1000]  # Initial guess: v0=1500, k=1000
        params, _ = curve_fit(logarithmic_model, twt_valid, vel_valid, p0=p0)
        v0, k = params
        
        # Calculate R^2 for the regression
        predicted = logarithmic_model(twt_valid, v0, k)
        r2 = calculate_r2(vel_valid, predicted)
        
        if status_callback:
            status_callback(60, f"Found best fit logarithmic regression: V = {v0:.1f} + {k:.4f}·ln(TWT) (R² = {r2:.4f})")
            
        # Generate the velocity grid using the logarithmic model
        vel_values_grid = np.zeros_like(vel_traces_grid, dtype=float)
        
        # Apply the model to each trace
        for i in range(vel_values_grid.shape[1]):
            # Apply the logarithmic model with non-negative constraint
            model_velocities = logarithmic_model(twt_range, v0, k)
            # Ensure physical reasonableness - minimum velocity of 1000 m/s (typical water velocity)
            model_velocities = np.maximum(model_velocities, 1000)
            vel_values_grid[:, i] = model_velocities
            
            if status_callback and i % max(1, vel_values_grid.shape[1]//10) == 0:
                progress = 60 + (i / vel_values_grid.shape[1] * 30)
                status_callback(int(progress), f"Processing trace {i+1}/{vel_values_grid.shape[1]}")
            
            if cancel_check and cancel_check():
                return {'vel_values_grid': None, 'model_type': None}
                
    except Exception as fit_error:
        return {'error': f"Failed to fit logarithmic model: {str(fit_error)}"}
        
    # Return results
    model_description = f"Logarithmic Regression: V = {v0:.1f} + {k:.4f}·ln(TWT) (R² = {r2:.4f})"
    return {
        'vel_values_grid': vel_values_grid,
        'vel_traces_grid': vel_traces_grid,
        'vel_twts_grid': vel_twts_grid,
        'vel_traces': vel_traces,
        'vel_twts': vel_twts,
        'vel_values': vel_values,
        'model_type': model_description,
        'model_params': {
            'type': 'logarithmic',
            'v0': v0,
            'k': k,
            'r2': r2
        }
    }

def best_logarithmic_fit(text_file_path=None, segy_file_path=None, 
                        status_callback=None, cancel_check=None, **kwargs):
    """Find the best logarithmic velocity model (V₀+k·ln(t)) that fits all data.
    
    Args:
        text_file_path: Path to velocity data file (optional if vel_traces, vel_twts, vel_values provided)
        segy_file_path: Path to SEGY file
        status_callback: Function for updating progress
        cancel_check: Function for checking if operation should be cancelled
        **kwargs: Additional parameters (vel_traces, vel_twts, vel_values, console can be passed here)
    
    Returns:
        dict: Result with interpolated velocity grid and metadata
    """
    # Extract parameters from kwargs
    vel_traces = kwargs.get('vel_traces')
    vel_twts = kwargs.get('vel_twts')
    vel_values = kwargs.get('vel_values')
    console = kwargs.get('console')
    
    return run_interpolation(
        text_file_path, segy_file_path,
        best_logarithmic_interpolate,
        status_callback=status_callback, 
        cancel_check=cancel_check,
        vel_traces=vel_traces, vel_twts=vel_twts, vel_values=vel_values,
        console=console
    )
