@echo off
echo Running ShanBot Video Generation...

:: Check if a date parameter was provided
if "%~1"=="" (
    python simple_blue_video_adapter.py
) else (
    python simple_blue_video_adapter.py --date %1
)

echo.
echo Press any key to exit...
pause > nul 