@echo off
chcp 65001 >nul

:: .venv가 있으면 활성화, 없으면 시스템 Python 사용
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [오류] Python이 설치되어 있지 않거나 PATH에 없습니다.
        pause
        exit /b 1
    )
)

:: 필수 패키지 설치 확인
python -c "import pandas, numpy, matplotlib" >nul 2>&1
if errorlevel 1 (
    echo [설치] 필수 패키지를 설치합니다...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [오류] 패키지 설치에 실패했습니다.
        pause
        exit /b 1
    )
)

python viewer.py
