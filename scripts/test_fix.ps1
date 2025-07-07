# Test script to verify dcm2nifti detection fix
Write-Host "Testing dcm2nifti detection..." -ForegroundColor Cyan

# Source the main script functions
. .\batch_convert.ps1 -ExamPath "C:\test" -Converter "general_echo" -DicomFolders @("001") -OutputFolders @("test") -DryRun
