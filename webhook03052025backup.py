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


def call_gemini_with_retry(model_name: str, prompt: str, retry_count: int = 0) -> Optional[str]:
    """
    Call Gemini API with retry logic and multiple fallback models.

    Args:
        model_name: Name of the Gemini model to use
        prompt: The prompt to send to Gemini
        retry_count: Current retry attempt number

    Returns:
        Generated text or None if all retries fail
    """
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        if "429" in str(e) and retry_count < MAX_RETRIES:
            # Rate limit: if primary model, fallback to flash-thinking; otherwise retry same model
            if model_name == GEMINI_MODEL_PRO:
                logger.warning(
                    f"Rate limit hit for {model_name}. Falling back to flash-thinking model after delay.")
                time.sleep(RETRY_DELAY)
                return call_gemini_with_retry(GEMINI_MODEL_FLASH, prompt, retry_count + 1)
            else:
                wait_time = RETRY_DELAY * (retry_count + 1)
                logger.warning(
                    f"Rate limit hit. Waiting {wait_time} seconds before retry {retry_count + 1} on {model_name}")
                time.sleep(wait_time)
                return call_gemini_with_retry(model_name, prompt, retry_count + 1)
        elif retry_count < MAX_RETRIES:  # Other errors, try fallback models
            if model_name == GEMINI_MODEL_PRO:
                logger.warning(
                    f"Main model failed: {e}. Trying first fallback model after delay.")
                time.sleep(RETRY_DELAY)
                return call_gemini_with_retry(GEMINI_MODEL_FLASH, prompt, retry_count + 1)
            elif model_name == GEMINI_MODEL_FLASH:
                logger.warning(
                    f"First fallback model failed: {e}. Trying second fallback model after delay.")
                time.sleep(RETRY_DELAY)
                return call_gemini_with_retry(GEMINI_MODEL_FLASH_STANDARD, prompt, retry_count + 1)
        logger.error(f"All Gemini attempts failed: {e}")
        return None
# --- Gemini Configuration END ---


def split_response_into_messages(text: str) -> List[str]:
    """Split response text into up to 3 messages of roughly equal length."""
    logger.info(f"Splitting response of length {len(text)}")

    # If text is short enough, return as single message
    if len(text) <= 150:
        return [text]

    # Split into sentences while preserving punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # If only 1-2 sentences, return as is
    if len(sentences) <= 2:
        return sentences

    # For 3+ sentences, combine into up to 3 messages
    result = []
    current_message = ""
    target_length = len(text) / 3  # Aim for roughly equal thirds

    for sentence in sentences:
        if len(current_message) + len(sentence) <= target_length or not current_message:
            if current_message:
                current_message += " "
            current_message += sentence
        else:
            result.append(current_message)
            current_message = sentence

        # Don't exceed 3 messages
        if len(result) == 2:
            result.append(current_message + " " +
                          " ".join(sentences[sentences.index(sentence)+1:]))
            break

    # Handle case where we haven't hit 3 messages yet
    if current_message and len(result) < 3:
        result.append(current_message)

    logger.info(f"Split into {len(result)} messages")
    for i, msg in enumerate(result):
        logger.info(f"Message {i+1} length: {len(msg)}")

    return result


def format_conversation_history(history_list: List[Dict[str, str]]) -> str:
    """Formats the conversation history list into a readable string."""
    formatted_lines = []
    for entry in history_list:
        timestamp = entry.get("timestamp", "")
        msg_type = entry.get("type", "unknown").capitalize()
        text = entry.get("text", "")
        # Format timestamp nicely if possible (optional)
        try:
            # Attempt to parse and format timestamp
            dt_object = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00"))
            formatted_ts = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            formatted_ts = timestamp  # Fallback to original string

        formatted_lines.append(f"{formatted_ts} [{msg_type}]: {text}")
    return "\n".join(formatted_lines)


def get_user_data(ig_username: str) -> tuple[str, Dict, list, str, float, str, str]:
    """
    Load user data from analytics_data_good.json with detailed logging
    Returns: (current_stage, user_data, conversation_topics,
              trial_status, last_bot_timestamp, last_bot_response, interests)
    """
    logger.info(f"\n=== GET USER DATA START ===")
    logger.info(f"Searching for user: '{ig_username}'")

    analytics_file_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"
    logger.info(f"Loading data from: {analytics_file_path}")

    try:
        with open(analytics_file_path, 'r') as f:
            analytics_data = json.load(f)
        logger.info("Successfully loaded analytics file")

        # Debug log to show structure
        logger.info(
            f"Available keys in analytics data: {list(analytics_data.keys())}")

    except Exception as e:
        logger.error(f"Failed to load analytics file: {e}")
        return None, None, [], None, 0.0, None, None

    logger.info(f"Searching for username: '{ig_username}'")

    # Look for user in conversations
    conversations = analytics_data.get('conversations', {})
    user_data = None

    # First try direct match in conversations
    if ig_username in conversations:
        user_data = conversations[ig_username].get('metrics', {})
        logger.info(f"Found user directly in conversations: {ig_username}")
    else:
        # If not found directly, search through all conversations
        for conv_id, conv_data in conversations.items():
            if isinstance(conv_data, dict) and 'metrics' in conv_data:
                metrics = conv_data['metrics']
                if metrics.get('ig_username') == ig_username:
                    user_data = metrics
                    logger.info(
                        f"Found user data under conversation ID: {conv_id}")
                    break

    if not user_data:
        logger.warning(f"User {ig_username} not found in conversations")
        return None, None, [], None, 0.0, None, None

    logger.info(f"\n=== USER FOUND: {ig_username} ===")
    logger.info(f"Available keys in user_data: {list(user_data.keys())}")

    # Get current stage
    current_stage = "Topic 1"  # Default value
    if "journey_stage" in user_data and "current_stage" in user_data["journey_stage"]:
        current_stage = user_data["journey_stage"]["current_stage"]
        logger.info(f"FOUND current_stage = {current_stage}")
    else:
        logger.info("NO current_stage found - defaulting to Topic 1")

    # Get bio
    bio = None
    if "client_analysis" in user_data and "profile_bio" in user_data["client_analysis"]:
        bio = user_data["client_analysis"]["profile_bio"]
        logger.info(f"FOUND bio = {bio}")
    else:
        logger.info("NO bio found")

    # Get conversation topics
    conversation_topics = []
    if "client_analysis" in user_data and "conversation_topics" in user_data["client_analysis"]:
        conversation_topics = user_data["client_analysis"]["conversation_topics"]
        logger.info("FOUND conversation topics:")
        for i, topic in enumerate(conversation_topics, 1):
            logger.info(f"  Topic {i}: {topic}")
    else:
        logger.info("NO conversation topics found")

    # Get interests
    interests = []
    if "client_analysis" in user_data and "interests" in user_data["client_analysis"]:
        interests = user_data["client_analysis"]["interests"]
        logger.info("FOUND interests:")
        for i, interest in enumerate(interests, 1):
            logger.info(f"  Interest {i}: {interest}")
    else:
        logger.info("NO interests found")

    # Get trial status
    trial_status = None
    if "trial_week_1" in user_data and user_data["trial_week_1"]:
        trial_status = "Trial Week 1"
        logger.info(f"FOUND trial status = {trial_status}")

    # Get conversation history
    conversation_history = []
    if "conversation_history" in user_data:
        conversation_history = user_data["conversation_history"]
        logger.info(
            f"FOUND conversation history with {len(conversation_history)} entries")
        logger.info("Last 3 messages:")
        for msg in conversation_history[-3:]:
            logger.info(f"  {msg['type']}: {msg['text'][:100]}...")

    # Get last bot response timestamp
    last_bot_response = None
    if conversation_history:
        for msg in reversed(conversation_history):
            if msg["type"] == "ai":
                last_bot_response = msg["timestamp"]
                logger.info(
                    f"FOUND last bot response timestamp = {last_bot_response}")
                break

    logger.info("\n=== DATA RETRIEVAL COMPLETE ===")

    return (
        current_stage,
        user_data,  # Return full user data instead of just formatted history
        conversation_topics,
        trial_status,
        0.0,  # placeholder for any float value needed
        last_bot_response,
        json.dumps(interests) if interests else None
    )


def get_melbourne_time_str():
    """Get current Melbourne time with error handling."""
    try:
        melbourne_tz = pytz.timezone('Australia/Melbourne')
        current_time = datetime.now(melbourne_tz)
        return current_time.strftime("%Y-%m-%d %I:%M %p AEST")
    except Exception as e:
        logger.error(f"Error getting Melbourne time: {e}")
        # Fallback to UTC or local time if pytz fails
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}

# --- ADDED: Intent Detection Function Stub --- START ---

# Global dictionary to store program information between messages
program_info = {}


async def detect_and_handle_action(ig_username: str, message_text: str, data: Dict = None) -> bool:
    """Uses Gemini to detect user intent and handles multiple actions like Trainerize edits within one message."""
    logger.info(
        f"[detect_and_handle_action] Analyzing message from {ig_username} for multiple actions: {message_text[:100]}"
    )

    if not data:
        logger.error("No data dictionary provided to detect_and_handle_action")
        return False

    # --- NEW MULTI-ACTION PROMPT --- START ---
    intent_prompt = f"""Analyze this message to identify ALL requested workout program changes (adding or removing exercises).

Message: "{message_text}"

Standard Workout Day Categories & Target Output Types:
- Leg Day (keywords: leg, legs, lower body) -> output type: "Leg Day"
- Back day (keywords: back, pull) -> output type: "Back day"
- Chest day (keywords: chest, push) -> output type: "Chest day"
- Core Day (keywords: core, abs, abdominals) -> output type: "Core Day"
- Shoulder Day (keywords: shoulders, delts) -> output type: "Shoulder Day"
- Cardio Day (keywords: cardio, run, bike, conditioning) -> output type: "Cardio Day"
- Arm Day (keywords: arms, biceps, triceps) -> output type: "Arm Day"

Instructions:
1. Identify **every distinct action** requested (add, remove). Treat modification requests as 'remove' for now.
2. For each action, identify the **exercise name**.
3. For each action, identify the **specific workout day** mentioned or inferred (e.g., "leg day", "chest day").
4. Map the workout day to one of the **Standard Workout Day Categories** above and use the full `output type` (e.g., "Leg Day", "Back day") for the 'workout_type' field.
5. **Prioritize user-mentioned day** for 'workout_type'. Infer if not mentioned.
6. If adding an exercise, include default sets ('3') and reps ('10'). These are not needed for 'remove'.
7. Respond ONLY with a JSON object containing a list called "actions", even if only one action is found. If no workout actions are found, the list should be empty and "is_workout_request" should be false.

Format:
{{
    "is_workout_request": true/false,
    "actions": [
        {{
            "action": "add/remove", // MUST be "add" or "remove"
            "workout_type": "Leg Day/Back day/...", // Standard full output type or null
            "exercise_name": "specific exercise name" or null,
            "sets": "3" or null, // Only for "add"
            "reps": "10" or null  // Only for "add"
        }},
        // ... more actions if found ...
    ],
    "confidence": 0-100, // Overall confidence for detecting *any* workout request
    "explanation": "brief explanation summarizing all actions identified (e.g., 'User wants to remove X and add Y to Back day')"
}}
"""
    # --- NEW MULTI-ACTION PROMPT --- END ---

    try:
        # Get intent analysis from Gemini
        intent_response = call_gemini_with_retry(
            GEMINI_MODEL_FLASH, intent_prompt)
        if not intent_response:
            logger.error("Failed to get intent analysis from Gemini")
            return False

        # Clean the response of any markdown formatting
        cleaned_response = intent_response.strip()
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.split("\n", 1)[1]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response.rsplit("\n", 1)[0]
        cleaned_response = cleaned_response.replace("json\n", "", 1)

        # Parse the cleaned JSON
        intent_data = json.loads(cleaned_response)
        logger.info(f"Intent analysis: {json.dumps(intent_data, indent=2)}")

        # Check if it's a workout request and confidence is high
        if intent_data.get('is_workout_request', False) and intent_data.get('confidence', 0) > 70:
            requested_actions = intent_data.get('actions', [])
            if not requested_actions:
                logger.warning(
                    "Workout request detected, but no actions found in the list.")
                return False  # Not handled if list is empty

            # --- Check if essential info is present for *at least one* action ---
            # We proceed if we have enough info to attempt *something*, even if later actions lack detail.
            can_proceed = False
            target_workout_type = None
            for action_item in requested_actions:
                if action_item.get('workout_type') and action_item.get('exercise_name') and action_item.get('action'):
                    can_proceed = True
                    # Use workout type from the first valid action for navigation
                    target_workout_type = action_item.get('workout_type')
                    break

            if not can_proceed:
                logger.warning(
                    "Detected workout request, but missing essential details (workout_type, exercise_name, or action) for all actions.")
                # TODO: Potentially ask for clarification here instead of returning False
                # For now, if the initial analysis didn't get enough, we won't proceed.
                # Construct a generic "need more info" response?
                # Example: response = "I see you want to change your workout, but I need a bit more detail. Can you tell me the specific exercise, the action (add/remove), and which workout day?"
                # update_manychat_fields(...) and return True?
                return False

            # --- Prepare for Trainerize --- #
            client_full_name = data.get(
                'name') or f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
            subscriber_id = data.get('id')
            if not client_full_name or not subscriber_id:
                logger.error(
                    "Missing client name or subscriber ID for Trainerize automation.")
                return False  # Cannot proceed without these

            logger.info(
                f"Attempting Trainerize modifications for {client_full_name} based on {len(requested_actions)} actions...")

            trainerize = None
            modification_attempted_and_failed = False
            action_summary = {"success": [], "failed": []}
            overall_success = False

            try:
                # --- Trainerize Login and Navigation (Done Once) --- #
                trainerize = TrainerizeAutomation()
                username = "shannonbirch@cocospersonaltraining.com"
                password = "cyywp7nyk2"

                if not trainerize.login(username, password):
                    raise Exception("Failed to login to Trainerize")
                trainerize.handle_notification_popup()

                if not trainerize.navigate_to_client(client_full_name):
                    raise Exception("Failed to navigate to client")

                if not trainerize.navigate_to_training_program():
                    raise Exception("Failed to navigate to training program")

                # Use the workout type determined earlier (from first valid action)
                if not target_workout_type:
                    # This case should be caught by the can_proceed check, but as a safeguard:
                    raise Exception(
                        "Target workout type could not be determined.")

                if not trainerize.click_workout_fuzzy(target_workout_type):
                    exact_workout_name = f"{target_workout_type.title()} Day"
                    raise Exception(
                        f"Failed to find workout containing '{target_workout_type}' using fuzzy match (tried exact: {exact_workout_name})")

                if not trainerize.click_edit_workout():
                    raise Exception("Failed to enter edit mode")
                # --- End Login and Navigation --- #

                # --- Loop Through Requested Actions --- START ---
                for i, action_item in enumerate(requested_actions):
                    action_type = action_item.get('action')
                    exercise_name = action_item.get('exercise_name')
                    # Ensure workout_type matches the one we navigated to, or log a warning?
                    # For simplicity, we assume all actions in one message are for the same workout day found initially.
                    current_workout_type = action_item.get('workout_type')
                    if current_workout_type != target_workout_type:
                        logger.warning(
                            f"Action {i+1} workout type '{current_workout_type}' differs from navigated type '{target_workout_type}'. Proceeding anyway.")

                    if not action_type or not exercise_name:
                        logger.warning(
                            f"Skipping invalid action item {i+1}: Missing action or exercise name. Details: {action_item}")
                        action_summary["failed"].append(
                            f"Item {i+1} (invalid details)")
                        continue  # Skip to next action

                    logger.info(
                        f"--- Performing Action {i+1}/{len(requested_actions)}: {action_type.upper()} '{exercise_name}' ---")
                    action_successful_this_time = False
                    try:
                        if action_type == 'add':
                            # Use default if Gemini didn't provide
                            sets = action_item.get('sets', '3')
                            # Use default if Gemini didn't provide
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
                        # Continue to the next action even if one fails

                    # Record result
                    if action_successful_this_time:
                        action_summary["success"].append(
                            f"{action_type} {exercise_name}")
                    else:
                        action_summary["failed"].append(
                            f"{action_type} {exercise_name}")
                # --- Loop Through Requested Actions --- END ---

                # --- Save Workout (After Loop) --- START ---
                logger.info(
                    "Attempting to save workout after processing all actions...")
                if trainerize.save_workout():
                    logger.info("Workout saved successfully.")
                    overall_success = True  # Mark overall success if save worked
                else:
                    logger.error("Failed to save workout after modifications!")
                    overall_success = False  # Mark overall failure if save failed
                    # Even if save fails, report on individual actions
                # --- Save Workout (After Loop) --- END ---

            except Exception as e:
                logger.error(f"Error during Trainerize automation: {str(e)}")
                # Note failure, summary will be empty/reflect failures
                action_summary["failed"].append(
                    f"Overall process failed ({str(e)[:50]}...)")
                modification_attempted_and_failed = True  # Mark as failed
            finally:
                if trainerize:
                    if not modification_attempted_and_failed and overall_success:
                        logger.info(
                            "Trainerize modifications successful, cleaning up.")
                        trainerize.cleanup()
                    else:
                        logger.warning(
                            "Trainerize modification had failures or save failed! Leaving browser open.")
                        print(
                            "\n*** Trainerize browser window left open due to error or failed save. Please close it manually. ***\n")
                        # No cleanup called here deliberately

            # --- Construct Final Response --- #
            # Simplified response logic based on overall success and any failures
            if overall_success and not action_summary["failed"]:
                # All actions succeeded and saved
                response = "Easy updated your program, need anything else?"
            else:
                # Either an action failed or the save failed
                response = "Yep ill get onto that asap and get back to you when its done!"

            # --- Update ManyChat and Analytics --- #
            field_updates = {
                "o1 Response": response,
                "CONVERSATION": message_text  # Original message
            }
            update_success = update_manychat_fields(
                subscriber_id, field_updates)
            if not update_success:
                logger.error(
                    f"Failed to update ManyChat fields for {ig_username}")

            # Update analytics with a summary of actions
            ai_response_for_analytics = f"Attempted actions: Success={action_summary['success']}, Failed={action_summary['failed']}, Save Success={overall_success}"
            update_analytics_data(ig_username, message_text,
                                  ai_response_for_analytics)
            logger.info(
                f"Updated analytics data for {ig_username} with action summary.")

            return True  # Indicate action was handled (or attempted)

        else:
            # Not a workout request or low confidence
            logger.info(
                "Message not identified as a confident workout modification request.")
            return False

    except json.JSONDecodeError as json_err:
        logger.error(
            f"Failed to parse Gemini response as JSON: {intent_response}\nError: {json_err}")
        return False  # Failed to parse, cannot handle

    except Exception as e:
        logger.error(f"Error in detect_and_handle_action: {str(e)}")
        # Maybe send a generic error to Manychat?
        return False  # Indicate failure to handle

# --- ADDED: Intent Detection Function Stub --- END ---

# --- Onboarding Google Sheets Helper Function START ---


def get_checkin_data(instagram_name: str) -> Dict[str, str]:
    """
    Retrieve client data for check-in from the Coaching Onboarding Form.

    Args:
        instagram_name: Instagram username to search for

    Returns:
        Dictionary with client data fields
    """
    logger.info(f"Retrieving check-in data for: {instagram_name}")

    try:
        # This uses the same credentials and spreadsheet as the onboarding flow
        creds = google.oauth2.service_account.Credentials.from_service_account_file(
            SHEETS_CREDENTIALS_PATH, scopes=SCOPES)
        service = googleapiclient.discovery.build(
            'sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        result = sheet.values().get(
            spreadsheetId=ONBOARDING_SPREADSHEET_ID,
            range=ONBOARDING_RANGE_NAME
        ).execute()

        values = result.get('values', [])
        if not values:
            logger.error("No data found in onboarding sheet")
            return {}

        # Get the header row to understand column positions
        headers = values[0]

        # Find the column indices for each required field
        instagram_col = next(
            (i for i, h in enumerate(headers) if "Instagram" in h), None)
        first_name_col = next(
            (i for i, h in enumerate(headers) if "First name" in h), None)
        last_name_col = next(
            (i for i, h in enumerate(headers) if "Last Name" in h), None)
        gender_col = next(
            (i for i, h in enumerate(headers) if "Gender" in h), None)
        weight_col = next(
            (i for i, h in enumerate(headers) if "Weight" in h), None)
        goals_col = next((i for i, h in enumerate(headers)
                         if "Long term fitness goals" in h), None)
        diet_col = next((i for i, h in enumerate(headers)
                        if "Dietary Requirements" in h), None)
        dob_col = next((i for i, h in enumerate(headers)
                       if "Date of Birth" in h), None)
        height_col = next(
            (i for i, h in enumerate(headers) if "Height" in h), None)
        gym_col = next((i for i, h in enumerate(
            headers) if "Gym Access" in h), None)
        freq_col = next((i for i, h in enumerate(headers)
                        if "Training Frequency" in h), None)
        exercises_col = next((i for i, h in enumerate(
            headers) if "Exercises they enjoy" in h), None)
        calories_col = next((i for i, h in enumerate(
            headers) if "Daily Calories" in h), None)
        conversation_col = next((i for i, h in enumerate(
            headers) if "Total Conversation" in h), None)
        legit_col = next((i for i, h in enumerate(
            headers) if "Legit Checkin" in h), None)

        client_data = {}
        # Search for the row with the matching Instagram username
        for row in values[1:]:  # Skip header row
            if instagram_col is not None and len(row) > instagram_col:
                row_instagram = row[instagram_col].strip(
                ).lower() if row[instagram_col] else ""
                if instagram_name.lower() in row_instagram:
                    logger.info(
                        f"Found client in onboarding sheet: {row_instagram}")

                    # Extract all required fields
                    client_data = {
                        "First Name": row[first_name_col] if first_name_col is not None and len(row) > first_name_col else "",
                        "Last Name": row[last_name_col] if last_name_col is not None and len(row) > last_name_col else "",
                        "Gender": row[gender_col] if gender_col is not None and len(row) > gender_col else "",
                        "Weight": row[weight_col] if weight_col is not None and len(row) > weight_col else "",
                        "Long Term Goals": row[goals_col] if goals_col is not None and len(row) > goals_col else "",
                        "Dietary Requirements": row[diet_col] if diet_col is not None and len(row) > diet_col else "",
                        "Date of Birth": row[dob_col] if dob_col is not None and len(row) > dob_col else "",
                        "Height": row[height_col] if height_col is not None and len(row) > height_col else "",
                        "Gym Access": row[gym_col] if gym_col is not None and len(row) > gym_col else "",
                        "Training Frequency": row[freq_col] if freq_col is not None and len(row) > freq_col else "",
                        "Instagram Name": row[instagram_col] if instagram_col is not None and len(row) > instagram_col else "",
                        "Exercises Enjoyed": row[exercises_col] if exercises_col is not None and len(row) > exercises_col else "",
                        "Daily Calories": row[calories_col] if calories_col is not None and len(row) > calories_col else "",
                        "Total Conversation": row[conversation_col] if conversation_col is not None and len(row) > conversation_col else "",
                        "Legit Checkin": row[legit_col] if legit_col is not None and len(row) > legit_col else ""
                    }
                    break

        if not client_data:
            logger.warning(
                f"Client with Instagram name {instagram_name} not found in onboarding sheet")

        return client_data

    except Exception as e:
        logger.error(f"Error retrieving checkin data: {str(e)}")
        return {}


def build_member_chat_prompt(client_data: Dict[str, Any], current_message: str, conversation_history: str = "") -> str:
    try:
        # Extract values from the nested structure we see in the logs
        journey_stage = client_data.get('journey_stage', {})
        current_stage = journey_stage.get('current_stage', 'Topic 1') if isinstance(
            journey_stage, dict) else journey_stage
        trial_status = "Trial Week 1" if client_data.get(
            'trial_week_1') else "Initial Contact"

        # Get user profile information from client_analysis
        client_analysis = client_data.get('client_analysis', {})
        bio = client_analysis.get('profile_bio', 'Not available')
        interests = client_analysis.get('interests', [])

        # Get client details from the nested structure
        client_details = client_data.get('client_details', {})
        first_name = client_details.get('first_name', '')
        last_name = client_details.get('last_name', '')
        sex = client_details.get('sex', '')
        fitness_goals = client_details.get('fitness_goals', '')
        dietary_requirements = client_details.get('dietary_requirements', '')
        training_frequency = client_details.get('training_frequency', '')

        # Get conversation topics
        topics = client_analysis.get('conversation_topics', [])
        topics_str = "\n- " + \
            "\n- ".join(topics) if topics else "No topics recorded yet"

        # Get current time
        current_melbourne_time_str = get_melbourne_time_str()

        # Format the prompt template
        prompt = f"""Current Conversation Context:
Stage Information:
Current Stage: {current_stage}
Trial Status: {trial_status}

User Profile Information:
Instagram: @{client_data.get('ig_username', '')}
Bio: {bio}
Interests: {json.dumps(interests)}

Conversation Topics to Cover:
{topics_str}

Client Details:
Name: {first_name} {last_name}
Sex: {sex}
Fitness Goals: {fitness_goals}
Dietary Requirements: {dietary_requirements}
Training Frequency: {training_frequency}

Current Context:
Time in Melbourne: {current_melbourne_time_str}

Full Conversation History:
{conversation_history}

Current Message:
{current_message}
"""
        return prompt
    except Exception as e:
        logger.error(f"Error building member chat prompt: {str(e)}")
        # Return a simplified prompt if there's an error
        return f"Message: {current_message}\nHistory: {conversation_history}"


def update_analytics_data(ig_username: str, user_message: str, ai_response: str):
    """Reads analytics_data_good.json, updates conversation history, and writes back."""
    logger.info(
        f"---> [update_analytics_data] Attempting to update history for '{ig_username}'")
    analytics_file_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"

    try:
        # 1. Read existing data
        try:
            with open(analytics_file_path, "r") as f:
                analytics_data = json.load(f)
                logger.info(
                    f"---> [update_analytics_data] Read existing data from {analytics_file_path}")
        except FileNotFoundError:
            logger.warning(
                f"---> [update_analytics_data] {analytics_file_path} not found. Creating new structure.")
            # Create base structure if file doesn't exist
            analytics_data = {"global_metrics": {}, "conversations": {}}
        except json.JSONDecodeError:
            logger.error(
                f"---> [update_analytics_data] Error decoding {analytics_file_path}. Cannot update.")
            return  # Exit if file is corrupt

        # 2. Find the user within 'conversations'
        conversations_data = analytics_data.get('conversations', {})
        if not isinstance(conversations_data, dict):
            logger.error(
                "---> [update_analytics_data] 'conversations' key is not a dictionary. Resetting.")
            conversations_data = {}
            analytics_data['conversations'] = conversations_data

        target_user_id = None
        target_user_data = None
        search_ig_username_lower = ig_username.strip().lower()

        for user_id, user_data in conversations_data.items():
            if isinstance(user_data, dict):
                metrics_data = user_data.get("metrics", {})
                if isinstance(metrics_data, dict):
                    json_ig_username = metrics_data.get("ig_username", None)
                    if isinstance(json_ig_username, str) and json_ig_username.strip().lower() == search_ig_username_lower:
                        target_user_id = user_id
                        target_user_data = user_data  # We need the whole user_data to modify
                        logger.info(
                            f"---> [update_analytics_data] Found user '{ig_username}' with ID '{target_user_id}'")
                        break

        # 3. Update conversation history (if user found)
        if target_user_id and target_user_data:
            # Ensure 'metrics' and 'conversation_history' structure exists
            if "metrics" not in target_user_data or not isinstance(target_user_data["metrics"], dict):
                target_user_data["metrics"] = {}
                logger.warning(
                    f"---> [update_analytics_data] Created missing 'metrics' dict for user {target_user_id}")
            metrics_dict = target_user_data["metrics"]
            # Save IG username in metrics for lookup
            metrics_dict["ig_username"] = ig_username
            if "conversation_history" not in metrics_dict or not isinstance(metrics_dict["conversation_history"], list):
                metrics_dict["conversation_history"] = []
                logger.warning(
                    f"---> [update_analytics_data] Created missing 'conversation_history' list for user {target_user_id}")

            history_list = metrics_dict["conversation_history"]

            # Get current timestamp in ISO format (UTC)
            current_timestamp_iso = datetime.now(timezone.utc).isoformat()

            # Append user message
            if user_message:
                history_list.append({
                    "timestamp": current_timestamp_iso,
                    "type": "user",
                    "text": user_message
                })
                logger.info(
                    "---> [update_analytics_data] Appended user message to history.")

            # Set first_message_timestamp if not set
            metrics = target_user_data["metrics"]
            if not metrics.get("first_message_timestamp"):
                metrics["first_message_timestamp"] = current_timestamp_iso
                logger.info(
                    "---> [update_analytics_data] Set first_message_timestamp to current time.")

            # Append AI response
            if ai_response:
                history_list.append({
                    "timestamp": current_timestamp_iso,  # Use same timestamp for related pair
                    "type": "ai",
                    "text": ai_response
                })
                logger.info(
                    "---> [update_analytics_data] Appended AI response to history.")

            # Always update last_message_timestamp to current time
            metrics["last_message_timestamp"] = current_timestamp_iso
            logger.info(
                "---> [update_analytics_data] Updated last_message_timestamp to current time.")

            # Update the data in the main structure
            conversations_data[target_user_id] = target_user_data

        else:
            logger.warning(
                f"---> [update_analytics_data] User '{ig_username}' not found in {analytics_file_path}. Cannot update history.")
            # Optionally, you could create a new user entry here if desired
            return  # Exit if user not found and not creating new entries

        # 4. Write the entire updated structure back to the file
        try:
            with open(analytics_file_path, "w") as f:
                # Use indent for readability
                json.dump(analytics_data, f, indent=2)
                logger.info(
                    f"---> [update_analytics_data] Successfully wrote updated data to {analytics_file_path}")
        except IOError as e:
            logger.error(
                f"---> [update_analytics_data] Error writing to {analytics_file_path}: {e}")

    except Exception as e:
        logger.error(
            f"---> [update_analytics_data] Unexpected error during update: {e}", exc_info=True)


# --- Helper Function for Media Analysis --- START ---
def transcribe_audio_with_google(audio_bytes: bytes) -> Optional[str]:
    """
    Transcribe audio using Google Cloud Speech-to-Text with FFmpeg conversion
    """
    if not AUDIO_PROCESSING_AVAILABLE:
        logger.warning(
            "Audio processing is not available - cannot transcribe audio")
        return "Audio message received (transcription not available)"

    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_mp4, \
                tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:

            # Write the MP4 data to temp file
            temp_mp4.write(audio_bytes)
            temp_mp4.flush()

            # Convert audio to WAV format using ffmpeg
            ffmpeg_cmd = [
                FFMPEG_PATH,
                "-i", temp_mp4.name,
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-y",
                temp_wav.name
            ]

            try:
                result = subprocess.run(
                    ffmpeg_cmd, check=True, capture_output=True, text=True)
                logger.info(f"FFmpeg conversion successful: {result.stdout}")
            except subprocess.CalledProcessError as e:
                logger.error(f"FFmpeg conversion failed: {e.stderr}")
                return None

            # Initialize Speech client
            client = speech_v1.SpeechClient()

            # Read the WAV audio file
            with open(temp_wav.name, "rb") as audio_file:
                content = audio_file.read()

            audio = speech_v1.RecognitionAudio(content=content)
            config = speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-AU",
                enable_automatic_punctuation=True,
                model="phone_call",
                use_enhanced=True,
                audio_channel_count=1,
                enable_word_confidence=True,
                speech_contexts=[{
                    "phrases": [
                        "hey", "hello", "morning", "afternoon", "evening",
                        "training", "workout", "exercise", "gym", "fitness", "program"
                    ],
                    "boost": 20.0
                }]
            )

            response = client.recognize(config=config, audio=audio)

            if response.results:
                transcription = response.results[0].alternatives[0].transcript
                logger.info(f"Successfully transcribed audio: {transcription}")
                return transcription
            else:
                logger.warning("No transcription results received")
                return None

    except Exception as e:
        logger.error(f"Error in audio transcription: {e}", exc_info=True)
        return None
    finally:
        try:
            os.unlink(temp_mp4.name)
            os.unlink(temp_wav.name)
        except Exception as cleanup_e:
            logger.warning(f"Error cleaning up temp files: {cleanup_e}")


def analyze_media_url(media_url: str) -> tuple[Optional[str], Optional[str]]:
    """
    Downloads and processes media content, prioritizing video analysis for video files.
    """
    if not media_url:
        return None, None

    try:
        response = requests.get(media_url, stream=True, timeout=15)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()
        media_bytes = response.content
        logger.info(
            f"Successfully downloaded media data ({len(media_bytes)} bytes) of type {content_type}.")

        media_type = None
        prompt_text = None
        transcription = None

        # --- Image Handling ---
        if content_type.startswith('image/'):
            media_type = 'image'
            prompt_text = "Describe this image briefly, focusing on the main subject and action."
            if PIL_AVAILABLE:
                try:
                    img = Image.open(io.BytesIO(media_bytes))
                    img.verify()
                    logger.info("PIL verification successful for image.")
                except Exception as pil_e:
                    logger.error(
                        f"PIL verification failed for image data: {pil_e}", exc_info=True)
                    return None, None

        # --- Video Handling ---
        elif content_type == 'video/mp4':
            media_type = 'video'
            logger.info("Processing as video content")
            # Attempt to transcribe audio regardless of size
            try:
                transcription = transcribe_audio_with_google(media_bytes)
                if transcription:
                    logger.info(
                        f"Successfully transcribed audio from video: {transcription}")
                else:
                    logger.info("Could not transcribe audio from video.")
            except Exception as audio_e:
                logger.error(
                    f"Error during audio transcription attempt for video: {audio_e}", exc_info=True)

            # First, try to detect if this is an exercise video
            exercise_detection_prompt = """This is a video clip. Please analyze it and determine if it shows someone performing an exercise or workout. If it does:
            1. Identify the specific exercise being performed
            2. Note the number of repetitions visible (if applicable)
            3. Describe the overall form and technique shown

            If it's not an exercise video, just say "Not an exercise video" and describe the general content instead."""

            # Try exercise detection first with main model
            try:
                exercise_detection_model = genai.GenerativeModel(
                    GEMINI_MODEL_PRO)
                exercise_detection_contents = [
                    {
                        "parts": [
                            {"text": exercise_detection_prompt},
                            {"inline_data": {
                                "mime_type": content_type, "data": media_bytes}}
                        ]
                    }
                ]

                exercise_detection_response = exercise_detection_model.generate_content(
                    exercise_detection_contents)
                exercise_analysis = exercise_detection_response.text.strip()

                # If it's an exercise video, use a detailed technique analysis prompt
                if "Not an exercise video" not in exercise_analysis:
                    prompt_text = """This is an exercise video. Please provide a detailed analysis including:
                    1. Exercise Identification: What exercise is being performed?
                    2. Form Analysis: Describe the technique and form shown in detail
                    3. Key Points: List the main technical aspects being demonstrated correctly or incorrectly
                    4. Safety Concerns: Note any potential safety issues or form corrections needed
                    5. Recommendations: Provide specific suggestions for improvement if needed

                    Format the response in clear sections for readability."""
                else:
                    # Use standard video analysis prompt for non-exercise videos
                    prompt_text = """This is a video clip. Please:
                    1. Describe the main visual elements and actions
                    2. Note any text or captions visible
                    3. If audio is present, briefly describe its nature (e.g., speech, music, background noise)"""

            except Exception as e:
                logger.error(
                    f"Error during exercise detection with main model: {e}")
                # If main model fails, try flash model with exercise-focused prompt
                try:
                    logger.info(
                        "Attempting exercise analysis with flash model...")
                    model = genai.GenerativeModel(GEMINI_MODEL_FLASH)
                    exercise_focused_prompt = """As a professional strength coach, analyze this exercise video clip in detail. Focus on:

1. Exercise Details:
- What exercise is being performed?
- Any specific variation or style?
- How many reps are shown?

2. Technical Analysis:
- Starting position and setup
- Movement execution quality
- Range of motion and depth
- Body positioning and alignment

3. Key Observations:
- What's being done well
- Areas needing improvement
- Safety considerations
- Quick form tips

If this isn't an exercise video, simply describe what you see."""

                    flash_contents = [
                        {
                            "parts": [
                                {"text": exercise_focused_prompt},
                                {"inline_data": {
                                    "mime_type": content_type, "data": media_bytes}}
                            ]
                        }
                    ]
                    flash_response = model.generate_content(flash_contents)
                    flash_analysis = flash_response.text.strip()

                    # Check if flash model detected exercise content
                    if any(exercise_term in flash_analysis.lower() for exercise_term in ['exercise', 'form', 'technique', 'deadlift', 'squat', 'bench', 'workout', 'rep', 'position', 'movement']):
                        prompt_text = """Provide a detailed exercise technique analysis including:
                        1. Exercise name and setup details
                        2. Movement execution quality
                        3. Specific form points observed
                        4. Safety considerations
                        5. Improvement suggestions"""
                    else:
                        # Fall back to standard video prompt
                        prompt_text = """This is a video clip. Please:
                        1. Describe the main visual elements and actions
                        2. Note any text or captions visible
                        3. If audio is present, briefly describe its nature"""

                except Exception as flash_e:
                    logger.error(f"Flash model also failed: {flash_e}")
                    # Ultimate fallback - use simple prompt
                    prompt_text = "Please describe what you see in this video, focusing on any exercise or movement technique if present."

        # --- Audio Handling ---
        elif content_type.startswith('audio/'):
            media_type = 'audio'
            logger.info("Processing as audio content")
            # Try Google Speech-to-Text first
            transcription = transcribe_audio_with_google(media_bytes)
            if transcription:
                # Return only transcription for pure audio
                return 'audio', transcription
            else:
                # Fall back to Gemini if transcription fails
                logger.warning(
                    "Speech-to-Text failed for audio, falling back to Gemini audio analysis...")
                prompt_text = "This is an audio file. Please describe any indicators of audio content you can detect."

        else:
            logger.warning(f"Unrecognized content type: {content_type}")
            return None, None

        # --- Gemini Analysis (for image, video, or failed audio transcription) ---
        if not prompt_text:
            logger.error(
                f"No prompt text generated for media type {media_type}. This shouldn't happen.")
            return media_type, "Error: Could not generate analysis prompt."

        media_part = {
            "mime_type": content_type,
            "data": media_bytes
        }

        # Combine prompt and media for Gemini
        gemini_contents = [
            {
                "parts": [
                    {"text": prompt_text},
                    {"inline_data": media_part}
                ]
            }
        ]

        # Call Gemini with retry logic
        gemini_description = None
        try:
            # Try main model first
            model = genai.GenerativeModel(GEMINI_MODEL_PRO)
            response = model.generate_content(contents=gemini_contents)
            gemini_description = response.text.strip()
            logger.info(f"Successfully processed {media_type} with main model")
        except Exception as e:
            logger.warning(
                f"Main model failed for {media_type}: {e}. Trying flash model...")
            try:
                # Try flash model
                model = genai.GenerativeModel(GEMINI_MODEL_FLASH)
                simple_prompt = f"Briefly describe this {media_type} content."
                # Update prompt
                gemini_contents[0]['parts'][0]['text'] = simple_prompt
                response = model.generate_content(contents=gemini_contents)
                gemini_description = response.text.strip()
                logger.info(
                    f"Successfully processed {media_type} with flash model")
            except Exception as e2:
                logger.error(
                    f"All models failed to process {media_type}: {e2}")
                gemini_description = "Analysis failed."

        # --- Combine results for Video ---
        if media_type == 'video':
            final_result = f"Video Content: {gemini_description if gemini_description else 'Visual analysis failed.'}"
            if transcription:
                final_result += f" (Audio transcription: {transcription})"
            return media_type, final_result

        # --- Return results for Image or failed Audio ---
        else:
            return media_type, gemini_description

    except requests.exceptions.RequestException as req_e:
        logger.error(
            f"Failed to download media from {media_url[:100]}: {req_e}", exc_info=True)
        return None, None
    except Exception as e:
        logger.error(
            f"Unexpected error during media analysis: {e}", exc_info=True)
        return None, None

# --- Helper Function to Process Conversation for Media --- START ---


def process_conversation_for_media(conversation_text: str) -> str:
    """
    Detects media URLs in conversation text, analyzes them, and replaces URLs with descriptions.
    """
    if not conversation_text:
        return ""

    url_pattern = r"(https?://lookaside\.fbsbx\.com/ig_messaging_cdn/\?asset_id=[\w-]+&signature=[\w\-_.~]+)"
    processed_text = conversation_text
    urls_found = list(re.finditer(url_pattern, conversation_text))

    if not urls_found:
        logger.info("No media URLs found in conversation text.")
        return conversation_text

    logger.info(
        f"Found {len(urls_found)} potential media URLs in conversation.")
    for match in urls_found:
        url = match.group(1)
        logger.info(f"Processing URL found: {url[:100]}...")
        media_type, result_text = analyze_media_url(url)

        if media_type and result_text:
            if media_type == 'image':
                replacement_text = f"(Sent a photo: {result_text})"
            elif media_type == 'audio':
                # This case should now only happen for pure audio files where transcription succeeded
                replacement_text = f"(Voice message: {result_text})"
            elif media_type == 'video':
                # Result_text for video now includes both visual description and transcription if available
                replacement_text = f"(Sent a video: {result_text})"
            else:
                # Fallback for unexpected types or Gemini audio description
                replacement_text = f"({media_type}: {result_text})"

            logger.info(
                f"Replacing URL with {media_type} description: {replacement_text[:100]}...")
        else:
            replacement_text = f"(Sent {media_type if media_type else 'media'}, but analysis failed)"
            logger.warning(f"Using generic placeholder for {url[:100]}")

        processed_text = processed_text.replace(url, replacement_text, 1)

    logger.info("Finished processing conversation text for media.")
    return processed_text
# --- Helper Function to Process Conversation for Media --- END ---

# --- Instagram Webhook Verification --- START ---


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
                    sender_id), full_message, response_text)
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

        # Check for media URLs in the message and process them
        url_pattern = r"(https?://lookaside\.fbsbx\.com/ig_messaging_cdn/\?asset_id=[\w-]+&signature=[\w\-_.~]+)"
        urls_found = list(re.finditer(url_pattern, combined_text))

        processed_message = combined_text
        if urls_found:
            logger.info(f"Found {len(urls_found)} media URLs in message")
            for match in urls_found:
                url = match.group(1)
                media_type, result_text = analyze_media_url(url)
                if result_text:
                    # Extract transcription from result text if it contains it
                    if "Audio transcription:" in result_text:
                        processed_message = result_text.split("Audio transcription:")[
                            1].strip().rstrip(")")
                        logger.info(
                            f"Extracted audio transcription: {processed_message}")
                    else:
                        processed_message = result_text
                        logger.info(
                            f"Using media analysis result: {processed_message}")

        # Get subscriber_id from payload
        subscriber_id = payload.get('id')
        if not subscriber_id:
            logger.error(
                f"No subscriber_id found in payload for {ig_username}")
            return

        # First try action detection
        action_handled = await detect_and_handle_action(ig_username, processed_message, payload)

        if not action_handled:
            try:
                # Get user data and build chat prompt
                user_data = get_user_data(ig_username)
                if not user_data:
                    logger.error(f"No user data found for {ig_username}")
                    return

                # Unpack the user data tuple
                current_stage, metrics_dict, conversation_topics, bio, last_response_time, trial_status, interests = user_data

                # Format the full conversation history
                conversation_history = metrics_dict.get(
                    'conversation_history', [])
                formatted_history = format_conversation_history(
                    conversation_history)

                # Add current message to history
                full_conversation = f"{formatted_history}\nLead: {processed_message}" if formatted_history else processed_message

                logger.info(
                    f"Formatted {len(conversation_history)} messages for Gemini prompt")

                # Format the prompt using the template from prompts.py
                prompt = prompts.GENERAL_CHAT_PROMPT_TEMPLATE.format(
                    current_stage=current_stage,
                    trial_status=trial_status,
                    ig_username=ig_username,
                    bio=bio,
                    interests=interests,
                    topics_str="\n".join(
                        conversation_topics) if conversation_topics else "No topics yet",
                    first_name=metrics_dict.get('first_name', ''),
                    last_name=metrics_dict.get('last_name', ''),
                    sex=metrics_dict.get('sex', ''),
                    fitness_goals=metrics_dict.get('fitness_goals', ''),
                    dietary_requirements=metrics_dict.get(
                        'dietary_requirements', ''),
                    training_frequency=metrics_dict.get(
                        'training_frequency', ''),
                    current_melbourne_time_str=get_melbourne_time_str(),
                    full_conversation=full_conversation
                )

                # Get AI response
                response = await get_ai_response(prompt)
                if not response:
                    logger.error(f"No response generated for {ig_username}")
                    return

                # Update ManyChat fields
                field_updates = {
                    "o1 Response": response,
                    "CONVERSATION": combined_text
                }

                success = update_manychat_fields(subscriber_id, field_updates)
                if not success:
                    logger.error(
                        f"Failed to update ManyChat fields for subscriber {subscriber_id} ({ig_username})")
                else:
                    logger.info(
                        f"Successfully updated ManyChat fields for {ig_username}")

                # Update analytics
                update_analytics_data(ig_username, processed_message, response)
                logger.info(f"Updated analytics for {ig_username}")

            except Exception as e:
                logger.error(f"Error in general chat processing: {str(e)}")
                # Don't send any response if we're not sure what happened
                return

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


async def get_ai_response(prompt: str) -> Optional[str]:
    """Get AI response using Gemini models with fallbacks."""
    try:
        # First try with GEMINI_MODEL_PRO
        response = call_gemini_with_retry(GEMINI_MODEL_PRO, prompt)
        if response:
            return response

        # If that fails, try GEMINI_MODEL_FLASH
        logger.warning("Primary model failed, trying FLASH model...")
        response = call_gemini_with_retry(GEMINI_MODEL_FLASH, prompt)
        if response:
            return response

        # Last resort, try GEMINI_MODEL_FLASH_STANDARD
        logger.warning("FLASH model failed, trying FLASH_STANDARD model...")
        response = call_gemini_with_retry(GEMINI_MODEL_FLASH_STANDARD, prompt)
        if response:
            return response

        logger.error("All Gemini models failed to generate response")
        return None

    except Exception as e:
        logger.error(f"Error getting AI response: {str(e)}")
        return None


if __name__ == "__main__":
    uvicorn.run("webhook_manychat23:app",  # Use import string instead of app object
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
