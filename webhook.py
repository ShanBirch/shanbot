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
# Main model (set to fast, reliable flash-lite)
GEMINI_MODEL_PRO = "gemini-2.5-flash-lite"
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


def get_user_data(ig_username: str) -> tuple[Optional[str], Optional[Dict], list, Optional[str], float, Optional[str], Optional[str], Optional[bool], Optional[str]]:
    """
    Load user data from analytics_data_good.json with detailed logging
    Returns: (current_stage, user_data_metrics, conversation_topics,
              trial_status, last_bot_timestamp, last_bot_response, interests_json, is_in_checkin_flow, full_name, checkin_type)
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
        # --- MODIFIED: Return structure matches new definition ---
        return None, None, [], None, 0.0, None, None, False, None, None

    logger.info(f"Searching for username: '{ig_username}'")

    # Look for user in conversations
    conversations = analytics_data.get('conversations', {})
    user_data_full = None  # Store the entire user object temporarily
    user_data_metrics = None  # Store just the metrics dict

    # First try direct match in conversations
    if ig_username in conversations:
        # --- MODIFIED: Store full user data first ---
        user_data_full = conversations[ig_username]
        user_data_metrics = user_data_full.get(
            'metrics', {}) if isinstance(user_data_full, dict) else {}
        logger.info(f"Found user directly in conversations: {ig_username}")
    else:
        # If not found directly, search through all conversations
        for conv_id, conv_data in conversations.items():
            if isinstance(conv_data, dict) and 'metrics' in conv_data:
                metrics = conv_data['metrics']
                if isinstance(metrics, dict) and metrics.get('ig_username') == ig_username:
                    # --- MODIFIED: Store full user data first ---
                    user_data_full = conv_data
                    user_data_metrics = metrics
                    logger.info(
                        f"Found user data under conversation ID: {conv_id}")
                    break

    if not user_data_metrics:
        logger.warning(f"User {ig_username} not found in conversations")
        # --- MODIFIED: Return structure matches new definition ---
        return None, None, [], None, 0.0, None, None, False, None, None

    logger.info(f"\n=== USER FOUND: {ig_username} ===")
    # --- MODIFIED: Log keys from metrics dict ---
    logger.info(
        f"Available keys in user_data[metrics]: {list(user_data_metrics.keys())}")

    # Get current stage
    current_stage = "Topic 1"  # Default value
    # --- MODIFIED: Check metrics dict ---
    if "journey_stage" in user_data_metrics and isinstance(user_data_metrics["journey_stage"], dict) and "current_stage" in user_data_metrics["journey_stage"]:
        current_stage = user_data_metrics["journey_stage"]["current_stage"]
        logger.info(f"FOUND current_stage = {current_stage}")
    else:
        logger.info("NO current_stage found - defaulting to Topic 1")

    # Get bio
    bio = None
    # --- MODIFIED: Check metrics dict ---
    if "client_analysis" in user_data_metrics and isinstance(user_data_metrics["client_analysis"], dict) and "profile_bio" in user_data_metrics["client_analysis"]:
        bio = user_data_metrics["client_analysis"]["profile_bio"]
        logger.info(f"FOUND bio = {bio}")
    else:
        logger.info("NO bio found")

    # Get conversation topics
    conversation_topics = []
    # --- MODIFIED: Check metrics dict ---
    if "client_analysis" in user_data_metrics and isinstance(user_data_metrics["client_analysis"], dict) and "conversation_topics" in user_data_metrics["client_analysis"]:
        conversation_topics = user_data_metrics["client_analysis"]["conversation_topics"]
        logger.info("FOUND conversation topics:")
        for i, topic in enumerate(conversation_topics, 1):
            logger.info(f"  Topic {i}: {topic}")
    else:
        logger.info("NO conversation topics found")

    # Get interests
    interests = []
    # --- MODIFIED: Check metrics dict ---
    if "client_analysis" in user_data_metrics and isinstance(user_data_metrics["client_analysis"], dict) and "interests" in user_data_metrics["client_analysis"]:
        interests = user_data_metrics["client_analysis"]["interests"]
        logger.info("FOUND interests:")
        for i, interest in enumerate(interests, 1):
            logger.info(f"  Interest {i}: {interest}")
    else:
        logger.info("NO interests found")
    # Convert to JSON string for return
    interests_json = json.dumps(interests) if interests else None

    # Get trial status
    trial_status = None
    # --- MODIFIED: Check metrics dict ---
    if "trial_week_1" in user_data_metrics and user_data_metrics["trial_week_1"]:
        trial_status = "Trial Week 1"
        logger.info(f"FOUND trial status = {trial_status}")

    # Get conversation history
    conversation_history = []
    # --- MODIFIED: Check metrics dict ---
    if "conversation_history" in user_data_metrics:
        conversation_history = user_data_metrics["conversation_history"]
        logger.info(
            f"FOUND conversation history with {len(conversation_history)} entries")
        logger.info("Last 3 messages:")
        for msg in conversation_history[-3:]:
            logger.info(f"  {msg['type']}: {msg['text'][:100]}...")

    # Get last bot response timestamp
    last_bot_response_timestamp = None  # Changed variable name for clarity
    if conversation_history:
        for msg in reversed(conversation_history):
            if msg["type"] == "ai":
                last_bot_response_timestamp = msg["timestamp"]
                logger.info(
                    f"FOUND last bot response timestamp = {last_bot_response_timestamp}")
                break

    # --- ADDED: Get is_in_checkin_flow status --- START ---
    is_in_checkin_flow = False  # Default
    # --- MODIFIED: Check metrics dict ---
    if "is_in_checkin_flow" in user_data_metrics and isinstance(user_data_metrics["is_in_checkin_flow"], bool):
        is_in_checkin_flow = user_data_metrics["is_in_checkin_flow"]
    logger.info(f"FOUND is_in_checkin_flow = {is_in_checkin_flow}")
    # --- ADDED: Get is_in_checkin_flow status --- END ---

    # --- ADDED: Get checkin_type status --- START ---
    checkin_type = None  # Default
    # --- MODIFIED: Check metrics dict ---
    if "checkin_type" in user_data_metrics and isinstance(user_data_metrics["checkin_type"], str):
        checkin_type = user_data_metrics["checkin_type"]
    logger.info(f"FOUND checkin_type = {checkin_type}")
    # --- ADDED: Get checkin_type status --- END ---

    # --- ADDED: Get full name --- START ---
    first_name = ""
    last_name = ""
    full_name = None  # Initialize full_name

    # 1. Prioritize PERSON NAME from client_analysis.profile_bio
    try:
        profile_bio = user_data_metrics.get(
            'client_analysis', {}).get('profile_bio', {})
        if isinstance(profile_bio, dict):
            person_name_analysis = profile_bio.get("PERSON NAME")
            if isinstance(person_name_analysis, str) and person_name_analysis.strip() and person_name_analysis.strip().lower() != 'unknown':
                person_name_analysis = person_name_analysis.strip()
                name_parts = person_name_analysis.split()
                if len(name_parts) >= 1:
                    first_name = name_parts[0]
                if len(name_parts) >= 2:
                    last_name = name_parts[-1]  # Assume last part is last name
                if first_name and last_name:
                    full_name = f"{first_name} {last_name}"
                    logger.info(
                        f"Derived full name from client_analysis: {full_name}")
                else:
                    # Reset if we didn't get both parts from analysis
                    first_name = ""
                    last_name = ""
    except Exception as e:
        logger.warning(
            f"Error processing PERSON NAME from client_analysis: {e}")
        first_name = ""
        last_name = ""

    # 2. Fallback to client_details if name not found in analysis
    if not full_name:
        client_details = user_data_metrics.get('client_details', {})
        if isinstance(client_details, dict):
            first_name_details = client_details.get('first_name', '')
            last_name_details = client_details.get('last_name', '')
            if first_name_details and last_name_details:
                first_name = first_name_details
                last_name = last_name_details
                full_name = f"{first_name} {last_name}".strip()
                logger.info(
                    f"Derived full name from client_details: {full_name}")

    # 3. Fallback to top-level 'metrics' (often from ManyChat payload) if still not found
    if not full_name:
        first_name_metrics = user_data_metrics.get('first_name', '')
        last_name_metrics = user_data_metrics.get('last_name', '')
        if first_name_metrics and last_name_metrics:
            first_name = first_name_metrics
            last_name = last_name_metrics
            full_name = f"{first_name} {last_name}".strip()
            logger.info(
                f"Derived full name from top-level metrics: {full_name}")

    # 4. Final fallback to ig_username
    if not full_name:
        # Use IG username as ultimate fallback if names are empty
        full_name = ig_username
        logger.warning(
            f"Could not find first/last name for {ig_username}, using username as full name.")
    else:
        logger.info(f"Final derived full name = {full_name}")
    # --- ADDED: Get full name --- END ---

    logger.info("\n=== DATA RETRIEVAL COMPLETE ===")

    # --- MODIFIED: Return structure matches new definition ---
    return (
        current_stage,
        user_data_metrics,  # Return the metrics dict
        conversation_topics,
        trial_status,
        0.0,  # placeholder for any float value needed
        last_bot_response_timestamp,  # Return the timestamp string
        interests_json,  # Return interests as JSON string
        is_in_checkin_flow,  # Return check-in status
        full_name,  # Return full name
        checkin_type  # Return check-in type
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


def add_todo_item(ig_username: str, client_name: str, task_description: str, status: str = "pending"):
    """Adds a 'to do' or completed action item to the analytics data file."""
    analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
    log_prefix = "[add_todo_item]" if status == "pending" else "[log_completed_action]"
    logger.info(
        f"---> {log_prefix} Logging item for {ig_username}: {task_description} (Status: {status})")
    try:
        # 1. Read existing data
        try:
            with open(analytics_file_path, "r") as f:
                analytics_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.error(
                f"Could not load analytics data from {analytics_file_path} to add todo item. Initializing.")
            analytics_data = {"global_metrics": {}, "conversations": {
            }, "action_items": []}  # Initialize structure

        # 2. Ensure 'action_items' list exists
        if "action_items" not in analytics_data or not isinstance(analytics_data["action_items"], list):
            analytics_data["action_items"] = []
            logger.warning(
                "---> [add_todo_item] Initialized 'action_items' list.")

        # 3. Create and append new task
        new_task = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ig_username": ig_username,
            "client_name": client_name or ig_username,  # Use username as fallback
            "task_description": task_description,
            "status": status  # Use the provided status
        }
        analytics_data["action_items"].append(new_task)
        logger.info(f"---> {log_prefix} Appended new item.")

        # 4. Write back to file
        try:
            with open(analytics_file_path, "w") as f:
                json.dump(analytics_data, f, indent=2)
            logger.info(
                f"---> {log_prefix} Successfully saved updated analytics data.")
        except IOError as e:
            logger.error(
                f"---> {log_prefix} Error writing updated analytics data: {e}")

    except Exception as e:
        logger.error(f"---> {log_prefix} Unexpected error: {e}", exc_info=True)

# --- Helper Function to Add "To Do" Item --- END ---


async def detect_and_handle_action(ig_username: str, message_text: str, data: Dict = None) -> bool:
    """Uses Gemini to detect user intent and handles multiple actions like Trainerize edits or food analysis within one message."""
    logger.info(
        f"[detect_and_handle_action] Analyzing message from {ig_username} for multiple actions: {message_text[:100]}"
    )

    if not data:
        logger.error("No data dictionary provided to detect_and_handle_action")
        return False

    # --- NEW MULTI-ACTION PROMPT --- START ---
    intent_prompt = f"""Analyze this message to identify ALL requested actions:
1. Workout program changes (adding or removing exercises).
2. Requests for a form check/technique analysis based on a video.
3. Requests for calorie/macro analysis of food based on an image.

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

Workout Change Instructions:
- Identify every distinct workout change action requested (add, remove).
- For each action, identify the exercise name.
- For each action, identify the specific workout day mentioned or inferred. Map it to one of the Standard Workout Day Categories and use the full `output type` for 'workout_type'.
- Prioritize user-mentioned day for 'workout_type'. Infer if not mentioned.
- If adding an exercise, include default sets ('3') and reps ('10').

--- Form Check Requests ---
Form Check Keywords: form check, check form, technique, review video, analyse video, look at my lift

Form Check Instructions:
- If the user asks for a form check or technique review related to a video (using keywords above or similar phrasing), set "is_form_check_request" to true.

--- Calorie/Macro Analysis Requests ---
Food Analysis Keywords: calories, macros, check food, analyse meal, how much protein/carbs/fat, food pic

Food Analysis Instructions:
- Set "is_food_analysis_request" to true if the user uses food analysis keywords.
- Independently, check if the message text contains a plausible image URL (look for 'lookaside.fbsbx.com'). Set "has_image_url" to true if found, false otherwise.

--- Output Format ---
Respond ONLY with a JSON object. Make sure the entire response is valid JSON.
- Include "is_workout_request": true/false,
- Include "actions": [...],
- Include "is_form_check_request": true/false,
- Include "is_food_analysis_request": true/false, (based on keywords only)
- Include "has_image_url": true/false, (based on URL presence in this message)
- Include "confidence": 0-100,
- Include "explanation": "..."

Format:
{{{{  # Use double braces to escape JSON braces within f-string
    "is_workout_request": true/false,
    "actions": [
        // ... workout actions ...
    ],
    "is_form_check_request": true/false,
    "is_food_analysis_request": true/false,
    "has_image_url": true/false,
    "confidence": 0-100,
    "explanation": "brief explanation summarizing all actions/requests"
}}}}
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
        # More robust cleaning for markdown fences and optional 'json' identifier
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[len("```json"):].strip()
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[len("```"):].strip()

        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-len("```")].strip()

        # *** START Robust Parsing Logic (First/Last Brace Extraction) ***
        intent_data = None
        try:
            # Find the first '{' and the last '}'
            first_brace_index = cleaned_response.find('{')
            last_brace_index = cleaned_response.rfind('}')

            if first_brace_index != -1 and last_brace_index != -1 and last_brace_index > first_brace_index:
                # Extract the substring between the first '{' and the last '}'
                potential_json_str = cleaned_response[first_brace_index: last_brace_index + 1]
                # Log extracted block
                logger.info(
                    f"Extracted potential JSON block (first/last brace): {potential_json_str[:500]}...")
                try:
                    # Attempt to parse the extracted block
                    intent_data = json.loads(potential_json_str)
                    logger.info(
                        f"Intent analysis (parsed from first/last brace extraction): {json.dumps(intent_data, indent=2)}")
                except json.JSONDecodeError as json_err:
                    logger.error(
                        f"Failed to parse the JSON block extracted via first/last brace: {json_err}")
                    logger.error(
                        f"Original Gemini response (cleaned): {cleaned_response}")
                    logger.error(f"Extracted substring: {potential_json_str}")
                    return False  # Parsing failed
            else:
                # Could not find valid start/end braces
                logger.error(
                    "Could not find valid starting '{' and ending '}' braces in the response.")
                logger.error(
                    f"Original Gemini response (cleaned): {cleaned_response}")
                return False  # Extraction failed

        except Exception as e:
            # Catch any other unexpected errors during extraction/parsing setup
            logger.error(
                f"Unexpected error during JSON extraction/parsing setup: {e}", exc_info=True)
            logger.error(
                f"Original Gemini response (cleaned): {cleaned_response}")
            return False

        # Check if data was successfully parsed
        if not intent_data:
            logger.error(
                "Intent data is None after parsing attempt. Cannot proceed.")
            logger.error(
                f"Original Gemini response (cleaned): {cleaned_response}")
            return False
        # *** END Robust Parsing Logic ***

        # --- Extract data from analysis ---
        is_workout_req = intent_data.get('is_workout_request', False)
        is_form_check_req = intent_data.get('is_form_check_request', False)
        is_food_analysis_req = intent_data.get(
            'is_food_analysis_request', False)  # Based on keywords
        # Check if URL was in *this* message
        has_image_url = intent_data.get('has_image_url', False)
        confidence = intent_data.get('confidence', 0)
        requested_actions = intent_data.get('actions', [])
        # Get subscriber_id here for easier access
        subscriber_id = data.get('id')
        # Get names for analytics
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        # --- Handle Form Check Request (PRIORITY 1) ---
        if is_form_check_req and confidence > 70:
            logger.info(
                f"Form check request detected for {ig_username} with confidence {confidence}.")
            form_check_pending[ig_username] = True
            # Select a random response from the list
            response = random.choice(FORM_CHECK_REQUEST_RESPONSES)
            logger.info(
                f"Using dynamic response for form check request: '{response}'")
            field_updates = {
                "o1 Response": response,
                "CONVERSATION": message_text  # Original message
            }
            update_success = update_manychat_fields(
                subscriber_id, field_updates)
            if not update_success:
                logger.error(
                    f"Failed to update ManyChat fields for form check request {ig_username}")

            # Update analytics with a summary
            ai_response_for_analytics = "AI responded asking user to send video for form check."
            update_analytics_data(ig_username, message_text, ai_response_for_analytics, subscriber_id, data.get(
                # Added subscriber_id and names
                'first_name', ''), data.get('last_name', ''))
            logger.info(
                f"Updated analytics data for {ig_username} after form check request.")
            return True  # Form check intent handled

        # --- Handle Food Analysis Request (PRIORITY 2) --- Added Block ---
        elif is_food_analysis_req and confidence > 70:
            logger.info(
                f"Food analysis request detected for {ig_username} with confidence {confidence}.")

            # Client name for potential ToDo item
            client_name_for_todo = data.get(
                'name') or f"{first_name} {last_name}".strip() or ig_username

            # Check if the image URL was provided in this specific message according to intent analysis
            if has_image_url:
                # Extract image URL from message_text (Gemini confirmed it's there)
                url_pattern = r"(https?://lookaside\.fbsbx\.com/ig_messaging_cdn/\?asset_id=[\w-]+&signature=[\w\-_.~]+)"
                match = re.search(url_pattern, message_text)
                if match:
                    image_url = match.group(1)
                    logger.info(
                        f"Found image URL for food analysis: {image_url[:100]}...")

                    # Extract the user description (text part of the combined message)
                    user_desc_text = message_text.replace(
                        image_url, "").strip()

                    # Call the calorie analysis function, passing the description
                    # Parse the raw analysis to extract numbers
                    analysis_result = raw_analysis  # Default if parsing fails
                    remaining_message = None
                    combined_response = raw_analysis  # Default for analytics
                    # Default field updates (only o1 Response)
                    field_updates = {
                        "o1 Response": analysis_result,
                        "CONVERSATION": f"(User sent image for calorie check: {image_url[:50]}...)"
                    }

                    try:
                        logger.info(f"Raw analysis to parse: {raw_analysis}")
                        # Extract numbers using regex (more flexible patterns)
                        calories_match = re.search(
                            r'Calories\s*=?\s*(\d+)', raw_analysis, re.IGNORECASE)
                        protein_match = re.search(
                            r'Protein\s*=?\s*(\d+)', raw_analysis, re.IGNORECASE)
                        carbs_match = re.search(
                            r'(?:Carbs?|Carbohydrates?)\s*=?\s*(\d+)', raw_analysis, re.IGNORECASE)
                        fats_match = re.search(
                            r'Fats?\s*=?\s*(\d+)', raw_analysis, re.IGNORECASE)

                        # Log what we found
                        logger.info(f"Regex matches - Calories: {calories_match.group(1) if calories_match else 'None'}, "
                                    f"Protein: {protein_match.group(1) if protein_match else 'None'}, "
                                    f"Carbs: {carbs_match.group(1) if carbs_match else 'None'}, "
                                    f"Fats: {fats_match.group(1) if fats_match else 'None'}")

                        if all([calories_match, protein_match, carbs_match, fats_match]):
                            # If parsing succeeds, proceed with tracking and formatting
                            calories = int(calories_match.group(1))
                            protein = int(protein_match.group(1))
                            carbs = int(carbs_match.group(1))
                            fats = int(fats_match.group(1))

                            logger.info(f"Successfully parsed values - Calories: {calories}, "
                                        f"Protein: {protein}g, Carbs: {carbs}g, Fats: {fats}g")

                            # Keep the raw analysis for the first message
                            analysis_result = raw_analysis

                            # Update tracking with new meal
                            update_calorie_tracking(
                                ig_username, calories, protein, carbs, fats)

                            # Get current remaining values for second message
                            remaining = get_current_remaining_macros(
                                ig_username)

                            # Second message - Current remaining calories/macros for the day
                            if remaining:
                                remaining_message = (
                                    f"Your remaining macros for today:\n"
                                    f"Calories: {remaining['remaining_calories']}kcal\n"
                                    f"Protein: {remaining['remaining_protein']}g\n"
                                    f"Carbs: {remaining['remaining_carbs']}g\n"
                                    f"Fats: {remaining['remaining_fats']}g"
                                )
                            else:
                                remaining_message = "Could not retrieve remaining macros."

                            logger.info(
                                f"Analysis result (o1): {analysis_result}")
                            logger.info(
                                f"Remaining message (o2): {remaining_message}")

                            # **** IMPORTANT: Define field_updates HERE when successful ****
                            field_updates = {
                                "o1 Response": analysis_result,
                                "o1 Response 2": remaining_message,  # Include o1 Response 2
                                "CONVERSATION": f"(User sent image for calorie check: {image_url[:50]}...)"
                            }
                            # Set combined response for analytics
                            combined_response = f"{analysis_result}\n\n{remaining_message}"

                        else:
                            # Parsing failed, keep the default field_updates (only o1 Response)
                            logger.error(
                                f"Failed to parse all values from analysis: {raw_analysis}")
                            # analysis_result, remaining_message, combined_response, field_updates remain as their defaults

                    except Exception as e:
                        logger.error(
                            f"Error during food analysis parsing/tracking: {e}", exc_info=True)
                        logger.error(
                            f"Raw analysis that failed: {raw_analysis}")
                        # Keep default field_updates, analysis_result, combined_response on error
                        remaining_message = None  # Ensure this is None on error

                    # ***** Send updates to ManyChat OUTSIDE the try/except *****
                    # This ensures we always send *something*, even if it's just the raw analysis on error
                    update_success = update_manychat_fields(
                        subscriber_id, field_updates)
                    if not update_success:
                        logger.error(
                            f"Failed to update ManyChat fields for {ig_username}")

                    # ***** Update analytics OUTSIDE the try/except *****
                    # Use combined_response which defaults to raw_analysis if parsing failed
                    update_analytics_data(
                        ig_username,
                        f"(Sent food image: {image_url[:50]}...)",
                        combined_response,
                        subscriber_id,
                        first_name,
                        last_name
                    )

                else:
                    # This case should be rare if has_image_url was true, but handle it.
                    logger.error(
                        f"Intent analysis indicated image URL present for {ig_username}, but regex failed to find it in: '{message_text}'")
                    response_text = "Hmm, thought I saw a picture link but couldn't grab it. Can you try sending the food pic again?"
                    field_updates = {
                        "o1 Response": response_text, "CONVERSATION": message_text}
                    ai_response_for_analytics = "AI failed to extract detected image URL."
                    user_message_for_analytics = message_text

            else:
                # No image URL provided in this message, ask for it.
                logger.info(
                    f"Food analysis request for {ig_username} detected without image URL. Asking user to send photo.")
                response_text = "Yep send the photo through, and a brief description of the ingredients used will help as well"
                # SET THE STATE HERE
                food_analysis_pending[ig_username] = True
                logger.info(
                    f"Set food_analysis_pending state for {ig_username}")

                field_updates = {
                    "o1 Response": response_text,
                    "CONVERSATION": message_text  # Keep original request text
                }
                ai_response_for_analytics = "AI asked user to send food photo and ingredients."
                user_message_for_analytics = message_text

            # Send response (either analysis or request for photo) and update analytics
            update_success = update_manychat_fields(
                subscriber_id, field_updates)
            if not update_success:
                logger.error(
                    f"Failed to update ManyChat fields for food analysis flow for {ig_username}")

            update_analytics_data(
                ig_username, user_message_for_analytics, ai_response_for_analytics, subscriber_id, first_name, last_name)
            logger.info(
                f"Updated analytics for {ig_username} during food analysis flow.")
            # Food analysis request handled (either by analysing or asking for image)
            return True

        # --- Handle Workout Modification Request (PRIORITY 3 - bumped down) ---
        # Check if it's a workout request and confidence is high
        elif is_workout_req and confidence > 70:
            # requested_actions = intent_data.get('actions', []) # Already extracted above
            if not requested_actions:
                logger.warning(
                    "Workout request detected, but no actions found in the list.")
                return False  # Not handled if list is empty

            # --- Check if essential info is present for *at least one* action ---
            # We proceed if we have enough info to attempt *something*, even if later actions lack detail.
            can_proceed = False
            target_workout_type = None
            for action_item in requested_actions:
                # *** MODIFIED: Check Gemini's action_type vs action vs type ***
                action = action_item.get('action') or action_item.get(
                    # Check all three keys
                    'action_type') or action_item.get('type')
                # *** ADDED: Check Gemini's exercise vs exercise_name ***
                exercise = action_item.get('exercise_name') or action_item.get(
                    'exercise')  # Check both keys
                if action_item.get('workout_type') and exercise and action:
                    # *** END MODIFICATION ***
                    can_proceed = True
                    # Use workout type from the first valid action for navigation
                    target_workout_type = action_item.get('workout_type')
                    break

            if not can_proceed:
                logger.warning(
                    # *** MODIFIED: Update warning message ***
                    "Detected workout request, but missing essential details (workout_type, exercise_name/exercise, or action/action_type/type) for all actions.")
                # --- ADDED: Ask for Clarification --- START ---
                clarification_message = ("I think you want to change your workout, but I missed some details. "
                                         "Can you please tell me the specific exercise, the action (add/remove), "
                                         "and the workout day (e.g., Legs, Back)?")

                # Prepare for ManyChat update
                subscriber_id_for_clarification = data.get('id')
                first_name_for_clarification = data.get('first_name', '')
                last_name_for_clarification = data.get('last_name', '')

                if subscriber_id_for_clarification:
                    field_updates = {
                        "o1 Response": clarification_message,
                        "CONVERSATION": message_text  # Keep original message in CONVERSATION for context
                    }
                    update_success = update_manychat_fields(
                        subscriber_id_for_clarification, field_updates)
                    if not update_success:
                        logger.error(
                            f"Failed to send clarification request to ManyChat for {ig_username}")

                    # Update analytics
                    update_analytics_data(ig_username,
                                          user_message=message_text,
                                          ai_response=clarification_message,
                                          subscriber_id=subscriber_id_for_clarification,
                                          first_name=first_name_for_clarification,
                                          last_name=last_name_for_clarification)
                    logger.info(
                        f"Sent clarification request and updated analytics for {ig_username}.")
                    return True  # Indicate that the clarification action was handled
                else:
                    logger.error(
                        f"Cannot send clarification request for {ig_username}, missing subscriber_id.")
                    return False  # Fallback if we can't even send the request
                # --- ADDED: Ask for Clarification --- END ---
                # TODO: Potentially ask for clarification here instead of returning False - DONE
                # For now, if the initial analysis didn't get enough, we won't proceed.
                # Construct a generic "need more info" response?
                # Example: response = "I see you want to change your workout, but I need a bit more detail. Can you tell me the specific exercise, the action (add/remove), and which workout day?"
                # update_manychat_fields(...) and return True?
                # return False # Original line - REMOVED

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
                    # *** MODIFIED: Check Gemini's action_type vs action vs type ***
                    action_type = action_item.get('action') or action_item.get(
                        # Check all three keys
                        'action_type') or action_item.get('type')
                    # *** END MODIFICATION ***
                    # *** ADDED: Check Gemini's exercise vs exercise_name ***
                    exercise_name = action_item.get('exercise_name') or action_item.get(
                        'exercise')  # Check both keys
                    # *** END MODIFICATION ***
                    # Ensure workout_type matches the one we navigated to, or log a warning?
                    # For simplicity, we assume all actions in one message are for the same workout day found initially.
                    current_workout_type = action_item.get('workout_type')
                    if current_workout_type != target_workout_type:
                        logger.warning(
                            f"Action {i+1} workout type '{current_workout_type}' differs from navigated type '{target_workout_type}'. Proceeding anyway.")

                    if not action_type or not exercise_name:
                        logger.warning(
                            f"Skipping invalid action item {i+1}: Missing action/action_type or exercise_name/exercise. Details: {action_item}")
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
                            # *** MODIFIED: Use the extracted exercise_name variable ***
                            if trainerize.add_exercise(exercise_name, sets, reps):
                                action_successful_this_time = True
                                logger.info(
                                    f"Action {i+1} SUCCEEDED: Added '{exercise_name}'")
                            else:
                                logger.error(
                                    f"Action {i+1} FAILED: Could not add '{exercise_name}'")
                        elif action_type == 'remove':
                            # *** MODIFIED: Use the extracted exercise_name variable ***
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
                            # *** MODIFIED: Use the extracted exercise_name variable ***
                            f"Action {i+1} ({action_type} '{exercise_name}') FAILED with exception: {loop_e}")
                        # Continue to the next action even if one fails

                    # Record result
                    if action_successful_this_time:
                        action_summary["success"].append(
                            # *** MODIFIED: Use the extracted exercise_name variable ***
                            f"{action_type} {exercise_name}")
                    else:
                        action_summary["failed"].append(
                            # *** MODIFIED: Use the extracted exercise_name variable ***
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
                error_message = f"Error during Trainerize automation: {str(e)}"
                logger.error(error_message)
                # *** ADD TODO ITEM FOR OVERALL FAILURE ***
                # Log truncated error
                add_todo_item(ig_username, client_full_name,
                              f"Trainerize automation failed: {str(e)[:100]}...")
                # *** END ADD TODO ***

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
                        # *** ADD TODO ITEM FOR PARTIAL/SAVE FAILURE ***
                        fail_reason = "Save workout failed" if not overall_success else f"Action(s) failed: {action_summary['failed']}"
                        add_todo_item(ig_username, client_full_name,
                                      f"Trainerize issue: {fail_reason}")
                        # *** END ADD TODO ***
                        print(
                            "\n*** Trainerize browser window left open due to error or failed save. Please close it manually. ***\n")
                        # No cleanup called here deliberately

            # --- Construct Final Response --- #
            # Simplified response logic based on overall success and any failures
            if overall_success and not action_summary["failed"]:
                # All actions succeeded and saved
                response = "Easy updated your program, need anything else?"
                # *** ADD COMPLETED ITEM FOR SUCCESSFUL TRAINERIZE ACTION ***
                success_desc = f"Successfully performed Trainerize actions: {action_summary['success']}"
                add_todo_item(ig_username, client_full_name,
                              success_desc, status="completed")
                # *** END ADD COMPLETED ***
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
                                  ai_response_for_analytics,
                                  subscriber_id, first_name, last_name)  # Pass names
            logger.info(
                f"Updated analytics data for {ig_username} with action summary.")

            return True  # Indicate action was handled (or attempted)

        else:
            # Not a workout request or low confidence
            logger.info(
                "Message not identified as a confident workout modification request.")
            return False

    # Removed the specific JSONDecodeError catch here as it's handled by the robust parsing logic above

    except Exception as e:
        # Added exc_info
        logger.error(
            f"Error in detect_and_handle_action: {str(e)}", exc_info=True)
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


def update_analytics_data(
    ig_username: str,
    user_message: str,
    ai_response: str,
    subscriber_id: str,
    first_name: str,
    last_name: str,
    set_checkin_flow_false: Optional[bool] = None  # Added optional parameter
):
    """
    Reads analytics_data_good.json, updates conversation history,
    and creates a new user entry if the user doesn't exist. Optionally resets check-in flag.
    Writes back the changes.
    """
    logger.info(
        f"---> [update_analytics_data] Attempting to update/create history for '{ig_username}' (ID: {subscriber_id})")
    analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"

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

        # 3. Create new user if not found, otherwise update history
        current_timestamp_iso = datetime.now(timezone.utc).isoformat()

        if not target_user_id:
            # --- CREATE NEW USER ---
            logger.info(
                f"---> [update_analytics_data] User '{ig_username}' not found. Creating new profile.")
            new_user_key = subscriber_id  # Use ManyChat subscriber ID as the unique key
            new_user_data = {
                "metrics": {
                    "ig_username": ig_username,
                    # Basic info from ManyChat payload
                    "first_name": first_name,
                    "last_name": last_name,
                    # Initialize history (will be populated right after creation)
                    "conversation_history": [],
                    # Default values for other fields
                    "journey_stage": {"current_stage": "Topic 1"},
                    "client_analysis": {
                        "profile_bio": "",
                        "interests": [],
                        "conversation_topics": []
                    },
                    "client_details": {
                        "first_name": first_name,
                        "last_name": last_name,
                        "sex": "",
                        "fitness_goals": "",
                        "dietary_requirements": "",
                        "training_frequency": ""
                    },
                    "trial_week_1": False,  # Default trial status
                    "is_in_checkin_flow": False,
                    # --- ADDED: Calorie and Macro Tracking Structure ---
                    "calorie_tracking": {
                        "daily_target": 2000,  # Standard default
                        "current_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "calories_consumed": 0,
                        "remaining_calories": 2000,
                        "macros": {
                            "protein": {
                                # Standard default (in grams)
                                "daily_target": 180,
                                "consumed": 0,
                                "remaining": 180
                            },
                            "carbs": {
                                # Standard default (in grams)
                                "daily_target": 250,
                                "consumed": 0,
                                "remaining": 250
                            },
                            "fats": {
                                # Standard default (in grams)
                                "daily_target": 65,
                                "consumed": 0,
                                "remaining": 65
                            }
                        },
                        "meals_today": []  # Array to store today's meals
                    },
                    # --- END ADDED ---
                    "first_message_timestamp": current_timestamp_iso,  # Set on creation
                    # Set on creation (will be updated below too)
                    "last_message_timestamp": current_timestamp_iso
                }
            }
            # Add the new user data to the conversations
            conversations_data[new_user_key] = new_user_data
            target_user_id = new_user_key
            target_user_data = new_user_data
            logger.info(
                f"---> [update_analytics_data] Created new user profile for '{ig_username}' with ID '{target_user_id}'")
            # --- END CREATE NEW USER ---

        # Ensure 'metrics' and 'conversation_history' structure exists (important for existing users too)
        if "metrics" not in target_user_data or not isinstance(target_user_data["metrics"], dict):
            target_user_data["metrics"] = {}
            logger.warning(
                f"---> [update_analytics_data] Created missing 'metrics' dict for user {target_user_id}")
        metrics_dict = target_user_data["metrics"]
        # Save/Ensure IG username in metrics for lookup resilience
        metrics_dict["ig_username"] = ig_username
        if "conversation_history" not in metrics_dict or not isinstance(metrics_dict["conversation_history"], list):
            metrics_dict["conversation_history"] = []
            logger.warning(
                f"---> [update_analytics_data] Created missing 'conversation_history' list for user {target_user_id}")

        history_list = metrics_dict["conversation_history"]

        # Append user message
        if user_message:
            history_list.append({
                "timestamp": current_timestamp_iso,
                "type": "user",
                "text": user_message
            })
            logger.info(
                f"---> [update_analytics_data] Appended user message to history for {target_user_id}.")

        # Append AI response
        if ai_response:
            history_list.append({
                "timestamp": current_timestamp_iso,  # Use same timestamp for related pair
                "type": "ai",
                "text": ai_response
            })
            logger.info(
                f"---> [update_analytics_data] Appended AI response to history for {target_user_id}.")

        # Ensure first_message_timestamp is set (for older records or if creation logic changes)
        if not metrics_dict.get("first_message_timestamp"):
            metrics_dict["first_message_timestamp"] = current_timestamp_iso
            logger.info(
                "---> [update_analytics_data] Set first_message_timestamp.")

        # Always update last_message_timestamp to current time
        metrics_dict["last_message_timestamp"] = current_timestamp_iso
        logger.info(
            f"---> [update_analytics_data] Updated last_message_timestamp for {target_user_id}.")

        # Update the data in the main structure (important!)
        analytics_data['conversations'][target_user_id] = target_user_data

        # --- ADDED: Logic to reset check-in flag --- START ---
        if set_checkin_flow_false is True:
            user_metrics_to_update = analytics_data['conversations'][target_user_id].get(
                'metrics', {})
            if isinstance(user_metrics_to_update, dict):
                user_metrics_to_update['is_in_checkin_flow'] = False
                # Also clear the checkin_type when ending the flow
                if 'checkin_type' in user_metrics_to_update:
                    # Set to None or del user_metrics_to_update['checkin_type']
                    user_metrics_to_update['checkin_type'] = None
                    logger.info(
                        f"---> [update_analytics_data] Reset 'checkin_type' to None for user {target_user_id}.")
                logger.info(
                    f"---> [update_analytics_data] Reset 'is_in_checkin_flow' to False for user {target_user_id}.")
            else:
                logger.error(
                    f"---> [update_analytics_data] Could not reset 'is_in_checkin_flow': 'metrics' not found or not a dict for user {target_user_id}.")
        # --- ADDED: Logic to reset check-in flag --- END ---

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

                # Parse the raw analysis to extract numbers
                analysis_result = raw_analysis  # Default if parsing fails
                remaining_message = None
                combined_response = raw_analysis  # Default for analytics
                # Default field updates (only o1 Response)
                field_updates = {
                    "o1 Response": analysis_result,
                    "CONVERSATION": f"(User sent image for calorie check: {image_url[:50]}...)"
                }

                try:
                    logger.info(f"Raw analysis to parse: {raw_analysis}")
                    # Extract numbers using regex (more flexible patterns)
                    calories_match = re.search(
                        r'Calories\s*=?\s*(\d+)', raw_analysis, re.IGNORECASE)
                    protein_match = re.search(
                        r'Protein\s*=?\s*(\d+)', raw_analysis, re.IGNORECASE)
                    carbs_match = re.search(
                        r'(?:Carbs?|Carbohydrates?)\s*=?\s*(\d+)', raw_analysis, re.IGNORECASE)
                    fats_match = re.search(
                        r'Fats?\s*=?\s*(\d+)', raw_analysis, re.IGNORECASE)

                    # Log what we found
                    logger.info(f"Regex matches - Calories: {calories_match.group(1) if calories_match else 'None'}, "
                                f"Protein: {protein_match.group(1) if protein_match else 'None'}, "
                                f"Carbs: {carbs_match.group(1) if carbs_match else 'None'}, "
                                f"Fats: {fats_match.group(1) if fats_match else 'None'}")

                    if all([calories_match, protein_match, carbs_match, fats_match]):
                        # If parsing succeeds, proceed with tracking and formatting
                        calories = int(calories_match.group(1))
                        protein = int(protein_match.group(1))
                        carbs = int(carbs_match.group(1))
                        fats = int(fats_match.group(1))

                        logger.info(f"Successfully parsed values - Calories: {calories}, "
                                    f"Protein: {protein}g, Carbs: {carbs}g, Fats: {fats}g")

                        # Keep the raw analysis for the first message
                        analysis_result = raw_analysis

                        # Update tracking with new meal
                        update_calorie_tracking(
                            ig_username, calories, protein, carbs, fats)

                        # Get current remaining values for second message
                        remaining = get_current_remaining_macros(ig_username)

                        # Second message - Current remaining calories/macros for the day
                        if remaining:
                            remaining_message = (
                                f"Your remaining macros for today:\n"
                                f"Calories: {remaining['remaining_calories']}kcal\n"
                                f"Protein: {remaining['remaining_protein']}g\n"
                                f"Carbs: {remaining['remaining_carbs']}g\n"
                                f"Fats: {remaining['remaining_fats']}g"
                            )
                        else:
                            remaining_message = "Could not retrieve remaining macros."

                        logger.info(f"Analysis result (o1): {analysis_result}")
                        logger.info(
                            f"Remaining message (o2): {remaining_message}")

                        # **** IMPORTANT: Define field_updates HERE when successful ****
                        field_updates = {
                            "o1 Response": analysis_result,
                            "o1 Response 2": remaining_message,  # Include o1 Response 2
                            "CONVERSATION": f"(User sent image for calorie check: {image_url[:50]}...)"
                        }
                        # Set combined response for analytics
                        combined_response = f"{analysis_result}\n\n{remaining_message}"

                    else:
                        # Parsing failed, keep the default field_updates (only o1 Response)
                        logger.error(
                            f"Failed to parse all values from analysis: {raw_analysis}")
                        # analysis_result, remaining_message, combined_response, field_updates remain as their defaults

                except Exception as e:
                    logger.error(
                        f"Error during food analysis parsing/tracking: {e}", exc_info=True)
                    logger.error(f"Raw analysis that failed: {raw_analysis}")
                    # Keep default field_updates, analysis_result, combined_response on error
                    remaining_message = None  # Ensure this is None on error

                # ***** Send updates to ManyChat OUTSIDE the try/except *****
                # This ensures we always send *something*, even if it's just the raw analysis on error
                update_success = update_manychat_fields(
                    subscriber_id, field_updates)
                if not update_success:
                    logger.error(
                        f"Failed to update ManyChat fields for {ig_username}")

                # ***** Update analytics OUTSIDE the try/except *****
                # Use combined_response which defaults to raw_analysis if parsing failed
                update_analytics_data(
                    ig_username,
                    f"(Sent food image: {image_url[:50]}...)",
                    combined_response,
                    subscriber_id,
                    first_name,
                    last_name
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

            # Get client name for todo items
            client_name = f"{first_name} {last_name}".strip() or ig_username

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
                # Add completed item for successful analysis
                add_todo_item(ig_username, client_name,
                              "Analyzed workout form check video and provided feedback",
                              status="completed")
            else:
                logger.error(f"Technique analysis failed for {ig_username}.")
                response_to_user = "Sorry, I couldn't analyze the video properly. Please ensure it's a valid video file link."
                # Add todo item for failed analysis
                add_todo_item(ig_username, client_name,
                              "Form check video analysis failed - needs manual review")

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
        #                 logger.info(
        #                     f"Using media analysis result: {processed_message}")

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
                if is_in_checkin_flow:
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
                                # If type is missing or unexpected, default to general chat
                                prompt_template = prompts.GENERAL_CHAT_PROMPT_TEMPLATE
                                logger.warning(
                                    f"Unexpected or missing checkin_type ('{checkin_type}'). Falling back to GENERAL_CHAT_PROMPT_TEMPLATE.")
                        else:
                            logger.warning(
                                "Failed to load check-in data. Falling back to GENERAL_CHAT_PROMPT_TEMPLATE.")
                            prompt_template = prompts.GENERAL_CHAT_PROMPT_TEMPLATE
                    else:
                        logger.warning(
                            "Could not find latest check-in file. Falling back to GENERAL_CHAT_PROMPT_TEMPLATE.")
                        prompt_template = prompts.GENERAL_CHAT_PROMPT_TEMPLATE

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

                # Add check-in data placeholders if using a check-in template and data is available
                if (prompt_template in [prompts.CHECKIN_PROMPT_TEMPLATE_MON, prompts.CHECKIN_PROMPT_TEMPLATE_WED]) and checkin_data_dict:
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
                if prompt_template in [prompts.CHECKIN_PROMPT_TEMPLATE_MON, prompts.CHECKIN_PROMPT_TEMPLATE_WED]:
                    # Add all keys specifically used in check-in templates
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
                    # Determine template name for logging
                    if prompt_template == prompts.CHECKIN_PROMPT_TEMPLATE_MON:
                        template_name = "CHECKIN_PROMPT_TEMPLATE_MON"
                    elif prompt_template == prompts.CHECKIN_PROMPT_TEMPLATE_WED:
                        template_name = "CHECKIN_PROMPT_TEMPLATE_WED"
                    else:
                        template_name = "GENERAL_CHAT_PROMPT_TEMPLATE"
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
                    logger.error(
                        f"No response generated for {ig_username}, using fallback.")
                    return False

                # Check if this is an acknowledgment to a form check
                last_messages = conversation_history[-3:
                                                     ] if conversation_history else []
                was_form_check = any("form check analysis" in msg.get(
                    'text', '').lower() for msg in last_messages)
                is_acknowledgment = any(word in processed_message.lower() for word in [
                                        'thanks', 'ok', 'yep', 'got it', 'makes sense'])

                if was_form_check and is_acknowledgment:
                    # Simple acknowledgment response
                    response = "No worries mate! Let me know if you need anything else."
                    # Add completed item to dashboard
                    add_todo_item(ig_username, f"{first_name} {last_name}".strip() or ig_username,
                                  "Client acknowledged form check feedback",
                                  status="completed")

                    field_updates = {
                        "o1 Response": response,
                        "CONVERSATION": processed_message
                    }
                    update_success = update_manychat_fields(
                        subscriber_id, field_updates)
                    if not update_success:
                        logger.error(
                            f"Failed to send acknowledgment response to {ig_username}")

                    update_analytics_data(
                        ig_username, processed_message, response, subscriber_id, first_name, last_name)
                    return True

                # Clean the response of any markdown formatting
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[len(
                        "```json"):].strip()
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[len("```"):].strip()
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-len("```")].strip()

                # Find the first '{' and the last '}'
                first_brace_index = cleaned_response.find('{')
                last_brace_index = cleaned_response.rfind('}')

                if first_brace_index != -1 and last_brace_index != -1 and last_brace_index > first_brace_index:
                    # Extract the substring between the first '{' and the last '}'
                    potential_json_str = cleaned_response[first_brace_index:last_brace_index + 1]

                    # Clean up common issues in the JSON
                    # Remove any lines that don't follow proper JSON format
                    lines = potential_json_str.split('\n')
                    cleaned_lines = []
                    in_array = False
                    for line in lines:
                        line = line.strip()
                        # Skip empty lines
                        if not line:
                            continue
                        # Check if we're in an array
                        if '[' in line:
                            in_array = True
                        if ']' in line:
                            in_array = False
                        # Only keep lines that look like valid JSON
                        if (
                            line.startswith('{') or
                            line.startswith('}') or
                            line.startswith('[') or
                            line.startswith(']') or
                            ':' in line or
                            (line.startswith('},') and in_array) or
                            line == '},' or
                            line == '],'
                        ):
                            # Remove trailing commas before closing braces
                            if line.endswith(',}'):
                                line = line.replace(',}', '}')
                            if line.endswith(',]'):
                                line = line.replace(',]', ']')
                            cleaned_lines.append(line)

                    potential_json_str = '\n'.join(cleaned_lines)

                    try:
                        intent_data = json.loads(potential_json_str)
                        logger.info(
                            f"Successfully cleaned and parsed JSON: {json.dumps(intent_data, indent=2)}")
                    except json.JSONDecodeError as json_err:
                        logger.error(
                            f"Failed to parse cleaned JSON: {json_err}")
                        logger.error(
                            f"Cleaned JSON attempt: {potential_json_str}")
                        return False
                else:
                    logger.error(
                        "Could not find valid JSON structure in response")
                    return False

                # Extract workout request details
                is_workout_req = intent_data.get('is_workout_request', False)
                confidence = intent_data.get('confidence', 0)
                actions = intent_data.get('actions', [])

                if is_workout_req and confidence > 70 and actions:
                    # Validate each action has required fields
                    valid_actions = []
                    for action in actions:
                        # Get action type and normalize it
                        action_type = action.get(
                            'action_type') or action.get('action')
                        if action_type:
                            # Normalize action type (convert add_exercise to add, etc)
                            if 'add' in action_type.lower():
                                action_type = 'add'
                            elif 'remove' in action_type.lower():
                                action_type = 'remove'

                        # Check for both possible field names for exercise
                        exercise = action.get(
                            'exercise_name') or action.get('exercise')
                        workout_type = action.get('workout_type')

                        if exercise and action_type and workout_type:
                            valid_actions.append({
                                'exercise': exercise,
                                'action': action_type,  # Use normalized action type
                                'workout_type': workout_type,
                                # Convert to string if number
                                'sets': str(action.get('sets', '3')),
                                # Convert to string if number
                                'reps': str(action.get('reps', '10'))
                            })
                            logger.info(
                                f"Validated action: {action_type} {exercise} to {workout_type}")
                        else:
                            logger.warning(
                                f"Invalid action found - exercise: {exercise}, action_type: {action_type}, workout_type: {workout_type}")

                    if valid_actions:
                        logger.info(
                            f"Found {len(valid_actions)} valid workout modifications to process")
                        # Process the workout modifications
                        try:
                            # Initialize Trainerize
                            trainerize = TrainerizeAutomation()
                            username = "shannonbirch@cocospersonaltraining.com"
                            password = "cyywp7nyk2"

                            if not trainerize.login(username, password):
                                raise Exception(
                                    "Failed to login to Trainerize")

                            if not trainerize.navigate_to_client(full_name):
                                raise Exception(
                                    f"Could not find client: {full_name}")

                            if not trainerize.navigate_to_training_program():
                                raise Exception(
                                    "Could not access training program")

                            success_count = 0
                            for action in valid_actions:
                                try:
                                    if not trainerize.click_workout_fuzzy(action['workout_type']):
                                        logger.error(
                                            f"Could not find workout: {action['workout_type']}")
                                        continue

                                    if not trainerize.click_edit_workout():
                                        logger.error(
                                            "Could not enter edit mode")
                                        continue

                                    if action['action'].lower() == 'add':
                                        if trainerize.add_exercise(action['exercise'], action['sets'], action['reps']):
                                            success_count += 1
                                    elif action['action'].lower() == 'remove':
                                        if trainerize.remove_exercise(action['exercise']):
                                            success_count += 1

                                    if not trainerize.save_workout():
                                        raise Exception(
                                            "Failed to save workout changes")

                                except Exception as action_e:
                                    logger.error(
                                        f"Error processing action: {action_e}")
                                    continue

                            if success_count > 0:
                                response = "Done! Updated your workout program with those changes. Need anything else?"
                                # Add completed item for successful modifications
                                success_actions = [
                                    f"{action['action']} {action['exercise']} to {action['workout_type']}" for action in valid_actions]
                                add_todo_item(ig_username, client_full_name,
                                              f"Successfully performed Trainerize actions: {', '.join(success_actions)}",
                                              status="completed")
                            else:
                                response = "Yep ill get onto that asap and get back to you when its done!"
                                # Add to Things To Do list
                                todo_actions = [
                                    f"{action['action']} {action['exercise']} to {action['workout_type']}" for action in valid_actions]
                                add_todo_item(ig_username, client_full_name,
                                              # Simpler format for todo items
                                              f"Workout modification: {', '.join(todo_actions)}")

                            field_updates = {
                                "o1 Response": response,
                                "CONVERSATION": message_text
                            }
                            update_success = update_manychat_fields(
                                subscriber_id, field_updates)
                            if not update_success:
                                logger.error(
                                    f"Failed to send confirmation to {ig_username}")

                            update_analytics_data(
                                ig_username, message_text, response, subscriber_id, first_name, last_name)

                            return True

                        except Exception as e:
                            logger.error(
                                f"Error in Trainerize automation: {e}")
                            error_response = "Sorry, I ran into a technical issue. Let me get that sorted and I'll help you update your workout."
                            # Add todo item for technical error
                            add_todo_item(ig_username, client_full_name,
                                          f"Technical error during workout modification: {str(e)[:100]}...")
                            field_updates = {
                                "o1 Response": error_response,
                                "CONVERSATION": message_text
                            }
                            update_manychat_fields(
                                subscriber_id, field_updates)
                            return True

                    else:
                        logger.warning(
                            "No valid actions found in workout request")
                        return False

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


async def get_ai_response(prompt: str) -> Optional[str]:
    """Get AI response using Gemini models with fallbacks."""
    try:
        # Add JSON formatting requirement to the prompt
        json_prompt = f"""
        {prompt}
        
        IMPORTANT: Format your response as a valid JSON object with the following structure:
        {{
            "response": "your actual response here",
            "confidence": number between 0 and 100,
            "is_workout_request": boolean,
            "is_form_check_request": boolean,
            "is_food_analysis_request": boolean,
            "has_image_url": boolean
        }}
        """

        # First try with GEMINI_MODEL_PRO
        response = call_gemini_with_retry(GEMINI_MODEL_PRO, json_prompt)
        if response:
            # Clean the response and ensure it's valid JSON
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[len("```json"):].strip()
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[len("```"):].strip()
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-len("```")].strip()

            try:
                # Parse the response as JSON to validate it
                json_response = json.loads(cleaned_response)
                # Return just the response text from the JSON object
                return json_response.get("response", cleaned_response)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract response from the text
                logger.warning(
                    "Failed to parse response as JSON, attempting fallback models")
                return None

        # If that fails, try GEMINI_MODEL_FLASH
        logger.warning("Primary model failed, trying FLASH model...")
        response = call_gemini_with_retry(GEMINI_MODEL_FLASH, json_prompt)
        if response:
            try:
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[len(
                        "```json"):].strip()
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[len("```"):].strip()
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-len("```")].strip()

                json_response = json.loads(cleaned_response)
                return json_response.get("response", cleaned_response)
            except json.JSONDecodeError:
                logger.warning(
                    "FLASH model failed to produce valid JSON, trying final fallback")
                return None

        # Last resort, try GEMINI_MODEL_FLASH_STANDARD
        logger.warning("FLASH model failed, trying FLASH_STANDARD model...")
        response = call_gemini_with_retry(
            GEMINI_MODEL_FLASH_STANDARD, json_prompt)
        if response:
            try:
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[len(
                        "```json"):].strip()
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[len("```"):].strip()
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-len("```")].strip()

                json_response = json.loads(cleaned_response)
                return json_response.get("response", cleaned_response)
            except json.JSONDecodeError:
                # If all JSON parsing attempts fail, return the cleaned response as is
                logger.warning(
                    "All models failed to produce valid JSON, using raw response")
                return cleaned_response

        logger.error("All Gemini models failed to generate response")
        return None

    except Exception as e:
        logger.error(f"Error getting AI response: {str(e)}")
        return None


# --- ADDED: Helper functions for loading check-in data --- START ---
def find_latest_checkin_file(full_name: str) -> Optional[str]:
    """Find the latest check-in JSON file for a given full name."""
    try:
        # Use full_name to construct pattern
        if not full_name or not isinstance(full_name, str):
            logger.error(
                "[find_latest_checkin_file] Invalid full_name provided.")
            return None

        # --- Use pathlib for robustness --- #
        # --- Add os.path.exists check for debugging --- #
        logger.info(
            f"[find_latest_checkin_file] Checking existence with os.path.exists for: {CHECKIN_REVIEWS_DIR}")
        if not os.path.exists(CHECKIN_REVIEWS_DIR):
            logger.error(
                f"[find_latest_checkin_file] os.path.exists failed for directory: {CHECKIN_REVIEWS_DIR}")
            # Return None here as if the basic check fails, pathlib likely will too
            return None
        else:
            logger.info(
                f"[find_latest_checkin_file] os.path.exists confirmed directory exists: {CHECKIN_REVIEWS_DIR}")
        # --- End os.path.exists check --- #

        checkin_dir_path = Path(CHECKIN_REVIEWS_DIR)
        if not checkin_dir_path.is_dir():
            logger.error(
                f"[find_latest_checkin_file] Check-in directory not found: {CHECKIN_REVIEWS_DIR}")
            return None

        # Try standard name order
        safe_name = full_name.replace(' ', '_').lower()
        filename_pattern = f"{safe_name}_*_fitness_wrapped_data.json"
        # --- Ensure logging uses full_name --- #
        logger.info(
            f"[find_latest_checkin_file] Searching pattern for '{full_name}': {checkin_dir_path / filename_pattern}")
        files = list(checkin_dir_path.glob(filename_pattern))

        # --- Debug: Log initial glob result --- #
        logger.info(
            f"[find_latest_checkin_file] Initial glob result for standard pattern '{filename_pattern}': {files}")
        # --- End Debug ---

        # Try swapped name order if no files found with standard order
        if not files:
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                # Simple swap
                swapped_name = f"{name_parts[-1]} {name_parts[0]}"
                safe_name_swapped = swapped_name.replace(' ', '_').lower()
                filename_pattern_swapped = f"{safe_name_swapped}_*_fitness_wrapped_data.json"
                # --- Ensure logging uses full_name --- #
                logger.info(
                    f"[find_latest_checkin_file] Trying swapped pattern for '{full_name}': {checkin_dir_path / filename_pattern_swapped}")
                files = list(checkin_dir_path.glob(filename_pattern_swapped))

        if not files:
            # --- Ensure logging uses full_name --- #
            logger.warning(
                f"[find_latest_checkin_file] No check-in files found for '{full_name}' matching patterns.")
            return None

        # Extract dates and sort
        dated_files = []
        for f_path in files:
            try:
                # Extract date string assuming format username_YYYYMMDD_...
                filename = os.path.basename(f_path)
                # filename_base = filename.split('_fitness_wrapped_data.json')[0]
                # filename_parts = filename_base.split('_')
                # Assuming date is YYYY-MM-DD format right before _fitness...
                date_str_match = re.search(r'_(\d{4}-\d{2}-\d{2})_', filename)
                if date_str_match:
                    date_str = date_str_match.group(1)
                    # Attempt to parse the date (YYYY-MM-DD format)
                    file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    # --- Store Path object --- #
                    dated_files.append((file_date, f_path))
                else:
                    logger.warning(
                        f"[find_latest_checkin_file] Could not parse YYYY-MM-DD date from filename: {filename}")
            except (ValueError, IndexError, AttributeError) as e:
                logger.warning(
                    f"[find_latest_checkin_file] Error parsing date from file {f_path}: {e}")

        if not dated_files:
            # --- Ensure logging uses full_name --- #
            logger.error(
                f"[find_latest_checkin_file] No files with parseable dates found for '{full_name}'")
            return None

        # Sort by date, newest first
        dated_files.sort(key=lambda x: x[0], reverse=True)
        latest_file_path = dated_files[0][1]
        # --- Ensure logging uses full_name --- #
        # --- Convert Path back to string for return --- #
        latest_file_str = str(latest_file_path)
        logger.info(
            f"[find_latest_checkin_file] Found latest check-in file for '{full_name}': {latest_file_str}")
        return latest_file_str

    except Exception as e:
        # --- Ensure logging uses full_name --- #
        logger.error(
            f"[find_latest_checkin_file] Error finding latest check-in file for '{full_name}': {e}", exc_info=True)
        return None


def load_json_data(file_path: str) -> Optional[Dict]:
    """Safely load JSON data from a file."""
    if not file_path or not os.path.exists(file_path):
        logger.error(
            f"[load_json_data] File not found or path is invalid: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            logger.info(
                f"[load_json_data] Successfully loaded JSON data from: {file_path}")
            return data
    except json.JSONDecodeError as e:
        logger.error(
            f"[load_json_data] Failed to decode JSON from {file_path}: {e}")
        return None
    except FileNotFoundError:  # Should be caught by os.path.exists, but good practice
        logger.error(f"[load_json_data] File not found error for: {file_path}")
        return None
    except Exception as e:
        logger.error(
            f"[load_json_data] Unexpected error loading JSON from {file_path}: {e}", exc_info=True)
        return None
# --- ADDED: Helper functions for loading check-in data --- END ---


def update_calorie_tracking(ig_username: str, calories: int, protein: int, carbs: int, fats: int) -> Optional[Dict]:
    """Update user's calorie tracking and return remaining values."""
    try:
        logger.info(
            f"Updating calorie tracking for {ig_username} - Calories: {calories}, P: {protein}g, C: {carbs}g, F: {fats}g")
        analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
        with open(analytics_file_path, 'r') as f:
            data = json.load(f)

        # Find the user
        user_found = False
        for user_id, user_data in data['conversations'].items():
            if isinstance(user_data, dict) and 'metrics' in user_data:
                metrics = user_data['metrics']
                if isinstance(metrics, dict) and metrics.get('ig_username') == ig_username:
                    user_found = True
                    calorie_tracking = metrics.get('calorie_tracking', {})
                    logger.info(
                        f"Found user's calorie tracking data: {json.dumps(calorie_tracking, indent=2)}")

                    # Check if it's a new day
                    current_date = datetime.now(
                        timezone.utc).strftime("%Y-%m-%d")
                    if calorie_tracking.get('current_date') != current_date:
                        logger.info(
                            f"New day detected. Resetting tracking. Old date: {calorie_tracking.get('current_date')}, New date: {current_date}")
                        # Reset for new day
                        calorie_tracking.update({
                            'current_date': current_date,
                            'calories_consumed': 0,
                            'remaining_calories': calorie_tracking['daily_target'],
                            'macros': {
                                'protein': {
                                    'daily_target': calorie_tracking['macros']['protein']['daily_target'],
                                    'consumed': 0,
                                    'remaining': calorie_tracking['macros']['protein']['daily_target']
                                },
                                'carbs': {
                                    'daily_target': calorie_tracking['macros']['carbs']['daily_target'],
                                    'consumed': 0,
                                    'remaining': calorie_tracking['macros']['carbs']['daily_target']
                                },
                                'fats': {
                                    'daily_target': calorie_tracking['macros']['fats']['daily_target'],
                                    'consumed': 0,
                                    'remaining': calorie_tracking['macros']['fats']['daily_target']
                                }
                            },
                            'meals_today': []
                        })

                    # Update consumed values
                    calorie_tracking['calories_consumed'] += calories
                    calorie_tracking['remaining_calories'] = calorie_tracking['daily_target'] - \
                        calorie_tracking['calories_consumed']

                    # Update macros
                    calorie_tracking['macros']['protein']['consumed'] += protein
                    calorie_tracking['macros']['protein']['remaining'] = calorie_tracking['macros'][
                        'protein']['daily_target'] - calorie_tracking['macros']['protein']['consumed']

                    calorie_tracking['macros']['carbs']['consumed'] += carbs
                    calorie_tracking['macros']['carbs']['remaining'] = calorie_tracking['macros'][
                        'carbs']['daily_target'] - calorie_tracking['macros']['carbs']['consumed']

                    calorie_tracking['macros']['fats']['consumed'] += fats
                    calorie_tracking['macros']['fats']['remaining'] = calorie_tracking['macros'][
                        'fats']['daily_target'] - calorie_tracking['macros']['fats']['consumed']

                    # Add meal to today's meals
                    meal_entry = {
                        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                        "calories": calories,
                        "protein": protein,
                        "carbs": carbs,
                        "fats": fats
                    }
                    calorie_tracking['meals_today'].append(meal_entry)

                    logger.info(
                        f"Updated tracking data: {json.dumps(calorie_tracking, indent=2)}")

                    # Save updated data
                    metrics['calorie_tracking'] = calorie_tracking
                    with open(analytics_file_path, 'w') as f:
                        json.dump(data, f, indent=2)

                    # Return remaining values
                    remaining = {
                        "remaining_calories": calorie_tracking['remaining_calories'],
                        "remaining_protein": calorie_tracking['macros']['protein']['remaining'],
                        "remaining_carbs": calorie_tracking['macros']['carbs']['remaining'],
                        "remaining_fats": calorie_tracking['macros']['fats']['remaining']
                    }
                    logger.info(
                        f"Returning remaining values: {json.dumps(remaining, indent=2)}")
                    return remaining

        if not user_found:
            logger.warning(f"User {ig_username} not found in analytics data")
        return None

    except Exception as e:
        logger.error(f"Error updating calorie tracking: {e}", exc_info=True)
        return None


def format_food_analysis_response(calories: int, protein: int, carbs: int, fats: int, ig_username: str) -> str:
    """Format the food analysis response with remaining calories and macros."""
    try:
        # Update tracking and get remaining values
        remaining = update_calorie_tracking(
            ig_username, calories, protein, carbs, fats)

        if remaining:
            return (f"This meal contains:\n"
                    f"Calories: {calories}kcal (Remaining today: {remaining['remaining_calories']}kcal)\n"
                    f"Protein: {protein}g (Remaining: {remaining['remaining_protein']}g)\n"
                    f"Carbs: {carbs}g (Remaining: {remaining['remaining_carbs']}g)\n"
                    f"Fats: {fats}g (Remaining: {remaining['remaining_fats']}g)")
        else:
            # Fallback to basic response if tracking update fails
            return f"Calories = {calories}, Protein = {protein}g, Carbs = {carbs}g, Fats = {fats}g"

    except Exception as e:
        logger.error(f"Error formatting food analysis response: {e}")
        return f"Calories = {calories}, Protein = {protein}g, Carbs = {carbs}g, Fats = {fats}g"


def get_current_remaining_macros(ig_username: str) -> Optional[Dict]:
    """Get the current remaining calories and macros from analytics data."""
    try:
        analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
        with open(analytics_file_path, 'r') as f:
            data = json.load(f)

        # Find the user
        for user_id, user_data in data['conversations'].items():
            if isinstance(user_data, dict) and 'metrics' in user_data:
                metrics = user_data['metrics']
                if isinstance(metrics, dict) and metrics.get('ig_username') == ig_username:
                    calorie_tracking = metrics.get('calorie_tracking', {})

                    # Return current remaining values
                    return {
                        "remaining_calories": calorie_tracking.get('remaining_calories', 0),
                        "remaining_protein": calorie_tracking.get('macros', {}).get('protein', {}).get('remaining', 0),
                        "remaining_carbs": calorie_tracking.get('macros', {}).get('carbs', {}).get('remaining', 0),
                        "remaining_fats": calorie_tracking.get('macros', {}).get('fats', {}).get('remaining', 0)
                    }

        logger.warning(f"User {ig_username} not found in analytics data")
        return None

    except Exception as e:
        logger.error(f"Error getting remaining macros: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    uvicorn.run("webhook:app",  # Use import string instead of app object
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
