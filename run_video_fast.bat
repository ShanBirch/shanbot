@echo off
echo Running Optimized ShanBot Video Generation...

:: Check if a date parameter was provided
if "%~1"=="" (
    python simple_blue_video_optimized.py
) else (
    python simple_blue_video_optimized.py --date %1
)

echo.
echo Press any key to exit...
pause > nul 