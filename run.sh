#!/bin/bash
# PyHyB Launcher Bootstrapper for macOS / Linux

# Define color outputs for premium look
INFO='\033[0;34m'
SUCCESS='\033[0;32m'
WARNING='\033[0;33m'
ERROR='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${INFO}============================================================${NC}"
echo -e "${INFO}             PyHyB Environment Setup & Bootstrapper${NC}"
echo -e "${INFO}============================================================${NC}"

# Check for python3, attempt auto-install if missing
if ! command -v python3 &> /dev/null; then
    echo -e "${WARNING}Python 3 is not detected on your system. Attempting automatic installation...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo -e "${INFO}Homebrew found! Installing Python via brew...${NC}"
            brew install python
        else
            echo -e "${WARNING}Homebrew not found. Downloading the official Python macOS installer...${NC}"
            curl -L -o /tmp/python_macos.pkg https://www.python.org/ftp/python/3.11.9/python-3.11.9-macos11.pkg
            if [ $? -eq 0 ]; then
                echo -e "${INFO}Opening the official Python macOS installer package. Please complete the installer setup...${NC}"
                open /tmp/python_macos.pkg
                echo -e "${WARNING}Please re-run ./run.sh after completing the Python installer window.${NC}"
                exit 0
            else
                echo -e "${ERROR}Failed to download Python macOS installer. Please install Python 3.9+ manually.${NC}"
                exit 1
            fi
        fi
    else
        # Linux
        if command -v apt-get &> /dev/null; then
            echo -e "${INFO}Debian/Ubuntu detected. Installing python3-venv and python3 via apt (requires sudo)...${NC}"
            sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
        elif command -v dnf &> /dev/null; then
            echo -e "${INFO}RedHat/Fedora detected. Installing python3 via dnf (requires sudo)...${NC}"
            sudo dnf install -y python3 python3-pip
        else
            echo -e "${ERROR}Unsupported package manager. Please install Python 3.9+ manually.${NC}"
            exit 1
        fi
    fi
fi

# Double check python3 is now available
if ! command -v python3 &> /dev/null; then
    echo -e "${ERROR}Error: Python 3 could not be installed automatically.${NC}"
    echo -e "${ERROR}Please install Python 3.9+ manually to run PyHyB.${NC}"
    exit 1
fi

# Determine python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "Found Python: ${SUCCESS}v$PYTHON_VERSION${NC}"

# Check if virtual environment matches current python version
if [ -d ".venv" ]; then
    VENV_PYTHON_VERSION=$(.venv/bin/python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
    if [ "$VENV_PYTHON_VERSION" != "$PYTHON_VERSION" ]; then
        echo -e "${WARNING}Virtual environment Python version (v$VENV_PYTHON_VERSION) does not match system Python (v$PYTHON_VERSION). Recreating virtual environment...${NC}"
        rm -rf .venv
    fi
fi

# Create virtual environment if it does not exist
if [ ! -d ".venv" ]; then
    echo -e "Creating virtual environment '.venv'..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo -e "${ERROR}Error: Failed to create virtual environment.${NC}"
        exit 1
    fi
fi

# Activate virtual environment
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${ERROR}Error: Failed to activate virtual environment.${NC}"
    exit 1
fi

# Check if environment is already installed to avoid reinstall overhead
if [ ! -f ".venv/.initialized" ]; then
    echo -e "Installing dependencies & packages (first-time setup)..."
    python3 -m pip install --upgrade pip
    python3 -m pip install --no-cache-dir -e .
    if [ $? -eq 0 ]; then
        touch .venv/.initialized
        echo -e "${SUCCESS}Environment initialized successfully!${NC}"
    else
        echo -e "${ERROR}Error: Dependency installation failed. Cleaning up .venv...${NC}"
        rm -rf .venv
        exit 1
    fi
fi

echo -e "${SUCCESS}Starting PyHyB Launcher Menu...${NC}"
python3 launcher.py
