@echo off
echo Starting ManyChat Webhook Service...
:start
cd "C:\Users\Shannon\OneDrive\Desktop\shanbot"
python -m app.manychat_webhook_fixed
echo Service stopped or crashed. Restarting in 5 seconds...
timeout /t 5
goto start 