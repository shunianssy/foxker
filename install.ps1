# Foxker Installation Script (PowerShell)
# Install Foxker as a docker command replacement

param(
    [switch]$AddToPath
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Foxker Installation Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[Check] Python..." -NoNewline
try {
    $pythonVersion = python --version 2>&1
    Write-Host " OK ($pythonVersion)" -ForegroundColor Green
} catch {
    Write-Host " Failed" -ForegroundColor Red
    Write-Host "[Error] Python not found, please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check WSL
Write-Host "[Check] WSL..." -NoNewline
try {
    $wslList = wsl --list 2>&1
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " Failed" -ForegroundColor Red
    Write-Host "[Error] WSL not found, please install WSL" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Install Foxker
Write-Host "[Step 1/3] Installing Foxker package..." -ForegroundColor Yellow
pip install -e . --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Installation failed" -ForegroundColor Red
    exit 1
}
Write-Host "[Done] Foxker package installed" -ForegroundColor Green
Write-Host ""

# Create portable scripts
Write-Host "[Step 2/3] Creating portable scripts..." -ForegroundColor Yellow

$foxkerDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($foxkerDir)) {
    $foxkerDir = Get-Location
}

# Create docker.ps1 proxy script
$dockerPs1Content = @'
# Foxker Docker Proxy Script
param([Parameter(ValueFromRemainingArguments)]$Args)
python "$foxkerDir\foxker\cli.py" @Args
'@
$dockerPs1Content = $dockerPs1Content.Replace('$foxkerDir', $foxkerDir)
$dockerPs1Content | Out-File -FilePath "$foxkerDir\docker.ps1" -Encoding UTF8

# Create docker.bat proxy script
$dockerBatContent = "@echo off`r`nREM Foxker Docker Proxy Script`r`npython `"$foxkerDir\foxker\cli.py`" %*"
$dockerBatContent | Out-File -FilePath "$foxkerDir\docker.bat" -Encoding ASCII

Write-Host "[Done] Portable scripts created" -ForegroundColor Green
Write-Host ""

# Check Podman
Write-Host "[Step 3/3] Checking Podman availability..." -ForegroundColor Yellow
python -c "from foxker import DockerProxy, Config; p = DockerProxy(); print('Podman available' if p.check_podman_available() else 'Podman not available, please install Podman in WSL')"
Write-Host ""

# Add to PATH
if ($AddToPath) {
    Write-Host "[Config] Adding to user PATH..." -ForegroundColor Yellow
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($currentPath -notlike "*$foxkerDir*") {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$foxkerDir", "User")
        Write-Host "[Done] Added to PATH" -ForegroundColor Green
    } else {
        Write-Host "[Info] Already in PATH" -ForegroundColor Yellow
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Usage:" -ForegroundColor White
Write-Host "  1. Portable: Add $foxkerDir to PATH"
Write-Host "  2. Or run: .\docker.bat [command]"
Write-Host "  3. Or use: python -m foxker [command]"
Write-Host ""
Write-Host "Examples:" -ForegroundColor White
Write-Host "  docker ps"
Write-Host "  docker run -it ubuntu bash"
Write-Host "  docker build -t myimage ."
Write-Host ""
Write-Host "Foxker Commands:" -ForegroundColor White
Write-Host "  docker --foxker-info     Show proxy info"
Write-Host "  docker --foxker-check    Check environment"
Write-Host "  docker --foxker-config   Show config"
Write-Host "  docker --foxker-gui      Launch settings GUI"
Write-Host ""
Write-Host "Or launch GUI directly:" -ForegroundColor White
Write-Host "  foxker-gui"
Write-Host ""
