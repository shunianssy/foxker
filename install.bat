@echo off
REM Foxker 安装脚本 for Windows
REM 将 Foxker 安装为系统 docker 命令的替代

setlocal enabledelayedexpansion

echo ========================================
echo Foxker 安装脚本
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    exit /b 1
)

REM 检查 WSL
wsl --list >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 WSL，请先安装 WSL
    exit /b 1
)

echo [信息] Python 已安装
echo [信息] WSL 已安装
echo.

REM 安装 Foxker
echo [步骤 1/3] 安装 Foxker 包...
pip install -e . --quiet
if errorlevel 1 (
    echo [错误] 安装失败
    exit /b 1
)
echo [完成] Foxker 包安装成功
echo.

REM 创建便携式启动脚本
echo [步骤 2/3] 创建便携式脚本...

REM 获取当前目录
set "FOXKER_DIR=%~dp0"
set "FOXKER_DIR=%FOXKER_DIR:~0,-1%"

REM 创建 docker.bat 代理脚本
(
echo @echo off
echo REM Foxker Docker 代理脚本
echo python "%FOXKER_DIR%\foxker\cli.py" %%*
) > "%FOXKER_DIR%\docker.bat"

REM 创建 docker.cmd 代理脚本
(
echo @echo off
echo REM Foxker Docker 代理脚本
echo python "%FOXKER_DIR%\foxker\cli.py" %%*
) > "%FOXKER_DIR%\docker.cmd"

echo [完成] 便携式脚本创建成功
echo.

REM 检查 Podman
echo [步骤 3/3] 检查 Podman 可用性...
python -c "from foxker import DockerProxy, Config; p = DockerProxy(); print('Podman 可用' if p.check_podman_available() else 'Podman 不可用，请在 WSL 中安装 Podman')"
echo.

echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 使用方法:
echo   1. 便携式使用: 将 %FOXKER_DIR% 添加到 PATH
echo   2. 或直接运行: docker.bat [命令]
echo   3. 或使用: python -m foxker [命令]
echo.
echo 示例:
echo   docker ps
echo   docker run -it ubuntu bash
echo   docker build -t myimage .
echo.
echo Foxker 特有命令:
echo   docker --foxker-info     显示代理信息
echo   docker --foxker-check    检查环境
echo   docker --foxker-config   显示配置
echo.

endlocal
