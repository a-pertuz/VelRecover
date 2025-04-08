"""I/O operations for VelRecover."""

import os
import shutil
import numpy as np
import pandas as pd
import seisio

from .console_utils import info_message, success_message, error_message

def initialize_directories(config):
    """Initialize required directories."""
    return config.create_directories()

def copy_tutorial_files(work_dir, console=None):
    """
    Copy tutorial files to the specified directory using importlib
    
    Args:
        work_dir (str): Target directory where tutorial files will be copied
        console: Optional console for logging
    
    Returns:
        bool: True if copying was successful, False otherwise
    """
    import importlib.resources
    from .console_utils import info_message, warning_message, success_message
    
    if console:
        info_message(console, f"Copying tutorial files to {work_dir}")
    
    success = True
    copied_files = []
    
    # Create the target directory if it doesn't exist
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        # Get the path to the examples directory using importlib.resources
        with importlib.resources.path('velrecover', 'examples') as tutorial_path:
            tutorial_dir = str(tutorial_path)
        
        if console:
            info_message(console, f"Found example files at: {tutorial_dir}")
        
        if os.path.exists(tutorial_dir):
            # Copy the SEGY folder
            src_segy = os.path.join(tutorial_dir, "SEGY")
            dst_segy = os.path.join(work_dir, "SEGY")
            
            if os.path.exists(src_segy):
                if console:
                    info_message(console, f"Copying SEGY files from {src_segy}")
                
                os.makedirs(dst_segy, exist_ok=True)
                
                # List files before copying
                segy_files = os.listdir(src_segy)
                
                for file in segy_files:
                    src_path = os.path.join(src_segy, file)
                    dst_path = os.path.join(dst_segy, file)
                    if os.path.isfile(src_path):
                        try:
                            shutil.copy2(src_path, dst_path)
                            copied_files.append(dst_path)
                        except Exception as file_error:
                            if console:
                                warning_message(console, f"Error copying {file}: {file_error}")
                            success = False
            else:
                if console:
                    warning_message(console, f"SEGY source directory not found: {src_segy}")
                success = False
            
            # Copy the VELS folder with subfolders
            src_vels = os.path.join(tutorial_dir, "VELS")
            dst_vels = os.path.join(work_dir, "VELS")
            
            if os.path.exists(src_vels):
                if console:
                    info_message(console, f"Copying VELS directory from {src_vels}")
                
                if os.path.exists(dst_vels):
                    shutil.rmtree(dst_vels)
                
                try:
                    shutil.copytree(src_vels, dst_vels)
                    
                    # Add copied files to the list
                    for root, _, files in os.walk(dst_vels):
                        for file in files:
                            copied_files.append(os.path.join(root, file))
                    
                except Exception as vels_error:
                    if console:
                        warning_message(console, f"Error copying VELS directory: {vels_error}")
                    success = False
            else:
                if console:
                    warning_message(console, f"VELS source directory not found: {src_vels}")
                success = False
                
        else:
            if console:
                warning_message(console, f"Tutorial directory not found: {tutorial_dir}")
            success = False
    except Exception as e:
        if console:
            warning_message(console, f"Error accessing tutorial files: {e}")
        success = False
    
    # Summary
    if success and copied_files:
        if console:
            success_message(console, f"Copied {len(copied_files)} tutorial files to {work_dir}")
    else:
        if console:
            warning_message(console, "Some tutorial files could not be copied")
    
    return success

def copy_data_between_directories(source_dir, target_dir, progress_callback=None):
    """Copy data from one directory to another with progress updates."""
    try:
        # Show progress
        if progress_callback:
            progress_callback(0, "Preparing to copy data files...")
        
        folders = ['VELS', 'SEGY']
        processed = 0
        copied_files = []
        
        for folder in folders:
            src_folder = os.path.join(source_dir, folder)
            dst_folder = os.path.join(target_dir, folder)
            
            if os.path.exists(src_folder):
                # Create target folder if it doesn't exist
                os.makedirs(dst_folder, exist_ok=True)
                
                # Get list of all files to copy
                all_files = []
                for root, dirs, files in os.walk(src_folder):
                    for file in files:
                        src_file = os.path.join(root, file)
                        # Create relative path
                        rel_path = os.path.relpath(src_file, src_folder)
                        dst_file = os.path.join(dst_folder, rel_path)
                        # Make sure destination directory exists
                        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                        all_files.append((src_file, dst_file))
                
                # Copy files with progress updates
                total_files = len(all_files)
                for i, (src_file, dst_file) in enumerate(all_files):
                    shutil.copy2(src_file, dst_file)
                    copied_files.append(dst_file)
                    if progress_callback and total_files > 0:
                        progress = int((i + 1) / total_files * 50) + processed
                        progress_callback(progress, f"Copying {os.path.basename(src_file)}...")
            
            processed += 50  # Each folder is 50% of the progress
        
        if progress_callback:
            progress_callback(100, f"Copied {len(copied_files)} files")
        
        return {
            'success': True,
            'copied_files': copied_files
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

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
