@echo off
chcp 65001 >nul
echo ============================================
echo  JitterViewer .exe Build Script
echo ============================================

:: Activate .venv if exists, otherwise use system Python
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python is not installed or not found in PATH.
        pause
        exit /b 1
    )
)

:: Install build dependencies
echo [INFO] Checking required packages...
python -c "import pandas, numpy, matplotlib" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing runtime packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install runtime packages.
        pause
        exit /b 1
    )
)

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

:: Clean previous build artifacts
echo [BUILD] Cleaning previous build files...
if exist "dist\JitterViewer.exe" del /f /q "dist\JitterViewer.exe"
if exist "build" rmdir /s /q "build"
if exist "JitterViewer.spec" del /f /q "JitterViewer.spec"

:: Build single-file executable with PyInstaller
echo [BUILD] Starting single-file EXE build...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name JitterViewer ^
    --hidden-import matplotlib.backends.backend_tkagg ^
    --hidden-import pandas ^
    --hidden-import numpy ^
    --collect-data matplotlib ^
    viewer.py

if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Build Complete: dist\JitterViewer.exe
echo ============================================
pause