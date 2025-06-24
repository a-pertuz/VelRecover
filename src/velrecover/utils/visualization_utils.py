"""Visualization utilities for VelRecover application."""

import numpy as np
import matplotlib.pyplot as plt
import seisio
import seisplot

class SeismicDisplayManager:
    """Class for managing seismic data display and velocity overlays."""
    
    def __init__(self, ax, console=None):

        self.ax = ax
        self.console = console
        self.perc = 75
        self.seismic_data = None
        self.vel_traces = None
        self.vel_twts = None
        self.vel_values = None
        self.colorbar = None
        
        # SEGY metadata
        self.dt_ms = None  # Sample interval in milliseconds
        self.delay = None  # Delay time in milliseconds
        self.nsamples = None
        self.ntraces = None
    
    def load_segy(self, segy_file_path):

        try:
            # Load the SEGY data
            sio = seisio.input(segy_file_path)
            nsamples = sio.nsamples
            ntraces = sio.ntraces
            dt_ms = sio.vsi / 1000.0
            delay = sio.delay
            dataset = sio.read_all_traces()
            self.seismic_data = dataset["data"]
            
            # Store SEGY metadata
            self.nsamples = nsamples
            self.ntraces = ntraces
            self.dt_ms = dt_ms
            self.delay = delay
            
            # Return metadata
            return {
                "nsamples": nsamples,
                "ntraces": ntraces,
                "dt_ms": dt_ms,
                "delay": delay,
                "dataset": dataset
            }
            
        except Exception as e:
            if self.console:
                self.console.append(f"Error loading SEGY file: {str(e)}")
            raise
    
    def load_velocity_picks(self, vel_traces, vel_twts, vel_values, color_range=None):
        self.vel_traces = vel_traces
        self.vel_twts = vel_twts
        self.vel_values = vel_values
        self.vel_color_range = color_range
    
    def display(self, redraw_picks=True, clear_ax=True, show_colorbar=True):
        """ Display the seismic data and velocity picks. """

        if self.seismic_data is None:
            if self.console:
                self.console.append("No seismic data to display")
            return
        
        if clear_ax:
            self.ax.clear()
            if self.colorbar is not None:
                try:
                    self.colorbar.remove()
                except Exception:
                    pass
                self.colorbar = None
        
        # Plot the seismic data
        seisplot.plot(self.seismic_data, 
                      perc=self.perc, 
                      haxis="tracf", 
                      hlabel="Trace Number",
                      vlabel="Time (ms)",
                      colormap='gray',
                      ax=self.ax
                      )
        
        # Overlay the velocity picks if available and requested
        if redraw_picks and self.vel_traces is not None and len(self.vel_traces) > 0 and self.dt_ms is not None:
            # Create a colormap for the velocity values
            if self.vel_color_range is not None:
                vmin, vmax = self.vel_color_range
            else:
                vmin, vmax = np.min(self.vel_values), np.max(self.vel_values)
                
            # Use 'jet' colormap for consistency with interpolation display
            cmap = plt.cm.jet
            
            # Convert TWT values to sample indices for proper display
            # Formula: sample_index = (twt - delay) / dt_ms
            if self.delay is not None:
                # Create array of TWT values converted to proper sample positions
                sample_positions = (self.vel_twts - self.delay) / self.dt_ms
                
                # Log the conversion for debugging
                if self.console:
                    self.console.append(f"Converting TWT values using delay={self.delay}ms, dt={self.dt_ms}ms")
            else:
                # If no delay information, assume zero delay
                sample_positions = self.vel_twts / self.dt_ms
                
                if self.console:
                    self.console.append("Warning: No delay information available, assuming zero delay")
            
            # Plot the picks as scatter points
            sc = self.ax.scatter(self.vel_traces, sample_positions, 
                               c=self.vel_values, cmap=cmap, 
                               vmin=vmin, vmax=vmax,
                               s=30, edgecolor='black', linewidth=0.5, 
                               alpha=0.8, marker='o', zorder=10)
            
            # Add a colorbar for the velocity values only if requested
            if show_colorbar:
                self.colorbar = self.ax.figure.colorbar(sc, ax=self.ax)
                self.colorbar.set_label('Velocity (m/s)')
            
            if self.console:
                self.console.append(f"Plotted {len(self.vel_traces)} velocity picks with velocity range {vmin:.1f}-{vmax:.1f} m/s")
        
        return self.ax
    
    def clear(self):
        """Clear the display and reset the data."""
        self.seismic_data = None
        self.vel_traces = None
        self.vel_twts = None
        self.vel_values = None
        
        self.ax.clear()
        # Safer colorbar removal - same as in display method
        if self.colorbar is not None:
            try:
                self.colorbar.remove()
            except Exception as e:
                pass
            self.colorbar = None
        
        self.ax.set_title("No seismic data loaded")
        
    def set_percentile(self, perc):
        """ Set the percentile value for seismic amplitude scaling."""
        self.perc = perc