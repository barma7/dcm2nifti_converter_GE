# GeneralSeriesConverter Documentation

## Overview

The `GeneralSeriesConverter` (also called `general_echo`) is a flexible, adaptive DICOM to NIfTI converter designed to handle multi-echo sequences that don't have specific converters. It **automatically detects echo structure** from DICOM metadata and creates organized NIfTI volumes with proper echo time metadata.

**Key Point**: This converter works with **any GE multi-echo sequence** - it doesn't need sequence-specific knowledge!

## Key Features

- **Automatic Echo Detection**: Detects echo times from DICOM headers
- **Adaptive Processing**: Works with any number of echoes (1, 2, 3, 4+)
- **4D Volume Creation**: Automatically creates 4D NIfTI volumes for multi-echo data
- **Standardized Metadata**: Uses consistent metadata schema across conversions
- **Position Sorting**: Optional spatial position sorting for consistent slice ordering
- **Robust**: Comprehensive error handling and validation

## When to Use This Converter

✅ **Use GeneralSeriesConverter when:**
- You have a custom/research multi-echo sequence
- You don't know what sequence type something is
- You want quick exploration of echo structure
- You need to batch process diverse sequences
- The specific sequence converter isn't available

❌ **Use Specific Converters when:**
- You have MESE (use `mese` converter) - specialized handling for spin echoes
- You have DESS (use `dess` converter) - optimized for dual-echo steady state
- You have UTE (use `ute` converter) - handles short echo times and co-registration
- You have IDEAL (use `ideal` converter) - water/fat separation with complex data
- You have MEGRE (use `megre` converter) - multi-echo GRE sequences

## Parameters

### Required Parameters
- `input_folder` (str or Path): Folder containing DICOM files
- `output_folder` (str or Path): Output directory for NIfTI files

### Optional Parameters
- `sort_by_position` (bool, default=True): Sort slices by spatial position for proper 3D/4D alignment
  - Set to `False` if you want to preserve acquisition order

## Usage Examples

### Python - Basic Usage

```python
from dcm2nifti import Dicom2NiftiConverter
from pathlib import Path

converter = Dicom2NiftiConverter()

# Simple conversion
result = converter.convert(
    sequence_type='general_echo',
    input_folder='/path/to/dicoms',
    output_folder='/path/to/output'
)

# Check what was detected
print(f"Echo times found: {result.metadata.get('echo_times', [])}")
print(f"Number of slices: {result.metadata.get('num_slices', 'unknown')}")
print(f"Number of echoes: {result.metadata.get('num_echoes', 'unknown')}")
print(f"Output files created: {result.output_files}")
```

### Python - Without Position Sorting

```python
# Use acquisition order instead of spatial sorting
result = converter.convert(
    sequence_type='general_echo',
    input_folder='/path/to/dicoms',
    output_folder='/path/to/output',
    sort_by_position=False
)
```

### Python - Batch Processing Multiple Studies

```python
from pathlib import Path
from dcm2nifti import Dicom2NiftiConverter

def batch_process_studies(studies_dir):
    converter = Dicom2NiftiConverter()
    studies_dir = Path(studies_dir)
    
    # Find all DICOM folders
    conversions = []
    for study_dir in studies_dir.iterdir():
        dicoms_dir = study_dir / 'dicoms'
        output_dir = study_dir / 'nifti'
        
        if dicoms_dir.exists():
            conversions.append({
                'sequence_type': 'general_echo',
                'input_folder': str(dicoms_dir),
                'output_folder': str(output_dir)
            })
    
    # Process all studies
    results = converter.batch_convert(conversions)
    
    # Report results
    for study_id, result in results.items():
        if isinstance(result, Exception):
            print(f"{study_id}: FAILED - {result}")
        else:
            metadata = result.metadata
            print(f"{study_id}: SUCCESS")
            print(f"  Echo times: {metadata.get('echo_times')}")
            print(f"  Files: {len(result.output_files)}")

# Usage
batch_process_studies('/data/studies')
```

### Python - Error Handling

```python
from dcm2nifti import Dicom2NiftiConverter

converter = Dicom2NiftiConverter()

try:
    result = converter.convert(
        sequence_type='general_echo',
        input_folder='/path/to/dicoms',
        output_folder='/path/to/output',
        sort_by_position=True
    )
    
    # Process successful conversion
    if result:
        echo_times = result.metadata.get('echo_times', [])
        if len(echo_times) < 2:
            print(f"Warning: Only {len(echo_times)} echo(es) detected")
        
        # Proceed with analysis
        process_nifti_files(result.output_files)
    else:
        print("Conversion returned None")
        
except ValueError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"Conversion failed: {e}")
```

### Command Line

```bash
# Basic conversion
python -m dcm2nifti /path/to/dicoms /path/to/output general_echo

# Without spatial sorting (use acquisition order)
python -m dcm2nifti /path/to/dicoms /path/to/output general_echo --no_sort_by_position

# With verbose logging
python -m dcm2nifti /path/to/dicoms /path/to/output general_echo --verbose
```

## Output Structure

```
output_folder/
├── 4d_array.nii.gz              # 4D volume (if multiple echoes)
├── echo_01.nii.gz               # 3D volumes for each echo
├── echo_02.nii.gz
├── echo_03.nii.gz
├── echo_times.txt               # List of echo times in ms
├── spacing_wo_gap.txt           # Voxel spacing (x, y, z)
└── conversion_metadata.json      # Conversion details and parameters
```

### File Descriptions

1. **4D Volume** (`4d_array.nii.gz`)
   - Created when 2+ echoes detected
   - 4th dimension = echo time dimension
   - Dimensions: [x, y, z, num_echoes]
   - Use for T2/T2* mapping and relaxometry

2. **Individual Echo Files** (`echo_01.nii.gz`, `echo_02.nii.gz`, etc.)
   - 3D NIfTI files for each echo
   - Useful if you need to process echoes separately
   - Can be deleted if not needed (saves disk space)

3. **Echo Times** (`echo_times.txt`)
   - One echo time per line (in milliseconds)
   - Ordered to match 4D volume
   - Example:
     ```
     10.0
     20.0
     30.0
     ```

4. **Spacing** (`spacing_wo_gap.txt`)
   - Voxel dimensions: [x_mm, y_mm, z_mm]
   - Useful for scaling in analysis

5. **Metadata** (`conversion_metadata.json`)
   - Records what was converted
   - JSON format with conversion parameters and results
   - Useful for reproducibility and tracking

## Metadata Dictionary

The `result.metadata` includes:

```python
{
    'sequence_type': 'GENERAL_SERIES',
    'series_description': 'T2_Map',
    'series_number': 5,
    'num_echoes': 4,
    'echo_times': [10.0, 20.0, 30.0, 40.0],  # in milliseconds
    'num_slices': 32,
    'spacing': (0.5, 0.5, 2.0),              # x, y, z in mm
    'slice_thickness': 2.0,
    'processed_as': 'general_series',
    'repetition_time': 2000,                 # in ms
    'flip_angle': 90.0,
    'pixel_spacing': [0.5, 0.5]             # in-plane resolution
}
```

## What Happens During Conversion

1. **Validates Input**
   - Checks folder exists
   - Finds all DICOM files
   - Verifies DICOM format

2. **Reads DICOM Headers**
   - Extracts echo times from each file
   - Gets spatial information (position, slice thickness)
   - Collects metadata (series description, parameters)

3. **Groups by Echo Time**
   - Files with same echo time → same group
   - Groups ordered by echo time (shortest first)

4. **Sorts Slices** (if `sort_by_position=True`)
   - Orders slices by spatial position
   - Ensures correct 3D/4D volume structure

5. **Creates NIfTI Files**
   - One 3D file per echo time
   - One 4D file combining all echoes (if >1 echo)
   - Sets proper spacing and orientation

6. **Saves Metadata**
   - Echo times to text file
   - Spatial information to file
   - Full metadata to conversion record

## Technical Details

### Echo Time Detection
- Reads `EchoTime` DICOM tag (0018,0081)
- Groups files with identical echo times
- Handles missing echo time gracefully

### Spatial Positioning
- Uses `ImagePositionPatient` DICOM tag
- Falls back to `InstanceNumber` if position unavailable
- Ensures consistent slice ordering

### Data Type
- Converts all output to Float32 (32-bit floating point)
- Preserves intensities from original DICOM
- Compatible with most analysis software

## Performance

- **Memory**: Loads one echo at a time (low memory usage)
- **Speed**: ~1-2 seconds per echo (depends on slice count)
- **Disk**: 1-3x the input DICOM size (creates both 3D and 4D)

## Troubleshooting

### Problem: Few or no echoes detected
**Check**: Do DICOM files have `EchoTime` tags?
```bash
# Linux/Mac: Use dcmdump to verify
dcmdump +L +C <dicom_file> | grep EchoTime

# Windows: Use DICOM viewers or dicom_dump.py tools
```

### Problem: Slices in wrong order
**Solution**: Try with `sort_by_position=False`
```python
result = converter.convert(
    'general_echo', '/dicoms', '/output',
    sort_by_position=False
)
```

### Problem: Wrong voxel spacing
**Check**: Your image viewer settings (NIfTI spacing is correct)
**Verify**: `spacing_wo_gap.txt` contains expected values

### Problem: Memory error on large datasets
**Solution**: Process fewer slices or use machine with more RAM
**Alternative**: Manually split DICOM folder and process parts separately

## Integration with Analysis Pipelines

### Example: fMRI/T2 Mapping Pipeline

```python
from dcm2nifti import Dicom2NiftiConverter
import numpy as np
import nibabel as nib
from pathlib import Path

def t2_mapping_pipeline(dicom_folder, output_folder):
    """Automated T2 mapping from DICOM to NIfTI to maps."""
    
    # Step 1: Convert DICOM to NIfTI
    converter = Dicom2NiftiConverter()
    result = converter.convert(
        'general_echo',
        dicom_folder,
        output_folder,
        sort_by_position=True
    )
    
    if not result:
        raise ValueError("DICOM conversion failed")
    
    # Step 2: Load the 4D NIfTI
    nifti_4d_path = Path(output_folder) / '4d_array.nii.gz'
    img_4d = nib.load(str(nifti_4d_path))
    data_4d = img_4d.get_fdata()
    
    # Step 3: Get echo times
    echo_times_path = Path(output_folder) / 'echo_times.txt'
    echo_times = np.loadtxt(str(echo_times_path))
    
    # Step 4: Calculate T2 map (simple exponential fit)
    t2_map = calculate_t2_map(data_4d, echo_times)
    
    # Step 5: Save T2 map
    t2_img = nib.Nifti1Image(t2_map, img_4d.affine)
    nib.save(t2_img, Path(output_folder) / 'T2_map.nii.gz')
    
    print(f"T2 mapping complete: {t2_map.shape}")
    print(f"T2 range: {t2_map.min():.1f} - {t2_map.max():.1f} ms")
    
    return t2_map

def calculate_t2_map(data_4d, echo_times):
    """Simple mono-exponential T2 fitting."""
    # This is a placeholder - implement your fitting method
    pass

# Usage
t2_map = t2_mapping_pipeline('/dicoms', '/output')
```

## Best Practices

1. **Verify Metadata**: Always check `echo_times.txt` matches what you expect
2. **Test First**: Convert a small subset before processing large batches
3. **Keep Metadata**: Save conversion logs for reproducibility
4. **Validate Echo Times**: Use `--validate-only` flag first for exploration
5. **Document Parameters**: Record `sort_by_position` setting in your pipeline

## See Also

- [README.md](../README.md) - Main documentation with all converters
- [MESE Converter](MESE.md) - For dedicated T2 relaxometry sequences
- [DESS Converter](DESS.md) - For dual-echo steady state sequences
- [UTE Converter](UTE.md) - For ultra-short echo time sequences

```

### Command Line Interface

```bash
# Basic conversion
python -m dcm2nifti /path/to/dicoms /path/to/output general_echo

# With spatial position sorting (default)
python -m dcm2nifti /path/to/dicoms /path/to/output general_echo --sort_by_position

# Without spatial position sorting
python -m dcm2nifti /path/to/dicoms /path/to/output general_echo --no_sort_by_position
```

## Output Structure

```
output_folder/
├── 4d_array.nii.gz              # Main 4D output (multi-echo) or 3D (single echo)
├── echo_1.nii.gz                # Individual echo files (one per echo time)
├── echo_2.nii.gz
├── echo_3.nii.gz
├── echo_times.txt               # Echo times in milliseconds
├── spacing_wo_gap.txt           # Voxel spacing information
└── conversion_metadata.json     # Conversion parameters and metadata
```

## File Descriptions

### Output Files

1. **Main 4D/3D Volume** (`4d_array.nii.gz`)
   - 4D NIfTI file for multi-echo data (echoes in 4th dimension)
   - 3D NIfTI file for single echo data
   - Proper direction matrices for spatial transformations

2. **Individual Echo Files** (`echo_1.nii.gz`, `echo_2.nii.gz`, ...)
   - 3D NIfTI files for each echo time
   - Numbered sequentially starting from 1
   - Float32 data type for consistent processing

3. **Echo Times Metadata** (`echo_times.txt`)
   - List of echo times in milliseconds, one per line
   - Ordered to match the 4th dimension of 4d_array.nii.gz
   - Used for further analysis and processing

4. **Spacing Information** (`spacing_wo_gap.txt`)
   - Voxel spacing in x, y, z dimensions
   - In millimeters

5. **Conversion Metadata** (`conversion_metadata.json`)
   - JSON file with conversion parameters and statistics
   - Useful for reproducibility and documentation
   - Includes echo detection results and processing parameters

### Metadata Structure

The converter provides comprehensive metadata including:

```python
metadata = {
    'sequence_type': 'GENERAL_SERIES',
    'sort_by_position': True,
    'echo_data': {
        'num_echoes': 3,
        'echo_times': [5.0, 10.0, 15.0],
        'num_slices': 24,
        'image_size': [256, 256, 24],
        'spacing': [0.9375, 0.9375, 3.0],
        'slice_thickness': 3.0
    }
}
```

## Technical Details

### Echo Time Detection
- Reads `EchoTime` DICOM tag (0018,0081)
- Falls back to 0.0 if tag is missing
- Groups files with identical echo times

### Series Grouping
- Uses `SeriesNumber` DICOM tag (0020,0011)
- Creates separate groups for each series
- Falls back to 'unknown' if tag is missing

### Spatial Positioning
- Uses existing `sort_dicom_files_by_position` utility
- Sorts by `ImagePositionPatient` and `InstanceNumber`
- Ensures consistent slice ordering

### Image Processing
- Converts all images to Float32 format
- Maintains original spacing and orientation
- Corrects slice thickness when necessary
- Creates proper 4D direction matrices

## Error Handling

The converter handles various error conditions:

1. **Missing DICOM Files**: Validates input folder contains DICOM files
2. **Invalid Echo Times**: Skips files with missing or invalid echo time tags
3. **Insufficient Echoes**: Filters groups below minimum echo threshold
4. **File Processing Errors**: Logs warnings and continues with valid files
5. **Series Reading Errors**: Gracefully handles corrupted or incompatible files

## Performance Considerations

- **Memory Usage**: Loads one echo at a time to manage memory
- **Disk I/O**: Minimizes file reads by grouping operations
- **Processing Time**: Scales linearly with number of echoes and files
- **Storage**: Creates both individual and 4D volumes for flexibility

## Integration with Other Converters

The `GeneralEchoConverter` is designed to complement specific sequence converters:

- Use **MESE** for standard multi-echo spin echo sequences
- Use **IDEAL** for water/fat separation sequences
- Use **UTE** for ultra-short echo time sequences
- Use **GeneralEcho** for research or unknown multi-echo sequences

## Best Practices

1. **Data Organization**: Keep DICOM files organized in a single folder (doesn't need series separation)
2. **Quality Control**: Review `conversion_metadata.json` for echo detection results
3. **Storage Planning**: Consider disk space for both individual echoes and 4D volumes
4. **Documentation**: Save conversion parameters for reproducibility
5. **Spatial Sorting**: Use default `sort_by_position=True` for proper anatomical alignment

## Troubleshooting

### Common Issues

1. **No echoes found**: Check DICOM files have valid `EchoTime` tags
2. **Incorrect echo grouping**: Verify all echoes in the folder have the same series number when expected
3. **Spatial misalignment**: Try enabling `sort_by_position=True` (default) for proper slice ordering
4. **Memory errors**: Process smaller datasets or increase available RAM
5. **Missing output files**: Verify the DICOM files are valid and readable

### Debugging Tips

1. Use logging to see detailed processing information
2. Check `conversion_metadata.json` to verify echo detection results
3. Verify input DICOM tags with DICOM viewer tools
4. Test with a small subset of data first
5. Compare generated echo times with expected values from DICOM headers
