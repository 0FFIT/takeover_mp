@echo off
title takeover_mp
echo Starting takeover_mp...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)

REM Install required packages if not already installed
echo Checking required dependencies...
pip install -r requirements.txt >nul 2>&1

REM Run the Python script
echo Running Takeover MP...
python takeover_mp.py

exit /b