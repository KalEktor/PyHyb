@echo off
rem PyHyB Launcher Bootstrapper for Windows

rem Force working directory to the directory containing this batch file (fixes Admin startup path issues)
cd /d "%~dp0"

echo ============================================================
echo              PyHyB Environment Setup ^& Bootstrapper
echo ============================================================

rem Check for a working Python installation (ignoring Microsoft Store dummy execution aliases)
python -c "import sys" >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not detected or is not fully configured on your system.
    echo Attempting automatic installation via Windows Package Manager (winget)...

    where winget >nul 2>nul
    if %errorlevel% eq 0 (
        winget install --id Python.Python.3.11 --exact --silent --accept-source-agreements --accept-package-agreements
        if %errorlevel% eq 0 (
            echo Python installed successfully via winget!
            goto :refresh_path
        )
    )

    echo winget failed or not found. Downloading Python 3.11 web installer...
    curl -L -o "%TEMP%\python_installer.exe" https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    if %errorlevel% neq 0 (
        echo Error: Failed to download Python installer automatically.
        echo Please download and install Python 3.9+ manually from https://www.python.org/
        pause
        exit /b 1
    )

    echo Running Python silent installer...
    start /wait "" "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    del "%TEMP%\python_installer.exe" >nul 2>nul

    :refresh_path
    echo Refreshing environment path...
    rem Retrieve updated PATH from registry so the current session can find the new python executable
    for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "PATH=%%b"
    for /f "tokens=2*" %%a in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "PATH=%%b;%PATH%"
)

rem Double check python is now available and fully functional
python -c "import sys" >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python could not be installed automatically or Microsoft Store Alias is blocking.
    echo Please install Python 3.9+ manually and make sure to check "Add Python to PATH" in the installer.
    pause
    exit /b 1
)

rem Self-healing check: verify if the virtual environment is healthy and matching
if exist .venv (
    .venv\Scripts\python.exe -c "import sys; import pyhyb" >nul 2>nul
    if %errorlevel% neq 0 (
        echo Virtual environment is broken, outdated, or corrupted. Recreating...
        rmdir /s /q .venv
        if exist .venv\.initialized (
            del .venv\.initialized >nul 2>nul
        )
    )
)

rem Create virtual environment if it does not exist
if not exist .venv (
    echo Creating virtual environment '.venv'...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

rem Activate virtual environment
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment.
    pause
    exit /b 1
)

rem Check if environment is already installed to avoid reinstall overhead
if not exist .venv\.initialized (
    echo Installing dependencies ^& packages (first-time setup)...
    python -m pip install --upgrade pip
    python -m pip install --no-cache-dir -e .
    if %errorlevel% eq 0 (
        echo. > .venv\.initialized
        echo Environment initialized successfully!
    ) else (
        echo Error: Dependency installation failed. Cleaning up .venv...
        deactivate >nul 2>nul
        rmdir /s /q .venv
        pause
        exit /b 1
    )
)

echo Starting PyHyB Launcher Menu...
python launcher.py
