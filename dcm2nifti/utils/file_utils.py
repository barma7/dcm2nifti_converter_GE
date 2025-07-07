"""
File I/O utility functions.
"""

import numpy as np
import SimpleITK as sitk
import nibabel as nib
from typing import Union, List, Any, Dict
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)


def save_nifti_image(image: sitk.Image, output_path: Union[str, Path]) -> None:
    """
    Save a SimpleITK image to a NIfTI file.
    
    Args:
        image: SimpleITK image to save
        output_path: Output file path
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sitk.WriteImage(image, str(output_path))
        logger.info(f"Saved NIfTI image to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save NIfTI image to {output_path}: {e}")
        raise


def save_metadata(data: Union[List, np.ndarray], 
                 output_path: Union[str, Path],
                 fmt: str = '%f') -> None:
    """
    Save numerical metadata to a text file.
    
    Args:
        data: Data to save (list or array)
        output_path: Output file path
        fmt: Format string for saving numbers
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        np.savetxt(output_path, data, fmt=fmt)
        logger.info(f"Saved metadata to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save metadata to {output_path}: {e}")
        raise


def load_metadata(file_path: Union[str, Path]) -> np.ndarray:
    """
    Load numerical metadata from a text file.
    
    Args:
        file_path: Path to metadata file
        
    Returns:
        Loaded data as numpy array
    """
    try:
        return np.loadtxt(file_path)
    except Exception as e:
        logger.error(f"Failed to load metadata from {file_path}: {e}")
        raise


def save_conversion_summary(results: Dict[str, Any], 
                          output_folder: Union[str, Path]) -> None:
    """
    Save a summary of the conversion process.
    
    Args:
        results: Dictionary containing conversion results
        output_folder: Output folder path
    """
    try:
        output_path = Path(output_folder) / "conversion_summary.txt"
        
        with open(output_path, 'w') as f:
            f.write("DICOM to NIfTI Conversion Summary\n")
            f.write("=" * 40 + "\n\n")
            
            for key, value in results.items():
                f.write(f"{key}: {value}\n")
        
        logger.info(f"Saved conversion summary to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to save conversion summary: {e}")


def create_nibabel_image(array: np.ndarray, 
                        reference_image: sitk.Image) -> nib.Nifti1Image:
    """
    Create a NiBabel image from a numpy array using SimpleITK image as reference.
    
    Args:
        array: Input numpy array
        reference_image: Reference SimpleITK image for affine transformation
        
    Returns:
        NiBabel Nifti1Image
    """
    try:
        # Get affine transformation from SimpleITK image
        spacing = reference_image.GetSpacing()
        origin = reference_image.GetOrigin()
        direction = np.array(reference_image.GetDirection()).reshape(3, 3)
        
        # Create affine matrix
        affine = np.eye(4)
        affine[:3, :3] = direction * spacing
        affine[:3, 3] = origin
        
        # Create NiBabel image
        nib_image = nib.Nifti1Image(array, affine)
        
        return nib_image
        
    except Exception as e:
        logger.error(f"Failed to create NiBabel image: {e}")
        raise


def validate_output_files(output_files: List[Union[str, Path]]) -> bool:
    """
    Validate that output files were created successfully.
    
    Args:
        output_files: List of output file paths
        
    Returns:
        True if all files exist and are valid, False otherwise
    """
    all_valid = True
    
    for file_path in output_files:
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"Output file does not exist: {file_path}")
            all_valid = False
            continue
        
        if file_path.stat().st_size == 0:
            logger.error(f"Output file is empty: {file_path}")
            all_valid = False
            continue
        
        # Additional validation for specific file types
        if file_path.suffix.lower() in ['.nii', '.nii.gz']:
            try:
                # Try to load the NIfTI file to verify it's valid
                sitk.ReadImage(str(file_path))
                logger.debug(f"Validated NIfTI file: {file_path}")
            except Exception as e:
                logger.error(f"Invalid NIfTI file {file_path}: {e}")
                all_valid = False
    
    return all_valid


def save_structured_metadata(data: Dict[str, Any], 
                            output_path: Union[str, Path]) -> None:
    """
    Save structured metadata (dictionaries, lists) to a JSON file.
    
    Args:
        data: Dictionary or other structured data to save
        output_path: Output file path
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert any non-serializable objects to strings
        def serialize_data(obj):
            if hasattr(obj, '__dict__'):
                return str(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif hasattr(obj, 'tolist'):
                return obj.tolist()
            else:
                return obj
        
        # Create a serializable copy of the data
        serializable_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                serializable_data[key] = {k: serialize_data(v) for k, v in value.items()}
            elif isinstance(value, list):
                serializable_data[key] = [serialize_data(v) for v in value]
            else:
                serializable_data[key] = serialize_data(value)
        
        with open(output_path, 'w') as f:
            json.dump(serializable_data, f, indent=2)
        
        logger.info(f"Saved structured metadata to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save structured metadata to {output_path}: {e}")
        raise
