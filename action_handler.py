# action_handler.py
import json
import logging
from datetime import datetime
import os
import random
import re
import subprocess
import time
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field
from fastapi import Request, BackgroundTasks

# --- Placeholder for imports from our new utilities module ---
from utilities import (
    call_gemini_with_retry,
    get_user_data,
    update_analytics_data,
    add_todo_item,
    update_manychat_fields,
    get_video_analysis,
    get_db_connection,
    get_username_from_manychat,
    add_response_to_review_queue,
    schedule_auto_response,
    is_auto_mode_active,
    is_vegan_auto_mode_active
)
from fastapi.responses import JSONResponse
from calorietracker import get_calorie_analysis
# This class might be better in a dedicated 'services' or 'integrations' module
from pb import TrainerizeAutomation

# Add fallback for missing CalorieTracker class
try:
    from calorietracker import CalorieTracker_CalorieTracker
except ImportError:
    # Fallback class if calorietracker module is not available
    class CalorieTracker_CalorieTracker:
        def __init__(self, *args, **kwargs):
            pass

        def analyze_food_image(self, *args, **kwargs):
            return "Calorie tracker not available"

logger = logging.getLogger("action_handler")

# --- Globals for State Tracking ---
form_check_pending: Dict[str, bool] = {}
food_analysis_pending: Dict[str, bool] = {}

# --- Pydantic Models for Trainerize ---


class ExerciseDefinition(BaseModel):
    name: str
    sets: str
    reps: str


class WorkoutDefinition(BaseModel):
    day_type: str = Field(
        ..., description="Supported: 'back', 'chest_tris', 'shoulders_core', 'legs', 'arms_core'.")
    exercises_list: List[ExerciseDefinition]


class BuildProgramRequest(BaseModel):
    client_name: str
    program_name: str
    workout_definitions: List[WorkoutDefinition]

# --- Main Action Detection Function ---


async def detect_and_handle_action(
    ig_username: str,
    message_text: str,
    subscriber_id: Optional[str],
    data: Dict,
    batch_start_time_s: float
) -> bool:
    """
    Analyzes user message for specific intents (workout changes, form checks, food analysis, etc.)
    and handles them directly. Returns True if an action was handled, False otherwise.
    """
    logger.info(
        f"Analyzing message from {ig_username} for actionable intents.")

    # Simplified intent detection prompt
    intent_prompt = f"""
    Analyze the message to identify key actions. Respond with a JSON object.
    Message: "{message_text}"
    Actions to detect:
    1.  `is_workout_request`: User wants to modify their workout program.
    2.  `is_form_check_request`: User wants a technique analysis from a video.
    3.  `is_food_analysis_request`: User wants calorie/macro analysis from a photo.
    4.  `is_ad_response`: User is responding to a 'Plant-Based Challenge' ad.

    Output ONLY a valid JSON object like:
    {{
        "is_workout_request": boolean,
        "is_form_check_request": boolean,
        "is_food_analysis_request": boolean,
        "is_ad_response": boolean,
        "confidence": 0-100
    }}
    """
    try:
        # Use a fast model for initial intent detection
        intent_response_str = await call_gemini_with_retry("gemini-2.5-flash-lite", intent_prompt)
        # Extract JSON from the response string
        json_match = re.search(r'\{.*\}', intent_response_str, re.DOTALL)
        if not json_match:
            logger.warning(
                f"Could not find JSON in intent response for '{message_text[:50]}...'")
            return False

        intent_data = json.loads(json_match.group())
        logger.info(f"Intent analysis result: {intent_data}")

        confidence = intent_data.get('confidence', 0)
        if confidence < 75:
            logger.info(
                "Intent confidence below 75%, skipping dedicated action handlers.")
            return False

        # Route to the correct handler based on intent
        if intent_data.get('is_workout_request'):
            # Placeholder for workout change logic
            logger.info(
                "Workout request detected. (Handler not fully implemented in this refactor).")
            # return await handle_workout_request(...)
            return False  # Returning false until fully implemented

        elif intent_data.get('is_form_check_request'):
            return await handle_form_check_request(ig_username, message_text, subscriber_id, data, batch_start_time_s)

        elif intent_data.get('is_food_analysis_request'):
            return await handle_food_analysis_request(ig_username, message_text, subscriber_id, data)

        elif intent_data.get('is_ad_response'):
            return await handle_ad_response(ig_username, message_text, subscriber_id, data, batch_start_time_s)

        return False

    except Exception as e:
        logger.error(f"Error in detect_and_handle_action: {e}", exc_info=True)
        return False

# --- Specific Action Handlers ---


async def handle_form_check_request(ig_username, message_text, subscriber_id, data, batch_start_time_s) -> bool:
    """Handles logic for form check video analysis."""
    logger.info(f"Handling form check request for {ig_username}.")
    video_url_match = re.search(
        r"(https?://lookaside\.fbsbx\.com\S+)", message_text)

    if video_url_match:
        video_url = video_url_match.group(1)
        user_desc = message_text.replace(video_url, "").strip()

        analysis_result = get_video_analysis(
            video_url, os.getenv("GEMINI_API_KEY"))

        response_to_user = analysis_result if analysis_result and "error" not in analysis_result.lower(
        ) else "Sorry, couldn't analyze the video. Please try sending it again."

        update_manychat_fields(
            subscriber_id, {"o1 Response": response_to_user})
        update_analytics_data(ig_username, message_text, response_to_user,
                              subscriber_id, data.get('first_name'), data.get('last_name'))

        form_check_pending.pop(ig_username, None)  # Clear pending state
        return True

    else:  # No video in the message
        if not form_check_pending.get(ig_username):
            form_check_pending[ig_username] = True
            response_text = random.choice(
                ["Would love to, Send it through!", "Yeah keen! Flick it over.", "Sweet, send it my way."])
            update_manychat_fields(
                subscriber_id, {"o1 Response": response_text})
            update_analytics_data(ig_username, message_text, response_text, subscriber_id, data.get(
                'first_name'), data.get('last_name'))
            return True
        else:
            # Already asked for video, but they sent text again. Let general AI handle.
            return False


async def handle_food_analysis_request(ig_username, message_text, subscriber_id, data) -> bool:
    """Handles logic for food photo calorie analysis."""
    logger.info(f"Handling food analysis request for {ig_username}.")
    image_url_match = re.search(
        r"(https?://lookaside\.fbsbx\.com\S+)", message_text)

    if image_url_match:
        image_url = image_url_match.group(1)
        user_desc = message_text.replace(image_url, "").strip()

        # Use the calorietracker signature (with model fallbacks)
        analysis_result = get_calorie_analysis(
            image_url=image_url,
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            primary_model="gemini-2.5-flash-lite",
            first_fallback_model="gemini-2.0-flash",
            second_fallback_model="gemini-2.0-flash-thinking-exp-01-21",
            user_description=user_desc
        )

        if analysis_result and "error" not in analysis_result.lower():
            tracker = CalorieTracker_CalorieTracker()
            part1, part2 = tracker.handle_food_analysis_webhook(
                ig_username, analysis_result, user_desc)
            update_manychat_fields(subscriber_id, {"o1 Response": part1})
            if part2:
                # Use a background task to send the second message after a short delay
                # This requires access to background_tasks, which might need to be passed down.
                # For simplicity here, we send it directly.
                time.sleep(2)
                update_manychat_fields(subscriber_id, {"o1 Response 2": part2})

            update_analytics_data(ig_username, message_text, f"{part1} | {part2}", subscriber_id, data.get(
                'first_name'), data.get('last_name'))

        else:
            error_msg = "Sorry mate, had a bit of trouble analysing that pic. Can you try sending it again?"
            update_manychat_fields(subscriber_id, {"o1 Response": error_msg})
            update_analytics_data(ig_username, message_text, error_msg, subscriber_id, data.get(
                'first_name'), data.get('last_name'))

        food_analysis_pending.pop(ig_username, None)
        return True

    else:  # No image in message
        if not food_analysis_pending.get(ig_username):
            food_analysis_pending[ig_username] = True
            response_text = "Yep send the photo through, and a brief description of the ingredients used will help as well"
            update_manychat_fields(
                subscriber_id, {"o1 Response": response_text})
            update_analytics_data(ig_username, message_text, response_text, subscriber_id, data.get(
                'first_name'), data.get('last_name'))
            return True
        else:
            return False


async def handle_ad_response(ig_username, message_text, subscriber_id, data, batch_start_time_s) -> bool:
    """Handles responses from users who clicked on a paid ad."""
    logger.info(f"Handling ad response for {ig_username}.")

    # Get user data to check ad flow state
    _, metrics, _ = get_user_data(ig_username, subscriber_id)

    # Mark user as being in the ad flow
    # In a real scenario, this would be more robust
    ad_script_state = metrics.get('ad_script_state', 'step1')

    # This prompt can be moved to a separate prompts.py file
    ad_prompt = f"""
    You are Shannon, a friendly fitness coach. A potential client, {ig_username}, has responded to your Plant-Based Challenge ad.
    Your goal is to guide them to book a call.
    Their message: "{message_text}"
    Conversation history: {metrics.get('conversation_history', [])}
    Current script step: {ad_script_state}

    Based on the step, continue the conversation naturally.
    - Step 1: Acknowledge their interest and ask about their fitness goals.
    - Step 2: Relate to their goal and briefly explain how the challenge helps.
    - Step 3: Encourage them to book a free discovery call to discuss further.
    
    Your response:
    """

    ai_response = await call_gemini_with_retry("gemini-2.5-flash-lite", ad_prompt)
    if not ai_response:
        return False

    user_message_timestamp_iso = datetime.fromtimestamp(
        batch_start_time_s).isoformat()

    # Ad responses from paying customers should always be reviewed
    logger.info(f"Queuing ad response for {ig_username} for manual review.")
    add_response_to_review_queue(
        user_ig_username=ig_username,
        user_subscriber_id=subscriber_id,
        incoming_message_text=message_text,
        incoming_message_timestamp=user_message_timestamp_iso,
        generated_prompt_text=ad_prompt,
        proposed_response_text=ai_response,
        prompt_type="plant_based_ad_response"
    )

    # Update analytics and advance state
    next_state = f"step{int(ad_script_state[-1]) + 1}" if 'step' in ad_script_state else 'completed'
    update_analytics_data(
        ig_username,
        message_text,
        ai_response,
        subscriber_id,
        data.get('first_name'),
        data.get('last_name'),
        is_in_ad_flow=True,
        ad_script_state=next_state
    )

    return True  # We've handled this by queueing it for review


async def check_and_trigger_bio_analysis(ig_username: str, subscriber_id: Optional[str] = None):
    """Checks if a user's Instagram bio has been analyzed and triggers it if not."""
    # (This function's implementation remains largely the same but relies on utilities)
    logger.info(f"Checking bio analysis status for {ig_username}")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT bio_analysis_status FROM users WHERE ig_username = ?", (ig_username,))
    status_result = cursor.fetchone()
    conn.close()

    if status_result and status_result[0] in ['completed', 'failed_private_profile']:
        logger.info(
            f"Skipping analysis for {ig_username}, status is '{status_result[0]}'")
        return

    logger.info(f"Triggering Instagram analysis for {ig_username}")
    # The command to run the external script
    analyzer_script_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\anaylize_followers.py"
    if not os.path.exists(analyzer_script_path):
        logger.error(f"Analyzer script not found: {analyzer_script_path}")
        return

    cmd = ["python", analyzer_script_path, "--direct-user", ig_username]

    # Run in a non-blocking way
    subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
    logger.info(f"Started analysis for {ig_username} in a new process.")

# (Wix processing logic would also go here)


async def process_wix_form_submission(request: Request, background_tasks: BackgroundTasks):
    # This function would contain the logic from the original `process_wix_form_submission`
    # and would call helper functions that should be moved to `utilities.py`.
    logger.info(
        "Wix form submission received. (Handler not fully implemented in this refactor).")
    return JSONResponse(content={"status": "received"}, status_code=200)
