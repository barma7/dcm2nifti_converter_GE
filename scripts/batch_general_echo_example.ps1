# Simple Batch Convert Script for General Echo
# Specific script for the example: water_oil_emulsions study
#
# Usage: .\batch_general_echo_example.ps1
# Usage (custom output): .\batch_general_echo_example.ps1 -CustomOutputPath "D:\Results"

param(
    [Parameter(Mandatory=$false)]
    [string]$CustomOutputPath = ""
)

# Configuration - Modify these paths as needed
$ExamPath = "D:\Research\Projects\bone_phantom\water_oil_emulsions\7279_07072025"
$Converter = "general_echo"
$OutputRoot = "ELAB"

# Define the mapping of DICOM folders to output folders
$folderMapping = @{
    "003" = "1"
    "004" = "2" 
    "005" = "3"
    "006" = "4"
    "007" = "5"
    "008" = "6"
    "010" = "7"
    "011" = "8"
    "012" = "9"
    "013" = "10"
}

Write-Host "=== DCM2NIfTI Batch Processing - General Echo ===" -ForegroundColor Cyan
Write-Host "Exam Path: $ExamPath" -ForegroundColor Yellow
Write-Host "Converter: $Converter" -ForegroundColor Yellow
if ($CustomOutputPath) {
    Write-Host "Custom Output Path: $CustomOutputPath" -ForegroundColor Yellow
} else {
    Write-Host "Output Root: $OutputRoot (under exam path)" -ForegroundColor Yellow
}
Write-Host ""

# Check if exam path exists
if (-not (Test-Path $ExamPath)) {
    Write-Host "ERROR: Exam path does not exist: $ExamPath" -ForegroundColor Red
    exit 1
}

# Create output root directory
if ($CustomOutputPath) {
    $outputRootPath = $CustomOutputPath
    Write-Host "Using custom output path: $outputRootPath" -ForegroundColor Green
} else {
    $outputRootPath = Join-Path $ExamPath $OutputRoot
}

if (-not (Test-Path $outputRootPath)) {
    New-Item -ItemType Directory -Path $outputRootPath -Force | Out-Null
    Write-Host "Created output directory: $outputRootPath" -ForegroundColor Green
}

# Process each folder
$successCount = 0
$totalCount = $folderMapping.Count
$startTime = Get-Date

foreach ($dicomFolder in $folderMapping.Keys) {
    $outputFolder = $folderMapping[$dicomFolder]
    $dicomPath = Join-Path $ExamPath $dicomFolder
    $outputPath = Join-Path $outputRootPath $outputFolder
    
    Write-Host "Processing $dicomFolder -> $outputFolder ($successCount/$totalCount)" -ForegroundColor Cyan
    
    # Check if DICOM folder exists
    if (-not (Test-Path $dicomPath)) {
        Write-Host "  WARNING: DICOM folder not found: $dicomPath" -ForegroundColor Yellow
        continue
    }
    
    # Create output folder
    if (-not (Test-Path $outputPath)) {
        New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
    }
    
    # Run conversion
    try {
        $command = "python -m dcm2nifti `"$dicomPath`" `"$outputPath`" $Converter"
        Write-Host "  Executing: $command" -ForegroundColor Gray
        
        Invoke-Expression $command
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  SUCCESS: Processed $dicomFolder" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  ERROR: Failed to process $dicomFolder (exit code: $LASTEXITCODE)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ERROR: Exception processing $dicomFolder`: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Processed: $successCount/$totalCount folders" -ForegroundColor $(if ($successCount -eq $totalCount) { "Green" } else { "Yellow" })
Write-Host "Duration: $($duration.TotalMinutes.ToString('F1')) minutes" -ForegroundColor Yellow

if ($successCount -eq $totalCount) {
    Write-Host "All conversions completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Some conversions failed. Please check the output above." -ForegroundColor Yellow
}

# Alternative approach using the main batch_convert.ps1 script:
# .\batch_convert.ps1 -ExamPath "$ExamPath" -Converter "$Converter" -DicomFolders @("003","004","005","006","007","008","010","011","012","013") -OutputFolders @("1","2","3","4","5","6","7","8","9","10")
# .\batch_convert.ps1 -ExamPath "$ExamPath" -Converter "$Converter" -DicomFolders @("003","004","005","006","007","008","010","011","012","013") -OutputFolders @("1","2","3","4","5","6","7","8","9","10") -MainOutputPath "D:\MyResults"
