"""I/O operations for SEGYRecover."""

import os
import numpy as np
import pandas as pd
import seisio
from PySide6.QtWidgets import QFileDialog



def save_velocity_text_data(segy_file_path, cdp_grid, twt_grid, vel_grid, output_dir):
    """Save interpolated velocity data to text file."""
    try:
        # Load the SEGY dataset for X, Y coordinates
        sio = seisio.input(segy_file_path)
        dataset = sio.read_dataset()
        sx = dataset["sx"]
        sy = dataset["sy"]

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
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{base_name}_interpolated_2D.dat")
        output_data.to_csv(output_path, sep='\t', index=False)
        
        return {
            'success': True,
            'path': output_path,
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'path': None,
            'error': str(e)
        }

def save_velocity_binary_data(segy_file_path, vel_grid, output_dir):
    """Save interpolated velocity data to binary file."""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create output file path
        base_name = os.path.splitext(os.path.basename(segy_file_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_interpolated_2D.bin")
        
        # Save binary data
        vel_grid.astype('float32').tofile(output_path)
        
        return {
            'success': True,
            'path': output_path,
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'path': None,
            'error': str(e)
        }
