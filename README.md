# DCM2NIfTI Converter for GE MRI Sequences

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
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
- Python 3.7 or higher
- Required packages will be installed automatically

### Install from source
```bash
git clone https://github.com/barma7/dcm2nifti_converter_GE.git
cd dcm2nifti_converter_GE
pip install -e .
```

### Manual installation
```bash
pip install SimpleITK pydicom nibabel numpy pathlib
```

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

```python
from dcm2nifti import Dicom2NiftiConverter

# Create converter
converter = Dicom2NiftiConverter()

# Convert a single sequence
result = converter.convert(
    sequence_type='mese',
    input_folder='/path/to/dicoms',
    output_folder='/path/to/output'
)

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
        'series_numbers': [300, 400, 500],
        'coregister': True
    }
]

results = converter.batch_convert(conversions)

# Check available converters
print(converter.get_available_sequences())

# Get parameters for a specific sequence
params = converter.get_sequence_parameters('ute')
```

## 📂 Output Structure

Each conversion creates organized output with the following structure:

```
output_folder/
├── echo_01_TE_10.00ms.nii.gz    # Individual echo images
├── echo_02_TE_20.00ms.nii.gz
├── 4d_multiecho.nii.gz          # 4D combined volume
├── echo_times.txt               # Echo time metadata
└── conversion_metadata.txt      # Conversion parameters
```

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

- **Base Classes**: `SequenceConverter` defines the interface
- **Sequence Converters**: Specialized classes for each sequence type
- **Utility Modules**: Shared functionality for DICOM/NIfTI operations
- **Core Orchestrator**: `Dicom2NiftiConverter` manages the process

## 🧪 Adding New Converters

To add support for a new sequence type:

```python
from dcm2nifti.base import SequenceConverter, ConversionResult

class MySequenceConverter(SequenceConverter):
    @property
    def sequence_name(self) -> str:
        return "MY_SEQUENCE"
    
    def validate_input(self, input_folder, **kwargs) -> bool:
        # Implement validation logic
        return True
    
    def convert(self, input_folder, output_folder, **kwargs) -> ConversionResult:
        # Implement conversion logic
        pass

# Register the converter
converter = Dicom2NiftiConverter()
converter.register_converter('my_sequence', MySequenceConverter)
```

## 🔧 Configuration

### Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Custom Parameters
Each sequence type supports specific parameters. Use `--get-parameters <sequence>` to see available options.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for GE MRI DICOM processing
- Uses SimpleITK for image processing
- Supports standard NIfTI output format

## 📧 Contact

For questions or issues, please open a GitHub issue or contact the maintainers.

---

**Note**: This tool is designed for research purposes. Always validate outputs and ensure compliance with your institution's data handling policies.
