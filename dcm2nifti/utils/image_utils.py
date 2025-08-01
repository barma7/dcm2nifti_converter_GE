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


def whiten_image(image):
    """
    Apply quartile-based normalization (whitening) to a medical image.
    This function performs slice-by-slice quartile normalization on a 3D medical image.
    The normalization process includes median centering, percentile-based scaling,
    and clipping of extreme values to reduce noise and improve image contrast.
    Parameters
    ----------
    image : SimpleITK.Image
        Input 3D medical image to be whitened. Expected to have shape 
        (nb_slices, nb_rows, nb_cols).
    Returns
    -------
    SimpleITK.Image
        Whitened image with the same spatial information as the input.
        Pixel values are normalized to approximately [-1, 1] range with
        outliers clipped at 3rd and 97th percentiles.
    Notes
    -----
    The whitening process involves:
    1. Median centering of each slice
    2. Normalization by 75th percentile
    3. Quartile-based scaling to [-1, 1] range
    4. Clipping extreme values (below 3rd percentile, above 97th percentile)
    The function preserves the original image's spatial metadata (origin, spacing, direction).
    """
    # ensure input is a SimpleITK image
    if not isinstance(image, sitk.Image):
        raise TypeError("Input must be a SimpleITK.Image")
    # check if copy can be imported
    try:
        from copy import copy
    except ImportError:
        raise ImportError("copy module is required for this function")

    img_array_orig = sitk.GetArrayFromImage(image)
    # performe quartile normalization
    img_array_whiten = copy(img_array_orig) 
    
    for s in range(img_array_orig.shape[0]):

        # the image is supposed to be (nb_slices, nb_rows, nb_cols)
        img_array_reshape = img_array_orig[s,...].reshape((img_array_orig[s,...].shape[0],img_array_orig[s,...].shape[1], -1)) 
    
        
        img_array_centered = img_array_reshape - np.median(img_array_reshape)
        img_array_normalized = img_array_centered / np.percentile(img_array_centered, 75)
        img_clean = ((img_array_normalized - np.percentile(img_array_normalized,25)) / (np.percentile(img_array_normalized,75) - np.percentile(img_array_normalized,25))) * (2) + -1
    
        img_clean[img_clean < np.percentile(img_clean,3)] = np.percentile(img_clean,3)
        img_clean[img_clean > np.percentile(img_clean,97)] = np.percentile(img_clean,97)

        img_array_whiten[s,...] = img_clean.reshape((-1, img_array_orig[s,...].shape[0],img_array_orig[s,...].shape[1]))

    img_whiten = sitk.GetImageFromArray(img_array_whiten)
    img_whiten.CopyInformation(image)
    return img_whiten


# def register_volumes(target_image: sitk.Image, 
#                     moving_image: sitk.Image, 
#                     temp_folder: Union[str, Path],
#                     rigid: bool = True) -> Tuple[sitk.Image, Any]:
#     """
#     Register two volumes using SimpleITK registration framework.
    
#     Args:
#         target_image: Target (fixed) image
#         moving_image: Moving image to be registered
#         temp_folder: Temporary folder for intermediate files
#         rigid: If True, use rigid registration; otherwise use affine
        
#     Returns:
#         Tuple of (registered_image, transform)
#     """
#     try:
#         # Initialize registration framework
#         registration_method = sitk.ImageRegistrationMethod()
        
#         # Set metric
#         registration_method.SetMetricAsMeanSquares()
        
#         # Set optimizer
#         registration_method.SetOptimizerAsRegularStepGradientDescent(
#             learningRate=1.0,
#             minStep=0.001,
#             numberOfIterations=500,
#             gradientMagnitudeTolerance=1e-6
#         )
        
#         # Set interpolator
#         registration_method.SetInterpolator(sitk.sitkLinear)
        
#         # Set transform
#         if rigid:
#             initial_transform = sitk.CenteredTransformInitializer(
#                 target_image, 
#                 moving_image, 
#                 sitk.Euler3DTransform(), 
#                 sitk.CenteredTransformInitializerFilter.GEOMETRY
#             )
#         else:
#             initial_transform = sitk.CenteredTransformInitializer(
#                 target_image, 
#                 moving_image, 
#                 sitk.AffineTransform(3), 
#                 sitk.CenteredTransformInitializerFilter.GEOMETRY
#             )
        
#         registration_method.SetInitialTransform(initial_transform)
        
#         # Execute registration
#         final_transform = registration_method.Execute(target_image, moving_image)
        
#         # Apply transform
#         registered_image = sitk.Resample(
#             moving_image, 
#             target_image, 
#             final_transform, 
#             sitk.sitkLinear, 
#             0.0, 
#             moving_image.GetPixelID()
#         )
        
#         logger.info(f"Registration completed. Final metric value: {registration_method.GetMetricValue()}")
        
#         return registered_image, final_transform
        
#     except Exception as e:
#         logger.error(f"Registration failed: {e}")
#         # Return original image if registration fails
#         return moving_image, None


# def apply_transform(image: sitk.Image, 
#                    transform: Any, 
#                    temp_folder: Union[str, Path],
#                    reference_image: Optional[sitk.Image] = None) -> sitk.Image:
#     """
#     Apply a transformation to an image.
    
#     Args:
#         image: Input image
#         transform: Transformation to apply
#         temp_folder: Temporary folder for intermediate files
#         reference_image: Optional reference image for resampling
        
#     Returns:
#         Transformed image
#     """
#     try:
#         if transform is None:
#             logger.warning("No transform provided, returning original image")
#             return image
        
#         if reference_image is None:
#             reference_image = image
        
#         # Apply transform
#         transformed_image = sitk.Resample(
#             image, 
#             reference_image, 
#             transform, 
#             sitk.sitkLinear, 
#             0.0, 
#             image.GetPixelID()
#         )
        
#         return transformed_image
        
#     except Exception as e:
#         logger.error(f"Transform application failed: {e}")
#         return image

def register_volumes(target: sitk.Image,
                    moving: sitk.Image,
                    out_path: Union[str, Path],
                    moving_mask: sitk.Image =None, 
                    target_mask: sitk.Image =None, 
                    rigid: bool = True) -> Tuple[sitk.Image, Any]:
    
    """
    Register a moving image to a target image using Elastix registration.
    This function performs image registration using SimpleITK's ElastixImageFilter
    to align a moving image with a target (fixed) image. The registration can be
    either rigid or affine transformation.
    Args:
        target (sitk.Image): The fixed/target image to register to.
        moving (sitk.Image): The moving image to be registered.
        out_path (Union[str, Path]): Output directory path for registration results.
        moving_mask (sitk.Image, optional): Mask for the moving image to constrain
            registration to specific regions. Defaults to None.
        target_mask (sitk.Image, optional): Mask for the target image to constrain
            registration to specific regions. Defaults to None.
        rigid (bool, optional): If True, performs rigid registration; if False,
            performs affine registration. Defaults to True.
    Returns:
        Tuple[sitk.Image, Any]: A tuple containing:
            - sitk.Image: The registered image (moving image transformed to target space)
            - Any: The Elastix filter object containing registration parameters and results,
                    or None if registration failed
    Raises:
        Exception: If registration fails, logs error and returns original moving image
                    with None as the second element of the tuple.
    Note:
        - If masks are provided, they are automatically cast to UInt8 format
        - Mask origins and directions are synchronized with their respective images
        - Registration logging is temporarily disabled during execution but re-enabled
            for output directory logging
        - On failure, the original moving image is returned unchanged
    """
    try:
        selx = sitk.ElastixImageFilter()
        selx.SetMovingImage(moving)
        selx.SetFixedImage(target)
        if moving_mask is not None:
            moving_mask = sitk.Cast(moving_mask, sitk.sitkUInt8)
            target_mask = sitk.Cast(target_mask, sitk.sitkUInt8)
            moving_mask.SetOrigin(moving.GetOrigin())
            moving_mask.SetDirection(moving.GetDirection())
            target_mask.SetOrigin(target.GetOrigin())
            target_mask.SetDirection(target.GetDirection())
            selx.SetMovingMask(moving_mask)
            selx.SetFixedMask(target_mask)

        if rigid:
            #selx.SetParameterMap(selx.ReadParameterFile(flc.ELASTIX_RIGID_PARAMS_FILE))
            parameter_map = sitk.GetDefaultParameterMap("rigid")
            selx.SetParameterMap(parameter_map)
        else:
            #selx.SetParameterMap(selx.ReadParameterFile(flc.ELASTIX_AFFINE_PARAMS_FILE))
            parameter_map = sitk.GetDefaultParameterMap("affine")
            selx.SetParameterMap(parameter_map)
        
        # Set the log level to OFF
        selx.LogToConsoleOff()
        selx.LogToFileOff()

        # Specify the output directory
        selx.SetOutputDirectory(out_path)
        selx.LogToConsoleOn()
        selx.LogToFileOn()
        # Execute registration
        selx.Execute()


        # Extract Image
        registered_image = selx.GetResultImage()
        
        logger.info(f"Registration completed successfully")

        return registered_image, selx         
        
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        # Return original image if registration fails
        return moving, None

def apply_transform(moving: sitk.Image,
                    selx: Any, 
                    out_path: Union[str, Path],
                    mask: bool =False):
    """
    Apply a transformation to a moving image using SimpleITK Transformix.
    This function applies a pre-computed transformation (typically from image registration)
    to transform a moving image into the coordinate space of a reference image.
    Args:
        moving (sitk.Image): The moving image to be transformed.
        selx (Any): The elastix registration object containing transformation parameters.
        out_path (Union[str, Path]): Output directory path for intermediate files.
        mask (bool, optional): If True, applies transformation suitable for binary masks
                                using nearest neighbor interpolation. Defaults to False.
    Returns:
        sitk.Image: The transformed image. Returns the original moving image if 
                    transformation fails.
    Raises:
        Exception: Logs error if transformation fails and returns original image.
    Note:
        - When mask=True, B-spline interpolation order is set to 0 for binary preservation
        - Logging is disabled during transformation to reduce console output
        - Uses Transformix filter from SimpleITK/elastix for the actual transformation
    """

    try:
        # Use Transformix to apply registration to segmentation
        transform_parameter_map = selx.GetTransformParameterMap()
        if mask:
            transform_parameter_map[0]['FinalBSplineInterpolationOrder'] = ['0']
            #transform_parameter_map[0]['ResampleInterpolator'] = ['FinalNearestNeighborInterpolator']

        transformix_filter = sitk.TransformixImageFilter()
        transformix_filter.SetTransformParameterMap(transform_parameter_map)

        transformix_filter.SetMovingImage(moving)
        transformix_filter.SetOutputDirectory(out_path)

        # Set the log level to OFF
        transformix_filter.LogToConsoleOff()
        transformix_filter.LogToFileOff()

        # Execute the transformation
        transformix_filter.Execute()

        # Get the result image
        registered_volume = transformix_filter.GetResultImage()
        
        return registered_volume
    except Exception as e:
        logger.error(f"Transform application failed: {e}")
        return moving

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
