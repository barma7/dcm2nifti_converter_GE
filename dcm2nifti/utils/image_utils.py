"""
Image processing utility functions.
"""

import numpy as np
import SimpleITK as sitk
from typing import Tuple, Union, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def sitk_image_from_array(array: np.ndarray, 
                         spacing: Tuple[float, float, float], 
                         reference_image: Optional[sitk.Image] = None) -> sitk.Image:
    """
    Create a SimpleITK image from a numpy array with proper spacing and orientation.
    
    Args:
        array: Input numpy array
        spacing: Pixel spacing as (x, y, z) tuple
        reference_image: Optional reference image for origin and direction
        
    Returns:
        SimpleITK image
    """
    # Create image from array
    image = sitk.GetImageFromArray(array)
    
    # Set spacing
    image.SetSpacing(spacing)
    
    # Copy origin and direction from reference if provided
    if reference_image is not None:
        image.SetOrigin(reference_image.GetOrigin())
        image.SetDirection(reference_image.GetDirection())
    
    return image


def create_4d_direction_matrix(direction_3d: Tuple[float, ...]) -> Tuple[float, ...]:
    """
    Create a 4D direction matrix from a 3D direction matrix.
    
    Args:
        direction_3d: 3D direction matrix as tuple of 9 floats
        
    Returns:
        4D direction matrix as tuple of 16 floats
    """
    # Convert to numpy array and reshape
    direction_3d_matrix = np.array(direction_3d).reshape(3, 3)
    
    # Create 4x4 identity matrix
    direction_4d_matrix = np.eye(4)
    direction_4d_matrix[:3, :3] = direction_3d_matrix
    
    # Return as flattened tuple
    return tuple(direction_4d_matrix.flatten())


def whiten_image(image: sitk.Image, 
                percentile_low: float = 1.0, 
                percentile_high: float = 99.0) -> sitk.Image:
    """
    Normalize image intensities to improve registration performance.
    
    Args:
        image: Input SimpleITK image
        percentile_low: Lower percentile for normalization
        percentile_high: Upper percentile for normalization
        
    Returns:
        Normalized SimpleITK image
    """
    # Convert to numpy array
    array = sitk.GetArrayFromImage(image)
    
    # Calculate percentiles
    low_val = np.percentile(array, percentile_low)
    high_val = np.percentile(array, percentile_high)
    
    # Normalize
    array_normalized = np.clip((array - low_val) / (high_val - low_val), 0, 1)
    
    # Convert back to SimpleITK image
    normalized_image = sitk.GetImageFromArray(array_normalized)
    normalized_image.CopyInformation(image)
    
    return normalized_image


def register_volumes(target_image: sitk.Image, 
                    moving_image: sitk.Image, 
                    temp_folder: Union[str, Path],
                    rigid: bool = True) -> Tuple[sitk.Image, Any]:
    """
    Register two volumes using SimpleITK registration framework.
    
    Args:
        target_image: Target (fixed) image
        moving_image: Moving image to be registered
        temp_folder: Temporary folder for intermediate files
        rigid: If True, use rigid registration; otherwise use affine
        
    Returns:
        Tuple of (registered_image, transform)
    """
    try:
        # Initialize registration framework
        registration_method = sitk.ImageRegistrationMethod()
        
        # Set metric
        registration_method.SetMetricAsMeanSquares()
        
        # Set optimizer
        registration_method.SetOptimizerAsRegularStepGradientDescent(
            learningRate=1.0,
            minStep=0.001,
            numberOfIterations=500,
            gradientMagnitudeTolerance=1e-6
        )
        
        # Set interpolator
        registration_method.SetInterpolator(sitk.sitkLinear)
        
        # Set transform
        if rigid:
            initial_transform = sitk.CenteredTransformInitializer(
                target_image, 
                moving_image, 
                sitk.Euler3DTransform(), 
                sitk.CenteredTransformInitializerFilter.GEOMETRY
            )
        else:
            initial_transform = sitk.CenteredTransformInitializer(
                target_image, 
                moving_image, 
                sitk.AffineTransform(3), 
                sitk.CenteredTransformInitializerFilter.GEOMETRY
            )
        
        registration_method.SetInitialTransform(initial_transform)
        
        # Execute registration
        final_transform = registration_method.Execute(target_image, moving_image)
        
        # Apply transform
        registered_image = sitk.Resample(
            moving_image, 
            target_image, 
            final_transform, 
            sitk.sitkLinear, 
            0.0, 
            moving_image.GetPixelID()
        )
        
        logger.info(f"Registration completed. Final metric value: {registration_method.GetMetricValue()}")
        
        return registered_image, final_transform
        
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        # Return original image if registration fails
        return moving_image, None


def apply_transform(image: sitk.Image, 
                   transform: Any, 
                   temp_folder: Union[str, Path],
                   reference_image: Optional[sitk.Image] = None) -> sitk.Image:
    """
    Apply a transformation to an image.
    
    Args:
        image: Input image
        transform: Transformation to apply
        temp_folder: Temporary folder for intermediate files
        reference_image: Optional reference image for resampling
        
    Returns:
        Transformed image
    """
    try:
        if transform is None:
            logger.warning("No transform provided, returning original image")
            return image
        
        if reference_image is None:
            reference_image = image
        
        # Apply transform
        transformed_image = sitk.Resample(
            image, 
            reference_image, 
            transform, 
            sitk.sitkLinear, 
            0.0, 
            image.GetPixelID()
        )
        
        return transformed_image
        
    except Exception as e:
        logger.error(f"Transform application failed: {e}")
        return image


def calculate_porosity_index(echo_1_array: np.ndarray, 
                           echo_2_array: np.ndarray,
                           clip_min: float = 0.0,
                           clip_max: float = 100.0) -> np.ndarray:
    """
    Calculate porosity index from two echo images.
    
    Args:
        echo_1_array: First echo image array
        echo_2_array: Second echo image array
        clip_min: Minimum value for clipping
        clip_max: Maximum value for clipping
        
    Returns:
        Porosity index array
    """
    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        pi = (echo_2_array / echo_1_array) * 100
    
    # Replace NaN and inf values with 0
    pi = np.nan_to_num(pi, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Clip values
    pi = np.clip(pi, clip_min, clip_max)
    
    return pi


def calculate_saturation_recovery_index(ute_array: np.ndarray, 
                                      ir_ute_array: np.ndarray,
                                      clip_min: float = 0.0,
                                      clip_max: float = 1000.0) -> np.ndarray:
    """
    Calculate saturation recovery index from UTE and IR-UTE images.
    
    Args:
        ute_array: UTE image array
        ir_ute_array: IR-UTE image array
        clip_min: Minimum value for clipping
        clip_max: Maximum value for clipping
        
    Returns:
        Saturation recovery index array
    """
    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        sr_index = ute_array / ir_ute_array
    
    # Replace NaN and inf values with 0
    sr_index = np.nan_to_num(sr_index, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Clip values
    sr_index = np.clip(sr_index, clip_min, clip_max)
    
    return sr_index


def calculate_complex_magnitude(real_array: np.ndarray, 
                              imag_array: np.ndarray) -> np.ndarray:
    """
    Calculate magnitude from real and imaginary arrays.
    
    Args:
        real_array: Real component array
        imag_array: Imaginary component array
        
    Returns:
        Magnitude array
    """
    return np.sqrt(real_array**2 + imag_array**2)
