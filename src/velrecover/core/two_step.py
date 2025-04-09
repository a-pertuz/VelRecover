"""Two-step interpolation model for velocity analysis."""

import numpy as np
import cv2
from scipy.interpolate import RBFInterpolator

from ..utils.console_utils import info_message, warning_message, success_message


def two_step_interpolation(cdp, twt, vel, cdp_range, twt_range, ntraces=None, nsamples=None, 
                          dt_ms=4.0, delay=0.0, console=None, blur_value=2.5):
    """
    Perform two-step interpolation:
    1. Extrapolate velocities for each CDP to cover the full TWT range using RBF interpolation
    2. Use nearest neighbor for missing CDPs and then apply Gaussian smoothing
    
    Parameters:
        blur_value: Controls the Gaussian blur kernel size (higher = smoother transitions)
    """
    if console:
        info_message(console, "Starting two-step interpolation...")
    
    min_cdp, max_cdp = cdp_range
    min_twt, max_twt = twt_range
    
    # Create a full grid using exact dimensions from SEGY file if provided
    if ntraces is not None and nsamples is not None:
        cdp_full = np.linspace(min_cdp, max_cdp, ntraces)
        twt_full = np.linspace(min_twt, max_twt, nsamples)
    else:
        # Ensure grid includes the actual CDP values from the data
        data_min_cdp = np.min(cdp)
        data_max_cdp = np.max(cdp)
        
        # Use the wider range
        min_cdp = min(min_cdp, data_min_cdp)
        max_cdp = max(max_cdp, data_max_cdp)
        
        cdp_step = 1.0  # Use 1.0 CDP spacing
        twt_step = min(5.0, (max_twt - min_twt) / 200)  # Use 5ms or smaller if needed
        
        cdp_full = np.arange(min_cdp, max_cdp + cdp_step, cdp_step)
        twt_full = np.arange(min_twt, max_twt + twt_step, twt_step)
    
    # Create output grids
    cdp_grid, twt_grid = np.meshgrid(cdp_full, twt_full)
    vel_grid = np.zeros_like(cdp_grid, dtype=float)
    vel_grid.fill(np.nan)  # Initialize with NaN
    
    # Step 1: Interpolate for each unique CDP using RBF
    unique_cdps = np.unique(cdp)
    
    if console:
        info_message(console, f"Step 1: Interpolating velocities for {len(unique_cdps)} CDPs...")
    
    # Create mapping from unique CDPs to column indices
    cdp_to_col_idx = {}
    for i, grid_cdp in enumerate(cdp_full):
        distances = np.abs(unique_cdps - grid_cdp)
        if np.min(distances) <= 0.5:  # If within 0.5 of a unique CDP
            closest_cdp = unique_cdps[np.argmin(distances)]
            if closest_cdp not in cdp_to_col_idx:
                cdp_to_col_idx[closest_cdp] = i
    
    # Process each unique CDP
    for unique_cdp in unique_cdps:
        cdp_mask = cdp == unique_cdp
        cdp_twt = twt[cdp_mask]
        cdp_vel = vel[cdp_mask]
        
        if len(cdp_twt) < 2:
            if console:
                warning_message(console, f"CDP {unique_cdp} has only {len(cdp_twt)} points. Skipping.")
            continue
        
        # Sort data points by TWT for proper interpolation
        sort_idx = np.argsort(cdp_twt)
        cdp_twt = cdp_twt[sort_idx]
        cdp_vel = cdp_vel[sort_idx]
        
        try:
            # Reshape for RBF interpolator
            points = cdp_twt.reshape(-1, 1)
            values = cdp_vel

            # Create the RBF interpolator
            rbf_interpolator = RBFInterpolator(points, values, 
                                            kernel='linear', 
                                            smoothing=10)

            # Evaluate at desired points
            query_points = twt_full.reshape(-1, 1)
            extrapolated_vel = rbf_interpolator(query_points)
            
            # Ensure no negative velocities
            extrapolated_vel = np.maximum(extrapolated_vel, np.min(cdp_vel) * 0.5)
            
            # Find column index for this CDP
            if unique_cdp in cdp_to_col_idx:
                col_idx = cdp_to_col_idx[unique_cdp]
                vel_grid[:, col_idx] = extrapolated_vel
            else:
                # Find closest matching column
                col_idx = np.abs(cdp_full - unique_cdp).argmin()
                vel_grid[:, col_idx] = extrapolated_vel
        except Exception as e:
            if console:
                warning_message(console, f"RBF interpolation failed for CDP {unique_cdp}: {str(e)}")
    
    # Step 2: Fill missing CDPs using nearest neighbor, then apply Gaussian blur
    if console:
        info_message(console, "Step 2: Filling missing CDPs using nearest neighbor + Gaussian smoothing...")
    
    # Find columns where we have valid data
    valid_cols = []
    for j in range(vel_grid.shape[1]):
        if not np.all(np.isnan(vel_grid[:, j])):
            valid_cols.append(j)
    
    if len(valid_cols) <= 1:
        if console:
            warning_message(console, "Not enough valid CDPs for interpolation")
        return cdp_grid, twt_grid, vel_grid
    
    # First pass: Use nearest neighbor to fill all gaps
    for j in range(vel_grid.shape[1]):
        if j in valid_cols:
            continue  # Skip columns that already have data
        
        # Find nearest valid column (minimum distance)
        distances = np.array([abs(j - vc) for vc in valid_cols])
        nearest_col = valid_cols[np.argmin(distances)]
        
        # Copy data from nearest column
        vel_grid[:, j] = vel_grid[:, nearest_col]
    
    # Second pass: Apply Gaussian blur to smooth transitions
    info_message(console, "Applying Gaussian smoothing with kernel size 251...")
    
    vel_grid = cv2.GaussianBlur(vel_grid.astype(np.float32), (251, 251), 0)
    
    success_message(console, f"Interpolation complete: {vel_grid.shape[1]} CDPs × {vel_grid.shape[0]} samples")
    
    return cdp_grid, twt_grid, vel_grid
