"""Utilities for velocity data interpolation."""

import numpy as np
from scipy.optimize import curve_fit

# Import models only when needed in each function to avoid circular imports
from ..core.base import load_segy_data, calculate_r2
from ..core.linear_models import linear_model
from ..core.logarithmic_models import logarithmic_model

# Import our own gaussian blur function
from ..core.gauss_blur import apply_gaussian_blur

# Import VelocityData from its own module
from .VelocityData import VelocityData

from ..utils.console_utils import info_message


def load_text_data(file_path, delimiter=None):
    """
    Load velocity data from a text file.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        dict: Result with success/error information and loaded data
    """
    try:
        # Create velocity data object
        vel_data = VelocityData()
        


        # Auto-detect delimiter if not specified
        if delimiter is None:
            with open(file_path, 'r') as f:
                first_lines = [f.readline() for _ in range(3)]
            has_tabs = any('\t' in line for line in first_lines)
            delimiter = '\t' if has_tabs else None
        
        # Load data
        data = np.loadtxt(file_path, delimiter=delimiter, skiprows=1, comments='#')
        
        # Check data dimensions
        if data.shape[1] < 3:
            return {
                'success': False,
                'error': 'Invalid data format. Expected at least 3 columns: CDP TWT VEL'
            }
        
        # Store data in velocity data object
        vel_data.cdp = data[:, 0]
        vel_data.twt = data[:, 1]
        vel_data.vel = data[:, 2]
        
        # Store text file path for reference
        vel_data.text_file_path = file_path
        
        # Calculate regression parameters
        vel_data.regression_params = calculate_regression_params(vel_data.twt, vel_data.vel)
        
        # Return success with data
        return {
            'success': True,
            'data': vel_data,
            'stats': {
                'points': len(vel_data.cdp),
                'CDP range': f"{min(vel_data.cdp):.0f} to {max(vel_data.cdp):.0f}",
                'TWT range': f"{min(vel_data.twt):.1f} to {max(vel_data.twt):.1f} ms",
                'velocity range': f"{min(vel_data.vel):.0f} to {max(vel_data.vel):.0f} m/s",
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def calculate_regression_params(twt, vel):
    """Calculate regression parameters for visualization."""
    if twt is None or vel is None:
        return {}
    
    result = {}
    
    try:
        # Linear regression
        p0_linear = [1500, 0.5]  # Initial guess
        params_linear, _ = curve_fit(linear_model, twt, vel, p0=p0_linear)
        v0_linear, k_linear = params_linear
        pred_linear = linear_model(twt, v0_linear, k_linear)
        r2_linear = calculate_r2(vel, pred_linear)
        
        result['linear'] = {
            'v0': v0_linear,
            'k': k_linear,
            'r2': r2_linear
        }
        
        # Logarithmic regression if we have positive TWT values
        valid_indices = twt > 0
        if np.sum(valid_indices) > 2:
            twt_valid = twt[valid_indices]
            vel_valid = vel[valid_indices]
            
            p0_log = [1500, 1000]  # Initial guess
            params_log, _ = curve_fit(logarithmic_model, twt_valid, vel_valid, p0=p0_log)
            v0_log, k_log = params_log
            pred_log = logarithmic_model(twt_valid, v0_log, k_log)
            r2_log = calculate_r2(vel_valid, pred_log)
            
            result['logarithmic'] = {
                'v0': v0_log,
                'k': k_log,
                'r2': r2_log
            }
            
    except Exception:
        pass
        
    return result

def load_segy_file(velocity_data, file_path):
    """
    Load SEGY file and associate with velocity data.
    
    Args:
        velocity_data: VelocityData object to update
        file_path: Path to the SEGY file
        
    Returns:
        dict: Result with success/error information
    """
    try:
        import seisio
        
        # Load SEGY file header to get dimensions
        sio = seisio.input(file_path)
        
        # Set SEGY dimensions in velocity data
        velocity_data.set_segy_dimensions(
            nsamples=sio.nsamples,
            ntraces=sio.ntraces,
            dt_ms=sio.vsi / 1000.0,
            delay=sio.delay
        )
        
        # Update SEGY file path
        velocity_data.segy_file_path = file_path
        
        # If interpolation exists, align to SEGY dimensions
        if velocity_data.has_interpolation():
            velocity_data.align_to_segy_dimensions()
        
        return {'success': True}
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def interpolate(velocity_data, method, console=None, status_callback=None, cancel_check=None, **kwargs):
    """
    Perform interpolation using the specified method.
    
    Args:
        velocity_data: VelocityData object with loaded data
        method: Interpolation method ('rbf', 'custom_linear', etc.)
        console: Console widget for logging
        status_callback: Function for progress updates
        cancel_check: Function to check if operation should be cancelled
        **kwargs: Additional parameters for specific methods
    
    Returns:
        dict: Result with success/error information
    """
    # Import here to avoid circular imports
    from ..core.rbf_models import interpolate_velocity_data_rbf
    from ..core.linear_models import custom_linear_model, best_linear_fit
    from ..core.logarithmic_models import best_logarithmic_fit, custom_logarithmic_model
    from ..core.two_step import two_step_interpolation
    
    try:
        # Common parameters for all interpolation methods
        common_params = {
            'console': console,
            'status_callback': status_callback,
            'cancel_check': cancel_check,
            'cdp': velocity_data.cdp,
            'twt': velocity_data.twt,
            'vel': velocity_data.vel,
            'segy_file_path': velocity_data.segy_file_path
        }
        
        # Log parameter info for debugging
        if console and method == "custom_linear" and 'v0' in kwargs and 'k' in kwargs:
            info_message(console, f"Using custom linear parameters: v0={kwargs['v0']:.2f}, k={kwargs['k']:.6f}")
        
        if console and method == "custom_log" and 'v0' in kwargs and 'k' in kwargs:
            info_message(console, f"Using custom logarithmic parameters: v0={kwargs['v0']:.2f}, k={kwargs['k']:.1f}")
        
        # Select appropriate interpolation function based on method
        if method == "rbf":
            result = interpolate_velocity_data_rbf(**common_params)
        elif method == "custom_linear":
            # Extract custom model parameters
            v0 = float(kwargs.get('v0', 1500.0))
            k = float(kwargs.get('k', 0.5))
            result = custom_linear_model(v0=v0, k=k, **common_params)
        elif method == "custom_log":
            # Extract custom model parameters
            v0 = float(kwargs.get('v0', 1500.0))
            k = float(kwargs.get('k', 1000.0))
            result = custom_logarithmic_model(v0=v0, k=k, **common_params)
        elif method == "best_linear":
            result = best_linear_fit(**common_params)
        elif method == "best_log":
            result = best_logarithmic_fit(**common_params)
        elif method == "two_step":
            segy_data = load_segy_data(velocity_data.segy_file_path, status_callback)
            cdp_range = (float(min(segy_data['CDP_range'])), float(max(segy_data['CDP_range'])))
            twt_range = (float(min(segy_data['TWT_range'])), float(max(segy_data['TWT_range'])))
            
            # Call two_step_interpolation with exact SEGY dimensions
            cdp_grid, twt_grid, vel_grid = two_step_interpolation(
                velocity_data.cdp, velocity_data.twt, velocity_data.vel,
                cdp_range, twt_range,
                ntraces=segy_data['ntraces'],
                nsamples=segy_data['nsamples'],
                dt_ms=segy_data['dt_ms'],
                delay=segy_data['delay'],
                console=console
            )
            
            # Format result like other methods
            result = {
                'CDP': velocity_data.cdp,
                'TWT': velocity_data.twt,
                'VEL': velocity_data.vel,
                'CDP_grid': cdp_grid,
                'TWT_grid': twt_grid,
                'VEL_grid': vel_grid,
                'ntraces': segy_data['ntraces'],
                'nsamples': segy_data['nsamples'],
                'model_type': "Two-Step Interpolation",
                'model_params': {
                    'type': 'two_step'
                }
            }
        else:
            return {
                'success': False,
                'error': f"Unknown interpolation method: {method}"
            }
        
        # Check for cancellation
        if result.get('cancelled'):
            return {
                'success': False,
                'cancelled': True
            }
        
        # Check for errors
        if 'error' in result:
            return {
                'success': False,
                'error': result['error']
            }
        
        # Store results
        velocity_data.cdp_grid = result['CDP_grid']
        velocity_data.twt_grid = result['TWT_grid']
        velocity_data.vel_grid = result['VEL_grid']
        velocity_data.original_vel_grid = result['VEL_grid'].copy()
        velocity_data.output_vel_grid = result['VEL_grid'].copy()
        velocity_data.model_type = result['model_type']
        velocity_data.ntraces = result['ntraces']
        velocity_data.nsamples = result.get('nsamples', velocity_data.twt_grid.shape[0])
        
        if 'model_params' in result:
            velocity_data.model_params = result['model_params']
        
        # Calculate statistics
        stats = {
            'method': velocity_data.model_type,
            'cdp_range': (int(np.min(velocity_data.cdp_grid)), int(np.max(velocity_data.cdp_grid))),
            'twt_range': (float(np.min(velocity_data.twt_grid)), float(np.max(velocity_data.twt_grid))),
            'vel_range': (float(np.min(velocity_data.vel_grid)), float(np.max(velocity_data.vel_grid))),
            'dimensions': f"{velocity_data.vel_grid.shape[0]} time samples × {velocity_data.vel_grid.shape[1]} traces"
        }
        
        return {
            'success': True,
            'stats': stats
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def apply_smoothing(velocity_data, blur_value):
    """Apply Gaussian blur to velocity grid."""
    try:
        blur_value = int(blur_value)
        velocity_data.output_vel_grid = apply_gaussian_blur(velocity_data.vel_grid, blur_value)
        
        return {
            'success': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
