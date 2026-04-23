@echo off
title Interview Ninja
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python app.py
pause