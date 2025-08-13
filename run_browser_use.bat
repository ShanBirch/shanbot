@echo off
echo Starting Browser-Use with Docker...
echo.

REM Set your OpenAI API key here (replace with your actual key)
set OPENAI_API_KEY=your_openai_key_here

REM Run Browser-Use Docker container
docker run -it --rm -p 7575:7575 -e OPENAI_API_KEY=%OPENAI_API_KEY% gregpr07/browser-use

echo.
echo Browser-Use container stopped.
pause