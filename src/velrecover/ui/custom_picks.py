"""Custom velocity picks functionality for the SEGY viewer."""

import os
import numpy as np
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from ..utils.console_utils import info_message, warning_message, success_message
from .dialogs import VelocityEntryDialog

class CustomPicksManager:
    """Manager for custom velocity picks functionality."""
    
    def __init__(self, segy_viewer, console=None):
        """
        Initialize the custom picks manager.
        
        Args:
            segy_viewer: The parent SEGY viewer that contains the picks
            console: Console widget for logging messages
        """
        self.segy_viewer = segy_viewer
        self.console = console
        
        # Initialize picks arrays
        self.custom_cdp = np.array([])
        self.custom_twt = np.array([])
        self.custom_vel = np.array([])
        self.has_picks = False
        self.delete_mode = False
        self.custom_picks_mode = False
        
        # Store original picks for potential restoration
        self.original_cdp = None
        self.original_twt = None
        self.original_vel = None
        
        # Reference to the original velocity data file path
        self.source_file_path = None
    
    def initialize_from_existing(self, cdp, twt, vel, source_file_path=None):
        """
        Initialize custom picks from existing velocity picks.
        
        Args:
            cdp: Array of CDP values
            twt: Array of TWT values
            vel: Array of velocity values
            source_file_path: Path to the source velocity file
        """
        if cdp is not None and twt is not None and vel is not None:
            self.custom_cdp = np.copy(cdp)
            self.custom_twt = np.copy(twt)
            self.custom_vel = np.copy(vel)
            self.has_picks = len(self.custom_cdp) > 0
            
            # Store original picks
            self.original_cdp = np.copy(cdp)
            self.original_twt = np.copy(twt)
            self.original_vel = np.copy(vel)
            
            # Store source file path
            self.source_file_path = source_file_path
            
            if self.console:
                info_message(self.console, "Custom picks initialized from existing picks")
        else:
            self.custom_cdp = np.array([])
            self.custom_twt = np.array([])
            self.custom_vel = np.array([])
            self.has_picks = False
            
            if self.console:
                info_message(self.console, "Empty custom picks initialized")
    
    def reset(self):
        """Reset custom picks to original values."""
        if self.original_cdp is not None and self.original_twt is not None and self.original_vel is not None:
            self.custom_cdp = np.copy(self.original_cdp)
            self.custom_twt = np.copy(self.original_twt)
            self.custom_vel = np.copy(self.original_vel)
            self.has_picks = len(self.custom_cdp) > 0
            
            if self.console:
                info_message(self.console, "Custom picks reset to original values")
        else:
            self.clear()
    
    def clear(self):
        """Clear all custom picks."""
        self.custom_cdp = np.array([])
        self.custom_twt = np.array([])
        self.custom_vel = np.array([])
        self.has_picks = False
        
        if self.console:
            info_message(self.console, "Custom picks cleared")
    
    def add_pick(self, cdp, twt, vel):
        """
        Add a new velocity pick.
        
        Args:
            cdp: CDP value
            twt: TWT value
            vel: Velocity value
            
        Returns:
            bool: True if added successfully
        """
        try:
            self.custom_cdp = np.append(self.custom_cdp, cdp)
            self.custom_twt = np.append(self.custom_twt, twt)
            self.custom_vel = np.append(self.custom_vel, vel)
            self.has_picks = True
            
            if self.console:
                info_message(self.console, f"Added new pick at CDP {cdp:.0f}, TWT {twt:.1f} ms with {vel} m/s")
                
            return True
        except Exception as e:
            if self.console:
                warning_message(self.console, f"Error adding velocity pick: {str(e)}")
            return False
    
    def update_pick(self, idx, vel):
        """
        Update the velocity of an existing pick.
        
        Args:
            idx: Index of the pick to update
            vel: New velocity value
            
        Returns:
            bool: True if updated successfully
        """
        if idx < 0 or idx >= len(self.custom_cdp):
            return False
            
        try:
            cdp = self.custom_cdp[idx]
            twt = self.custom_twt[idx]
            self.custom_vel[idx] = vel
            
            if self.console:
                info_message(self.console, f"Updated pick at CDP {cdp:.0f}, TWT {twt:.1f} ms to {vel} m/s")
                
            return True
        except Exception as e:
            if self.console:
                warning_message(self.console, f"Error updating velocity pick: {str(e)}")
            return False
    
    def delete_pick(self, idx):
        """
        Delete a velocity pick.
        
        Args:
            idx: Index of the pick to delete
            
        Returns:
            tuple: (deleted_cdp, deleted_twt, deleted_vel) or None if failed
        """
        if idx < 0 or idx >= len(self.custom_cdp):
            return None
            
        try:
            deleted_cdp = self.custom_cdp[idx]
            deleted_twt = self.custom_twt[idx]
            deleted_vel = self.custom_vel[idx]
            
            # Remove the pick
            self.custom_cdp = np.delete(self.custom_cdp, idx)
            self.custom_twt = np.delete(self.custom_twt, idx)
            self.custom_vel = np.delete(self.custom_vel, idx)
            
            # Update has_picks flag
            self.has_picks = len(self.custom_cdp) > 0
            
            if self.console:
                info_message(self.console, f"Deleted pick at CDP {deleted_cdp:.0f}, TWT {deleted_twt:.1f} ms with {deleted_vel:.0f} m/s")
                
            return (deleted_cdp, deleted_twt, deleted_vel)
        except Exception as e:
            if self.console:
                warning_message(self.console, f"Error deleting velocity pick: {str(e)}")
            return None
    
    def find_nearest_pick(self, cdp, twt, cdp_tolerance=10, twt_tolerance=20):
        """
        Find the index of the nearest pick to a given position.
        
        Args:
            cdp: CDP value to search near
            twt: TWT value to search near
            cdp_tolerance: Tolerance for CDP values
            twt_tolerance: Tolerance for TWT values
            
        Returns:
            tuple: (index, distance) or (-1, float('inf')) if no pick found
        """
        if len(self.custom_cdp) == 0:
            return -1, float('inf')
            
        distances = []
        for i in range(len(self.custom_cdp)):
            # Calculate normalized distance to account for different scales of CDP and TWT
            cdp_dist = abs(self.custom_cdp[i] - cdp) / cdp_tolerance
            twt_dist = abs(self.custom_twt[i] - twt) / twt_tolerance
            distance = np.sqrt(cdp_dist**2 + twt_dist**2)
            distances.append(distance)
        
        # Find the minimum distance
        min_idx = np.argmin(distances)
        min_distance = distances[min_idx]
        
        # Return index only if it's within tolerance
        if min_distance <= 1.5:  # Within 1.5x of the normalized tolerance
            return min_idx, min_distance
        else:
            return -1, float('inf')
    
    def save_custom_picks(self):
        """
        Save custom picks to a file using a file dialog.
        
        Returns:
            tuple: (success, file_path) or (False, None) if cancelled or failed
        """
        if not self.has_picks or len(self.custom_cdp) == 0:
            if self.console:
                info_message(self.console, "No custom picks to save")
            return False, None
            
        # Determine default directory and filename
        default_dir = os.path.dirname(self.source_file_path) if self.source_file_path else None
        default_filename = None
        
        if self.source_file_path:
            base, ext = os.path.splitext(os.path.basename(self.source_file_path))
            default_filename = f"{base}_custom{ext}"
            
            # Get complete default path
            if default_dir:
                default_path = os.path.join(default_dir, default_filename)
            else:
                default_path = default_filename
        else:
            default_path = "custom_picks.txt"
            
        # Show file dialog to select save location
        file_path, _ = QFileDialog.getSaveFileName(
            self.segy_viewer,
            "Save Custom Picks",
            default_path,
            "Text Files (*.txt *.dat);;All Files (*.*)"
        )
        
        if not file_path:
            return False, None  # User cancelled
            
        try:
            # Create a formatted string with the data
            with open(file_path, 'w') as f:
                # Write header
                f.write("# Custom velocity picks - created by velrecover\n")
                f.write("# CDP TWT(ms) Velocity(m/s)\n")
                
                # Write each data point
                for cdp, twt, vel in zip(self.custom_cdp, self.custom_twt, self.custom_vel):
                    f.write(f"{cdp:.0f} {twt:.1f} {vel:.0f}\n")
            
            if self.console:
                success_message(self.console, f"Custom picks saved to: {os.path.basename(file_path)}")
                
            return True, file_path
            
        except Exception as e:
            if self.console:
                warning_message(self.console, f"Error saving custom picks: {str(e)}")
                
            # Show error message
            QMessageBox.critical(
                self.segy_viewer,
                "Save Error",
                f"Failed to save custom picks: {str(e)}"
            )
            
            return False, None
            
    def enable_custom_picks_mode(self, enable=True):
        """
        Enable or disable custom picks mode.
        
        Args:
            enable: Whether to enable custom picks mode
        """
        self.custom_picks_mode = enable
        
        if enable and not self.has_picks and self.original_cdp is not None:
            # Initialize custom picks from original picks
            self.custom_cdp = np.copy(self.original_cdp)
            self.custom_twt = np.copy(self.original_twt)
            self.custom_vel = np.copy(self.original_vel)
            self.has_picks = len(self.custom_cdp) > 0
            
            if self.console:
                info_message(self.console, "Custom pick mode enabled with existing picks")
        elif enable:
            if len(self.custom_cdp) == 0:
                self.custom_cdp = np.array([])
                self.custom_twt = np.array([])
                self.custom_vel = np.array([])
            self.has_picks = len(self.custom_cdp) > 0
            if self.console:
                info_message(self.console, "Custom pick mode enabled")
        else:
            if self.console:
                info_message(self.console, "Custom pick mode disabled")
                
    def is_custom_picks_mode_enabled(self):
        """Return whether custom picks mode is enabled."""
        return self.custom_picks_mode
        
    def has_custom_picks(self):
        """Return whether custom picks exist."""
        return self.has_picks
        
    def get_picks(self):
        """Get the current custom picks."""
        return self.custom_cdp, self.custom_twt, self.custom_vel
        
    def handle_click(self, event, delete_mode, sample_to_twt_func):
        """
        Handle mouse click events on the canvas.
        
        Args:
            event: The click event
            delete_mode: Whether delete mode is active
            sample_to_twt_func: Function to convert sample index to TWT
            
        Returns:
            bool: True if the click was handled
        """
        if not self.custom_picks_mode or not event.inaxes or event.button != 1:  # Left click only
            return False
            
        # Get the click position in data coordinates
        cdp = event.xdata
        sample_index = event.ydata
        
        # Convert sample index to TWT
        twt = sample_to_twt_func(sample_index)
        
        if cdp is None or twt is None:
            return False
            
        # Increase tolerance for selection
        cdp_tolerance = 10
        twt_tolerance = 20
        
        # Check if we're in delete mode
        if delete_mode and self.has_picks:
            # Find closest pick to the clicked position
            idx, distance = self.find_nearest_pick(cdp, twt, cdp_tolerance, twt_tolerance)
            
            if idx >= 0:
                # Delete the pick
                deleted_info = self.delete_pick(idx)
                if deleted_info:
                    return True
            elif self.console:
                info_message(self.console, f"No pick found near CDP {cdp:.0f}, TWT {twt:.1f} ms")
            return False
        
        # If not in delete mode, handle adding or editing picks
        # Check if we're editing an existing pick
        idx, distance = self.find_nearest_pick(cdp, twt, cdp_tolerance, twt_tolerance)
        editing_existing = idx >= 0
        
        # Get appropriate default velocity
        if editing_existing:
            default_vel = int(self.custom_vel[idx])
            cdp = self.custom_cdp[idx]
            twt = self.custom_twt[idx]
        else:
            # Try to get velocity from grid if available
            default_vel = None  # Default value
            try:
                if hasattr(self.segy_viewer, 'has_velocity_grid') and self.segy_viewer.has_velocity_grid:
                    # Convert CDP, TWT to grid indices
                    closest_cdp_idx = np.argmin(np.abs(self.segy_viewer.cdp_grid[0, :] - cdp))
                    closest_twt_idx = np.argmin(np.abs(self.segy_viewer.twt_grid[:, 0] - twt))
                    default_vel = int(self.segy_viewer.vel_grid[closest_twt_idx, closest_cdp_idx])
            except:
                pass
                
        # Create velocity entry dialog
        dialog = VelocityEntryDialog(self.segy_viewer, min_vel=1000, max_vel=8000, default_vel=None)
        dialog.set_position_info(cdp, twt)
        
        if dialog.exec() == QDialog.Accepted:
            # Get velocity value
            vel = dialog.get_velocity()
            
            if editing_existing:
                # Update existing pick
                self.update_pick(idx, vel)
            else:
                # Add new pick
                self.add_pick(cdp, twt, vel)
                
            return True
        
        return False
        
    def overlay_velocity_picks(self, ax, vmin=None, vmax=None):
        """
        Overlay velocity picks as colored circles on the SEGY display.
        
        Args:
            ax: The matplotlib axis to plot on
            vmin: Minimum velocity value for colormap
            vmax: Maximum velocity value for colormap
            
        Returns:
            matplotlib.collections.PathCollection: The scatter plot object
        """
        if not self.has_picks:
            return None
            
        try:
            # Convert TWT to sample indices for display
            sample_indices = [self.segy_viewer._twt_to_sample_index(t) for t in self.custom_twt]
            
            # If in custom pick mode, use different marker style
            marker = 'o'
            edge_color = 'black'
            size = 60
            if self.custom_picks_mode:
                marker = '*'
                edge_color = 'white'
                size = 80
            
            scatter = ax.scatter(
                self.custom_cdp,    # X values (CDP/trace)
                sample_indices,     # Y values (converted to sample index)
                c=self.custom_vel,  # Color based on velocity
                cmap='jet',         # Colormap
                vmin=vmin,          # Min velocity for color scaling
                vmax=vmax,          # Max velocity for color scaling
                s=size,             # Size for visibility
                alpha=0.9,          # Opacity
                edgecolors=edge_color,# Border color
                linewidths=0.8,     # Border width
                marker=marker,      # Marker style
                zorder=20           # Highest zorder to ensure visibility on top
            )
            
            # Store mappable for colorbar in the SEGY viewer
            self.segy_viewer.velocity_mappable = scatter
            
            # Add labels for velocity values
            # Skip some labels if there are too many points to avoid clutter
            skip_factor = max(1, int(len(self.custom_cdp) / 25))
            
            for i in range(0, len(self.custom_cdp), skip_factor):
                velocity_value = int(self.custom_vel[i])
                # Create text with white background for better readability
                text = ax.text(
                    self.custom_cdp[i], 
                    sample_indices[i] - 5,  # Position slightly above the point
                    str(velocity_value),
                    fontsize=8, 
                    ha='center',
                    va='bottom',
                    color='black',
                    bbox=dict(
                        facecolor='white',
                        alpha=0.7,
                        edgecolor='none',
                        boxstyle='round,pad=0.2'
                    ),
                    zorder=25  # Above the scatter points
                )
            
            if self.console:
                info_message(self.console, f"Overlaid {len(self.custom_cdp)} velocity picks on SEGY display")
                
            return scatter
            
        except Exception as e:
            if self.console:
                warning_message(self.console, f"Error overlaying velocity picks: {str(e)}")
            return None