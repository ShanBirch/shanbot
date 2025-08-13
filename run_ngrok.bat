@echo off
echo Starting ngrok tunnel to port 8000...
:start
cd "C:\Users\Shannon\ngrok" 
ngrok http 8000
echo ngrok stopped or crashed. Restarting in 5 seconds...
timeout /t 5
goto start 