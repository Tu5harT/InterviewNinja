@echo off
title Interview Ninja - Setup
echo ========================================
echo   Interview Ninja Setup Script
echo ========================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+ first.
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
if exist .venv (
    echo Virtual environment already exists.
) else (
    python -m venv .venv
    echo Virtual environment created.
)
echo.

REM Activate virtual environment and install dependencies
echo [2/5] Installing dependencies...
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
echo.

REM Download spaCy model
echo [3/5] Downloading spaCy English model...
python -m spacy download en_core_web_sm
echo.

REM Create directories
echo [4/5] Creating directories...
if not exist "data" mkdir "data"
if not exist "uploads" mkdir "uploads"
if not exist "recordings" mkdir "recordings"
if not exist "instance" mkdir "instance"
echo Directories created.
echo.

REM Final instructions
echo [5/5] Setup complete!
echo.
echo ========================================
echo   Next Steps:
echo ========================================
echo.
echo 1. Run: python app.py
echo 2. Open: http://localhost:5000
echo.
echo NOTE: On first run, AI models will be
echo       downloaded. This may take 5-10 mins.
echo.
echo ========================================
pause