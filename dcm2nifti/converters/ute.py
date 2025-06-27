"""
UTE (Ultra-short Echo Time) sequence converter.
"""

import SimpleITK as sitk
import numpy as np
from pathlib import Path
from typing import List, Union, Tuple, Any
from os.path import join
from copy import copy
import pdb  # For debugging

from ..base import SequenceConverter, ConversionResult
from ..utils import (
    analyze_dicom_series,
    validate_dicom_series,
    sort_dicom_files_by_position,
    copy_image_headers,
    get_slice_thickness,
    sitk_image_from_array,
    create_4d_direction_matrix,
    whiten_image,
    register_volumes,
    apply_transform,
    calculate_porosity_index,
    save_nifti_image,
    save_metadata
)


class UTEConverter(SequenceConverter):
    """
    Converter for UTE (Ultra-short Echo Time) sequences.
    
    UTE sequences can have multiple series that need to be combined,
    and optionally co-registered for motion correction.
    """
    
    @property
    def sequence_name(self) -> str:
        return "UTE"
    
    @property
    def required_parameters(self) -> List[str]:
        return ["input_folder", "output_folder", "series_numbers"]
    
    @property
    def optional_parameters(self) -> List[str]:
        return ["coregister"]
    
    def validate_input(self, input_folder: Union[str, Path], **kwargs) -> bool:
        """
        Validate input for UTE conversion.
        
        Args:
            input_folder: Path to folder containing DICOM series folders
            **kwargs: Additional parameters
                series_numbers (List[str]): List of series numbers to combine
            
        Returns:
            True if input is valid
            
        Raises:
            ValueError: If validation fails
        """
        series_numbers = kwargs.get('series_numbers')
        if not series_numbers:
            raise ValueError("UTE conversion requires series_numbers parameter")
        
        input_path = Path(input_folder)
        
        # Check that all series folders exist
        for series_number in series_numbers:
            series_folder = input_path / series_number
            if not series_folder.exists():
                raise ValueError(f"Series folder not found: {series_folder}")
            
            # Check for DICOM files in each series
            series_reader = sitk.ImageSeriesReader()
            dicom_files = series_reader.GetGDCMSeriesFileNames(str(series_folder))
            
            if not dicom_files:
                raise ValueError(f"No DICOM files found in series folder: {series_folder}")
        
        self.logger.info(f"UTE validation successful: {len(series_numbers)} series to process")
        
        return True
    
    def convert(self, input_folder: Union[str, Path], output_folder: Union[str, Path], **kwargs) -> ConversionResult:
        """
        Convert UTE DICOM series to NIfTI format.
        
        Args:
            input_folder: Path to folder containing DICOM series folders
            output_folder: Path to folder where outputs will be saved
            **kwargs: Additional parameters
                series_numbers (List[str]): List of series numbers to combine
                coregister (bool): Whether to perform co-registration
            
        Returns:
            ConversionResult containing converted images and metadata
        """
        print(f"DEBUG: Starting UTE conversion")
        print(f"DEBUG: Input folder: {input_folder}")
        print(f"DEBUG: Output folder: {output_folder}")
        print(f"DEBUG: Kwargs: {kwargs}")
        
        self._log_conversion_start(input_folder, output_folder)
        
        # Get parameters
        series_numbers = kwargs.get('series_numbers', [])
        coregister = kwargs.get('coregister', False)
        
        if not series_numbers:
            raise ValueError("UTE conversion requires series_numbers parameter")
        
        # Create output directory
        output_path = self._create_output_directory(output_folder)
        
        if coregister:
            return self._convert_with_registration(input_folder, output_path, series_numbers)
        else:
            return self._convert_without_registration(input_folder, output_path, series_numbers)
    
    def _convert_without_registration(self, input_folder: Union[str, Path], 
                                    output_path: Path, 
                                    series_numbers: List[str]) -> ConversionResult:
        """Convert UTE series without registration."""
        input_path = Path(input_folder)
        
        echo_images = []
        echo_times = []
        center_freqs = []
        
        self.logger.info(f"Processing {len(series_numbers)} series without registration")
        
        # Process each series
        for series_idx, series_number in enumerate(series_numbers):
            series_folder = input_path / series_number
            
            # Load DICOM files
            series_reader = sitk.ImageSeriesReader()
            dicom_files = series_reader.GetGDCMSeriesFileNames(str(series_folder))
            
            # Get metadata
            slice_thickness = get_slice_thickness(dicom_files[0])
            analysis = analyze_dicom_series(dicom_files)
            
            # Extract center frequency
            headers = copy_image_headers([dicom_files[0]])
            center_freq = [float(headers[0].get('ImagingFrequency', 0))]  # MHz
            
            nb_echoes = analysis['num_echoes']
            nb_slices = analysis['slices_per_echo']
            
            self.logger.info(f"Series {series_number}: {nb_echoes} echoes, {nb_slices} slices")
            
            # Process each echo in this series
            slicer_idx = 0
            for e in range(nb_echoes):
                # Get DICOM files for this echo
                echo_dicom_files = dicom_files[slicer_idx:slicer_idx + nb_slices]
                echo_dicom_files = sort_dicom_files_by_position(echo_dicom_files)
                
                # Load DICOM series
                series_reader.SetFileNames(echo_dicom_files)
                echo_image = series_reader.Execute()
                echo_image = sitk.Cast(echo_image, sitk.sitkFloat32)
                
                # Get correct spacing
                spacing = echo_image.GetSpacing()
                correct_spacing = (spacing[0], spacing[1], slice_thickness)
                
                # Create image with correct spacing
                echo_volume = sitk.GetArrayFromImage(echo_image)
                echo_image_corrected = sitk_image_from_array(echo_volume, correct_spacing, echo_image)
                
                # Extract echo time
                echo_headers = copy_image_headers(echo_dicom_files)
                echo_time = float(echo_headers[1].get('EchoTime', 0))
                
                echo_images.append(echo_image_corrected)
                echo_times.append(echo_time)
                center_freqs.append(center_freq)
                
                slicer_idx += nb_slices
        
        # Sort images by echo time
        sorted_indices = np.argsort(echo_times)
        echo_images_sorted = [echo_images[i] for i in sorted_indices]
        echo_times_sorted = [echo_times[i] for i in sorted_indices]
        
        # Calculate Porosity Index if multiple echoes available
        output_files = []
        if len(echo_times_sorted) > 1:
            self._calculate_and_save_porosity_index(echo_images_sorted, echo_times_sorted, output_path, output_files)
        
        # Create 4D image
        direction_4d = create_4d_direction_matrix(echo_images_sorted[0].GetDirection())
        image_4d = sitk.JoinSeries(echo_images_sorted)
        image_4d.SetDirection(direction_4d)
        
        # Save outputs
        nifti_path = output_path / '4d_array.nii.gz'
        save_nifti_image(image_4d, nifti_path)
        output_files.append(str(nifti_path))
        
        echo_times_path = output_path / 'echo_times.txt'
        save_metadata(echo_times_sorted, echo_times_path)
        output_files.append(str(echo_times_path))
        
        center_freq_path = output_path / 'center_freq.txt'
        save_metadata(center_freqs[0], center_freq_path)
        output_files.append(str(center_freq_path))
        
        # Create metadata
        metadata = {
            'sequence_type': 'UTE',
            'num_echoes': len(echo_times_sorted),
            'num_series': len(series_numbers),
            'echo_times': echo_times_sorted,
            'center_frequency': center_freqs[0],
            'coregistered': False
        }
        
        result = ConversionResult(
            images=[image_4d] + echo_images_sorted,
            metadata=metadata,
            output_files=output_files,
            sequence_type='UTE'
        )
        
        self._log_conversion_complete(output_path)
        return result
    
    def _convert_with_registration(self, input_folder: Union[str, Path], 
                                 output_path: Path, 
                                 series_numbers: List[str]) -> ConversionResult:
        """Convert UTE series with co-registration."""
        input_path = Path(input_folder)
        
        # Process each series separately first
        series_echo_images = []
        series_echo_times = []
        center_freqs = []
        
        self.logger.info(f"Processing {len(series_numbers)} series with registration")
        
        for series_idx, series_number in enumerate(series_numbers):
            series_folder = input_path / series_number
            
            # Load DICOM files
            series_reader = sitk.ImageSeriesReader()
            dicom_files = series_reader.GetGDCMSeriesFileNames(str(series_folder))
            
            # Get metadata
            slice_thickness = get_slice_thickness(dicom_files[0])
            analysis = analyze_dicom_series(dicom_files)
            
            # Extract center frequency
            headers = copy_image_headers([dicom_files[0]])
            center_freq = [float(headers[0].get('ImagingFrequency', 0))]
            center_freqs.append(center_freq)
            
            nb_echoes = analysis['num_echoes']
            nb_slices = analysis['slices_per_echo']
            
            series_images = []
            series_times = []
            
            # Process each echo in this series
            slicer_idx = 0
            for e in range(nb_echoes):
                # Get DICOM files for this echo
                echo_dicom_files = dicom_files[slicer_idx:slicer_idx + nb_slices]
                echo_dicom_files = sort_dicom_files_by_position(echo_dicom_files)
                
                # Load DICOM series
                series_reader.SetFileNames(echo_dicom_files)
                echo_image = series_reader.Execute()
                echo_image = sitk.Cast(echo_image, sitk.sitkFloat32)
                
                # Get correct spacing
                spacing = echo_image.GetSpacing()
                correct_spacing = (spacing[0], spacing[1], slice_thickness)
                
                # Create image with correct spacing
                echo_volume = sitk.GetArrayFromImage(echo_image)
                echo_image_corrected = sitk_image_from_array(echo_volume, correct_spacing, echo_image)
                
                # Extract echo time
                echo_headers = copy_image_headers(echo_dicom_files)
                echo_time = float(echo_headers[0].get('EchoTime', 0))
                
                series_images.append(echo_image_corrected)
                series_times.append(echo_time)
                
                slicer_idx += nb_slices
            
            series_echo_images.append(series_images)
            series_echo_times.append(series_times)
        
        # Perform co-registration
        target_series_idx = len(series_numbers) // 2  # Use middle series as target
        target_echo_idx = 0
        target_image = whiten_image(series_echo_images[target_series_idx][target_echo_idx])
        
        # Create temporary folder for registration
        temp_folder = output_path / 'elastix_tmp'
        temp_folder.mkdir(parents=True, exist_ok=True)
        
        registered_series_images = []
        
        for i, series_images in enumerate(series_echo_images):
            if i == target_series_idx:
                registered_series_images.append(series_images)  # No registration needed
            else:
                moving_image = whiten_image(series_images[target_echo_idx])
                _, transform = register_volumes(target_image, moving_image, temp_folder, rigid=True)
                
                # Apply transform to all echoes in this series
                registered_images = []
                for j, image in enumerate(series_images):
                    transformed_image = apply_transform(image, transform, temp_folder, target_image)
                    # Ensure consistent spatial properties
                    transformed_image.SetOrigin(target_image.GetOrigin())
                    transformed_image.SetSpacing(target_image.GetSpacing())
                    transformed_image.SetDirection(target_image.GetDirection())
                    registered_images.append(transformed_image)
                
                registered_series_images.append(registered_images)
        
        # Flatten and sort by echo time
        all_echo_images = [img for series in registered_series_images for img in series]
        all_echo_times = [time for series in series_echo_times for time in series]
        
        sorted_indices = np.argsort(all_echo_times)
        echo_images_sorted = [all_echo_images[i] for i in sorted_indices]
        echo_times_sorted = [all_echo_times[i] for i in sorted_indices]
        
        # Calculate Porosity Index if multiple echoes available
        output_files = []
        if len(echo_times_sorted) > 1:
            self._calculate_and_save_porosity_index(echo_images_sorted, echo_times_sorted, output_path, output_files)
        
        # Create 4D image
        direction_4d = create_4d_direction_matrix(echo_images_sorted[0].GetDirection())
        image_4d = sitk.JoinSeries(echo_images_sorted)
        image_4d.SetDirection(direction_4d)
        
        # Save outputs
        nifti_path = output_path / '4d_array.nii.gz'
        save_nifti_image(image_4d, nifti_path)
        output_files.append(str(nifti_path))
        
        echo_times_path = output_path / 'echo_times.txt'
        save_metadata(echo_times_sorted, echo_times_path)
        output_files.append(str(echo_times_path))
        
        center_freq_path = output_path / 'center_freq.txt'
        save_metadata(center_freqs[0], center_freq_path)
        output_files.append(str(center_freq_path))
        
        # Create metadata
        metadata = {
            'sequence_type': 'UTE',
            'num_echoes': len(echo_times_sorted),
            'num_series': len(series_numbers),
            'echo_times': echo_times_sorted,
            'center_frequency': center_freqs[0],
            'coregistered': True
        }
        
        result = ConversionResult(
            images=[image_4d] + echo_images_sorted,
            metadata=metadata,
            output_files=output_files,
            sequence_type='UTE'
        )
        
        self._log_conversion_complete(output_path)
        return result
    
    def _calculate_and_save_porosity_index(self, echo_images: List[sitk.Image], 
                                         echo_times: List[float],
                                         output_path: Path,
                                         output_files: List[str]) -> None:
        """Calculate and save porosity index."""
        self.logger.info(f"Calculating PI with {len(echo_images)} echo images")
        self.logger.info(f"Echo times: {echo_times}")

        # Find echo closest to 2.2 ms
        echo_time_2p2 = min(echo_times, key=lambda x: abs(x - 2.2))
        echo_time_2p2_idx = echo_times.index(echo_time_2p2)
        
        self.logger.info(f"Using echo at {echo_time_2p2} ms (index {echo_time_2p2_idx}) for PI calculation")
        
        # Get arrays
        echo_array_0 = sitk.GetArrayFromImage(echo_images[0])
        echo_array_2p2 = sitk.GetArrayFromImage(echo_images[echo_time_2p2_idx])
        
        self.logger.info(f"Echo 0 array shape: {echo_array_0.shape}, range: [{echo_array_0.min():.2f}, {echo_array_0.max():.2f}]")
        self.logger.info(f"Echo 2.2ms array shape: {echo_array_2p2.shape}, range: [{echo_array_2p2.min():.2f}, {echo_array_2p2.max():.2f}]")
        
        # Calculate PI
        pi_array = calculate_porosity_index(echo_array_0, echo_array_2p2, 0, 100)
        
        self.logger.info(f"PI array shape: {pi_array.shape}, range: [{pi_array.min():.2f}, {pi_array.max():.2f}]")
        
        # Create image and save
        pi_image = sitk_image_from_array(pi_array, echo_images[0].GetSpacing(), echo_images[0])
        pi_path = output_path / 'PI.nii.gz'
        save_nifti_image(pi_image, pi_path)
        output_files.append(str(pi_path))
        
        self.logger.info(f"Calculated and saved Porosity Index using echo at {echo_time_2p2} ms")
