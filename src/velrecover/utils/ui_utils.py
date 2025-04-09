"""UI utility functions for VelRecover."""

import time
from datetime import timedelta
from PySide6.QtWidgets import QMessageBox

from .console_utils import info_message, warning_message, error_message, success_message

def create_progress_callback(console, status_bar, start_time):
    """
    Create a progress callback function that includes time estimation.
    
    Args:
        console: Console widget for logging messages
        status_bar: Status bar widget for updating progress
        start_time: Start time for time estimation
        
    Returns:
        function: A progress callback function for long operations
    """
    last_update_time = [start_time]  # Use a list for mutable reference
    update_interval = 0.5  # seconds between progress updates
    
    def progress_callback(percent, message=""):
        current_time = time.time()
        
        # Only update status bar at reasonable intervals to avoid UI slowdown
        if current_time - last_update_time[0] >= update_interval or percent >= 100:
            elapsed_time = current_time - start_time
            
            # Only show time estimate if we're at least 5% through the process
            estimated_message = ""
            if percent > 5 and percent < 100:
                # Estimate total time based on progress so far
                estimated_total = elapsed_time * 100 / percent
                estimated_remaining = estimated_total - elapsed_time
                
                # Format as MM:SS
                time_remaining = str(timedelta(seconds=int(estimated_remaining))).split('.')[0]
                estimated_message = f" (Est. remaining: {time_remaining})"
            
            update_message = f"{message}{estimated_message}" if message else f"Processing...{estimated_message}"
            status_bar.update(percent, update_message)
            last_update_time[0] = current_time
            
    return progress_callback

def show_error_dialog(parent, title, error_message, error_type=None):
    """
    Show an error dialog with appropriate advice based on error type.
    
    Args:
        parent: Parent widget for the dialog
        title: Dialog title
        error_message: The error message to display
        error_type: Optional error type for specialized advice
    """
    error_msg = error_message.lower() if error_message else ""
    
    if error_type == "memory" or "memory" in error_msg:
        QMessageBox.critical(
            parent, title, 
            f"{error_message}\n\n"
            "The system ran out of memory. Try:\n"
            "1. Close other applications to free memory\n"
            "2. Use a smaller dataset or lower resolution\n"
            "3. Try a different interpolation method"
        )
    elif error_type == "numerical" or any(term in error_msg for term in ["singular", "linalg", "overflow", "underflow"]):
        QMessageBox.critical(
            parent, title, 
            f"{error_message}\n\n"
            "A numerical error occurred. Try:\n"
            "1. Check your data for anomalous values\n"
            "2. Try a different interpolation method\n"
            "3. Ensure your data points aren't too closely spaced"
        )
    elif error_type == "file" or any(term in error_msg for term in ["file", "permission", "access", "open", "read", "write"]):
        QMessageBox.critical(
            parent, title, 
            f"{error_message}\n\n"
            "A file operation error occurred. Check:\n"
            "1. If you have appropriate permissions\n"
            "2. If the file is being used by another application\n"
            "3. If you have enough disk space"
        )
    else:
        QMessageBox.critical(
            parent, title, 
            f"{error_message}\n\n"
            "Try using a different approach or check your data."
        )

def track_operation_time(console, operation_name, callback_fn):
    """
    Track the time taken by an operation and log it.
    
    Args:
        console: Console widget for logging
        operation_name: Name of the operation being performed
        callback_fn: The function to time
        
    Returns:
        The result of the callback function
    """
    info_message(console, f"Starting {operation_name}...")
    start_time = time.time()
    
    try:
        result = callback_fn()
        
        # Calculate and display elapsed time
        elapsed_time = time.time() - start_time
        time_str = str(timedelta(seconds=int(elapsed_time))).split('.')[0]
        
        success_message(console, f"{operation_name} completed in {time_str}")
        return result
    except Exception as e:
        # Calculate and display elapsed time on error
        elapsed_time = time.time() - start_time
        time_str = str(timedelta(seconds=int(elapsed_time))).split('.')[0]
        
        error_message(console, f"{operation_name} failed after {time_str}: {str(e)}")
        raise  # Re-raise the exception for the caller to handle

def confirm_action(parent, title, message, default_yes=False):
    """
    Show a confirmation dialog and return user's choice.
    
    Args:
        parent: Parent widget for the dialog
        title: Dialog title
        message: The message to display
        default_yes: Whether the "Yes" button should be the default
        
    Returns:
        bool: True if the user confirmed, False otherwise
    """
    default_button = QMessageBox.Yes if default_yes else QMessageBox.No
    
    reply = QMessageBox.question(
        parent, title, message,
        QMessageBox.Yes | QMessageBox.No,
        default_button
    )
    
    return reply == QMessageBox.Yes