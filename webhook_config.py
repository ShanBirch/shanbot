# Configuration for webhook_manychat23.py

# --- API Keys ---
MANYCHAT_API_KEY = "996573:5b6dc180662de1be343655db562ee918"
IG_GRAPH_ACCESS_TOKEN = "EAAJaUdyYIDgBO2TVUXn3nZChZBUEyJlkUi5oZCbVKm5TOMZA3l33bQaMZCRkiLNsZACYnxg8B1LarhVHeb0HmPQoAZBSEHfAw3B0ZAPHp1jx5Etp7TmarfSlfb5QJmMZCfIY7lDmRaqzhxtgxxGlniEukynpJoQHBKVK6ppbkRDjGTfUzVGwNvPEajwYScllwZACYZD"
# WARNING: Load API Key from environment variable for security!
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
GEMINI_API_KEY_FALLBACK = "AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y"

# --- File Paths ---
ANALYTICS_FILE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"
DAILY_TRACKER_FILE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\daily_tracker.json"
CHECKIN_REVIEWS_DIR = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output\checkin_reviews"
SHEETS_CREDENTIALS_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\sheets_credentials.json"
FFMPEG_PATH = r"C:\ffmpeg\ffmpeg.exe"
FFPROBE_PATH = r"C:\ffmpeg\ffprobe.exe"

# --- Google Sheets Configuration ---
SPREADSHEET_ID = "1nDVn6jhkYBubVTQqbYU3PKo_WooeuTsQzsaNNcQdJlo"
RANGE_NAME = "Sheet1!A:E"
ONBOARDING_SPREADSHEET_ID = "1038Ep0lYGEtpipNAIzH7RB67-KOAfXA-TcUTKBKqIfo"
ONBOARDING_RANGE_NAME = "Sheet1!A:AAF"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# --- Gemini Configuration ---
GEMINI_MODEL_PRO = "gemini-2.5-pro-exp-03-25"
GEMINI_MODEL_FLASH = "gemini-2.0-flash-thinking-exp-01-21"
GEMINI_MODEL_FLASH_STANDARD = "gemini-2.0-flash"
RETRY_DELAY = 16
MAX_RETRIES = 3

# --- Trainerize Credentials (Consider secure storage) ---
TRAINERIZE_USERNAME = "shannonbirch@cocospersonaltraining.com"
TRAINERIZE_PASSWORD = "cyywp7nyk2"

# --- ManyChat Buffering ---
BUFFER_WINDOW = 15

# --- Response Options ---
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

# --- Onboarding Trigger ---
ONBOARDING_TRIGGER_PHRASE = "get you onboarded"
