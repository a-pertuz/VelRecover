"""Two-step interpolation model for velocity analysis."""

import numpy as np
from scipy.interpolate import RBFInterpolator

from ..utils.console_utils import info_message, warning_message, success_message

def two_step_interpolation(cdp, twt, vel, cdp_range, twt_range, ntraces=None, nsamples=None, 
                          dt_ms=4.0, delay=0.0, console=None):
    """
    Perform two-step interpolation:
    1. Extrapolate velocities for each CDP to cover the full TWT range using RBF interpolation
    2. Interpolate missing CDPs using RBF interpolation with linear kernel
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
    
    # Step 2: Fill missing CDPs using RBF interpolation instead of nearest neighbor
    if console:
        info_message(console, "Step 2: Filling missing CDPs using RBF interpolation...")
    
    # Fill remaining NaN values
    valid_mask = ~np.isnan(vel_grid)
    if np.any(valid_mask):
        # Get points where we have velocity data
        grid_points = np.array([(twt_grid[i, j], cdp_grid[i, j]) 
                            for i, j in zip(*np.where(valid_mask))])
        grid_values = vel_grid[valid_mask]
        
        # Get points where we need to interpolate
        nan_points = np.array([(twt_grid[i, j], cdp_grid[i, j]) 
                            for i, j in zip(*np.where(~valid_mask))])
        
        if len(grid_points) > 0 and len(nan_points) > 0:
            # Use RBF interpolation with linear kernel and smoothing=10
            rbf_interp = RBFInterpolator(grid_points, grid_values, 
                                        kernel='linear', 
                                        smoothing=10)
            interp_values = rbf_interp(nan_points)
            
            # Assign interpolated values to grid
            for (i, j), value in zip(zip(*np.where(~valid_mask)), interp_values):
                vel_grid[i, j] = value
    
    if console:
        success_message(console, f"Interpolation complete: {vel_grid.shape[1]} CDPs × {vel_grid.shape[0]} samples")
    
    return cdp_grid, twt_grid, vel_grid
