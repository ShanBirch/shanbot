@echo off
echo Starting Shanbot Services...
echo.

REM Change to the shanbot directory
cd /d "C:\Users\Shannon\OneDrive\Desktop\shanbot"

echo Starting webhook server in new window...
start "Shanbot Webhook" cmd /k "python -m uvicorn webhook0605:app --host 0.0.0.0 --port 8001 --reload"

echo Waiting 3 seconds before starting dashboard...
timeout /t 3 /nobreak > nul

echo Starting dashboard in new window...
start "Shanbot Dashboard" cmd /k "cd /d C:\Users\Shannon\OneDrive\Desktop\shanbot\app\dashboard_modules && python -m streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0"

echo.
echo Both services are starting!
echo.
echo Webhook will be available at: http://localhost:8001
echo Dashboard will be available at: http://localhost:8501
echo.
echo Close this window or press any key to continue...
pause 