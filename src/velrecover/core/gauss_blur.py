"""Gaussian blur utility for smoothing velocity grids."""

import numpy as np
import cv2

def apply_gaussian_blur(vel_grid, blur_value):
    """    Apply Gaussian blur to velocity grid."""
    
    # Ensure blur value is odd and at least 3
    kernel_size = max(3, blur_value * 10 + 1)
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    # Apply Gaussian blur
    blurred_grid = cv2.GaussianBlur(vel_grid.astype(np.float32), 
                                    (kernel_size, kernel_size), 0)
    
    return blurred_grid
