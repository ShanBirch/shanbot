from typing import Dict, Any, List, Optional, Tuple, Union
import json
import requests
import logging
import hashlib
import hmac
import os
import google.generativeai as genai
import google.oauth2.service_account
import googleapiclient.discovery
import re
from datetime import datetime, timezone
import pytz
from app import prompts
import time
from collections import defaultdict
import dateutil.parser as parser
import httpx
from pydantic import BaseModel, Field
from google.cloud import speech_v1
import io
import tempfile
import random
import asyncio
from pathlib import Path
import subprocess
from PIL import Image
from post_onboarding_handler import PostOnboardingHandler
from todo_utils import add_todo_item

# Configure logging
logger = logging.getLogger("manychat_webhook")

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

# Global configuration
MANYCHAT_API_KEY = os.getenv(
    "MANYCHAT_API_KEY", "996573:5b6dc180662de1be343655db562ee918")
GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY", "AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y")
GEMINI_MODEL_PRO = "gemini-2.5-pro-exp-03-25"
GEMINI_MODEL_FLASH = "gemini-2.0-flash-thinking-exp-01-21"
GEMINI_MODEL_FLASH_STANDARD = "gemini-2.0-flash"

# File paths
CHECKIN_REVIEWS_DIR = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\output\\checkin_reviews"
SHEETS_CREDENTIALS_PATH = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\sheets_credentials.json"

# Global state tracking
form_check_pending: Dict[str, bool] = {}
food_analysis_pending: Dict[str, bool] = {}
program_info = {}
manychat_last_bot_sent_timestamps: Dict[str, float] = {}
manychat_message_buffer: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
manychat_last_message_time: Dict[str, float] = {}
program_edit_pending: Dict[str, str] = {}
message_buffer = {}

# Response options
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

# Constants
BUFFER_WINDOW = 15  # seconds to wait for grouping messages
RETRY_DELAY = 16  # Seconds to wait before retry
MAX_RETRIES = 3  # Maximum number of retry attempts

# Google Sheets Configuration
SPREADSHEET_ID = "1nDVn6jhkYBubVTQqbYU3PKo_WooeuTsQzsaNNcQdJlo"
ONBOARDING_SPREADSHEET_ID = "1038Ep0lYGEtpipNAIzH7RB67-KOAfXA-TcUTKBKqIfo"
RANGE_NAME = "Sheet1!A:E"
ONBOARDING_RANGE_NAME = "Sheet1!A:AAF"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Initialize Gemini
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {e}", exc_info=True)

# Add this helper function near the top or with other helpers
ONBOARDING_COMPLETION_TRIGGERS = [
    "ill go over everything and set you up now",
    "thanks for joining up",
    "let me get into this",
    "i'll go over everything and set you up now",
    "i'll go over everything and set you up now",
    # Add more as needed
]


def is_onboarding_complete(ai_response: str) -> bool:
    response_lower = ai_response.lower()
    return any(trigger in response_lower for trigger in ONBOARDING_COMPLETION_TRIGGERS)

# Utility Functions


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
    except FileNotFoundError:
        logger.error(f"[load_json_data] File not found error for: {file_path}")
        return None
    except Exception as e:
        logger.error(
            f"[load_json_data] Unexpected error loading JSON from {file_path}: {e}", exc_info=True)
        return None


def transcribe_audio_with_google(audio_bytes: bytes) -> Optional[str]:
    """Transcribe audio using Google Cloud Speech-to-Text with FFmpeg conversion"""
    if not AUDIO_PROCESSING_AVAILABLE:
        logger.warning(
            "Audio processing is not available - cannot transcribe audio")
        return "Audio message received (transcription not available)"

    try:
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_mp4, \
                tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:

            temp_mp4.write(audio_bytes)
            temp_mp4.flush()

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

            client = speech_v1.SpeechClient()

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
    """Downloads and processes media content, prioritizing video analysis for video files."""
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

        elif content_type == 'video/mp4':
            media_type = 'video'
            logger.info("Processing as video content")
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

            exercise_detection_prompt = """This is a video clip. Please analyze it and determine if it shows someone performing an exercise or workout. If it does:
            1. Identify the specific exercise being performed
            2. Note the number of repetitions visible (if applicable)
            3. Describe the overall form and technique shown

            If it's not an exercise video, just say "Not an exercise video" and describe the general content instead."""

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

                if "Not an exercise video" not in exercise_analysis:
                    prompt_text = """This is an exercise video. Please provide a detailed analysis including:
                    1. Exercise Identification: What exercise is being performed?
                    2. Form Analysis: Describe the technique and form shown in detail
                    3. Key Points: List the main technical aspects being demonstrated correctly or incorrectly
                    4. Safety Concerns: Note any potential safety issues or form corrections needed
                    5. Recommendations: Provide specific suggestions for improvement if needed

                    Format the response in clear sections for readability."""
                else:
                    prompt_text = """This is a video clip. Please:
                    1. Describe the main visual elements and actions
                    2. Note any text or captions visible
                    3. If audio is present, briefly describe its nature (e.g., speech, music, background noise)"""

            except Exception as e:
                logger.error(
                    f"Error during exercise detection with main model: {e}")
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

                    if any(exercise_term in flash_analysis.lower() for exercise_term in ['exercise', 'form', 'technique', 'deadlift', 'squat', 'bench', 'workout', 'rep', 'position', 'movement']):
                        prompt_text = """Provide a detailed exercise technique analysis including:
                        1. Exercise name and setup details
                        2. Movement execution quality
                        3. Specific form points observed
                        4. Safety considerations
                        5. Improvement suggestions"""
                    else:
                        prompt_text = """This is a video clip. Please:
                        1. Describe the main visual elements and actions
                        2. Note any text or captions visible
                        3. If audio is present, briefly describe its nature"""

                except Exception as flash_e:
                    logger.error(f"Flash model also failed: {flash_e}")
                    prompt_text = "Please describe what you see in this video, focusing on any exercise or movement technique if present."

        elif content_type.startswith('audio/'):
            media_type = 'audio'
            logger.info("Processing as audio content")
            transcription = transcribe_audio_with_google(media_bytes)
            if transcription:
                return 'audio', transcription
            else:
                logger.warning(
                    "Speech-to-Text failed for audio, falling back to Gemini audio analysis...")
                prompt_text = "This is an audio file. Please describe any indicators of audio content you can detect."

        else:
            logger.warning(f"Unrecognized content type: {content_type}")
            return None, None

        if not prompt_text:
            logger.error(
                f"No prompt text generated for media type {media_type}. This shouldn't happen.")
            return media_type, "Error: Could not generate analysis prompt."

        media_part = {
            "mime_type": content_type,
            "data": media_bytes
        }

        gemini_contents = [
            {
                "parts": [
                    {"text": prompt_text},
                    {"inline_data": media_part}
                ]
            }
        ]

        gemini_description = None
        try:
            model = genai.GenerativeModel(GEMINI_MODEL_PRO)
            response = model.generate_content(contents=gemini_contents)
            gemini_description = response.text.strip()
            logger.info(f"Successfully processed {media_type} with main model")
        except Exception as e:
            logger.warning(
                f"Main model failed for {media_type}: {e}. Trying flash model...")
            try:
                model = genai.GenerativeModel(GEMINI_MODEL_FLASH)
                simple_prompt = f"Briefly describe this {media_type} content."
                gemini_contents[0]['parts'][0]['text'] = simple_prompt
                response = model.generate_content(contents=gemini_contents)
                gemini_description = response.text.strip()
                logger.info(
                    f"Successfully processed {media_type} with flash model")
            except Exception as e2:
                logger.error(
                    f"All models failed to process {media_type}: {e2}")
                gemini_description = "Analysis failed."

        if media_type == 'video':
            final_result = f"Video Content: {gemini_description if gemini_description else 'Visual analysis failed.'}"
            if transcription:
                final_result += f" (Audio transcription: {transcription})"
            return media_type, final_result
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


def process_conversation_for_media(conversation_text: str) -> str:
    """Detects media URLs in conversation text, analyzes them, and replaces URLs with descriptions."""
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
                replacement_text = f"(Voice message: {result_text})"
            elif media_type == 'video':
                replacement_text = f"(Sent a video: {result_text})"
            else:
                replacement_text = f"({media_type}: {result_text})"
            logger.info(
                f"Replacing URL with {media_type} description: {replacement_text[:100]}...")
        else:
            replacement_text = f"(Sent {media_type if media_type else 'media'}, but analysis failed)"
            logger.warning(f"Using generic placeholder for {url[:100]}")

        processed_text = processed_text.replace(url, replacement_text, 1)

    logger.info("Finished processing conversation text for media.")
    return processed_text


async def get_ai_response(prompt: str) -> Optional[str]:
    """Get response from Gemini with proper fallback handling"""
    async def try_model(model_name: str, retry_count: int = 0) -> Optional[str]:
        try:
            response = await call_gemini_with_retry(model_name, prompt)
            if response:
                logger.info(f"Got successful response from model {model_name}")
                return response
            logger.warning(f"No response from model {model_name}")
        except Exception as e:
            logger.error(f"Error with model {model_name}: {e}")
        return None

    # Try primary model
    logger.info("Trying primary model (PRO)")
    response = await try_model(GEMINI_MODEL_PRO)
    if response:
        return response

    # If primary fails, wait and try flash thinking model
    logger.warning(
        "Primary model failed. Waiting before trying flash-thinking model...")
    await asyncio.sleep(RETRY_DELAY)  # Wait before trying fallback
    logger.info("Trying flash-thinking model")
    response = await try_model(GEMINI_MODEL_FLASH)
    if response:
        return response

    # If flash thinking fails, wait and try standard flash model
    logger.warning(
        "Flash thinking model failed. Waiting before trying standard flash model...")
    await asyncio.sleep(RETRY_DELAY)  # Wait before trying second fallback
    logger.info("Trying standard flash model")
    response = await try_model(GEMINI_MODEL_FLASH_STANDARD)
    if response:
        return response

    # If all models fail, return None
    logger.error("All models failed to generate response")
    return None


async def call_gemini_with_retry(model_name: str, prompt: str, retry_count: int = 0) -> Optional[str]:
    """Call Gemini API with retry logic and multiple fallback models."""
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        if "429" in str(e) and retry_count < MAX_RETRIES:
            if model_name == GEMINI_MODEL_PRO:
                logger.warning(
                    f"Rate limit hit for {model_name}. Falling back to flash-thinking model after delay.")
                await asyncio.sleep(RETRY_DELAY)
                return await call_gemini_with_retry(GEMINI_MODEL_FLASH, prompt, retry_count + 1)
            else:
                wait_time = RETRY_DELAY * (retry_count + 1)
                logger.warning(
                    f"Rate limit hit. Waiting {wait_time} seconds before retry {retry_count + 1} on {model_name}")
                await asyncio.sleep(wait_time)
                return await call_gemini_with_retry(model_name, prompt, retry_count + 1)
        elif retry_count < MAX_RETRIES:
            if model_name == GEMINI_MODEL_PRO:
                logger.warning(
                    f"Main model failed: {e}. Trying first fallback model after delay.")
                await asyncio.sleep(RETRY_DELAY)
                return await call_gemini_with_retry(GEMINI_MODEL_FLASH, prompt, retry_count + 1)
            elif model_name == GEMINI_MODEL_FLASH:
                logger.warning(
                    f"First fallback model failed: {e}. Trying second fallback model after delay.")
                await asyncio.sleep(RETRY_DELAY)
                return await call_gemini_with_retry(GEMINI_MODEL_FLASH_STANDARD, prompt, retry_count + 1)
        logger.error(f"All Gemini attempts failed: {e}")
        return None


def update_manychat_fields(subscriber_id: str, field_updates: Dict[str, str]) -> bool:
    """Update custom fields in ManyChat for a subscriber"""
    filtered_updates = {
        k: v for k, v in field_updates.items() if v is not None and v != ""}
    if not filtered_updates:
        logger.info("No valid field updates to send to ManyChat.")
        return True

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
    logger.info(f"ManyChat API Request Payload: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(
            "https://api.manychat.com/fb/subscriber/setCustomFields",
            headers=headers,
            json=data,
            timeout=10
        )
        logger.info(
            f"ManyChat API response: {response.status_code} - {response.text[:500]}")
        response.raise_for_status()
        logger.info(
            f"Successfully updated ManyChat fields for subscriber {subscriber_id}.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Error updating ManyChat fields for subscriber {subscriber_id}: {e}", exc_info=True)
        if hasattr(e, 'response') and e.response is not None:
            logger.error(
                f"ManyChat Error Response Body: {e.response.text[:500]}")
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error during ManyChat field update for {subscriber_id}: {e}", exc_info=True)
        return False


def get_user_data(ig_username: str, subscriber_id: Optional[str] = None) -> tuple[list, dict, Optional[str]]:
    """Retrieve user data from analytics file, searching by subscriber_id first, then ig_username.

    Args:
        ig_username: The Instagram username (can be a generated placeholder).
        subscriber_id: The ManyChat subscriber ID (optional but preferred for searching).

    Returns:
        A tuple containing:
            - list: The conversation history (empty list if user not found).
            - dict: The metrics dictionary (empty dict if user not found).
            - Optional[str]: The user ID (key in the analytics file) if found, otherwise None.
    """
    logger.info(f"\n=== GET USER DATA START ===")
    logger.info(
        f"Searching for user: ig='{ig_username}', sub_id='{subscriber_id}'")
    analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
    logger.info(f"Loading data from: {analytics_file_path}")

    try:
        with open(analytics_file_path, "r") as f:
            analytics_data = json.load(f)
        logger.info("Successfully loaded analytics file")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load or parse analytics file: {e}")
        return [], {}, None  # Return default values on file error

    conversations_data = analytics_data.get('conversations', {})
    found_user_id = None
    user_data = None

    # 1. Try searching by subscriber_id if provided
    if subscriber_id:
        logger.info(f"Attempting search by subscriber_id: '{subscriber_id}'")
        for user_id_key, data_entry in conversations_data.items():
            if isinstance(data_entry, dict):
                metrics = data_entry.get("metrics", {})
                if isinstance(metrics, dict) and metrics.get("subscriber_id") == subscriber_id:
                    found_user_id = user_id_key
                    user_data = data_entry
                    logger.info(
                        f"Found user by subscriber_id. User ID key: '{found_user_id}'")
                    break  # Stop searching once found

    # 2. If not found by subscriber_id (or subscriber_id wasn't provided), try searching by ig_username
    if not found_user_id and ig_username:
        logger.info(f"Attempting search by ig_username: '{ig_username}'")
        search_ig_username_lower = ig_username.strip().lower()
        for user_id_key, data_entry in conversations_data.items():
            # Also check if the main key is the ig_username (legacy structure?)
            if user_id_key.lower() == search_ig_username_lower:
                found_user_id = user_id_key
                user_data = data_entry
                logger.info(
                    f"Found user by matching main key with ig_username. User ID key: '{found_user_id}'")
                break
            # Check within metrics
            if isinstance(data_entry, dict):
                metrics = data_entry.get("metrics", {})
                if isinstance(metrics, dict):
                    json_ig_username = metrics.get("ig_username", None)
                    if isinstance(json_ig_username, str) and json_ig_username.strip().lower() == search_ig_username_lower:
                        found_user_id = user_id_key
                        user_data = data_entry
                        logger.info(
                            f"Found user by ig_username in metrics. User ID key: '{found_user_id}'")
                        break  # Stop searching once found

    # 3. Process results
    if found_user_id and user_data:
        metrics_dict = user_data.get('metrics', {})
        # Retrieve conversation_history from INSIDE metrics_dict
        conversation_history = metrics_dict.get('conversation_history', [])

        # Ensure subscriber_id is stored in metrics if not already present
        if subscriber_id and metrics_dict.get("subscriber_id") != subscriber_id:
            logger.info(
                f"Adding/updating subscriber_id '{subscriber_id}' to metrics for user '{found_user_id}'")
            metrics_dict["subscriber_id"] = subscriber_id

        logger.info(
            f"Returning data for user: {found_user_id}. History length: {len(conversation_history)}")
        return conversation_history, metrics_dict, found_user_id
    else:
        logger.warning(
            f"User not found using ig_username='{ig_username}' or subscriber_id='{subscriber_id}'")
        return [], {}, None


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
    and creates a new user entry if the user doesn't exist. Prioritizes lookup by subscriber_id.
    Optionally resets check-in flag. Writes back the changes.
    """
    logger.info(
        f"---> [update_analytics_data] Attempting to update/create history for ig='{ig_username}' (SubID: {subscriber_id})")
    analytics_file_path = r"C:\\\\Users\\\\Shannon\\\\OneDrive\\\\Desktop\\\\shanbot\\\\app\\\\analytics_data_good.json"

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

        # 2. Find the user within 'conversations' using prioritized search
        conversations_data = analytics_data.get('conversations', {})
        if not isinstance(conversations_data, dict):
            logger.error(
                "---> [update_analytics_data] 'conversations' key is not a dictionary. Resetting.")
            conversations_data = {}
            analytics_data['conversations'] = conversations_data

        target_user_id = None
        target_user_data = None
        search_ig_username_lower = ig_username.strip().lower() if ig_username else None

        # --- Prioritized Search Logic ---
        # 1. Search by subscriber_id in metrics
        if subscriber_id:
            logger.info(
                f"---> [update_analytics_data] Searching by subscriber_id: '{subscriber_id}'")
            for user_id_key, data_entry in conversations_data.items():
                if isinstance(data_entry, dict):
                    metrics = data_entry.get("metrics", {})
                    if isinstance(metrics, dict) and metrics.get("subscriber_id") == str(subscriber_id):
                        target_user_id = user_id_key
                        target_user_data = data_entry
                        logger.info(
                            f"---> [update_analytics_data] Found user by subscriber_id. User ID key: '{target_user_id}'")
                        break

        # 2. If not found, search by ig_username in metrics
        if not target_user_id and search_ig_username_lower:
            logger.info(
                f"---> [update_analytics_data] Searching by ig_username in metrics: '{search_ig_username_lower}'")
            for user_id_key, data_entry in conversations_data.items():
                if isinstance(data_entry, dict):
                    metrics = data_entry.get("metrics", {})
                    if isinstance(metrics, dict):
                        json_ig_username = metrics.get("ig_username", None)
                        if isinstance(json_ig_username, str) and json_ig_username.strip().lower() == search_ig_username_lower:
                            target_user_id = user_id_key
                            target_user_data = data_entry
                            logger.info(
                                f"---> [update_analytics_data] Found user by ig_username in metrics. User ID key: '{target_user_id}'")
                            break

        # 3. If not found, search by top-level key matching ig_username (legacy)
        if not target_user_id and search_ig_username_lower:
            logger.info(
                f"---> [update_analytics_data] Searching by top-level key matching ig_username: '{search_ig_username_lower}'")
            if search_ig_username_lower in conversations_data:
                target_user_id = search_ig_username_lower
                target_user_data = conversations_data[target_user_id]
                logger.info(
                    f"---> [update_analytics_data] Found user by matching top-level key. User ID key: '{target_user_id}'")

        # --- End Prioritized Search Logic ---

        # 3. Create new user if not found, otherwise update history
        current_timestamp_iso = datetime.now(timezone.utc).isoformat()

        if not target_user_id:
            # --- CREATE NEW USER ---
            if not subscriber_id:
                logger.error(
                    "---> [update_analytics_data] Cannot create new user without a subscriber_id.")
                return  # Cannot proceed without a unique ID

            logger.info(
                f"---> [update_analytics_data] User not found by any method. Creating new profile using subscriber_id '{subscriber_id}' as key.")
            # Use ManyChat subscriber ID as the unique key
            new_user_key = str(subscriber_id)
            new_user_data = {
                "metrics": {
                    # Use provided ig_username or generate one
                    "ig_username": ig_username or f"user_{subscriber_id}",
                    "subscriber_id": str(subscriber_id),
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
                    # --- ADDED: Initialize check-in flag for new users ---
                    "is_in_checkin_flow": False,
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
                f"---> [update_analytics_data] Created new user profile for ig='{ig_username}' with SubID key '{target_user_id}'")
            # --- END CREATE NEW USER ---
        elif not target_user_data:  # Should not happen if target_user_id is set, but safety check
            logger.error(
                f"---> [update_analytics_data] Found user ID '{target_user_id}' but target_user_data is missing. Aborting update.")
            return

        # Ensure 'metrics' and 'conversation_history' structure exists (important for existing users too)
        if "metrics" not in target_user_data or not isinstance(target_user_data["metrics"], dict):
            target_user_data["metrics"] = {}
            logger.warning(
                f"---> [update_analytics_data] Created missing 'metrics' dict for user {target_user_id}")
        metrics_dict = target_user_data["metrics"]

        # --- Updated logic for ig_username ---
        existing_ig_username_in_metrics = metrics_dict.get("ig_username")
        # ig_username parameter to this function comes from webhook0605.py (payload)
        new_ig_username_from_payload = ig_username

        is_existing_good = existing_ig_username_in_metrics and \
            not (existing_ig_username_in_metrics.startswith("user_")
                 and existing_ig_username_in_metrics[5:].isdigit())
        is_new_placeholder = new_ig_username_from_payload.startswith("user_") and \
            new_ig_username_from_payload[5:].isdigit()

        if is_existing_good and is_new_placeholder:
            logger.info(
                f"[update_analytics_data] Preserving existing valid ig_username '{existing_ig_username_in_metrics}' for user '{target_user_id}' over new placeholder '{new_ig_username_from_payload}'.")
            # metrics_dict["ig_username"] remains unchanged
        elif metrics_dict.get("ig_username") != new_ig_username_from_payload:
            logger.info(
                f"[update_analytics_data] Updating ig_username from '{metrics_dict.get('ig_username')}' to '{new_ig_username_from_payload}' for user '{target_user_id}'.")
            metrics_dict["ig_username"] = new_ig_username_from_payload
        else:
            logger.info(
                f"[update_analytics_data] ig_username '{existing_ig_username_in_metrics}' for user '{target_user_id}' is already up-to-date.")
        # --- End updated logic for ig_username ---

        # Update/ensure subscriber_id is correct (and string)
        metrics_dict["subscriber_id"] = str(subscriber_id)
        logger.info(
            f"[update_analytics_data] Metrics now contains: ig_username='{metrics_dict.get('ig_username')}', subscriber_id='{metrics_dict.get('subscriber_id')}' for user ID '{target_user_id}'")

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

        # --- Check for onboarding completion and trigger post-onboarding process ---
        # NOTE: This check might need adjustment based on where the background task is actually triggered.
        # If the background task trigger happens *after* this function call in webhook0605.py,
        # then this check here might be redundant or could be moved.
        # However, keeping it here ensures the 'is_onboarding' flag gets set if the trigger phrase is in the AI response saved here.
        # if is_onboarding_complete(ai_response):
        #     logger.info(
        #         f"[update_analytics_data] Onboarding completion phrase detected in AI response for {target_user_id}, setting is_onboarding=True")
        #     metrics_dict['is_onboarding'] = True
            # The actual background task launch should happen in webhook0605.py after this function returns.

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


# --- Helper Function for Media Analysis --- START -


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


def build_member_chat_prompt(
    client_data: Dict[str, Any],
    current_message: str,
    conversation_history: str = "",
    current_stage: str = "Topic 1",
    trial_status: str = "Initial Contact",
    full_name: str = None
) -> str:
    try:
        logger.info(
            f"[build_member_chat_prompt] client_data (first 500 chars): {json.dumps(client_data, indent=2)[:500]}...")
        # Get conversation history from metrics
        history = []
        if isinstance(client_data.get('conversation_history'), list):
            history = client_data['conversation_history']  # All messages
            logger.info(f"Found {len(history)} total messages in history")
            if len(history) > 100:
                logger.warning(
                    f"User has a very large conversation history ({len(history)} messages).")
        # Format conversation history with timestamps
        formatted_history = ""
        for msg in history:
            try:
                timestamp = msg.get('timestamp', '')
                msg_type = msg.get('type', '')
                msg_text = msg.get('text', '')
                # Try to parse and format timestamp nicely
                try:
                    dt_object = datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00"))
                    formatted_ts = dt_object.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, AttributeError):
                    formatted_ts = timestamp
                if msg_type and msg_text:
                    formatted_history += f"[{formatted_ts}] {msg_type}: {msg_text}\n"
            except Exception as msg_e:
                logger.warning(f"Error formatting message in history: {msg_e}")
                continue

        # For logging to terminal, show only the last few messages
        num_messages_to_log = 5
        history_lines_for_log = formatted_history.splitlines()
        logged_history_display = "\n".join(
            history_lines_for_log[-num_messages_to_log:])
        if len(history_lines_for_log) > num_messages_to_log:
            logged_history_display = f"... (last {num_messages_to_log} of {len(history_lines_for_log)} messages) ...\n" + \
                logged_history_display

        logger.info(
            f"Formatted conversation history (for terminal log - last {num_messages_to_log} lines):\n{logged_history_display}")

        # Add current message with current timestamp TO THE FULL HISTORY for the prompt
        current_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        # Start with all historical messages
        full_history_for_prompt = formatted_history
        if full_history_for_prompt:  # if there was history, add a newline before current
            full_history_for_prompt += f"\n[{current_ts}] Lead: {current_message}"
        else:  # if no history, current message is the start
            full_history_for_prompt = f"[{current_ts}] Lead: {current_message}"

        # Initialize template parameters with defaults
        template_params = {
            'current_melbourne_time_str': get_melbourne_time_str(),
            # Use the complete history for the prompt
            'full_conversation': full_history_for_prompt,
            'sex': '',  # Default empty for optional parameter
            'fitness_goals': '',  # Default empty for optional parameter
            'dietary_requirements': '',  # Default empty for optional parameter
            'training_frequency': ''  # Default empty for optional parameter
        }
        # Check onboarding status first
        is_onboarding = client_data.get('is_onboarding', False)
        logger.info(
            f"[build_member_chat_prompt] Onboarding status found: {is_onboarding} for client_data")
        # Get name information from multiple sources
        first_name = None
        last_name = None

        # Try client_details first
        client_details = client_data.get('client_details', {})
        if isinstance(client_details, dict):
            first_name = client_details.get('first_name')
            last_name = client_details.get('last_name')
            if first_name:
                logger.info(
                    f"Found name in client_details: {first_name} {last_name}")

        # If not found, try client_analysis bio
        if not first_name and isinstance(client_data.get('client_analysis'), dict):
            bio = client_data['client_analysis'].get('profile_bio', {})
            if isinstance(bio, dict) and bio.get('PERSON NAME'):
                name_parts = bio['PERSON NAME'].split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = name_parts[-1]
                    logger.info(
                        f"Found name in profile bio: {first_name} {last_name}")

        # If still not found, try top-level data
        if not first_name:
            first_name = client_data.get('first_name')
            last_name = client_data.get('last_name')
            if first_name:
                logger.info(
                    f"Found name in top-level data: {first_name} {last_name}")

        # Add name parameters if found
        if first_name:
            template_params['first_name'] = first_name
            logger.info(f"Added first_name to template_params: {first_name}")
        if last_name:
            template_params['last_name'] = last_name
            logger.info(f"Added last_name to template_params: {last_name}")
        if first_name and last_name:
            template_params['full_name'] = f"{first_name} {last_name}"
            logger.info(
                f"Added full_name to template_params: {template_params['full_name']}")

        # Collect all available data with logging
        if client_data.get('ig_username'):
            template_params['ig_username'] = client_data['ig_username']
            logger.info(
                f"Added ig_username to template_params: {template_params['ig_username']}")

        client_analysis = client_data.get('client_analysis', {})
        if isinstance(client_analysis, dict):
            if isinstance(client_analysis.get('profile_bio'), (str, dict)):
                template_params['bio'] = client_analysis['profile_bio']
                logger.info("Added bio to template_params")

            interests = client_analysis.get('interests', [])
            if interests:
                template_params['interests'] = json.dumps(interests)
                logger.info(
                    f"Added {len(interests)} interests to template_params")

            topics = client_analysis.get('conversation_topics', [])
            template_params['topics_str'] = "\n- " + \
                "\n- ".join(topics) if topics else "No topics recorded yet"
            logger.info(
                f"Added {len(topics)} conversation topics to template_params")

        # Add other parameters if available
        if current_stage:
            template_params['current_stage'] = current_stage
            logger.info(
                f"Added current_stage to template_params: {current_stage}")

        if trial_status:
            template_params['trial_status'] = trial_status
            logger.info(
                f"Added trial_status to template_params: {trial_status}")

        # --- Start New Extraction Logic ---
        logger.info(
            "[build_member_chat_prompt] Attempting to extract meal plan, workout, and nutrition summaries.")

        # Initialize with defaults
        template_params['meal_plan_summary'] = "Meal plan details not available."
        template_params['workout_program_summary'] = "Workout program details not available."
        template_params['nutrition_summary'] = "Nutrition tracking details not available."

        # Meal Plan Summary
        # Assuming 'meal_plan' might exist directly under metrics (client_data)
        meal_plan_data = client_data.get('meal_plan')
        if meal_plan_data:
            if isinstance(meal_plan_data, str):  # Use directly if it's a simple string summary
                template_params['meal_plan_summary'] = meal_plan_data
            # Create a placeholder summary if it's a complex object
            elif isinstance(meal_plan_data, dict):
                # Refine this based on the actual structure if needed
                # Example summary
                summary = f"Meal Plan Active (Details: {len(meal_plan_data)} components)"
                template_params['meal_plan_summary'] = summary
            else:  # Handle unexpected format
                template_params['meal_plan_summary'] = "Meal plan data found but format unrecognized."
            logger.info(
                f"Extracted Meal Plan Summary: {template_params['meal_plan_summary'][:100]}...")
        else:
            logger.info("No 'meal_plan' data found in metrics.")

        # Workout Program Summary
        # Assuming 'workout_program' might exist directly under metrics (client_data)
        workout_program_data = client_data.get('workout_program')
        if workout_program_data:
            # Use directly if it's a simple string summary
            if isinstance(workout_program_data, str):
                template_params['workout_program_summary'] = workout_program_data
            # Create a placeholder summary if it's a complex object
            elif isinstance(workout_program_data, dict):
                # Refine this based on the actual structure if needed
                # Example summary
                summary = f"Workout Program Active (Details: {len(workout_program_data)} days/components)"
                template_params['workout_program_summary'] = summary
            else:  # Handle unexpected format
                template_params['workout_program_summary'] = "Workout program data found but format unrecognized."
            logger.info(
                f"Extracted Workout Program Summary: {template_params['workout_program_summary'][:100]}...")
        else:
            logger.info("No 'workout_program' data found in metrics.")

        # Nutrition Summary (from calorie_tracking)
        calorie_tracking_data = client_data.get('calorie_tracking')
        if isinstance(calorie_tracking_data, dict):
            cal_target = calorie_tracking_data.get('daily_target', 'N/A')
            macros = calorie_tracking_data.get('macros', {})
            prot_target = macros.get('protein', {}).get('daily_target', 'N/A')
            carb_target = macros.get('carbs', {}).get('daily_target', 'N/A')
            fat_target = macros.get('fats', {}).get('daily_target', 'N/A')
            summary = f"Daily Targets: Calories={cal_target}, P={prot_target}g, C={carb_target}g, F={fat_target}g"
            template_params['nutrition_summary'] = summary
            logger.info(f"Extracted Nutrition Summary: {summary}")
        else:
            logger.info("No 'calorie_tracking' data found or not a dict.")

        # --- End New Extraction Logic ---

        # Log all parameters before template formatting
        logger.info("\n=== TEMPLATE PARAMETERS ===")
        for key, value in template_params.items():
            if key == 'full_conversation':  # Special handling for logging full_conversation
                # Log the truncated version for the terminal
                terminal_log_conversation = "\n".join(
                    full_history_for_prompt.splitlines()[-num_messages_to_log:])
                if len(full_history_for_prompt.splitlines()) > num_messages_to_log:
                    terminal_log_conversation = f"... (last {num_messages_to_log} of {len(full_history_for_prompt.splitlines())} messages in prompt) ...\n" + \
                        terminal_log_conversation
                logger.info(
                    f"{key} (for prompt - logged last {num_messages_to_log}):\n{terminal_log_conversation}")
            elif isinstance(value, str) and len(value) > 100:
                logger.info(f"{key}: {value[:100]}...")
            else:
                logger.info(f"{key}: {value}")
        logger.info("=== END TEMPLATE PARAMETERS ===\n")

        # Format the conversation history for the prompt
        full_conversation_history_formatted = format_conversation_history(
            client_data.get("conversation_history", [])
        )

        # --- Log only the last 5 messages to the terminal ---
        history_for_logging = client_data.get("conversation_history", [])
        last_5_messages_formatted = format_conversation_history(
            history_for_logging[-5:])
        logger.info(
            f"Formatted conversation for prompt (last 5 shown):\n{last_5_messages_formatted}")
        logger.info(
            f"Number of messages in full history for prompt: {len(history_for_logging)}")
        # --- End logging modification ---

        # Dynamically select the prompt template based on current_stage
        if is_onboarding:
            logger.info(
                "TEMPLATE SELECTION: Using ONBOARDING_PROMPT_TEMPLATE for onboarding flow")
            try:
                prompt = prompts.ONBOARDING_PROMPT_TEMPLATE.format(
                    **template_params)
                logger.info(
                    "TEMPLATE CONFIRMATION: Successfully formatted ONBOARDING_PROMPT_TEMPLATE")
                logger.info(f"Used parameters: {list(template_params.keys())}")
                return prompt
            except KeyError as e:
                logger.warning(
                    f"Optional parameter missing in onboarding template: {e}, using empty string")
                # Add missing parameter with empty string
                template_params[str(e.args[0])] = ''
                try:
                    prompt = prompts.ONBOARDING_PROMPT_TEMPLATE.format(
                        **template_params)
                    logger.info(
                        "TEMPLATE CONFIRMATION: Successfully formatted ONBOARDING_PROMPT_TEMPLATE with defaults")
                    return prompt
                except Exception as e2:
                    logger.error(f"Still failed after adding defaults: {e2}")
                    is_onboarding = False  # Fall back to general template

        # General template as default or fallback
        logger.info(
            "TEMPLATE SELECTION: Using GENERAL_CHAT_PROMPT_TEMPLATE for regular conversation")
        try:
            prompt = prompts.GENERAL_CHAT_PROMPT_TEMPLATE.format(
                **template_params)
            logger.info(
                "TEMPLATE CONFIRMATION: Successfully formatted GENERAL_CHAT_PROMPT_TEMPLATE")
            logger.info(f"Used parameters: {list(template_params.keys())}")
            return prompt
        except KeyError as e:
            logger.warning(
                f"Optional parameter missing in general template: {e}, using empty string")
            # Add missing parameter with empty string
            template_params[str(e.args[0])] = ''
            try:
                prompt = prompts.GENERAL_CHAT_PROMPT_TEMPLATE.format(
                    **template_params)
                logger.info(
                    "TEMPLATE CONFIRMATION: Successfully formatted GENERAL_CHAT_PROMPT_TEMPLATE with defaults")
                return prompt
            except Exception as e2:
                logger.error(f"Still failed after adding defaults: {e2}")
                return f"Message: {current_message}\nHistory: {conversation_history}"

    except Exception as e:
        logger.error(f"Error building member chat prompt: {str(e)}")
        return f"Message: {current_message}\nHistory: {conversation_history}"


async def send_manychat_message(subscriber_id: str, message: str) -> bool:
    """Send a message to a ManyChat subscriber."""
    try:
        field_updates = {
            "o1 Response": message
        }
        return update_manychat_fields(subscriber_id, field_updates)
    except Exception as e:
        logger.error(f"Error sending message to ManyChat: {e}")
        return False


# --- Helper Function to Add "To Do" Item --- START ---


# --- Helper Function to Add "To Do" Item --- END ---


# Added subscriber_id
async def detect_and_handle_action(ig_username: str, message_text: str, subscriber_id: Optional[str], data: Dict = None) -> bool:
    """Uses Gemini to detect user intent and handles multiple actions like Trainerize edits or food analysis within one message."""
    logger.info(
        f"[detect_and_handle_action] Analyzing message from {ig_username} (SubID: {subscriber_id}) for multiple actions: {message_text[:100]}"
    )

    if not data:
        logger.error("No data dictionary provided to detect_and_handle_action")
        # If data is missing, we likely don't have subscriber_id either, handle gracefully
        # Fallback to trying lookup by ig_username only, although less reliable
        subscriber_id = None  # Explicitly set to None if data dict is missing

    # --- ONBOARDING CHECK --- START ---
    logger.info(
        f"[detect_and_handle_action] Starting onboarding check for {ig_username} (SubID: {subscriber_id})")

    try:
        # Get user data to check onboarding status, passing subscriber_id
        # Ensure get_user_data returns 3 values: history, metrics, user_id_key
        conversation_history, metrics_dict, user_id_key = get_user_data(
            ig_username, subscriber_id)  # Pass subscriber_id

        if user_id_key:  # Check if user was found
            logger.info(
                f"[detect_and_handle_action] Retrieved metrics for onboarding check: {json.dumps(metrics_dict.get('calorie_tracking', {}), indent=2)}")

            # Check if user is in onboarding
            is_onboarding = metrics_dict.get('is_onboarding', False)
            logger.info(
                f"[detect_and_handle_action] Onboarding status for {ig_username}: {is_onboarding}")

            if is_onboarding:
                logger.info(
                    f"[detect_and_handle_action] User {ig_username} is in onboarding flow")
                # Let the main flow handle onboarding messages, but indicate action was (implicitly) handled
                return True
            else:
                # Existing log might be confusing, clarify it means onboarding *flag* is false/missing
                logger.info(
                    f"[detect_and_handle_action] User {ig_username} is NOT marked as currently onboarding.")
        else:
            # This case means get_user_data failed to find the user
            logger.warning(
                f"[detect_and_handle_action] User not found during onboarding check (ig='{ig_username}', sub='{subscriber_id}'). Cannot check onboarding status.")
            # Continue processing as if not onboarding, as we can't confirm otherwise

    except Exception as e:
        # Catch potential unpacking errors if get_user_data structure changes unexpectedly
        logger.error(
            f"[detect_and_handle_action] Error during onboarding check (potentially unpacking): {str(e)}", exc_info=True)
        # Proceed cautiously, assuming not onboarding if check fails
        pass  # Allow execution to continue to intent detection

    logger.info(
        f"[detect_and_handle_action] Completed onboarding check for {ig_username}")
    # --- ONBOARDING CHECK --- END ---

    intent_prompt = f"""Analyze this message to identify ALL requested actions:
# ... rest of intent_prompt ...
"""
    # ... rest of detect_and_handle_action ...


async def set_manychat_custom_field(subscriber_id: str, field_name: str, field_value: Any, field_id: Optional[int] = None) -> bool:
    """Sets a custom field for a ManyChat subscriber, using field_id if provided."""
    if not MANYCHAT_API_KEY or MANYCHAT_API_KEY == "YOUR_MANYCHAT_API_KEY_HERE":
        logger.error(
            "[ManyChat] MANYCHAT_API_KEY is not configured. Cannot set custom field.")
        return False
    if not subscriber_id:
        logger.error(
            f"[ManyChat] Missing subscriber_id ('{subscriber_id}') for set_manychat_custom_field.")
        return False
    if not field_name and not field_id:
        logger.error(
            f"[ManyChat] Missing both field_name and field_id for set_manychat_custom_field. One must be provided.")
        return False

    api_url = "https://api.manychat.com/fb/subscriber/setCustomField"
    headers = {
        "Authorization": f"Bearer {MANYCHAT_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "subscriber_id": str(subscriber_id),
        "field_value": field_value
    }

    if field_id:
        payload["field_id"] = field_id
        logger.info(
            f"[ManyChat] Attempting to set custom field by ID '{field_id}': {field_value} (type: {type(field_value)}) for subscriber_id: {subscriber_id} via API.")
    elif field_name:  # Fallback to field_name if field_id is not provided
        payload["field_name"] = field_name
        logger.info(
            f"[ManyChat] Attempting to set custom field by NAME '{field_name}': {field_value} (type: {type(field_value)}) for subscriber_id: {subscriber_id} via API.")

    logger.debug(f"[ManyChat] Payload: {json.dumps(payload)}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, headers=headers, json=payload, timeout=15)

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("status") == "success":
                logger.info(
                    f"[ManyChat] Successfully set custom field (ID: {field_id if field_id else 'N/A'}, Name: {field_name if field_name else 'N/A'}) to '{field_value}' for subscriber_id: {subscriber_id}.")
                return True
            else:
                logger.error(
                    f"[ManyChat] API succeeded but returned error status for custom field (ID: {field_id if field_id else 'N/A'}, Name: {field_name if field_name else 'N/A'}) for subscriber_id {subscriber_id}. Response: {response_data}")
                return False
        else:
            logger.error(
                f"[ManyChat] Failed to set custom field (ID: {field_id if field_id else 'N/A'}, Name: {field_name if field_name else 'N/A'}) for subscriber_id {subscriber_id}. Status: {response.status_code}, Response: {response.text[:300]}")
            return False
    except httpx.TimeoutException:
        logger.error(
            f"[ManyChat] Timeout while trying to set custom field (ID: {field_id if field_id else 'N/A'}, Name: {field_name if field_name else 'N/A'}) for {subscriber_id}.")
        return False
    except Exception as e:
        logger.error(
            f"[ManyChat] Exception while trying to set custom field (ID: {field_id if field_id else 'N/A'}, Name: {field_name if field_name else 'N/A'}) for {subscriber_id}: {e}", exc_info=True)
        return False
