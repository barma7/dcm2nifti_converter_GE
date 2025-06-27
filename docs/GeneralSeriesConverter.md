# GeneralSeriesConverter Documentation

## Overview

The `GeneralSeriesConverter` is a flexible DICOM to NIfTI converter designed to handle multi-echo sequences that don't have specific converters. It automatically groups DICOM images by echo time and creates organized 4D NIfTI volumes with proper metadata.

## Key Features

- **Automatic Echo Grouping**: Groups DICOM files by echo time values
- **4D Volume Creation**: Automatically creates 4D NIfTI volumes for multi-echo data
- **Comprehensive Metadata**: Saves detailed echo time and conversion metadata
- **Position Sorting**: Optional spatial position sorting for consistent slice ordering

## Use Cases

1. **Research Sequences**: Custom multi-echo sequences without specific converters
2. **Data Exploration**: Quick overview of echo structure in unknown datasets
3. **Quality Control**: Validation of multi-echo acquisitions
4. **Variable Echo Times**: Sequences with non-standard echo time patterns
5. **Mixed Datasets**: Processing datasets with multiple sequence types

## Parameters

### Required Parameters
- `input_folder`: Path to folder containing DICOM files
- `output_folder`: Path to output directory

### Optional Parameters
- `sort_by_position` (default: True): Whether to sort files by spatial position
- `sort_by_position` (default: True): Whether to sort files by spatial position

## Usage Examples

### Python API

```python
from dcm2nifti import Dicom2NiftiConverter

converter = Dicom2NiftiConverter()

# Basic multi-echo conversion
result = converter.convert(
    sequence_type='general_echo',
    input_folder='/path/to/dicoms',
    output_folder='/path/to/output'
)

# Only process sequences with multiple echoes
result = converter.convert(
    sequence_type='general_echo',
    input_folder='/path/to/dicoms',
    output_folder='/path/to/output',
    min_echoes=2
)

# Process all echoes together (no series grouping)
result = converter.convert(
    sequence_type='general_echo',
    input_folder='/path/to/dicoms',
    output_folder='/path/to/output',
    group_by_series=False
)
```

### Command Line Interface

```bash
# Basic conversion
python -m dcm2nifti /path/to/dicoms /path/to/output general_echo

# Only process multi-echo sequences (2+ echoes)
python -m dcm2nifti /path/to/dicoms /path/to/output general_echo --min_echoes 2

# Process all echoes together
python -m dcm2nifti /path/to/dicoms /path/to/output general_echo --no_group_by_series

# Combination of options
python -m dcm2nifti /path/to/dicoms /path/to/output general_echo \
    --min_echoes 3 --no_group_by_series --verbose
```

## Output Structure

### With Series Grouping (default)
```
output_folder/
├── conversion_metadata.txt          # Overall conversion metadata
├── series_123/                      # First series group
│   ├── echo_01_TE_5.00ms.nii.gz    # Individual echo files
│   ├── echo_02_TE_10.00ms.nii.gz
│   ├── echo_03_TE_15.00ms.nii.gz
│   ├── 4d_multiecho.nii.gz         # 4D volume (if >1 echo)
│   └── echo_times.txt               # Echo time metadata
└── series_456/                      # Second series group
    ├── echo_01_TE_2.50ms.nii.gz
    ├── echo_02_TE_7.50ms.nii.gz
    ├── 4d_multiecho.nii.gz
    └── echo_times.txt
```

### Without Series Grouping
```
output_folder/
├── conversion_metadata.txt
└── all/                             # All echoes processed together
    ├── echo_01_TE_2.50ms.nii.gz
    ├── echo_02_TE_5.00ms.nii.gz
    ├── echo_03_TE_7.50ms.nii.gz
    ├── echo_04_TE_10.00ms.nii.gz
    ├── echo_05_TE_15.00ms.nii.gz
    ├── 4d_multiecho.nii.gz
    └── echo_times.txt
```

## File Descriptions

### Output Files

1. **Individual Echo Files** (`echo_XX_TE_YYms.nii.gz`)
   - 3D NIfTI files for each echo time
   - Numbered sequentially with echo time in filename
   - Float32 data type for consistent processing

2. **4D Multi-echo Volume** (`4d_multiecho.nii.gz`)
   - Created when multiple echoes are present
   - 4th dimension represents echo time
   - Proper 4D direction matrix for spatial transformations

3. **Echo Times Metadata** (`echo_times.txt`)
   - List of echo times in milliseconds
   - Ordered to match 4D volume structure
   - Used for further processing and analysis

4. **Conversion Metadata** (`conversion_metadata.txt`)
   - Overall conversion parameters and results
   - Group information and processing statistics
   - Useful for reproducibility and documentation

### Metadata Structure

The converter provides comprehensive metadata including:

```python
metadata = {
    'sequence_type': 'GENERAL_ECHO',
    'min_echoes': 2,
    'group_by_series': True,
    'sort_by_position': True,
    'num_groups': 2,
    'groups': {
        'group_series_123': {
            'num_echoes': 3,
            'echo_times': [5.0, 10.0, 15.0],
            'echo_time_range': [5.0, 15.0],
            'slice_thickness': 3.0,
            'center_frequency': 127.766,
            'files_per_echo': {'5.00': 24, '10.00': 24, '15.00': 24},
            'image_size': [256, 256, 24],
            'spacing': [0.9375, 0.9375, 3.0]
        }
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

1. **Data Organization**: Organize DICOM files by series before conversion
2. **Echo Validation**: Use `min_echoes` to filter incomplete acquisitions
3. **Quality Control**: Review `conversion_metadata.txt` for processing summary
4. **Storage Planning**: Consider disk space for both 3D and 4D outputs
5. **Documentation**: Save conversion parameters for reproducibility

## Troubleshooting

### Common Issues

1. **No echoes found**: Check DICOM files have valid `EchoTime` tags
2. **Empty output**: Verify `min_echoes` threshold is appropriate
3. **Missing series**: Check if `group_by_series=False` is needed
4. **Memory errors**: Process smaller datasets or increase available RAM
5. **Spatial misalignment**: Enable `sort_by_position` for proper ordering

### Debugging Tips

1. Use `--verbose` flag for detailed processing logs
2. Check `conversion_metadata.txt` for group statistics
3. Verify input DICOM tags with DICOM viewers
4. Test with `--validate-only` flag first
5. Compare echo times in output metadata files
