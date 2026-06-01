@echo off
chcp 65001 >nul

python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않거나 PATH에 없습니다.
    echo        install_requirements.bat 을 먼저 실행해주세요.
    pause
    exit /b 1
)

python viewer.py
