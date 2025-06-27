"""
Basic tests for the DCM2NIfTI converter.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add the package to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dcm2nifti import Dicom2NiftiConverter
from dcm2nifti.base import SequenceConverter, ConversionResult


class TestDicom2NiftiConverter:
    """Test cases for the main converter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.converter = Dicom2NiftiConverter()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test converter initialization."""
        assert isinstance(self.converter, Dicom2NiftiConverter)
        assert len(self.converter.list_supported_sequences()) > 0
    
    def test_list_supported_sequences(self):
        """Test listing supported sequences."""
        sequences = self.converter.list_supported_sequences()
        assert 'mese' in sequences
        assert 'dess' in sequences
        assert 'ute' in sequences
    
    def test_get_converter(self):
        """Test getting converter instances."""
        mese_converter = self.converter.get_converter('mese')
        assert isinstance(mese_converter, SequenceConverter)
        assert mese_converter.sequence_name == 'MESE'
    
    def test_get_converter_invalid_sequence(self):
        """Test error handling for invalid sequence types."""
        with pytest.raises(ValueError, match="Unsupported sequence type"):
            self.converter.get_converter('invalid_sequence')
    
    def test_get_sequence_parameters(self):
        """Test getting sequence parameters."""
        params = self.converter.get_sequence_parameters('mese')
        assert 'required' in params
        assert 'optional' in params
        assert isinstance(params['required'], list)
        assert isinstance(params['optional'], list)
    
    def test_register_custom_converter(self):
        """Test registering a custom converter."""
        
        class MockConverter(SequenceConverter):
            @property
            def sequence_name(self):
                return "MOCK"
            
            @property
            def required_parameters(self):
                return ["input_folder", "output_folder"]
            
            @property
            def optional_parameters(self):
                return []
            
            def validate_input(self, input_folder, **kwargs):
                return True
            
            def convert(self, input_folder, output_folder, **kwargs):
                return ConversionResult([], {}, [], "MOCK")
        
        # Register custom converter
        self.converter.register_converter('mock', MockConverter)
        
        # Verify it was registered
        assert 'mock' in self.converter.list_supported_sequences()
        
        # Verify we can get an instance
        mock_converter = self.converter.get_converter('mock')
        assert isinstance(mock_converter, MockConverter)


class TestSequenceConverters:
    """Test cases for individual sequence converters."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.converter = Dicom2NiftiConverter()
    
    def test_mese_converter_properties(self):
        """Test MESE converter properties."""
        mese = self.converter.get_converter('mese')
        assert mese.sequence_name == 'MESE'
        assert 'input_folder' in mese.required_parameters
        assert 'output_folder' in mese.required_parameters
    
    def test_dess_converter_properties(self):
        """Test DESS converter properties.""" 
        dess = self.converter.get_converter('dess')
        assert dess.sequence_name == 'DESS'
        assert 'input_folder' in dess.required_parameters
        assert 'output_folder' in dess.required_parameters
    
    def test_ute_converter_properties(self):
        """Test UTE converter properties."""
        ute = self.converter.get_converter('ute')
        assert ute.sequence_name == 'UTE'
        assert 'series_numbers' in ute.required_parameters


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_import_utilities(self):
        """Test that utility functions can be imported."""
        from dcm2nifti.utils import (
            copy_image_headers,
            get_slice_thickness,
            sort_dicom_files_by_position,
            analyze_dicom_series,
            validate_dicom_series,
            sitk_image_from_array,
            save_nifti_image,
            save_metadata
        )
        
        # Just verify they're callable
        assert callable(copy_image_headers)
        assert callable(get_slice_thickness)
        assert callable(sort_dicom_files_by_position)
        assert callable(analyze_dicom_series)
        assert callable(validate_dicom_series)
        assert callable(sitk_image_from_array)
        assert callable(save_nifti_image)
        assert callable(save_metadata)


def test_conversion_result():
    """Test ConversionResult class."""
    result = ConversionResult(
        images=[],
        metadata={'test': 'value'},
        output_files=['file1.nii.gz', 'file2.txt'],
        sequence_type='TEST'
    )
    
    assert result.sequence_type == 'TEST'
    assert result.metadata['test'] == 'value'
    assert len(result.output_files) == 2
    assert 'TEST' in str(result)


if __name__ == '__main__':
    # Run tests if pytest is available
    try:
        pytest.main([__file__, '-v'])
    except ImportError:
        print("pytest not available. Running basic tests...")
        
        # Run basic tests manually
        converter_tests = TestDicom2NiftiConverter()
        converter_tests.setup_method()
        
        try:
            converter_tests.test_initialization()
            print("✓ Initialization test passed")
            
            converter_tests.test_list_supported_sequences()
            print("✓ List sequences test passed")
            
            converter_tests.test_get_converter()
            print("✓ Get converter test passed")
            
            converter_tests.test_get_sequence_parameters()
            print("✓ Get parameters test passed")
            
            print("\nBasic tests completed successfully!")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
        
        finally:
            converter_tests.teardown_method()
