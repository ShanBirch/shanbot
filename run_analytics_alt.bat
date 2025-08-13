@echo off
cd C:\Users\Shannon\OneDrive\Desktop\shanbot
set PYTHONPATH=%PYTHONPATH%;%CD%
"C:\Users\Shannon\OneDrive\Desktop\shanbot\venv\Scripts\python.exe" -c "import streamlit.cli; streamlit.cli.main()" run app\analytics_dashboard.py 