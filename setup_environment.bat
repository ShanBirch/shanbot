@echo off
echo Setting up Shanbot environment...

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    py -3.13 -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install required packages
echo Installing required packages...
python -m pip install --upgrade pip
pip install fastapi uvicorn pydantic requests google-generativeai streamlit pandas matplotlib selenium google-cloud-speech pydub python-dateutil google-api-python-client google-auth-httplib2 google-auth-oauthlib moviepy Pillow

echo Environment setup complete!
pause 