"""Data class for velocity interpolation data with SEGY alignment support."""

import numpy as np
from scipy.interpolate import griddata

class VelocityData:
    """Data class to hold velocity interpolation data and ensure SEGY alignment."""
    
    def __init__(self):
        """Initialize with empty data."""
        self.cdp = None
        self.twt = None
        self.vel = None
        self.cdp_grid = None
        self.twt_grid = None
        self.vel_grid = None
        self.original_vel_grid = None
        self.output_vel_grid = None
        self.model_type = None
        self.model_params = None
        self.regression_params = None
        self.text_file_path = None
        self.segy_file_path = None
        self.ntraces = None
        self.nsamples = None
        self.dt_ms = None
        self.delay = None
        self.segy_dimensions = None
    
    def has_data(self):
        """Check if velocity data is loaded."""
        return self.cdp is not None and len(self.cdp) > 0
    
    def has_interpolation(self):
        """Check if interpolation has been performed."""
        return self.vel_grid is not None
    
    def has_segy(self):
        """Check if SEGY file path is set."""
        return self.segy_file_path is not None
    
    def matches_segy_dimensions(self):
        """Check if velocity grid dimensions match SEGY dimensions."""
        if not self.has_interpolation() or not self.has_segy() or self.segy_dimensions is None:
            return False
        return (self.vel_grid.shape[0] == self.segy_dimensions[0] and 
                self.vel_grid.shape[1] == self.segy_dimensions[1])
    
    def set_segy_dimensions(self, nsamples, ntraces, dt_ms=None, delay=None):
        """Set SEGY dimensions for reference."""
        self.segy_dimensions = (nsamples, ntraces)
        self.nsamples = nsamples
        self.ntraces = ntraces
        if dt_ms is not None:
            self.dt_ms = dt_ms
        if delay is not None:
            self.delay = delay
    
    def align_to_segy_dimensions(self):
        """Resample velocity grid to match SEGY dimensions if needed."""
        if not self.has_interpolation() or not self.has_segy() or self.segy_dimensions is None:
            return False
        
        if self.matches_segy_dimensions():
            return True  # Already aligned
        
        # Resample velocity grid to match SEGY dimensions
        try:
            nsamples, ntraces = self.segy_dimensions
            
            # Create source grid points
            source_cdps = np.unique(self.cdp_grid[0, :])
            source_twts = np.unique(self.twt_grid[:, 0])
            
            # Create target grid with correct SEGY dimensions
            target_cdps = np.linspace(min(source_cdps), max(source_cdps), ntraces)
            target_twts = np.linspace(min(source_twts), max(source_twts), nsamples)
            
            # Create new grids
            new_cdp_grid, new_twt_grid = np.meshgrid(target_cdps, target_twts)
            
            # Reshape for griddata
            points = np.vstack((self.cdp_grid.flatten(), self.twt_grid.flatten())).T
            values = self.vel_grid.flatten()
            
            # Perform interpolation
            xi = np.vstack((new_cdp_grid.flatten(), new_twt_grid.flatten())).T
            new_vel_grid = griddata(points, values, xi, method='linear')
            
            # Reshape to 2D
            new_vel_grid = new_vel_grid.reshape(new_twt_grid.shape)
            
            # Update grids
            self.cdp_grid = new_cdp_grid
            self.twt_grid = new_twt_grid
            self.vel_grid = new_vel_grid
            self.original_vel_grid = new_vel_grid.copy()
            self.output_vel_grid = new_vel_grid.copy()
            
            return True
        except Exception:
            return False
    
    def reset(self):
        """Reset all data."""
        self.__init__()
