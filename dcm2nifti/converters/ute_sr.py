"""
UTE_SR (Ultra-short Echo Time Suppression Ratio) converter.
"""

import SimpleITK as sitk
import numpy as np
from pathlib import Path
from typing import List, Union, Tuple, Any
from os.path import join

from ..base import SequenceConverter, ConversionResult
from ..utils import (
    save_nifti_image,
    sitk_image_from_array
)
from .ute import UTEConverter


class UTESRConverter(SequenceConverter):
    """
    Converter for UTE with Suppression Ratio calculator sequences.
    
    This converter processes two UTE series (UTE and IR-UTE) and calculates
    a Suppression Ratio (SR) map as the ratio between the signals.
    """
    
    def __init__(self):
        super().__init__()
        self.ute_converter = UTEConverter()
    
    @property
    def sequence_name(self) -> str:
        return "UTE_SR"
    
    @property
    def required_parameters(self) -> List[str]:
        return ["input_folder", "output_folder", "series_numbers"]
    
    @property
    def optional_parameters(self) -> List[str]:
        return []
    
    def validate_input(self, input_folder: Union[str, Path], **kwargs) -> bool:
        """
        Validate input parameters for UTE_SR conversion.
        
        Args:
            input_folder: Path to the folder containing DICOM files
            **kwargs: Additional parameters (series_numbers required)
            
        Returns:
            bool: True if input is valid, False otherwise
        """
        try:
            series_numbers = kwargs.get('series_numbers', [])
            
            if not series_numbers or len(series_numbers) != 2:
                self.logger.error("UTE_SR requires exactly 2 series numbers (UTE and IR-UTE)")
                return False
            
            input_path = Path(input_folder)
            if not input_path.exists():
                self.logger.error(f"Input folder does not exist: {input_folder}")
                return False
            
            # Check if both series folders exist
            for series_num in series_numbers:
                series_path = input_path / str(series_num)
                if not series_path.exists():
                    self.logger.error(f"Series folder does not exist: {series_path}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating UTE_SR input: {e}")
            return False
    
    def convert(self, input_folder: Union[str, Path], output_folder: Union[str, Path], 
                series_numbers: List[Union[str, int]], **kwargs) -> ConversionResult:
        """
        Convert UTE_SR DICOM series to NIfTI format.
        
        Processes two series (UTE and IR-UTE), converts them separately and then 
        calculates the SR index as the ratio between UTE and IR-UTE signals.
        
        Args:
            input_folder: Path to the folder containing DICOM files
            output_folder: Path to the output folder
            series_numbers: List containing exactly 2 series numbers [UTE, IR-UTE]
            **kwargs: Additional parameters
            
        Returns:
            ConversionResult: Result of the conversion process
        """
        try:
            # Validate inputs
            if not self.validate_input(input_folder, series_numbers=series_numbers, **kwargs):
                raise ValueError("Input validation failed")
            
            if len(series_numbers) != 2:
                raise ValueError("Please provide exactly 2 series numbers for the SR conversion.")
            
            self.logger.info(f"Converting UTE_SR sequence with series {series_numbers}")
            
            # Create lists for individual series
            series_numbers_uTE = [series_numbers[0]] 
            series_numbers_IRuTE = [series_numbers[1]]
            
            # Create output folders for the two series
            output_path = Path(output_folder)
            output_folder_uTE = output_path / 'uTE'
            output_folder_IRuTE = output_path / 'IRuTE'
            output_folder_uTE.mkdir(parents=True, exist_ok=True)
            output_folder_IRuTE.mkdir(parents=True, exist_ok=True)
            
            # Convert the two series separately using UTE converter
            self.logger.info("Converting UTE series...")
            ute_result = self.ute_converter.convert(
                input_folder, str(output_folder_uTE), series_numbers=series_numbers_uTE, coregister=False
            )
            
            self.logger.info("Converting IR-UTE series...")
            irute_result = self.ute_converter.convert(
                input_folder, str(output_folder_IRuTE), series_numbers=series_numbers_IRuTE, coregister=False
            )
            
            # Get the echo images from the results
            # the first image in each result is the 4D image, so we skip it
            echo_images_uTE = ute_result.images[1:]
            echo_images_IRuTE = irute_result.images[1:]
            
            if not echo_images_uTE or not echo_images_IRuTE:
                raise ValueError("Failed to extract echo images from UTE conversions")
            
            # Extract arrays from the first echo of each series
            echo_array_uTE = sitk.GetArrayFromImage(echo_images_uTE[0])
            echo_array_IRuTE = sitk.GetArrayFromImage(echo_images_IRuTE[0])
            
            # Create SR index array by taking the ratio of uTE and IRuTE
            # Avoid division by zero by adding small epsilon
            epsilon = 1e-10
            sr_index = np.clip(
                (echo_array_uTE / (echo_array_IRuTE + epsilon)), 
                0, 1000
            )
            
            # Replace NaN values with zeros
            sr_index[np.isnan(sr_index)] = 0
            
            # Build 3D image and save
            sr_index_image = sitk_image_from_array(
                sr_index, 
                echo_images_uTE[0].GetSpacing(), 
                echo_images_uTE[0]
            )
            
            sr_index_path = output_path / 'SR_index.nii.gz'
            save_nifti_image(sr_index_image, str(sr_index_path))
            
            # Collect all output files
            output_files = ute_result.output_files + irute_result.output_files + [str(sr_index_path)]
            
            # Prepare metadata
            metadata = {
                'sequence_type': 'UTE_SR',
                'series_numbers': series_numbers,
                'ute_series': series_numbers[0],
                'irute_series': series_numbers[1],
                'echo_images_ute': echo_images_uTE,
                'echo_images_irute': echo_images_IRuTE,
                'sr_index_image': sr_index_image,
                'sr_index_range': [float(sr_index.min()), float(sr_index.max())],
                'ute_metadata': ute_result.metadata,
                'irute_metadata': irute_result.metadata
            }
            
            self.logger.info(f"UTE_SR conversion completed successfully")
            self.logger.info(f"SR index range: {metadata['sr_index_range']}")
            
            return ConversionResult(
                images=[sr_index_image] + echo_images_uTE + echo_images_IRuTE,
                metadata=metadata,
                output_files=output_files,
                sequence_type='UTE_SR'
            )
            
        except Exception as e:
            self.logger.error(f"Error in UTE_SR conversion: {e}")
            raise ValueError(f"Conversion failed: {str(e)}")
    
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
            'description': 'Converts UTE and IR-UTE series to NIfTI and generates SR index map',
            'series_requirements': 'Exactly 2 series numbers required: [UTE_series, IR-UTE_series]',
            'outputs': [
                'uTE/ folder with UTE conversion results',
                'IRuTE/ folder with IR-UTE conversion results', 
                'SR_index.nii.gz - Saturation Recovery index map'
            ]
        }
