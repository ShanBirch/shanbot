"""Main webhook handler and FastAPI application."""

import json
import logging
import os
import uvicorn
import asyncio
import time
import pytz
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from app import prompts

from user_management import (
    update_manychat_fields,
    update_analytics_data,
    find_latest_checkin_file,
    load_json_data,
    format_conversation_history
)
from action_handlers import (
    detect_and_handle_action,
    call_gemini_with_retry,
    form_check_pending,
    food_analysis_pending
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("manychat_webhook")
logger.info("Logging configured.")

# Constants
GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY", "AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y")
GEMINI_MODEL_PRO = "gemini-2.5-pro-exp-03-25"
GEMINI_MODEL_FLASH = "gemini-2.0-flash-thinking-exp-01-21"
GEMINI_MODEL_FLASH_STANDARD = "gemini-2.0-flash"

# Configure Gemini
if not GEMINI_API_KEY:
    logger.warning(
        "GEMINI_API_KEY environment variable not set. Gemini calls will fail.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {e}", exc_info=True)

# FastAPI app setup
app = FastAPI(title="Instagram Webhook Receiver")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global message handling
message_buffer = {}
last_message_timestamps: Dict[str, float] = {}
last_bot_reply_timestamps: Dict[str, float] = {}


def get_melbourne_time_str():
    """Get current Melbourne time with error handling."""
    try:
        melbourne_tz = pytz.timezone('Australia/Melbourne')
        current_time = datetime.now(melbourne_tz)
        return current_time.strftime("%Y-%m-%d %I:%M %p AEST")
    except Exception as e:
        logger.error(f"Error getting Melbourne time: {e}")
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def split_response_into_messages(text: str) -> List[str]:
    """Split response text into up to 3 messages of roughly equal length."""
    logger.info(f"Splitting response of length {len(text)}")

    if len(text) <= 150:
        return [text]

    sentences = text.split('. ')
    if len(sentences) <= 2:
        return sentences

    result = []
    current_message = ""
    target_length = len(text) / 3

    for sentence in sentences:
        if len(current_message) + len(sentence) <= target_length or not current_message:
            if current_message:
                current_message += ". "
            current_message += sentence
        else:
            result.append(current_message + ".")
            current_message = sentence

            if len(result) == 2:
                result.append(current_message + ". " +
                              ". ".join(sentences[sentences.index(sentence)+1:]))
                break

    if current_message and len(result) < 3:
        result.append(current_message + ".")

    return result


async def process_general_chat(ig_username: str, message_text: str, data: Dict) -> bool:
    """Process a message as general chat when no specific action is detected."""
    try:
        # Get user data for context
        subscriber_id = data.get('id')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        # Build prompt context
        current_time = get_melbourne_time_str()

        # Check if user is in check-in flow
        is_in_checkin_flow = False
        checkin_type = None
        checkin_data = None

        # Load check-in data if in check-in flow
        if is_in_checkin_flow:
            full_name = f"{first_name} {last_name}".strip() or ig_username
            latest_checkin_file = find_latest_checkin_file(full_name)
            if latest_checkin_file:
                checkin_data = load_json_data(latest_checkin_file)

        # Select appropriate prompt template
        if is_in_checkin_flow and checkin_data:
            if checkin_type == 'monday':
                prompt_template = prompts.CHECKIN_PROMPT_TEMPLATE_MON
            elif checkin_type == 'wednesday':
                prompt_template = prompts.CHECKIN_PROMPT_TEMPLATE_WED
            else:
                prompt_template = prompts.GENERAL_CHAT_PROMPT_TEMPLATE
        else:
            prompt_template = prompts.GENERAL_CHAT_PROMPT_TEMPLATE

        # Format prompt with available data
        prompt = prompt_template.format(
            current_melbourne_time_str=current_time,
            ig_username=ig_username,
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}".strip() or ig_username,
            message=message_text,
            # Add other required fields with defaults
            bio="",
            interests="[]",
            topics_str="No topics yet",
            fitness_goals="",
            dietary_requirements="",
            training_frequency="",
            current_stage="Topic 1",
            trial_status="Initial Contact",
            full_conversation=message_text
        )

        # Get AI response
        response = call_gemini_with_retry(GEMINI_MODEL_PRO, prompt)
        if not response:
            logger.error(f"Failed to get AI response for {ig_username}")
            return False

        # Update ManyChat
        field_updates = {
            "o1 Response": response,
            "CONVERSATION": message_text
        }
        update_success = update_manychat_fields(subscriber_id, field_updates)
        if not update_success:
            logger.error(f"Failed to update ManyChat fields for {ig_username}")
            return False

        # Update analytics
        update_analytics_data(
            ig_username=ig_username,
            user_message=message_text,
            ai_response=response,
            subscriber_id=subscriber_id,
            first_name=first_name,
            last_name=last_name
        )

        return True

    except Exception as e:
        logger.error(f"Error in process_general_chat: {e}", exc_info=True)
        return False


async def schedule_response(sender_id: str, initial_delay_to_use: int):
    """Schedule and process a delayed response to a user message."""
    try:
        target_total_wait = initial_delay_to_use
        user_response_time_seconds = 0

        user_message_arrival_ts = last_message_timestamps.get(sender_id)
        last_bot_reply_ts = last_bot_reply_timestamps.get(sender_id)

        if user_message_arrival_ts and last_bot_reply_ts:
            user_response_time_seconds = user_message_arrival_ts - last_bot_reply_ts
            user_response_time_seconds = max(0, user_response_time_seconds)
            target_total_wait = max(
                initial_delay_to_use, user_response_time_seconds)

        logger.info(
            f"[schedule_response] Base Delay: {initial_delay_to_use}s, User Response Time: {user_response_time_seconds:.1f}s. Target Total Wait: {target_total_wait:.1f}s")

        await asyncio.sleep(target_total_wait)
        logger.info(
            f"[schedule_response] Woke up after {target_total_wait:.1f}s total wait for {sender_id}.")

        messages = message_buffer.pop(sender_id, [])
        if not messages:
            logger.info(
                f"No messages left in buffer for {sender_id} after delay.")
            return

        full_message = ' '.join(msg.get('last_input_text', '')
                                for msg in messages)
        logger.info(
            f"Processing combined message for {sender_id}: '{full_message}'")

        # First try action detection
        action_handled = await detect_and_handle_action(sender_id, full_message, messages[0])
        if action_handled:
            logger.info(f"Message handled by action detection for {sender_id}")
            return

        # If no action detected, process as general chat
        chat_handled = await process_general_chat(sender_id, full_message, messages[0])
        if not chat_handled:
            logger.error(f"Failed to process general chat for {sender_id}")
            try:
                await update_manychat_fields(sender_id, {
                    "o1 Response": "Sorry, I'm having trouble processing your message right now. Please try again later.",
                    "CONVERSATION": full_message
                })
            except Exception as e:
                logger.error(
                    f"Failed to send error message to {sender_id}: {e}")

    except asyncio.CancelledError:
        logger.info(f"Response task for {sender_id} was cancelled.")
    except Exception as e:
        logger.error(
            f"Error in scheduled response task for {sender_id}: {e}", exc_info=True)
        try:
            await update_manychat_fields(sender_id, {
                "o1 Response": "Sorry, something went wrong on my end. Please try again later.",
                "CONVERSATION": "Error processing message"
            })
        except Exception as send_err:
            logger.error(
                f"Failed to send error message to {sender_id}: {send_err}")


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint that redirects to health check"""
    logger.info("Root endpoint accessed")
    return {"status": "Shanbot API running", "message": "Use /webhook endpoints for functionality"}


@app.get("/debug")
async def debug_endpoint(request: Request):
    """Debug endpoint that returns all query parameters and headers"""
    query_params = dict(request.query_params)
    headers = dict(request.headers)

    logger.info(f"DEBUG ENDPOINT ACCESSED - Query params: {query_params}")

    if "hub.mode" in query_params and "hub.verify_token" in query_params and "hub.challenge" in query_params:
        mode = query_params.get("hub.mode")
        token = query_params.get("hub.verify_token")
        challenge = query_params.get("hub.challenge")

        logger.info(
            f"DEBUG: Facebook verification detected! Mode: {mode}, Token: {token}, Challenge: {challenge}")

        verify_token = "Shanbotcyywp7nyk"
        if mode == "subscribe" and token == verify_token:
            logger.info("DEBUG: Token verification successful")
        else:
            logger.warning(
                f"DEBUG: Token verification failed. Expected: {verify_token}, Got: {token}")

        return PlainTextResponse(content=challenge)

    return {
        "status": "debug",
        "query_params": query_params,
        "headers": {k: v for k, v in headers.items()},
        "timestamp": datetime.now().isoformat()
    }


@app.post("/webhook/manychat")
async def process_manychat_webhook(request: Request):
    """Process incoming webhook requests from ManyChat."""
    try:
        data = await request.json()
        logger.info(f"Received webhook request body: {json.dumps(data)}")

        ig_username = data.get('ig_username', '')
        subscriber_id = data.get('id', '')

        if not ig_username:
            logger.error("No Instagram username found in payload")
            return {"status": "error", "message": "No Instagram username found"}

        message_text = data.get('last_input_text', '')
        if not message_text:
            logger.error("No message text found in payload")
            return {"status": "error", "message": "No message text found"}

        # Add message to buffer
        if ig_username not in message_buffer:
            message_buffer[ig_username] = []
        message_buffer[ig_username].append(data)
        logger.info(f"Added message to buffer for {ig_username}")

        # Update timestamps
        current_time = time.time()
        last_message_timestamps[ig_username] = current_time
        logger.info(f"Updated last message timestamp for {ig_username}")

        # Create delayed processing task
        asyncio.create_task(schedule_response(ig_username, 15))
        logger.info(f"Created delayed processing task for {ig_username}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "webhook_new:app",
        host="0.0.0.0",
        port=8002,  # Use a different port than the original
        reload=True,
        reload_dirs=["c:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot"],
        timeout_keep_alive=300,
        timeout_graceful_shutdown=300,
        limit_concurrency=100,
        backlog=2048
    )
