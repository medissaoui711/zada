@echo off
title ZADA - AI Programming Assistant
color 0A
echo ========================================
echo    🏔️ ZADA v1.0 - AI Programming Assistant
echo    Where Code Grows
echo ========================================
echo.

cd /d "%USERPROFILE%\Projects\zada"

if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing requirements...
    call .venv\Scripts\activate
    pip install -r requirements.txt
)

call .venv\Scripts\activate
python zada.py

pause