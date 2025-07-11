"""
IDEAL (Iterative Decomposition of water and fat with Echo Asymmetry and Least-squares estimation) sequence converter.
"""

import SimpleITK as sitk
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import List, Union, Tuple, Any, Dict
from os.path import join
import pydicom

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
from .mese import MESEConverter


class IDEALConverter(SequenceConverter):
    """
    Converter for IDEAL (Iterative Decomposition of water and fat with Echo Asymmetry 
    and Least-squares estimation) sequences.
    
    This converter can handle both complex (magnitude/real/imaginary) and magnitude-only
    IDEAL acquisitions, producing 4D NIfTI images with proper echo time metadata.
    """
    
    def __init__(self):
        super().__init__()
        self.mese_converter = MESEConverter()
    
    @property
    def sequence_name(self) -> str:
        return "IDEAL"
    
    @property
    def required_parameters(self) -> List[str]:
        return ["input_folder", "output_folder"]
    
    @property
    def optional_parameters(self) -> List[str]:
        return ["complex", "invert"]
    
    def validate_input(self, input_folder: Union[str, Path], **kwargs) -> bool:
        """
        Validate input parameters for IDEAL conversion.
        
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
            
            # Validate complex parameter
            complex_mode = kwargs.get('complex', False)
            if not isinstance(complex_mode, bool):
                self.logger.error("'complex' parameter must be a boolean")
                return False
            
            # Validate invert parameter
            invert = kwargs.get('invert', False)
            if not isinstance(invert, bool):
                self.logger.error("'invert' parameter must be a boolean")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating IDEAL input: {e}")
            return False
    
    def convert(self, input_folder: Union[str, Path], output_folder: Union[str, Path], 
                complex: bool = False, invert: bool = False, **kwargs) -> ConversionResult:
        """
        Convert IDEAL DICOM series to NIfTI format.
        
        Args:
            input_folder: Path to the folder containing DICOM files
            output_folder: Path to the output folder
            complex: Whether to process complex data (real/imaginary components)
            invert: Whether to invert slice order
            **kwargs: Additional parameters
            
        Returns:
            ConversionResult: Result of the conversion process
        """
        try:
            # Validate inputs
            if not self.validate_input(input_folder, complex=complex, invert=invert, **kwargs):
                return ConversionResult(
                    success=False,
                    message="Input validation failed",
                    output_files=[],
                    metadata={}
                )
            
            self.logger.info(f"Converting IDEAL sequence (complex={complex}, invert={invert})")
            
            output_path = Path(output_folder)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Load DICOM series
            series_reader = sitk.ImageSeriesReader()
            dicom_names = series_reader.GetGDCMSeriesFileNames(str(input_folder))
            
            if not dicom_names:
                return ConversionResult(
                    success=False,
                    message="No DICOM files found in the input folder",
                    output_files=[],
                    metadata={}
                )
            
            # Get metadata from first DICOM
            first_dicom = pydicom.dcmread(dicom_names[0])
            slice_thickness = get_slice_thickness(dicom_names[0])
            center_freq = [float(first_dicom.ImagingFrequency)]  # in MHz
            
            output_files = []
            metadata = {
                'sequence_type': 'IDEAL',
                'complex_mode': complex,
                'invert': invert,
                'center_frequency': center_freq,
                'slice_thickness': slice_thickness
            }
            
            if complex:
                # Process complex data (real and imaginary components)
                result = self._convert_complex_ideal(
                    dicom_names, output_path, slice_thickness, invert, series_reader
                )
                if not result['success']:
                    return ConversionResult(
                        success=False,
                        message=result['message'],
                        output_files=[],
                        metadata={}
                    )
                
                output_files.extend(result['output_files'])
                metadata.update(result['metadata'])
                
            else:
                # Process magnitude-only data using MESE converter
                self.logger.info("Processing magnitude-only IDEAL data using MESE converter")
                mese_result = self.mese_converter.convert(input_folder, output_folder)
                
                if not mese_result.success:
                    return ConversionResult(
                        success=False,
                        message=f"Failed to convert magnitude IDEAL data: {mese_result.message}",
                        output_files=[],
                        metadata={}
                    )
                
                output_files.extend(mese_result.output_files)
                metadata.update(mese_result.metadata)
                metadata['processed_as'] = 'magnitude_only_mese'
            
            # Save center frequency metadata
            center_freq_path = output_path / 'center_freq.txt'
            save_metadata(center_freq, str(center_freq_path))
            output_files.append(str(center_freq_path))
            
            self.logger.info(f"IDEAL conversion completed successfully")
            
            return ConversionResult(
                success=True,
                message=f"Successfully converted IDEAL sequence with {len(output_files)} output files",
                output_files=output_files,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error in IDEAL conversion: {e}")
            return ConversionResult(
                success=False,
                message=f"Conversion failed: {str(e)}",
                output_files=[],
                metadata={}
            )
    
    def _convert_complex_ideal(self, dicom_names: List[str], output_path: Path, 
                              slice_thickness: float, invert: bool, 
                              series_reader: sitk.ImageSeriesReader) -> Dict[str, Any]:
        """
        Convert complex IDEAL data with real and imaginary components.
        
        Args:
            dicom_names: List of DICOM file names
            output_path: Output directory path
            slice_thickness: Slice thickness from DICOM
            invert: Whether to invert slice order
            series_reader: SimpleITK series reader
            
        Returns:
            dict: Result dictionary with success status, files, and metadata
        """
        try:
            self.logger.info("Processing complex IDEAL data")
            
            # Analyze DICOM structure
            instance_numbers = [int(pydicom.dcmread(f).InstanceNumber) for f in dicom_names]
            echo_numbers = [int(pydicom.dcmread(f).EchoNumbers) for f in dicom_names]
            
            Nb_echoes = len(set(echo_numbers))
            Nb_slices = len(set(instance_numbers)) // Nb_echoes // 2  # Divide by 2 for real/imag
            
            # Pattern is: Slice1 echo1: REAL, IMAG, Slice1 echo2: REAL, IMAG, etc.
            dicom_names_real = dicom_names[0::2]  # Every other starting from 0
            dicom_names_imag = dicom_names[1::2]  # Every other starting from 1
            
            echo_times = sorted(list(set(float(pydicom.dcmread(f).EchoTime) for f in dicom_names)))
            
            images_4d = []
            echo_images_list = []
            output_files = []
            sv_names = ['4d_array_real.nii.gz', '4d_array_imag.nii.gz']
            
            # Process real and imaginary components
            for idx, (dcm_names, component) in enumerate(zip([dicom_names_real, dicom_names_imag], 
                                                           ['real', 'imaginary'])):
                
                self.logger.info(f"Processing {component} component")
                
                echo_volumes = []
                echo_images = []
                echo_times_component = []
                
                # Process each echo
                for e in range(Nb_echoes):
                    dicom_names_echo = dcm_names[e::Nb_echoes]
                    dicom_names_echo = sort_dicom_files_by_position(dicom_names_echo)
                    
                    if invert:
                        dicom_names_echo = dicom_names_echo[::-1]
                    
                    # Load DICOM series for this echo
                    series_reader.SetFileNames(dicom_names_echo)
                    echo_image = series_reader.Execute()
                    echo_image = sitk.Cast(echo_image, sitk.sitkFloat32)
                    echo_volume = sitk.GetArrayFromImage(echo_image)
                    
                    # Correct spacing
                    spacing = echo_image.GetSpacing()
                    correct_spacing = (spacing[0], spacing[1], slice_thickness)
                    echo_image = sitk_image_from_array(echo_volume, correct_spacing, echo_image)
                    
                    # Extract echo time from headers
                    echo_header = copy_image_headers(dicom_names_echo)
                    echo_times_component.append(float(echo_header[0].get('EchoTime')))
                    
                    echo_images.append(echo_image)
                    echo_volumes.append(echo_volume)
                
                # Create 4D image
                direction_4d = create_4d_direction_matrix(echo_images[0])
                image_4d = sitk.JoinSeries(echo_images)
                image_4d.SetDirection(direction_4d)
                
                # Save 4D image
                output_file = output_path / sv_names[idx]
                save_nifti_image(image_4d, str(output_file))
                output_files.append(str(output_file))
                
                images_4d.append(image_4d)
                echo_images_list.append(echo_images)
            
            # Reconstruct magnitude image from real and imaginary components
            self.logger.info("Reconstructing magnitude image")
            
            real4d = nib.load(str(output_path / '4d_array_real.nii.gz'))
            imag4d = nib.load(str(output_path / '4d_array_imag.nii.gz'))
            
            # Calculate magnitude: sqrt(real^2 + imag^2)
            mag4d_data = np.sqrt(real4d.get_fdata()**2 + imag4d.get_fdata()**2)
            mag4d = nib.Nifti1Image(mag4d_data, real4d.affine)
            
            mag_output = output_path / '4d_array_mag.nii.gz'
            nib.save(mag4d, str(mag_output))
            output_files.append(str(mag_output))
            
            # Save echo times
            echo_times_path = output_path / 'echo_times.txt'
            save_metadata(echo_times, str(echo_times_path))
            output_files.append(str(echo_times_path))
            
            metadata = {
                'nb_echoes': Nb_echoes,
                'nb_slices': Nb_slices,
                'echo_times': echo_times,
                'echo_images_real': echo_images_list[0] if echo_images_list else [],
                'echo_images_imag': echo_images_list[1] if len(echo_images_list) > 1 else [],
                'images_4d': images_4d,
                'components_processed': ['real', 'imaginary', 'magnitude']
            }
            
            return {
                'success': True,
                'message': 'Complex IDEAL conversion completed',
                'output_files': output_files,
                'metadata': metadata
            }
            
        except Exception as e:
            self.logger.error(f"Error in complex IDEAL conversion: {e}")
            return {
                'success': False,
                'message': f'Complex IDEAL conversion failed: {str(e)}',
                'output_files': [],
                'metadata': {}
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
            'description': 'Converts IDEAL DICOM series to NIfTI format',
            'parameter_details': {
                'complex': 'Boolean flag for processing complex data (real/imaginary components)',
                'invert': 'Boolean flag to invert slice order'
            },
            'outputs_complex': [
                '4d_array_real.nii.gz - Real component 4D image',
                '4d_array_imag.nii.gz - Imaginary component 4D image',
                '4d_array_mag.nii.gz - Magnitude 4D image',
                'echo_times.txt - Echo time metadata',
                'center_freq.txt - Center frequency metadata'
            ],
            'outputs_magnitude': [
                '4d_array.nii.gz - 4D magnitude image (via MESE converter)',
                'echo_times.txt - Echo time metadata',
                'center_freq.txt - Center frequency metadata'
            ]
        }
