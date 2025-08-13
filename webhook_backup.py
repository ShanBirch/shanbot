# from .schemas.manychat import ManyChat_Webhook_Payload # Removed/Commented out
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
    build_member_chat_prompt
)
# Add import at the top
from calorie_manager_calorietracker import CalorieTracker_CalorieTracker

# Set up logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("manychat_webhook")
logger.info("Logging configured.")  # Confirm logging setup

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

# Onboarding Google Sheets Configuration
# Use the Coaching Onboarding Form spreadsheet ID
# Correct Coaching Onboarding Form
ONBOARDING_SPREADSHEET_ID = "1038Ep0lYGEtpipNAIzH7RB67-KOAfXA-TcUTKBKqIfo"
# Update range to include all columns from A to AAF in the Coaching Onboarding Form
# Make sure this points to the correct sheet tab name
ONBOARDING_RANGE_NAME = "Sheet1!A:AAF"

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
    """Process messages after a delay to allow for buffering"""
    try:
        await asyncio.sleep(15)  # Wait for buffer window
        logger.info(
            f"Buffer window expired for {ig_username}. Processing messages...")

        # Process buffered messages
        result = process_buffered_messages(ig_username)
        if not result:
            logger.info(f"No messages to process for {ig_username}")
            return

        combined_text, payload = result
        # Ensure ig_username is defined here
        ig_username = payload.get('ig_username')
        if not ig_username:
            logger.error(
                f"Cannot process message: Missing 'ig_username' in payload.")
            return

        subscriber_id = payload.get('id')
        first_name = payload.get('first_name', '')  # Extract names
        last_name = payload.get('last_name', '')

        # --- NEW: Check for Pending Food Analysis Photo --- START ---
        if food_analysis_pending.get(ig_username):
            logger.info(
                f"Checking incoming message from {ig_username} for pending food photo.")
            url_pattern = r"(https?://lookaside\.fbsbx\.com/ig_messaging_cdn/\?asset_id=[\w-]+&signature=[\w\-_.~]+)"
            match = re.search(url_pattern, combined_text)
            if match:
                image_url = match.group(1)
                logger.info(
                    f"Found image URL from {ig_username} while food analysis was pending: {image_url[:100]}...")

                # Clear the pending state FIRST
                food_analysis_pending.pop(ig_username, None)
                logger.info(
                    f"Cleared food_analysis_pending state for {ig_username}.")

                # Extract the user description (text part of the combined message)
                user_desc_text = combined_text.replace(image_url, "").strip()

                # Call the calorie analysis function, passing the description
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
                        f"Food analysis failed for pending request from {ig_username} (URL: {image_url[:50]}...)")
                    field_updates = {
                        "o1 Response": analysis_result,
                        "CONVERSATION": f"(User sent image for calorie check: {image_url[:50]}...)"
                    }
                else:
                    # Create calorie tracker instance
                    tracker = CalorieTracker_CalorieTracker()

                    # Get both responses
                    o1_response, o1_response_2 = tracker.handle_food_analysis_webhook(
                        ig_username=ig_username,
                        analysis_text=analysis_result,
                        description=user_desc_text
                    )

                    # Update ManyChat fields with both responses
                    field_updates = {
                        "o1 Response": o1_response,
                        "o1 Response 2": o1_response_2,
                        "CONVERSATION": f"(User sent image for calorie check: {image_url[:50]}...)"
                    }

                # Send response and update analytics
                update_success = update_manychat_fields(
                    subscriber_id, field_updates)
                if not update_success:
                    logger.error(
                        f"Failed to update ManyChat fields for pending food analysis for {ig_username}")

                update_analytics_data(
                    ig_username=ig_username,
                    user_message=f"(Sent food photo: {image_url[:50]}...)",
                    ai_response=f"Analysis: {analysis_result}",
                    subscriber_id=subscriber_id,
                    first_name=first_name,
                    last_name=last_name
                )
                logger.info(
                    f"Updated analytics for {ig_username} after handling pending food analysis.")

                return  # IMPORTANT: Stop processing here, analysis handled.
            else:
                logger.info(
                    f"Food analysis still pending for {ig_username}, but no image URL found in this message batch.")
                # Ensure ig_username is defined here (it should be from payload)
                if not ig_username:
                    logger.error(
                        "Cannot process message: Missing 'ig_username' after pending checks.")
                    return
                # Let the message proceed through normal flow if no image found
        # --- NEW: Check for Pending Food Analysis Photo --- END ---

        # --- Check for Media URLs and Form Check Status --- START ---
        # NOTE: This runs AFTER the pending food photo check above
        url_pattern = r"(https?://lookaside\.fbsbx\.com/ig_messaging_cdn/\?asset_id=[\w-]+&signature=[\w\-_.~]+)"
        urls_found = list(re.finditer(url_pattern, combined_text))
        processed_message = combined_text  # Start with original text
        media_url_to_analyze = None
        media_analysis_result = None
        media_type = None

        if urls_found:
            logger.info(
                f"Found {len(urls_found)} media URLs in message from {ig_username}")
            # Prioritize video if a form check is pending
            if form_check_pending.get(ig_username):
                for match in urls_found:
                    url = match.group(1)
                    # Simple check for video content type (can be refined)
                    try:
                        head_response = requests.head(url, timeout=5)
                        content_type = head_response.headers.get(
                            'Content-Type', '').lower()
                        if 'video' in content_type:
                            media_url_to_analyze = url
                            media_type = 'video'
                            logger.info(
                                f"Prioritizing video URL for pending form check: {url[:100]}...")
                            break  # Found the video for the form check
                    except requests.exceptions.RequestException as head_e:
                        logger.warning(
                            f"Could not check content type for {url[:100]}: {head_e}")
                if not media_url_to_analyze:
                    logger.warning(
                        f"Form check pending for {ig_username}, but no video URL found in message. Proceeding with text analysis.")
            else:
                # If no form check pending, just take the first URL for general processing
                media_url_to_analyze = urls_found[0].group(1)
                logger.info(
                    f"Processing first found media URL (no form check pending): {media_url_to_analyze[:100]}...")

        # --- Handle Pending Form Check with Video --- START ---
        if media_type == 'video' and form_check_pending.get(ig_username):
            logger.info(
                f"Processing video for pending form check from {ig_username}.")
            # Remove the pending state
            form_check_pending.pop(ig_username, None)

            # Call the technique analysis function
            analysis = get_video_analysis(
                media_url_to_analyze,
                GEMINI_API_KEY,
                GEMINI_MODEL_PRO,  # Pass primary model
                GEMINI_MODEL_FLASH,  # Pass first fallback
                GEMINI_MODEL_FLASH_STANDARD  # Pass second fallback
            )

            if analysis:
                logger.info(
                    f"Successfully received technique analysis for {ig_username}.")
                response_to_user = analysis  # Send the analysis directly
                # *** ADD COMPLETED FOR SUCCESS ***
                add_todo_item(ig_username, client_name_for_todo,
                              f"Successfully provided form check analysis: {media_url_to_analyze[:50]}...", status="completed")
            else:
                logger.error(f"Technique analysis failed for {ig_username}.")
                response_to_user = "Sorry, I couldn't analyze the video properly. Please ensure it's a valid video file link."
                # *** ADD TODO FOR FAILURE ***
                # Default status is pending
                add_todo_item(ig_username, client_name_for_todo,
                              f"Failed form check analysis: {media_url_to_analyze[:50]}...")

            # Update ManyChat
            field_updates = {
                "o1 Response": response_to_user,
                # Log action
                "CONVERSATION": f"(User sent video for form check: {media_url_to_analyze[:50]}...)"
            }
            update_success = update_manychat_fields(
                subscriber_id, field_updates)
            if not update_success:
                logger.error(
                    f"Failed to update ManyChat fields after form check analysis for {ig_username}")

            # Update analytics
            ai_response_for_analytics = f"AI provided form check analysis. Analysis successful: {bool(analysis)}"
            update_analytics_data(
                ig_username, f"(Sent video: {media_url_to_analyze[:50]}...)", ai_response_for_analytics, subscriber_id, first_name, last_name)
            logger.info(
                f"Updated analytics for {ig_username} after form check analysis.")
            return  # Form check analysis complete, exit processing for this message
        # --- Handle Pending Form Check with Video --- END ---

        # --- Process General Media (if not a form check video) --- START ---
        if media_url_to_analyze and not (media_type == 'video' and form_check_pending.get(ig_username)):
            logger.info(
                f"Performing general media analysis for URL: {media_url_to_analyze[:100]}...")
            media_type, media_analysis_result = analyze_media_url(
                media_url_to_analyze)
            if media_analysis_result:
                replacement_text = f"(Sent {media_type}: {media_analysis_result})" if media_type else f"(Sent media: {media_analysis_result})"
                # Replace the first found URL in the original text
                processed_message = combined_text.replace(
                    media_url_to_analyze, replacement_text, 1)
                logger.info(
                    f"Replaced media URL with analysis in processed message.")
            else:
                # Keep original text but log failure
                logger.warning(
                    f"General media analysis failed for {media_url_to_analyze[:100]}. Using original text.")
                processed_message = combined_text  # Ensure it stays as original text
        else:
            # No URLs or it was handled as form check video, use original text
            processed_message = combined_text
        # --- Process General Media (if not a form check video) --- END ---

        # --- Check for media URLs in the message and process them
        # url_pattern = r"(https?://lookaside\.fbsbx\.com/ig_messaging_cdn/\?asset_id=[\w-]+&signature=[\w\-_.~]+)"
        # urls_found = list(re.finditer(url_pattern, combined_text))

        # processed_message = combined_text
        # if urls_found:
        #     logger.info(f"Found {len(urls_found)} media URLs in message")
        #     for match in urls_found:
        #         url = match.group(1)
        #         media_type, result_text = analyze_media_url(url)
        #         if result_text:
        #             # Extract transcription from result text if it contains it
        #             if "Audio transcription:" in result_text:
        #                 processed_message = result_text.split("Audio transcription:")[
        #                     1].strip().rstrip(")")
        #                 logger.info(
        #                     f"Extracted audio transcription: {processed_message}")
        #             else:
        #                 processed_message = result_text
        #                 logger                 f"Using media analysis result: {processed_message}")

        # First try action detection (using potentially modified message)
        action_handled = await detect_and_handle_action(ig_username, processed_message, payload)

        if not action_handled:
            try:
                # Get user data - might be None for new users
                user_data_tuple = get_user_data(ig_username)

                # Prepare data for prompt, handling potentially new users
                current_stage = "Topic 1"  # Default for new user
                metrics_dict = {}  # Default for new user
                conversation_topics = []  # Default for new user
                bio = ""  # Default for new user
                trial_status = "Initial Contact"  # Default for new user
                interests = "[]"  # Default for new user (JSON string)
                formatted_history = ""  # Default for new user
                is_in_checkin_flow = False  # Default check-in status
                full_name = ig_username  # Default name

                if user_data_tuple:
                    # --- MODIFIED: Unpack tuple according to new definition ---
                    # Returns: (stage, metrics, topics, trial, _, _, interests_json, checkin_flow, name)
                    (
                        current_stage, metrics_dict, conversation_topics, trial_status,
                        _, _, interests_json, is_in_checkin_flow, full_name, checkin_type
                    ) = user_data_tuple
                    # --- END MODIFICATION ---

                    # Extract bio and history from metrics
                    bio = metrics_dict.get('client_analysis', {}).get(
                        'profile_bio', '') if metrics_dict else ''
                    # Use the returned JSON string or default
                    interests = interests_json if interests_json else "[]"
                    conversation_history = metrics_dict.get(
                        'conversation_history', []) if metrics_dict else []
                    formatted_history = format_conversation_history(
                        conversation_history)
                    logger.info(
                        f"Using existing user data for {ig_username}. Check-in flow: {is_in_checkin_flow}")
                else:
                    logger.info(
                        f"No existing data found for {ig_username}. Will create profile.")
                    # Defaults already set above are used
                    full_name = f"{first_name} {last_name}".strip(
                    ) or ig_username  # Construct name from payload

                # Always add current message to history for the prompt context
                full_conversation_for_prompt = f"{formatted_history}\\nLead: {processed_message}" if formatted_history else f"Lead: {processed_message}"

                # Get client details from payload (for new users) or metrics (for existing)
                # --- MODIFIED: Use full_name derived earlier ---
                prompt_full_name = full_name  # Use the name derived from get_user_data or payload

                # --- Get other details primarily from metrics, fallback to payload/empty ---
                metrics_client_details = metrics_dict.get(
                    'client_details', {}) if metrics_dict else {}
                prompt_first_name = metrics_client_details.get(
                    'first_name') or first_name  # Use from metrics or payload
                prompt_last_name = metrics_client_details.get(
                    'last_name') or last_name  # Use from metrics or payload
                prompt_sex = metrics_client_details.get('sex', '')
                prompt_fitness_goals = metrics_client_details.get(
                    'fitness_goals', '')
                prompt_dietary_requirements = metrics_client_details.get(
                    'dietary_requirements', '')
                prompt_training_frequency = metrics_client_details.get(
                    'training_frequency', '')

                # --- Conditionally Choose Prompt and Load Check-in Data --- START ---
                prompt_template = prompts.GENERAL_CHAT_PROMPT_TEMPLATE  # Default
                checkin_data_dict = None  # Default to None

                # --- MODIFIED: Select prompt based on check-in type --- START ---
                if is_in_checkin_flow and checkin_type:  # Only change template if both conditions are true
                    logger.info(
                        f"User {ig_username} is in check-in flow. Check-in type: '{checkin_type}'")
                    latest_checkin_file = find_latest_checkin_file(full_name)
                    if latest_checkin_file:
                        checkin_data_dict = load_json_data(latest_checkin_file)
                        if checkin_data_dict:
                            # Choose MON or WED template based on stored type
                            if checkin_type == 'monday':
                                prompt_template = prompts.CHECKIN_PROMPT_TEMPLATE_MON
                                logger.info(
                                    "Using CHECKIN_PROMPT_TEMPLATE_MON.")
                            elif checkin_type == 'wednesday':
                                prompt_template = prompts.CHECKIN_PROMPT_TEMPLATE_WED
                                logger.info(
                                    "Using CHECKIN_PROMPT_TEMPLATE_WED.")
                            else:
                                # If type is missing or unexpected, keep general chat
                                logger.warning(
                                    f"Unexpected checkin_type ('{checkin_type}'). Using GENERAL_CHAT_PROMPT_TEMPLATE.")
                        else:
                            logger.warning(
                                "Failed to load check-in data. Using GENERAL_CHAT_PROMPT_TEMPLATE.")
                    else:
                        logger.warning(
                            "Could not find latest check-in file. Using GENERAL_CHAT_PROMPT_TEMPLATE.")
                else:
                    logger.info(
                        f"Using default GENERAL_CHAT_PROMPT_TEMPLATE for {ig_username}")
                # --- END MODIFIED ---

                # --- Check for check-in ending keywords ---
                reset_checkin_flow = False
                if is_in_checkin_flow:
                    ending_keywords = ["thanks", "ok", "okay",
                                       "got it", "cool", "sweet", "perfect"]
                    if any(keyword in processed_message.lower() for keyword in ending_keywords):
                        reset_checkin_flow = True
                        logger.info(
                            f"Detected check-in ending keyword in message from {ig_username}. Flagging to reset flow.")

                # --- Format the chosen prompt ---
                prompt_args = {
                    "current_stage": current_stage,
                    "trial_status": trial_status,
                    "ig_username": ig_username,
                    "bio": bio,
                    "interests": interests,
                    "topics_str": "\n- ".join(conversation_topics) if conversation_topics else "No topics yet",
                    # --- Pass individual name components AND full name ---
                    "first_name": prompt_first_name,
                    "last_name": prompt_last_name,
                    "full_name": prompt_full_name,  # Added full name
                    # --- Pass other details ---
                    "sex": prompt_sex,
                    "fitness_goals": prompt_fitness_goals,
                    "dietary_requirements": prompt_dietary_requirements,
                    "training_frequency": prompt_training_frequency,
                    "current_melbourne_time_str": get_melbourne_time_str(),
                    "full_conversation": full_conversation_for_prompt
                }

                # Add check-in data placeholders if using the check-in template and data is available
                if prompt_template == prompts.CHECKIN_PROMPT_TEMPLATE and checkin_data_dict:
                    # Example: mapping keys from checkin_data_dict to prompt placeholders
                    prompt_args["checkin_date_range"] = checkin_data_dict.get(
                        "date_range", "N/A")
                    prompt_args["checkin_current_weight"] = checkin_data_dict.get(
                        "current_weight", "N/A")
                    prompt_args["checkin_total_weight_change"] = checkin_data_dict.get(
                        "total_weight_change", "N/A")
                    prompt_args["checkin_calories_consumed"] = checkin_data_dict.get(
                        "average_daily_calories", "N/A")
                    prompt_args["checkin_step_count"] = checkin_data_dict.get(
                        "average_daily_steps", "N/A")
                    prompt_args["checkin_sleep_hours"] = checkin_data_dict.get(
                        "average_daily_sleep", "N/A")
                    prompt_args["checkin_personalized_message"] = checkin_data_dict.get(
                        "personalized_message", "Keep up the great work!")  # Provide default

                # --- Define ALL expected keys for the selected template --- #
                expected_keys = []
                if prompt_template == prompts.CHECKIN_PROMPT_TEMPLATE:
                    # Add all keys specifically used in CHECKIN_PROMPT_TEMPLATE
                    expected_keys = [
                        "current_melbourne_time_str", "date_range", "current_weight",
                        "total_weight_change", "workouts_this_week", "calories_consumed",
                        "step_count", "sleep_hours", "personalized_message", "ig_username",
                        "full_name", "first_name", "last_name", "sex", "bio", "interests",
                        "fitness_goals", "dietary_requirements", "training_frequency",
                        "current_stage", "trial_status", "topics_str", "full_conversation",
                        "client_summary"  # Include the potentially missing key
                    ]
                elif prompt_template == prompts.GENERAL_CHAT_PROMPT_TEMPLATE:
                    # Add all keys specifically used in GENERAL_CHAT_PROMPT_TEMPLATE
                    expected_keys = [
                        "current_melbourne_time_str", "ig_username", "full_name",
                        "first_name", "last_name", "sex", "bio", "interests",
                        "fitness_goals", "dietary_requirements", "training_frequency",
                        "current_stage", "trial_status", "topics_str", "full_conversation"
                    ]
                # Add more elif blocks here if you have other templates

                # --- Ensure all expected keys exist with a default value --- #
                for key in expected_keys:
                    if key not in prompt_args:
                        logger.warning(
                            f"Expected key '{key}' missing from prompt_args. Setting default 'N/A'.")
                        prompt_args[key] = "N/A"

                # Format the prompt, handling potential missing keys gracefully
                try:
                    # Now format using the guaranteed-to-have-all-keys dict
                    prompt = prompt_template.format(**prompt_args)
                    template_name = "CHECKIN_PROMPT_TEMPLATE" if prompt_template == prompts.CHECKIN_PROMPT_TEMPLATE else "GENERAL_CHAT_PROMPT_TEMPLATE"
                    logger.info(
                        f"Successfully formatted prompt using {template_name}")
                except Exception as format_e:
                    logger.error(
                        f"Unexpected error formatting prompt: {format_e}", exc_info=True)
                    # Fallback to very basic prompt if formatting fails critically
                    prompt = f"User message: {processed_message}\nHistory: {full_conversation_for_prompt}"

                # --- Conditionally Choose Prompt and Load Check-in Data --- END ---

                # Get AI response
                response = await get_ai_response(prompt)
                if not response:
                    # Fallback response
                    response = "Sorry, I couldn't process that right now. Can you try rephrasing?"
                    logger.error(
                        f"No response generated for {ig_username}, using fallback.")
                else:
                    logger.info(f"Generated AI response for {ig_username}")

                # --- START: Onboarding Trigger Detection ---
                onboarding_trigger_phrase = "get you onboarded"
                start_onboarding = False
                if response and onboarding_trigger_phrase in response.lower():  # Check in lowercase
                    start_onboarding = True
                    logger.info(
                        f"Onboarding trigger phrase detected for {ig_username}")

                if start_onboarding:
                    # --- ONBOARDING FLOW ---
                    logger.info(f"Starting onboarding flow for {ig_username}")

                    # 1. Update Analytics State (Set onboarding flag and expectation)
                    analytics_update_successful = False  # Flag to track success
                    try:
                        # Load current data to update
                        analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
                        try:
                            with open(analytics_file_path, "r") as f:
                                analytics_data = json.load(f)
                        except (FileNotFoundError, json.JSONDecodeError):
                            logger.error(
                                f"Failed to load analytics data from {analytics_file_path} for onboarding.")
                            # Fallback to avoid crash
                            analytics_data = {"conversations": {}}

                        # Find the user (logic similar to update_analytics_data)
                        target_user_id = None
                        conversations_data = analytics_data.get(
                            'conversations', {})
                        search_ig_username_lower = ig_username.strip().lower()
                        for user_id, user_data_loop in conversations_data.items():
                            if isinstance(user_data_loop, dict):
                                metrics_data = user_data_loop.get(
                                    "metrics", {})
                                if isinstance(metrics_data, dict):
                                    json_ig_username = metrics_data.get(
                                        "ig_username", None)
                                    if isinstance(json_ig_username, str) and json_ig_username.strip().lower() == search_ig_username_lower:
                                        target_user_id = user_id
                                        break

                        if target_user_id and target_user_id in conversations_data:
                            metrics_to_update = conversations_data[target_user_id].setdefault(
                                'metrics', {})
                            metrics_to_update['is_onboarding'] = True
                            # Ask for all meals first
                            metrics_to_update['expected_onboarding_input'] = "all_meals"
                            # Optionally clear previous target calculations if re-onboarding
                            metrics_to_update.pop('target_calories', None)
                            metrics_to_update.pop('target_protein', None)
                            metrics_to_update.pop('target_carbs', None)
                            metrics_to_update.pop('target_fats', None)
                            logger.info(
                                f"Set onboarding state for user {target_user_id}")

                            # Save the updated analytics data immediately
                            with open(analytics_file_path, "w") as f:
                                json.dump(analytics_data, f, indent=2)
                            logger.info(
                                f"Saved updated onboarding state for {target_user_id}")
                            analytics_update_successful = True  # Mark success

                        else:
                            logger.error(
                                f"Could not find user {ig_username} (ID: {target_user_id}) in analytics data to start onboarding.")
                            # Keep start_onboarding as True, but analytics_update_successful is False

                    except Exception as e:
                        logger.error(
                            f"Error updating analytics state for onboarding trigger for {ig_username}: {e}", exc_info=True)
                        # Keep start_onboarding as True, but analytics_update_successful is False

                    # 2. Prepare and Send the First Onboarding Question (Only if state update was successful)
                    if analytics_update_successful:
                        first_onboarding_question = "Awesome, let's get you onboarded. Ill sought it all out for you, first thing to do is write you up a quick 2-day meal plan, whats your go to meals? Breakfast lunch, dinner, do you know 2 of each?"
                        onboarding_field_updates = {
                            "o1 Response": first_onboarding_question,
                            # Keep user's trigger message in CONVERSATION for context
                            "CONVERSATION": processed_message
                        }
                        onboarding_update_success = update_manychat_fields(
                            subscriber_id, onboarding_field_updates)
                        if not onboarding_update_success:
                            logger.error(
                                f"Failed to send first onboarding question to {ig_username}")
                        else:
                            logger.info(
                                f"Sent first onboarding question to {ig_username}")

                        # 3. Update Analytics History (Special Entry)
                        # Use the user's message that triggered the flow, but a custom AI response
                        onboarding_ai_response = "[Onboarding Triggered - Asking about go-to meals]"
                        update_analytics_data(
                            ig_username=ig_username,
                            # The user message that contained the trigger phrase (or media analysis)
                            user_message=processed_message,
                            ai_response=onboarding_ai_response,
                            subscriber_id=subscriber_id,
                            first_name=first_name,
                            last_name=last_name,
                            # Keep existing logic for check-in reset
                            set_checkin_flow_false=reset_checkin_flow
                        )
                        logger.info(
                            f"Updated analytics history for {ig_username} to reflect onboarding start.")
                    else:
                        # If analytics update failed, fallback to sending original response
                        logger.warning(
                            f"Analytics update failed for onboarding trigger for {ig_username}. Sending original AI response instead.")
                        start_onboarding = False  # Flip the flag to fall through to the else block

                # --- END ONBOARDING FLOW ---

                # --- Check if we should proceed with standard response (NOT onboarding OR onboarding failed) ---
                if not start_onboarding:
                    # --- STANDARD RESPONSE FLOW ---
                    field_updates = {
                        "o1 Response": response,
                        "CONVERSATION": processed_message  # User's message
                    }

                    success = update_manychat_fields(
                        subscriber_id, field_updates)
                    if not success:
                        logger.error(
                            f"Failed to update ManyChat fields for subscriber {subscriber_id} ({ig_username})")
                    else:
                        logger.info(
                            f"Successfully updated ManyChat fields for {ig_username}")

                    # Update analytics (this will create the user if they don't exist)
                    update_analytics_data(
                        ig_username=ig_username,
                        user_message=processed_message,
                        ai_response=response,
                        subscriber_id=subscriber_id,  # Pass required ID
                        first_name=first_name,       # Pass required name
                        last_name=last_name,         # Pass required name
                        # --- Pass the reset flag ---
                        set_checkin_flow_false=reset_checkin_flow
                    )
                    logger.info(
                        f"Updated analytics for {ig_username} (created if new). Reset check-in flag: {reset_checkin_flow}")
                # --- END STANDARD RESPONSE FLOW ---

            except Exception as e:
                logger.error(
                    f"Error in general chat processing for {ig_username}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Error in delayed message processing: {str(e)}")
    finally:
        # Ensure buffer is cleared even if processing fails
        if ig_username in message_buffer:
            message_buffer.pop(ig_username, None)
            logger.info(
                f"Cleared message buffer for {ig_username} after processing")


@app.post("/webhook/manychat")
async def process_manychat_webhook(request: Request):
    try:
        # Parse the request body
        data = await request.json()
        logger.info(f"Received webhook request body: {json.dumps(data)}")
        logger.info(f"Parsed request data: {json.dumps(data, indent=2)}")

        # Extract Instagram username and subscriber ID
        ig_username = data.get('ig_username', '')
        subscriber_id = data.get('id', '')

        if not ig_username:
            logger.error("No Instagram username found in payload")
            return {"status": "error", "message": "No Instagram username found"}

        # Get the last input text
        message_text = data.get('last_input_text', '')
        if not message_text:
            logger.error("No message text found in payload")
            return {"status": "error", "message": "No message text found"}

        # Add message to buffer
        add_to_message_buffer(ig_username, data)
        logger.info(f"Added message to buffer for {ig_username}")

        # Create delayed processing task
        asyncio.create_task(delayed_message_processing(ig_username))
        logger.info(f"Created delayed processing task for {ig_username}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
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
    uvicorn.run("webhook0505:app",  # Use import string instead of app object
                host="0.0.0.0",
                port=8001,  # Changed back to 8001
                reload=True,  # Enable auto-reload
                # Watch this directory for changes
                reload_dirs=["c:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot"],
                timeout_keep_alive=300,
                timeout_graceful_shutdown=300,
                limit_concurrency=100,
                backlog=2048
                )
