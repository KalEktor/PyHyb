@echo off
rem PyHyB Launcher Bootstrapper for Windows

rem Force working directory to the directory containing this batch file (fixes Admin startup path issues)
cd /d "%~dp0"

echo ============================================================
echo              PyHyB Environment Setup ^& Bootstrapper
echo ============================================================

rem Check for a working Python installation (ignoring Microsoft Store dummy execution aliases)
python -c "import sys" >nul 2>nul
if %errorlevel% equ 0 goto :python_healthy

echo Python is not detected or is not fully configured on your system.
echo Attempting automatic installation via Windows Package Manager (winget)...

where winget >nul 2>nul
if %errorlevel% neq 0 goto :try_curl

winget install --id Python.Python.3.11 --exact --silent --accept-source-agreements --accept-package-agreements
if %errorlevel% equ 0 goto :refresh_path

:try_curl
echo winget failed or not found. Downloading Python 3.11 web installer...
curl -L -o "%TEMP%\python_installer.exe" https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
if %errorlevel% equ 0 goto :run_installer

echo Error: Failed to download Python installer automatically.
echo Please download and install Python 3.9+ manually from https://www.python.org/
pause
exit /b 1

:run_installer
echo Running Python silent installer...
start /wait "" "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del "%TEMP%\python_installer.exe" >nul 2>nul

:refresh_path
echo Refreshing environment path...
rem Retrieve updated PATH from registry so the current session can find the new python executable
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "PATH=%%b;%PATH%"

:python_healthy
rem Double check python is now available and fully functional
python -c "import sys" >nul 2>nul
if %errorlevel% equ 0 goto :venv_check

echo Error: Python could not be installed automatically or Microsoft Store Alias is blocking.
echo Please install Python 3.9+ manually and make sure to check "Add Python to PATH" in the installer.
pause
exit /b 1

:venv_check
rem Self-healing check: verify if the virtual environment is healthy and matching
if not exist .venv goto :create_venv

.venv\Scripts\python.exe -c "import sys; import pyhyb" >nul 2>nul
if %errorlevel% equ 0 goto :activate_venv

echo Virtual environment is broken, outdated, or corrupted. Recreating...
rmdir /s /q .venv
if exist .venv\.initialized (
    del .venv\.initialized >nul 2>nul
)

:create_venv
echo Creating virtual environment '.venv'...
python -m venv .venv
if %errorlevel% equ 0 goto :activate_venv

echo Error: Failed to create virtual environment.
pause
exit /b 1

:activate_venv
rem Activate virtual environment
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment.
    pause
    exit /b 1
)

if exist .venv\.initialized goto :start_app

echo Installing dependencies ^& packages (first-time setup)...
python -m pip install --upgrade pip
python -m pip install --no-cache-dir -e .
if %errorlevel% equ 0 goto :init_success

echo Error: Dependency installation failed. Cleaning up .venv...
deactivate >nul 2>nul
rmdir /s /q .venv
pause
exit /b 1

:init_success
echo. > .venv\.initialized
echo Environment initialized successfully!

:start_app
echo Starting PyHyB Launcher Menu...
python launcher.py
