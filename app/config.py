# app/config.py (cloud deployment configuration)
import os
import logging

# API Keys and Tokens - Using environment variables for cloud deployment
MANYCHAT_API_KEY = os.getenv(
    "MANYCHAT_API_KEY", "996573:5b6dc180662de1be343655db562ee918")
IG_GRAPH_ACCESS_TOKEN = os.getenv("INSTAGRAM_GRAPH_API_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini Model Configuration - Updated to stable models for cloud
GEMINI_MODEL_PRO = "gemini-2.0-flash-exp"
GEMINI_MODEL_FLASH = "gemini-1.5-flash"
GEMINI_MODEL_FLASH_STANDARD = "gemini-1.5-flash-8b"
RETRY_DELAY = 16
MAX_RETRIES = 3

# Cloud-compatible file paths (no local file dependencies)
SHEETS_CREDENTIALS_PATH = None  # Will use service account from env var
ANALYTICS_FILE_PATH = None  # Will use cloud storage/database
CHECKIN_REVIEWS_DIR = None  # Will use cloud storage

# Google Sheets Configuration
SPREADSHEET_ID = "1nDVn6jhkYBubVTQqbYU3PKo_WooeuTsQzsaNNcQdJlo"
ONBOARDING_SPREADSHEET_ID = "1038Ep0lYGEtpipNAIzH7RB67-KOAfXA-TcUTKBKqIfo"
RANGE_NAME = "Sheet1!A:E"
ONBOARDING_RANGE_NAME = "Sheet1!A:AAF"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# FFmpeg Configuration - Not needed in cloud (will use cloud services)
FFMPEG_PATH = None
FFPROBE_PATH = None

# Message Processing Configuration
BUFFER_WINDOW = 15  # seconds to wait for grouping messages

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Trainerize Credentials - Using environment variables
TRAINERIZE_USERNAME = os.getenv(
    "TRAINERIZE_USERNAME", "shannonbirch@cocospersonaltraining.com")
TRAINERIZE_PASSWORD = os.getenv("TRAINERIZE_PASSWORD", "cyywp7nyk2")

# Response Templates
FORM_CHECK_REQUEST_RESPONSES = [
    "Would love to, Send it through!",
    "Yeah keen! Flick it over.",
    "Sweet, send it my way.",
    "Yep, happy to take a look. Send it over.",
    "Awesome, send the video through when you're ready.",
    "Sure thing, let's see it.",
    "Keen to check it out, send it through!",
    "Easy, flick the video over.",
    "Yep, send it over and I'll have a look.",
    "Go for it, send the vid!"
]
