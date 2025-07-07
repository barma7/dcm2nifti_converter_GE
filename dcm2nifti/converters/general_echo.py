"""
General multi-echo DICOM converter that groups images by echo time.
"""

import SimpleITK as sitk
import numpy as np
from pathlib import Path
from typing import List, Union, Dict, Any, Optional
import pydicom
from collections import defaultdict

from ..base import SequenceConverter, ConversionResult
from ..utils import (
    analyze_dicom_series,
    validate_dicom_series,
    sort_dicom_files_by_position,
    copy_image_headers,
    get_slice_thickness,
    sitk_image_from_array,
    create_4d_direction_matrix,
    save_nifti_image,
    save_metadata,
    save_structured_metadata
)


class GeneralSeriesConverter(SequenceConverter):
    """
    General converter for DICOM sequences with single or multiple echo times.
    
    This converter automatically groups DICOM images by echo time and creates
    3D NIfTI volumes for single echo sequences or 4D NIfTI volumes for multi-echo
    sequences with proper echo time metadata. It processes all files in the input 
    folder regardless of series number, grouping them purely by echo time.
    """
    
    def __init__(self):
        super().__init__()
    
    @property
    def sequence_name(self) -> str:
        return "GENERAL_SERIES"
    
    @property
    def required_parameters(self) -> List[str]:
        return ["input_folder", "output_folder"]
    
    @property
    def optional_parameters(self) -> List[str]:
        return ["sort_by_position"]
    
    def validate_input(self, input_folder: Union[str, Path], **kwargs) -> bool:
        """
        Validate input parameters for general echo conversion.
        
        Args:
            input_folder: Path to the folder containing DICOM files
            **kwargs: Additional parameters
            
        Returns:
            bool: True if input is valid, False otherwise
        """
        try:
            input_path = Path(input_folder)
            if not input_path.exists():
                self.logger.error(f"Input folder does not exist: {input_folder}")
                return False
            
            # Check if DICOM files exist
            dicom_files = list(input_path.glob("*.dcm")) + list(input_path.glob("*.IMA"))
            if not dicom_files:
                # Try recursive search
                dicom_files = list(input_path.rglob("*.dcm")) + list(input_path.rglob("*.IMA"))
            
            if not dicom_files:
                self.logger.error(f"No DICOM files found in: {input_folder}")
                return False
            
            # Validate sort_by_position parameter
            sort_by_position = kwargs.get('sort_by_position', True)
            if not isinstance(sort_by_position, bool):
                self.logger.error("'sort_by_position' parameter must be a boolean")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating general echo input: {e}")
            return False
    
    def convert(self, input_folder: Union[str, Path], output_folder: Union[str, Path], 
                sort_by_position: bool = True, **kwargs) -> ConversionResult:
        """
        Convert DICOM series to NIfTI format, grouping by echo time.
        
        Handles both single echo sequences (creates 3D NIfTI) and multi-echo 
        sequences (creates individual 3D files plus 4D volume).
        
        Args:
            input_folder: Path to the folder containing DICOM files
            output_folder: Path to the output folder
            sort_by_position: Whether to sort files by spatial position
            **kwargs: Additional parameters
            
        Returns:
            ConversionResult: Result of the conversion process
        """
        try:
            # Validate inputs
            if not self.validate_input(input_folder, sort_by_position=sort_by_position, **kwargs):
                raise ValueError("Input validation failed")
            
            self.logger.info(f"Converting general sequence")
            self.logger.info(f"Sort by position: {sort_by_position}")
            
            output_path = Path(output_folder)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Find all DICOM files
            input_path = Path(input_folder)
            dicom_files = []
            
            # Search for DICOM files
            for pattern in ["*.dcm", "*.IMA"]:
                dicom_files.extend(list(input_path.glob(pattern)))
                dicom_files.extend(list(input_path.rglob(pattern)))
            
            # Remove duplicates and convert to strings
            dicom_files = list(set(str(f) for f in dicom_files))
            
            if not dicom_files:
                raise ValueError("No DICOM files found in the input folder")
            
            self.logger.info(f"Found {len(dicom_files)} DICOM files")
            
            # Group files by echo time
            echo_dict = self._group_files_by_echo(dicom_files)
            
            if not echo_dict:
                raise ValueError("No echo groups found")
            
            self.logger.info(f"Found {len(echo_dict)} unique echo times")
            
            # Process the echo group
            result = self._process_echo_group(
                echo_dict, output_path, sort_by_position
            )
            
            output_files = result['output_files']
            images = result['images']
            
            # Save overall metadata
            metadata = {
                'sequence_type': 'GENERAL_SERIES',
                'sort_by_position': sort_by_position,
                'echo_data': result['metadata']
            }
            
            # Save conversion metadata
            metadata_path = output_path / 'conversion_metadata.json'
            save_structured_metadata(metadata, str(metadata_path))
            output_files.append(str(metadata_path))
            
            self.logger.info(f"General sequence conversion completed successfully")
            self.logger.info(f"Processed {len(echo_dict)} echo times with {len(output_files)} total files")
            
            return ConversionResult(
                images=images,
                metadata=metadata,
                output_files=output_files,
                sequence_type='GENERAL_SERIES'
            )
            
        except Exception as e:
            self.logger.error(f"Error in general echo conversion: {e}")
            raise ValueError(f"Conversion failed: {str(e)}")
    
    def _group_files_by_echo(self, dicom_files: List[str]) -> Dict[float, List[str]]:
        """
        Group DICOM files by echo time.
        
        Args:
            dicom_files: List of DICOM file paths
            
        Returns:
            Dictionary mapping echo times to file lists
        """
        echo_dict = defaultdict(list)
        
        for file_path in dicom_files:
            try:
                dcm = pydicom.dcmread(file_path)
                
                # Get echo time
                echo_time = float(dcm.EchoTime) if hasattr(dcm, 'EchoTime') else 0.0
                echo_dict[echo_time].append(file_path)
                
            except Exception as e:
                self.logger.warning(f"Could not process file {file_path}: {e}")
                continue
        
        return dict(echo_dict)
    
    def _process_echo_group(self, echo_dict: Dict[float, List[str]], 
                           output_path: Path, 
                           sort_by_position: bool) -> Dict[str, Any]:
        """
        Process echo files to create 4D NIfTI volume.
        
        Args:
            echo_dict: Dictionary mapping echo times to file lists
            output_path: Output directory path
            sort_by_position: Whether to sort files by spatial position
            
        Returns:
            Dictionary with processing results
        """
        # Sort echo times
        echo_times = sorted(echo_dict.keys())
        
        self.logger.info(f"Processing {len(echo_times)} echoes: {echo_times}")
        
        # Create group output directory
        group_output = output_path
        group_output.mkdir(exist_ok=True)
        
        echo_images = []
        echo_volumes = []
        processed_echo_times = []
        
        # Process each echo
        for i, echo_time in enumerate(echo_times):
            file_list = echo_dict[echo_time]
            
            if sort_by_position:
                file_list = sort_dicom_files_by_position(file_list)
            
            # Load DICOM series for this echo
            series_reader = sitk.ImageSeriesReader()
            series_reader.SetFileNames(file_list)
            
            try:
                echo_image = series_reader.Execute()
                echo_image = sitk.Cast(echo_image, sitk.sitkFloat32)
                
                # Get slice thickness from first file
                slice_thickness = get_slice_thickness(file_list[0])
                
                # Correct spacing if needed
                spacing = echo_image.GetSpacing()
                if len(spacing) >= 3:
                    correct_spacing = (spacing[0], spacing[1], slice_thickness)
                    echo_volume = sitk.GetArrayFromImage(echo_image)
                    echo_image = sitk_image_from_array(echo_volume, correct_spacing, echo_image)
                
                echo_images.append(echo_image)
                echo_volumes.append(sitk.GetArrayFromImage(echo_image))
                processed_echo_times.append(echo_time)
                
                # Save individual echo
                echo_filename = f"echo_{i+1:01d}.nii.gz"
                echo_path = group_output / echo_filename
                save_nifti_image(echo_image, str(echo_path))
                
                self.logger.info(f"Processed echo {echo_time:.2f}ms with {len(file_list)} slices")
                
            except Exception as e:
                self.logger.warning(f"Failed to process echo {echo_time:.2f}ms: {e}")
                continue
        
        if not echo_images:
            raise ValueError(f"No valid echoes found")
        
        # Create 4D image if multiple echoes
        output_files = []
        images = []
        
        if len(echo_images) > 1:
            # Create 4D direction matrix
            direction_4d = create_4d_direction_matrix(echo_images[0])
            
            # Join echo images into 4D volume
            image_4d = sitk.JoinSeries(echo_images)
            image_4d.SetDirection(direction_4d)
            
            # Save 4D image
            image_4d_path = group_output / '4d_multiecho.nii.gz'
            save_nifti_image(image_4d, str(image_4d_path))
            output_files.append(str(image_4d_path))
            images.append(image_4d)
            
            self.logger.info(f"Created 4D volume with {len(echo_images)} echoes")
        else:
            # Single echo case - no 4D volume needed
            self.logger.info(f"Single echo found - no 4D volume created")
        
        # Add individual echo files to output list
        for i, echo_time in enumerate(processed_echo_times):
            echo_filename = f"echo_{i+1:01d}.nii.gz"
            echo_path = group_output / echo_filename
            output_files.append(str(echo_path))
        
        images.extend(echo_images)
        
        # Save echo times metadata
        echo_times_path = group_output / 'echo_times.txt'
        save_metadata(processed_echo_times, str(echo_times_path))
        output_files.append(str(echo_times_path))
        
        # Get metadata from first file
        first_file = echo_dict[processed_echo_times[0]][0]
        first_dcm = pydicom.dcmread(first_file)
        
        # Save repetition time metadata
        flip_angle = float(getattr(first_dcm, 'FlipAngle', 0))
        flip_angle_path = group_output / 'flip_angle.txt'
        save_metadata([flip_angle], str(flip_angle_path))
        rep_time = float(getattr(first_dcm, 'RepetitionTime', 0))
        rep_time_path = group_output / 'repetition_time.txt'
        save_metadata([rep_time], str(rep_time_path))
        output_files.append(str(rep_time_path))
        output_files.append(str(flip_angle_path))
        
        metadata = {
            'num_echoes': len(processed_echo_times),
            'echo_times': processed_echo_times,
            'echo_time_range': [min(processed_echo_times), max(processed_echo_times)],
            'repetition_time': rep_time,
            'slice_thickness': get_slice_thickness(first_file),
            'center_frequency': float(getattr(first_dcm, 'ImagingFrequency', 0)),
            'files_per_echo': {f"{et:.2f}": len(echo_dict[et]) for et in processed_echo_times},
            'image_size': list(echo_images[0].GetSize()) if echo_images else [],
            'spacing': list(echo_images[0].GetSpacing()) if echo_images else []
        }
        
        return {
            'output_files': output_files,
            'images': images,
            'metadata': metadata
        }
    
    def get_supported_parameters(self) -> dict:
        """
        Get information about supported parameters for this converter.
        
        Returns:
            dict: Dictionary containing parameter information
        """
        return {
            'sequence_name': self.sequence_name,
            'required_parameters': self.required_parameters,
            'optional_parameters': self.optional_parameters,
            'description': 'Converts DICOM series to NIfTI format, grouping by echo time (supports single or multi-echo)',
            'parameter_details': {
                'sort_by_position': 'Whether to sort files by spatial position (default: True)'
            },
            'outputs': [
                'Individual echo files: echo_X.nii.gz',
                '4D multi-echo volume: 4d_multiecho.nii.gz (if multiple echoes)',
                'Echo times metadata: echo_times.txt',
                'Repetition time metadata: repetition_time.txt',
                'Conversion metadata: conversion_metadata.json'
            ],
            'use_cases': [
                'Single or multi-echo sequences without specific converters',
                'Custom echo time analysis',
                'Research sequences with variable echo times',
                'Quality control and data exploration'
            ]
        }
