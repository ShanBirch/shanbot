@echo off
set PYTHON_PATH="C:\Users\Shannon\OneDrive\Desktop\shanbot\venv\Scripts\python.exe"
call venv\Scripts\activate.bat
cd app
%PYTHON_PATH% -m webhook_manychat.py 