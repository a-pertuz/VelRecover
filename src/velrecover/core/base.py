"""Base functionality for interpolation methods."""

import numpy as np
import seisio

from ..utils.console_utils import info_message, error_message, success_message


def load_segy_data(segy_file_path, status_callback=None):
    """Load SEGY data and return grid parameters."""
    if status_callback:
        status_callback(5, "Loading SEGY file...")
    
    # Load SEGY file
    sio = seisio.input(segy_file_path)
    nsamples = sio.nsamples
    ntraces = sio.ntraces
    dt = sio.vsi  # Microseconds
    delay = sio.delay
    
    # Calculate TWT range
    dt_ms = dt / 1000.0  # Convert microseconds to milliseconds
    TWT_start = delay  # Use delay as starting time
    TWT_end = TWT_start + (nsamples - 1) * dt_ms
    TWT_range = np.linspace(TWT_start, TWT_end, nsamples)
    CDP_range = np.arange(ntraces)
    
    if status_callback:
        status_callback(10, f"Processing {len(CDP_range)} CDPs and {len(TWT_range)} TWTs...")
        
    return {
        'TWT_range': TWT_range,
        'CDP_range': CDP_range,
        'ntraces': ntraces,
        'nsamples': nsamples,
        'dt_ms': dt_ms,
        'delay': delay
    }

def load_velocity_data(text_file_path, status_callback=None):
    """Load velocity data from text file."""
    if status_callback:
        status_callback(20, "Loading velocity data from text file...")
    
    # Read first few lines to detect delimiter
    with open(text_file_path, 'r') as f:
        first_lines = [f.readline() for _ in range(3)]
    
    # Auto-detect if it's tab-delimited
    has_tabs = any('\t' in line for line in first_lines)
    delimiter = '\t' if has_tabs else None  # None will make loadtxt split on any whitespace
    
    # Load data with appropriate delimiter
    data = np.loadtxt(text_file_path, delimiter=delimiter, skiprows=1)
    CDP, TWT, VEL = data[:, 0], data[:, 1], data[:, 2]
    
    return CDP, TWT, VEL

def create_grid(CDP_range, TWT_range, ntraces, nsamples, status_callback=None):
    """Create grid for interpolation based on SEGY dimensions."""
    if status_callback:
        status_callback(30, "Creating interpolation grid...")

    # Generate grid using SEGY dimensions
    CDP_grid, TWT_grid = np.meshgrid(
        np.linspace(CDP_range[0], CDP_range[-1], ntraces),
        np.linspace(TWT_range[0], TWT_range[-1], nsamples)
    )
    return CDP_grid, TWT_grid

def calculate_r2(y_true, y_pred):
    """Calculate the coefficient of determination (R²)"""
    ss_total = np.sum((y_true - np.mean(y_true)) ** 2)
    ss_residual = np.sum((y_true - y_pred) ** 2)
    
    if ss_total == 0:
        return 0  
    
    r2 = 1 - (ss_residual / ss_total)
    return max(0, r2)

def run_interpolation(text_file_path=None, segy_file_path=None, interpolation_func=None, 
                     additional_args=None, status_callback=None, cancel_check=None, 
                     cdp=None, twt=None, vel=None, console=None):
    """Common implementation for all interpolation methods."""
    try:
        # Load SEGY data
        segy_data = load_segy_data(segy_file_path, status_callback)
        TWT_range = segy_data['TWT_range']
        CDP_range = segy_data['CDP_range']
        ntraces = segy_data['ntraces']
        
        # Use provided velocity data or load from file
        if cdp is not None and twt is not None and vel is not None:
            CDP = cdp
            TWT = twt
            VEL = vel
        else:
            # Check if text file is provided
            if not text_file_path:
                return {'error': "No velocity data provided and no text file path specified"}
                
            # Load velocity data from file
            CDP, TWT, VEL = load_velocity_data(text_file_path, status_callback)
        
        # Create interpolation grid
        CDP_grid, TWT_grid = create_grid(CDP_range, TWT_range, ntraces, segy_data['nsamples'], status_callback)
        
        # Check for cancellation
        if cancel_check and cancel_check():
            return {'cancelled': True}
        
        # Prepare arguments
        args = [
            CDP, TWT, VEL, 
            CDP_grid, TWT_grid, 
            CDP_range, TWT_range, 
            status_callback, cancel_check
        ]
        
        # Add additional arguments if provided
        if additional_args:
            args.extend(additional_args)
        
        # Run the interpolation algorithm
        result = interpolation_func(*args)
        
        # Check for cancellation
        if cancel_check and cancel_check():
            return {'cancelled': True}
        
        # Add base data to the result
        result.update({
            'CDP': CDP,
            'TWT': TWT,
            'VEL': VEL,
            'CDP_grid': CDP_grid,
            'TWT_grid': TWT_grid,
            'ntraces': ntraces,
            'cancelled': False
        })
        
        return result
        
    except Exception as e:
        if console:
            error_message(console, f"Error during interpolation: {str(e)}")
        return {'error': str(e), 'cancelled': False}