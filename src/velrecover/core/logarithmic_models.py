"""Logarithmic interpolation models for velocity analysis."""

import numpy as np
from scipy.optimize import curve_fit

from .base import calculate_r2, run_interpolation

def logarithmic_model(twt, v0, k):
    """Logarithmic velocity model: V = V₀ + k·ln(TWT)"""
    # Add a small epsilon to TWT to avoid log(0)
    return v0 + k * np.log(twt + 1e-6)  

def custom_logarithmic_interpolate(vel_traces, vel_twts, vel_values, vel_traces_grid, vel_twts_grid, 
                                  trace_range, twt_range, v0, k):
    """Custom logarithmic model implementation."""
    # Generate the velocity grid using the specified parameters
    vel_values_grid = np.zeros_like(vel_traces_grid, dtype=float)
    
    # Apply the logarithmic model to each point
    for i in range(vel_values_grid.shape[1]):  # For each trace
        vel_values_grid[:, i] = logarithmic_model(vel_twts_grid[:, 0], v0, k)
    
    # Calculate R² for the provided model
    predicted = logarithmic_model(vel_twts, v0, k)
    r2 = calculate_r2(vel_values, predicted)
    
    # Generate model description
    model_description = f"Custom Log: V = {v0:.1f} + {k:.1f}·ln(TWT) (R² = {r2:.4f})"
    
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

def best_logarithmic_interpolate(vel_traces, vel_twts, vel_values, vel_traces_grid, vel_twts_grid, 
                                trace_range, twt_range):
    """Best fit logarithmic model implementation."""
    # Fit logarithmic model to all velocity data using regression
    try:
        # Initial parameter guess
        p0 = [1500, 1000]  # Initial guess: v0=1500, k=1000
        params, _ = curve_fit(logarithmic_model, vel_twts, vel_values, p0=p0)
        v0, k = params
        
        # Calculate R^2 for the regression
        predicted = logarithmic_model(vel_twts, v0, k)
        r2 = calculate_r2(vel_values, predicted)
        
        # Generate the velocity grid using the regression parameters
        vel_values_grid = np.zeros_like(vel_traces_grid, dtype=float)
        
        # Apply the model to each trace
        for i in range(vel_values_grid.shape[1]):
            vel_values_grid[:, i] = logarithmic_model(vel_twts_grid[:, 0], v0, k)
                
    except Exception as fit_error:
        return {'error': f"Failed to fit logarithmic model: {str(fit_error)}"}
        
    # Return results
    model_description = f"Log Regression: V = {v0:.1f} + {k:.1f}·ln(TWT) (R² = {r2:.4f})"
    
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

def custom_logarithmic_model(vel_traces, vel_twts, vel_values, twt_range, trace_range, 
                             ntraces, nsamples, v0=1500, k=1000, console=None):
    """Apply a custom logarithmic model with user-provided parameters."""
    return run_interpolation(
        vel_traces, vel_twts, vel_values,
        custom_logarithmic_interpolate, twt_range, trace_range,
        ntraces, nsamples, additional_args=[v0, k], console=console
    )

def best_logarithmic_fit(vel_traces, vel_twts, vel_values, twt_range, trace_range, 
                         ntraces, nsamples, console=None):
    """Find the best logarithmic velocity model that fits all data."""
    return run_interpolation(
        vel_traces, vel_twts, vel_values,
        best_logarithmic_interpolate, twt_range, trace_range,
        ntraces, nsamples, console=console
    )
