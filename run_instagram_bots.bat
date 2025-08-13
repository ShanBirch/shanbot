@echo off
set PYTHON_PATH="C:\Users\Shannon\OneDrive\Desktop\shanbot\venv\Scripts\python.exe"
call venv\Scripts\activate.bat
cd app
echo Choose which bot to run:
echo 1. Followers Bot
echo 2. Story Bot
echo.
set /p choice="Enter number (1 or 2): "

if "%choice%"=="1" (
    %PYTHON_PATH% followersbot2.py
) else if "%choice%"=="2" (
    %PYTHON_PATH% story1.py
) else (
    echo Invalid choice!
    pause
) 