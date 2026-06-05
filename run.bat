@echo off
chcp 65001 >nul

:: Activate .venv if exists, otherwise use system Python
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python is not installed or not found in PATH.
        pause
        exit /b 1
    )
)

:: Check required packages
python -c "import pandas, numpy, matplotlib" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install packages.
        pause
        exit /b 1
    )
)

python viewer.py