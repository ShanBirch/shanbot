"""
Shanbot Webhook - Refactored v2.0
=================================
AI-powered fitness coaching automation webhook for Instagram/ManyChat integration.
Handles workout modifications, form checks, food analysis, and general conversation.
"""

import os
import sys
import json
import time
import asyncio
import logging
import traceback
import functools
import random
import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union

# External dependencies
import uvicorn
import requests
import pytz
import dateutil.parser as parser
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import google.generativeai as genai

# Core Shanbot imports
from webhook_handlers import (
    get_melbourne_time_str, format_conversation_history, split_response_into_messages,
    analyze_media_url, process_conversation_for_media, get_ai_response,
    call_gemini_with_retry, get_user_data, update_analytics_data, add_todo_item,
    build_member_chat_prompt, get_username_from_manychat
)

# Business logic imports
from post_onboarding_handler import PostOnboardingHandler
from calorie_manager_calorietracker import CalorieTracker_CalorieTracker
from calorietracker import get_calorie_analysis
from techniqueanalysis import get_video_analysis
from pb import TrainerizeAutomation

# Dashboard and analytics
from app.dashboard_modules.dashboard_sqlite_utils import (
    add_response_to_review_queue, get_good_few_shot_examples,
    create_scheduled_responses_table_if_not_exists, get_db_connection
)
from app.dashboard_modules.auto_mode_state import is_auto_mode_active, is_vegan_auto_mode_active
from app.dashboard_modules.notifications import add_email_collected_notification
from app import prompts

# Configuration
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("shanbot_webhook")
logger.info("🤖 Shanbot Webhook v2.0 starting up...")

# Windows async fix
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# API Configuration
MANYCHAT_API_KEY = "996573:5b6dc180662de1be343655db562ee918"
GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY", "AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y")
GEMINI_MODEL_PRO = "gemini-2.5-pro-exp-03-25"
GEMINI_MODEL_FLASH = "gemini-2.0-flash-thinking-exp-01-21"
GEMINI_MODEL_FLASH_STANDARD = "gemini-2.0-flash"

try:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("✅ Gemini API configured")
except Exception as e:
    logger.error(f"❌ Gemini configuration failed: {e}")

# Global state
message_buffer: Dict[str, List[Dict]] = defaultdict(list)
manychat_last_bot_sent_timestamps: Dict[str, float] = {}
user_buffer_tasks: Dict[str, asyncio.Task] = {}
form_check_pending: Dict[str, bool] = {}
food_analysis_pending: Dict[str, bool] = {}

BUFFER_WINDOW = 15  # seconds

# FastAPI App
app = FastAPI(title="Shanbot Webhook v2.0", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[
                   "*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_response_time_bucket(time_diff_seconds: float) -> str:
    """Convert time difference to ManyChat response time bucket."""
    if time_diff_seconds <= 120:
        return "response time is 0-2minutes"
    elif time_diff_seconds <= 300:
        return "response time is 2-5 minutes"
    elif time_diff_seconds <= 600:
        return "response time is 5-10 minutes"
    elif time_diff_seconds <= 1200:
        return "response time is 10-20 minutes"
    elif time_diff_seconds <= 1800:
        return "response time is 20-30 minutes"
    elif time_diff_seconds <= 3600:
        return "response time is 30-60 minutes"
    elif time_diff_seconds <= 7200:
        return "response time is 1-2 Hours"
    else:
        return "response time is 2-5 Hours"


def update_manychat_fields(subscriber_id: str, field_updates: Dict[str, str]) -> bool:
    """Update ManyChat custom fields."""
    filtered_updates = {
        k: v for k, v in field_updates.items() if v is not None and v != ""}
    if not filtered_updates:
        return True

    field_data = [{"field_name": field_name, "field_value": value}
                  for field_name, value in filtered_updates.items()]
    data = {"subscriber_id": subscriber_id, "fields": field_data}
    headers = {"Authorization": f"Bearer {MANYCHAT_API_KEY}",
               "Content-Type": "application/json"}

    try:
        response = requests.post("https://api.manychat.com/fb/subscriber/setCustomFields",
                                 headers=headers, json=data, timeout=10)
        response.raise_for_status()
        logger.info(f"✅ Updated ManyChat fields for {subscriber_id}")
        return True
    except Exception as e:
        logger.error(f"❌ ManyChat update failed for {subscriber_id}: {e}")
        return False


async def filter_shannon_response(original_response: str, user_message: str = None) -> str:
    """Filter AI response to match Shannon's authentic voice."""
    filter_prompt = f"""You are ensuring this response sounds like Shannon, a friendly Australian fitness coach.

Original: "{original_response}"
User message: "{user_message or 'N/A'}"

If the response already sounds like a human coach chatting on Instagram with no AI self-references, return it exactly as-is.
If it has AI-like language or meta-commentary, rewrite it in Shannon's casual Aussie style.

Output only the final response:"""

    try:
        filtered = await call_gemini_with_retry(GEMINI_MODEL_FLASH, filter_prompt)
        return filtered.strip() if filtered and filtered.strip() else original_response
    except Exception as e:
        logger.error(f"Response filtering failed: {e}")
        return original_response


def extract_media_url(message_text: str) -> Optional[str]:
    """Extract media URL from message."""
    url_pattern = r"(https?://lookaside\.fbsbx\.com/ig_messaging_cdn/\?asset_id=[\w-]+&signature=[\w\-_.~]+)"
    match = re.search(url_pattern, message_text)
    return match.group(1) if match else None

# ============================================================================
# ACTION HANDLERS
# ============================================================================


class WorkoutHandler:
    """Handles workout program modification requests."""

    @staticmethod
    async def detect_intent(message_text: str) -> Tuple[bool, int, List[Dict]]:
        """Detect workout modification intent."""
        intent_prompt = f"""Analyze this message for workout program changes:
"{message_text}"

Standard workout days: Leg Day, Back day, Chest day, Core Day, Shoulder Day, Cardio Day, Arm Day

Extract workout modifications and return JSON:
{{
    "is_workout_request": boolean,
    "confidence": 0-100,
    "actions": [{{
        "action": "add" or "remove",
        "exercise": "exercise name",
        "workout_type": "workout day category",
        "sets": "3",
        "reps": "10"
    }}]
}}"""

        try:
            response = await call_gemini_with_retry(GEMINI_MODEL_FLASH, intent_prompt)
            # Clean JSON response
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:].strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()

            data = json.loads(cleaned)
            return data.get('is_workout_request', False), data.get('confidence', 0), data.get('actions', [])
        except Exception as e:
            logger.error(f"Workout intent detection failed: {e}")
            return False, 0, []

    @staticmethod
    async def handle(ig_username: str, message_text: str, subscriber_id: str, data: Dict, actions: List[Dict]) -> bool:
        """Execute workout modifications."""
        logger.info(f"🏋️ Processing workout modification for {ig_username}")

        try:
            client_name = data.get(
                'name') or f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
            if not client_name or not actions:
                return False

            # Execute Trainerize automation
            success = await WorkoutHandler._execute_trainerize_changes(ig_username, client_name, actions)

            # Send response
            response = "Easy updated your program, need anything else?" if success else \
                "Yep ill get onto that asap and get back to you when its done!"

            field_updates = {"o1 Response": response,
                             "CONVERSATION": message_text, "response time": "action"}
            update_manychat_fields(subscriber_id, field_updates)
            manychat_last_bot_sent_timestamps[subscriber_id] = time.time()

            return True

        except Exception as e:
            logger.error(f"❌ Workout modification failed: {e}")
            return False

    @staticmethod
    async def _execute_trainerize_changes(ig_username: str, client_name: str, actions: List[Dict]) -> bool:
        """Execute workout changes in Trainerize."""
        trainerize = None
        try:
            trainerize = TrainerizeAutomation()

            if not trainerize.login("shannonbirch@cocospersonaltraining.com", "cyywp7nyk2"):
                raise Exception("Trainerize login failed")

            trainerize.handle_notification_popup()

            if not trainerize.navigate_to_client(client_name):
                raise Exception("Failed to navigate to client")

            if not trainerize.navigate_to_training_program():
                raise Exception("Failed to navigate to training program")

            # Get target workout type from first action
            target_workout_type = actions[0].get(
                'workout_type') if actions else None
            if not target_workout_type:
                raise Exception("No workout type specified")

            if not trainerize.click_workout_fuzzy(target_workout_type):
                raise Exception(
                    f"Failed to find workout: {target_workout_type}")

            if not trainerize.click_edit_workout():
                raise Exception("Failed to enter edit mode")

            # Process each action
            success_count = 0
            for action in actions:
                action_type = action.get('action')
                exercise_name = action.get('exercise')

                if not action_type or not exercise_name:
                    continue

                try:
                    if action_type == 'add':
                        sets = action.get('sets', '3')
                        reps = action.get('reps', '10')
                        if trainerize.add_exercise(exercise_name, sets, reps):
                            success_count += 1
                    elif action_type == 'remove':
                        if trainerize.remove_exercise(exercise_name):
                            success_count += 1
                except Exception as e:
                    logger.error(
                        f"Action failed: {action_type} {exercise_name}: {e}")

            # Save changes
            if success_count > 0 and trainerize.save_workout():
                add_todo_item(ig_username, client_name,
                              f"Updated {success_count} exercises", "completed")
                return True
            else:
                add_todo_item(ig_username, client_name,
                              "Workout update failed")
                return False

        except Exception as e:
            logger.error(f"Trainerize automation error: {e}")
            add_todo_item(ig_username, client_name,
                          f"Trainerize error: {str(e)[:100]}")
            return False
        finally:
            if trainerize:
                trainerize.cleanup()


class FormCheckHandler:
    """Handles form check video analysis requests."""

    @staticmethod
    async def detect_intent(message_text: str) -> Tuple[bool, int]:
        """Detect form check intent."""
        keywords = ['form check', 'check form', 'technique',
                    'review video', 'analyse video', 'look at my lift']
        message_lower = message_text.lower()

        if any(keyword in message_lower for keyword in keywords):
            return True, 85

        # Use Gemini for more nuanced detection
        intent_prompt = f"""Is this a request for form/technique analysis of an exercise video?
Message: "{message_text}"
Reply with just "YES" or "NO" and confidence 0-100."""

        try:
            response = await call_gemini_with_retry(GEMINI_MODEL_FLASH, intent_prompt)
            is_form_check = "YES" in response.upper()
            confidence = 75 if is_form_check else 25
            return is_form_check, confidence
        except:
            return False, 0

    @staticmethod
    async def handle(ig_username: str, message_text: str, subscriber_id: str, data: Dict) -> bool:
        """Handle form check request."""
        logger.info(f"📹 Processing form check for {ig_username}")

        video_url = extract_media_url(message_text)
        client_name = data.get('name', ig_username)

        if video_url:
            # Analyze video immediately
            form_check_pending.pop(ig_username, None)  # Clear pending flag
            return await FormCheckHandler._analyze_video(ig_username, client_name, video_url, message_text, subscriber_id)
        else:
            # Request video
            form_check_pending[ig_username] = True
            responses = ["Would love to, Send it through!", "Yeah keen! Flick it over.",
                         "Sweet, send it my way.", "Sure thing, let's see it."]

            field_updates = {"o1 Response": random.choice(
                responses), "CONVERSATION": message_text, "response time": "action"}
            update_manychat_fields(subscriber_id, field_updates)
            manychat_last_bot_sent_timestamps[subscriber_id] = time.time()
            return True

    @staticmethod
    async def _analyze_video(ig_username: str, client_name: str, video_url: str, description: str, subscriber_id: str) -> bool:
        """Analyze form check video."""
        try:
            analysis = get_video_analysis(
                video_url, GEMINI_API_KEY, GEMINI_MODEL_PRO, GEMINI_MODEL_FLASH, GEMINI_MODEL_FLASH_STANDARD)

            if analysis and "error" not in analysis.lower():
                response = analysis
                add_todo_item(ig_username, client_name,
                              f"Form check completed: {video_url[:50]}...", "completed")
            else:
                response = "Sorry mate, had trouble analyzing that video. Can you try sending it again?"
                add_todo_item(ig_username, client_name,
                              f"Form check failed: {video_url[:50]}...")

            field_updates = {"o1 Response": response,
                             "CONVERSATION": f"(Video: {video_url[:50]}...)", "response time": "action"}
            update_manychat_fields(subscriber_id, field_updates)
            manychat_last_bot_sent_timestamps[subscriber_id] = time.time()
            return True

        except Exception as e:
            logger.error(f"❌ Form check analysis failed: {e}")
            return False


class FoodAnalysisHandler:
    """Handles food/calorie analysis requests."""

    @staticmethod
    async def detect_intent(message_text: str) -> Tuple[bool, int]:
        """Detect food analysis intent."""
        keywords = ['calories', 'macros', 'check food',
                    'analyse meal', 'protein', 'carbs', 'fat', 'food pic']
        message_lower = message_text.lower()

        if any(keyword in message_lower for keyword in keywords):
            return True, 80
        return False, 0

    @staticmethod
    async def handle(ig_username: str, message_text: str, subscriber_id: str, data: Dict) -> bool:
        """Handle food analysis request."""
        logger.info(f"🍎 Processing food analysis for {ig_username}")

        image_url = extract_media_url(message_text)
        client_name = data.get('name', ig_username)

        if image_url:
            # Analyze food immediately
            food_analysis_pending.pop(ig_username, None)  # Clear pending flag
            return await FoodAnalysisHandler._analyze_food(ig_username, client_name, image_url, message_text, subscriber_id)
        else:
            # Request photo
            food_analysis_pending[ig_username] = True
            response = "Yep send the photo through, and a brief description of the ingredients used will help as well"

            field_updates = {"o1 Response": response,
                             "CONVERSATION": message_text, "response time": "action"}
            update_manychat_fields(subscriber_id, field_updates)
            manychat_last_bot_sent_timestamps[subscriber_id] = time.time()
            return True

    @staticmethod
    async def _analyze_food(ig_username: str, client_name: str, image_url: str, description: str, subscriber_id: str) -> bool:
        """Analyze food image for calories and macros."""
        try:
            # Get description without URL
            clean_description = description.replace(image_url, "").strip()

            # Get calorie analysis
            analysis = get_calorie_analysis(image_url, GEMINI_API_KEY, GEMINI_MODEL_PRO,
                                            GEMINI_MODEL_FLASH, GEMINI_MODEL_FLASH_STANDARD,
                                            user_description=clean_description)

            if analysis and "error" not in analysis.lower():
                # Process with calorie tracker
                tracker = CalorieTracker_CalorieTracker()
                response_part1, response_part2 = tracker.handle_food_analysis_webhook(
                    ig_username=ig_username, analysis_text=analysis, description=clean_description)

                # Send first response
                field_updates = {"o1 Response": response_part1,
                                 "CONVERSATION": f"(Food: {image_url[:50]}...)", "response time": "action"}
                update_manychat_fields(subscriber_id, field_updates)

                # Send second response if available
                if response_part2:
                    await asyncio.sleep(2)
                    update_manychat_fields(
                        subscriber_id, {"o1 Response 2": response_part2})

                manychat_last_bot_sent_timestamps[subscriber_id] = time.time()
                add_todo_item(ig_username, client_name,
                              f"Food analysis completed: {image_url[:50]}...", "completed")

            else:
                response = "Sorry mate, had trouble analyzing that food pic. Can you try again?"
                field_updates = {
                    "o1 Response": response, "CONVERSATION": f"(Food: {image_url[:50]}...)", "response time": "action"}
                update_manychat_fields(subscriber_id, field_updates)
                manychat_last_bot_sent_timestamps[subscriber_id] = time.time()
                add_todo_item(ig_username, client_name,
                              f"Food analysis failed: {image_url[:50]}...")

            return True

        except Exception as e:
            logger.error(f"❌ Food analysis failed: {e}")
            return False

# ============================================================================
# CORE MESSAGE PROCESSING
# ============================================================================


async def detect_and_handle_action(ig_username: str, message_text: str, subscriber_id: str, data: Dict, batch_start_time_s: float) -> bool:
    """Detect and route user actions to appropriate handlers."""
    logger.info(
        f"🔍 Analyzing message from {ig_username}: {message_text[:100]}...")

    try:
        # Handle pending form checks first (highest priority)
        if form_check_pending.get(ig_username) and extract_media_url(message_text):
            form_check_pending.pop(ig_username, None)
            return await FormCheckHandler.handle(ig_username, message_text, subscriber_id, data)

        # Handle pending food analysis
        if food_analysis_pending.get(ig_username) and extract_media_url(message_text):
            return await FoodAnalysisHandler.handle(ig_username, message_text, subscriber_id, data)

        # Detect workout modifications
        is_workout, workout_confidence, workout_actions = await WorkoutHandler.detect_intent(message_text)
        if is_workout and workout_confidence > 70:
            return await WorkoutHandler.handle(ig_username, message_text, subscriber_id, data, workout_actions)

        # Detect form check requests
        is_form_check, form_confidence = await FormCheckHandler.detect_intent(message_text)
        if is_form_check and form_confidence > 70:
            return await FormCheckHandler.handle(ig_username, message_text, subscriber_id, data)

        # Detect food analysis requests
        is_food_analysis, food_confidence = await FoodAnalysisHandler.detect_intent(message_text)
        if is_food_analysis and food_confidence > 70:
            return await FoodAnalysisHandler.handle(ig_username, message_text, subscriber_id, data)

        return False  # No specific action detected, use general AI

    except Exception as e:
        logger.error(f"❌ Action detection failed for {ig_username}: {e}")
        return False


async def handle_general_conversation(ig_username: str, message: str, subscriber_id: str, data: Dict, metrics: Dict, batch_start_time: float):
    """Handle general conversation using AI with auto/manual routing."""
    try:
        # Get user context
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip() or ig_username

        current_stage = metrics.get('journey_stage', {}).get(
            'current_stage', "Topic 1")
        trial_status = metrics.get('trial_status', "Initial Contact")

        # Get few-shot examples
        few_shot_examples = get_good_few_shot_examples(limit=50)

        # Build AI prompt
        conversation_history = format_conversation_history(
            metrics.get('conversation_history', []))
        prompt, prompt_type = build_member_chat_prompt(
            client_data=metrics, current_message=message, current_stage=current_stage,
            trial_status=trial_status, full_name=full_name,
            full_conversation_string=conversation_history, few_shot_examples=few_shot_examples
        )

        # Generate AI response
        ai_response = await get_ai_response(prompt)
        if not ai_response:
            logger.error(f"❌ No AI response for {ig_username}")
            return

        # Filter response
        ai_response = await filter_shannon_response(ai_response, message)

        # Check auto mode
        should_auto_send = await check_auto_mode(ig_username)

        if should_auto_send:
            await send_immediate_response(subscriber_id, ai_response, message, batch_start_time)
        else:
            await queue_for_review(ig_username, subscriber_id, message, ai_response, prompt, prompt_type, batch_start_time)

    except Exception as e:
        logger.error(f"❌ General conversation failed: {e}")


async def check_auto_mode(ig_username: str) -> bool:
    """Check if auto mode is active."""
    try:
        if is_auto_mode_active():
            return True

        if is_vegan_auto_mode_active():
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT is_fresh_vegan FROM conversation_strategy_log WHERE username = ? AND is_fresh_vegan = 1 LIMIT 1", (ig_username,))
            result = cursor.fetchone()
            conn.close()
            return bool(result)

        return False
    except:
        return False


async def send_immediate_response(subscriber_id: str, ai_response: str, user_message: str, batch_start_time: float):
    """Send AI response immediately (auto mode)."""
    try:
        # Calculate response time
        last_bot_time = manychat_last_bot_sent_timestamps.get(
            subscriber_id, batch_start_time)
        time_diff = batch_start_time - last_bot_time
        response_time_bucket = get_response_time_bucket(time_diff)

        # Send response time first
        update_manychat_fields(
            subscriber_id, {"response time": response_time_bucket})
        await asyncio.sleep(1)

        # Split and send response
        response_parts = split_response_into_messages(ai_response)
        field_names = ["o1 Response", "o1 Response 2", "o1 Response 3"]

        for i, part in enumerate(response_parts[:len(field_names)]):
            field_updates = {field_names[i]: part}
            if i == 0:
                field_updates["CONVERSATION"] = user_message

            update_manychat_fields(subscriber_id, field_updates)

            if i < len(response_parts) - 1:
                await asyncio.sleep(random.uniform(1, 3))

        manychat_last_bot_sent_timestamps[subscriber_id] = time.time()
        logger.info(f"📤 Sent immediate response to {subscriber_id}")

    except Exception as e:
        logger.error(f"❌ Failed to send immediate response: {e}")


async def queue_for_review(ig_username: str, subscriber_id: str, user_message: str, ai_response: str, prompt: str, prompt_type: str, batch_start_time: float):
    """Queue response for manual review."""
    try:
        review_id = add_response_to_review_queue(
            user_ig_username=ig_username, user_subscriber_id=subscriber_id,
            incoming_message_text=user_message, incoming_message_timestamp=datetime.fromtimestamp(
                batch_start_time).isoformat(),
            generated_prompt_text=prompt, proposed_response_text=ai_response, prompt_type=prompt_type
        )

        if review_id:
            logger.info(
                f"📝 Queued response for review (ID: {review_id}) for @{ig_username}")
        else:
            logger.error(f"❌ Failed to queue response for @{ig_username}")

    except Exception as e:
        logger.error(f"❌ Failed to queue response: {e}")

# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================


@app.post("/webhook/manychat")
async def process_manychat_webhook(request: Request, background_tasks: BackgroundTasks):
    """Main ManyChat webhook processor."""
    try:
        # Parse request
        raw_body = await request.body()
        data = json.loads(raw_body.decode('utf-8'))

        # Extract subscriber ID
        subscriber_id = data.get("id") or data.get("subscriber", {}).get("id")
        if not subscriber_id:
            logger.error("❌ No subscriber ID in payload")
            return PlainTextResponse("Error: Subscriber ID missing", status_code=400)

        # Extract Instagram username
        ig_username = await extract_ig_username(data, subscriber_id)

        logger.info(f"📨 Webhook: {subscriber_id} (@{ig_username})")

        # Add to message buffer
        user_message_created_at = data.get("created_at", time.time())
        message_buffer[subscriber_id].append(
            {"payload": data, "timestamp": user_message_created_at})

        # Cancel existing processing task and schedule new one
        if subscriber_id in user_buffer_tasks:
            try:
                user_buffer_tasks[subscriber_id].cancel()
            except:
                pass

        # Schedule processing after buffer window
        task = background_tasks.add_task(
            process_buffered_messages, subscriber_id, ig_username)
        user_buffer_tasks[subscriber_id] = task

        logger.info(
            f"⏰ Buffering message for {BUFFER_WINDOW}s: {subscriber_id}")
        return PlainTextResponse("Webhook received", status_code=200)

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def extract_ig_username(data: Dict, subscriber_id: str) -> str:
    """Extract Instagram username with fallbacks."""
    # Try direct fields
    username = data.get("ig_username")
    if username and username.strip() and not username.startswith('user_'):
        return username.strip()

    # Try subscriber data
    subscriber_data = data.get("subscriber", {})
    for field in ["name", "user_name"]:
        username = subscriber_data.get(field)
        if username and username.strip() and not username.startswith('user_'):
            return username.strip()

    # Try custom fields
    custom_fields = subscriber_data.get("custom_fields", {})
    username = custom_fields.get("ig_username")
    if username and username.strip() and not username.startswith('user_'):
        return username.strip()

    # Try ManyChat API
    try:
        api_username = await get_username_from_manychat(subscriber_id)
        if api_username and not api_username.startswith('user_'):
            return api_username
    except Exception as e:
        logger.warning(f"API username fetch failed: {e}")

    return f"user_{subscriber_id}"


async def process_buffered_messages(subscriber_id: str, ig_username: str):
    """Process accumulated messages after buffer window."""
    try:
        await asyncio.sleep(BUFFER_WINDOW)

        # Get buffered messages
        messages = message_buffer.pop(subscriber_id, [])
        if not messages:
            return

        logger.info(
            f"🔄 Processing {len(messages)} messages for @{ig_username}")

        # Combine messages
        combined_text, latest_payload = combine_messages(messages)
        batch_start_time = messages[0]["timestamp"]

        # Get user data
        conversation_history, metrics, user_id = get_user_data(
            ig_username, subscriber_id)

        # Process message
        processed_message = process_conversation_for_media(combined_text)

        # Try action handlers first
        action_handled = await detect_and_handle_action(ig_username, combined_text, subscriber_id, latest_payload, batch_start_time)

        if not action_handled:
            # Handle with general AI
            await handle_general_conversation(ig_username, processed_message, subscriber_id, latest_payload, metrics, batch_start_time)

        # Update analytics
        update_analytics_data(
            ig_username=ig_username, user_message=processed_message,
            ai_response="[Action handled]" if action_handled else "[AI response queued]",
            subscriber_id=subscriber_id, first_name=latest_payload.get(
                "first_name", ""),
            last_name=latest_payload.get("last_name", ""),
            user_message_timestamp=datetime.fromtimestamp(
                batch_start_time).isoformat()
        )

        logger.info(f"✅ Completed processing for @{ig_username}")

    except Exception as e:
        logger.error(f"❌ Buffer processing failed: {e}")
    finally:
        user_buffer_tasks.pop(subscriber_id, None)


def combine_messages(messages: List[Dict]) -> Tuple[str, Dict]:
    """Combine multiple messages intelligently."""
    if len(messages) == 1:
        text = messages[0]["payload"].get("last_input_text", "")
        return text, messages[0]["payload"]

    # Handle duplicates
    message_counts = {}
    unique_messages = []

    for msg in messages:
        text = msg["payload"].get("last_input_text", "").strip()
        if text:
            if text in message_counts:
                message_counts[text] += 1
            else:
                message_counts[text] = 1
                unique_messages.append(text)

    # Format with counts
    formatted_parts = []
    for msg in unique_messages:
        count = message_counts[msg]
        formatted_parts.append(f"[{count}x] {msg}" if count > 1 else msg)

    return " ".join(formatted_parts), messages[-1]["payload"]

# Health endpoints


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0", "timestamp": datetime.now().isoformat()}


@app.get("/")
async def root():
    return {"service": "Shanbot Webhook v2.0", "status": "operational", "docs": "/docs"}


@app.get("/test")
async def test():
    return {"status": "ok", "message": "Webhook test successful", "timestamp": datetime.now().isoformat()}

# Startup


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Shanbot Webhook v2.0 ready!")
    try:
        conn = get_db_connection()
        create_scheduled_responses_table_if_not_exists(conn)
        conn.close()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting Shanbot Webhook v2.0...")
    uvicorn.run("webhook_refactored:app",
                host="0.0.0.0", port=8000, reload=True)
