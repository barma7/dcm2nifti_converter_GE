"""
DICOM utility functions.
"""

import pydicom
import numpy as np
from typing import List, Dict, Any, Union, Tuple
from pathlib import Path
import SimpleITK as sitk
import logging

logger = logging.getLogger(__name__)


def copy_image_headers(dicom_files: List[Union[str, Path]]) -> List[Dict[str, Any]]:
    """
    Extract DICOM headers from a list of DICOM files.
    
    Args:
        dicom_files: List of DICOM file paths
        
    Returns:
        List of dictionaries containing DICOM header information
    """
    headers = []
    for dicom_file in dicom_files:
        try:
            ds = pydicom.dcmread(dicom_file)
            header = {}
            
            # Extract commonly used DICOM tags
            header['EchoTime'] = getattr(ds, 'EchoTime', None)
            header['RepetitionTime'] = getattr(ds, 'RepetitionTime', None)
            header['InversionTime'] = getattr(ds, 'InversionTime', None)
            header['FlipAngle'] = getattr(ds, 'FlipAngle', None)
            header['SliceThickness'] = getattr(ds, 'SliceThickness', None)
            header['SpacingBetweenSlices'] = getattr(ds, 'SpacingBetweenSlices', None)
            header['ImageOrientationPatient'] = getattr(ds, 'ImageOrientationPatient', None)
            header['ImagePositionPatient'] = getattr(ds, 'ImagePositionPatient', None)
            header['PixelSpacing'] = getattr(ds, 'PixelSpacing', None)
            header['InstanceNumber'] = getattr(ds, 'InstanceNumber', None)
            header['EchoNumbers'] = getattr(ds, 'EchoNumbers', None)
            header['AcquisitionNumber'] = getattr(ds, 'AcquisitionNumber', None)
            header['SeriesNumber'] = getattr(ds, 'SeriesNumber', None)
            header['ImagingFrequency'] = getattr(ds, 'ImagingFrequency', None)
            header['MRAcquisitionType'] = getattr(ds, 'MRAcquisitionType', None)
            
            headers.append(header)
            
        except Exception as e:
            logger.error(f"Error reading DICOM header from {dicom_file}: {e}")
            continue
            
    return headers


def get_slice_thickness(dicom_file: Union[str, Path]) -> float:
    """
    Extract slice thickness from DICOM file.
    
    Args:
        dicom_file: Path to DICOM file
        
    Returns:
        Slice thickness in mm
    """
    try:
        ds = pydicom.dcmread(dicom_file)
        
        # Try SliceThickness first
        if hasattr(ds, 'SliceThickness') and ds.SliceThickness is not None:
            return float(ds.SliceThickness)
        
        # Fall back to SpacingBetweenSlices
        if hasattr(ds, 'SpacingBetweenSlices') and ds.SpacingBetweenSlices is not None:
            return float(ds.SpacingBetweenSlices)
        
        # If neither is available, try to calculate from ImagePositionPatient
        logger.warning(f"No slice thickness found in {dicom_file}, using default value of 1.0 mm")
        return 1.0
        
    except Exception as e:
        logger.error(f"Error extracting slice thickness from {dicom_file}: {e}")
        return 1.0


def sort_dicom_files_by_position(dicom_files: List[Union[str, Path]]) -> List[Union[str, Path]]:
    """
    Sort DICOM files by slice position.
    
    Args:
        dicom_files: List of DICOM file paths
        
    Returns:
        Sorted list of DICOM file paths
    """
    if not dicom_files:
        return dicom_files
    
    # Extract headers for sorting
    headers = copy_image_headers(dicom_files)
    
    slice_projections = []
    for idx, header in enumerate(headers):
        if (header.get('ImageOrientationPatient') is not None and 
            header.get('ImagePositionPatient') is not None):
            
            IOP = np.array(header['ImageOrientationPatient'])
            IPP = np.array(header['ImagePositionPatient'])
            normal = np.cross(IOP[:3], IOP[3:])
            projection = np.dot(IPP, normal)
            
            slice_projections.append({
                'd': projection, 
                'dicom_file': dicom_files[idx], 
                'header': header
            })
        else:
            # If orientation/position info is missing, keep original order
            slice_projections.append({
                'd': idx, 
                'dicom_file': dicom_files[idx], 
                'header': header
            })
    
    # Sort by projection distance
    sorted_projections = sorted(slice_projections, key=lambda x: x['d'])
    
    # Return sorted file paths
    sorted_files = [proj['dicom_file'] for proj in sorted_projections]
    
    return sorted_files


def analyze_dicom_series(dicom_files: List[Union[str, Path]]) -> Dict[str, Any]:
    """
    Analyze DICOM series to determine sequence characteristics.
    
    Args:
        dicom_files: List of DICOM file paths
        
    Returns:
        Dictionary containing series analysis results
    """
    if not dicom_files:
        return {}
    
    headers = copy_image_headers(dicom_files)
    
    # Extract unique values for key parameters
    echo_times = [h.get('EchoTime') for h in headers if h.get('EchoTime') is not None]
    echo_numbers = [h.get('EchoNumbers') for h in headers if h.get('EchoNumbers') is not None]
    instance_numbers = [h.get('InstanceNumber') for h in headers if h.get('InstanceNumber') is not None]
    acquisition_numbers = [h.get('AcquisitionNumber') for h in headers if h.get('AcquisitionNumber') is not None]
    
    if len(set(echo_times)) > 1:
        # the sequence is a multi-echo sequence
        logger.info("Detected multi-echo sequence")
    
    num_echoes = len(set(echo_times)) if echo_times else 1
    num_slices = len(set(instance_numbers)) // num_echoes if num_echoes > 0 else len(instance_numbers)  

    analysis = {
        'num_files': len(dicom_files),
        'unique_echo_times': sorted(list(set(echo_times))) if echo_times else [],
        'unique_echo_numbers': sorted(list(set(echo_numbers))) if echo_numbers else [],
        'unique_instance_numbers': sorted(list(set(instance_numbers))) if instance_numbers else [],
        'unique_acquisition_numbers': sorted(list(set(acquisition_numbers))) if acquisition_numbers else [],
        'num_echoes': num_echoes,
        'num_slices': num_slices,
        'slices_per_echo': num_slices,
        'mr_acquisition_type': headers[0].get('MRAcquisitionType') if headers else None,
        'imaging_frequency': headers[0].get('ImagingFrequency') if headers else None,
    }
            
    return analysis


def validate_dicom_series(dicom_files: List[Union[str, Path]], 
                         expected_sequence_type: str = None) -> Tuple[bool, List[str]]:
    """
    Validate DICOM series for consistency and completeness.
    
    Args:
        dicom_files: List of DICOM file paths
        expected_sequence_type: Expected sequence type (optional)
        
    Returns:
        Tuple of (is_valid, list_of_warnings)
    """
    warnings = []
    
    if not dicom_files:
        return False, ["No DICOM files provided"]
    
    try:
        headers = copy_image_headers(dicom_files)
        
        # Check if all files have consistent series information
        series_numbers = [h.get('SeriesNumber') for h in headers if h.get('SeriesNumber') is not None]
        if len(set(series_numbers)) > 1:
            warnings.append(f"Multiple series numbers found: {set(series_numbers)}")
        
        # Check for missing critical tags
        for i, header in enumerate(headers):
            if header.get('ImageOrientationPatient') is None:
                warnings.append(f"Missing ImageOrientationPatient in file {i}")
            if header.get('ImagePositionPatient') is None:
                warnings.append(f"Missing ImagePositionPatient in file {i}")
            if header.get('PixelSpacing') is None:
                warnings.append(f"Missing PixelSpacing in file {i}")
        
        # Check for sequence-specific requirements
        analysis = analyze_dicom_series(dicom_files)
        
        if expected_sequence_type:
            if expected_sequence_type.lower() in ['mese', 'megre'] and analysis['num_echoes'] < 2:
                warnings.append(f"Expected multi-echo sequence but found only {analysis['num_echoes']} echo(s)")
            elif expected_sequence_type.lower() == 'dess' and analysis['num_echoes'] != 2:
                warnings.append(f"DESS sequence should have 2 echoes but found {analysis['num_echoes']}")
        
        is_valid = len(warnings) == 0
        return is_valid, warnings
        
    except Exception as e:
        return False, [f"Error validating DICOM series: {e}"]
