@echo off
echo Creating Shannon's recent check-in video...
echo.

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Run the Python script
python create_shannon_checkin_video.py

REM Deactivate the virtual environment
call deactivate

echo.
if %errorlevel% equ 0 (
    echo Video generation completed successfully!
) else (
    echo Error occurred during video generation.
)
pause 