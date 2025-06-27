"""
Example usage of the refactored DCM2NIfTI converter.
"""

from pathlib import Path
import sys
import os

# Add the package to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dcm2nifti import Dicom2NiftiConverter
import logging

def example_single_conversion():
    """Example of converting a single sequence."""
    print("=== Single Conversion Example ===")
    
    # Create converter with verbose logging
    converter = Dicom2NiftiConverter(log_level=logging.INFO)
    
    # Example paths (you would replace these with your actual paths)
    input_folder = r"D:\Research\Projects\scan_test\mese_dicoms"
    output_folder = r"D:\Research\Projects\scan_test\mese_output"
    
    try:
        # List supported sequences
        print("Supported sequences:", converter.list_supported_sequences())
        
        # Get parameter information
        print("MESE parameters:", converter.get_sequence_parameters('mese'))
        
        # Validate input (optional step)
        print("Validating input...")
        converter.validate_conversion('mese', input_folder)
        print("✓ Validation passed")
        
        # Perform conversion
        print("Converting...")
        result = converter.convert('mese', input_folder, output_folder)
        
        print(f"✓ Conversion successful!")
        print(f"Converted {len(result.images)} images")
        print(f"Generated {len(result.output_files)} files:")
        for file_path in result.output_files:
            print(f"  - {file_path}")
        
        print(f"Metadata: {result.metadata}")
        
    except Exception as e:
        print(f"✗ Conversion failed: {e}")


def example_batch_conversion():
    """Example of batch converting multiple sequences."""
    print("\n=== Batch Conversion Example ===")
    
    converter = Dicom2NiftiConverter()
    
    # Define multiple conversions
    conversions = [
        {
            'sequence_type': 'mese',
            'input_folder': r"D:\Research\Projects\scan_test\mese_dicoms",
            'output_folder': r"D:\Research\Projects\scan_test\mese_output"
        },
        {
            'sequence_type': 'dess',
            'input_folder': r"D:\Research\Projects\scan_test\dess_dicoms", 
            'output_folder': r"D:\Research\Projects\scan_test\dess_output"
        },
        {
            'sequence_type': 'ute',
            'input_folder': r"D:\Research\Projects\scan_test\ute_dicoms",
            'output_folder': r"D:\Research\Projects\scan_test\ute_output",
            'series_numbers': ['400', '500', '600'],
            'coregister': True
        }
    ]
    
    try:
        results = converter.batch_convert(conversions)
        
        print(f"Batch conversion completed:")
        for conversion_id, result in results.items():
            if isinstance(result, Exception):
                print(f"  {conversion_id}: ✗ Failed - {result}")
            else:
                print(f"  {conversion_id}: ✓ Success - {len(result.output_files)} files")
                
    except Exception as e:
        print(f"✗ Batch conversion failed: {e}")


def example_custom_converter():
    """Example of creating and registering a custom converter."""
    print("\n=== Custom Converter Example ===")
    
    from dcm2nifti.base import SequenceConverter, ConversionResult
    from dcm2nifti.utils import save_nifti_image
    import SimpleITK as sitk
    
    class CustomSequenceConverter(SequenceConverter):
        """Example custom converter for demonstration."""
        
        @property
        def sequence_name(self) -> str:
            return "CUSTOM"
        
        @property 
        def required_parameters(self):
            return ["input_folder", "output_folder"]
        
        @property
        def optional_parameters(self):
            return ["custom_param"]
        
        def validate_input(self, input_folder, **kwargs):
            # Simple validation - check if folder exists
            if not Path(input_folder).exists():
                raise ValueError(f"Input folder does not exist: {input_folder}")
            return True
        
        def convert(self, input_folder, output_folder, **kwargs):
            self._log_conversion_start(input_folder, output_folder)
            
            # Create output directory
            output_path = self._create_output_directory(output_folder)
            
            # This is just a dummy conversion for demonstration
            # In reality, you would implement your sequence-specific logic here
            
            # Create a dummy image
            dummy_array = sitk.GetArrayFromImage(sitk.Image([64, 64, 32], sitk.sitkFloat32))
            dummy_image = sitk.GetImageFromArray(dummy_array)
            
            # Save dummy output
            output_file = output_path / "custom_output.nii.gz"
            save_nifti_image(dummy_image, output_file)
            
            result = ConversionResult(
                images=[dummy_image],
                metadata={'sequence_type': 'CUSTOM', 'note': 'This is a demo'},
                output_files=[str(output_file)],
                sequence_type='CUSTOM'
            )
            
            self._log_conversion_complete(output_folder)
            return result
    
    # Register and use the custom converter
    converter = Dicom2NiftiConverter()
    converter.register_converter('custom', CustomSequenceConverter)
    
    print("Registered custom converter")
    print("Updated supported sequences:", converter.list_supported_sequences())
    
    # You could now use it like any other converter:
    # result = converter.convert('custom', '/some/path', '/some/output')


def main():
    """Run all examples."""
    print("DCM2NIfTI Refactored - Usage Examples")
    print("=" * 50)
    
    # Note: These examples use dummy paths. 
    # In real usage, you would replace these with your actual DICOM folder paths.
    
    example_single_conversion()
    example_batch_conversion() 
    example_custom_converter()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nTo use with real data:")
    print("1. Replace the example paths with your actual DICOM folder paths")
    print("2. Ensure your DICOM folders contain valid DICOM files")
    print("3. Run the conversion")


if __name__ == '__main__':
    main()
