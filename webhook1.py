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
                            "Can you tell me more about your Vegetarian Weight Loss Challenge"
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
