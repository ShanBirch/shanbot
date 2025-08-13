@echo off
echo Starting Social Media Video Enhancer...
echo.
echo DO NOT CLOSE THIS WINDOW WHILE YOUR VIDEO IS BEING PROCESSED
echo.
echo =======================================================
echo.

REM Run the Python script - using the simple version for greater reliability
python "%~dp0\social_media_enhancer_simple.py"

echo.
echo =======================================================
echo.
echo Video processing has completed or the application was closed.
echo Your enhanced video should be available in the same folder as the original.
echo.
echo Press any key to exit...
pause > nul 