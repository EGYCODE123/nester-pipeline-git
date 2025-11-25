# Uninstall Windows Service for Kvadrat Waste API
param(
    [string]$ServiceName = "KvadratWasteAPI"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command nssm -ErrorAction SilentlyContinue)) {
    Write-Error "NSSM is not installed. Please download from https://nssm.cc/download and add to PATH."
    exit 1
}

Write-Host "Stopping service: $ServiceName"
nssm stop $ServiceName

Write-Host "Removing service: $ServiceName"
nssm remove $ServiceName confirm

Write-Host "Service '$ServiceName' uninstalled successfully!"









