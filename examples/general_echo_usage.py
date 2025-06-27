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
            min_echoes=1,              # Minimum echoes required
            group_by_series=True,      # Group by series number
            sort_by_position=True      # Sort by spatial position
        )
        print(f"✓ Conversion successful!")
        print(f"Generated files: {len(result.output_files)}")
        print(f"Number of groups processed: {result.metadata['num_groups']}")
        
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Example 2: Convert only sequences with multiple echoes
    print("Example 2: Multi-echo sequences only (min 2 echoes)")
    try:
        result = converter.convert(
            sequence_type='general_echo',
            input_folder='/path/to/multiecho/dicoms',
            output_folder='/path/to/output_multiecho',
            min_echoes=2,              # Only process groups with 2+ echoes
            group_by_series=True,
            sort_by_position=True
        )
        print(f"✓ Multi-echo conversion successful!")
        print(f"Processed {result.metadata['num_groups']} multi-echo groups")
        
    except Exception as e:
        print(f"✗ Multi-echo conversion failed: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Example 3: Process all echoes together (no series grouping)
    print("Example 3: All echoes together (no series grouping)")
    try:
        result = converter.convert(
            sequence_type='general_echo',
            input_folder='/path/to/multiecho/dicoms',
            output_folder='/path/to/output_combined',
            min_echoes=1,
            group_by_series=False,     # Process all echoes together
            sort_by_position=True
        )
        print(f"✓ Combined echo conversion successful!")
        print(f"All echoes processed as one group")
        
    except Exception as e:
        print(f"✗ Combined echo conversion failed: {e}")


def example_cli_usage():
    """Example CLI usage for the general echo converter."""
    
    print("CLI Usage Examples for GeneralSeriesConverter:")
    print("=" * 50)
    
    print("\n1. Basic conversion:")
    print("python -m dcm2nifti /path/to/dicoms /path/to/output general_echo")
    
    print("\n2. Only process multi-echo sequences (2+ echoes):")
    print("python -m dcm2nifti /path/to/dicoms /path/to/output general_echo --min_echoes 2")
    
    print("\n3. Process all echoes together (no series grouping):")
    print("python -m dcm2nifti /path/to/dicoms /path/to/output general_echo --no_group_by_series")
    
    print("\n4. Don't sort by spatial position:")
    print("python -m dcm2nifti /path/to/dicoms /path/to/output general_echo --no_sort_by_position")
    
    print("\n5. Combination of options:")
    print("python -m dcm2nifti /path/to/dicoms /path/to/output general_echo \\")
    print("    --min_echoes 3 --no_group_by_series --verbose")
    
    print("\n6. Get parameter information:")
    print("python -m dcm2nifti --get-parameters general_echo")


def example_output_structure():
    """Example of output structure for GeneralSeriesConverter."""
    
    print("Expected Output Structure:")
    print("=" * 30)
    print("""
    output_folder/
    ├── conversion_metadata.txt          # Overall conversion metadata
    ├── series_123/                      # First series group
    │   ├── echo_01_TE_5.00ms.nii.gz    # Individual echo files
    │   ├── echo_02_TE_10.00ms.nii.gz
    │   ├── echo_03_TE_15.00ms.nii.gz
    │   ├── 4d_multiecho.nii.gz         # 4D volume (if >1 echo)
    │   └── echo_times.txt               # Echo time metadata
    ├── series_456/                      # Second series group
    │   ├── echo_01_TE_2.50ms.nii.gz
    │   ├── echo_02_TE_7.50ms.nii.gz
    │   ├── 4d_multiecho.nii.gz
    │   └── echo_times.txt
    └── all/                             # If group_by_series=False
        ├── echo_01_TE_2.50ms.nii.gz
        ├── echo_02_TE_5.00ms.nii.gz
        ├── echo_03_TE_7.50ms.nii.gz
        ├── echo_04_TE_10.00ms.nii.gz
        ├── echo_05_TE_15.00ms.nii.gz
        ├── 4d_multiecho.nii.gz
        └── echo_times.txt
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
