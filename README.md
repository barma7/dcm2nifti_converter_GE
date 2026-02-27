# DCM2NIfTI Converter for GE MRI Sequences

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A modular DICOM to NIfTI converter specifically designed for GE MRI sequences. This tool provides converters for different MRI sequence types with proper handling of multi-echo data, slice positioning, and metadata preservation.

## 🚀 Features

- **Modular Architecture**: Each sequence type has its own converter class
- **Multi-Echo Support**: Automatic echo time detection and 4D volume creation
- **CLI**: Command-line interface with different options for different converters (to handle co-registration for example)
- **Batch Processing**: Support for batch conversion of multiple sequences
- **Error Handling**: Comprehensive validation and error reporting
- **Extensible Design**: Easy to add new sequence types
- **Metadata**: Preserves some DICOM metadata in output files

## 🔬 Supported Sequences

| Sequence | Description | Features |
|----------|-------------|----------|
| **MESE** | Multi-Echo Spin Echo | 
| **DESS** | Dual Echo Steady State |
| **UTE** | Ultra-short Echo Time | Short T2 imaging, optional co-registration for multi-series |
| **UTE_SR** | UTE Suppression Ratio | Porosity mapping, multi-series combination |
| **IDEAL** | Iterative Decomposition | Water/fat separation sequences |
| **General Series** | Groups by echo time, general purpose |

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- Required packages will be installed automatically

### Install from source
```bash
git clone https://github.com/barma7/dcm2nifti_converter_GE.git
cd dcm2nifti_converter_GE
pip install -e .
```

### Manual installation
```bash
pip install simpleitk-simpleelastix pydicom nibabel numpy pathlib
```

**Note**: We use `simpleitk-simpleelastix>=2.5.0` instead of SimpleITK to support image registration via Elastix (required for UTE co-registration features).

## 🖥️ Usage

### Command Line Interface

```bash
# Convert MESE sequence
python -m dcm2nifti /path/to/dicoms /path/to/output mese

# Convert DESS sequence  
python -m dcm2nifti /path/to/dicoms /path/to/output dess

# Convert UTE sequence with co-registration
python -m dcm2nifti /path/to/dicoms /path/to/output ute --series_numbers 300 400 500 --coregister

# Convert general multi-echo sequence
python -m dcm2nifti /path/to/dicoms /path/to/output general_echo

# List all supported sequences
python -m dcm2nifti --list-sequences

# Get parameters for a specific sequence
python -m dcm2nifti --get-parameters ute
```

# Get parameters for a sequence type
python -m dcm2nifti --get-parameters mese

# Validate input without converting
python -m dcm2nifti /path/to/dicoms /path/to/output mese --validate-only
```

### Python API

#### Basic Usage

```python
from dcm2nifti import Dicom2NiftiConverter

# Create converter instance
converter = Dicom2NiftiConverter()

# Convert a single sequence
result = converter.convert(
    sequence_type='mese',
    input_folder='/path/to/dicoms',
    output_folder='/path/to/output'
)

# Access conversion results
if result:
    print(f"Conversion successful!")
    print(f"Output files: {result.output_files}")
    print(f"Metadata: {result.metadata}")
```

#### Batch Processing

```python
# Batch convert multiple sequences
conversions = [
    {
        'sequence_type': 'mese',
        'input_folder': '/path/to/mese/dicoms',
        'output_folder': '/path/to/mese/output'
    },
    {
        'sequence_type': 'ute',
        'input_folder': '/path/to/ute/dicoms',
        'output_folder': '/path/to/ute/output',
        'series_numbers': ['300', '400', '500'],  # String series numbers
        'coregister': True
    },
    {
        'sequence_type': 'dess',
        'input_folder': '/path/to/dess/dicoms',
        'output_folder': '/path/to/dess/output',
        'save_echo_images': True
    },
    {
        'sequence_type': 'ideal',
        'input_folder': '/path/to/ideal/dicoms',
        'output_folder': '/path/to/ideal/output',
        'complex': True,  # Process complex data
        'invert': False   # Don't invert slices
    }
]

results = converter.batch_convert(conversions)

# Check results
for conversion_id, result in results.items():
    if isinstance(result, Exception):
        print(f"{conversion_id}: Failed - {result}")
    else:
        print(f"{conversion_id}: Success - {len(result.output_files)} files")
```

#### Sequence Information

```python
# List available sequences
available_sequences = converter.list_supported_sequences()
print(f"Available sequences: {available_sequences}")

# Get parameters for a specific sequence type
ute_params = converter.get_sequence_parameters('ute')
print(f"UTE required parameters: {ute_params['required']}")
print(f"UTE optional parameters: {ute_params['optional']}")

# Validate input before conversion
is_valid = converter.validate_conversion(
    sequence_type='mese',
    input_folder='/path/to/dicoms'
)
```

## � Python Script Integration

Integrate the converter into your analysis pipelines for seamless DICOM processing:

### Example: Research Pipeline Integration

```python
import logging
from pathlib import Path
from dcm2nifti import Dicom2NiftiConverter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MRIProcessingPipeline:
    """Example MRI processing pipeline using dcm2nifti."""
    
    def __init__(self, study_dir: Path):
        self.study_dir = Path(study_dir)
        self.converter = Dicom2NiftiConverter()
        self.results = {}
    
    def process_subject(self, subject_id: str):
        """Process a single subject's DICOM data."""
        subject_dir = self.study_dir / subject_id
        output_dir = self.study_dir / 'derivatives' / subject_id
        
        # Define conversions for this subject
        conversions = [
            {
                'sequence_type': 'mese',
                'input_folder': str(subject_dir / 'MESE'),
                'output_folder': str(output_dir / 'mese'),
                'sort_by_position': True
            },
            {
                'sequence_type': 'ute',
                'input_folder': str(subject_dir),
                'output_folder': str(output_dir / 'ute'),
                'series_numbers': ['300', '400', '500'],
                'coregister': True
            }
        ]
        
        # Run conversions
        subject_results = self.converter.batch_convert(conversions)
        self.results[subject_id] = subject_results
        
        # Process results
        self._process_results(subject_id, subject_results)
    
    def _process_results(self, subject_id: str, results):
        """Post-process conversion results."""
        for conv_id, result in results.items():
            if isinstance(result, Exception):
                logging.error(f"{subject_id}/{conv_id}: {result}")
            else:
                logging.info(
                    f"{subject_id}/{conv_id}: Success - "
                    f"{len(result.output_files)} files generated"
                )
                logging.info(f"  Echo times: {result.metadata.get('echo_times', [])}")
                logging.info(f"  Processing: {result.metadata.get('processed_as', 'unknown')}")
    
    def process_batch(self, subject_ids: list):
        """Process multiple subjects."""
        for subject_id in subject_ids:
            print(f"\nProcessing {subject_id}...")
            try:
                self.process_subject(subject_id)
            except Exception as e:
                logging.error(f"Failed to process {subject_id}: {e}")
    
    def get_summary(self) -> dict:
        """Get summary of all processed subjects."""
        summary = {}
        for subject_id, results in self.results.items():
            successful = sum(
                1 for r in results.values() 
                if not isinstance(r, Exception)
            )
            summary[subject_id] = {
                'total': len(results),
                'successful': successful,
                'failed': len(results) - successful
            }
        return summary

# Usage
if __name__ == '__main__':
    pipeline = MRIProcessingPipeline('/path/to/study')
    subjects = ['sub-001', 'sub-002', 'sub-003']
    
    # Process all subjects
    pipeline.process_batch(subjects)
    
    # Print summary
    print("\nProcessing Summary:")
    for subject_id, stats in pipeline.get_summary().items():
        print(f"{subject_id}: {stats['successful']}/{stats['total']} successful")
```

### Example: Error Handling and Validation

```python
from dcm2nifti import Dicom2NiftiConverter
from pathlib import Path

def safe_convert(sequence_type: str, input_folder: str, output_folder: str, **kwargs):
    """Safely convert DICOM with validation and error handling."""
    converter = Dicom2NiftiConverter()
    
    # Validate input first
    try:
        is_valid = converter.validate_conversion(sequence_type, input_folder, **kwargs)
        if not is_valid:
            print(f"Validation failed for {sequence_type}")
            return None
    except Exception as e:
        print(f"Validation error: {e}")
        return None
    
    # Perform conversion
    try:
        result = converter.convert(
            sequence_type=sequence_type,
            input_folder=input_folder,
            output_folder=output_folder,
            **kwargs
        )
        print(f"Conversion successful: {len(result.output_files)} files")
        return result
    except Exception as e:
        print(f"Conversion error: {e}")
        return None

# Usage
result = safe_convert(
    sequence_type='ideal',
    input_folder='/data/dicoms',
    output_folder='/data/nifti',
    complex=True
)
```

### Example: Direct Converter Access

```python
# Import specific converter classes for direct access
from dcm2nifti.converters import MESEConverter, UTEConverter
from pathlib import Path

# Use MESE converter directly
mese_converter = MESEConverter()

# Validate and convert
if mese_converter.validate_input('/path/to/dicoms'):
    result = mese_converter.convert(
        input_folder='/path/to/dicoms',
        output_folder='/path/to/output',
        sort_by_position=True
    )
    print(f"Echo times: {result.metadata['echo_times']}")
    print(f"Number of slices: {result.metadata.get('num_slices', 'unknown')}")

# Use UTE converter with custom parameters
ute_converter = UTEConverter()

ute_result = ute_converter.convert(
    input_folder='/path/to/ute/data',
    output_folder='/path/to/ute/output',
    series_numbers=['300', '400', '500'],
    coregister=True
)
```

## 📂 Output Structure

Each conversion creates organized output with the following structure:

```
output_folder/
├── 4d_array.nii.gz             # Main 4D output (multi-echo) or 3D (single echo)
├── echo_1.nii.gz               # Individual echo (if save_echo_images=True)
├── echo_2.nii.gz
├── echo_times.txt              # Echo times metadata
├── spacing_wo_gap.txt          # Voxel spacing
└── conversion_metadata.json     # Conversion parameters and info
```

### Metadata Dictionary Structure

Each conversion result includes standardized metadata:

```python
result.metadata = {
    'sequence_type': 'MESE',           # Sequence type
    'series_description': 'T2_Relaxometry',
    'series_number': 5,
    'num_echoes': 8,                   # Number of echoes
    'echo_times': [10.0, 20.0, ...],   # Echo times in ms
    'num_slices': 32,                  # Number of slices
    'spacing': (0.5, 0.5, 2.0),        # Voxel spacing (x, y, z)
    'processed_as': 'multi_echo_spin_echo',
    'repetition_time': 2000,           # TR in ms
    'flip_angle': 90.0,                # Flip angle in degrees
    'pixel_spacing': [0.5, 0.5]        # In-plane resolution
}

## 🔄 Batch Processing Scripts

The `scripts/` folder contains PowerShell scripts for batch processing multiple DICOM folders:

- **`batch_convert.ps1`**: Flexible script for any converter type with customizable parameters
- **`batch_general_echo_example.ps1`**: Ready-to-use script for specific studies

**Example batch processing:**
```powershell
cd scripts
.\batch_convert.ps1 -ExamPath "D:\Research\Projects\study\exam_date" -Converter "general_echo" -DicomFolders @("003","004","005") -OutputFolders @("1","2","3")
```

See `scripts/README.md` for detailed usage instructions.

## 🏗️ Architecture

The converter uses a modular architecture with:

- **Base Classes**: `SequenceConverter` defines the interface with standardized metadata
- **Sequence Converters**: Specialized classes for each sequence type (MESE, DESS, UTE, IDEAL, MEGRE, GeneralSeries)
- **Utility Modules**: Shared functionality for DICOM/NIfTI operations
- **Core Orchestrator**: `Dicom2NiftiConverter` manages the conversion process
- **Standardized Metadata**: All converters use `create_standard_metadata()` for consistency

## 🧪 Adding New Converters

To add support for a new sequence type:

```python
from dcm2nifti.base import SequenceConverter, ConversionResult
from typing import List, Union, Dict, Any
from pathlib import Path
import pydicom

class MySequenceConverter(SequenceConverter):
    """Custom sequence converter."""
    
    @property
    def sequence_name(self) -> str:
        return "MY_SEQUENCE"
    
    @property
    def required_parameters(self) -> List[str]:
        return ["input_folder", "output_folder"]
    
    @property
    def optional_parameters(self) -> List[str]:
        return ["custom_param"]
    
    def validate_input(self, input_folder: Union[str, Path], **kwargs) -> bool:
        """Validate input parameters."""
        try:
            input_path = Path(input_folder)
            if not input_path.exists():
                self.logger.error(f"Input folder not found: {input_folder}")
                return False
            
            dicom_files = list(input_path.glob("*.dcm"))
            if not dicom_files:
                self.logger.error("No DICOM files found")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False
    
    def convert(self, input_folder: Union[str, Path], 
                output_folder: Union[str, Path], **kwargs) -> ConversionResult:
        """Convert DICOM sequence to NIfTI."""
        self._log_conversion_start(input_folder, output_folder)
        
        # Validate
        if not self.validate_input(input_folder, **kwargs):
            raise ValueError("Input validation failed")
        
        # Implementation here
        output_path = self._create_output_directory(output_folder)
        
        # Use standardized metadata
        first_dicom = list(Path(input_folder).glob("*.dcm"))[0]
        metadata = self.create_standard_metadata(
            first_dicom,
            sequence_type='MY_SEQUENCE',
            processed_as='custom_processing'
        )
        
        # Create and return result
        result = ConversionResult(
            images=[],  # Your images here
            metadata=metadata,
            output_files=[],  # Your output files
            sequence_type='MY_SEQUENCE'
        )
        
        self._log_conversion_complete(output_folder)
        return result

# Register the converter
converter = Dicom2NiftiConverter()
converter.register_converter('my_sequence', MySequenceConverter)

# Use it
result = converter.convert(
    sequence_type='my_sequence',
    input_folder='/path/to/dicoms',
    output_folder='/path/to/output'
)
```

**Key Points for Custom Converters:**
- Inherit from `SequenceConverter`
- Define `sequence_name` and parameter properties
- Use `create_standard_metadata()` for consistent metadata
- Call `validate_input()` before processing
- Return `ConversionResult` with images, metadata, and output files

## 🔧 Configuration

### Logging
```python
import logging
from dcm2nifti import Dicom2NiftiConverter

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Can be DEBUG, INFO, WARNING, ERROR
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create converter with custom log level
converter = Dicom2NiftiConverter(log_level=logging.DEBUG)
```

### Sequence-Specific Parameters

Each sequence type supports specific parameters:

```python
# MESE: Multi-Echo Spin Echo
result = converter.convert('mese', input_dir, output_dir, sort_by_position=True)

# DESS: Dual Echo Steady State (always 2 echoes)
result = converter.convert('dess', input_dir, output_dir, save_echo_images=True)

# UTE: Ultra-short Echo Time
result = converter.convert('ute', input_dir, output_dir, 
                          series_numbers=['300', '400', '500'],
                          coregister=True)

# IDEAL: Iterative Decomposition
result = converter.convert('ideal', input_dir, output_dir,
                          complex=True,  # Process complex data
                          invert=False)   # Invert slice order

# GeneralSeries: Auto-detect multi-echo structure
result = converter.convert('general_echo', input_dir, output_dir,
                          sort_by_position=True)
```

For a complete list of parameters for each sequence, use:
```bash
# Command line
python -m dcm2nifti --get-parameters mese

# Python API
params = converter.get_sequence_parameters('mese')
print(f"Required: {params['required']}")
print(f"Optional: {params['optional']}")
```

## 📚 Examples

See the `examples/` folder for:
- `usage_examples.py` - Basic usage examples for all converters
- `general_echo_usage.py` - Detailed GeneralSeries example

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

When contributing:
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for classes and methods
- Use standardized metadata via `create_standard_metadata()`
- Test with multiple sequence types if possible

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for GE MRI DICOM processing
- Uses SimpleITK for image processing
- Supports standard NIfTI output format

## 📧 Contact

For questions or issues, please open a GitHub issue or contact the maintainers.

## 🎯 Quick Reference

### Common Conversion Scenarios

```python
from dcm2nifti import Dicom2NiftiConverter

converter = Dicom2NiftiConverter()

# Scenario 1: Simple multi-echo sequence
result = converter.convert('mese', '/dicoms', '/output')

# Scenario 2: T2 relaxometry with echo images saved
result = converter.convert('mese', '/dicoms', '/output')
echo_times = result.metadata['echo_times']

# Scenario 3: UTE with motion correction across series
result = converter.convert('ute', '/parent_dir', '/output',
                          series_numbers=['5', '6', '7'],
                          coregister=True)

# Scenario 4: Complex IDEAL data (magnitude + real + imaginary)
result = converter.convert('ideal', '/dicoms', '/output', complex=True)

# Scenario 5: Batch process entire study
conversions = [
    {'sequence_type': 'mese', 'input_folder': '/mese_data', 'output_folder': '/out1'},
    {'sequence_type': 'dess', 'input_folder': '/dess_data', 'output_folder': '/out2'},
    {'sequence_type': 'ute', 'input_folder': '/ute_data', 'output_folder': '/out3',
     'series_numbers': ['300', '400', '500'], 'coregister': True}
]
results = converter.batch_convert(conversions)
```

## 📋 Requirements Summary

- **Python 3.7+** - For type hints and modern syntax
- **simpleitk-simpleelastix** - Medical image processing with Elastix registration
- **pydicom** - DICOM file reading
- **nibabel** - NIfTI file I/O
- **numpy** - Numerical operations
- **scipy** - Scientific computing (optional, for some features)

## ✅ Robustness & Error Handling

The converter includes:

- **Comprehensive validation** - Input checking at each step
- **Standardized metadata** - Consistent across all sequence types
- **Error recovery** - Detailed error messages for debugging
- **Logging** - Full audit trail of operations
- **Type hints** - Better IDE support and error detection

---

**Note**: This tool is designed for research purposes. Always validate outputs and ensure compliance with your institution's data handling policies.
