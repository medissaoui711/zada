@echo off
title cartage - AI Programming Assistant
color 0A
echo ========================================
echo    🏔️ cartage v1.0 - AI Programming Assistant
echo    Where Code Grows
echo ========================================
echo.

cd /d "%USERPROFILE%\Projects\cartage"

if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing requirements...
    call .venv\Scripts\activate
    pip install -r requirements.txt
)

call .venv\Scripts\activate
python cartage.py

pause