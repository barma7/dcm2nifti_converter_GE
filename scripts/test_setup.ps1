# Test Script for DCM2NIfTI Setup
# This script verifies that dcm2nifti is working correctly

Write-Host "=== DCM2NIfTI Setup Test ===" -ForegroundColor Cyan

# Test 1: Check Python
Write-Host "Testing Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found in PATH" -ForegroundColor Red
    exit 1
}

# Test 2: Check dcm2nifti module
Write-Host "Testing dcm2nifti module..." -ForegroundColor Yellow
try {
    $result = python -m dcm2nifti --help 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  SUCCESS: dcm2nifti module is available" -ForegroundColor Green
    } else {
        Write-Host "  ERROR: dcm2nifti module not working" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ERROR: Failed to test dcm2nifti module" -ForegroundColor Red
    exit 1
}

# Test 3: List available sequences
Write-Host "Listing available sequences..." -ForegroundColor Yellow
try {
    python -m dcm2nifti --list-sequences
    Write-Host "  SUCCESS: Sequences listed successfully" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Failed to list sequences" -ForegroundColor Red
    exit 1
}

# Test 4: Get parameters for general_echo
Write-Host "Testing general_echo parameters..." -ForegroundColor Yellow
try {
    python -m dcm2nifti --get-parameters general_echo
    Write-Host "  SUCCESS: general_echo parameters retrieved" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Failed to get general_echo parameters" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== ALL TESTS PASSED ===" -ForegroundColor Green
Write-Host "Your dcm2nifti setup is working correctly!" -ForegroundColor Green
Write-Host "You can now use the batch processing scripts." -ForegroundColor Cyan
