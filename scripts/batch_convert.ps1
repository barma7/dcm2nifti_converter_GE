# DCM2NIfTI Batch Processing Script
# This script processes multiple DICOM folders using dcm2nifti converter
# 
# Usage Examples:
# .\batch_convert.ps1 -ExamPath "D:\Research\Projects\bone_phantom\water_oil_emulsions\7279_07072025" -Converter "general_echo" -DicomFolders @("003","004","005","006","007","008","010","011","012","013") -OutputFolders @("1","2","3","4","5","6","7","8","9","10")
# .\batch_convert.ps1 -ExamPath "D:\Research\Projects\exam" -Converter "mese" -DicomFolders @("100","200","300") -OutputFolders @("mese_1","mese_2","mese_3")
# .\batch_convert.ps1 -ExamPath "D:\Research\Projects\bone_phantom\water_oil_emulsions\7279_07072025" -Converter "general_echo" -DicomFolders @("003","004") -OutputFolders @("1","2") -MainOutputPath "D:\Research\Projects\my_conversions"
# .\batch_convert.ps1 -ExamPath "D:\Research\Projects\exam" -Converter "mese" -DicomFolders @("100","200") -OutputFolders @("mese_1","mese_2") -MainOutputPath "C:\Results" -DryRun
#
# Parameters:
#   -ExamPath: Root path containing DICOM folders
#   -Converter: Type of converter to use (general_echo, mese, dess, ute, etc.)
#   -DicomFolders: Array of DICOM folder names to process
#   -OutputFolders: Array of corresponding output folder names
#   -OutputRoot: Default output folder name under ExamPath (default: "ELAB")
#   -MainOutputPath: Optional custom output root path. If specified, output will go here instead of ExamPath\OutputRoot
#   -PythonEnv: Optional conda environment name to activate
#   -DryRun: If specified, shows what would be done without executing
#   -VerboseOutput: Enable verbose output

param(
    [Parameter(Mandatory=$true)]
    [string]$ExamPath,
    
    [Parameter(Mandatory=$true)]
    [string]$Converter,
    
    [Parameter(Mandatory=$true)]
    [string[]]$DicomFolders,
    
    [Parameter(Mandatory=$true)]
    [string[]]$OutputFolders,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputRoot = "ELAB",
    
    [Parameter(Mandatory=$false)]
    [string]$MainOutputPath = "",
    
    [Parameter(Mandatory=$false)]
    [string]$PythonEnv = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$VerboseOutput = $false
)

# Validate inputs
if ($DicomFolders.Length -ne $OutputFolders.Length) {
    Write-Error "Number of DICOM folders must match number of output folders"
    exit 1
}

if (-not (Test-Path $ExamPath)) {
    Write-Error "Exam path does not exist: $ExamPath"
    exit 1
}

# Function to log messages with timestamp
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "White" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

# Function to activate Python environment if specified
function Set-PythonEnvironment {
    if ($PythonEnv -ne "") {
        Write-Log "Activating Python environment: $PythonEnv"
        if (Test-Path "$PythonEnv\Scripts\Activate.ps1") {
            & "$PythonEnv\Scripts\Activate.ps1"
        } elseif (Test-Path "$PythonEnv\Scripts\activate.bat") {
            & "$PythonEnv\Scripts\activate.bat"
        } else {
            Write-Log "Could not find activation script in: $PythonEnv" "WARNING"
        }
    }
}

# Function to check if dcm2nifti is available
function Test-Dcm2Nifti {
    try {
        # Get the project root directory (parent of scripts folder)
        $projectRoot = Split-Path -Parent $PSScriptRoot
        $originalLocation = Get-Location
        
        Set-Location $projectRoot
        $result = python -m dcm2nifti --help 2>&1
        Set-Location $originalLocation
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "dcm2nifti is available"
            return $true
        } else {
            Write-Log "dcm2nifti is not available or not working properly" "ERROR"
            return $false
        }
    } catch {
        Set-Location $originalLocation
        Write-Log "Python or dcm2nifti not found in PATH" "ERROR"
        return $false
    }
}

# Function to process a single folder
function Process-Folder {
    param(
        [string]$DicomFolder,
        [string]$OutputFolder,
        [string]$DicomPath,
        [string]$OutputPath
    )
    
    Write-Log "Processing folder: $DicomFolder -> $OutputFolder"
    
    # Check if DICOM folder exists
    if (-not (Test-Path $DicomPath)) {
        Write-Log "DICOM folder does not exist: $DicomPath" "ERROR"
        return $false
    }
    
    # Create output directory if it doesn't exist
    if (-not $DryRun) {
        if (-not (Test-Path $OutputPath)) {
            New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
            Write-Log "Created output directory: $OutputPath"
        }
    }
    
    # Build the dcm2nifti command
    $command = "python -m dcm2nifti `"$DicomPath`" `"$OutputPath`" $Converter"
    
    if ($VerboseOutput) {
        $command += " --verbose"
    }
    
    Write-Log "Command: $command"
    
    if ($DryRun) {
        Write-Log "DRY RUN - Would execute: $command" "WARNING"
        return $true
    }
    
    # Execute the conversion
    try {
        # Get the project root directory (parent of scripts folder)
        $projectRoot = Split-Path -Parent $PSScriptRoot
        $originalLocation = Get-Location
        
        Set-Location $projectRoot
        $startTime = Get-Date
        Invoke-Expression $command
        $endTime = Get-Date
        $duration = $endTime - $startTime
        Set-Location $originalLocation
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Successfully processed $DicomFolder in $($duration.TotalSeconds.ToString('F1')) seconds" "SUCCESS"
            return $true
        } else {
            Write-Log "Failed to process $DicomFolder (exit code: $LASTEXITCODE)" "ERROR"
            return $false
        }
    } catch {
        Set-Location $originalLocation
        Write-Log "Exception during processing $DicomFolder`: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Main execution
Write-Log "Starting batch conversion with dcm2nifti"
Write-Log "Exam Path: $ExamPath"
Write-Log "Converter: $Converter"
if ($MainOutputPath) {
    Write-Log "Main Output Path: $MainOutputPath (custom)"
} else {
    Write-Log "Output Root: $OutputRoot (under exam path)"
}
Write-Log "Processing $($DicomFolders.Length) folders"

if ($DryRun) {
    Write-Log "DRY RUN MODE - No actual conversions will be performed" "WARNING"
}

# Set Python environment if specified
Set-PythonEnvironment

# Check if dcm2nifti is available
if (-not (Test-Dcm2Nifti)) {
    Write-Log "Cannot proceed without dcm2nifti. Please check your Python environment." "ERROR"
    exit 1
}

# Create output root directory
if ($MainOutputPath) {
    # Use custom main output path
    $outputRootPath = $MainOutputPath
    Write-Log "Using custom main output path: $outputRootPath"
} else {
    # Use default behavior (relative to exam folder)
    $outputRootPath = Join-Path $ExamPath $OutputRoot
}

if (-not $DryRun) {
    if (-not (Test-Path $outputRootPath)) {
        New-Item -ItemType Directory -Path $outputRootPath -Force | Out-Null
        Write-Log "Created output root directory: $outputRootPath"
    }
}

# Process each folder
$successCount = 0
$failCount = 0
$startTime = Get-Date

for ($i = 0; $i -lt $DicomFolders.Length; $i++) {
    $dicomFolder = $DicomFolders[$i]
    $outputFolder = $OutputFolders[$i]
    
    $dicomPath = Join-Path $ExamPath $dicomFolder
    $outputPath = Join-Path $outputRootPath $outputFolder
    
    Write-Log "--- Processing $($i + 1)/$($DicomFolders.Length) ---"
    
    $success = Process-Folder -DicomFolder $dicomFolder -OutputFolder $outputFolder -DicomPath $dicomPath -OutputPath $outputPath
    
    if ($success) {
        $successCount++
    } else {
        $failCount++
    }
    
    Write-Log "--- Completed $($i + 1)/$($DicomFolders.Length) ---"
}

$endTime = Get-Date
$totalDuration = $endTime - $startTime

# Summary
Write-Log "=== BATCH CONVERSION SUMMARY ==="
Write-Log "Total folders processed: $($DicomFolders.Length)"
Write-Log "Successful conversions: $successCount" "SUCCESS"
Write-Log "Failed conversions: $failCount" $(if ($failCount -gt 0) { "ERROR" } else { "SUCCESS" })
Write-Log "Total time: $($totalDuration.TotalMinutes.ToString('F1')) minutes"

if ($failCount -gt 0) {
    Write-Log "Some conversions failed. Please check the logs above for details." "WARNING"
    exit 1
} else {
    Write-Log "All conversions completed successfully!" "SUCCESS"
    exit 0
}
