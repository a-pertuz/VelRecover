"""Utility functions for exporting velocity data."""

import os
import numpy as np
import pandas as pd
import seisio  # Assuming this is the library used for SEGY operations

def save_velocity_text_data(config, segy_file_path, cdp_grid, twt_grid, vel_grid):
    """Save interpolated velocity data to text file."""
    try:
        # Load the SEGY dataset for X, Y coordinates
        sio = seisio.input(segy_file_path)
        dataset = sio.read_dataset()
        sx = dataset["sx"]
        sy = dataset["sy"]
        
        # Ensure the array dimensions align with SEGY dimensions
        if len(sx) != vel_grid.shape[1]:
            # We need to ensure the arrays have the same number of CDPs
            # If mismatched, interpolate to match the SEGY's CDP count
            from scipy.interpolate import griddata
            
            # Get the current grid points
            old_cdps = np.unique(cdp_grid[0, :])
            old_twts = np.unique(twt_grid[:, 0])
            
            # Create a new grid with the correct CDP count
            new_cdps = np.linspace(min(old_cdps), max(old_cdps), len(sx))
            new_twts = old_twts  # Preserve time samples
            
            # Recreate the grid with correct dimensions
            new_cdp_grid, new_twt_grid = np.meshgrid(new_cdps, new_twts)
            
            # Interpolate velocity values to the new grid
            grid_points = (cdp_grid.ravel(), twt_grid.ravel())
            vel_values = vel_grid.ravel()
            new_grid_points = (new_cdp_grid.ravel(), new_twt_grid.ravel())
            new_vel_grid = griddata(grid_points, vel_values, new_grid_points).reshape(new_twt_grid.shape)
            
            # Update the grids for saving
            cdp_grid = new_cdp_grid
            twt_grid = new_twt_grid
            vel_grid = new_vel_grid

        # Create dataframe with SEGY trace metadata
        segy_data = pd.DataFrame({
            'CDP': range(1, len(sx) + 1),
            'X': sx,
            'Y': sy
        })
        segy_data['CDP'] = segy_data['CDP'].astype(int)

        # Create dataframe with interpolated velocities
        vel_data = pd.DataFrame({
            'CDP': cdp_grid.ravel().astype(int),
            'TWT': twt_grid.ravel().astype(int),
            'VEL': vel_grid.ravel().astype(int)
        })
        vel_data['CDP'] = vel_data['CDP'] + 1

        # Ensure data is in the correct byte order
        for col in segy_data.columns:
            if segy_data[col].dtype.byteorder == '>':
                segy_data[col] = segy_data[col].astype(segy_data[col].dtype.newbyteorder('<'))

        for col in vel_data.columns:
            if vel_data[col].dtype.byteorder == '>':
                vel_data[col] = vel_data[col].astype(vel_data[col].dtype.newbyteorder('<'))

        # Merge datasets
        output_data = pd.merge(segy_data, vel_data, on='CDP')

        # Save data to file
        base_name = os.path.splitext(os.path.basename(segy_file_path))[0]
        os.makedirs(config.vels_dir, exist_ok=True)
        output_path = os.path.join(config.vels_dir, f"{base_name}_interpolated_2D.dat")
        output_data.to_csv(output_path, sep='\t', index=False)
        
        return {
            'success': True,
            'path': output_path
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def save_velocity_binary_data(config, segy_file_path, vel_grid):
    """Save interpolated velocity data to binary file."""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(config.vels_dir, exist_ok=True)
        
        # Create output file path
        base_name = os.path.splitext(os.path.basename(segy_file_path))[0]
        output_path = os.path.join(config.vels_dir, f"{base_name}_interpolated_2D.bin")
        
        # Load SEGY info to confirm dimensions match
        sio = seisio.input(segy_file_path)
        nsamples = sio.nsamples
        ntraces = sio.ntraces
        
        # Check if the velocity grid has the correct dimensions
        if vel_grid.shape[0] != nsamples or vel_grid.shape[1] != ntraces:
            # Log warning about dimension mismatch and resample
            from scipy.interpolate import griddata
            import numpy as np
            
            # Create source and target grids
            source_shape = vel_grid.shape
            source_cdps = np.linspace(0, ntraces-1, source_shape[1])
            source_twts = np.linspace(0, nsamples-1, source_shape[0])
            source_cdp_grid, source_twt_grid = np.meshgrid(source_cdps, source_twts)
            
            # Create target grid with correct SEGY dimensions
            target_cdps = np.arange(ntraces)
            target_twts = np.arange(nsamples)
            target_cdp_grid, target_twt_grid = np.meshgrid(target_cdps, target_twts)
            
            # Interpolate to the correct dimensions
            grid_points = (source_cdp_grid.ravel(), source_twt_grid.ravel())
            vel_values = vel_grid.ravel()
            target_points = (target_cdp_grid.ravel(), target_twt_grid.ravel())
            resampled_vel_grid = griddata(grid_points, vel_values, target_points).reshape((nsamples, ntraces))
            
            # Use the resampled grid
            vel_grid = resampled_vel_grid
        
        # Save binary data with correct float32 format
        vel_grid.astype('float32').tofile(output_path)
        
        return {
            'success': True,
            'path': output_path
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }