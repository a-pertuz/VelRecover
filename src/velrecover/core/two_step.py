"""Two-step interpolation model for velocity analysis."""

import numpy as np
import cv2
from scipy.interpolate import RBFInterpolator

from ..utils.console_utils import info_message, warning_message, success_message
from .base import run_interpolation


def two_step_interpolate(vel_traces, vel_twts, vel_values, vel_traces_grid, vel_twts_grid, 
                       trace_range, twt_range, blur_value=2.5):
    """
    Perform two-step interpolation:
    1. Extrapolate velocities for each trace using RBF interpolation
    2. Use nearest neighbor for missing traces and apply Gaussian smoothing
    """
    # Extract dimensions from grid
    ntraces = vel_traces_grid.shape[1]
    nsamples = vel_traces_grid.shape[0]
    
    # Create full range of values
    min_trace, max_trace = trace_range
    min_twt, max_twt = twt_range
    
    traces_full = np.linspace(min_trace, max_trace, ntraces)
    twts_full = np.linspace(min_twt, max_twt, nsamples)
    
    # Initialize velocity grid with NaN (to identify unfilled cells)
    vel_values_grid = np.zeros_like(vel_traces_grid, dtype=float)
    vel_values_grid.fill(np.nan)
    
    # Step 1: Interpolate for each unique trace using RBF
    unique_traces = np.unique(vel_traces)
    
    # Create mapping from unique traces to column indices
    trace_to_col_idx = {}
    for i, grid_trace in enumerate(traces_full):
        distances = np.abs(unique_traces - grid_trace)
        if np.min(distances) <= 0.5:  # If within 0.5 of a unique trace
            closest_trace = unique_traces[np.argmin(distances)]
            if closest_trace not in trace_to_col_idx:
                trace_to_col_idx[closest_trace] = i
    
    # Process each unique trace
    for i, unique_trace in enumerate(unique_traces):
        # Get points for this trace
        trace_mask = vel_traces == unique_trace
        trace_twts = vel_twts[trace_mask]
        trace_vals = vel_values[trace_mask]
        
        if len(trace_twts) < 2:
            continue
        
        # Sort data points by TWT for proper interpolation
        sort_idx = np.argsort(trace_twts)
        trace_twts = trace_twts[sort_idx]
        trace_vals = trace_vals[sort_idx]
        
        try:
            # Reshape for RBF interpolator
            points = trace_twts.reshape(-1, 1)
            values = trace_vals
            
            # Create the RBF interpolator
            rbf_interpolator = RBFInterpolator(
                points, values, 
                kernel='linear', 
                smoothing=10
            )
            
            # Evaluate at desired points
            query_points = twts_full.reshape(-1, 1)
            extrapolated_vel = rbf_interpolator(query_points)
            
            # Ensure no negative velocities
            extrapolated_vel = np.maximum(extrapolated_vel, np.min(trace_vals) * 0.5)
            
            # Find column index for this trace
            if unique_trace in trace_to_col_idx:
                col_idx = trace_to_col_idx[unique_trace]
                vel_values_grid[:, col_idx] = extrapolated_vel
            else:
                # Find closest matching column
                col_idx = np.abs(traces_full - unique_trace).argmin()
                vel_values_grid[:, col_idx] = extrapolated_vel
                
        except Exception as e:
            # Skip this trace if interpolation fails
            continue
    
    # Step 2: Fill missing traces using nearest neighbor
    # Find columns where we have valid data
    valid_cols = []
    for j in range(vel_values_grid.shape[1]):
        if not np.all(np.isnan(vel_values_grid[:, j])):
            valid_cols.append(j)
    
    if len(valid_cols) <= 1:
        return {'error': "Not enough valid traces for interpolation"}
    
    # Use nearest neighbor to fill all gaps
    for j in range(vel_values_grid.shape[1]):
        if j in valid_cols:
            continue  # Skip columns that already have data
        
        # Find nearest valid column (minimum distance)
        distances = np.array([abs(j - vc) for vc in valid_cols])
        nearest_col = valid_cols[np.argmin(distances)]
        
        # Copy data from nearest column
        vel_values_grid[:, j] = vel_values_grid[:, nearest_col]
    
    # Step 3: Apply Gaussian smoothing
    # Calculate kernel size based on blur value (odd number required)
    kernel_size = int(100 * blur_value) // 2 * 2 + 1  # Ensure odd
    kernel_size = max(3, min(kernel_size, 251))  # Limit between 3 and 251
    
    # Apply Gaussian blur
    vel_values_grid = cv2.GaussianBlur(vel_values_grid.astype(np.float32), (kernel_size, kernel_size), 0)
    
    # Generate model description
    model_description = f"Two-Step Interpolation (Blur={blur_value})"
    
    # Return results
    return {
        'vel_values_grid': vel_values_grid,
        'vel_traces_grid': vel_traces_grid,
        'vel_twts_grid': vel_twts_grid,
        'vel_traces': vel_traces,
        'vel_twts': vel_twts,
        'vel_values': vel_values,
        'model_type': model_description,
        'model_params': {
            'type': 'two_step',
            'blur_value': blur_value
        }
    }


def two_step_model(vel_traces, vel_twts, vel_values, twt_range, trace_range, 
                  ntraces, nsamples, blur_value=2.5, console=None):
    """Apply the two-step interpolation model to create a smooth velocity field."""
    if console:
        info_message(console, f"Running two-step interpolation with blur value {blur_value}")
    
    return run_interpolation(
        vel_traces, vel_twts, vel_values,
        two_step_interpolate, twt_range, trace_range,
        ntraces, nsamples, additional_args=[blur_value], console=console
    )
