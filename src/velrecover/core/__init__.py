"""Interpolation package for velocity analysis."""

# Import all public functions from submodules
from .base import (

    create_grid,
    run_interpolation, 
    calculate_r2
)

from .linear_models import (
    linear_model, 
    custom_linear_model,
    best_linear_fit
)

from .logarithmic_models import (
    logarithmic_model,
    custom_logarithmic_model,
    best_logarithmic_fit
)

from .rbf_models import (
    rbf_interpolate, 
    interpolate_velocity_data_rbf
)

from .two_step import (
    two_step_model
)

from .gauss_blur import (
    apply_gaussian_blur
)

__all__ = [
    # Base functions
    'load_segy_data', 'load_velocity_data', 'create_grid',
    'run_interpolation', 'calculate_r2',
    
    # Linear models
    'linear_model', 'custom_linear_model', 'best_linear_fit',
    
    # Logarithmic models
    'logarithmic_model', 'custom_logarithmic_model', 'best_logarithmic_fit',
    
    # RBF models
    'rbf_interpolate', 'interpolate_velocity_data_rbf',
    
    # Two-step interpolation
    'two_step_interpolation',
    
    # Gaussian blur
    'apply_gaussian_blur'
]
