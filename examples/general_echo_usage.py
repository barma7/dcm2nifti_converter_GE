"""
Example usage of the GeneralSeriesConverter.

This example demonstrates how to use the GeneralSeriesConverter to process
multi-echo DICOM sequences that don't have specific converters.
"""

import sys
from pathlib import Path

# Add the parent directory to the path to import dcm2nifti
sys.path.insert(0, str(Path(__file__).parent.parent))

from dcm2nifti import Dicom2NiftiConverter


def example_general_echo_conversion():
    """Example of using the general echo converter."""
    
    # Initialize the converter
    converter = Dicom2NiftiConverter()
    
    # Example 1: Basic multi-echo conversion
    print("Example 1: Basic multi-echo conversion")
    try:
        result = converter.convert(
            sequence_type='general_echo',
            input_folder='/path/to/multiecho/dicoms',
            output_folder='/path/to/output',
            # Optional parameters with defaults:
            sort_by_position=True      # Sort by spatial position
        )
        print(f"✓ Conversion successful!")
        print(f"Generated files: {len(result.output_files)}")
        print(f"Echo times: {result.metadata.get('echo_times', [])}")
        
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Example 2: Convert with spatial sorting
    print("Example 2: Multi-echo conversion with spatial sorting")
    try:
        result = converter.convert(
            sequence_type='general_echo',
            input_folder='/path/to/multiecho/dicoms',
            output_folder='/path/to/output_multiecho',
            sort_by_position=True      # Sort slices by spatial position
        )
        print(f"✓ Multi-echo conversion successful!")
        print(f"Echo times found: {result.metadata.get('echo_times', [])}")
        
    except Exception as e:
        print(f"✗ Multi-echo conversion failed: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Example 3: Convert without spatial sorting
    print("Example 3: Multi-echo conversion without spatial sorting")
    try:
        result = converter.convert(
            sequence_type='general_echo',
            input_folder='/path/to/multiecho/dicoms',
            output_folder='/path/to/output_combined',
            sort_by_position=False     # Skip spatial position sorting
        )
        print(f"✓ Conversion successful!")
        print(f"Echo times found: {result.metadata.get('echo_times', [])}")
        
    except Exception as e:
        print(f"✗ Combined echo conversion failed: {e}")


def example_cli_usage():
    """Example CLI usage for the general echo converter."""
    
    print("CLI Usage Examples for GeneralSeriesConverter (general_echo):")
    print("=" * 50)
    
    print("\n1. Basic conversion:")
    print("python -m dcm2nifti /path/to/dicoms /path/to/output general_echo")
    
    print("\n2. Sort by spatial position (default):")
    print("python -m dcm2nifti /path/to/dicoms /path/to/output general_echo --sort_by_position")
    
    print("\n3. Don't sort by spatial position:")
    print("python -m dcm2nifti /path/to/dicoms /path/to/output general_echo --no_sort_by_position")
    
    print("\n4. Get parameter information:")
    print("python -m dcm2nifti --get-parameters general_echo")


def example_output_structure():
    """Example of output structure for GeneralSeriesConverter."""
    
    print("Expected Output Structure:")
    print("=" * 30)
    print("""
    output_folder/
    ├── 4d_array.nii.gz              # Main 4D (multi-echo) or 3D (single echo) output
    ├── echo_1.nii.gz                # Individual echo files
    ├── echo_2.nii.gz
    ├── echo_3.nii.gz
    ├── echo_times.txt               # Echo times in milliseconds
    ├── spacing_wo_gap.txt           # Voxel spacing
    └── conversion_metadata.json      # Conversion parameters and metadata
    """)


if __name__ == "__main__":
    print("GeneralSeriesConverter Examples")
    print("============================")
    
    # Show parameter information
    converter = Dicom2NiftiConverter()
    params = converter.get_sequence_parameters('general_echo')
    
    print(f"\nSupported Parameters:")
    print(f"Required: {params['required']}")
    print(f"Optional: {params['optional']}")
    
    print("\n" + "="*60 + "\n")
    
    # Show examples (these would need real data to actually run)
    example_cli_usage()
    print("\n" + "="*60 + "\n")
    example_output_structure()
    
    print("\nNote: The conversion examples above show the API usage,")
    print("but would need actual DICOM data to execute successfully.")
