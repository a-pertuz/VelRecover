"""Edit tab for VelRecover application."""

import os
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSplitter, QGroupBox, QComboBox, QSpinBox,
    QDoubleSpinBox, QFormLayout, QFileDialog, QInputDialog,
    QMessageBox
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from ..utils.visualization_utils import SeismicDisplayManager
from ..utils.console_utils import (
    section_header, success_message, error_message, 
    warning_message, info_message, progress_message,
    summary_statistics
)

"""
The methods used in this file include:
- __init__
- _setup_ui
- update_with_data
- _load_velocity_data
- _apply_time_shift
- _set_edit_mode
- _on_canvas_click
- _add_new_pick
- _edit_pick
- _delete_pick
- _find_closest_pick
- _save_edits
- _continue_without_edits
- _save_state_to_history
- _undo
- _redo
- _update_button_states
- reset
"""

class SimpleNavigationToolbar(NavigationToolbar):
    """Simplified navigation toolbar with only Home, Pan and Zoom tools."""
    
    # Define which tools to keep
    toolitems = [t for t in NavigationToolbar.toolitems if t[0] in ('Home', 'Pan', 'Zoom', 'Save')]
    
    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)

class EditTab(QWidget):
    """Tab for editing and cleaning velocity data."""
    
    # Signal when editing is complete
    editingCompleted = Signal(object)
    # Signal to proceed to next step
    proceedRequested = Signal()
    
    def __init__(self, console=None, work_dir=None, parent=None):
        super().__init__(parent)
        self.setObjectName("edit_tab")
        self.console = console
        self.work_dir = work_dir
        
        # Initialize state variables
        self.segy_file_path = None
        self.velocity_file_path = None
        self.vel_traces = None
        self.vel_twts = None
        self.vel_values = None
        self.segy_metadata = None
        
        # Create history for undo/redo
        self.history = []
        self.history_index = -1
        self.max_history = 20  # Maximum number of history states
        
        # Flag for edit mode
        self.edit_mode = None  # Can be None, 'new', 'edit', 'delete'
        
        # Create matplotlib figure for SEGY display
        self.figure = Figure(figsize=(8, 6), constrained_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Create seismic display manager
        self.display_manager = SeismicDisplayManager(self.ax, self.console)
        
        # Connect to canvas click events
        self.canvas.mpl_connect('button_press_event', self._on_canvas_click)
        
        # Set up the user interface
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Tab header
        header = QLabel("Edit Velocity Data")
        header.setObjectName("tab_header")
        layout.addWidget(header)
        

        # Instruction text
        instruction = QLabel("Use the tools below to edit, delete or create new velocity picks.")
        instruction.setObjectName("description_label")
        instruction.setWordWrap(True)
        layout.addWidget(instruction)
        
        # Create top section with tool groupboxes
        tools_section = QHBoxLayout()
        
        # Time shift groupbox
        time_shift_group = QGroupBox("Apply Time Shift")
        time_shift_layout = QHBoxLayout(time_shift_group)
        
        # Time shift spinbox for milliseconds
        self.time_shift_spinbox = QDoubleSpinBox()
        self.time_shift_spinbox.setRange(-1000, 1000)
        self.time_shift_spinbox.setValue(0)
        self.time_shift_spinbox.setSuffix(" ms")
        self.time_shift_spinbox.setSingleStep(10)
        time_shift_layout.addWidget(self.time_shift_spinbox)
        
        # Apply time shift button
        self.apply_shift_button = QPushButton("Apply Shift")
        self.apply_shift_button.clicked.connect(self._apply_time_shift)
        self.apply_shift_button.setEnabled(False)
        time_shift_layout.addWidget(self.apply_shift_button)
        
        tools_section.addWidget(time_shift_group)
        
        # Custom picks groupbox
        custom_picks_group = QGroupBox("Custom Velocity Picks")
        custom_picks_layout = QHBoxLayout(custom_picks_group)
        
        # New pick button
        self.new_pick_button = QPushButton("New")
        self.new_pick_button.clicked.connect(lambda: self._set_edit_mode('new'))
        self.new_pick_button.setEnabled(False)
        custom_picks_layout.addWidget(self.new_pick_button)
        
        # Edit pick button
        self.edit_pick_button = QPushButton("Edit")
        self.edit_pick_button.clicked.connect(lambda: self._set_edit_mode('edit'))
        self.edit_pick_button.setEnabled(False)
        custom_picks_layout.addWidget(self.edit_pick_button)
        
        # Delete pick button
        self.delete_pick_button = QPushButton("Delete")
        self.delete_pick_button.clicked.connect(lambda: self._set_edit_mode('delete'))
        self.delete_pick_button.setEnabled(False)
        custom_picks_layout.addWidget(self.delete_pick_button)
        
        tools_section.addWidget(custom_picks_group)
        
        # Undo/Redo buttons
        history_group = QGroupBox("History")
        history_layout = QHBoxLayout(history_group)
        
        self.undo_button = QPushButton("Undo")
        self.undo_button.clicked.connect(self._undo)
        self.undo_button.setEnabled(False)
        history_layout.addWidget(self.undo_button)
        
        self.redo_button = QPushButton("Redo")
        self.redo_button.clicked.connect(self._redo)
        self.redo_button.setEnabled(False)
        history_layout.addWidget(self.redo_button)
        
        tools_section.addWidget(history_group)
        
        layout.addLayout(tools_section)
        
        # SEGY Display section
        display_group = QGroupBox("SEGY Display with Velocity Picks")
        display_layout = QVBoxLayout(display_group)
        
        # Instruction label for edit mode
        self.edit_mode_label = QLabel("Click on a button above to start editing")
        self.edit_mode_label.setAlignment(Qt.AlignCenter)
        self.edit_mode_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        display_layout.addWidget(self.edit_mode_label)
        
        # Add the matplotlib canvas
        display_layout.addWidget(self.canvas)
        
        # Add navigation toolbar
        toolbar = SimpleNavigationToolbar(self.canvas, self)
        display_layout.addWidget(toolbar)
        
        layout.addWidget(display_group, 1)  # Give it a stretch factor of 1
        
        # Actions
        action_layout = QHBoxLayout()
        
        # Save button
        self.save_button = QPushButton("Save Edits")
        self.save_button.setObjectName("save_edits_button")
        self.save_button.clicked.connect(self._save_edits)
        self.save_button.setEnabled(False)
        action_layout.addWidget(self.save_button)
        
        # Continue without edits button
        self.continue_button = QPushButton("Continue Without Edits")
        self.continue_button.setObjectName("continue_without_edits_button")
        self.continue_button.clicked.connect(self._continue_without_edits)
        self.continue_button.setEnabled(False)
        action_layout.addWidget(self.continue_button)
        
        action_layout.addStretch()

        # Next button
        self.next_button = QPushButton("Next")
        self.next_button.setObjectName("primary_button")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.proceedRequested.emit)
        action_layout.addWidget(self.next_button)
        
        layout.addLayout(action_layout)
    
    def update_with_data(self, velocity_data):
        """
        Update the tab with the loaded data.
        
        Parameters:
        -----------
        velocity_data : dict
            Dictionary containing the velocity data and SEGY file paths
        """
        if not velocity_data:
            if self.console:
                warning_message(self.console, "No velocity data to edit")
            return
        
        try:
            # Extract data from the velocity_data dictionary
            self.segy_file_path = velocity_data.get("segy_file_path")
            self.velocity_file_path = velocity_data.get("velocity_file_path")
            self.segy_metadata = velocity_data.get("segy_metadata")
            
            # Extract velocity data arrays if available
            self.vel_traces = velocity_data.get("vel_traces")
            self.vel_twts = velocity_data.get("vel_twts")
            self.vel_values = velocity_data.get("vel_values")
            
            # Load the SEGY data
            if self.segy_file_path:
                if self.console:
                    info_message(self.console, f"Loading SEGY data from: {self.segy_file_path}")
                self.segy_metadata = self.display_manager.load_segy(self.segy_file_path)
            
            # Set velocity data in display manager if available
            if self.vel_traces is not None and self.vel_twts is not None and self.vel_values is not None:
                self.display_manager.load_velocity_picks(self.vel_traces, self.vel_twts, self.vel_values)
            # Otherwise, load from file if available
            elif self.velocity_file_path:
                if self.console:
                    info_message(self.console, f"Loading velocity data from: {self.velocity_file_path}")
                self._load_velocity_data(self.velocity_file_path)
            
            # Display data
            self.display_manager.display()
            self.canvas.draw()
            
            # Save initial state for undo/redo
            self._save_state_to_history()
            
            # Enable editing tools
            self._update_button_states()
            
            # Enable continue button
            self.continue_button.setEnabled(True)
            
            if self.console:
                section_header(self.console, "Edit Mode")
                success_message(self.console, "Data loaded successfully. Ready for editing.")
        
        except Exception as e:
            if self.console:
                error_message(self.console, f"Error updating edit tab: {str(e)}")
                import traceback
                error_message(self.console, traceback.format_exc())
            # Reset state
            self.segy_file_path = None
            self.velocity_file_path = None
    
    def _load_velocity_data(self, file_path):
        """Load velocity data from file."""
        try:
            # Try to auto-detect delimiter from common formats
            with open(file_path, 'r') as f:
                # Read first line to detect delimiter and check if it's a header
                first_line = f.readline().strip()
                has_header = False
                
                # Check if first line contains non-numeric characters (likely a header)
                if any(not c.isdigit() and c not in '.-+\t, ;' for c in first_line):
                    has_header = True
                
                if '\t' in first_line:
                    delimiter = '\t'  # Tab-delimited
                elif ',' in first_line:
                    delimiter = ','   # Comma-delimited
                elif ';' in first_line:
                    delimiter = ';'   # Semicolon-delimited
                else:
                    delimiter = None  # Let numpy try to figure it out (space-delimited)
            
            # Load the data using numpy, skip header row if detected
            data = np.loadtxt(file_path, delimiter=delimiter, skiprows=1 if has_header else 0)
            
            # Check if the file has three columns
            if data.shape[1] < 3:
                raise ValueError("Velocity file must have at least three columns: trace, twt, velocity")
            
            # Extract the columns
            self.vel_traces = data[:, 0]  # First column: trace number
            self.vel_twts = data[:, 1]    # Second column: two-way time
            self.vel_values = data[:, 2]  # Third column: velocity value
            
            # Update the display manager
            self.display_manager.load_velocity_picks(self.vel_traces, self.vel_twts, self.vel_values)
            
            if self.console:
                success_message(self.console, f"Velocity data loaded: {len(self.vel_traces)} picks")
            
        except Exception as e:
            if self.console:
                error_message(self.console, f"Error loading velocity file: {str(e)}")
            raise
    
    def _apply_time_shift(self):
        """Apply time shift to all velocity picks."""
        if self.vel_twts is None or len(self.vel_twts) == 0:
            return
        
        # Get the time shift value in milliseconds
        time_shift = self.time_shift_spinbox.value()
        
        if time_shift == 0:
            return
        
        # Save current state for undo
        self._save_state_to_history()
        
        # Apply the time shift
        self.vel_twts = self.vel_twts + time_shift
        
        # Update the display
        self.display_manager.load_velocity_picks(self.vel_traces, self.vel_twts, self.vel_values)
        self.display_manager.display()
        self.canvas.draw()
        
        # Enable save button
        self.save_button.setEnabled(True)
        
        if self.console:
            info_message(self.console, f"Applied time shift of {time_shift} ms")
        
    def _set_edit_mode(self, mode):
        """Set the edit mode and update UI accordingly."""
        # If clicking the same mode button again, turn off edit mode
        if self.edit_mode == mode:
            self.edit_mode = None
            self.edit_mode_label.setText("Click on a button above to start editing")
            self._update_button_states()
            return
        
        self.edit_mode = mode
        
        # Update UI based on mode
        if mode == 'new':
            self.edit_mode_label.setText("Click on the SEGY display to add a new velocity pick")
            self.new_pick_button.setStyleSheet("background-color: #e6f2ff; font-weight: bold;")
            self.edit_pick_button.setStyleSheet("")
            self.delete_pick_button.setStyleSheet("")
        elif mode == 'edit':
            self.edit_mode_label.setText("Click on an existing pick to edit its velocity value")
            self.new_pick_button.setStyleSheet("")
            self.edit_pick_button.setStyleSheet("background-color: #e6f2ff; font-weight: bold;")
            self.delete_pick_button.setStyleSheet("")
        elif mode == 'delete':
            self.edit_mode_label.setText("Click on an existing pick to delete it")
            self.new_pick_button.setStyleSheet("")
            self.edit_pick_button.setStyleSheet("")
            self.delete_pick_button.setStyleSheet("background-color: #ffe6e6; font-weight: bold;")
        else:
            self.edit_mode_label.setText("Click on a button above to start editing")
            self.new_pick_button.setStyleSheet("")
            self.edit_pick_button.setStyleSheet("")
            self.delete_pick_button.setStyleSheet("")
    
    def _on_canvas_click(self, event):
        """Handle clicks on the canvas based on the current edit mode."""
        if event.inaxes != self.ax or self.edit_mode is None:
            return
        
        # Get the click coordinates
        trace = int(round(event.xdata))
        
        # For time, we need to convert back from sample index to TWT
        # Formula: twt = (sample_index * dt_ms) + delay
        if self.segy_metadata and 'dt_ms' in self.segy_metadata and 'delay' in self.segy_metadata:
            dt_ms = self.segy_metadata['dt_ms']
            delay = self.segy_metadata['delay']
            twt = (event.ydata * dt_ms) + delay
        else:
            # If we don't have metadata, just use the y-value directly
            twt = event.ydata
        
        if self.edit_mode == 'new':
            self._add_new_pick(trace, twt)
        elif self.edit_mode == 'edit':
            self._edit_pick(trace, twt)
        elif self.edit_mode == 'delete':
            self._delete_pick(trace, twt)
    
    def _add_new_pick(self, trace, twt):
        """Add a new velocity pick at the specified location."""
        # Ask user for the velocity value
        velocity, ok = QInputDialog.getDouble(
            self, "Enter Velocity", "Velocity (m/s):", 
            2000.0, 500.0, 10000.0, 1
        )
        
        if not ok:
            return
        
        # Save current state for undo
        self._save_state_to_history()
        
        # Add the new pick
        if self.vel_traces is None:
            self.vel_traces = np.array([trace])
            self.vel_twts = np.array([twt])
            self.vel_values = np.array([velocity])
        else:
            self.vel_traces = np.append(self.vel_traces, trace)
            self.vel_twts = np.append(self.vel_twts, twt)
            self.vel_values = np.append(self.vel_values, velocity)
        
        # Update the display
        self.display_manager.load_velocity_picks(self.vel_traces, self.vel_twts, self.vel_values)
        self.display_manager.display()
        self.canvas.draw()
        
        # Enable save button
        self.save_button.setEnabled(True)
        
        if self.console:
            info_message(self.console, f"Added new pick at trace={trace}, twt={twt:.2f}, velocity={velocity}")
    
    def _edit_pick(self, trace, twt):
        """Edit the velocity of an existing pick near the click location."""
        if self.vel_traces is None or len(self.vel_traces) == 0:
            return
        
        # Find the closest pick
        idx, distance = self._find_closest_pick(trace, twt)
        
        # If too far, ignore
        max_distance = 20  # Maximum distance in pixels
        if distance > max_distance:
            if self.console:
                warning_message(self.console, f"No pick found near trace={trace}, twt={twt:.2f}")
            return
        
        # Get current velocity
        current_velocity = self.vel_values[idx]
        
        # Ask user for the new velocity value
        velocity, ok = QInputDialog.getDouble(
            self, "Edit Velocity", "New velocity (m/s):", 
            current_velocity, 500.0, 10000.0, 1
        )
        
        if not ok or velocity == current_velocity:
            return
        
        # Save current state for undo
        self._save_state_to_history()
        
        # Update the velocity
        self.vel_values[idx] = velocity
        
        # Update the display
        self.display_manager.load_velocity_picks(self.vel_traces, self.vel_twts, self.vel_values)
        self.display_manager.display()
        self.canvas.draw()
        
        # Enable save button
        self.save_button.setEnabled(True)
        
        if self.console:
            info_message(self.console, f"Updated pick at trace={self.vel_traces[idx]}, twt={self.vel_twts[idx]:.2f}, velocity={velocity}")
    
    def _delete_pick(self, trace, twt):
        """Delete an existing pick near the click location."""
        if self.vel_traces is None or len(self.vel_traces) == 0:
            return
        
        # Find the closest pick
        idx, distance = self._find_closest_pick(trace, twt)
        
        # If too far, ignore
        max_distance = 20  # Maximum distance in pixels
        if distance > max_distance:
            if self.console:
                warning_message(self.console, f"No pick found near trace={trace}, twt={twt:.2f}")
            return
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Delete velocity pick at trace={self.vel_traces[idx]}, twt={self.vel_twts[idx]:.2f}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Save current state for undo
        self._save_state_to_history()
        
        # Delete the pick
        self.vel_traces = np.delete(self.vel_traces, idx)
        self.vel_twts = np.delete(self.vel_twts, idx)
        self.vel_values = np.delete(self.vel_values, idx)
        
        # Update the display
        self.display_manager.load_velocity_picks(self.vel_traces, self.vel_twts, self.vel_values)
        self.display_manager.display()
        self.canvas.draw()
        
        # Enable save button
        self.save_button.setEnabled(True)
        
        if self.console:
            info_message(self.console, f"Deleted pick at trace={trace}, twt={twt:.2f}")
            
    def _find_closest_pick(self, trace, twt):
        """
        Find the closest velocity pick to the given trace and TWT.
        """
        if self.vel_traces is None or len(self.vel_traces) == 0:
            return None, float('inf')

        # Calculate the Euclidean distance to all picks
        distances = np.sqrt((self.vel_traces - trace) ** 2 + (self.vel_twts - twt) ** 2)

        # Find the index of the closest pick
        closest_index = np.argmin(distances)
        closest_distance = distances[closest_index]

        return closest_index, closest_distance

    def _save_edits(self):
        """Save the edited velocity picks to a file."""
        if self.vel_traces is None or len(self.vel_traces) == 0:
            QMessageBox.warning(self, "No Data", "No velocity data to save")
            return
        
        # Ask for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Velocity File", 
            os.path.join(self.work_dir, "VELS", "CUSTOM"), 
            "DAT Files (*.dat);;All Files (*.*)"
        )

        if not file_path:
            return
        
        try:
            # Save the velocity data
            data = np.column_stack((self.vel_traces, self.vel_twts, self.vel_values))
            np.savetxt(file_path, data, fmt='%.6f', delimiter='\t', 
                      header='TRACE\tTWT\tVELOCITY', comments='')
            
            # Update the velocity file path
            self.velocity_file_path = file_path
            
            # Enable the next button
            self.next_button.setEnabled(True)
            
            # Disable the save button
            self.save_button.setEnabled(False)
            
            if self.console:
                section_header(self.console, "Velocity Data Saved")
                success_message(self.console, f"Saved to: {file_path}")
                info_message(self.console, f"Saved {len(self.vel_traces)} velocity picks")
                info_message(self.console, "Ready to proceed to interpolation")
            
            # Emit the editing completed signal
            edited_data = {
                "segy_file_path": self.segy_file_path,
                "velocity_file_path": self.velocity_file_path,
                "vel_traces": self.vel_traces,
                "vel_twts": self.vel_twts,
                "vel_values": self.vel_values
            }
            self.editingCompleted.emit(edited_data)
            
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Error saving velocity data: {str(e)}")
            if self.console:
                error_message(self.console, f"Error saving velocity data: {str(e)}")
    
    def _continue_without_edits(self):
        """Continue to the next tab without making any edits."""
        # Enable the next button
        self.next_button.setEnabled(True)
        
        if self.console:
            info_message(self.console, "Continuing without edits")
        
        # Emit the editing completed signal with the original data
        edited_data = {
            "segy_file_path": self.segy_file_path,
            "velocity_file_path": self.velocity_file_path,
            "vel_traces": self.vel_traces,
            "vel_twts": self.vel_twts,
            "vel_values": self.vel_values
        }
        self.editingCompleted.emit(edited_data)
        
    def _save_state_to_history(self):
        """Save the current state to the history for undo/redo."""
        if self.vel_traces is None:
            return
            
        # Create a copy of the current state
        state = {
            "vel_traces": self.vel_traces.copy(),
            "vel_twts": self.vel_twts.copy(),
            "vel_values": self.vel_values.copy()
        }
        
        # If we're in the middle of the history, discard future states
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        # Add the new state to history
        self.history.append(state)
        self.history_index = len(self.history) - 1
        
        # If history is too long, remove oldest entries
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            self.history_index = len(self.history) - 1
        
        # Update button states
        self._update_button_states()
    
    def _undo(self):
        """Undo the last edit."""
        if self.history_index <= 0:
            return
        
        # Move back in history
        self.history_index -= 1
        
        # Restore the state
        state = self.history[self.history_index]
        self.vel_traces = state["vel_traces"].copy()
        self.vel_twts = state["vel_twts"].copy()
        self.vel_values = state["vel_values"].copy()
        
        # Update the display
        self.display_manager.load_velocity_picks(self.vel_traces, self.vel_twts, self.vel_values)
        self.display_manager.display()
        self.canvas.draw()
        
        # Enable save button
        self.save_button.setEnabled(True)
        
        # Update button states
        self._update_button_states()
        
        if self.console:
            info_message(self.console, "Undo: Reverted to previous state")
    
    def _redo(self):
        """Redo the last undone edit."""
        if self.history_index >= len(self.history) - 1:
            return
        
        # Move forward in history
        self.history_index += 1
        
        # Restore the state
        state = self.history[self.history_index]
        self.vel_traces = state["vel_traces"].copy()
        self.vel_twts = state["vel_twts"].copy()
        self.vel_values = state["vel_values"].copy()
        
        # Update the display
        self.display_manager.load_velocity_picks(self.vel_traces, self.vel_twts, self.vel_values)
        self.display_manager.display()
        self.canvas.draw()
        
        # Enable save button
        self.save_button.setEnabled(True)
        
        # Update button states
        self._update_button_states()
        
        if self.console:
            info_message(self.console, "Redo: Restored next state")
    
    def _update_button_states(self):
        """Update the enabled state of buttons based on current state."""
        # Undo/Redo buttons
        self.undo_button.setEnabled(self.history_index > 0)
        self.redo_button.setEnabled(self.history_index < len(self.history) - 1)
        
        # Editing buttons
        has_data = self.vel_traces is not None and len(self.vel_traces) > 0
        self.apply_shift_button.setEnabled(has_data)
        self.new_pick_button.setEnabled(self.segy_file_path is not None)
        self.edit_pick_button.setEnabled(has_data)
        self.delete_pick_button.setEnabled(has_data)
        self.save_button.setEnabled(has_data)
    
    def reset(self):
        """Reset the tab to its initial state."""
        self.segy_file_path = None
        self.velocity_file_path = None
        self.vel_traces = None
        self.vel_twts = None
        self.vel_values = None
        self.segy_metadata = None
        
        # Reset history
        self.history = []
        self.history_index = -1
        
        # Reset edit mode
        self.edit_mode = None
        self.edit_mode_label.setText("Click on a button above to start editing")
        
        # Reset button states
        self._update_button_states()
        self.next_button.setEnabled(False)
        self.continue_button.setEnabled(False)
        self.new_pick_button.setStyleSheet("")
        self.edit_pick_button.setStyleSheet("")
        self.delete_pick_button.setStyleSheet("")
        
        # Clear the display
        self.display_manager.clear()
        self.canvas.draw()