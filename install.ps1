# Foxker 安装脚本 (PowerShell)
# 将 Foxker 安装为系统 docker 命令的替代

param(
    [switch]$Portable,
    [string]$InstallDir = "",
    [switch]$AddToPath
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Foxker 安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
Write-Host "[检查] Python..." -NoNewline
try {
    $pythonVersion = python --version 2>&1
    Write-Host " OK ($pythonVersion)" -ForegroundColor Green
} catch {
    Write-Host " 失败" -ForegroundColor Red
    Write-Host "[错误] 未找到 Python，请先安装 Python 3.8+" -ForegroundColor Red
    exit 1
}

# 检查 WSL
Write-Host "[检查] WSL..." -NoNewline
try {
    $wslList = wsl --list 2>&1
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " 失败" -ForegroundColor Red
    Write-Host "[错误] 未找到 WSL，请先安装 WSL" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 安装 Foxker
Write-Host "[步骤 1/3] 安装 Foxker 包..." -ForegroundColor Yellow
pip install -e . --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 安装失败" -ForegroundColor Red
    exit 1
}
Write-Host "[完成] Foxker 包安装成功" -ForegroundColor Green
Write-Host ""

# 创建便携式脚本
Write-Host "[步骤 2/3] 创建便携式脚本..." -ForegroundColor Yellow

$foxkerDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($foxkerDir)) {
    $foxkerDir = Get-Location
}

# 创建 docker.ps1 代理脚本
$dockerPs1Content = @"
# Foxker Docker 代理脚本
param([Parameter(ValueFromRemainingArguments)]`$Args)
python "$foxkerDir\foxker\cli.py" @Args
"@
$dockerPs1Content | Out-File -FilePath "$foxkerDir\docker.ps1" -Encoding UTF8

# 创建 docker.bat 代理脚本
$dockerBatContent = @"
@echo off
REM Foxker Docker 代理脚本
python "$foxkerDir\foxker\cli.py" %*
"@
$dockerBatContent | Out-File -FilePath "$foxkerDir\docker.bat" -Encoding ASCII

Write-Host "[完成] 便携式脚本创建成功" -ForegroundColor Green
Write-Host ""

# 检查 Podman
Write-Host "[步骤 3/3] 检查 Podman 可用性..." -ForegroundColor Yellow
python -c "from foxker import DockerProxy, Config; p = DockerProxy(); print('Podman 可用' if p.check_podman_available() else 'Podman 不可用，请在 WSL 中安装 Podman')"
Write-Host ""

# 添加到 PATH
if ($AddToPath) {
    Write-Host "[配置] 添加到用户 PATH..." -ForegroundColor Yellow
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($currentPath -notlike "*$foxkerDir*") {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$foxkerDir", "User")
        Write-Host "[完成] 已添加到 PATH" -ForegroundColor Green
    } else {
        Write-Host "[信息] PATH 中已存在" -ForegroundColor Yellow
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "使用方法:" -ForegroundColor White
Write-Host "  1. 便携式使用: 将 $foxkerDir 添加到 PATH"
Write-Host "  2. 或直接运行: .\docker.bat [命令]"
Write-Host "  3. 或使用: python -m foxker [命令]"
Write-Host ""
Write-Host "示例:" -ForegroundColor White
Write-Host "  docker ps"
Write-Host "  docker run -it ubuntu bash"
Write-Host "  docker build -t myimage ."
Write-Host ""
Write-Host "Foxker 特有命令:" -ForegroundColor White
Write-Host "  docker --foxker-info     显示代理信息"
Write-Host "  docker --foxker-check    检查环境"
Write-Host "  docker --foxker-config   显示配置"
Write-Host "  docker --foxker-gui      启动设置界面"
Write-Host ""
Write-Host "或直接启动设置界面:" -ForegroundColor White
Write-Host "  foxker-gui"
Write-Host ""
