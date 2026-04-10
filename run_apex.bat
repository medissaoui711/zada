@echo off
title Apex - القمة في البرمجة المساعدة
color 0A
echo ========================================
echo    🏔️ Apex - AI Programming Assistant
echo ========================================
echo.

cd /d "%USERPROFILE%\Projects\ecl-apex"

if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing requirements...
    call .venv\Scripts\activate
    pip install -r requirements.txt
)

call .venv\Scripts\activate
python apex.py

pause