@echo off
REM Foxker Installation Script for Windows
REM Install Foxker as a docker command replacement

echo ========================================
echo Foxker Installation Script
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found, please install Python 3.8+
    exit /b 1
)

REM Check WSL
wsl --list >nul 2>&1
if errorlevel 1 (
    echo [Error] WSL not found, please install WSL
    exit /b 1
)

echo [Check] Python OK
echo [Check] WSL OK
echo.

REM Install Foxker
echo [Step 1/3] Installing Foxker package...
pip install -e . --quiet
if errorlevel 1 (
    echo [Error] Installation failed
    exit /b 1
)
echo [Done] Foxker package installed
echo.

REM Create portable scripts
echo [Step 2/3] Creating portable scripts...

REM Get current directory
set "FOXKER_DIR=%~dp0"
set "FOXKER_DIR=%FOXKER_DIR:~0,-1%"

REM Create docker.bat proxy script
(
echo @echo off
echo REM Foxker Docker Proxy Script
echo python "%FOXKER_DIR%\foxker\cli.py" %%*
) > "%FOXKER_DIR%\docker.bat"

REM Create docker.cmd proxy script
(
echo @echo off
echo REM Foxker Docker Proxy Script
echo python "%FOXKER_DIR%\foxker\cli.py" %%*
) > "%FOXKER_DIR%\docker.cmd"

echo [Done] Portable scripts created
echo.

REM Check Podman
echo [Step 3/3] Checking Podman availability...
python -c "from foxker import DockerProxy, Config; p = DockerProxy(); print('Podman available' if p.check_podman_available() else 'Podman not available, please install Podman in WSL')"
echo.

echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Usage:
echo   1. Portable: Add %FOXKER_DIR% to PATH
echo   2. Or run: docker.bat [command]
echo   3. Or use: python -m foxker [command]
echo.
echo Examples:
echo   docker ps
echo   docker run -it ubuntu bash
echo   docker build -t myimage .
echo.
echo Foxker Commands:
echo   docker --foxker-info     Show proxy info
echo   docker --foxker-check    Check environment
echo   docker --foxker-config   Show config
echo   docker --foxker-gui      Launch settings GUI
echo.
echo Or launch GUI directly:
echo   foxker-gui
echo.

endlocal
