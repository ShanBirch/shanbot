import sys
import os
import asyncio
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from typing import Dict, Any, List, Optional, Tuple, Union
import json
import requests
import logging
import hashlib
import hmac
import os
import uvicorn
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from fastapi import FastAPI, Request, HTTPException, Header, Depends
import google.generativeai as genai  # Added Gemini import
# Add Google Sheets imports
import google.oauth2.service_account
import googleapiclient.discovery
import re
from datetime import datetime, timezone
import pytz  # Make sure pytz is imported
from app import prompts  # Import prompts from the app package
import time
from fastapi.middleware.cors import CORSMiddleware  # Add this import
import asyncio  # Added to allow async delays between messages
from collections import defaultdict
import dateutil.parser as parser
import httpx
from pb import TrainerizeAutomation
from pydantic import BaseModel, Field
from google.cloud import speech_v1
import io
import tempfile
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
# Added import for technique analysis
from techniqueanalysis import get_video_analysis
# Added import for calorie analysis
from calorietracker import get_calorie_analysis
import glob  # Added for finding check-in files
import re  # Added for date parsing in find_latest_checkin_file
from pathlib import Path  # Added for robust path handling
# Import handlers from webhook_handlers.py
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
    send_manychat_message
)
# Add import at the top
from calorie_manager_calorietracker import CalorieTracker_CalorieTracker
from post_onboarding_handler import PostOnboardingHandler

# Set up logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("manychat_webhook")
logger.info("Logging configured.")  # Confirm logging setup
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


async def detect_and_handle_action(ig_username: str, message_text: str, data: Dict = None) -> bool:
    """Uses Gemini to detect user intent and handles multiple actions like Trainerize edits or food analysis within one message."""
    logger.info(
        f"[detect_and_handle_action] Analyzing message from {ig_username} for multiple actions: {message_text[:100]}"
    )

    if not data:
        logger.error("No data dictionary provided to detect_and_handle_action")
        return False

    # --- ONBOARDING CHECK --- START ---
    logger.info(
        f"[detect_and_handle_action] Starting onboarding check for {ig_username}")

    try:
        # Get user data to check onboarding status
        user_data_tuple = get_user_data(ig_username)
        if user_data_tuple:
            _, metrics_dict, _, _, _, _, _, _, _, _ = user_data_tuple

            logger.info(
                f"[detect_and_handle_action] Retrieved metrics for onboarding check: {json.dumps(metrics_dict.get('calorie_tracking', {}), indent=2)}")

            # Check if user is in onboarding
            if isinstance(metrics_dict, dict) and isinstance(metrics_dict.get('calorie_tracking'), dict):
                is_onboarding = metrics_dict['calorie_tracking'].get(
                    'is_onboarding', False)
                logger.info(
                    f"[detect_and_handle_action] Onboarding status for {ig_username}: {is_onboarding}")

                if is_onboarding:
                    logger.info(
                        f"[detect_and_handle_action] User {ig_username} is in onboarding flow")
                    return True  # Let the main flow handle onboarding messages
            else:
                logger.info(
                    f"[detect_and_handle_action] No calorie_tracking data found for {ig_username}")
    except Exception as e:
        logger.error(
            f"[detect_and_handle_action] Error during onboarding check: {str(e)}")

    logger.info(
        f"[detect_and_handle_action] Completed onboarding check for {ig_username}")
    # --- ONBOARDING CHECK --- END ---

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
Tracking Keywords: track calories, track macros, monitor food, log meals, calorie tracking, track my cals

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
            subscriber_id = data.get('id')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')

            # Check message type and content
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
                            "CONVERSATION": message_text
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
                    "CONVERSATION": message_text
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

                return True

            # Handle Form Check Request (only if not a workout request)
            elif is_form_check_req and confidence > 70 and has_video and not is_workout_message:
                logger.info(
                    f"Form check request detected for {ig_username} with confidence {confidence}.")
                form_check_pending[ig_username] = True
                response = random.choice(FORM_CHECK_REQUEST_RESPONSES)
                logger.info(
                    f"Using dynamic response for form check request: '{response}'")
                field_updates = {
                    "o1 Response": response,
                    "CONVERSATION": message_text
                }
                update_success = update_manychat_fields(
                    subscriber_id, field_updates)
                if not update_success:
                    logger.error(
                        f"Failed to update ManyChat fields for form check request {ig_username}")

                ai_response_for_analytics = "AI responded asking user to send video for form check."
                update_analytics_data(
                    ig_username,
                    message_text,
                    ai_response_for_analytics,
                    subscriber_id,
                    first_name,
                    last_name
                )
                logger.info(
                    f"Updated analytics data for {ig_username} after form check request.")
                return True

            # Handle Calorie Tracking Request
            elif is_calorie_tracking_req and confidence > 70:
                logger.info(
                    f"Calorie tracking request detected for {ig_username}")
                food_analysis_pending[ig_username] = True
                logger.info(
                    f"Set food_analysis_pending state for {ig_username}")
                response = "Sure, I can help track your calories! Send me a photo of your food along with a quick description of what's in it, and I'll analyze the calories and macros for you."
                field_updates = {
                    "o1 Response": response,
                    "CONVERSATION": message_text
                }
                update_success = update_manychat_fields(
                    subscriber_id, field_updates)
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

            # Handle Food Analysis Request
            elif is_food_analysis_req and confidence > 70:
                logger.info(
                    f"Food analysis request detected for {ig_username} with confidence {confidence}.")
                client_name_for_todo = data.get(
                    'name') or f"{first_name} {last_name}".strip() or ig_username

                if has_image_url:
                    url_pattern = r"(https?://lookaside\.fbsbx\.com/ig_messaging_cdn/\?asset_id=[\w-]+&signature=[\w\-_.~]+)"
                    match = re.search(url_pattern, message_text)
                    if match:
                        image_url = match.group(1)
                        logger.info(
                            f"Found image URL for food analysis: {image_url[:100]}...")
                        user_desc_text = message_text.replace(
                            image_url, "").strip()
                        analysis_result = get_calorie_analysis(
                            image_url,
                            GEMINI_API_KEY,
                            GEMINI_MODEL_PRO,
                            GEMINI_MODEL_FLASH,
                            GEMINI_MODEL_FLASH_STANDARD,
                            user_description=user_desc_text
                        )

                        if not analysis_result:
                            analysis_result = "Sorry mate, had a bit of trouble analysing that pic. Can you try sending it again?"
                            logger.error(
                                f"Food analysis failed for {ig_username} (URL: {image_url[:50]}...)")
                            add_todo_item(
                                ig_username,
                                client_name_for_todo,
                                f"Failed calorie analysis for image: {image_url[:50]}..."
                            )
                        else:
                            add_todo_item(
                                ig_username,
                                client_name_for_todo,
                                f"Successfully provided calorie analysis for image: {image_url[:50]}...",
                                status="completed"
                            )

                        field_updates = {
                            "o1 Response": analysis_result,
                            "CONVERSATION": f"(User sent image for calorie check: {image_url[:50]}...)"
                        }
                        ai_response_for_analytics = f"AI provided food analysis. Analysis message: {analysis_result[:100]}"
                        user_message_for_analytics = f"(Sent food image: {image_url[:50]}...)"
                    else:
                        logger.error(
                            f"Intent analysis indicated image URL present for {ig_username}, but regex failed to find it in: '{message_text}'")
                        response_text = "Hmm, thought I saw a picture link but couldn't grab it. Can you try sending the food pic again?"
                        field_updates = {
                            "o1 Response": response_text,
                            "CONVERSATION": message_text
                        }
                        ai_response_for_analytics = "AI failed to extract detected image URL."
                        user_message_for_analytics = message_text
                else:
                    logger.info(
                        f"Food analysis request for {ig_username} detected without image URL. Asking user to send photo.")
                    response_text = "Yep send the photo through, and a brief description of the ingredients used will help as well"
                    food_analysis_pending[ig_username] = True
                    logger.info(
                        f"Set food_analysis_pending state for {ig_username}")
                    field_updates = {
                        "o1 Response": response_text,
                        "CONVERSATION": message_text
                    }
                    ai_response_for_analytics = "AI asked user to send food photo and ingredients."
                    user_message_for_analytics = message_text

                update_success = update_manychat_fields(
                    subscriber_id, field_updates)
                if not update_success:
                    logger.error(
                        f"Failed to update ManyChat fields for food analysis flow for {ig_username}")

                update_analytics_data(
                    ig_username,
                    user_message_for_analytics,
                    ai_response_for_analytics,
                    subscriber_id,
                    first_name,
                    last_name
                )
                logger.info(
                    f"Updated analytics for {ig_username} during food analysis flow.")
                return True

            else:
                logger.info(
                    "Message not identified as a confident action request.")
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

        # Get user data for prompt context (using the already looked-up username if available)
        prev_conv, bio, conversation_topics, interests = "", "N/A", [], "N/A"  # Defaults
        if ig_usernames.get(sender_id):
            try:
                # Re-use get_user_data which handles file reading and parsing
                prev_conv, bio, conversation_topics, interests = get_user_data(
                    ig_usernames.get(sender_id))
                logger.info(
                    f"Retrieved context for {ig_usernames.get(sender_id)} for prompt generation.")
            except Exception as gud_e:
                logger.error(
                    f"Error retrieving context via get_user_data for {ig_usernames.get(sender_id)}: {gud_e}")
        else:
            logger.warning(
                f"Cannot retrieve context for prompt generation, username unknown for {sender_id}.")

        # Build AI prompt
        topics_str = "\\n- " + \
            "\\n- ".join(conversation_topics) if conversation_topics else "N/A"
        current_time = get_melbourne_time_str()
        combined_history_for_prompt = (prev_conv + "\\n") if prev_conv else ""
        # Add the latest message(s)
        combined_history_for_prompt += f"Lead: {full_message}"

        prompt = prompts.GENERAL_CHAT_PROMPT_TEMPLATE.format(
            current_melbourne_time_str=current_time,
            bio=bio if bio else "N/A",
            topics_str=topics_str,
            interests=interests if interests else "N/A",
            full_conversation=combined_history_for_prompt
        )
        logger.info(
            f"Generated prompt for {sender_id} (length: {len(prompt)})")

        # Call Gemini
        response_text = call_gemini_with_retry(
            # Provide a fallback
            GEMINI_MODEL_PRO, prompt) or "Sorry, I couldn't generate a response right now."
        logger.info(
            f"Generated Gemini response for {sender_id}: '{response_text[:100]}...'")

        # Update analytics_data.json (using the already looked-up username)
        if ig_usernames.get(sender_id):
            try:
                update_analytics_data(ig_usernames.get(
                    sender_id), full_message, response_text, ig_usernames.get(sender_id), "Shannon", "Birch")
                logger.info(
                    f"Updated analytics data for {ig_usernames.get(sender_id)}")
            except Exception as e:
                logger.error(
                    f"Error updating analytics for {ig_usernames.get(sender_id)} ({sender_id}): {e}")
        else:
            logger.warning(
                f"No IG username for {sender_id}, skipping analytics update.")

        # Split and send messages
        response_messages = split_response_into_messages(response_text)
        logger.info(
            f"Split response into {len(response_messages)} message chunks for {sender_id}")
        messages_sent_successfully = 0
        for idx, msg in enumerate(response_messages, 1):
            logger.info(
                f"Sending message {idx}/{len(response_messages)} to {sender_id}: '{msg[:50]}...'")
            # --- MODIFIED: Track success of send_instagram_reply --- START ---
            send_success = await send_instagram_reply(sender_id, msg)
            if send_success:
                messages_sent_successfully += 1
                logger.info(
                    f"Sent message {idx}/{len(response_messages)} to {sender_id}")
                # Dynamic delay based on message length
                await asyncio.sleep(max(len(msg)/10, 2))
            else:
                logger.error(
                    f"Failed to send message {idx}/{len(response_messages)} to {sender_id}. Stopping send sequence.")
                break  # Stop trying to send further chunks if one fails
            # --- MODIFIED: Track success of send_instagram_reply --- END ---

        # --- ADDED: Update last_bot_reply_timestamp --- START ---
        if messages_sent_successfully > 0:
            # Only update if at least one message chunk was sent
            current_time_float = time.time()
            last_bot_reply_timestamps[sender_id] = current_time_float
            logger.info(
                f"Updated last_bot_reply_timestamp for {sender_id} to {current_time_float}")
        else:
            logger.warning(
                f"No messages were sent successfully to {sender_id}, not updating last_bot_reply_timestamp.")
        # --- ADDED: Update last_bot_reply_timestamp --- END ---

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


@app.post("/trainerize/build-program")
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
BUFFER_WINDOW = 15  # seconds to wait for grouping messages

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
        combined_text = ""
        for msg in user_buffer:
            msg_text = msg.get('payload', {}).get('last_input_text', '')
            if msg_text:
                if combined_text:
                    combined_text += "\n"
                combined_text += msg_text

        if not combined_text:
            logger.error(f"No message content found for {ig_username}")
            return None

        logger.info(
            f"Successfully processed buffer for {ig_username}: {combined_text}")
        return combined_text, payload

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
        current_stage, metrics_dict, conversation_topics, trial_status, _, last_bot_response, interests_json, is_in_checkin_flow, full_name, checkin_type = get_user_data(
            ig_username)

        combined_message = " ".join([msg["text"] for msg in messages])
        logger.info(f"Combined message: {combined_message}")

        # Clear buffer after reading
        message_buffer[ig_username] = []

        # Process media URLs in the combined message
        processed_message = process_conversation_for_media(combined_message)
        logger.info(
            f"Processed message (after media handling): {processed_message}")

        # Build chat prompt using build_member_chat_prompt with all required parameters
        chat_prompt = build_member_chat_prompt(
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
            last_name=messages[0].get("last_name", "")
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
async def process_manychat_webhook(request: Request):
    try:
        # Parse the request body
        data = await request.json()
        logger.info("\n=== WEBHOOK RECEIVED ===")
        logger.info(f"Received webhook request body: {json.dumps(data)}")

        # Extract Instagram username and subscriber ID
        ig_username = data.get('ig_username', '')
        subscriber_id = data.get('id', '')

        if not ig_username:
            logger.error("No Instagram username found in payload")
            return {"status": "error", "message": "No Instagram username found"}

        # Get user data and check onboarding status
        logger.info(f"\n=== CHECKING USER STATUS FOR {ig_username} ===")
        current_stage, metrics_dict, _, _, _, _, _, is_in_checkin_flow, _, _ = get_user_data(
            ig_username)

        # Check onboarding status first
        is_onboarding = False
        if metrics_dict and isinstance(metrics_dict.get('calorie_tracking'), dict):
            is_onboarding = metrics_dict['calorie_tracking'].get(
                'is_onboarding', False)
            logger.info(f"\n=== ONBOARDING STATUS CHECK IN WEBHOOK ===")
            logger.info(f"Found onboarding status = {is_onboarding}")
            if is_onboarding:
                logger.info(
                    "User is in onboarding flow - will use ONBOARDING_PROMPT_TEMPLATE")
            logger.info(f"=== END ONBOARDING STATUS CHECK IN WEBHOOK ===\n")
        else:
            logger.info("No onboarding status found in metrics")

        # Get the last message from the user
        message_text = data.get('last_input_text', '')
        if not message_text:
            logger.error("No message text found in payload")
            return {"status": "error", "message": "No message text found"}

        logger.info(f"User message: {message_text}")

        # Add message to buffer with onboarding status
        if ig_username not in message_buffer:
            message_buffer[ig_username] = []

        message_buffer[ig_username].append({
            "text": message_text,
            "subscriber_id": subscriber_id,
            "first_name": data.get('first_name', ''),
            "last_name": data.get('last_name', ''),
            "is_onboarding": is_onboarding  # Add onboarding status to message data
        })

        # Create task for delayed processing
        asyncio.create_task(delayed_message_processing(ig_username))

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


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
    elif time_diff_seconds <= 18000:  # 2-5 hours
        return "response time is 2-5 hours"
    else:  # Above 5 Hours
        return "response time is Above 5 Hours"


if __name__ == "__main__":
    logger.info("\n=== STARTING WEBHOOK SERVER (webhook0605.py) ===")
    uvicorn.run("webhook0605:app",  # Changed to use webhook0605
                host="0.0.0.0",
                port=8001,
                reload=False,
                reload_dirs=["c:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot"],
                timeout_keep_alive=300,
                timeout_graceful_shutdown=300,
                limit_concurrency=100,
                backlog=2048
                )
