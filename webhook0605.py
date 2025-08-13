# router with Wix onboarding endpoint
from trainerize_routes import router as trainerize_router
from wix_onboarding import router as wix_router
import functools  # Added for partial function application
from post_onboarding_handler import PostOnboardingHandler
from calorie_manager_calorietracker import CalorieTracker_CalorieTracker
from app.dashboard_modules.dashboard_sqlite_utils import add_response_to_review_queue, get_good_few_shot_examples, add_scheduled_response, create_scheduled_responses_table_if_not_exists, get_db_connection
from conversation_strategy import get_conversation_strategy_for_user, log_strategy_usage
from webhook_handlers import (
    get_melbourne_time_str,
    format_conversation_history,
    split_response_into_messages,
    load_json_data,
    transcribe_audio_with_google,
    analyze_media_url,
    process_conversation_for_media,
    get_ai_response,
    update_manychat_fields,
    call_gemini_with_retry,
    get_user_data,
    update_analytics_data,
    add_todo_item,
    get_checkin_data,
    find_latest_checkin_file,
    build_member_chat_prompt,
    send_manychat_message,
    get_username_from_manychat
)
from pathlib import Path  # Added for robust path handling
import re  # Added for date parsing in find_latest_checkin_file
import glob  # Added for finding check-in files
from calorietracker import get_calorie_analysis
from techniqueanalysis import get_video_analysis
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import random
import tempfile
import io
from google.cloud import speech_v1
from pydantic import BaseModel, Field
from pb import TrainerizeAutomation
import httpx
import dateutil.parser as parser
from collections import defaultdict
import asyncio  # Added to allow async delays between messages
from fastapi.middleware.cors import CORSMiddleware  # Add this import
import time
from app import prompts  # Import prompts from the app package
import pytz  # Make sure pytz is imported
from datetime import datetime, timezone, timedelta
import re
import googleapiclient.discovery
import google.oauth2.service_account
import google.generativeai as genai  # Added Gemini import
from fastapi import FastAPI, Request, HTTPException, Header, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse, Response
import uvicorn
import hmac
import hashlib
import logging
import requests
import json
from typing import Dict, Any, List, Optional, Tuple, Union
import asyncio
import sys
import os
import app.dashboard_modules.dashboard_sqlite_utils as db_utils
from app.dashboard_modules.auto_mode_state import is_auto_mode_active
import traceback
import re as _re_chal
from app.dashboard_modules.notifications import add_email_collected_notification

# Set up logging FIRST - before any other code that might use logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("manychat_webhook")
logger.info("Logging configured.")  # Confirm logging setup

# Suppress watchfiles spam in development mode
logging.getLogger("watchfiles.main").setLevel(logging.WARNING)

# Add the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the background bio fetcher
try:
    from background_bio_fetcher import start_background_bio_fetcher
    BIO_FETCHER_AVAILABLE = True
    logger.info("Background Bio Fetcher imported successfully")
except ImportError as e:
    BIO_FETCHER_AVAILABLE = False
    logger.warning(f"Background Bio Fetcher not available: {e}")

# Import for on-demand bio analysis
try:
    import subprocess
    import tempfile
    BIO_ANALYSIS_AVAILABLE = True
    logger.info("Bio analysis functionality available")
except ImportError as e:
    BIO_ANALYSIS_AVAILABLE = False
    logger.warning(f"Bio analysis not available: {e}")

# Original imports start here
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# Add Google Sheets imports
# Added import for technique analysis
# Added import for calorie analysis
# Import handlers from webhook_handlers.py
# Import the new function for queuing reviews

# Add import at the top

# New obvious startup message
logger.info("=== UPDATED VERSION WITH ONBOARDING DETECTION LOADED ===")

# Initialize audio processing flag
AUDIO_PROCESSING_AVAILABLE = False
try:
    import subprocess
    import tempfile
    AUDIO_PROCESSING_AVAILABLE = True
    logger.info("Audio processing is available using ffmpeg")
except ImportError:
    logger.warning(
        "Audio processing is not available - voice messages will be handled differently")

# Configure FFmpeg paths
FFMPEG_PATH = r"C:\ffmpeg\ffmpeg.exe"
FFPROBE_PATH = r"C:\ffmpeg\ffprobe.exe"
os.environ["FFMPEG_BINARY"] = FFMPEG_PATH
os.environ["FFPROBE_BINARY"] = FFPROBE_PATH

# Download FFmpeg if not present
if not os.path.exists(FFMPEG_PATH) or not os.path.exists(FFPROBE_PATH):
    try:
        import urllib.request
        import zipfile

        # Download FFmpeg
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        zip_path = r"C:\ffmpeg\ffmpeg.zip"

        if not os.path.exists(r"C:\ffmpeg"):
            os.makedirs(r"C:\ffmpeg")

        print("Downloading FFmpeg...")
        urllib.request.urlretrieve(ffmpeg_url, zip_path)

        print("Extracting FFmpeg...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(r"C:\ffmpeg")

        # Move files to correct location
        import shutil
        ffmpeg_dir = next(d for d in os.listdir(
            r"C:\ffmpeg") if d.startswith("ffmpeg"))
        shutil.move(os.path.join(r"C:\ffmpeg", ffmpeg_dir,
                    "bin", "ffmpeg.exe"), FFMPEG_PATH)
        shutil.move(os.path.join(r"C:\ffmpeg", ffmpeg_dir,
                    "bin", "ffprobe.exe"), FFPROBE_PATH)

        print("FFmpeg setup complete!")
    except Exception as e:
        print(f"Error setting up FFmpeg: {e}")

ig_usernames: Dict[str, str] = {}

# --- Add PIL for image type check ---
# Make sure these are added near the top with other imports
try:
    import PIL
    from PIL import Image
    import io
    PIL_AVAILABLE = True
    logger.info("PIL library found. Image verification enabled.")
except ImportError:
    PIL_AVAILABLE = False
    logger.warning(
        "PIL library not found. Image verification will be skipped.")
# --- End PIL Import ---

# --- Pydantic Models for Trainerize Actions ---


class ExerciseDefinition(BaseModel):
    name: str
    sets: str
    reps: str


class WorkoutDefinition(BaseModel):
    day_type: str = Field(..., description="Type of workout day. Supported values: 'back', 'chest_tris', 'shoulders_core', 'legs', 'arms_core'.")
    exercises_list: List[ExerciseDefinition]


class BuildProgramRequest(BaseModel):
    client_name: str
    program_name: str
    workout_definitions: List[WorkoutDefinition]


# --- FastAPI App Definition ---
app = FastAPI(title="Instagram Webhook Receiver")  # Renamed title

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Include external routers ---
app.include_router(wix_router)

# Initialize background bio fetcher on startup


@app.on_event("startup")
async def startup_event():
    """Initialize background services when the app starts"""
    logger.info("=== INITIALIZING BACKGROUND SERVICES ===")

    # Removed bulk Auto Instagram Analyzer - now using on-demand analysis per webhook
    logger.info("📊 Bio analysis will run on-demand per user webhook request")
    logger.info(
        "✅ This prevents bulk processing bottlenecks and improves webhook responsiveness")

    logger.info("=== BACKGROUND SERVICES INITIALIZATION COMPLETE ===")


async def check_and_trigger_bio_analysis(ig_username: str, subscriber_id: Optional[str] = None):
    """
    Check if user has bio analysis data, and trigger analysis if missing.
    This runs as a background task to not block webhook response.
    """
    if not BIO_ANALYSIS_AVAILABLE:
        logger.debug(f"Bio analysis not available for {ig_username}")
        return

    # Validate that ig_username is a real Instagram username, not a placeholder
    if not ig_username or not ig_username.strip():
        logger.warning(f"❌ Cannot trigger analysis: empty username")
        return

    # Check if username is a placeholder format (user_XXXXX)
    if ig_username.startswith('user_') and ig_username[5:].isdigit():
        logger.warning(
            f"❌ Cannot trigger analysis for placeholder username: {ig_username}")
        logger.info(
            f"🔧 Attempting to fetch real username from ManyChat API for subscriber {subscriber_id}")

        # Try to get real username from ManyChat API if subscriber_id is available
        if subscriber_id:
            try:
                from webhook_handlers import get_username_from_manychat
                real_username = await get_username_from_manychat(subscriber_id)
                if real_username and not (real_username.startswith('user_') and real_username[5:].isdigit()):
                    logger.info(
                        f"✅ Found real username from API: {real_username}")
                    ig_username = real_username  # Use the real username
                else:
                    logger.warning(
                        f"❌ Could not get valid username from ManyChat API for {subscriber_id}")
                    return
            except Exception as e:
                logger.error(
                    f"❌ Error fetching username from ManyChat API: {e}")
                return
        else:
            logger.warning(
                f"❌ No subscriber_id provided to fetch real username")
            return

    try:
        logger.info(f"🔍 Checking bio analysis status for {ig_username}")

        # NEW: Check bio_analysis_status first
        conn = get_db_connection()
        cursor = conn.cursor()

        # NEW: Check bio_analysis_status first
        cursor.execute(
            "SELECT bio_analysis_status FROM users WHERE ig_username = ?",
            (ig_username,)
        )
        status_result = cursor.fetchone()
        bio_analysis_status = status_result[0] if status_result else None

        if bio_analysis_status in [
            'completed',
            'failed_no_posts',
            'failed_private_profile',
            'failed_not_accessible',
            'failed_ai_analysis',
            'failed_post_processing_error',
            'failed_general_error'
        ]:
            logger.info(
                f"✅ Skipping Instagram analysis for {ig_username} because status is '{bio_analysis_status}'")
            conn.close()
            return

        # Check if user has complete Instagram analysis in SQLite
        cursor.execute(
            "SELECT metrics_json FROM users WHERE ig_username = ?",
            (ig_username,)
        )
        result = cursor.fetchone()
        conn.close()

        has_bio_analysis = False
        if result and result[0]:
            try:
                metrics_data = json.loads(result[0])
                client_analysis = metrics_data.get('client_analysis', {})

                # Check for key bio analysis fields and ensure not just an empty dict/list if analysis was partial
                if (client_analysis.get('interests') and
                    client_analysis.get('conversation_topics') and
                        client_analysis.get('posts_analyzed', 0) > 0):
                    has_bio_analysis = True
                    logger.info(
                        f"✅ {ig_username} already has bio analysis data")
                else:
                    logger.info(
                        f"📊 {ig_username} has partial or missing bio analysis (posts: {client_analysis.get('posts_analyzed', 0)}, interests: {len(client_analysis.get('interests', []))}) ")
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"⚠️ {ig_username} has corrupted metrics data")

        if not has_bio_analysis:
            # If analysis is not complete, and not already explicitly failed, trigger it
            logger.info(f"🚀 Triggering Instagram analysis for {ig_username}")
            await trigger_instagram_analysis_for_user(ig_username)
        else:
            logger.debug(f"✅ {ig_username} already has complete bio analysis")

    except Exception as e:
        logger.error(
            f"❌ Error checking bio analysis for {ig_username}: {e}", exc_info=True)


async def trigger_instagram_analysis_for_user(ig_username: str):
    """
    Trigger Instagram analysis for a specific user by calling analyze_followers.py
    Runs in background to not block webhook processing.
    """
    try:
        logger.info(f"🔄 Starting Instagram analysis for {ig_username}")

        # Path to the analyzer script
        analyzer_script_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\anaylize_followers.py"

        if not os.path.exists(analyzer_script_path):
            logger.error(
                f"❌ Analyzer script not found at {analyzer_script_path}")
            return

        # Use --direct-user flag instead of creating temporary file
        cmd = [
            "python", analyzer_script_path,
            "--direct-user", ig_username
        ]

        logger.info(f"🎯 Running analysis command: {' '.join(cmd)}")

        # Start the process in a new terminal window using cmd /k so you can see what's happening
        # Use cmd /k to keep the window open and show output
        cmd_with_terminal = ["cmd", "/k"] + cmd

        process = subprocess.Popen(
            cmd_with_terminal,
            cwd=os.path.dirname(analyzer_script_path),
            creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(
                subprocess, 'CREATE_NEW_CONSOLE') else 0
        )

        # Just start it and return - don't wait for completion to avoid blocking webhook
        logger.info(
            f"✅ Instagram analysis started for {ig_username} in new terminal window")

        return  # Exit early - don't wait for completion

    except Exception as e:
        logger.error(
            f"❌ Error triggering Instagram analysis for {ig_username}: {e}", exc_info=True)


# Your ManyChat API key
MANYCHAT_API_KEY = "996573:5b6dc180662de1be343655db562ee918"
# Instagram Graph API token (reuse your Page token) for username lookups
IG_GRAPH_ACCESS_TOKEN = "EAAJaUdyYIDgBO2TVUXn3nZChZBUEyJlkUi5oZCbVKm5TOMZA3l33bQaMZCRkiLNsZACYnxg8B1LarhVHeb0HmPQoAZBSEHfAw3B0ZAPHp1jx5Etp7TmarfSlfb5QJmMZCfIY7lDmRaqzhxtgxxGlniEukynpJoQHBKVK6ppbkRDjGTfUzVGwNvPEajwYScllwZACYZD"

# --- Google Sheets Configuration START ---
# Path to your credentials file
SHEETS_CREDENTIALS_PATH = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\sheets_credentials.json"
# The ID of your spreadsheet (General Chat)
SPREADSHEET_ID = "1nDVn6jhkYBubVTQqbYU3PKo_WooeuTsQzsaNNcQdJlo"
# The range containing the data - CHANGED to include Column E
RANGE_NAME = "Sheet1!A:E"

# Define the scopes required - Read-only is sufficient
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
# --- Google Sheets Configuration END ---

# --- ADDED: Check-in Review Directory --- START ---
CHECKIN_REVIEWS_DIR = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\output\\checkin_reviews"  # Corrected path
# --- ADDED: Check-in Review Directory --- END ---

# --- Gemini Configuration START ---
# WARNING: Load API Key from environment variable for security!
# Using your provided key as fallback
GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY", "AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y")
if not GEMINI_API_KEY:
    logger.warning(
        "GEMINI_API_KEY environment variable not set. Gemini calls will fail.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {e}", exc_info=True)

# Choose your Gemini model
# Main model (experimental version)
GEMINI_MODEL_PRO = "gemini-2.5-pro-exp-03-25"
# First fallback model (flash thinking)
GEMINI_MODEL_FLASH = "gemini-2.0-flash-thinking-exp-01-21"
# Second fallback model (standard flash)
GEMINI_MODEL_FLASH_STANDARD = "gemini-2.0-flash"
RETRY_DELAY = 16  # Seconds to wait before retry
MAX_RETRIES = 3  # Maximum number of retry attempts


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}

# --- ADDED: Intent Detection Function Stub --- START ---

# Global dictionary to store program information between messages
program_info = {}

# Global dictionary to track pending form check requests
form_check_pending: Dict[str, bool] = {}
# Global dictionary to track pending food analysis photo requests
food_analysis_pending: Dict[str, bool] = {}

# --- Response Options --- (New List)
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

# --- Helper Function to Add "To Do" Item --- START ---


# --- Helper Function to Add "To Do" Item --- END ---


async def detect_and_handle_action(ig_username: str, message_text: str, subscriber_id: Optional[str] = None, data: Dict = None, batch_start_time_s: float = None) -> bool:
    """Uses Gemini to detect user intent and handles multiple actions like Trainerize edits or food analysis within one message."""
    logger.info(
        f"[detect_and_handle_action] Analyzing message from {ig_username} for multiple actions: {message_text[:100]}"
    )
    # Ensure batch_start_time_s has a default if not passed, though it always should be from _handle_buffered_messages_for_subscriber
    if batch_start_time_s is None:
        # Fallback, but indicates a potential logic error if this happens
        batch_start_time_s = time.time()
        logger.warning(
            f"[detect_and_handle_action] batch_start_time_s was None for SID {subscriber_id}. Defaulting to now. This might lead to inaccurate response time.")

    if not data:
        logger.error("No data dictionary provided to detect_and_handle_action")
        return False

    # --- ONBOARDING STATUS LOGGING (Revised from ONBOARDING CHECK) --- START ---
    logger.info(
        f"[detect_and_handle_action] Checking current onboarding status for {ig_username} (SubID: {subscriber_id}) for logging and context.")

    local_metrics_dict_for_onboarding_status = {}  # Default
    is_onboarding_status_for_log = False  # Default
    try:
        # Fetch fresh metrics to log current onboarding status; this doesn't alter main flow decision here
        # This call is primarily for logging the current state accurately at this point.
        _, local_metrics_dict_for_onboarding_status, _ = get_user_data(
            ig_username, subscriber_id)

        if local_metrics_dict_for_onboarding_status:
            is_onboarding_status_for_log = local_metrics_dict_for_onboarding_status.get(
                'is_onboarding', False)
            logger.info(
                f"[detect_and_handle_action] Current onboarding flag for {ig_username} is: {is_onboarding_status_for_log}.")
        elif not local_metrics_dict_for_onboarding_status:
            logger.warning(
                f"[detect_and_handle_action] Could not retrieve user data to log onboarding status for {ig_username} (SubID: {subscriber_id}). Assuming not onboarding for internal checks if data is missing.")
    except Exception as e:
        logger.error(
            f"[detect_and_handle_action] Error fetching user data for onboarding status logging: {str(e)}")

    # IMPORTANT: The function NO LONGER returns early based on is_onboarding_status_for_log.
    # It will now proceed to the main intent detection logic below.
    # The decision to use ONBOARDING_PROMPT_TEMPLATE or general prompts occurs
    # later in _handle_buffered_messages_for_subscriber if this function returns False.

    logger.info(
        f"[detect_and_handle_action] Proceeding with specific intent detection for {ig_username}.")
    # --- ONBOARDING STATUS LOGGING --- END ---

    intent_prompt = f"""Analyze this message to identify ALL requested actions:
1. Workout program changes (adding or removing exercises).
2. Requests for a form check/technique analysis based on a video.
3. Requests for calorie/macro analysis of food based on an image.
4. Requests for calorie tracking or monitoring.

Message: "{message_text}"

--- Workout Changes ---
Standard Workout Day Categories & Target Output Types:
- Leg Day (keywords: leg, legs, lower body) -> output type: "Leg Day"
- Back day (keywords: back, pull) -> output type: "Back day"
- Chest day (keywords: chest, push) -> output type: "Chest day"
- Core Day (keywords: core, abs, abdominals) -> output type: "Core Day"
- Shoulder Day (keywords: shoulders, delts) -> output type: "Shoulder Day"
- Cardio Day (keywords: cardio, run, bike, conditioning) -> output type: "Cardio Day"
- Arm Day (keywords: arms, biceps, triceps) -> output type: "Arm Day"

--- Form Check Requests ---
Form Check Keywords: form check, check form, technique, review video, analyse video, look at my lift

--- Calorie/Macro Analysis Requests ---
Food Analysis Keywords: calories, macros, check food, analyse meal, how much protein/carbs/fat, food pic

--- Calorie Tracking Requests ---
Tracking Keywords: track calories

--- Output Format ---
IMPORTANT: You MUST respond with ONLY a valid JSON object. Do not include any additional text or formatting.
The JSON object MUST follow this EXACT structure:
{{
    "is_workout_request": boolean,
    "is_form_check_request": boolean,
    "is_food_analysis_request": boolean,
    "is_calorie_tracking_request": boolean,
    "actions": [
        {{
            "action": "add" or "remove",
            "exercise": "exercise name",
            "workout_type": "exact workout day category",
            "sets": "3",
            "reps": "10"
        }}
    ],
    "has_image_url": boolean,
    "confidence": number between 0 and 100,
    "explanation": "brief explanation"
}}"""

    try:
        # Get intent analysis from Gemini
        intent_response = await call_gemini_with_retry(GEMINI_MODEL_FLASH, intent_prompt)
        if not intent_response:
            logger.error("Failed to get intent analysis from Gemini")
            return False

        # Clean the response of any markdown formatting
        cleaned_response = intent_response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[len("```json"):].strip()
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[len("```"):].strip()
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-len("```")].strip()

            # Find the first '{' and the last '}'
            first_brace_index = cleaned_response.find('{')
            last_brace_index = cleaned_response.rfind('}')

            if first_brace_index != -1 and last_brace_index != -1 and last_brace_index > first_brace_index:
                potential_json_str = cleaned_response[first_brace_index:last_brace_index + 1]
                potential_json_str = re.sub(
                    r'\s+immunotherapy\s*\]', ']', potential_json_str)
                potential_json_str = re.sub(
                    r',(\s*[}\]])', r'\1', potential_json_str)
                potential_json_str = re.sub(
                    r'}\s*,\s*]', '}]', potential_json_str)

                try:
                    intent_data = json.loads(potential_json_str)
                    logger.info(
                        f"Successfully parsed intent data: {json.dumps(intent_data, indent=2)}")
                except json.JSONDecodeError as json_err:
                    logger.error(
                        f"Failed to parse the JSON block after cleaning: {json_err}")
                    return False
            else:
                logger.error(
                    "Could not find valid JSON braces in the response")
                return False

            # Extract data from analysis
            is_workout_req = intent_data.get('is_workout_request', False)
            is_form_check_req = intent_data.get('is_form_check_request', False)
            is_food_analysis_req = intent_data.get(
                'is_food_analysis_request', False)
            is_calorie_tracking_req = intent_data.get(
                'is_calorie_tracking_request', False)
            has_image_url = intent_data.get('has_image_url', False)
            confidence = intent_data.get('confidence', 0)
            requested_actions = intent_data.get('actions', [])
            # subscriber_id is now a direct parameter
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')

            # Define these early as they are used by multiple intent blocks
            client_name_for_todo = data.get(
                'name') or f"{first_name} {last_name}".strip() or ig_username

            extracted_video_url = None
            user_desc_text = message_text  # Default to full message_text

            url_pattern = r"(https?://lookaside\.fbsbx\.com/ig_messaging_cdn/\?asset_id=[\w-]+&signature=[\w\-_.~]+)"
            match = re.search(url_pattern, message_text)
            if match:
                extracted_video_url = match.group(1)
                logger.info(
                    f"Regex extracted a media URL: {extracted_video_url[:100]}...")
                # Update user_desc_text if a URL was found and removed
                user_desc_text = message_text.replace(
                    extracted_video_url, "").strip()

            # --- PRIORITY: Handle PENDING form check if a video is now supplied ---
            if form_check_pending.get(ig_username) and extracted_video_url:
                logger.info(
                    f"Form check was PENDING for {ig_username} and a video URL was found in current message. Prioritizing analysis.")
                user_msg_for_analytics, ai_resp_for_analytics = await _analyze_form_check_video(
                    ig_username,
                    client_name_for_todo,
                    extracted_video_url,
                    user_desc_text,
                    subscriber_id,
                    batch_start_time_s
                )
                form_check_pending.pop(ig_username, None)  # Clear pending flag
                update_analytics_data(
                    ig_username,
                    user_msg_for_analytics,
                    ai_resp_for_analytics,
                    subscriber_id,
                    first_name,
                    last_name
                )
                logger.info(
                    f"Updated analytics after form check video analysis (PRIORITY PENDING) for {ig_username}")
                return True  # Action handled

            # Check message type and content (original placement)
            has_transcription = "Audio transcription:" in message_text
            has_video = "Video Content:" in message_text
            is_workout_message = is_workout_req and confidence > 70

            # --- MODIFIED: Handle workout requests from any source (text, audio, or video) ---
            if is_workout_message:
                logger.info(
                    f"Processing workout request for {ig_username} (Source: {'Video' if has_video else 'Audio' if has_transcription else 'Text'})")

                # Rest of workout handling code...
                if not requested_actions:
                    logger.warning(
                        "Workout request detected, but no actions found in the list.")
                    return False

                can_proceed = False
                target_workout_type = None
                for action_item in requested_actions:
                    action = action_item.get('action') or action_item.get(
                        'action_type') or action_item.get('type')
                    exercise = action_item.get(
                        'exercise_name') or action_item.get('exercise')
                    if action_item.get('workout_type') and exercise and action:
                        can_proceed = True
                        target_workout_type = action_item.get('workout_type')
                        break

                if not can_proceed:
                    logger.warning(
                        "Detected workout request, but missing essential details.")
                    clarification_message = ("I think you want to change your workout, but I missed some details. "
                                             "Can you please tell me the specific exercise, the action (add/remove), "
                                             "and the workout day (e.g., Legs, Back)?")

                    if subscriber_id:
                        field_updates = {
                            "o1 Response": clarification_message,
                            "CONVERSATION": message_text,
                            "response time": "action"  # Explicitly set for workout changes
                        }
                        update_success = update_manychat_fields(
                            subscriber_id, field_updates)
                        if not update_success:
                            logger.error(
                                f"Failed to send clarification request to ManyChat for {ig_username}")

                        update_analytics_data(
                            ig_username,
                            user_message=message_text,
                            ai_response=clarification_message,
                            subscriber_id=subscriber_id,
                            first_name=first_name,
                            last_name=last_name
                        )
                        logger.info(
                            f"Sent clarification request and updated analytics for {ig_username}.")
                        return True
                    else:
                        logger.error(
                            f"Cannot send clarification request for {ig_username}, missing subscriber_id.")
                        return False

                # Get client details
                client_full_name = data.get(
                    'name') or f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
                if not client_full_name or not subscriber_id:
                    logger.error(
                        "Missing client name or subscriber ID for Trainerize automation.")
                    return False

                logger.info(
                    f"Attempting Trainerize modifications for {client_full_name} based on {len(requested_actions)} actions...")

                trainerize = None
                modification_attempted_and_failed = False
                action_summary = {"success": [], "failed": []}
                overall_success = False

                try:
                    # Trainerize Login and Navigation
                    trainerize = TrainerizeAutomation()
                    username = "shannonbirch@cocospersonaltraining.com"
                    password = "cyywp7nyk2"

                    if not trainerize.login(username, password):
                        raise Exception("Failed to login to Trainerize")
                    trainerize.handle_notification_popup()

                    if not trainerize.navigate_to_client(client_full_name):
                        raise Exception("Failed to navigate to client")

                    if not trainerize.navigate_to_training_program():
                        raise Exception(
                            "Failed to navigate to training program")

                    if not target_workout_type:
                        raise Exception(
                            "Target workout type could not be determined.")

                    if not trainerize.click_workout_fuzzy(target_workout_type):
                        exact_workout_name = f"{target_workout_type.title()} Day"
                        raise Exception(
                            f"Failed to find workout containing '{target_workout_type}' using fuzzy match (tried exact: {exact_workout_name})")

                    if not trainerize.click_edit_workout():
                        raise Exception("Failed to enter edit mode")

                    # Process each action
                    for i, action_item in enumerate(requested_actions):
                        action_type = action_item.get('action') or action_item.get(
                            'action_type') or action_item.get('type')
                        exercise_name = action_item.get('exercise_name') or action_item.get(
                            'exercise')
                        current_workout_type = action_item.get('workout_type')

                        if current_workout_type != target_workout_type:
                            logger.warning(
                                f"Action {i+1} workout type '{current_workout_type}' differs from navigated type '{target_workout_type}'. Proceeding anyway.")

                        if not action_type or not exercise_name:
                            logger.warning(
                                f"Skipping invalid action item {i+1}: Missing action/action_type or exercise_name/exercise.")
                            action_summary["failed"].append(
                                f"Item {i+1} (invalid details)")
                            continue

                        logger.info(
                            f"--- Performing Action {i+1}/{len(requested_actions)}: {action_type.upper()} '{exercise_name}' ---")
                        action_successful_this_time = False
                        try:
                            if action_type == 'add':
                                sets = action_item.get('sets', '3')
                                reps = action_item.get('reps', '10')
                                if trainerize.add_exercise(exercise_name, sets, reps):
                                    action_successful_this_time = True
                                    logger.info(
                                        f"Action {i+1} SUCCEEDED: Added '{exercise_name}'")
                                else:
                                    logger.error(
                                        f"Action {i+1} FAILED: Could not add '{exercise_name}'")
                            elif action_type == 'remove':
                                if trainerize.remove_exercise(exercise_name):
                                    action_successful_this_time = True
                                    logger.info(
                                        f"Action {i+1} SUCCEEDED: Removed '{exercise_name}'")
                                else:
                                    logger.error(
                                        f"Action {i+1} FAILED: Could not remove '{exercise_name}'")
                            else:
                                logger.error(
                                    f"Action {i+1} FAILED: Unknown action type '{action_type}'")

                        except Exception as loop_e:
                            logger.error(
                                f"Action {i+1} ({action_type} '{exercise_name}') FAILED with exception: {loop_e}")

                        if action_successful_this_time:
                            action_summary["success"].append(
                                f"{action_type} {exercise_name}")
                        else:
                            action_summary["failed"].append(
                                f"{action_type} {exercise_name}")

                    # Save changes
                    logger.info(
                        "Attempting to save workout after processing all actions...")
                    if trainerize.save_workout():
                        logger.info("Workout saved successfully.")
                        overall_success = True
                    else:
                        logger.error(
                            "Failed to save workout after modifications!")
                        overall_success = False

                except Exception as e:
                    error_message = f"Error during Trainerize automation: {str(e)}"
                    logger.error(error_message)
                    add_todo_item(ig_username, client_full_name,
                                  f"Trainerize automation failed: {str(e)[:100]}...")
                    action_summary["failed"].append(
                        f"Overall process failed ({str(e)[:50]}...)")
                    modification_attempted_and_failed = True

                finally:
                    if trainerize:
                        if not modification_attempted_and_failed and overall_success:
                            logger.info(
                                "Trainerize modifications successful, cleaning up.")
                            trainerize.cleanup()
                        else:
                            logger.warning(
                                "Trainerize modification had failures or save failed! Leaving browser open.")
                            fail_reason = "Save workout failed" if not overall_success else f"Action(s) failed: {action_summary['failed']}"
                            add_todo_item(ig_username, client_full_name,
                                          f"Trainerize issue: {fail_reason}")
                            print(
                                "\n*** Trainerize browser window left open due to error or failed save. Please close it manually. ***\n")

                # Construct response
                if overall_success and not action_summary["failed"]:
                    response = "Easy updated your program, need anything else?"
                    success_desc = f"Successfully performed Trainerize actions: {action_summary['success']}"
                    add_todo_item(ig_username, client_full_name,
                                  success_desc, status="completed")
                else:
                    response = "Yep ill get onto that asap and get back to you when its done!"

                # Update ManyChat and analytics
                field_updates = {
                    "o1 Response": response,
                    "CONVERSATION": message_text,
                    "response time": "action"  # Explicitly set for workout changes
                }
                update_success = update_manychat_fields(
                    subscriber_id, field_updates)
                if not update_success:
                    logger.error(
                        f"Failed to update ManyChat fields for {ig_username}")

                ai_response_for_analytics = f"Attempted actions: Success={action_summary['success']}, Failed={action_summary['failed']}, Save Success={overall_success}"
                update_analytics_data(ig_username, message_text,
                                      ai_response_for_analytics,
                                      subscriber_id, first_name, last_name)
                logger.info(
                    f"Updated analytics data for {ig_username} with action summary.")

                # --- ONBOARDING TRIGGER DETECTION (within workout change) ---
                onboarding_trigger_phrase = "get you onboarded"
                start_onboarding = False
                if ai_response_for_analytics and onboarding_trigger_phrase in ai_response_for_analytics.lower():
                    start_onboarding = True
                    logger.info(
                        f"[ONBOARDING] Trigger phrase detected for {ig_username}")

                if start_onboarding:
                    # Load analytics data
                    analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
                    analytics_update_successful = False
                    try:
                        with open(analytics_file_path, "r") as f:
                            analytics_data = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        logger.error(
                            f"[ONBOARDING] Failed to load analytics data for onboarding.")
                        analytics_data = {"conversations": {}}
                    # Find user
                    target_user_id = None
                    conversations_data = analytics_data.get(
                        'conversations', {})
                    search_ig_username_lower = ig_username.strip().lower()
                    for user_id, user_data_loop in conversations_data.items():
                        if isinstance(user_data_loop, dict):
                            metrics_data = user_data_loop.get("metrics", {})
                            if isinstance(metrics_data, dict):
                                json_ig_username = metrics_data.get(
                                    "ig_username", None)
                                if isinstance(json_ig_username, str) and json_ig_username.strip().lower() == search_ig_username_lower:
                                    target_user_id = user_id
                                    break
                    if target_user_id and target_user_id in conversations_data:
                        metrics_to_update = conversations_data[target_user_id].setdefault(
                            'metrics', {})
                        if not metrics_to_update.get('is_onboarding', False):
                            metrics_to_update['is_onboarding'] = True
                            metrics_to_update['expected_onboarding_input'] = "all_meals"
                            # Optionally clear previous target calculations if re-onboarding
                            metrics_to_update.pop('target_calories', None)
                            metrics_to_update.pop('target_protein', None)
                            metrics_to_update.pop('target_carbs', None)
                            metrics_to_update.pop('target_fats', None)
                            logger.info(
                                f"[ONBOARDING] Set onboarding state for user {target_user_id}")
                            with open(analytics_file_path, "w") as f:
                                json.dump(analytics_data, f, indent=2)
                            logger.info(
                                f"[ONBOARDING] Saved updated onboarding state for {target_user_id}")
                            analytics_update_successful = True
                        else:
                            logger.info(
                                f"[ONBOARDING] User {target_user_id} already has onboarding set.")
                    else:
                        logger.error(
                            f"[ONBOARDING] Could not find user {ig_username} in analytics data to start onboarding.")
                    # Send onboarding question if successful
                    if analytics_update_successful:
                        first_onboarding_question = "Awesome, let's get you onboarded. Ill sought it all out for you, first thing to do is write you up a quick 2-day meal plan, whats your go to meals? Breakfast lunch, dinner, do you know 2 of each?"
                        onboarding_field_updates = {
                            "o1 Response": first_onboarding_question,
                            "CONVERSATION": message_text
                        }
                        # Ensure subscriber_id for sending message is available
                        # 'data' is the payload for the current message being processed by detect_and_handle_action
                        # Prioritize data['id'] if available
                        subscriber_id_for_mc = data.get(
                            'id') if data else subscriber_id
                        if not subscriber_id_for_mc:
                            logger.error(
                                "[ONBOARDING] Critical: subscriber_id missing for sending onboarding message.")
                        else:
                            onboarding_update_success = update_manychat_fields(
                                subscriber_id_for_mc, onboarding_field_updates)
                            if not onboarding_update_success:
                                logger.error(
                                    f"[ONBOARDING] Failed to send first onboarding question to {ig_username} (SubID: {subscriber_id_for_mc})")
                            else:
                                logger.info(
                                    f"[ONBOARDING] Sent first onboarding question to {ig_username} (SubID: {subscriber_id_for_mc})")
                                # Track bot send time
                                manychat_last_bot_sent_timestamps[subscriber_id_for_mc] = time.time(
                                )

                        # Update analytics history
                        onboarding_ai_response = "[Onboarding Triggered by Workout Change - Asking about go-to meals]"
                        update_analytics_data(
                            ig_username=ig_username,
                            user_message=message_text,  # Original user message
                            ai_response=onboarding_ai_response,
                            subscriber_id=subscriber_id_for_mc,  # Use the same subscriber_id
                            first_name=data.get(
                                "first_name", "") if data else "",
                            last_name=data.get(
                                "last_name", "") if data else "",
                            set_checkin_flow_false=False
                        )
                        logger.info(
                            f"[ONBOARDING] Updated analytics history for {ig_username} to reflect onboarding start (triggered by workout change flow).")
                        # Action handled (onboarding started as part of workout change)
                return True
                # --- END ONBOARDING TRIGGER DETECTION (within workout change) ---

                return True  # Workout change action handled

            # Handle Form Check Request (REVISED LOGIC - Priority pending check is now above)
            elif is_form_check_req and confidence > 70 and not is_workout_message:
                logger.info(
                    f"Form Check Request path entered for {ig_username}. Confidence: {confidence}, Initial has_image_url from intent: {has_image_url}, form_check_pending: {form_check_pending.get(ig_username)}")
                # client_name_for_todo, extracted_video_url, user_desc_text are already defined above

                # Scenario 1: Initial form check request (NOT pending) AND a video is present in THIS message
                if not form_check_pending.get(ig_username) and extracted_video_url:
                    logger.info(
                        f"Initial form check request from {ig_username} WITH video URL (not pending). Analyzing.")
                    user_msg_for_analytics, ai_resp_for_analytics = await _analyze_form_check_video(
                        ig_username, client_name_for_todo, extracted_video_url, user_desc_text, subscriber_id, batch_start_time_s)

                    update_analytics_data(
                        ig_username,
                        user_msg_for_analytics,
                        ai_resp_for_analytics,
                        subscriber_id,
                        first_name,
                        last_name
                    )
                    logger.info(
                        f"Updated analytics after form check video analysis (initial with video) for {ig_username}")
                    return True  # Action handled (analysis attempted)

                # Scenario 2: Form check requested (high confidence on THIS message), but NO video in THIS current message
                # And is_form_check_req is true (from main elif condition)
                elif not extracted_video_url:
                    # And not already pending
                    if not form_check_pending.get(ig_username):
                        logger.info(
                            f"Initial form check request from {ig_username}, no video in this message. Asking and setting pending.")
                        form_check_pending[ig_username] = True
                        response_text = random.choice(
                            FORM_CHECK_REQUEST_RESPONSES)

                        # New: Set response time to "action"
                        response_time_value = "action"
                        if update_manychat_fields(subscriber_id, {"response time": response_time_value}):
                            logger.info(
                                f"Successfully set 'response time' to '{response_time_value}' for SID {subscriber_id} (form check ask)")
                            # Short delay
                            await asyncio.sleep(random.uniform(1, 2))
                        else:
                            logger.error(
                                f"Failed to set 'response time' for SID {subscriber_id} (form check ask)")

                        field_updates = {
                            "o1 Response": response_text, "CONVERSATION": message_text}
                        # REMOVED: Original response time bucket calculation here

                        if update_manychat_fields(subscriber_id, field_updates):
                            manychat_last_bot_sent_timestamps[subscriber_id] = time.time(
                            )
                        ai_response_for_analytics = "AI responded asking user to send video for form check."
                        user_message_for_analytics = message_text  # The original text message
                        update_analytics_data(ig_username, user_message_for_analytics,
                                              ai_response_for_analytics, subscriber_id, first_name, last_name)
                        return True  # Action handled (asked for video)
                    else:  # is_form_check_req=True for THIS message, already pending, but THIS message also has no video.
                        logger.info(
                            f"Form check ALREADY pending for {ig_username}, and this current text message (is_form_check_req=True) also has no video: '{message_text[:100]}'. Letting general AI handle.")
                        # Let general AI respond to the text message. Priority handler (above) would get a *subsequent* video message.
                        return False

                # Fallback for any other state within this is_form_check_req block
                else:
                    logger.warning(
                        f"Form check request for {ig_username} fell into an unexpected state within the 'is_form_check_req' block. video_url: {extracted_video_url}, pending: {form_check_pending.get(ig_username)}. Letting general AI handle.")
                    return False  # Let general AI handle

            # Handle Calorie Tracking Request
            elif is_calorie_tracking_req and confidence > 70:
                logger.info(
                    f"Calorie tracking request detected for {ig_username}")
                food_analysis_pending[ig_username] = True
                logger.info(
                    f"Set food_analysis_pending state for {ig_username}")
                response = "Sure, I can help track your calories! Send me a photo of your food along with a quick description of what's in it, and I'll analyze the calories and macros for you."

                # New: Set response time to "action"
                response_time_value = "action"
                if update_manychat_fields(subscriber_id, {"response time": response_time_value}):
                    logger.info(
                        f"Successfully set 'response time' to '{response_time_value}' for SID {subscriber_id} (calorie tracking init)")
                    await asyncio.sleep(random.uniform(1, 2))  # Short delay
                else:
                    logger.error(
                        f"Failed to set 'response time' for SID {subscriber_id} (calorie tracking init)")

                field_updates = {
                    "o1 Response": response,
                    "CONVERSATION": message_text,
                    "response time": "action"  # Explicitly set for workout changes
                }
                # REMOVED: Original response time bucket calculation here

                update_success = update_manychat_fields(
                    subscriber_id, field_updates)
                if update_success:
                    manychat_last_bot_sent_timestamps[subscriber_id] = time.time(
                    )
                if not update_success:
                    logger.error(
                        f"Failed to update ManyChat fields for calorie tracking request for {ig_username}")

                update_analytics_data(
                    ig_username=ig_username,
                    user_message=message_text,
                    ai_response=response,
                    subscriber_id=subscriber_id,
                    first_name=first_name,
                    last_name=last_name
                )
                return True

                # Handle Food Analysis Request (REVISED LOGIC)
            elif is_food_analysis_req and confidence > 70:
                logger.info(
                    f"Food analysis request context for {ig_username} (Confidence: {confidence}). Pending: {food_analysis_pending.get(ig_username)}")
                client_name_for_todo = data.get(
                    'name') or f"{first_name} {last_name}".strip() or ig_username

                extracted_image_url = None
                # Standard Instagram CDN URL pattern
                url_pattern = r"(https?://lookaside\.fbsbx\.com/ig_messaging_cdn/\?asset_id=[\w-]+&signature=[\w\-_.~]+)"
                match = re.search(url_pattern, message_text)
                if match:
                    extracted_image_url = match.group(1)
                    logger.info(
                        f"Regex extracted a media URL for food analysis: {extracted_image_url[:100]}...")

                    user_desc_text = message_text.replace(
                        extracted_image_url, "").strip() if extracted_image_url else message_text
                ai_response_for_analytics = ""
                # Default, will be overridden if image found
                user_message_for_analytics = message_text

                # Scenario 1: Image URL is present in the current message
                if extracted_image_url:
                    logger.info(
                        f"Food analysis for {ig_username} WITH image URL. Analyzing.")
                    user_message_for_analytics = f"(Sent food image: {extracted_image_url[:50]}... Description: {user_desc_text[:30]})"

                    # Clear pending flag if it was set, as we now have an image
                    if food_analysis_pending.pop(ig_username, None):
                        logger.info(
                            f"Cleared food_analysis_pending for {ig_username} as image is now provided.")

                    # Assuming get_calorie_analysis is a synchronous function based on current usage
                    # If it were async, it would be: raw_gemini_analysis_result = await get_calorie_analysis(...)
                    raw_gemini_analysis_result = get_calorie_analysis(
                        extracted_image_url,
                        GEMINI_API_KEY,
                        GEMINI_MODEL_PRO,
                        GEMINI_MODEL_FLASH,
                        GEMINI_MODEL_FLASH_STANDARD,
                        user_description=user_desc_text
                    )

                    if not raw_gemini_analysis_result or "Error" in raw_gemini_analysis_result or "failed" in raw_gemini_analysis_result.lower():
                        response_text_part1 = "Sorry mate, had a bit of trouble analysing that pic. Can you try sending it again?"
                        logger.error(
                            f"Food analysis failed for {ig_username}. Gemini result: {raw_gemini_analysis_result}")
                        add_todo_item(ig_username, client_name_for_todo,
                                      f"Failed calorie analysis for image: {extracted_image_url[:50]}...")
                        ai_response_for_analytics = response_text_part1

                        # New: Set response time to "action"
                        response_time_value = "action"
                        if update_manychat_fields(subscriber_id, {"response time": response_time_value}):
                            logger.info(
                                f"Successfully set 'response time' to '{response_time_value}' for SID {subscriber_id} (food analysis error)")
                            # Short delay
                            await asyncio.sleep(random.uniform(1, 2))
                        else:
                            logger.error(
                                f"Failed to set 'response time' for SID {subscriber_id} (food analysis error)")

                        field_updates = {"o1 Response": response_text_part1,
                                         "CONVERSATION": user_message_for_analytics}

                        # REMOVED: field_updates["response time"] = "calorie"

                        if update_manychat_fields(subscriber_id, field_updates):
                            manychat_last_bot_sent_timestamps[subscriber_id] = time.time(
                            )
                        else:  # This 'else' corresponds to 'if not raw_gemini_analysis_result or "Error" in ...'
                            # This block handles successful analysis
                            tracker = CalorieTracker_CalorieTracker()
                            response_text_part1, response_text_part2 = tracker.handle_food_analysis_webhook(
                                ig_username=ig_username,
                                analysis_text=raw_gemini_analysis_result,
                                description=user_desc_text
                            )
                            add_todo_item(ig_username, client_name_for_todo,
                                          f"Successfully provided calorie analysis for image: {extracted_image_url[:50]}... (Part 1: {response_text_part1[:50]}...)", status="completed")
                            ai_response_for_analytics = f"Meal Analysis: {response_text_part1[:70]}... Daily Update: {response_text_part2[:70]}..." if response_text_part2 else response_text_part1

                            # New: Set response time to "action" for successful analysis (part 1)
                            response_time_value_success = "action"
                            if update_manychat_fields(subscriber_id, {"response time": response_time_value_success}):
                                logger.info(
                                    f"Successfully set 'response time' to '{response_time_value_success}' for SID {subscriber_id} (food analysis part 1 success)")
                                # Short delay
                                await asyncio.sleep(random.uniform(1, 2))
                            else:
                                logger.error(
                                    f"Failed to set 'response time' for SID {subscriber_id} (food analysis part 1 success)")

                            field_updates_part1 = {
                                "o1 Response": response_text_part1, "CONVERSATION": user_message_for_analytics}

                            # REMOVED: field_updates_part1["response time"] = "calorie"

                            if update_manychat_fields(
                                    subscriber_id, field_updates_part1):
                                manychat_last_bot_sent_timestamps[subscriber_id] = time.time(
                                )

                            if response_text_part2:
                                # Schedule the second message as a background task to avoid blocking
                                async def send_second_part():
                                    # Keep this small delay for message separation
                                    await asyncio.sleep(random.uniform(1, 2))

                                    field_updates_part2 = {
                                        "o1 Response 2": response_text_part2}
                                    if update_manychat_fields(subscriber_id, field_updates_part2):
                                        # Update for the last part sent
                                        manychat_last_bot_sent_timestamps[subscriber_id] = time.time(
                                        )

                                # Small delay before sending part 2
                                await asyncio.sleep(random.uniform(1, 2))
                                field_updates_part2 = {
                                    "o1 Response 2": response_text_part2}
                                if update_manychat_fields(subscriber_id, field_updates_part2):
                                    manychat_last_bot_sent_timestamps[subscriber_id] = time.time(
                                    )

                    update_analytics_data(ig_username, user_message_for_analytics,
                                          ai_response_for_analytics, subscriber_id, first_name, last_name)
                    return True  # Action handled

                # Scenario 2: No image URL in the current message
                else:
                    if not food_analysis_pending.get(ig_username):
                        logger.info(
                            f"Initial food analysis request from {ig_username}, no image. Asking and setting pending.")
                        food_analysis_pending[ig_username] = True
                        response_text = "Yep send the photo through, and a brief description of the ingredients used will help as well"

                        # New: Set response time to "action"
                        response_time_value = "action"
                        if update_manychat_fields(subscriber_id, {"response time": response_time_value}):
                            logger.info(
                                f"Successfully set 'response time' to '{response_time_value}' for SID {subscriber_id} (food analysis ask)")
                            # Short delay
                            await asyncio.sleep(random.uniform(1, 2))
                        else:
                            logger.error(
                                f"Failed to set 'response time' for SID {subscriber_id} (food analysis ask)")

                        field_updates = {
                            "o1 Response": response_text, "CONVERSATION": message_text}

                        # REMOVED: Original response time bucket calculation here

                        if update_manychat_fields(subscriber_id, field_updates):
                            manychat_last_bot_sent_timestamps[subscriber_id] = time.time(
                            )
                        ai_response_for_analytics = "AI asked user to send food photo and ingredients."
                        update_analytics_data(
                            ig_username, message_text, ai_response_for_analytics, subscriber_id, first_name, last_name)
                        return True  # Action handled (asked for photo)
                    else:
                        logger.info(
                            f"Food analysis pending for {ig_username}, but still no image in this message: '{message_text[:100]}'. Letting general AI handle.")
                        # User was asked for a photo, but sent text instead.
                        # Return False to let the main conversational AI handle this text.
                        return False
            else:
                logger.info(
                    "Message not identified as a confident action request.")

                # Enhanced ad intent detection with permanent lead tagging
                async def detect_ad_intent_with_context(ig_username: str, message_text: str, conversation_history: list) -> tuple[bool, int, int]:
                    """
                    Use Gemini to analyze conversation context and determine if this is an ad response.
                    Returns: (is_ad_response, scenario, confidence)
                    """
                    try:
                        # Get recent conversation history for context
                        history_context = ""
                        if conversation_history:
                            # Last 5 messages for context
                            recent_messages = conversation_history[-5:]
                            history_context = "\n".join(
                                [f"{msg.get('type', 'user')}: {msg.get('text', '')}" for msg in recent_messages])

                        # First check for exact ManyChat button triggers (100% confidence)
                        exact_triggers = [
                            "Can you tell me more about your Vegan Weight Loss Challenge",
                            "I'm Ready to join the Vegan Weight Loss Challenge",
                            "I'm ready for the Vegetarian Weight Loss Challenge!",
                            "Can you tell me more about your Vegetarian Weight Loss Challenge",
                            "I want to learn more about your vegan challenge",
                            "Tell me more about your vegan challenge",
                            "I'm interested in your vegan challenge",
                            "I want to join your vegan challenge",
                            "Tell me more about your vegetarian challenge",
                            "I'm interested in your vegetarian challenge",
                            "I want to join your vegetarian challenge"
                        ]

                        for trigger in exact_triggers:
                            if trigger.lower() == message_text.lower().strip():
                                challenge_type = "vegan" if "vegan" in trigger.lower() else "vegetarian"
                                logger.info(
                                    f"[detect_ad_intent] Exact trigger match for {ig_username}: '{trigger}' -> {challenge_type}")
                                return True, 1, 100  # 100% confidence for exact matches

                        ad_detection_prompt = f"""
                        You are analyzing Instagram DMs to Shannon (fitness coach at Cocos PT Studio in Melbourne) to determine if this is someone responding to a Plant-Based Challenge ad.

                        CONTEXT:
                        - Shannon runs FB/IG ads for Plant-Based Weight Loss Challenges (Vegan & Vegetarian)
                        - She also proactively DMs vegans (different funnel)
                        - Some people find her organically

                        CONVERSATION HISTORY:
                        {history_context if history_context else "[New conversation - no prior history]"}

                        CURRENT MESSAGE: "{message_text}"

                        ANALYSIS CRITERIA:
                        🎯 **Strong Plant-Based Challenge Ad Indicators:**
                        - Direct mentions: "vegan challenge", "vegetarian challenge", "plant based challenge"
                        - Challenge terms: "28 day challenge", "weight loss challenge", "fitness challenge"
                        - Ad context: "saw your ad", "from Facebook", "from Instagram", "interested in your program"
                        - Diet + fitness: "vegan" + "weight loss/fitness", "vegetarian" + "program"
                        - Specific phrases: "tell me more about", "how do I start", "what's this about"
                        - Plant-based terms: "plant based", "vegan", "vegetarian" WITH fitness/challenge context

                        🚫 **NOT Plant-Based Ad Response:**
                        - Generic vegan chat without challenge context
                        - Pain/injury focus without plant-based mention
                        - Existing conversation continuation
                        - General fitness questions without plant-based context
                        - Responses to Shannon's outbound DMs

                        OUTPUT FORMAT:
                        {{
                            "is_ad_response": true/false,
                            "challenge_type": "vegan/vegetarian/plant_based",
                            "confidence": 0-100,
                            "reasoning": "Brief explanation"
                        }}

                        CHALLENGE TYPES:
                        - vegan = Strong vegan indicators ("vegan challenge", "vegan program")
                        - vegetarian = Strong vegetarian indicators ("vegetarian challenge")  
                        - plant_based = General plant-based without specific diet type
                        """

                        response = await call_gemini_with_retry(GEMINI_MODEL_FLASH, ad_detection_prompt)

                        # Parse the response
                        try:
                            import json
                            import re

                            # Extract JSON from response
                            json_match = re.search(
                                r'\{.*\}', response, re.DOTALL)
                            if json_match:
                                result = json.loads(json_match.group())
                                is_ad = result.get('is_ad_response', False)
                                challenge_type = result.get(
                                    'challenge_type', 'plant_based')
                                confidence = result.get('confidence', 0)

                                logger.info(
                                    f"[detect_ad_intent] Result for {ig_username}: ad={is_ad}, challenge_type={challenge_type}, confidence={confidence}%, reasoning={result.get('reasoning', 'N/A')}")

                                # Map challenge_type to scenario number for compatibility
                                scenario_map = {
                                    'vegan': 1,
                                    'vegetarian': 2,
                                    'plant_based': 3
                                }
                                scenario = scenario_map.get(challenge_type, 1)

                                return is_ad, scenario, confidence
                            else:
                                logger.warning(
                                    f"[detect_ad_intent] Could not parse JSON from response: {response}")
                                return False, 1, 0

                        except Exception as parse_error:
                            logger.error(
                                f"[detect_ad_intent] Error parsing response: {parse_error}")
                            return False, 1, 0

                    except Exception as e:
                        logger.error(
                            f"[detect_ad_intent] Error in ad detection: {e}")
                        return False, 1, 0

                # Check if user is already tagged as ad lead OR currently in ad flow
                _, metrics, _ = get_user_data(ig_username, subscriber_id)
                current_lead_source = metrics.get('lead_source', 'general')
                is_in_ad_flow = metrics.get('is_in_ad_flow', False)

                if current_lead_source in ['facebook_ad', 'plant_based_challenge'] or is_in_ad_flow:
                    # Already tagged as ad lead or currently in ad flow - use ad response flow
                    logger.info(
                        f"[detect_and_handle_action] User {ig_username} tagged as {current_lead_source} lead (lead_source={current_lead_source}) or in ad flow (is_in_ad_flow={is_in_ad_flow}) - using ad response flow")
                    # Get timestamp from batch_start_time_s
                    user_message_timestamp_iso = datetime.fromtimestamp(
                        batch_start_time_s).isoformat()
                    return await handle_ad_response(ig_username, message_text, subscriber_id, data.get('first_name', ''), data.get('last_name', ''), user_message_timestamp_iso)

                # Get conversation history for context
                conversation_history = metrics.get('conversation_history', [])

                # Only run ad detection for new/recent conversations (first 3 messages)
                if len(conversation_history) <= 3:
                    is_ad_response, scenario, confidence = await detect_ad_intent_with_context(ig_username, message_text, conversation_history)

                    if is_ad_response and confidence >= 70:  # High confidence threshold
                        challenge_types = {1: 'vegan',
                                           2: 'vegetarian', 3: 'plant_based'}
                        challenge_type = challenge_types.get(
                            scenario, 'plant_based')
                        logger.info(
                            f"[detect_and_handle_action] Detected Plant-Based Challenge ad response from {ig_username} (confidence: {confidence}%, type: {challenge_type}) - tagging as plant_based_challenge lead")

                        # First set the ad flow flags, then call handle_ad_response
                        # This ensures the user is properly flagged before handle_ad_response checks
                        user_message_timestamp_iso = datetime.fromtimestamp(
                            batch_start_time_s).isoformat()

                        # Set initial flags without full analytics update
                        try:
                            import sqlite3
                            conn = sqlite3.connect(
                                "app/analytics_data_good.sqlite")
                            cursor = conn.cursor()

                            # Check if user exists, if not create basic entry
                            cursor.execute(
                                "SELECT ig_username FROM users WHERE ig_username = ?", (ig_username,))
                            if not cursor.fetchone():
                                cursor.execute("""
                                    INSERT INTO users (ig_username, subscriber_id, lead_source, is_in_ad_flow, ad_script_state, ad_scenario) 
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (ig_username, subscriber_id, 'paid_plant_based_challenge', True, 'step1', scenario))
                            else:
                                cursor.execute("""
                                    UPDATE users 
                                    SET lead_source = ?, is_in_ad_flow = ?, ad_script_state = ?, ad_scenario = ? 
                                    WHERE ig_username = ?
                                """, ('paid_plant_based_challenge', True, 'step1', scenario, ig_username))

                            conn.commit()
                            conn.close()
                            logger.info(
                                f"Successfully set ad flow flags for {ig_username}")
                        except Exception as e:
                            logger.error(
                                f"Failed to set ad flow flags for {ig_username}: {e}")

                        # Now call handle_ad_response with the flags already set
                        # Force ad flow parameters since we just set them
                        result = await handle_ad_response_with_params(
                            ig_username=ig_username,
                            message_text=message_text,
                            subscriber_id=subscriber_id,
                            first_name=data.get('first_name', ''),
                            last_name=data.get('last_name', ''),
                            user_message_timestamp_iso=user_message_timestamp_iso,
                            force_ad_flow=True,
                            force_lead_source='paid_plant_based_challenge',
                            force_scenario=scenario,
                            force_script_state='step1'
                        )

                        # Update full analytics data after successful response
                        if result:
                            update_analytics_data(
                                ig_username=ig_username,
                                user_message=message_text,
                                ai_response="",  # Will be set by handle_ad_response
                                subscriber_id=subscriber_id,
                                first_name=data.get('first_name', ''),
                                last_name=data.get('last_name', ''),
                                lead_source='paid_plant_based_challenge',
                                is_in_ad_flow=True,
                                ad_script_state='step1',
                                ad_scenario=scenario,
                                user_message_timestamp=user_message_timestamp_iso
                            )

                        return result

                return False

    except Exception as e:
        logger.error(
            f"Error in detect_and_handle_action: {str(e)}", exc_info=True)
        # Maybe send a generic error to Manychat?
        return False  # Indicate failure to handle


@app.get("/debug")
async def debug_endpoint(request: Request):
    """Simple debug endpoint that returns all query parameters and headers"""
    query_params = dict(request.query_params)
    headers = dict(request.headers)

    # Log everything for debugging
    logger.info(f"DEBUG ENDPOINT ACCESSED - Query params: {query_params}")

    # If this is a Facebook verification attempt, handle it specially
    if "hub.mode" in query_params and "hub.verify_token" in query_params and "hub.challenge" in query_params:
        mode = query_params.get("hub.mode")
        token = query_params.get("hub.verify_token")
        challenge = query_params.get("hub.challenge")

        logger.info(
            f"DEBUG: Facebook verification detected! Mode: {mode}, Token: {token}, Challenge: {challenge}")

        # Verify the token for proper logging (but always return challenge in debug mode)
        verify_token = "Shanbotcyywp7nyk"
        if mode == "subscribe" and token == verify_token:
            logger.info("DEBUG: Token verification successful")
        else:
            logger.warning(
                f"DEBUG: Token verification failed. Expected: {verify_token}, Got: {token}")

        # Always return the challenge as plain text without verification for debugging
        return PlainTextResponse(content=challenge)

    return {
        "status": "debug",
        "query_params": query_params,
        "headers": {k: v for k, v in headers.items()},
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint that redirects to health check"""
    logger.info("Root endpoint accessed")
    return {"status": "Shanbot API running", "message": "Use /webhook endpoints for functionality"}


async def schedule_response(sender_id: str, initial_delay_to_use: int):
    try:
        # --- NEW DELAY LOGIC --- START ---
        # Start with the base delay (20s or 600s)
        target_total_wait = initial_delay_to_use
        user_response_time_seconds = 0  # Default

        # Get user message arrival time and bot last reply time
        user_message_arrival_ts = last_message_timestamps.get(sender_id)
        last_bot_reply_ts = last_bot_reply_timestamps.get(sender_id)

        if user_message_arrival_ts and last_bot_reply_ts:
            user_response_time_seconds = user_message_arrival_ts - last_bot_reply_ts
            # Ensure response time isn't negative (e.g., clock sync issues)
            user_response_time_seconds = max(0, user_response_time_seconds)
            target_total_wait = max(
                initial_delay_to_use, user_response_time_seconds)
            logger.info(
                f"[schedule_response] User response time: {user_response_time_seconds:.1f}s.")
        elif user_message_arrival_ts:
            logger.info(
                f"[schedule_response] User message timestamp found, but no previous bot reply timestamp. Using initial delay.")
        else:
            logger.info(
                f"[schedule_response] No user message arrival timestamp found. Using initial delay.")

        logger.info(
            f"[schedule_response] Base Delay: {initial_delay_to_use}s, User Response Time: {user_response_time_seconds:.1f}s. Target Total Wait: {target_total_wait:.1f}s")

        # Perform the calculated total wait
        await asyncio.sleep(target_total_wait)
        logger.info(
            f"[schedule_response] Woke up after {target_total_wait:.1f}s total wait for {sender_id}.")
        # --- NEW DELAY LOGIC --- END ---

        # --- Rest of the message processing ---
        messages = message_buffer.pop(sender_id, [])
        if not messages:
            logger.info(
                f"No messages left in buffer for {sender_id} after delay.")
            return  # Exit if buffer was cleared by another message

        full_message = ' '.join(messages)
        logger.info(
            f"Processing combined message for {sender_id}: '{full_message}'")

        # Get or create user data and conversation history
        full_conversation_history, metrics_dict, user_id = get_user_data(
            ig_username=ig_username,
            subscriber_id=subscriber_id  # Pass subscriber_id here
        )

        # Append new message to history
        if message_text or media_url:  # Only add if there's content
            new_message_entry = {
                "type": "user", "text": message_text or f"[{message_type.upper()} received]", "timestamp": get_melbourne_time_str()}
            if media_url:
                new_message_entry["media_url"] = media_url
                new_message_entry["media_type"] = message_type
            if not isinstance(full_conversation_history, list):
                full_conversation_history = []  # Ensure it's a list if not already

            # Check for duplicate consecutive messages from the same sender to prevent webhook retries from cluttering history
            if full_conversation_history and new_message_entry['message_text'] == full_conversation_history[-1].get('message_text') and new_message_entry['message_type'] == full_conversation_history[-1].get('message_type'):
                logger.info(
                    f"Skipping duplicate message from {new_message_entry['message_type']}: {new_message_entry['message_text'][:50]}...")
            else:
                full_conversation_history.append(new_message_entry)

        # ---- ONBOARDING DETECTION AND HANDLING ----
        # Remove or comment out the direct user message trigger for onboarding
        # onboarding_trigger_phrase = "initiate_onboarding_sequence"
        # if message_text.lower() == onboarding_trigger_phrase.lower():
        #    logger.info(f"Onboarding sequence triggered for {ig_username}.")
        #    post_onboarding_handler = PostOnboardingHandler(gemini_api_key=GEMINI_API_KEY)
        #    background_tasks.add_task(
        #        post_onboarding_handler.process_onboarding_completion,
        #        ig_username=ig_username,
        #        conversation_history=full_conversation_history
        #    )
        #    logger.info(f"Onboarding for {ig_username} scheduled in background. Returning 200 OK to ManyChat.")
        #    return PlainTextResponse("Onboarding process started.", status_code=200)
        # ---- END (REMOVED) USER-TRIGGERED ONBOARDING HANDLING ----

        # Existing logic for non-onboarding messages (ensure this is still called if not onboarding)
        logger.info(f"Passing to regular message handler for {ig_username}")
        action_handled = await detect_and_handle_action(ig_username, message_text, data if isinstance(data, dict) else {}, batch_start_time_s)

        ai_response_for_analytics = ""

        if not action_handled:
            logger.info(
                f"No specific action detected for {ig_username}, proceeding to general AI response.")
            current_stage = metrics_dict.get(
                'journey_stage', {}).get('current_stage', "Topic 1")
            trial_status = metrics_dict.get('trial_status', "Initial Contact")

            first_name_from_data = data.get("first_name", "")
            last_name_from_data = data.get("last_name", "")
            calculated_full_name = f"{first_name_from_data} {last_name_from_data}".strip(
            )
            if not calculated_full_name:
                full_name_from_metrics_fn = metrics_dict.get('first_name', '')
                full_name_from_metrics_ln = metrics_dict.get('last_name', '')
                calculated_full_name = f"{full_name_from_metrics_fn} {full_name_from_metrics_ln}".strip(
                )
            if not calculated_full_name:
                calculated_full_name = ig_username

            current_message_for_prompt_builder = message_text
            if not current_message_for_prompt_builder and media_url:
                analyzed_media_type, analyzed_media_text = analyze_media_url(
                    media_url)
                if analyzed_media_text:
                    current_message_for_prompt_builder = f"[{analyzed_media_type.upper() if analyzed_media_type else 'MEDIA'} Content: {analyzed_media_text}]"
                else:
                    current_message_for_prompt_builder = f"[{message_type.upper() if message_type else 'MEDIA'} received, analysis failed or not applicable]"
            elif media_url and current_message_for_prompt_builder:
                analyzed_media_type, analyzed_media_text = analyze_media_url(
                    media_url)
                if analyzed_media_text:
                    current_message_for_prompt_builder = f"{message_text} [{analyzed_media_type.upper() if analyzed_media_type else 'MEDIA'} Content: {analyzed_media_text}]"
                else:
                    current_message_for_prompt_builder = f"{message_text} [{message_type.upper() if message_type else 'MEDIA'} received, analysis failed or not applicable]"

            processed_current_user_message_text = process_conversation_for_media(
                current_message_for_prompt_builder)

            prompt_str_for_ai, prompt_type = build_member_chat_prompt(
                client_data=metrics_dict,
                current_message=processed_current_user_message_text,
                current_stage=current_stage,
                trial_status=trial_status,
                full_name=calculated_full_name
            )
            ai_raw_response_text = await get_ai_response(prompt_str_for_ai)

            # --- Post-process the response to ensure it's a direct reply from Shannon ---
            if ai_raw_response_text:
                ai_raw_response_text = await filter_shannon_response(ai_raw_response_text, processed_current_user_message_text)

            # --- Enforce soft challenge-offer flow (prevent premature link) ---
            if ai_raw_response_text:
                try:
                    ai_raw_response_text = enforce_challenge_offer_rules(
                        ai_raw_response_text, full_conversation_history)
                except Exception as e:
                    logger.error(f"Challenge offer gating error: {e}")
                # --- Remove repeated questions and rewrite if necessary ---
                ai_raw_response_text = await _dedup_and_rewrite_if_needed(ai_raw_response_text, full_conversation_history)

            if ai_raw_response_text:
                ai_response_for_analytics = ai_raw_response_text
                ai_responses_list_for_manychat = split_response_into_messages(
                    ai_raw_response_text)

                # New: Set response time for general AI replies
                # Default to an invalid state or handle appropriately
                time_diff_seconds_for_bucket = -1.0
                last_bot_sent_ts = manychat_last_bot_sent_timestamps.get(
                    subscriber_id)

                if last_bot_sent_ts is not None:
                    # batch_start_time_s is the timestamp of the current user's message (earliest in batch)
                    time_diff_seconds_for_bucket = batch_start_time_s - last_bot_sent_ts
                    logger.info(
                        f"[GENERAL RESPONSE] User message at {datetime.fromtimestamp(batch_start_time_s).isoformat()}, last bot message at {datetime.fromtimestamp(last_bot_sent_ts).isoformat()}. Difference for bucket: {time_diff_seconds_for_bucket:.2f}s"
                    )
                else:
                    # No in-memory record of the last bot message (likely after a service restart).
                    # Attempt a smarter fallback by inspecting the stored conversation history for the
                    # most recent 'ai' message timestamp. This keeps response-time buckets accurate even
                    # after restarts where the cache is cleared.
                    last_ai_ts_float: Optional[float] = None
                    for _entry in reversed(full_conversation_history):
                        if _entry.get("type") == "ai" and _entry.get("timestamp"):
                            try:
                                last_ai_dt = parser.parse(
                                    _entry["timestamp"], ignoretz=False)
                                last_ai_ts_float = last_ai_dt.timestamp()
                                break
                            except Exception:
                                # Skip entries with unparseable timestamps and keep searching
                                continue

                    if last_ai_ts_float is not None:
                        time_diff_seconds_for_bucket = batch_start_time_s - last_ai_ts_float
                        logger.info(
                            f"[GENERAL RESPONSE] Fallback using history. User message at {datetime.fromtimestamp(batch_start_time_s).isoformat()}, last AI message at {datetime.fromtimestamp(last_ai_ts_float).isoformat()}. Difference for bucket: {time_diff_seconds_for_bucket:.2f}s"
                        )
                    else:
                        # Ultimate fallback – use current processing latency (a few seconds)
                        time_diff_seconds_for_bucket = time.time() - batch_start_time_s
                        logger.info(
                            f"[GENERAL RESPONSE] No last AI message found in history for SID {subscriber_id}. Using processing latency for bucket: {time_diff_seconds_for_bucket:.2f}s"
                        )

                response_time_value_general = get_response_time_bucket(
                    time_diff_seconds_for_bucket)
                logger.info(
                    f"[GENERAL RESPONSE] Calculated time diff for bucket: {time_diff_seconds_for_bucket:.2f}s, Bucket: {response_time_value_general} for SID {subscriber_id}")

                if update_manychat_fields(subscriber_id, {"response time": response_time_value_general}):
                    logger.info(
                        f"Successfully set 'response time' to '{response_time_value_general}' for SID {subscriber_id} (general AI response)")
                    # Short delay before sending message content
                    await asyncio.sleep(random.uniform(1, 2))
                else:
                    logger.error(
                        f"Failed to set 'response time' for SID {subscriber_id} (general AI response)")

                field_names = ["o1 Response", "o1 Response 2", "o1 Response 3"]
                for i, response_text_chunk in enumerate(ai_responses_list_for_manychat):
                    if i < len(field_names):
                        field_name_to_use = field_names[i]
                        field_updates = {
                            field_name_to_use: response_text_chunk}
                        # Directly call update_manychat_fields which is expected to be in this file or imported correctly
                        success = update_manychat_fields(
                            subscriber_id, field_updates)
                        if not success:
                            logger.error(
                                f"Failed to send chunk {i+1} to field {field_name_to_use} for SID {subscriber_id}")
                        # Add a small delay between sending message parts, except for the last one
                    if i < len(ai_responses_list_for_manychat) - 1:
                        await asyncio.sleep(random.uniform(1, 3))
                    else:
                        logger.warning(
                            f"More than {len(field_names)} message chunks generated, but only {len(field_names)} fields are handled. Chunk {i+1} not sent.")

                # Update the timestamp *after* all chunks are sent
                if ai_responses_list_for_manychat:  # If any AI message was actually sent
                    manychat_last_bot_sent_timestamps[subscriber_id] = time.time(
                    )
                    logger.info(
                        f"Updated manychat_last_bot_sent_timestamps for SID {subscriber_id} after sending general AI response parts.")

                ai_onboarding_trigger_phrase = "No worries! Ill let you know when your set up, and youll get an invite via email from me! Let me get into this! Chat in a bit!".lower()
                if ai_onboarding_trigger_phrase in ai_response_for_analytics.lower():
                    logger.info(
                        f"AI response triggered onboarding sequence for {ig_username} (subscriber_id: {subscriber_id}).")
                    post_onboarding_handler = PostOnboardingHandler(
                        gemini_api_key=GEMINI_API_KEY)

                    onboarding_task_payload = functools.partial(
                        post_onboarding_handler.process_onboarding_completion,
                        ig_username=ig_username,
                        subscriber_id=subscriber_id,
                        conversation_history=full_conversation_history
                    )
                    background_tasks.add_task(onboarding_task_payload)
                    logger.info(
                        f"Full onboarding process for {ig_username} (subscriber_id: {subscriber_id}) scheduled in background via buffered handler.")
            else:
                logger.warning(
                    f"No AI response generated for {ig_username} (from combined message)")
                ai_response_for_analytics = "[AI FAILED TO RESPOND]"
        else:
            logger.info(
                f"Action handled for {ig_username} (from combined message), AI response might have been sent by action handler.")
            ai_response_for_analytics = "[Action handled by detect_and_handle_action]"

        # update_analytics_data will save the processed_final_combined_message_text as the user's message
        # and the ai_response_for_analytics as the AI's response to the conversation history.
        # Convert batch_start_time_s to ISO format for the user message timestamp
        user_message_timestamp_iso = datetime.fromtimestamp(
            batch_start_time_s).isoformat()

        update_analytics_data(
            ig_username=ig_username,
            user_message=processed_final_combined_message_text,
            ai_response=ai_response_for_analytics,
            subscriber_id=subscriber_id,
            first_name=first_name_for_analytics,
            last_name=last_name_for_analytics,
            user_message_timestamp=user_message_timestamp_iso  # Pass the actual timestamp
        )
        logger.info(
            f"Finished processing buffered messages for SID {subscriber_id}")

        return PlainTextResponse("Webhook processed", status_code=200)

    except asyncio.CancelledError:
        logger.info(f"Response task for {sender_id} was cancelled.")
    except Exception as e:
        logger.error(
            f"Error in scheduled response task for {sender_id}: {e}", exc_info=True)
        # Optionally try to send an error message to the user
        try:
            await send_instagram_reply(sender_id, "Sorry, something went wrong on my end. Please try again later.")
        except Exception as send_err:
            logger.error(
                f"Failed to send error message to {sender_id}: {send_err}")

# --- Story Comment Handling Functions --- START ---


@app.post("/trainerize/build-program-deprecated")
async def build_trainerize_program(request_data: BuildProgramRequest):
    """
    API endpoint to build a full training program for a client in Trainerize.
    """
    logger.info(
        f"Received request to build program for: {request_data.client_name}")

    try:
        # Create a new TrainerizeAutomation instance
        trainerize = TrainerizeAutomation()
        try:
            # Convert Pydantic model to dictionary list for the method call
            workout_defs_dict = [wd.dict()
                                 for wd in request_data.workout_definitions]

            # Call the method on the instance
            results = trainerize.build_full_program_for_client(
                client_name=request_data.client_name,
                program_name=request_data.program_name,
                workout_definitions=workout_defs_dict
            )

            # Check if the overall process encountered critical failures
            critical_failure = any(step['step'] in ['navigate_to_client', 'navigate_to_training_program',
                                                    'create_program'] and not step['success'] for step in results)

            if critical_failure:
                logger.error(
                    f"Critical failure during program build for {request_data.client_name}. Results: {results}")
                # Return a server error status code if critical steps failed
                return JSONResponse(
                    status_code=500,
                    content={
                        "message": "Failed to build program due to critical error during automation.", "details": results}
                )
            else:
                logger.info(
                    f"Successfully completed program build request for {request_data.client_name}. Results: {results}")
                return JSONResponse(
                    status_code=200,
                    content={"message": "Program build process initiated.",
                             "details": results}
                )
        finally:
            # Always cleanup the instance
            trainerize.cleanup()

    except Exception as e:
        logger.error(
            f"Error calling build_full_program_for_client for {request_data.client_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Internal server error during program build: {str(e)}")


def update_manychat_fields(subscriber_id: str, field_updates: Dict[str, str]) -> bool:
    """Update custom fields in ManyChat for a subscriber"""
    # Filter out None and empty string values
    filtered_updates = {
        k: v for k, v in field_updates.items() if v is not None and v != ""}
    if not filtered_updates:
        logger.info("No valid field updates to send to ManyChat.")
        return True  # Nothing to update, consider it success

    # Prepare the data using field_name
    field_data = [
        {"field_name": field_name, "field_value": value}
        for field_name, value in filtered_updates.items()
    ]
    data = {
        "subscriber_id": subscriber_id,
        "fields": field_data
    }

    headers = {
        "Authorization": f"Bearer {MANYCHAT_API_KEY}",
        "Content-Type": "application/json"
    }

    logger.info(
        f"Attempting to update ManyChat fields for subscriber {subscriber_id}: {list(filtered_updates.keys())}")
    # --- ADDED DETAILED PAYLOAD LOGGING ---
    logger.info(f"ManyChat API Request Payload: {json.dumps(data, indent=2)}")
    # --- END ADDED LOGGING ---
    try:
        response = requests.post(
            "https://api.manychat.com/fb/subscriber/setCustomFields", headers=headers, json=data, timeout=10)
        # Log beginning of response
        logger.info(
            f"ManyChat API response: {response.status_code} - {response.text[:500]}")
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        logger.info(
            f"Successfully updated ManyChat fields for subscriber {subscriber_id}.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Error updating ManyChat fields for subscriber {subscriber_id}: {e}", exc_info=True)
        # Log response body if available
        if hasattr(e, 'response') and e.response is not None:
            logger.error(
                f"ManyChat Error Response Body: {e.response.text[:500]}")
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error during ManyChat field update for {subscriber_id}: {e}", exc_info=True)
        return False


# --- ADDED: Dictionary to store last sent timestamp for ManyChat users ---
manychat_last_bot_sent_timestamps: Dict[str, float] = {}
# --- END ADDED ---

# --- ADDED: Message Buffer System ---

# Global dictionaries for message buffering
manychat_message_buffer: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
manychat_last_message_time: Dict[str, float] = {}
BUFFER_WINDOW = 60  # seconds to wait for grouping messages
user_buffer_task_scheduled: Dict[str, bool] = {}  # For new buffering logic
# Store actual task objects for cancellation
user_buffer_tasks: Dict[str, any] = {}

# Track workout edit states
program_edit_pending: Dict[str, str] = {}

# Global message buffer
message_buffer = {}


def add_to_message_buffer(ig_username: str, payload: Dict):
    """Add a message to the buffer for a given user"""
    if ig_username not in message_buffer:
        message_buffer[ig_username] = []
    message_buffer[ig_username].append(
        {'payload': payload, 'timestamp': datetime.now()})
    logger.info(f"Added message to buffer for {ig_username}")


def process_buffered_messages(ig_username: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Process any buffered messages for a given user"""
    try:
        # Get the user's buffered messages
        user_buffer = message_buffer.get(ig_username, [])
        if not user_buffer:
            logger.info(f"No buffered messages found for {ig_username}")
            return None

        # Get the payload from the first message (should contain user info)
        first_message = user_buffer[0]
        payload = first_message.get('payload', {})

        # Extract subscriber_id and other info
        subscriber_id = payload.get('id')
        if not subscriber_id:
            logger.error(
                f"No subscriber_id found in payload for {ig_username}")
            return None

        # Combine all messages
        combined_message_text_parts = []
        for msg in user_buffer:
            msg_text = msg.get('payload', {}).get('last_input_text', '')
            if msg_text:
                if combined_message_text_parts:
                    combined_message_text_parts.append("\n")
                combined_message_text_parts.append(msg_text)

        if not combined_message_text_parts:
            logger.error(f"No message content found for {ig_username}")
            return None

        logger.info(
            f"Successfully processed buffer for {ig_username}: {combined_message_text_parts}")

        # === SMART MESSAGE COMBINATION: Handle repeated messages intelligently ===
        if len(combined_message_text_parts) == 1:
            # Single message - use as-is
            final_combined_message_text = combined_message_text_parts[0].strip(
            )
        elif len(combined_message_text_parts) > 1:
            # Multiple messages - check for repetition
            message_counts = {}
            unique_messages = []

            for msg in combined_message_text_parts:
                msg_clean = msg.strip()
                if msg_clean:
                    if msg_clean in message_counts:
                        message_counts[msg_clean] += 1
                    else:
                        message_counts[msg_clean] = 1
                        unique_messages.append(msg_clean)

            # Build final message with smart formatting
            formatted_parts = []
            for msg in unique_messages:
                count = message_counts[msg]
                if count > 1:
                    formatted_parts.append(f"[{count}x] {msg}")
                else:
                    formatted_parts.append(msg)

            final_combined_message_text = " ".join(formatted_parts)
        else:
            final_combined_message_text = ""
        # === END SMART MESSAGE COMBINATION ===

        return final_combined_message_text, payload

    except Exception as e:
        logger.error(f"Error processing buffered messages: {str(e)}")
        return None
    finally:
        # Always clear the buffer after processing
        message_buffer.pop(ig_username, None)
        logger.info(f"Cleared message buffer for {ig_username}")


async def delayed_message_processing(ig_username: str):
    """Process messages after a delay to allow for grouping."""
    try:
        await asyncio.sleep(BUFFER_WINDOW)  # Wait for messages to accumulate

        logger.info(
            f"\n=== DELAYED MESSAGE PROCESSING START for {ig_username} ===")

        # Get buffered messages
        if ig_username not in message_buffer:
            logger.warning(f"No messages in buffer for {ig_username}")
            return

        messages = message_buffer[ig_username]
        if not messages:
            logger.warning(f"Empty message list in buffer for {ig_username}")
            return

        # Get user data for prompt context
        full_conversation_history, metrics_dict, user_id_key = get_user_data(
            ig_username=ig_username,
            subscriber_id=messages[0].get("subscriber_id", "")
        )

        # Extract needed values from metrics_dict
        current_stage = metrics_dict.get(
            'journey_stage', {}).get('current_stage', 'Topic 1')
        trial_status = metrics_dict.get('client_status', 'Initial Contact')
        full_name = f"{metrics_dict.get('first_name', '')} {metrics_dict.get('last_name', '')}".strip(
        )
        if not full_name:
            full_name = ig_username

        combined_message = " ".join([msg["text"] for msg in messages])
        logger.info(f"Combined message: {combined_message}")

        # Clear buffer after reading
        message_buffer[ig_username] = []

        # Process media URLs in the combined message
        processed_message = process_conversation_for_media(combined_message)
        logger.info(
            f"Processed message (after media handling): {processed_message}")

        # Build chat prompt using build_member_chat_prompt with all required parameters
        chat_prompt, prompt_type = build_member_chat_prompt(
            client_data=metrics_dict,
            current_message=processed_message,
            conversation_history="",
            current_stage=current_stage,
            trial_status=trial_status,
            full_name=full_name
        )

        # Get AI response
        ai_response = await get_ai_response(chat_prompt)
        if not ai_response:
            logger.error("Failed to get AI response")
            return

        # Update analytics data
        update_analytics_data(
            ig_username=ig_username,
            user_message=processed_message,
            ai_response=ai_response,
            subscriber_id=messages[0].get("subscriber_id", ""),
            first_name=messages[0].get("first_name", ""),
            last_name=messages[0].get("last_name", ""),
            set_checkin_flow_false=False
        )

        # Split and send response
        response_messages = split_response_into_messages(ai_response)
        for msg in response_messages:
            await send_manychat_message(
                subscriber_id=messages[0].get("subscriber_id", ""),
                message=msg
            )
            await asyncio.sleep(1)  # Small delay between messages

    except Exception as e:
        logger.error(
            f"Error in delayed_message_processing: {e}", exc_info=True)


@app.post("/webhook/manychat")
async def process_manychat_webhook(request: Request, background_tasks: BackgroundTasks):
    raw_body = await request.body()
    payload_str = raw_body.decode('utf-8')
    logger.info(f"Received raw payload: {payload_str[:1000]}...")

    manychat_signature = request.headers.get('X-ManyChat-Signature')
    if manychat_signature:
        # Assuming verify_manychat_signature function exists and works
        # if not verify_manychat_signature(payload_str, manychat_signature, MANYCHAT_API_KEY):
        #     logger.warning("Invalid X-ManyChat-Signature. Aborting.")
        #     raise HTTPException(status_code=403, detail="Invalid signature")
        logger.info(
            "X-ManyChat-Signature would be verified here (assuming function exists).")
    else:
        logger.info(
            "No X-ManyChat-Signature header found. Proceeding without signature verification.")

    try:
        data = json.loads(payload_str)
        logger.info(f"Parsed payload: {json.dumps(data, indent=2)[:1000]}...")
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON payload.")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    subscriber_id = data.get("id")
    if not subscriber_id:
        subscriber_id = data.get("subscriber", {}).get("id", "")
        if not subscriber_id:
            logger.error(
                "[Webhook] Critical: Subscriber ID missing in payload.")
            # Changed to 400
            return PlainTextResponse("Error: Subscriber ID missing", status_code=400)
    logger.info(f"[Webhook] Processing for subscriber_id: {subscriber_id}")

    # --- Start of ig_username extraction (should be robust as per previous edits) ---
    ig_username = None
    ig_username_from_payload = data.get("ig_username")

    # Always get raw_subscriber_data upfront as it's used in multiple fallbacks
    raw_subscriber_data = data.get("subscriber", {})
    if not isinstance(raw_subscriber_data, dict):  # Ensure it's a dict
        raw_subscriber_data = {}
        logger.warning(
            "[Webhook] 'subscriber' field in payload was not a dictionary. Defaulting to empty dict.")

    if ig_username_from_payload and isinstance(ig_username_from_payload, str) and ig_username_from_payload.strip():
        ig_username = ig_username_from_payload.strip()
        logger.info(
            f"[Webhook] Retrieved ig_username '{ig_username}' directly from payload.")

    if not ig_username:
        # raw_subscriber_data is already defined above
        custom_fields = raw_subscriber_data.get("custom_fields", {})
        if isinstance(custom_fields, dict):
            ig_username_from_cf = custom_fields.get("ig_username")
            if ig_username_from_cf and isinstance(ig_username_from_cf, str) and ig_username_from_cf.strip():
                ig_username = ig_username_from_cf.strip()
                logger.info(
                    f"[Webhook] Retrieved ig_username '{ig_username}' from subscriber.custom_fields.ig_username.")

        if not ig_username:
            # Re-get if not already gotten
            raw_subscriber_data = data.get("subscriber", {})
            ig_username_from_sub_name = raw_subscriber_data.get("name")
            if ig_username_from_sub_name and isinstance(ig_username_from_sub_name, str) and ig_username_from_sub_name.strip():
                temp_ig_name = ig_username_from_sub_name.strip()
                is_placeholder = temp_ig_name.startswith(
                    'user_') and temp_ig_name[5:].isdigit()
                if not is_placeholder:
                    ig_username = temp_ig_name
                    logger.info(
                        f"[Webhook] Retrieved ig_username '{ig_username}' from subscriber.name.")
                else:
                    logger.info(
                        f"[Webhook] subscriber.name ('{temp_ig_name}') is placeholder.")

    if not ig_username:
        # Further fallbacks for ig_username
        raw_subscriber_data = data.get("subscriber", {})
        ig_username_from_sub_uname = raw_subscriber_data.get("user_name")
        if ig_username_from_sub_uname and isinstance(ig_username_from_sub_uname, str) and ig_username_from_sub_uname.strip():
            temp_ig_username = ig_username_from_sub_uname.strip()
            is_placeholder_user_id_format = temp_ig_username.startswith(
                'user_') and temp_ig_username[5:] == str(subscriber_id)
            is_generic_placeholder = temp_ig_username.startswith(
                'user_') and temp_ig_username[5:].isdigit()
            if not is_placeholder_user_id_format and not is_generic_placeholder:
                ig_username = temp_ig_username
                logger.info(
                    f"[Webhook] Retrieved ig_username '{ig_username}' from subscriber.user_name.")
            elif is_placeholder_user_id_format or is_generic_placeholder:
                logger.info(
                    f"[Webhook] subscriber.user_name ('{temp_ig_username}') is placeholder.")

    # --- NEW: API call to ManyChat if username is missing or a placeholder ---
    is_placeholder_username = ig_username and ig_username.startswith(
        'user_') and ig_username[5:].isdigit()
    if not ig_username or is_placeholder_username:
        logger.warning(
            f"IG username is missing or a placeholder ('{ig_username}'). Attempting to fetch from ManyChat API for SID {subscriber_id}.")
        try:
            api_username = await get_username_from_manychat(subscriber_id)
            if api_username:
                logger.info(
                    f"Successfully fetched username '{api_username}' from API. Using it.")
                ig_username = api_username
            else:
                logger.warning(
                    f"Could not fetch a valid username from ManyChat API for SID {subscriber_id}. Proceeding with '{ig_username}'.")
        except Exception as api_e:
            logger.error(
                f"An exception occurred while trying to fetch username from ManyChat API: {api_e}")

    if not ig_username:
        ig_username = f"user_{subscriber_id}"  # Final fallback
        logger.warning(
            f"[Webhook] Using generated ig_username: '{ig_username}'.")
    # --- End of ig_username extraction ---

    # Add the current message payload to the user's buffer
    # The 'data' here is the full parsed JSON payload of the current webhook
    if subscriber_id not in manychat_message_buffer:
        manychat_message_buffer[subscriber_id] = []

    # Get 'created_at' or default to now
    user_message_created_at_s = data.get("created_at", time.time())

    manychat_message_buffer[subscriber_id].append(
        {"payload": data, "user_msg_created_at_s": user_message_created_at_s})
    logger.info(
        f"Appended message from SID {subscriber_id} (created_at: {datetime.fromtimestamp(user_message_created_at_s).isoformat()}) to buffer. Buffer size: {len(manychat_message_buffer[subscriber_id])}")

    # Enhanced timer restart logic: Cancel existing task if present and schedule a new one
    # This ensures the 60-second timer restarts with each new message
    if subscriber_id in user_buffer_tasks:
        # Cancel the existing task to restart the timer
        try:
            existing_task = user_buffer_tasks[subscriber_id]
            if existing_task and not existing_task.done():
                existing_task.cancel()
                logger.info(
                    f"⏰ Canceled existing buffer task for SID {subscriber_id} - timer restarting for {BUFFER_WINDOW}s")
        except Exception as e:
            logger.warning(
                f"Error canceling existing task for SID {subscriber_id}: {e}")

    # Always schedule a new task (either first message or restarting timer)
    user_buffer_task_scheduled[subscriber_id] = True
    new_task = background_tasks.add_task(
        run_core_processing_after_buffer, subscriber_id, ig_username, background_tasks)
    user_buffer_tasks[subscriber_id] = new_task

    if len(manychat_message_buffer[subscriber_id]) == 1:
        logger.info(
            f"🆕 Started {BUFFER_WINDOW}s buffer timer for SID: {subscriber_id}, IG: {ig_username}")
    else:
        logger.info(
            f"🔄 Restarted {BUFFER_WINDOW}s buffer timer for SID: {subscriber_id} (message #{len(manychat_message_buffer[subscriber_id])})")

    # --- After extracting ig_username and subscriber_id ---
    # Ensure subscriber_id is written to the user's profile if missing or different
    try:
        import sqlite3
        SQLITE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"
        conn = sqlite3.connect(SQLITE_PATH)
        c = conn.cursor()
        # Check current subscriber_id for this ig_username
        c.execute(
            "SELECT subscriber_id FROM users WHERE ig_username = ?", (ig_username,))
        row = c.fetchone()
        if row is not None:
            current_subscriber_id = row[0]
            if current_subscriber_id != subscriber_id:
                c.execute("UPDATE users SET subscriber_id = ? WHERE ig_username = ?",
                          (subscriber_id, ig_username))
                conn.commit()
                logger.info(
                    f"Updated subscriber_id for {ig_username} to {subscriber_id} in SQLite DB.")
        conn.close()
    except Exception as e:
        logger.error(
            f"Failed to update subscriber_id for {ig_username} in SQLite DB: {e}")

    return PlainTextResponse("Webhook received, processing deferred.", status_code=200)


@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify the server is running"""
    return {"status": "ok", "message": "Server is running"}


def get_response_time_bucket(time_diff_seconds: float) -> str:
    """
    Convert time difference to ManyChat response time bucket.
    Args:
        time_diff_seconds: Time difference in seconds
    Returns:
        String matching ManyChat's response time conditions
    """
    if time_diff_seconds <= 120:  # 0-2 minutes
        return "response time is 0-2minutes"
    elif time_diff_seconds <= 300:  # 2-5 minutes
        return "response time is 2-5 minutes"
    elif time_diff_seconds <= 600:  # 5-10 minutes
        return "response time is 5-10 minutes"
    elif time_diff_seconds <= 1200:  # 10-20 minutes
        return "response time is 10-20 minutes"
    elif time_diff_seconds <= 1800:  # 20-30 minutes
        return "response time is 20-30 minutes"
    elif time_diff_seconds <= 3600:  # 30-60 minutes
        return "response time is 30-60 minutes"
    elif time_diff_seconds <= 7200:  # 1-2 Hours
        return "response time is 1-2 Hours"
    else:  # This will now catch everything > 7200 seconds (2 hours)
        return "response time is 2-5 Hours"


async def _handle_buffered_messages_for_subscriber(subscriber_id: str, ig_username: str, message_payloads: List[Dict], bg_tasks: BackgroundTasks, batch_start_time_s: float):
    """
    Core logic to process a batch of buffered messages for a subscriber.
    Moved from the main body of process_manychat_webhook.
    """
    logger.info(
        f"[_handle_buffered_messages_for_subscriber] Processing {len(message_payloads)} buffered messages for SID: {subscriber_id}, IG: {ig_username}")

    combined_message_text_parts = []
    last_full_payload = None

    for p_data in message_payloads:
        current_msg_text = p_data.get("last_input_text", "")
        if not current_msg_text:
            current_msg_text = p_data.get("o1 input", "")

        current_media_url = None
        current_message_type = None
        latest_message_object = p_data.get("message")

        if isinstance(latest_message_object, dict):
            if not current_msg_text:
                current_msg_text = latest_message_object.get("text", "")

            # Only proceed to check attachments if latest_message_object is a dictionary
            if "attachments" in latest_message_object and latest_message_object["attachments"]:
                attachment = latest_message_object["attachments"][0]
                current_media_url = attachment.get("url")
                current_message_type = attachment.get("type")
                # Normalize audio type from common file extensions if type is 'file'
                if current_message_type == "file" and current_media_url and any(ext in current_media_url for ext in [".mp3", ".ogg", ".wav", ".m4a"]):
                    current_message_type = "audio"
        # Handle cases where 'message' might be a string
        elif isinstance(latest_message_object, str):
            if not current_msg_text:
                # Reverted: was latest_message_object.get("text", "")
                current_msg_text = latest_message_object
        # If latest_message_object is None or not a dict/str, current_msg_text remains as is (or empty)

        text_for_this_message_segment = current_msg_text
        if current_media_url:
            if not text_for_this_message_segment:
                text_for_this_message_segment = current_media_url
            elif current_media_url not in text_for_this_message_segment:
                text_for_this_message_segment = f"{text_for_this_message_segment} {current_media_url}"

        if text_for_this_message_segment:
            combined_message_text_parts.append(text_for_this_message_segment)

        last_full_payload = p_data

    # === SMART MESSAGE COMBINATION: Handle repeated messages intelligently ===
    if len(combined_message_text_parts) == 1:
        # Single message - use as-is
        final_combined_message_text = combined_message_text_parts[0].strip()
    elif len(combined_message_text_parts) > 1:
        # Multiple messages - check for repetition
        message_counts = {}
        unique_messages = []

        for msg in combined_message_text_parts:
            msg_clean = msg.strip()
            if msg_clean:
                if msg_clean in message_counts:
                    message_counts[msg_clean] += 1
                else:
                    message_counts[msg_clean] = 1
                    unique_messages.append(msg_clean)

        # Build final message with smart formatting
        formatted_parts = []
        for msg in unique_messages:
            count = message_counts[msg]
            if count > 1:
                formatted_parts.append(f"[{count}x] {msg}")
            else:
                formatted_parts.append(msg)

        final_combined_message_text = " ".join(formatted_parts)
    else:
        final_combined_message_text = ""
    # === END SMART MESSAGE COMBINATION ===

    if not final_combined_message_text:
        logger.info(
            f"Buffer for {subscriber_id} (IG: {ig_username}) contained no text after combining. Skipping.")
        return

    logger.info(
        f"Combined message for SID {subscriber_id} (IG: {ig_username}): '{final_combined_message_text[:200]}...'")

    # Process the combined message ONCE for media content.
    # This processed version will be used for history, AI prompts, and logging.
    processed_final_combined_message_text = process_conversation_for_media(
        final_combined_message_text)
    logger.info(
        f"Message after processing media (for history, prompts, logging): {processed_final_combined_message_text[:200]}...")

    # The original final_combined_message_text will be passed to detect_and_handle_action
    # to ensure its internal URL extraction works correctly.
    # The block that created 'text_for_action_detection' by replacing URL with raw analysis is removed.

    first_name_for_analytics = last_full_payload.get("first_name", "")
    last_name_for_analytics = last_full_payload.get("last_name", "")

    # Get user data (including conversation history up to this point)
    # Note: full_conversation_history here is a reference to the list within metrics_dict (or a loaded structure)
    # We will not append the current user message here; update_analytics_data will handle it.
    full_conversation_history, metrics_dict, user_id_key = get_user_data(
        ig_username=ig_username,
        subscriber_id=subscriber_id
    )

    # === NEW: On-demand bio analysis check ===
    # Check if this user has bio analysis data, and trigger analysis if missing
    # This runs as a background task to not block webhook processing
    if ig_username and ig_username.strip():
        bg_tasks.add_task(check_and_trigger_bio_analysis,
                          ig_username, subscriber_id)
        logger.debug(f"🔍 Queued bio analysis check for {ig_username}")
    # === END NEW ===

    # === NEW: Prepare conversation history for the prompt, including the current message(s) ===
    # Start with the history fetched from the DB
    history_for_prompt = full_conversation_history.copy()

    # Add the current user message(s) to the history for the prompt ONLY.
    # Use the batch_start_time_s for the timestamp of the user's message(s).
    # Use get_melbourne_time_str or a similar formatter for consistency if needed, but ISO format is often fine.
    # Using ISO format derived from batch_start_time_s to reflect arrival time more accurately than datetime.now()
    user_message_timestamp_iso = datetime.fromtimestamp(
        batch_start_time_s).isoformat()

    # Skipping adding the processed user message to `history_for_prompt` to avoid
    # duplication in the final prompt (it is already included in the dedicated
    # "Last User Message" block).
    # if processed_final_combined_message_text:
    #     history_for_prompt.append({
    #         "timestamp": user_message_timestamp_iso,
    #         "type": "user",
    #         "text": processed_final_combined_message_text
    #     })

    # Format this expanded history list for the prompt
    formatted_history_for_prompt_str = format_conversation_history(
        history_for_prompt)
    # === END NEW ===

    # detect_and_handle_action receives the ORIGINAL combined message text.
    action_handled = await detect_and_handle_action(ig_username, final_combined_message_text, subscriber_id, last_full_payload, batch_start_time_s)

    ai_response_for_analytics = ""

    if not action_handled:
        logger.info(
            f"No specific action detected for {ig_username} (from combined message), proceeding to general AI response.")

        # === AD DETECTION: Check if this is a plant-based challenge ad response ===
        try:
            # Only run ad detection for new/recent conversations (first 3 messages)
            if len(full_conversation_history) <= 3:
                is_ad_response, scenario, confidence = await detect_ad_intent_with_context(ig_username, final_combined_message_text, full_conversation_history)

                if is_ad_response and confidence >= 70:  # High confidence threshold
                    challenge_types = {1: 'vegan',
                                       2: 'vegetarian', 3: 'plant_based'}
                    challenge_type = challenge_types.get(
                        scenario, 'plant_based')
                    logger.info(
                        f"[detect_and_handle_action] Detected Plant-Based Challenge ad response from {ig_username} (confidence: {confidence}%, type: {challenge_type}) - triggering ad flow")

                    # Set initial flags without full analytics update
                    try:
                        from app.dashboard_modules.dashboard_sqlite_utils import update_analytics_data
                        update_analytics_data(
                            subscriber_id=subscriber_id,
                            ig_username=ig_username,
                            message_text=final_combined_message_text,
                            message_direction="incoming",
                            timestamp=user_message_timestamp_iso,
                            first_name=first_name_for_analytics,
                            last_name=last_name_for_analytics,
                            is_in_ad_flow=True,
                            ad_script_state="initial",
                            ad_scenario=scenario,
                            lead_source="plant_based_challenge"
                        )
                        logger.info(f"✅ Set ad flow flags for {ig_username}")
                    except Exception as flag_e:
                        logger.error(
                            f"❌ Error setting ad flow flags for {ig_username}: {flag_e}")

                    # Call the ad response handler
                    ad_handled = await handle_ad_response(
                        ig_username=ig_username,
                        message_text=final_combined_message_text,
                        subscriber_id=subscriber_id,
                        first_name=first_name_for_analytics,
                        last_name=last_name_for_analytics,
                        user_message_timestamp_iso=user_message_timestamp_iso
                    )

                    if ad_handled:
                        logger.info(
                            f"✅ Ad response handled successfully for {ig_username}")
                        return  # Exit early since ad was handled
                    else:
                        logger.warning(
                            f"⚠️ Ad response handling failed for {ig_username}, falling back to general response")
                else:
                    logger.info(
                        f"[detect_and_handle_action] No ad response detected for {ig_username} (confidence: {confidence}%)")
            else:
                logger.info(
                    f"[detect_and_handle_action] Skipping ad detection for {ig_username} - conversation too long ({len(full_conversation_history)} messages)")
        except Exception as ad_e:
            logger.error(f"❌ Error in ad detection for {ig_username}: {ad_e}")
        # === END AD DETECTION ===
        current_stage = metrics_dict.get(
            'journey_stage', {}).get('current_stage', "Topic 1")
        trial_status = metrics_dict.get('trial_status', "Initial Contact")

        calculated_full_name = f"{first_name_for_analytics} {last_name_for_analytics}".strip(
        )
        if not calculated_full_name:  # Fallback
            full_name_from_metrics_fn = metrics_dict.get('first_name', '')
            full_name_from_metrics_ln = metrics_dict.get('last_name', '')
            calculated_full_name = f"{full_name_from_metrics_fn} {full_name_from_metrics_ln}".strip(
            )
        if not calculated_full_name:
            calculated_full_name = ig_username

        # ---- ADDED: Fetch few-shot examples ----
        few_shot_examples = []  # Default to empty list
        try:
            few_shot_examples = get_good_few_shot_examples(
                limit=100)  # MODIFIED: Fetch up to 100 examples (increased from 50)
            if few_shot_examples:
                logger.info(
                    f"Successfully fetched {len(few_shot_examples)} few-shot examples for {ig_username}.")
            else:
                logger.info(f"No few-shot examples found for {ig_username}.")
        except Exception as e_fs:
            logger.error(
                f"Error fetching few-shot examples for {ig_username}: {e_fs}", exc_info=True)
        # ---- END ADDED ----

        # Use the processed message for the AI prompt
        prompt_str_for_ai, prompt_type = build_member_chat_prompt(
            client_data=metrics_dict,
            current_message=processed_final_combined_message_text,  # Use processed message
            current_stage=current_stage,
            trial_status=trial_status,
            full_name=calculated_full_name,
            # Pass the prepared history string
            full_conversation_string=formatted_history_for_prompt_str,
            few_shot_examples=few_shot_examples  # MODIFIED: Pass examples
        )
        ai_raw_response_text = await get_ai_response(prompt_str_for_ai)

        # Post-process the response using the processed user message for context
        if ai_raw_response_text:
            # Use processed message
            ai_raw_response_text = await filter_shannon_response(ai_raw_response_text, processed_final_combined_message_text)

        if ai_raw_response_text:
            ai_response_for_analytics = ai_raw_response_text  # This is the filtered response

            # ---- NEW: Check for challenge offers and create notifications ----
            offer_notification_created = False
            try:
                import sys
                import os
                app_dashboard_modules_path = os.path.join(
                    os.path.dirname(__file__), 'app', 'dashboard_modules')
                if app_dashboard_modules_path not in sys.path:
                    sys.path.insert(0, app_dashboard_modules_path)

                from notifications import check_ai_response_for_challenge_offer

                # Check if this AI response contains a challenge offer
                if check_ai_response_for_challenge_offer(ai_raw_response_text, ig_username):
                    logger.info(
                        f"🎯 Challenge offer notification created for {ig_username}")
                    offer_notification_created = True  # Set flag if notification was created
            except Exception as notif_e:
                logger.warning(
                    f"Could not check for challenge offer notification: {notif_e}")
            # ---- END NEW ----

            # ---- MODIFICATION: Check Auto Mode and either auto-schedule or queue for review ----
            incoming_msg_ts_iso = datetime.fromtimestamp(
                batch_start_time_s).isoformat()

            review_id = None  # Initialize review_id to None

            # Check auto mode status (both general and vegan modes)
            should_auto_process = False
            try:
                # Import the auto mode checkers
                import sys
                import os
                app_dashboard_modules_path = os.path.join(
                    os.path.dirname(__file__), 'app', 'dashboard_modules')
                if app_dashboard_modules_path not in sys.path:
                    sys.path.insert(0, app_dashboard_modules_path)

                from auto_mode_state import is_auto_mode_active, is_vegan_auto_mode_active

                # Check general auto mode
                general_auto_active = is_auto_mode_active()

                # Check vegan auto mode
                vegan_auto_active = is_vegan_auto_mode_active()

                if general_auto_active:
                    logger.info(
                        f"🤖 GENERAL AUTO MODE ACTIVE - Auto-processing {ig_username}")
                    should_auto_process = True
                elif vegan_auto_active:
                    # Check if user is a fresh vegan
                    try:
                        from dashboard_sqlite_utils import get_db_connection
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT is_fresh_vegan 
                            FROM conversation_strategy_log 
                            WHERE username = ? AND is_fresh_vegan = 1
                            LIMIT 1
                        """, (ig_username,))
                        result = cursor.fetchone()
                        conn.close()

                        if result:
                            logger.info(
                                f"🌱 VEGAN AUTO MODE ACTIVE - Auto-processing fresh vegan {ig_username}")
                            should_auto_process = True
                        else:
                            logger.info(
                                f"🌱 Vegan auto mode active but {ig_username} is not a fresh vegan - manual review required")
                            should_auto_process = False
                    except Exception as e:
                        logger.warning(
                            f"Could not check vegan status for {ig_username}: {e}")
                        should_auto_process = False
                else:
                    logger.info(
                        f"No auto mode active - {ig_username} requires manual review")
                    should_auto_process = False

            except ImportError:
                logger.warning(
                    "Could not import auto_mode_state, assuming Auto Mode is OFF.")
                should_auto_process = False

            if should_auto_process:
                logger.info(
                    f"🤖 AUTO MODE ACTIVE - Auto-scheduling response for {ig_username}")
                try:
                    # Ensure the scheduled responses table exists
                    conn = db_utils.get_db_connection()
                    create_scheduled_responses_table_if_not_exists(conn)
                    conn.close()

                    # Add to the review queue first, but with 'auto_scheduled' status
                    review_id = add_response_to_review_queue(
                        user_ig_username=ig_username,
                        user_subscriber_id=subscriber_id,
                        incoming_message_text=processed_final_combined_message_text,
                        incoming_message_timestamp=user_message_timestamp_iso,
                        generated_prompt_text=prompt_str_for_ai,
                        proposed_response_text=ai_raw_response_text,
                        prompt_type=prompt_type,
                        status='auto_scheduled'  # MODIFIED: Set status directly
                    )

                    if review_id:
                        # Now schedule the response with timing delay
                        from response_review import schedule_auto_response
                        success_schedule, schedule_message, delay_minutes = schedule_auto_response(
                            # Create a mock review_item for the function
                            {
                                'review_id': review_id,
                                'user_ig_username': ig_username,
                                'user_subscriber_id': subscriber_id,
                                'incoming_message_text': processed_final_combined_message_text,
                                'incoming_message_timestamp': user_message_timestamp_iso,
                                'proposed_response': ai_raw_response_text,
                                'status': 'auto_scheduled'
                            },
                            ai_raw_response_text,
                            user_notes="",
                            manual_context=""
                        )

                        if success_schedule:
                            logger.info(
                                f"✅ AUTO-SCHEDULED: {ig_username} - Response queued for {delay_minutes} minutes")
                        else:
                            logger.error(
                                f"❌ Auto-schedule FAILED for {ig_username}: {schedule_message}")
                    else:
                        logger.error(
                            f"❌ Failed to add auto-scheduled review for {ig_username}")

                except Exception as e_auto:
                    logger.error(
                        f"❌ Failed to auto-schedule for {ig_username}, falling back to manual review: {e_auto}", exc_info=True)
                    # Fallback: Add to review queue without scheduling
                    review_id = add_response_to_review_queue(
                        user_ig_username=ig_username,
                        user_subscriber_id=subscriber_id,
                        incoming_message_text=processed_final_combined_message_text,
                        incoming_message_timestamp=user_message_timestamp_iso,
                        generated_prompt_text=prompt_str_for_ai,
                        proposed_response_text=ai_raw_response_text,
                        prompt_type=prompt_type
                    )
            else:
                # --- ADDED: Standard behavior when auto-mode is OFF ---
                logger.info(
                    f"Auto mode is OFF. Adding response for {ig_username} to review queue.")
                review_id = add_response_to_review_queue(
                    user_ig_username=ig_username,
                    user_subscriber_id=subscriber_id,
                    incoming_message_text=processed_final_combined_message_text,
                    incoming_message_timestamp=user_message_timestamp_iso,
                    generated_prompt_text=prompt_str_for_ai,
                    proposed_response_text=ai_raw_response_text,
                    prompt_type=prompt_type
                )
                if review_id:
                    logger.info(
                        f"Successfully added response for {ig_username} to review queue (Review ID: {review_id})")
                else:
                    logger.error(
                        f"Failed to add response to review queue for {ig_username}")
                # --- END ADDED ---

            if review_id:
                logger.info(
                    f"Successfully queued response for review (ID: {review_id}) for SID: {subscriber_id}")
                # Optionally, you could set a generic ManyChat field here to indicate message received, e.g.:
                # update_manychat_fields(subscriber_id, {"last_message_status": "received_processing"})
            else:
                logger.error(
                    f"Failed to queue response for review for SID: {subscriber_id}. The AI response was: {ai_raw_response_text[:100]}...")
                # Decide on fallback: send directly, or send error message?
                # For now, let's log and it won't be sent, nor explicitly error out to user.

            # --- ONBOARDING TRIGGER DETECTION ---
            # Phrase to START the onboarding question sequence (updates analytics, uses ONBOARDING_PROMPT_TEMPLATE next time)
            initiate_onboarding_questions_phrase = "get you onboarded"  # More general phrase
            # Phrase to trigger the PostOnboardingHandler (AFTER onboarding questions are done)
            ai_full_onboarding_complete_phrase = "No worries! Ill let you know when your set up, and youll get an invite via email from me! Let me get into this! Chat in a bit!".lower()

            if initiate_onboarding_questions_phrase.lower() in ai_response_for_analytics.lower():
                logger.info(
                    f"[ONBOARDING QUESTIONS START] AI response '{ai_response_for_analytics[:50]}...' triggered start of onboarding questions for {ig_username} (SubID: {subscriber_id}).")
                analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
                try:
                    with open(analytics_file_path, "r+") as f:  # Open for reading and writing
                        analytics_data = json.load(f)
                        target_user_id_for_onboarding = None
                        conversations_data_onboarding = analytics_data.get(
                            'conversations', {})
                        search_ig_username_lower_onboarding = ig_username.strip().lower()

                        # Find user by subscriber_id first, then by ig_username if not found
                        found_by_sub_id = False
                        for user_id_loop_onboarding, user_data_loop_onboarding in conversations_data_onboarding.items():
                            if isinstance(user_data_loop_onboarding, dict):
                                metrics_data_onboarding = user_data_loop_onboarding.get(
                                    "metrics", {})
                                if isinstance(metrics_data_onboarding, dict) and metrics_data_onboarding.get("subscriber_id") == subscriber_id:
                                    target_user_id_for_onboarding = user_id_loop_onboarding
                                    found_by_sub_id = True
                                    break

                        if not found_by_sub_id:  # Fallback to ig_username if not found by subscriber_id
                            for user_id_loop_onboarding, user_data_loop_onboarding in conversations_data_onboarding.items():
                                if isinstance(user_data_loop_onboarding, dict):
                                    metrics_data_onboarding = user_data_loop_onboarding.get(
                                        "metrics", {})
                                    if isinstance(metrics_data_onboarding, dict):
                                        json_ig_username_onboarding = metrics_data_onboarding.get(
                                            "ig_username", None)
                                        if isinstance(json_ig_username_onboarding, str) and json_ig_username_onboarding.strip().lower() == search_ig_username_lower_onboarding:
                                            target_user_id_for_onboarding = user_id_loop_onboarding
                                            break

                        if target_user_id_for_onboarding and target_user_id_for_onboarding in conversations_data_onboarding:
                            metrics_to_update_onboarding = conversations_data_onboarding[target_user_id_for_onboarding].setdefault(
                                'metrics', {})
                            if not metrics_to_update_onboarding.get('is_onboarding', False):
                                metrics_to_update_onboarding['is_onboarding'] = True
                                # Or your desired first step
                                metrics_to_update_onboarding['expected_onboarding_input'] = "all_meals"
                                # Optionally clear previous target calculations if re-onboarding
                                metrics_to_update_onboarding.pop(
                                    'target_calories', None)
                                metrics_to_update_onboarding.pop(
                                    'target_protein', None)
                                metrics_to_update_onboarding.pop(
                                    'target_carbs', None)
                                metrics_to_update_onboarding.pop(
                                    'target_fats', None)
                                logger.info(
                                    f"[ONBOARDING QUESTIONS START] Set is_onboarding=true for user {target_user_id_for_onboarding}")
                                # Rewind to the beginning of the file
                                f.seek(0)
                                json.dump(analytics_data, f, indent=2)
                                f.truncate()  # Remove remaining part of old file
                                logger.info(
                                    f"[ONBOARDING QUESTIONS START] Saved updated onboarding state for {target_user_id_for_onboarding}")
                            else:
                                logger.info(
                                    f"[ONBOARDING QUESTIONS START] User {target_user_id_for_onboarding} already has is_onboarding=true.")
                        else:
                            logger.error(
                                f"[ONBOARDING QUESTIONS START] Could not find user {ig_username} (SubID: {subscriber_id}) in analytics data to set is_onboarding=true.")
                except (FileNotFoundError, json.JSONDecodeError, IOError) as e_analytics:
                    logger.error(
                        f"[ONBOARDING QUESTIONS START] Error accessing/updating analytics_data_good.json: {e_analytics}")

            # Separated logic for PostOnboardingHandler
            elif ai_full_onboarding_complete_phrase.lower() in ai_response_for_analytics.lower():
                logger.info(
                    f"[POST ONBOARDING HANDLER] AI response triggered PostOnboardingHandler for {ig_username} (subscriber_id: {subscriber_id}).")
                post_onboarding_handler = PostOnboardingHandler(
                    gemini_api_key=GEMINI_API_KEY)

                onboarding_task_payload = functools.partial(
                    post_onboarding_handler.process_onboarding_completion,
                    ig_username=ig_username,
                    subscriber_id=subscriber_id,  # Ensure subscriber_id is passed
                    conversation_history=full_conversation_history  # Pass the up-to-date history
                )
                bg_tasks.add_task(onboarding_task_payload)
                logger.info(
                    f"[POST ONBOARDING HANDLER] Full onboarding process for {ig_username} (subscriber_id: {subscriber_id}) scheduled in background.")
        else:
            logger.warning(
                f"No AI response generated for {ig_username} (from combined message)")
            ai_response_for_analytics = "[AI FAILED TO RESPOND]"
    else:
        logger.info(
            f"Action handled for {ig_username} (from combined message), AI response might have been sent by action handler.")
        # Ensure ai_response_for_analytics is set if an action was handled,
        # for consistent logging to update_analytics_data.
        # This might need to come from the return value of detect_and_handle_action if it sends a response.
        if not ai_response_for_analytics:  # If not already set by a sub-function of action_handled
            ai_response_for_analytics = "[Action implicitly handled by detect_and_handle_action or no AI response needed]"

    # update_analytics_data will save the processed_final_combined_message_text as the user's message
    # and the ai_response_for_analytics as the AI's response to the conversation history.
    # Convert batch_start_time_s to ISO format for the user message timestamp
    user_message_timestamp_iso = datetime.fromtimestamp(
        batch_start_time_s).isoformat()

    update_analytics_data(
        ig_username=ig_username,
        user_message=processed_final_combined_message_text,  # Use processed message
        ai_response=ai_response_for_analytics,
        subscriber_id=subscriber_id,
        first_name=first_name_for_analytics,
        last_name=last_name_for_analytics,
        user_message_timestamp=user_message_timestamp_iso  # Pass the actual timestamp
    )
    logger.info(
        f"Finished processing buffered messages for SID {subscriber_id}")


async def run_core_processing_after_buffer(subscriber_id: str, ig_username: str, bg_tasks: BackgroundTasks):
    """
    Waits for BUFFER_WINDOW, then retrieves and processes all messages for the subscriber.
    """
    logger.info(
        f"[run_core_processing_after_buffer] Task started for SID: {subscriber_id}, IG: {ig_username}. Waiting {BUFFER_WINDOW}s.")

    try:
        await asyncio.sleep(BUFFER_WINDOW)
    except asyncio.CancelledError:
        logger.info(
            f"[run_core_processing_after_buffer] Task was canceled for SID: {subscriber_id} - timer restarted by new message")
        return

    logger.info(
        f"[run_core_processing_after_buffer] Wait finished for SID: {subscriber_id}. Attempting to process buffer.")

    # Clean up task tracking
    user_buffer_task_scheduled.pop(subscriber_id, None)
    user_buffer_tasks.pop(subscriber_id, None)

    # buffered_message_payloads is a list of dicts like {"payload": data, "user_msg_created_at_s": timestamp}
    buffered_message_items = manychat_message_buffer.pop(subscriber_id, [])

    if not buffered_message_items:
        logger.info(
            f"No messages found in buffer for SID: {subscriber_id} after delay. Exiting task.")
        return

    # Extract payloads and find the earliest user message timestamp in the batch
    message_payloads_only = []
    batch_start_time_s = float('inf')
    if buffered_message_items:  # Ensure not empty before trying to access
        batch_start_time_s = buffered_message_items[0].get(
            "user_msg_created_at_s", time.time())  # Default to now if somehow missing

    for item in buffered_message_items:
        message_payloads_only.append(item["payload"])
        if "user_msg_created_at_s" in item:
            batch_start_time_s = min(
                batch_start_time_s, item["user_msg_created_at_s"])

    # If buffer was empty or items had no timestamp
    if batch_start_time_s == float('inf'):
        batch_start_time_s = time.time()
        logger.warning(
            f"Could not determine batch_start_time_s for SID {subscriber_id}, defaulting to current time.")

    logger.info(
        f"🔄 Processing {len(buffered_message_items)} buffered messages for SID {subscriber_id} after {BUFFER_WINDOW}s wait. Batch start: {datetime.fromtimestamp(batch_start_time_s).isoformat()}")

    await _handle_buffered_messages_for_subscriber(subscriber_id, ig_username, message_payloads_only, bg_tasks, batch_start_time_s)

# --- Helper function for actual form check video analysis ---


async def _analyze_form_check_video(ig_username: str, client_name_for_todo: str, video_url: str, user_desc_text: str, subscriber_id: str, batch_start_time_s: float):
    logger.info(
        f"[_analyze_form_check_video] Analyzing: {video_url[:60]} for {ig_username}")
    analysis_result_text = ""
    user_message_for_analytics = f"(Sent form check video: {video_url[:50]}... Description: '{user_desc_text[:30]}')"
    ai_response_for_analytics = ""

    try:
        analysis_result_text = get_video_analysis(
            video_url,
            GEMINI_API_KEY,
            GEMINI_MODEL_PRO,
            GEMINI_MODEL_FLASH,
            GEMINI_MODEL_FLASH_STANDARD
            # user_description=user_desc_text # This parameter is not accepted by get_video_analysis
        )
    except Exception as e:
        logger.error(f"Error calling get_video_analysis: {e}", exc_info=True)
        analysis_result_text = "Sorry, I encountered an error trying to analyze your video. Please try again later."

    if not analysis_result_text or "error" in analysis_result_text.lower() or "failed" in analysis_result_text.lower():
        response_to_user = analysis_result_text if analysis_result_text else "Sorry, couldn't analyze the video. Please try sending it again."
        logger.error(
            f"Video analysis failed for {ig_username}. Result: {analysis_result_text}")
        add_todo_item(ig_username, client_name_for_todo,
                      f"Video form check FAILED for: {video_url[:50]}...")
        ai_response_for_analytics = f"AI FAILED video form check. Reported: {response_to_user[:100]}"
    else:
        response_to_user = analysis_result_text
        add_todo_item(ig_username, client_name_for_todo,
                      f"Video form check COMPLETED for: {video_url[:50]}...", status="completed")
        ai_response_for_analytics = f"AI provided form check analysis. Analysis: {response_to_user[:100]}"

    field_updates = {"o1 Response": response_to_user,
                     "CONVERSATION": user_message_for_analytics}

    # For form check video analysis, explicitly set "response time" to "action"
    field_updates["response time"] = "action"
    logger.info(
        f"[_analyze_form_check_video] Set 'response time' to 'action' for SID {subscriber_id}")
    # Remove time_diff_seconds_for_bucket and related logging as it's not used for the bucket value here.
    # last_bot_sent_ts = manychat_last_bot_sent_timestamps.get(subscriber_id) # Keep if needed for other logic/logging

    # if last_bot_sent_ts is not None:
    #     # batch_start_time_s is the timestamp of the current user's message (earliest in batch that led to this analysis)
    #     time_diff_seconds_for_bucket = batch_start_time_s - last_bot_sent_ts
    #     logger.info(
    #         f"[_analyze_form_check_video] User message at {datetime.fromtimestamp(batch_start_time_s).isoformat()}, last bot message at {datetime.fromtimestamp(last_bot_sent_ts).isoformat()}. Difference for bucket: {time_diff_seconds_for_bucket:.2f}s"
    #     )
    # else:
    #     # Fallback to current reaction time for this analysis if no prior bot message.
    #     time_diff_seconds_for_bucket = time.time() - batch_start_time_s # Bot's actual processing time for this analysis
    #     logger.info(
    #         f"[_analyze_form_check_video] No last bot message timestamp for SID {subscriber_id}. Using current bot reaction time for bucket: {time_diff_seconds_for_bucket:.2f}s"
    #     )

    # response_bucket = get_response_time_bucket(time_diff_seconds_for_bucket) # No longer using this for "action"
    # field_updates["response time"] = response_bucket # Replaced by direct "action"
    # logger.info(
    #     f"[_analyze_form_check_video] Calculated time diff for bucket: {time_diff_seconds_for_bucket:.2f}s, Bucket: {response_bucket} for SID {subscriber_id}")

    if update_manychat_fields(subscriber_id, field_updates):
        manychat_last_bot_sent_timestamps[subscriber_id] = time.time()

    # Analytics update (using the specific subscriber_id and names associated with this video message if available)
    # Assuming first_name, last_name might need to be fetched or passed if not available in this scope directly from detect_and_handle_action's main params
    # For simplicity, using what's available. If data dictionary is passed to this helper, it can be used.
    # This needs to be called from detect_and_handle_action to have access to first_name, last_name for the specific message.
    # So, _analyze_form_check_video should return what's needed for analytics update, or analytics updated after it returns.
    # For now, returning the strings for analytics update in the main function.

    logger.info(
        f"Finished _analyze_form_check_video for {ig_username}. AI Response for analytics: {ai_response_for_analytics}")
    # Return these for the main function to log
    return user_message_for_analytics, ai_response_for_analytics


# Global dictionary to track pending form check requests
form_check_pending: Dict[str, bool] = {}

# --- Add post-processing function to filter Gemini responses ---


async def filter_shannon_response(original_response: str, user_message: str = None) -> str:
    """
    Ensures the response is a direct, in-character reply from Shannon. If not, rewrites it as one.
    The filter should be conservative: if the original response is already good, it should be returned unchanged.
    """
    # Example removed for brevity, as it's not directly used by the model, only for human understanding of Shannon's style.

    user_message_block = f"[CLIENT'S MESSAGE (if provided)]\n{user_message}\n" if user_message else "(No specific client message provided for this turn)"

    filter_prompt = f"""
Your task is to ensure an AI-generated response sounds like it's from Shannon, a friendly and knowledgeable fitness coach, and that it's a direct reply to a client. Shannon uses casual Aussie colloquialisms.

Here is the AI-generated response you need to evaluate:
[GENERATED RESPONSE]
{original_response}

Here was the client's message the AI was responding to (if available):
{user_message_block}

**Crucial Evaluation & Decision Process:**

1.  **Is the [GENERATED RESPONSE] ALREADY a direct, conversational message that Shannon would send?**
    *   Does it sound like a human coach chatting on Instagram?
    *   Is it free of any AI self-references (e.g., \"As an AI...\", \"I am a language model...\"), meta-commentary about the conversation (e.g., \"This response aims to...\", \"Based on the conversation history...\"), or explanations of its own thought process?

2.  **DECISION:**
    *   **IF YES** (the [GENERATED RESPONSE] is already a good, direct, in-character message from Shannon, and contains NO AI self-references or meta-commentary as described above):
        **Your output MUST be the [GENERATED RESPONSE] EXACTLY as it is.** Do not add any extra text or explanation. Just output the original response.

    *   **IF NO** (the [GENERATED RESPONSE] contains AI-like meta-commentary, explains itself, refers to itself as an AI, or is otherwise clearly not a direct message Shannon would type):
        **Then you MUST rewrite it.** Your rewritten message should be a perfect, direct, in-character reply that Shannon would send, completely removing any AI-like analysis or self-explanation. Output ONLY the rewritten message.

Your Output (either the original [GENERATED RESPONSE] or your rewritten version):
"""

    # Use the fastest model for filtering
    filtered = await call_gemini_with_retry(GEMINI_MODEL_FLASH, filter_prompt)

    # Clean up any markdown or code block formatting from the filter's output
    if filtered:
        filtered = filtered.strip()
        # Remove potential ```json or ``` markdown blocks if Gemini adds them
        if filtered.startswith("```json"):
            filtered = filtered[len("```json"):].strip()
            if filtered.endswith("```"):
                filtered = filtered[:-len("```")].strip()
        elif filtered.startswith("```"):
            filtered = filtered[len("```"):].strip()
            if filtered.endswith("```"):
                filtered = filtered[:-len("```")].strip()

    # Log if a change was made
    original_check = original_response.strip().lower()
    filtered_check = filtered.strip().lower() if filtered else ""

    if filtered and original_check != filtered_check:
        logger.info(
            f"[FILTER] Gemini response was modified by the filter.\nOriginal: {original_response}\nFiltered: {filtered}")
    elif not filtered:
        logger.warning(
            f"[FILTER] Filter returned an empty response. Falling back to original. Original: {original_response}")
        return original_response  # Fallback to original if filter fails to produce content
    else:
        logger.info(
            "[FILTER] Gemini response passed filter unchanged (or with only minor whitespace/case changes).")

    # Return filtered, or original if filtering resulted in None/empty
    return filtered or original_response


@app.post("/webhook/wix-onboarding")
async def process_wix_form_submission(request: Request, background_tasks: BackgroundTasks):
    """
    Process Wix form submissions from the coaching onboarding form.
    Maps Wix form data to existing client_data structure and triggers meal plan generation.
    """
    try:
        # Get the form data from Wix
        raw_body = await request.body()
        payload_str = raw_body.decode('utf-8')
        logger.info(
            f"[WIX-WEBHOOK] Received raw payload: {payload_str[:500]}...")

        try:
            wix_data = json.loads(payload_str)
            logger.info(
                f"[WIX-WEBHOOK] Parsed Wix form data: {json.dumps(wix_data, indent=2)[:1000]}...")
        except json.JSONDecodeError:
            logger.error("[WIX-WEBHOOK] Failed to parse JSON payload")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        # Extract form fields from Wix data
        # Note: Wix form field structure may vary - we'll need to adjust based on actual payload
        # Handle different Wix webhook structures
        form_data = wix_data.get('data', {}) or wix_data

        # Map Wix form data to our client_data structure
        client_data = _map_wix_form_to_client_data(form_data)

        if not client_data:
            logger.error(
                "[WIX-WEBHOOK] Failed to map Wix form data to client structure")
            return PlainTextResponse("Error: Could not process form data", status_code=400)

        logger.info(
            f"[WIX-WEBHOOK] Successfully mapped Wix data to client structure for: {client_data.get('personal_info', {}).get('full_name', {}).get('value', 'Unknown')}")

        # Generate a fake Instagram username and subscriber_id for the system
        email = client_data['personal_info']['email']['value']
        # Create username from email
        ig_username = f"wix_user_{email.split('@')[0]}"
        subscriber_id = f"wix_{int(time.time())}"  # Timestamp-based ID

        # Process the onboarding in the background using existing system
        background_tasks.add_task(
            _process_wix_onboarding_background,
            ig_username,
            subscriber_id,
            client_data
        )

        logger.info(
            f"[WIX-WEBHOOK] Scheduled background processing for {ig_username}")

        return PlainTextResponse("Form submitted successfully! Your meal plan and workout program are being created.", status_code=200)

    except Exception as e:
        logger.error(
            f"[WIX-WEBHOOK] Error processing Wix form submission: {str(e)}")
        logger.error(
            f"[WIX-WEBHOOK] Exception details: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Error processing form submission: {str(e)}")


def _map_wix_form_to_client_data(form_data: Dict) -> Optional[Dict]:
    """
    Map Wix form fields to the client_data structure expected by the meal plan system.
    This matches the structure used in post_onboarding_handler.py
    """
    try:
        # Extract common field patterns from Wix forms
        # Note: Field names will need to be adjusted based on actual Wix form field names

        # Handle Wix form structure - data is in submissions array
        submissions = form_data.get('submissions', [])

        # Create lookup dictionary from submissions
        field_map = {}
        for submission in submissions:
            label = submission.get('label', '').lower()
            value = submission.get('value', '')
            field_map[label] = value

        # Personal Information - using Wix form labels
        email = field_map.get('email') or form_data.get('email')
        first_name = field_map.get('first name') or field_map.get('firstname')
        last_name = field_map.get('last name') or field_map.get('lastname')
        phone = field_map.get('phone') or field_map.get('phonenumber')

        full_name = f"{first_name or ''} {last_name or ''}".strip()
        if not full_name:
            full_name = 'Unknown'

        # Physical Stats - using Wix form labels
        weight_str = field_map.get('weight', '').replace(
            'kgs', '').replace('kg', '').strip()
        weight = float(weight_str) if weight_str.replace(
            '.', '').isdigit() else 70

        height_str = field_map.get('height', '').replace('cm', '').strip()
        height = float(height_str) if height_str.replace(
            '.', '').isdigit() else 170

        # Calculate age from birthday if available
        birthday = field_map.get('birthday')
        age = 30  # default
        if birthday:
            try:
                from datetime import datetime
                birth_date = datetime.strptime(birthday, '%Y-%m-%d')
                today = datetime.now()
                age = today.year - birth_date.year - \
                    ((today.month, today.day) < (birth_date.month, birth_date.day))
            except:
                age = 30

        # Fitness Information - using Wix form labels
        primary_goal = field_map.get('fitness goal') or 'muscle_gain'
        activity_level = field_map.get('activity level') or 'moderately_active'
        gym_access = field_map.get('gym access') or field_map.get(
            'training location') or 'full_gym'

        # Training Information - using Wix form labels and field names
        training_days = field_map.get('training days') or form_data.get(
            'field:which_days_time_have_you_set_aside_to_train', 'monday-friday')
        training_experience = field_map.get(
            'training experience') or 'beginner'

        # Dietary Information
        dietary_type = form_data.get('dietaryType') or form_data.get(
            'diet_type') or 'plant-based'  # Default to plant-based
        dietary_restrictions = form_data.get('dietaryRestrictions') or form_data.get(
            'restrictions') or form_data.get('allergies')
        disliked_foods = form_data.get('dislikedFoods') or form_data.get(
            'food_dislikes') or form_data.get('dislikes')

        # Meal preferences
        regular_breakfast = form_data.get(
            'regularBreakfast') or form_data.get('breakfast_preferences')
        regular_lunch = form_data.get(
            'regularLunch') or form_data.get('lunch_preferences')
        regular_dinner = form_data.get(
            'regularDinner') or form_data.get('dinner_preferences')

        # Exercise preferences
        exercise_dislikes = form_data.get('exerciseDislikes') or form_data.get(
            'exercise_limitations') or form_data.get('exercises_to_avoid')

        # Build client_data structure matching post_onboarding_handler.py format
        client_data = {
            "personal_info": {
                "email": {"value": email or "", "confidence": 95},
                "full_name": {"value": full_name, "confidence": 95},
                "phone": {"value": phone or "", "confidence": 95},
                "age": {"value": int(age) if age and str(age).isdigit() else 30, "confidence": 90}
            },
            "physical_info": {
                "weight": {"value": weight, "unit": "kg", "confidence": 95},
                "height": {"value": height, "unit": "cm", "confidence": 95},
                "target_weight": {"value": weight + 5 if primary_goal == 'muscle_gain' else weight - 5, "unit": "kg", "confidence": 90},
                "primary_fitness_goal": {"value": primary_goal, "confidence": 95}
            },
            "training_info": {
                "activity_level": {"value": activity_level or "moderately_active", "confidence": 90},
                "gym_access": {"value": gym_access or "full_gym", "confidence": 95},
                "training_days": {"value": training_days or "3-4 days per week", "confidence": 90},
                "training_experience": {"value": training_experience or "beginner", "confidence": 85}
            },
            "dietary_info": {
                "diet_type": {"value": dietary_type, "confidence": 95},
                "dietary_restrictions": {"value": dietary_restrictions or "", "confidence": 90},
                "disliked_foods": {"value": disliked_foods or "", "confidence": 90},
                "regular_meals": {
                    "breakfast": {"value": regular_breakfast or "oats with protein", "confidence": 85},
                    "lunch": {"value": regular_lunch or "salad with protein", "confidence": 85},
                    "dinner": {"value": regular_dinner or "plant-based protein with vegetables", "confidence": 85}
                }
            },
            "exercise_preferences": {
                "dislikes": {"value": exercise_dislikes or "", "confidence": 90},
                "current_routine": {"value": "none", "confidence": 95}
            }
        }

        logger.info(
            f"[WIX-MAPPING] Successfully mapped form data for: {full_name}")
        return client_data

    except Exception as e:
        logger.error(f"[WIX-MAPPING] Error mapping Wix form data: {str(e)}")
        return None


async def _process_wix_onboarding_background(ig_username: str, subscriber_id: str, client_data: Dict):
    """
    Process Wix onboarding data through the existing meal plan system.
    This uses the same pipeline as Instagram DM onboarding but with pre-structured data.
    """
    try:
        logger.info(
            f"[WIX-BG] Starting background processing for {ig_username}")

        # Import the existing post-onboarding handler
        from post_onboarding_handler import PostOnboardingHandler

        # Initialize handler with Gemini API key - try different env var names
        gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv(
            "GOOGLE_AI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y"

        logger.info(f"[WIX-BG] Using API key: {gemini_api_key[:10]}...")

        if not gemini_api_key:
            logger.error("[WIX-BG] GEMINI_API_KEY not found in environment")
            return False

        handler = PostOnboardingHandler(gemini_api_key)

        # Convert Wix data to the format expected by the nutrition calculation
        converted_client_data = _convert_wix_data_to_expected_format(
            client_data)
        if not converted_client_data:
            logger.error(
                f"[WIX-BG] Failed to convert client data format for {ig_username}")
            return False

        # Calculate nutrition data using the handler's method
        nutrition_data = handler._calculate_nutrition(converted_client_data)
        if not nutrition_data:
            logger.error(
                f"[WIX-BG] Failed to calculate nutrition data for {ig_username}")
            return False

        logger.info(f"[WIX-BG] Calculated nutrition: {nutrition_data}")

        # Use the existing method that accepts direct client data with proper nutrition override
        success_flags = await handler.process_onboarding_with_fixed_data(
            ig_username=ig_username,
            subscriber_id=subscriber_id,
            direct_client_data=converted_client_data,
            nutrition_targets_override=nutrition_data
        )

        client_added = success_flags.get("client_added_success", False)
        meal_plan_uploaded = success_flags.get(
            "meal_plan_upload_success", False)
        workout_program_built = success_flags.get(
            "workout_program_build_success", False)

        onboarding_overall_success = client_added and meal_plan_uploaded and workout_program_built

        if onboarding_overall_success:
            logger.info(
                f"[WIX-BG] Successfully processed onboarding for {ig_username}")

            # Store the successful onboarding in our database
            try:
                import sqlite3
                SQLITE_PATH = "app/analytics_data_good.sqlite"
                conn = sqlite3.connect(SQLITE_PATH)
                c = conn.cursor()

                # Use extracted client full name for consistency and better display
                client_full_name = client_data.get('personal_info', {}).get(
                    'full_name', {}).get('value', ig_username)
                client_first_name = client_data.get('personal_info', {}).get(
                    'first_name', {}).get('value', '')
                client_last_name = client_data.get('personal_info', {}).get(
                    'last_name', {}).get('value', '')

                # Insert or update user record
                c.execute("""
                    INSERT OR REPLACE INTO users 
                    (ig_username, subscriber_id, first_name, last_name, email, source, created_at)
                    VALUES (?, ?, ?, ?, ?, 'wix_form', ?)
                """, (
                    ig_username,
                    subscriber_id,
                    client_first_name,
                    client_last_name,
                    client_data.get('personal_info', {}).get(
                        'email', {}).get('value', ''),
                    datetime.now().isoformat()
                ))

                conn.commit()

                # NEW: Update client_status to 'Trial Client' after successful onboarding
                try:
                    c.execute("""
                        UPDATE users
                        SET client_status = ?
                        WHERE ig_username = ? AND subscriber_id = ?
                    """, ('Trial Client', ig_username, subscriber_id))
                    conn.commit()
                    logger.info(
                        f"[WIX-BG] Updated client_status to 'Trial Client' for {ig_username}")
                except Exception as status_update_error:
                    logger.error(
                        f"[WIX-BG] Failed to update client_status for {ig_username}: {status_update_error}")

                conn.close()
                logger.info(
                    f"[WIX-BG] Stored user record in database for {ig_username}")

            except Exception as db_error:
                logger.error(f"[WIX-BG] Database error: {db_error}")
            # --- NEW: Add dashboard notification ---
            notification_message = f"New Trial Member - {client_full_name} (IG: @{ig_username}): "
            if client_added:
                notification_message += "Client Added to Trainerize. "
            else:
                notification_message += "Client addition to Trainerize FAILED. "

            if meal_plan_uploaded:
                notification_message += "Meal Plan Successfully Added. "
            else:
                notification_message += "Meal Plan FAILED to Add. "

            if workout_program_built:
                notification_message += "Workout Program Successfully Added."
            else:
                notification_message += "Workout Program FAILED to Add."

            try:
                add_todo_item(
                    ig_username=ig_username,  # Use ig_username for the todo item
                    client_name=client_full_name,  # Use full name for better display
                    task_description=notification_message,
                    status="pending"  # Always starts as pending for review
                )
                logger.info(
                    f"[WIX-BG] Added dashboard notification for {ig_username}: {notification_message}")
            except Exception as todo_error:
                logger.error(
                    f"[WIX-BG] Failed to add todo item for onboarding status: {todo_error}")

        else:
            logger.error(
                f"[WIX-BG] Failed to process onboarding for {ig_username}")
            client_full_name = client_data.get('personal_info', {}).get(
                'full_name', {}).get('value', ig_username)
            error_notification_message = f"Onboarding FAILED for {client_full_name} (IG: @{ig_username}). Needs manual check. Client Added: {client_added}, Meal Plan: {meal_plan_uploaded}, Workout Program: {workout_program_built}"
            try:
                add_todo_item(
                    ig_username=ig_username,
                    client_name=client_full_name,
                    task_description=error_notification_message,
                    status="pending"
                )
                logger.info(
                    f"[WIX-BG] Added error dashboard notification for {ig_username}: {error_notification_message}")
            except Exception as todo_error:
                logger.error(
                    f"[WIX-BG] Failed to add error todo item: {todo_error}")

        return onboarding_overall_success

    except Exception as e:
        logger.error(f"[WIX-BG] Error in background processing: {str(e)}")
        logger.error(f"[WIX-BG] Exception details: {traceback.format_exc()}")
        # Add a todo item for unexpected errors
        client_full_name = client_data.get('personal_info', {}).get(
            'full_name', {}).get('value', ig_username)
        unexpected_error_message = f"Unexpected error during onboarding for {client_full_name} (IG: @{ig_username}): {str(e)}. Needs manual check."
        try:
            add_todo_item(
                ig_username=ig_username,
                client_name=client_full_name,
                task_description=unexpected_error_message,
                status="pending"
            )
            logger.info(
                f"[WIX-BG] Added unexpected error notification for {ig_username}")
        except Exception as todo_error:
            logger.error(
                f"[WIX-BG] Failed to add unexpected error todo item: {todo_error}")

        return False


def _convert_wix_data_to_expected_format(wix_client_data: Dict) -> Dict:
    """
    Convert Wix form data structure to the format expected by PostOnboardingHandler._calculate_nutrition
    """
    try:
        # Extract values from Wix structure
        personal_info = wix_client_data.get('personal_info', {})
        physical_info = wix_client_data.get('physical_info', {})
        training_info = wix_client_data.get('training_info', {})
        dietary_info = wix_client_data.get('dietary_info', {})

        # Derive a more meaningful ig_username
        first_name_raw = personal_info.get('firstName', {}).get(
            'value', '').lower().replace(' ', '')
        last_name_raw = personal_info.get('lastName', {}).get(
            'value', '').lower().replace(' ', '')
        email_raw = personal_info.get('email', {}).get('value', '').split(
            '@')[0].lower().replace('.', '').replace('+', '')

        # Prioritize firstName_lastName, then email, then a generic fallback
        if first_name_raw and last_name_raw:
            derived_ig_username = f"{first_name_raw}_{last_name_raw}"
        elif email_raw:
            derived_ig_username = email_raw
        else:
            derived_ig_username = "wix_user_unknown"  # Fallback if no name or email

        # Map activity level from Wix string to integer
        activity_level_str = physical_info.get('activity_level', {}).get(
            'value', 'moderately_active').lower()
        activity_level_map = {
            'sedentary': 1,
            'lightly active': 2,
            'moderately active': 3,
            'very active': 4,
            'extra active': 5
        }
        converted_activity_level = activity_level_map.get(
            activity_level_str, 3)  # Default to 3

        # Convert to expected format for _calculate_nutrition
        converted_data = {
            "personal_info": {
                "email": {"value": personal_info.get('email', {}).get('value', ''), "confidence": 95},
                "full_name": {"value": personal_info.get('full_name', {}).get('value', ''), "confidence": 95},
                "phone": {"value": personal_info.get('phone', {}).get('value', ''), "confidence": 95},
                # Use actual birthday if available
                "birth_date": {"value": personal_info.get('birth_date', {}).get('value', '1990-06-05'), "confidence": 95},
                "gender": {"value": personal_info.get('gender', {}).get('value', 'male'), "confidence": 95}
            },
            "physical_info": {
                "current_weight_kg": {"value": float(physical_info.get('weight', {}).get('value', 70)), "confidence": 95},
                "height_cm": {"value": float(physical_info.get('height', {}).get('value', 170)), "confidence": 95},
                "primary_fitness_goal": {"value": physical_info.get('primary_fitness_goal', {}).get('value', 'muscle_gain'), "confidence": 95},
                "specific_weight_goal_kg": {"value": float(physical_info.get('target_weight', {}).get('value', 75)), "confidence": 90},
                "activity_level": {"value": converted_activity_level, "confidence": 95}
            },
            "dietary_info": {
                "diet_type": {"value": dietary_info.get('diet_type', {}).get('value', 'plant-based'), "confidence": 95},
                "regular_meals": dietary_info.get('regular_meals', {}),
                "meal_notes": {"value": dietary_info.get('meal_notes', {}).get('value', 'prefers plant-based meals'), "confidence": 95},
                "other_dietary_restrictions": {"value": dietary_info.get('dietary_restrictions', {}).get('value', ''), "confidence": 95},
                "disliked_foods": {"value": dietary_info.get('disliked_foods', {}).get('value', ''), "confidence": 95}
            },
            "training_info": {
                "current_routine": {"value": training_info.get('current_routine', {}).get('value', 'none'), "confidence": 95},
                "training_location": {"value": training_info.get('gym_access', {}).get('value', 'full_gym'), "confidence": 95},
                "disliked_exercises": {"value": training_info.get('disliked_exercises', {}).get('value', ''), "confidence": 95},
                "liked_exercises": {"value": training_info.get('liked_exercises', {}).get('value', ''), "confidence": 95},
                "training_days": {"value": training_info.get('training_days', {}).get('value', 'monday-friday'), "confidence": 95}
            },
            "general_info": {
                "location": {"value": personal_info.get('location', {}).get('value', 'Melbourne'), "confidence": 95}
            }
        }

        # Override ig_username with the derived one
        converted_data['personal_info']['ig_username'] = {
            'value': derived_ig_username, 'confidence': 100}

        logger.info(
            f"[WIX-CONVERSION] Successfully converted data structure for IG: {derived_ig_username}")
        return converted_data

    except Exception as e:
        logger.error(f"[WIX-CONVERSION] Error converting data: {str(e)}")
        return None


if __name__ == "__main__":
    logger.info("\n=== STARTING WEBHOOK SERVER (webhook0605.py) ===")
    uvicorn.run("webhook0605:app",  # Changed to use webhook0605
                host="0.0.0.0",
                port=8000,
                reload=True,
                reload_dirs=["c:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot"],
                timeout_keep_alive=300,
                timeout_graceful_shutdown=300,
                limit_concurrency=100,
                backlog=2048
                )

# ---------------------------------------------------------------------------
# Challenge offer gating helper functions
# ---------------------------------------------------------------------------


def _user_has_agreed_to_challenge(conv_history: list[dict]) -> bool:
    """Return True if user gave an affirmative answer after Shannon's soft intro."""
    intro_idx = -1
    for idx, entry in enumerate(conv_history):
        if entry.get('type') == 'ai':
            txt = entry.get('text', '').lower()
            if any(p in txt for p in [
                'would you be interested',
                'interested in hearing',
                'keen to hear',
                'keen to find out',
                    'would you be keen']):
                intro_idx = idx
    if intro_idx == -1:
        return False
    affirm_words = ['yes', 'yeah', 'yep', 'sure', 'keen', 'interested',
                    'sounds good', 'sounds great', 'ok', 'okay', 'absolutely']
    for entry in conv_history[intro_idx + 1:]:
        if entry.get('type') == 'user':
            txt = entry.get('text', '').lower()
            if any(w in txt for w in affirm_words):
                return True
            if any(w in txt for w in ['no', 'not', 'later', 'maybe']):
                return False
    return False


def enforce_challenge_offer_rules(ai_response: str, conv_history: list[dict]) -> str:
    """Ensure challenge link only sent after affirmative user response; otherwise replace with soft intro."""
    if 'cocospersonaltraining.com' in ai_response.lower():
        if not _user_has_agreed_to_challenge(conv_history):
            # Remove any URLs
            cleaned = _re_chal.sub(r'https?://\S+', '', ai_response).strip()
            soft_intro = "Hey I'm actually about to run a Vegan Fitness Challenge, it's totally free and a bunch of fun, would you be interested in hearing more?"
            if 'would you be interested' in cleaned.lower():
                return cleaned
            return soft_intro
    return ai_response

# ---------------------------------------------------------------------------
# Duplicate-question guard helpers
# ---------------------------------------------------------------------------


def _get_recent_ai_questions(conv_history: list[dict], limit: int = 5) -> list[str]:
    """Return last N Shannon questions (lower-cased, stripped of punctuation)."""
    qs: list[str] = []
    for entry in reversed(conv_history):
        if entry.get('type') == 'ai':
            txt = entry.get('text', '')
            if '?' in txt:
                # take question portion(s)
                for part in txt.split('?'):
                    part = part.strip()
                    if part:
                        qs.append(part.lower())
                if len(qs) >= limit:
                    break
    return qs[:limit]


async def _dedup_and_rewrite_if_needed(new_resp: str, conv_history: list[dict]) -> str:
    """Drop repeated questions; if any removed, ask Gemini to add a fresh one."""
    recent_qs = _get_recent_ai_questions(conv_history)

    # Split into sentence segments preserving punctuation
    segments: list[str] = []
    buff = ''
    for ch in new_resp:
        buff += ch
        if ch in '.!?':
            segments.append(buff)
            buff = ''
    if buff:
        segments.append(buff)

    cleaned_segments: list[str] = []
    duplicate_found = False
    for seg in segments:
        core = seg.strip().rstrip('?').strip().lower()
        if seg.strip().endswith('?') and core in recent_qs:
            duplicate_found = True
            continue  # skip dup question
        cleaned_segments.append(seg)

    cleaned_text = ' '.join(s.strip() for s in cleaned_segments).strip()
    if not duplicate_found:
        return new_resp  # nothing to change

    # We removed a question; ask Gemini to craft a fresh one
    recent_qs_str = '; '.join(recent_qs)
    rewrite_prompt = (
        "You are Shannon speaking casually (max 15 words). "
        "Rewrite the following line so it ends with ONE new open-ended question "
        "that is different from these recent questions: "
        f"{recent_qs_str}.\n\n"
        f"Line to rewrite: \"{cleaned_text}\""
    )

    try:
        alt = await call_gemini_with_retry(GEMINI_MODEL_FLASH, rewrite_prompt)
        if alt and isinstance(alt, str):
            return alt.strip()
    except Exception as e:
        logger.error(f"rewrite duplicate question error: {e}")

    # Fallback: return cleaned_text without duplicate question
    return cleaned_text or new_resp

app.include_router(trainerize_router)


async def handle_ad_response(ig_username: str, message_text: str, subscriber_id: str, first_name: str, last_name: str, user_message_timestamp_iso: str) -> bool:
    try:
        # Get user data including ad states
        _, metrics, _ = get_user_data(ig_username, subscriber_id)
        is_in_ad_flow = metrics.get('is_in_ad_flow', False)
        current_state = metrics.get('ad_script_state', 'step1')
        scenario = metrics.get('ad_scenario', 1)  # Default to 1

        logger.info(
            f"[handle_ad_response] Current state for {ig_username}: is_in_ad_flow={is_in_ad_flow}, ad_script_state={current_state}, scenario={scenario}")

        if not is_in_ad_flow:
            logger.info(
                f"[handle_ad_response] User {ig_username} is not in ad flow (is_in_ad_flow={is_in_ad_flow}), returning False")
            return False

        # Build prompt params
        bio_context = metrics.get('client_analysis', {}).get('profile_bio', '')
        weekly_workout_summary = json.dumps(metrics.get('workout_program', {}))
        meal_plan_summary = json.dumps(metrics.get('meal_plan', {}))
        current_stage = f"Ad Response {current_state}"
        trial_status = "Ad Lead"
        current_time = get_melbourne_time_str()
        full_conversation = format_conversation_history(metrics.get(
            'conversation_history', [])) + f"\nUser: {message_text}"

        # Determine challenge type from scenario
        challenge_types = {1: 'vegan', 2: 'vegetarian', 3: 'plant_based'}
        challenge_type = challenge_types.get(scenario, 'plant_based')

        # Use PAID Plant-Based Challenge prompt for plant_based_challenge leads
        if metrics.get('lead_source') == 'plant_based_challenge':
            prompt = prompts.PAID_VEGAN_CHALLENGE_PROMPT_TEMPLATE.format(
                current_melbourne_time_str=current_time,
                ig_username=ig_username,
                script_state=current_state,
                # Will be updated based on ManyChat button selection
                initial_trigger='direct_comment',
                bio=bio_context,
                full_conversation=full_conversation
            )
        else:
            # Fallback to existing FB ad prompt for facebook_ad leads
            prompt = prompts.COMBINED_AD_RESPONSE_PROMPT_TEMPLATE.format(
                current_melbourne_time_str=current_time,
                ig_username=ig_username,
                script_state=current_state,
                ad_scenario=scenario,
                bio=bio_context,
                full_conversation=full_conversation
            )

        response = await get_ai_response(prompt)
        if not response:
            logger.error(f"Failed to get ad response for {ig_username}")
            return False

        # Check for email collection in Plant-Based Challenge responses
        if metrics.get('lead_source') == 'plant_based_challenge':
            await detect_and_store_challenge_email(ig_username, message_text, subscriber_id, scenario)

        # Check auto mode status to determine how to handle the response (explicit Vegan Ad toggle only)
        should_auto_process = False
        try:
            # Import the vegan ad auto mode checker
            import sys
            import os
            app_dashboard_modules_path = os.path.join(
                os.path.dirname(__file__), 'app', 'dashboard_modules')
            if app_dashboard_modules_path not in sys.path:
                sys.path.insert(0, app_dashboard_modules_path)

            from auto_mode_state import is_vegan_ad_auto_mode_active

            vegan_ad_auto_active = is_vegan_ad_auto_mode_active()

            if vegan_ad_auto_active:
                logger.info(
                    f"🌱 VEGAN AD AUTO MODE ACTIVE - Auto-processing ad response for {ig_username}")
                should_auto_process = True
            else:
                logger.info(
                    f"Vegan Ad auto mode OFF - {ig_username} ad response requires manual review")
                should_auto_process = False

        except ImportError:
            logger.warning(
                "Could not import auto_mode_state, assuming Vegan Ad Auto Mode is OFF for ad response.")
            should_auto_process = False

        # Add to review queue with appropriate status
        review_status = 'auto_scheduled' if should_auto_process else 'pending_review'
        review_id = add_response_to_review_queue(
            user_ig_username=ig_username,
            user_subscriber_id=subscriber_id,
            incoming_message_text=message_text,
            incoming_message_timestamp=user_message_timestamp_iso,
            generated_prompt_text=prompt,
            proposed_response_text=response,
            prompt_type="facebook_ad_response",
            status=review_status
        )

        # If auto mode is active, schedule the response
        if should_auto_process and review_id:
            try:
                # Ensure the scheduled responses table exists
                conn = db_utils.get_db_connection()
                create_scheduled_responses_table_if_not_exists(conn)
                conn.close()

                # Schedule the response with timing delay
                from app.dashboard_modules.response_review import schedule_auto_response
                success_schedule, schedule_message, delay_minutes = schedule_auto_response(
                    # Create a mock review_item for the function
                    {
                        'review_id': review_id,
                        'user_ig_username': ig_username,
                        'user_subscriber_id': subscriber_id,
                        'incoming_message_text': message_text,
                        'incoming_message_timestamp': user_message_timestamp_iso,
                        'proposed_response': response,
                        'status': 'auto_scheduled'
                    },
                    response,
                    user_notes="[AUTO MODE - AD RESPONSE]",
                    manual_context=""
                )

                if success_schedule:
                    logger.info(
                        f"✅ AUTO-SCHEDULED: {ig_username} - Ad response queued for {delay_minutes} minutes")
                else:
                    logger.error(
                        f"❌ Auto-schedule FAILED for ad response {ig_username}: {schedule_message}")
            except Exception as e_auto:
                logger.error(
                    f"❌ Failed to auto-schedule ad response for {ig_username}: {e_auto}", exc_info=True)

        if review_id:
            logger.info(
                f"Successfully added ad response for {ig_username} to review queue (Review ID: {review_id})")

            # Update analytics with the generated response
            update_analytics_data(
                ig_username, message_text, response, subscriber_id, first_name, last_name
            )

            # Advance state
            next_state = 'completed' if current_state == 'step3' else f"step{int(current_state[-1]) + 1}"
            logger.info(
                f"[handle_ad_response] Advancing {ig_username} from {current_state} to {next_state}")

            update_analytics_data(
                ig_username, "", "", subscriber_id, first_name, last_name,
                ad_script_state=next_state
            )
            if next_state == 'completed':
                logger.info(
                    f"[handle_ad_response] Ad flow completed for {ig_username}, setting is_in_ad_flow=False")
                update_analytics_data(
                    ig_username, "", "", subscriber_id, first_name, last_name,
                    is_in_ad_flow=False
                )
                # ONLY FOR PAID CHALLENGE: If lead source is plant_based_challenge and flow is completed,
                # it means they confirmed booking a call. Add them to paid_challenge_bookings.
                if metrics.get('lead_source') == 'plant_based_challenge':
                    try:
                        from app.dashboard_modules.dashboard_sqlite_utils import add_paid_challenge_booking
                        add_paid_challenge_booking(ig_username)
                        logger.info(
                            f"✅ Recorded paid challenge booking confirmation for {ig_username}")
                    except Exception as e_booking:
                        logger.error(
                            f"❌ Failed to record paid challenge booking for {ig_username}: {e_booking}", exc_info=True)
            else:
                logger.info(
                    f"[handle_ad_response] Ad flow continues for {ig_username}, keeping is_in_ad_flow=True")

            return True
        else:
            logger.error(
                f"Failed to add ad response for {ig_username} to review queue")
            return False

    except Exception as e:
        logger.error(f"Error in handle_ad_response: {e}", exc_info=True)
        return False


async def handle_ad_response_with_params(ig_username: str, message_text: str, subscriber_id: str, first_name: str, last_name: str, user_message_timestamp_iso: str, force_ad_flow: bool = False, force_lead_source: str = None, force_scenario: int = None, force_script_state: str = None) -> bool:
    """
    Enhanced version of handle_ad_response that accepts forced parameters to bypass database lookups.
    Used when we know the user should be in ad flow but database might not be updated yet.
    """
    try:
        # Get user data including ad states, but override with forced params if provided
        _, metrics, _ = get_user_data(ig_username, subscriber_id)

        # Use forced parameters if provided, otherwise fall back to database values
        is_in_ad_flow = force_ad_flow if force_ad_flow is not None else metrics.get(
            'is_in_ad_flow', False)
        current_state = force_script_state if force_script_state else metrics.get(
            'ad_script_state', 'step1')
        scenario = force_scenario if force_scenario else metrics.get(
            'ad_scenario', 1)
        lead_source = force_lead_source if force_lead_source else metrics.get(
            'lead_source', 'general')

        logger.info(
            f"[handle_ad_response_with_params] Using parameters for {ig_username}: is_in_ad_flow={is_in_ad_flow}, ad_script_state={current_state}, scenario={scenario}, lead_source={lead_source} (forced: {force_ad_flow})")

        if not is_in_ad_flow:
            logger.info(
                f"[handle_ad_response_with_params] User {ig_username} is not in ad flow (is_in_ad_flow={is_in_ad_flow}), returning False")
            return False

        # Build prompt params
        bio_context = metrics.get('client_analysis', {}).get('profile_bio', '')
        weekly_workout_summary = json.dumps(metrics.get('workout_program', {}))
        meal_plan_summary = json.dumps(metrics.get('meal_plan', {}))
        current_stage = f"Ad Response {current_state}"
        trial_status = "Ad Lead"
        current_time = get_melbourne_time_str()
        full_conversation = format_conversation_history(metrics.get(
            'conversation_history', [])) + f"\nUser: {message_text}"

        # Determine challenge type from scenario
        challenge_types = {1: 'vegan', 2: 'vegetarian', 3: 'plant_based'}
        challenge_type = challenge_types.get(scenario, 'plant_based')

        # Use Plant-Based Challenge prompt for plant_based_challenge leads
        if lead_source == 'paid_plant_based_challenge':
            prompt = prompts.PAID_VEGAN_CHALLENGE_PROMPT_TEMPLATE.format(
                current_melbourne_time_str=current_time,
                ig_username=ig_username,
                script_state=current_state,
                initial_trigger='direct_comment',  # Corrected parameter
                bio=bio_context,
                full_conversation=full_conversation
            )
            logger.info(
                f"[handle_ad_response_with_params] Using PAID_VEGAN_CHALLENGE_PROMPT_TEMPLATE for {ig_username}")
        else:
            # Fallback to existing FB ad prompt for facebook_ad leads
            prompt = prompts.COMBINED_AD_RESPONSE_PROMPT_TEMPLATE.format(
                current_melbourne_time_str=current_time,
                ig_username=ig_username,
                ad_script_state=current_state,
                ad_scenario=scenario,
                bio=bio_context,
                full_conversation=full_conversation
            )
            logger.info(
                f"[handle_ad_response_with_params] Using COMBINED_AD_RESPONSE_PROMPT_TEMPLATE for {ig_username}")

        response = await get_ai_response(prompt)
        if not response:
            logger.error(f"Failed to get ad response for {ig_username}")
            return False

        # Check for email collection in Plant-Based Challenge responses
        if lead_source == 'plant_based_challenge':
            await detect_and_store_challenge_email(ig_username, message_text, subscriber_id, scenario)

        # Check for booking confirmation in PAID Plant-Based Challenge responses
        if lead_source == 'paid_plant_based_challenge' and metrics.get('paid_challenge_booking_status') != 'booked':
            await detect_and_confirm_paid_booking(ig_username, message_text, subscriber_id)

        # Check auto mode status to determine how to handle the response (plant-based challenge path)
        should_auto_process = False
        try:
            # Import the auto mode checkers
            import sys
            import os
            app_dashboard_modules_path = os.path.join(
                os.path.dirname(__file__), 'app', 'dashboard_modules')
            if app_dashboard_modules_path not in sys.path:
                sys.path.insert(0, app_dashboard_modules_path)

            from auto_mode_state import is_vegan_ad_auto_mode_active

            if is_vegan_ad_auto_mode_active():
                logger.info(
                    f"🌱 VEGAN AD AUTO MODE ACTIVE - Auto-processing plant-based challenge response for {ig_username}")
                should_auto_process = True
            else:
                logger.info(
                    f"No auto mode active - {ig_username} plant-based challenge response requires manual review")
                should_auto_process = False

        except ImportError:
            logger.warning(
                "Could not import auto_mode_state, assuming Auto Mode is OFF for plant-based challenge response.")
            should_auto_process = False

        # If auto mode is active, schedule the response
        if should_auto_process and review_id:
            try:
                # Ensure the scheduled responses table exists
                import app.dashboard_modules.dashboard_sqlite_utils as db_utils
                from app.dashboard_modules.dashboard_sqlite_utils import create_scheduled_responses_table_if_not_exists
                conn = db_utils.get_db_connection()
                create_scheduled_responses_table_if_not_exists(conn)
                conn.close()

                # Schedule the response with timing delay
                from app.dashboard_modules.response_review import schedule_auto_response
                success_schedule, schedule_message, delay_minutes = schedule_auto_response(
                    # Create a mock review_item for the function
                    {
                        'review_id': review_id,
                        'user_ig_username': ig_username,
                        'user_subscriber_id': subscriber_id,
                        'incoming_message_text': message_text,
                        'incoming_message_timestamp': user_message_timestamp_iso,
                        'proposed_response': response,
                        'status': 'auto_scheduled'
                    },
                    response,
                    user_notes="[AUTO MODE - PLANT-BASED CHALLENGE RESPONSE]",
                    manual_context=""
                )

                if success_schedule:
                    logger.info(
                        f"✅ AUTO-SCHEDULED: {ig_username} - Plant-based challenge response queued for {delay_minutes} minutes")
                else:
                    logger.error(
                        f"❌ Auto-schedule FAILED for plant-based challenge response {ig_username}: {schedule_message}")
            except Exception as e_auto:
                logger.error(
                    f"❌ Failed to auto-schedule plant-based challenge response for {ig_username}: {e_auto}", exc_info=True)

        # Add to review queue with appropriate status
        review_status = 'auto_scheduled' if should_auto_process else 'pending_review'
        review_id = add_response_to_review_queue(
            user_ig_username=ig_username,
            user_subscriber_id=subscriber_id,
            incoming_message_text=message_text,
            incoming_message_timestamp=user_message_timestamp_iso,
            generated_prompt_text=prompt,
            proposed_response_text=response,
            prompt_type="plant_based_challenge" if lead_source == 'plant_based_challenge' else "facebook_ad",
            status=review_status
        )

        if review_id:
            logger.info(
                f"Successfully added ad response for {ig_username} to review queue (Review ID: {review_id})")

            # Update analytics with the generated response
            update_analytics_data(
                ig_username, message_text, response, subscriber_id, first_name, last_name
            )

            # Advance state
            next_state = 'completed' if current_state == 'step3' else f"step{int(current_state[-1]) + 1}"
            logger.info(
                f"[handle_ad_response_with_params] Advancing {ig_username} from {current_state} to {next_state}")

            update_analytics_data(
                ig_username, "", "", subscriber_id, first_name, last_name,
                ad_script_state=next_state
            )
            if next_state == 'completed':
                logger.info(
                    f"[handle_ad_response_with_params] Ad flow completed for {ig_username}, setting is_in_ad_flow=False")
                update_analytics_data(
                    ig_username, "", "", subscriber_id, first_name, last_name,
                    is_in_ad_flow=False
                )

            return True
        else:
            logger.error(
                f"Failed to add ad response for {ig_username} to review queue")
            return False

    except Exception as e:
        logger.error(
            f"Error in handle_ad_response_with_params: {e}", exc_info=True)
        return False


async def detect_and_store_challenge_email(ig_username: str, message_text: str, subscriber_id: str, current_scenario: int):
    """Detect email in Plant-Based Challenge conversation and store challenge data"""
    import re
    from app.dashboard_modules.notifications import add_email_collected_notification

    # Email pattern detection
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, message_text)

    if emails:
        email = emails[0]  # Take the first email found

        # Determine challenge type from scenario
        challenge_types = {1: 'vegan', 2: 'vegetarian', 3: 'plant_based'}
        challenge_type = challenge_types.get(current_scenario, 'plant_based')

        try:
            import sqlite3
            from datetime import datetime

            conn = sqlite3.connect("app/analytics_data_good.sqlite")
            cursor = conn.cursor()

            # Update user with challenge email and data
            cursor.execute("""
                UPDATE users 
                SET challenge_email = ?, 
                    challenge_type = ?, 
                    challenge_signup_date = ?,
                    ad_script_state = 'step5'
                WHERE ig_username = ?
            """, (email, challenge_type, datetime.now().isoformat(), ig_username))

            conn.commit()
            conn.close()

            # Trigger blue email notification
            add_email_collected_notification(ig_username, email)

            logger.info(
                f"🌱 Challenge email collected for {ig_username}: {email} (Type: {challenge_type})")
            return True

        except Exception as e:
            logger.error(
                f"Error storing challenge email for {ig_username}: {e}")
            return False

        return False


async def detect_and_confirm_paid_booking(ig_username: str, message_text: str, subscriber_id: str):
    """
    Detects if a user's message confirms they have booked a Calendly call
    and updates their status in the database.
    """
    confirmation_prompt = f"""
    Analyze the user's message. Does it confirm they have booked a call, appointment, or session?
    Look for phrases like "booked", "done", "all set", "scheduled it", "just booked".

    User message: "{message_text}"

    If it is a confirmation, respond with "YES". Otherwise, respond with "NO".
    """
    try:
        confirmation = await call_gemini_with_retry(
            model_name="gemini-2.0-flash-thinking-exp-01-21",
            prompt=confirmation_prompt
        )

        if "YES" in confirmation.upper():
            from app.dashboard_modules.dashboard_sqlite_utils import add_paid_challenge_booking
            from app.dashboard_modules.notifications import add_notification

            add_paid_challenge_booking(ig_username)
            add_notification(
                title="✅ Insight Call Booked!",
                message=f"@{ig_username} has booked their paid challenge insight call.",
                notification_type="success",
                username=ig_username
            )
            logger.info(
                f"✅ Confirmed and recorded paid challenge booking for {ig_username}")
            return True

    except Exception as e:
        logger.error(
            f"Error detecting paid booking confirmation for {ig_username}: {e}", exc_info=True)

        return False
