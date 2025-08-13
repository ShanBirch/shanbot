@echo off
setlocal enabledelayedexpansion

echo Starting Instagram Story Bot...

:: Set the working directory to the script location
pushd "%~dp0"

:: Set Python path
set PYTHON_PATH=C:\Users\Shannon\AppData\Local\Microsoft\WindowsApps\python.exe
set SCRIPT_PATH=%~dp0story1_backup.py

:: Check if Python exists
if not exist "%PYTHON_PATH%" (
    echo Error: Python not found at %PYTHON_PATH%
    pause
    exit /b 1
)

:: Check if script exists
if not exist "%SCRIPT_PATH%" (
    echo Error: Script not found at %SCRIPT_PATH%
    pause
    exit /b 1
)

:: Run the bot
echo Running script: %SCRIPT_PATH%
"%PYTHON_PATH%" "%SCRIPT_PATH%"

:: Capture the exit code
set EXIT_CODE=%ERRORLEVEL%

:: If there was an error, pause
if not "%EXIT_CODE%"=="0" (
    echo.
    echo Script exited with code: %EXIT_CODE%
    pause
)

popd
exit /b %EXIT_CODE% 