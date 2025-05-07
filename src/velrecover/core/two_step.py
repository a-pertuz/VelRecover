"""Two-step interpolation model for velocity analysis."""

import numpy as np
import cv2
from scipy.interpolate import RBFInterpolator

from ..utils.console_utils import info_message, warning_message, success_message


def two_step_interpolation(vel_traces, vel_twts, vel_values, trace_range, twt_range, ntraces=None, nsamples=None, 
                          dt_ms=4.0, delay=0.0, console=None, blur_value=2.5):
    """
    Perform two-step interpolation:
    1. Extrapolate velocities for each trace to cover the full TWT range using RBF interpolation
    2. Use nearest neighbor for missing traces and then apply Gaussian smoothing
    
    Parameters:
        blur_value: Controls the Gaussian blur kernel size (higher = smoother transitions)
    """
    if console:
        info_message(console, "Starting two-step interpolation...")
    
    min_trace, max_trace = trace_range
    min_twt, max_twt = twt_range
    
    # Create a full grid using exact dimensions from SEGY file if provided
    if ntraces is not None and nsamples is not None:
        traces_full = np.linspace(min_trace, max_trace, ntraces)
        twts_full = np.linspace(min_twt, max_twt, nsamples)
    else:
        # Ensure grid includes the actual trace values from the data
        data_min_trace = np.min(vel_traces)
        data_max_trace = np.max(vel_traces)
        
        # Use the wider range
        min_trace = min(min_trace, data_min_trace)
        max_trace = max(max_trace, data_max_trace)
        
        trace_step = 1.0  # Use 1.0 trace spacing
        twt_step = min(5.0, (max_twt - min_twt) / 200)  # Use 5ms or smaller if needed
        
        traces_full = np.arange(min_trace, max_trace + trace_step, trace_step)
        twts_full = np.arange(min_twt, max_twt + twt_step, twt_step)
    
    # Create output grids
    vel_traces_grid, vel_twts_grid = np.meshgrid(traces_full, twts_full)
    vel_values_grid = np.zeros_like(vel_traces_grid, dtype=float)
    vel_values_grid.fill(np.nan)  # Initialize with NaN
    
    # Step 1: Interpolate for each unique trace using RBF
    unique_traces = np.unique(vel_traces)
    
    if console:
        info_message(console, f"Step 1: Interpolating velocities for {len(unique_traces)} traces...")
    
    # Create mapping from unique traces to column indices
    trace_to_col_idx = {}
    for i, grid_trace in enumerate(traces_full):
        distances = np.abs(unique_traces - grid_trace)
        if np.min(distances) <= 0.5:  # If within 0.5 of a unique trace
            closest_trace = unique_traces[np.argmin(distances)]
            if closest_trace not in trace_to_col_idx:
                trace_to_col_idx[closest_trace] = i
    
    # Process each unique trace
    for unique_trace in unique_traces:
        trace_mask = vel_traces == unique_trace
        trace_twts = vel_twts[trace_mask]
        trace_vals = vel_values[trace_mask]
        
        if len(trace_twts) < 2:
            if console:
                warning_message(console, f"Trace {unique_trace} has only {len(trace_twts)} points. Skipping.")
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
            rbf_interpolator = RBFInterpolator(points, values, 
                                            kernel='linear', 
                                            smoothing=10)

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
            if console:
                warning_message(console, f"RBF interpolation failed for trace {unique_trace}: {str(e)}")
    
    # Step 2: Fill missing traces using nearest neighbor, then apply Gaussian blur
    if console:
        info_message(console, "Step 2: Filling missing traces using nearest neighbor + Gaussian smoothing...")
    
    # Find columns where we have valid data
    valid_cols = []
    for j in range(vel_values_grid.shape[1]):
        if not np.all(np.isnan(vel_values_grid[:, j])):
            valid_cols.append(j)
    
    if len(valid_cols) <= 1:
        if console:
            warning_message(console, "Not enough valid traces for interpolation")
        return vel_traces_grid, vel_twts_grid, vel_values_grid
    
    # First pass: Use nearest neighbor to fill all gaps
    for j in range(vel_values_grid.shape[1]):
        if j in valid_cols:
            continue  # Skip columns that already have data
        
        # Find nearest valid column (minimum distance)
        distances = np.array([abs(j - vc) for vc in valid_cols])
        nearest_col = valid_cols[np.argmin(distances)]
        
        # Copy data from nearest column
        vel_values_grid[:, j] = vel_values_grid[:, nearest_col]
    
    # Second pass: Apply Gaussian blur to smooth transitions
    info_message(console, "Applying Gaussian smoothing with kernel size 251...")
    
    vel_values_grid = cv2.GaussianBlur(vel_values_grid.astype(np.float32), (251, 251), 0)
    
    success_message(console, f"Interpolation complete: {vel_values_grid.shape[1]} traces × {vel_values_grid.shape[0]} samples")
    
    return vel_traces_grid, vel_twts_grid, vel_values_grid
