# DCM2NIfTI Batch Processing Scripts

This folder contains PowerShell scripts for batch processing DICOM files using the dcm2nifti converter.

## Scripts Available

### 1. `batch_convert.ps1` - General Batch Processing Script

A flexible script that can process multiple DICOM folders with any converter type.

**Parameters:**
- `ExamPath` (required): Path to the main exam folder
- `Converter` (required): Converter type (e.g., "general_echo", "mese", "ute", etc.)
- `DicomFolders` (required): Array of DICOM folder names to process
- `OutputFolders` (required): Array of corresponding output folder names
- `OutputRoot` (optional): Root output folder name (default: "ELAB")
- `MainOutputPath` (optional): Custom output root path. If specified, output will go here instead of ExamPath\OutputRoot
- `PythonEnv` (optional): Path to Python environment to activate
- `DryRun` (optional): Switch to preview commands without executing
- `VerboseOutput` (optional): Switch for verbose output

**Usage Examples:**

```powershell
# Your specific use case - water oil emulsions study
.\batch_convert.ps1 -ExamPath "D:\Research\Projects\bone_phantom\water_oil_emulsions\7279_07072025" -Converter "general_echo" -DicomFolders @("003","004","005","006","007","008","010","011","012","013") -OutputFolders @("1","2","3","4","5","6","7","8","9","10")

# Process MESE sequences
.\batch_convert.ps1 -ExamPath "D:\Research\Projects\exam" -Converter "mese" -DicomFolders @("100","200","300") -OutputFolders @("mese_1","mese_2","mese_3")

# Dry run to preview commands
.\batch_convert.ps1 -ExamPath "D:\path\to\exam" -Converter "general_echo" -DicomFolders @("001","002") -OutputFolders @("1","2") -DryRun

# With custom Python environment
.\batch_convert.ps1 -ExamPath "D:\path\to\exam" -Converter "ute" -DicomFolders @("300","400","500") -OutputFolders @("ute_1","ute_2","ute_3") -PythonEnv "C:\Users\user\miniconda3\envs\tf-gpu"

# Save to custom output directory
.\batch_convert.ps1 -ExamPath "D:\Research\Projects\exam" -Converter "general_echo" -DicomFolders @("001","002") -OutputFolders @("1","2") -MainOutputPath "D:\MyResults"
```

### 2. `batch_general_echo_example.ps1` - Specific Example Script

A simple, ready-to-use script specifically configured for your water oil emulsions study.

**Features:**
- Pre-configured for your exact folder structure
- Processes folders 003, 004, 005, 006, 007, 008, 010, 011, 012, 013
- Outputs to folders 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 within ELAB/
- Uses general_echo converter

**Usage:**
```powershell
# Just run the script - no parameters needed
.\batch_general_echo_example.ps1
```

**To customize for different studies:**
Edit the variables at the top of the script:
```powershell
$ExamPath = "D:\Research\Projects\bone_phantom\water_oil_emulsions\7279_07072025"
$Converter = "general_echo"
$OutputRoot = "ELAB"

$folderMapping = @{
    "003" = "1"
    "004" = "2" 
    # ... add your folder mappings
}
```

## Output Structure

By default, both scripts will create the following structure under the exam folder:

```
ExamPath/
├── 003/                    # DICOM folders (input)
├── 004/
├── 005/
├── ...
└── ELAB/                   # Default output root
    ├── 1/                  # Converted NIfTI files
    │   ├── echo_1.nii.gz
    │   ├── echo_times.txt
    │   ├── repetition_time.txt
    │   └── conversion_metadata.json
    ├── 2/
    ├── 3/
    └── ...
```

When using `-MainOutputPath`, the output structure will be:

```
MainOutputPath/             # Custom output location
├── 1/                      # Converted NIfTI files
│   ├── echo_1.nii.gz
│   ├── echo_times.txt
│   ├── repetition_time.txt
│   └── conversion_metadata.json
├── 2/
├── 3/
└── ...
```

## Prerequisites

1. **Python Environment**: Ensure Python is in your PATH or specify the environment
2. **dcm2nifti**: The dcm2nifti package should be installed and working
3. **PowerShell**: Windows PowerShell 5.1 or PowerShell Core 7+

## Testing

Before running on important data, test with the dry run option:

```powershell
.\batch_convert.ps1 -ExamPath "your\path" -Converter "general_echo" -DicomFolders @("test") -OutputFolders @("test_out") -DryRun
```

## Troubleshooting

### Common Issues:

1. **"Execution policy" error**: Run PowerShell as Administrator and execute:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Python not found**: Either add Python to PATH or use the `-PythonEnv` parameter

3. **dcm2nifti not found**: Activate the correct Python environment where dcm2nifti is installed

4. **Permission errors**: Ensure you have write permissions to the output directories

### Verification:

Test dcm2nifti works manually:
```bash
python -m dcm2nifti --list-sequences
```

## Examples

### Quick Start - Your Study
```powershell
cd scripts
.\batch_general_echo_example.ps1
```

### Custom Processing
```powershell
cd scripts
.\batch_convert.ps1 -ExamPath "D:\your\exam\path" -Converter "mese" -DicomFolders @("series1","series2") -OutputFolders @("output1","output2") -Verbose
```

The scripts provide detailed logging and progress information, making it easy to monitor the batch processing progress and identify any issues.
