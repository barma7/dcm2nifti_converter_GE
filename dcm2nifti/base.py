"""
Base abstract class for sequence converters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import logging
import pydicom


# Standard metadata keys for all converters
METADATA_SCHEMA = {
    'sequence_type': str,       # e.g., 'MESE', 'IDEAL', 'UTE', 'DESS'
    'num_echoes': int,          # Number of echoes
    'echo_times': list,         # List of echo times in ms
    'repetition_time': float,   # TR in ms
    'flip_angle': float,        # Degrees
    'pixel_spacing': list,      # [x, y] in mm
    'slice_thickness': float,   # mm
    'processed_as': str,        # How the data was processed
    'series_description': str,  # Original series description
    'series_number': int,       # Series number
}


class SequenceConverter(ABC):
    """
    Abstract base class for all sequence converters.
    
    This class defines the interface that all sequence-specific converters must implement.
    It provides common functionality and ensures consistency across different sequence types.
    """
    
    def __init__(self):
        """Initialize the sequence converter with logging."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @property
    @abstractmethod
    def sequence_name(self) -> str:
        """Return the name of the sequence this converter handles."""
        pass
    
    @property
    @abstractmethod
    def required_parameters(self) -> List[str]:
        """Return a list of required parameters for this converter."""
        pass
    
    @property
    @abstractmethod
    def optional_parameters(self) -> List[str]:
        """Return a list of optional parameters for this converter."""
        pass
    
    @abstractmethod
    def validate_input(self, input_folder: Union[str, Path], **kwargs) -> bool:
        """
        Validate input parameters and DICOM files for this sequence type.
        
        Args:
            input_folder: Path to the folder containing DICOM files
            **kwargs: Additional parameters specific to the sequence
            
        Returns:
            bool: True if input is valid, False otherwise
            
        Raises:
            ValueError: If input validation fails
        """
        pass
    
    @abstractmethod
    def convert(self, input_folder: Union[str, Path], output_folder: Union[str, Path], **kwargs) -> Any:
        """
        Convert DICOM series to NIfTI format.
        
        Args:
            input_folder: Path to the folder containing DICOM files
            output_folder: Path to the folder where output files will be saved
            **kwargs: Additional parameters specific to the sequence
            
        Returns:
            Converted image data (format depends on sequence type)
            
        Raises:
            ValueError: If conversion fails
        """
        pass
    
    def _create_output_directory(self, output_folder: Union[str, Path]) -> Path:
        """
        Create output directory if it doesn't exist.
        
        Args:
            output_folder: Path to the output folder
            
        Returns:
            Path object for the output folder
        """
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Created output directory: {output_path}")
        return output_path
    
    def _log_conversion_start(self, input_folder: Union[str, Path], output_folder: Union[str, Path]):
        """Log the start of conversion process."""
        self.logger.info(f"Starting {self.sequence_name} conversion")
        self.logger.info(f"Input folder: {input_folder}")
        self.logger.info(f"Output folder: {output_folder}")
    
    def _log_conversion_complete(self, output_folder: Union[str, Path]):
        """Log the completion of conversion process."""
        self.logger.info(f"{self.sequence_name} conversion complete. Output saved to {output_folder}")
    
    def create_standard_metadata(self, dicom_file: Union[pydicom.Dataset, str], 
                                 sequence_type: str,
                                 **additional_fields) -> Dict[str, Any]:
        """
        Create standardized metadata dictionary.
        
        Args:
            dicom_file: First DICOM file of the series (Dataset or path)
            sequence_type: Type of sequence (MESE, IDEAL, UTE, etc.)
            **additional_fields: Additional converter-specific metadata
            
        Returns:
            Standardized metadata dictionary
        """
        # Load DICOM if it's a file path
        if isinstance(dicom_file, str):
            ds = pydicom.dcmread(dicom_file, stop_before_pixels=True)
        else:
            ds = dicom_file
        
        metadata = {
            'sequence_type': sequence_type,
            'series_description': str(ds.get('SeriesDescription', 'Unknown')),
            'series_number': int(ds.get('SeriesNumber', 0)),
            'repetition_time': float(ds.get('RepetitionTime', 0)),
            'flip_angle': float(ds.get('FlipAngle', 0)),
            'pixel_spacing': [float(x) for x in ds.get('PixelSpacing', [1.0, 1.0])],
            'slice_thickness': float(ds.get('SliceThickness', 1.0)),
        }
        
        # Add additional fields
        metadata.update(additional_fields)
        
        return metadata


class ConversionResult:
    """
    Container for conversion results.
    
    This class holds the results of a DICOM to NIfTI conversion,
    including the converted images and associated metadata.
    """
    
    def __init__(self, 
                 images: List[Any], 
                 metadata: Dict[str, Any], 
                 output_files: List[str],
                 sequence_type: str):
        """
        Initialize conversion result.
        
        Args:
            images: List of converted SimpleITK images
            metadata: Dictionary containing sequence metadata
            output_files: List of output file paths
            sequence_type: Type of sequence that was converted
        """
        self.images = images
        self.metadata = metadata
        self.output_files = output_files
        self.sequence_type = sequence_type
    
    def __repr__(self) -> str:
        return (f"ConversionResult(sequence_type='{self.sequence_type}', "
                f"num_images={len(self.images)}, "
                f"num_output_files={len(self.output_files)})")
