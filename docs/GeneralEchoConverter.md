# GeneralEchoConverter Documentation

## Quick Note

The converter is implemented as `GeneralSeriesConverter` in the code, but is called using `'general_echo'` as the sequence type.

**For complete documentation, see [GeneralSeriesConverter.md](GeneralSeriesConverter.md).**

## Quick Start

```python
from dcm2nifti import Dicom2NiftiConverter

converter = Dicom2NiftiConverter()

# Convert multi-echo sequence
result = converter.convert(
    sequence_type='general_echo',
    input_folder='/path/to/dicoms',
    output_folder='/path/to/output',
    sort_by_position=True  # Optional: sort slices by spatial position
)
```

## Key Features

- **Automatic Echo Detection**: Groups DICOM files by echo time values
- **4D Volume Creation**: Creates 4D NIfTI volumes for multi-echo data
- **Position Sorting**: Optional spatial position sorting for proper slice ordering
- **Standardized Metadata**: Saves detailed echo time and conversion metadata
- **Flexible**: Works with any number of echoes (1, 2, 3, 4+)

## Parameters

### Required
- `input_folder`: Path to folder containing DICOM files
- `output_folder`: Path to output directory

### Optional
- `sort_by_position` (default: True): Sort files by spatial position

## Output

Each conversion creates:
- `4d_array.nii.gz` - Main output (4D for multi-echo, 3D for single echo)
- `echo_1.nii.gz`, `echo_2.nii.gz`, etc. - Individual echo files
- `echo_times.txt` - Echo times in milliseconds
- `spacing_wo_gap.txt` - Voxel spacing information
- `conversion_metadata.json` - Conversion parameters and metadata

## Use Cases

- Custom/research multi-echo sequences
- Quick exploration of unknown echo structure
- Batch processing diverse sequences
- When specific sequence converters aren't available

## More Information

See [GeneralSeriesConverter.md](GeneralSeriesConverter.md) for:
- Detailed usage examples
- Python API patterns
- CLI usage
- Metadata dictionary structure
- Technical details
- Error handling and troubleshooting
