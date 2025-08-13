@echo off
echo Fitness Wrapped Setup Helper
echo ===========================
echo.

rem Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in your PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)

rem Create necessary directories
if not exist templates mkdir templates
if not exist fonts mkdir fonts
if not exist music mkdir music
if not exist output mkdir output

echo Created necessary directories: templates, fonts, music, output

rem Copy images from source to templates (with renaming)
echo.
echo Let's copy your Canva images to the templates folder.
echo.

rem Check if copying script exists, download if not
if not exist copy_rename_templates.py (
    echo Downloading template setup script...
    curl -o copy_rename_templates.py https://raw.githubusercontent.com/username/repo/main/copy_rename_templates.py
    if %errorlevel% neq 0 (
        echo Failed to download the script.
        echo Please download copy_rename_templates.py manually.
        pause
        exit /b
    )
)

rem Install required packages
echo Installing required Python packages...
pip install moviepy pillow

rem Run the copy/rename script
python copy_rename_templates.py

rem Check for the main fitness wrapped script
if not exist fitness_wrapped_final_updated.py (
    echo The main script is missing.
    echo Please make sure fitness_wrapped_final_updated.py is in the current directory.
    pause
    exit /b
)

echo.
echo Setup complete! You can now run:
echo python fitness_wrapped_final_updated.py
echo.
echo Press any key to exit...
pause > nul