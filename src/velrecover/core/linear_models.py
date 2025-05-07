"""Linear interpolation models for velocity analysis."""

import numpy as np
from scipy.optimize import curve_fit

from .base import calculate_r2, run_interpolation

def linear_model(twt, v0, k):
    """Linear velocity model: V = V₀ + k·TWT"""
    return v0 + k * twt

def custom_linear_interpolate(vel_traces, vel_twts, vel_values, vel_traces_grid, vel_twts_grid, 
                             trace_range, twt_range, v0, k):
    """Custom linear model implementation."""
    # Generate the velocity grid using the specified parameters
    vel_values_grid = np.zeros_like(vel_traces_grid, dtype=float)
    
    # Apply the linear model to each point
    for i in range(vel_values_grid.shape[1]):  # For each trace
        vel_values_grid[:, i] = linear_model(vel_twts_grid[:, 0], v0, k)
    
    # Calculate R² for the provided model
    predicted = linear_model(vel_twts, v0, k)
    r2 = calculate_r2(vel_values, predicted)
    
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
                           trace_range, twt_range):
    """Best fit linear model implementation."""
    # Fit linear model to all velocity data using regression
    try:
        # Initial parameter guess
        p0 = [1500, 0.5]  # Initial guess: v0=1500, k=0.5
        params, _ = curve_fit(linear_model, vel_twts, vel_values, p0=p0)
        v0, k = params
        
        # Calculate R^2 for the regression
        predicted = linear_model(vel_twts, v0, k)
        r2 = calculate_r2(vel_values, predicted)
        
        # Generate the velocity grid using the regression parameters
        vel_values_grid = np.zeros_like(vel_traces_grid, dtype=float)
        
        # Apply the model to each trace
        for i in range(vel_values_grid.shape[1]):
            vel_values_grid[:, i] = linear_model(vel_twts_grid[:, 0], v0, k)
                
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

def custom_linear_model(vel_traces, vel_twts, vel_values, twt_range, trace_range, 
                        ntraces, nsamples, v0=1500, k=0.5, console=None):
    """Apply a custom V₀+kt model with user-provided parameters."""
    return run_interpolation(
        vel_traces, vel_twts, vel_values,
        custom_linear_interpolate, twt_range, trace_range,
        ntraces, nsamples, additional_args=[v0, k], console=console
    )

def best_linear_fit(vel_traces, vel_twts, vel_values, twt_range, trace_range, 
                    ntraces, nsamples, console=None):
    """Find the best linear velocity model (V₀+kt) that fits all data."""
    return run_interpolation(
        vel_traces, vel_twts, vel_values,
        best_linear_interpolate, twt_range, trace_range,
        ntraces, nsamples, console=console
    )
