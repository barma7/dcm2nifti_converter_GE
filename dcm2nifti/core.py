"""
Core orchestrator class for DICOM to NIfTI conversion.
"""

import logging
from pathlib import Path
from typing import Dict, Type, Union, Any, Optional

from .base import SequenceConverter, ConversionResult
from .converters import MESEConverter, DESSConverter, UTEConverter, UTESRConverter, IDEALConverter, MEGREConverter, GeneralSeriesConverter


class Dicom2NiftiConverter:
    """
    Main orchestrator class for DICOM to NIfTI conversion.
    
    This class manages the conversion process by delegating to appropriate
    sequence-specific converters based on the sequence type.
    """
    
    def __init__(self, log_level: int = logging.INFO):
        """
        Initialize the converter.
        
        Args:
            log_level: Logging level (default: INFO)
        """
        # Set up logging
        self._setup_logging(log_level)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Register available converters
        self.converters: Dict[str, Type[SequenceConverter]] = {
            'mese': MESEConverter,
            'dess': DESSConverter,
            'ute': UTEConverter,
            'ute_sr': UTESRConverter,
            'ideal': IDEALConverter,
            'megre': MEGREConverter,
            'general_echo': GeneralSeriesConverter,
            # Additional converters can be added here
        }
        
        self.logger.info(f"Initialized DICOM to NIfTI converter with {len(self.converters)} sequence types")
    
    def _setup_logging(self, log_level: int) -> None:
        """Set up logging configuration."""
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def list_supported_sequences(self) -> list:
        """
        Get a list of supported sequence types.
        
        Returns:
            List of supported sequence type strings
        """
        return list(self.converters.keys())
    
    def get_converter(self, sequence_type: str) -> SequenceConverter:
        """
        Get a converter instance for the specified sequence type.
        
        Args:
            sequence_type: Type of sequence to convert
            
        Returns:
            Converter instance for the sequence type
            
        Raises:
            ValueError: If sequence type is not supported
        """
        sequence_type = sequence_type.lower()
        
        if sequence_type not in self.converters:
            supported = ', '.join(self.converters.keys())
            raise ValueError(f"Unsupported sequence type '{sequence_type}'. "
                           f"Supported types: {supported}")
        
        return self.converters[sequence_type]()
    
    def validate_conversion(self, sequence_type: str, 
                          input_folder: Union[str, Path], 
                          **kwargs) -> bool:
        """
        Validate input parameters for conversion.
        
        Args:
            sequence_type: Type of sequence to convert
            input_folder: Path to input folder containing DICOM files
            **kwargs: Additional sequence-specific parameters
            
        Returns:
            True if validation passes
            
        Raises:
            ValueError: If validation fails
        """
        converter = self.get_converter(sequence_type)
        return converter.validate_input(input_folder, **kwargs)
    
    def convert(self, sequence_type: str, 
                input_folder: Union[str, Path], 
                output_folder: Union[str, Path], 
                **kwargs) -> ConversionResult:
        """
        Convert DICOM series to NIfTI format.
        
        Args:
            sequence_type: Type of sequence to convert
            input_folder: Path to folder containing DICOM files
            output_folder: Path to folder where outputs will be saved
            **kwargs: Additional sequence-specific parameters
            
        Returns:
            ConversionResult containing conversion results and metadata
            
        Raises:
            ValueError: If conversion fails
        """
        self.logger.info(f"Starting {sequence_type.upper()} conversion")
        self.logger.info(f"Input: {input_folder}")
        self.logger.info(f"Output: {output_folder}")
        
        # Get appropriate converter
        converter = self.get_converter(sequence_type)
        
        # Validate input
        self.logger.info("Validating input...")
        converter.validate_input(input_folder, **kwargs)
        
        # Perform conversion
        self.logger.info("Starting conversion...")
        result = converter.convert(input_folder, output_folder, **kwargs)
        
        self.logger.info(f"Conversion completed successfully!")
        self.logger.info(f"Generated {len(result.output_files)} output files")
        
        return result
    
    def get_sequence_parameters(self, sequence_type: str) -> Dict[str, list]:
        """
        Get parameter information for a sequence type.
        
        Args:
            sequence_type: Type of sequence
            
        Returns:
            Dictionary with 'required' and 'optional' parameter lists
        """
        converter = self.get_converter(sequence_type)
        return {
            'required': converter.required_parameters,
            'optional': converter.optional_parameters
        }
    
    def register_converter(self, sequence_type: str, 
                          converter_class: Type[SequenceConverter]) -> None:
        """
        Register a new converter for a sequence type.
        
        Args:
            sequence_type: Type of sequence
            converter_class: Converter class that inherits from SequenceConverter
        """
        if not issubclass(converter_class, SequenceConverter):
            raise ValueError("Converter class must inherit from SequenceConverter")
        
        sequence_type = sequence_type.lower()
        self.converters[sequence_type] = converter_class
        
        self.logger.info(f"Registered converter for sequence type: {sequence_type}")
    
    def batch_convert(self, conversions: list) -> Dict[str, ConversionResult]:
        """
        Perform batch conversion of multiple sequences.
        
        Args:
            conversions: List of conversion dictionaries, each containing:
                - sequence_type: str
                - input_folder: str/Path
                - output_folder: str/Path
                - Any additional sequence-specific parameters
                
        Returns:
            Dictionary mapping conversion IDs to ConversionResults
        """
        results = {}
        
        self.logger.info(f"Starting batch conversion of {len(conversions)} sequences")
        
        for i, conversion_config in enumerate(conversions):
            conversion_id = f"conversion_{i+1}"
            
            try:
                self.logger.info(f"Processing {conversion_id}...")
                
                # Extract parameters
                sequence_type = conversion_config.pop('sequence_type')
                input_folder = conversion_config.pop('input_folder')
                output_folder = conversion_config.pop('output_folder')
                
                # Perform conversion
                result = self.convert(sequence_type, input_folder, output_folder, **conversion_config)
                results[conversion_id] = result
                
                self.logger.info(f"Completed {conversion_id}")
                
            except Exception as e:
                self.logger.error(f"Failed {conversion_id}: {e}")
                results[conversion_id] = e
        
        successful = sum(1 for r in results.values() if isinstance(r, ConversionResult))
        self.logger.info(f"Batch conversion completed: {successful}/{len(conversions)} successful")
        
        return results
