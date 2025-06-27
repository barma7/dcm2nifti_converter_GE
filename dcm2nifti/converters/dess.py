"""
DESS (Dual Echo Steady State) sequence converter.
"""

import SimpleITK as sitk
import numpy as np
from pathlib import Path
from typing import List, Union, Tuple, Any
from os.path import join

from ..base import SequenceConverter, ConversionResult
from ..utils import (
    analyze_dicom_series,
    validate_dicom_series,
    sort_dicom_files_by_position,
    copy_image_headers,
    get_slice_thickness,
    sitk_image_from_array,
    save_nifti_image,
    save_metadata
)


class DESSConverter(SequenceConverter):
    """
    Converter for DESS (Dual Echo Steady State) sequences.
    
    DESS sequences contain two echoes with different echo times,
    where echo data is interleaved by slice position.
    """
    
    @property
    def sequence_name(self) -> str:
        return "DESS"
    
    @property
    def required_parameters(self) -> List[str]:
        return ["input_folder", "output_folder"]
    
    @property
    def optional_parameters(self) -> List[str]:
        return ["save_echo_images"]
    
    def validate_input(self, input_folder: Union[str, Path], **kwargs) -> bool:
        """
        Validate input for DESS conversion.
        
        Args:
            input_folder: Path to folder containing DICOM files
            **kwargs: Additional parameters
            
        Returns:
            True if input is valid
            
        Raises:
            ValueError: If validation fails
        """
        # Get DICOM files
        series_reader = sitk.ImageSeriesReader()
        dicom_files = series_reader.GetGDCMSeriesFileNames(str(input_folder))
        
        if not dicom_files:
            raise ValueError("No DICOM files found in the input folder.")
        
        # Validate DICOM series
        is_valid, warnings = validate_dicom_series(dicom_files, "dess")
        
        if warnings:
            for warning in warnings:
                self.logger.warning(warning)
        
        # Analyze series
        analysis = analyze_dicom_series(dicom_files)
        
        if analysis['num_echoes'] != 2:
            raise ValueError(f"DESS sequence requires exactly 2 echoes, found {analysis['num_echoes']}")
        
        self.logger.info(f"DESS validation successful: {analysis['num_echoes']} echoes, "
                        f"{analysis['num_slices']} slices")
        
        return True
    
    def convert(self, input_folder: Union[str, Path], output_folder: Union[str, Path], **kwargs) -> ConversionResult:
        """
        Convert DESS DICOM series to NIfTI format.
        
        Args:
            input_folder: Path to folder containing DICOM files
            output_folder: Path to folder where outputs will be saved
            **kwargs: Additional parameters
                save_echo_images (bool): Whether to save individual echo images
            
        Returns:
            ConversionResult containing converted images and metadata
        """
        self._log_conversion_start(input_folder, output_folder)
        
        # Get parameters
        save_echo_images = kwargs.get('save_echo_images', True)
        
        # Create output directory
        output_path = self._create_output_directory(output_folder)
        
        # Load DICOM files
        series_reader = sitk.ImageSeriesReader()
        dicom_files = series_reader.GetGDCMSeriesFileNames(str(input_folder))
        
        if not dicom_files:
            raise ValueError("No DICOM files found in the input folder.")
        
        dicom_files = sort_dicom_files_by_position(dicom_files)
        
        # Get slice thickness
        slice_thickness = get_slice_thickness(dicom_files[0])
        
        # Load DESS data (echo1 and echo2 are interleaved in slices)
        series_reader.SetFileNames(dicom_files)
        dess_image = series_reader.Execute()
        dess_image = sitk.Cast(dess_image, sitk.sitkFloat32)
        dess_volume = sitk.GetArrayFromImage(dess_image)
        
        # Analyze series
        analysis = analyze_dicom_series(dicom_files)
        nb_echoes = analysis['num_echoes']
        nb_slices = analysis['slices_per_echo']
        
        # Split the volume into first and second echo
        dess_echoes = [dess_volume[0::2, :, :], dess_volume[1::2, :, :]]
        
        # Extract DICOM headers for each echo
        dess_headers = [
            copy_image_headers(dicom_files[0::2]),
            copy_image_headers(dicom_files[1::2]),
        ]
        
        # Create SimpleITK images for each echo
        dess_echo_images = []
        echo_times = []
        spacing = dess_image.GetSpacing()
        correct_spacing = (spacing[0], spacing[1], slice_thickness)
        
        output_files = []
        
        self.logger.info(f"Processing {nb_echoes} echoes with {nb_slices} slices each")
        
        for e in range(nb_echoes):
            # Create image from numpy array with correct spacing
            echo_image = sitk_image_from_array(dess_echoes[e], correct_spacing, dess_image)
            dess_echo_images.append(echo_image)
            
            # Extract echo time
            echo_time = float(dess_headers[e][0].get('EchoTime', 0))
            echo_times.append(echo_time)
            
            # Save individual echo image if requested
            if save_echo_images:
                echo_path = output_path / f"echo_{e+1}.nii.gz"
                save_nifti_image(echo_image, echo_path)
                output_files.append(str(echo_path))
            
            self.logger.info(f"Processed echo {e+1}/{nb_echoes}, TE = {echo_time} ms")
        
        # Save echo times if saving echo images
        if save_echo_images:
            echo_times_path = output_path / 'echo_times.txt'
            save_metadata(echo_times, echo_times_path)
            output_files.append(str(echo_times_path))
        
        # Create metadata dictionary
        metadata = {
            'sequence_type': 'DESS',
            'num_echoes': nb_echoes,
            'num_slices': nb_slices,
            'echo_times': echo_times,
            'spacing': correct_spacing,
            'slice_thickness': slice_thickness
        }
        
        # Create conversion result
        result = ConversionResult(
            images=dess_echo_images,
            metadata=metadata,
            output_files=output_files,
            sequence_type='DESS'
        )
        
        self._log_conversion_complete(output_folder)
        
        return result
