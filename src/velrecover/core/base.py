"""Base functionality for interpolation methods."""

import numpy as np
from ..utils.console_utils import info_message, error_message, success_message


def create_grid(trace_range, twt_range, ntraces, nsamples):
    """Create grid for interpolation based on SEGY dimensions."""
    # Generate grid using SEGY dimensions
    vel_traces_grid, vel_twts_grid = np.meshgrid(
        np.linspace(trace_range[0], trace_range[-1], ntraces),
        np.linspace(twt_range[0], twt_range[-1], nsamples)
    )
    return vel_traces_grid, vel_twts_grid

def calculate_r2(y_true, y_pred):
    """Calculate the coefficient of determination (R²)"""
    ss_total = np.sum((y_true - np.mean(y_true)) ** 2)
    ss_residual = np.sum((y_true - y_pred) ** 2)
    
    if ss_total == 0:
        return 0  
    
    r2 = 1 - (ss_residual / ss_total)
    return max(0, r2)


def run_interpolation(vel_traces, vel_twts, vel_values, 
                               interpolation_func, twt_range, trace_range, 
                               ntraces, nsamples, additional_args=None, console=None):
    
    try:
        # Create interpolation grid
        vel_traces_grid, vel_twts_grid = create_grid(trace_range, twt_range, ntraces, nsamples)
        
        # Prepare arguments for the interpolation function
        args = [
            vel_traces, vel_twts, vel_values, 
            vel_traces_grid, vel_twts_grid, 
            trace_range, twt_range
        ]
        
        # Add additional arguments if provided
        if additional_args:
            args.extend(additional_args)
        
        # Run the interpolation algorithm
        result = interpolation_func(*args)
        
        # Add base data to the result if not already present
        if 'vel_traces' not in result:
            result.update({
                'vel_traces': vel_traces,
                'vel_twts': vel_twts,
                'vel_values': vel_values,
                'vel_traces_grid': vel_traces_grid,
                'vel_twts_grid': vel_twts_grid,
                'ntraces': ntraces
            })
        
        return result
        
    except Exception as e:
        if console:
            error_message(console, f"Error during interpolation: {str(e)}")
        return {'error': str(e)}