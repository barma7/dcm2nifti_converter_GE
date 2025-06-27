"""
MESE (Multi-Echo Spin Echo) sequence converter.
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
    create_4d_direction_matrix,
    save_nifti_image,
    save_metadata
)


class MESEConverter(SequenceConverter):
    """
    Converter for MESE (Multi-Echo Spin Echo) sequences.
    
    MESE sequences contain multiple echoes with different echo times,
    typically used for T2 mapping and relaxometry studies.
    """
    
    @property
    def sequence_name(self) -> str:
        return "MESE"
    
    @property
    def required_parameters(self) -> List[str]:
        return ["input_folder", "output_folder"]
    
    @property
    def optional_parameters(self) -> List[str]:
        return []
    
    def validate_input(self, input_folder: Union[str, Path], **kwargs) -> bool:
        """
        Validate input for MESE conversion.
        
        Args:
            input_folder: Path to folder containing DICOM files
            **kwargs: Additional parameters (unused for MESE)
            
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
        is_valid, warnings = validate_dicom_series(dicom_files, "mese")
        
        if warnings:
            for warning in warnings:
                self.logger.warning(warning)
        
        # Analyze series
        analysis = analyze_dicom_series(dicom_files)
        
        if analysis['num_echoes'] < 2:
            raise ValueError(f"MESE sequence requires at least 2 echoes, found {analysis['num_echoes']}")
        
        self.logger.info(f"MESE validation successful: {analysis['num_echoes']} echoes, "
                        f"{analysis['num_slices']} slices")
        
        return True
    
    def convert(self, input_folder: Union[str, Path], output_folder: Union[str, Path], **kwargs) -> ConversionResult:
        """
        Convert MESE DICOM series to NIfTI format.
        
        Args:
            input_folder: Path to folder containing DICOM files
            output_folder: Path to folder where outputs will be saved
            **kwargs: Additional parameters (unused for MESE)
            
        Returns:
            ConversionResult containing converted images and metadata
        """
        self._log_conversion_start(input_folder, output_folder)
        
        # Create output directory
        output_path = self._create_output_directory(output_folder)
        
        # Load DICOM files
        series_reader = sitk.ImageSeriesReader()
        dicom_files = series_reader.GetGDCMSeriesFileNames(str(input_folder))
        
        if not dicom_files:
            raise ValueError("No DICOM files found in the input folder.")
        
        # Analyze series
        analysis = analyze_dicom_series(dicom_files)
        slice_thickness = get_slice_thickness(dicom_files[0])
        
        # Separate echoes
        nb_echoes = analysis['num_echoes']
        nb_slices = analysis['slices_per_echo']
        
        echo_images = []
        echo_times = []
        echo_headers = []
        
        self.logger.info(f"Processing {nb_echoes} echoes with {nb_slices} slices each")
        
        # Process each echo
        for e in range(nb_echoes):
            # Get DICOM files for this echo
            echo_dicom_files = dicom_files[e::nb_echoes]
            echo_dicom_files = sort_dicom_files_by_position(echo_dicom_files)
            
            # Load DICOM series for this echo
            series_reader.SetFileNames(echo_dicom_files)
            echo_image = series_reader.Execute()
            echo_image = sitk.Cast(echo_image, sitk.sitkFloat32)
            
            # Get correct spacing
            spacing = echo_image.GetSpacing()
            correct_spacing = (spacing[0], spacing[1], slice_thickness)
            
            # Create image with correct spacing
            #echo_volume = sitk.GetArrayFromImage(echo_image)
            #echo_image_corrected = sitk_image_from_array(echo_volume, correct_spacing, echo_image)
            
            # Extract headers and echo time
            headers = copy_image_headers(echo_dicom_files)
            echo_time = float(headers[0].get('EchoTime', 0))
            
            #echo_images.append(echo_image_corrected)
            echo_images.append(echo_image)
            echo_times.append(echo_time)
            echo_headers.append(headers)
            
            self.logger.info(f"Processed echo {e+1}/{nb_echoes}, TE = {echo_time} ms")
        
        # Create 4D image
        direction_4d = create_4d_direction_matrix(echo_images[0].GetDirection())
        image_4d = sitk.JoinSeries(echo_images)
        image_4d.SetDirection(direction_4d)
        
        # Save outputs
        output_files = []
        
        # Save 4D NIfTI
        nifti_path = output_path / '4d_array.nii.gz'
        save_nifti_image(image_4d, nifti_path)
        output_files.append(str(nifti_path))
        
        # Save echo times
        echo_times_path = output_path / 'echo_times.txt'
        save_metadata(echo_times, echo_times_path)
        output_files.append(str(echo_times_path))
        
        # Save spacing information
        spacing_path = output_path / 'spacing_wo_gap.txt'
        save_metadata([correct_spacing[0], correct_spacing[1], correct_spacing[2]], spacing_path)
        output_files.append(str(spacing_path))
        
        # Create metadata dictionary
        metadata = {
            'sequence_type': 'MESE',
            'num_echoes': nb_echoes,
            'num_slices': nb_slices,
            'echo_times': echo_times,
            'spacing': correct_spacing,
            'slice_thickness': slice_thickness
        }
        
        # Create conversion result
        result = ConversionResult(
            images=[image_4d] + echo_images,
            metadata=metadata,
            output_files=output_files,
            sequence_type='MESE'
        )
        
        self._log_conversion_complete(output_folder)
        
        return result
