#!/usr/bin/env pwsh

# gRPC Server test script
# Used to quickly test FileService gRPC server

param(
    [string]$ServerAddress = "localhost:50051"
)

$ErrorActionPreference = "Stop"

Write-Host "=== FileService gRPC Server Test ===" -ForegroundColor Green
Write-Host "Server address: " -NoNewline
Write-Host $ServerAddress -ForegroundColor Yellow
Write-Host ""

# Parse server address
$parts = $ServerAddress -split ':'
$host_part = $parts[0]
$port_part = if ($parts.Length -gt 1) { [int]$parts[1] } else { 50051 }

# Check if server is running
Write-Host "Checking server connection..." -ForegroundColor Yellow
try {
    $connection = Test-NetConnection -ComputerName $host_part -Port $port_part -WarningAction SilentlyContinue -InformationLevel Quiet -ErrorAction Stop
    
    if (-not $connection) {
        throw "Connection failed"
    }
    
    Write-Host "✓ Server connection OK" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "Error: Unable to connect to server $ServerAddress" -ForegroundColor Red
    Write-Host "Please ensure:" -ForegroundColor Yellow
    Write-Host "  1. gRPC server is running (go run cmd/main.go)"
    Write-Host "  2. Server address is correct"
    exit 1
}

# Run test client
Write-Host "Running test client..." -ForegroundColor Green
Write-Host ""

try {
    go run cmd/test_client/main.go -addr $ServerAddress
    
    if ($LASTEXITCODE -ne 0) {
        throw "Test client failed with exit code $LASTEXITCODE"
    }
}
catch {
    Write-Host "`nError running test client: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`nTest completed!" -ForegroundColor Green
