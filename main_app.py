# main_app.py
import os
import sys
import json
import time
import asyncio
import logging
import traceback
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

# --- Direct import from the app package to avoid circular dependency ---
from app.dashboard_modules.auto_mode_state import is_auto_mode_active, is_vegan_auto_mode_active, is_vegan_ad_auto_mode_active

# --- Placeholder for imports from our new modules ---
# These will be created in the next steps.
from action_handler import (
    detect_and_handle_action,
    check_and_trigger_bio_analysis,
    process_wix_form_submission
)
from utilities import (
    get_user_data,
    update_analytics_data,
    process_conversation_for_media,
    build_member_chat_prompt,
    get_ai_response,
    filter_shannon_response,
    split_response_into_messages,
    add_response_to_review_queue,
    schedule_auto_response,
    create_scheduled_responses_table_if_not_exists,
    get_db_connection as get_util_db_connection  # aliased to avoid conflict
)

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("main_app")

# Suppress noisy logs from third-party libraries
logging.getLogger("watchfiles.main").setLevel(logging.WARNING)

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- FastAPI App Initialization ---
app = FastAPI(title="Shanbot Webhook Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Variables & Buffers ---
# Global dictionaries for message buffering
manychat_message_buffer: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
user_buffer_tasks: Dict[str, asyncio.Task] = {}
BUFFER_WINDOW = 60  # seconds to wait for grouping messages

# Add buffer state tracking
# Track if user is currently being processed
user_buffer_locks: Dict[str, bool] = {}

# Add cleanup tracking
last_cleanup_time = time.time()
CLEANUP_INTERVAL = 300  # 5 minutes


def cleanup_stale_buffers():
    """Clean up stale buffers and tasks to prevent memory leaks."""
    global last_cleanup_time
    current_time = time.time()

    if current_time - last_cleanup_time < CLEANUP_INTERVAL:
        return

    last_cleanup_time = current_time
    cleaned_count = 0

    # Clean up done tasks
    for subscriber_id in list(user_buffer_tasks.keys()):
        task = user_buffer_tasks[subscriber_id]
        if task.done():
            user_buffer_tasks.pop(subscriber_id, None)
            user_buffer_locks.pop(subscriber_id, None)
            cleaned_count += 1

    # Clean up old buffers (older than 10 minutes)
    ten_minutes_ago = current_time - 600
    for subscriber_id in list(manychat_message_buffer.keys()):
        if manychat_message_buffer[subscriber_id]:
            oldest_message_time = min(
                item.get("user_msg_created_at_s", 0)
                for item in manychat_message_buffer[subscriber_id]
            )
            if oldest_message_time < ten_minutes_ago:
                manychat_message_buffer.pop(subscriber_id, None)
                user_buffer_locks.pop(subscriber_id, None)
                cleaned_count += 1

    if cleaned_count > 0:
        logger.info(f"Cleaned up {cleaned_count} stale buffers/tasks")


# --- Webhook Endpoints ---


@app.get("/", include_in_schema=False)
async def root():
    return {"status": "Shanbot API running", "docs_at": "/docs"}


@app.get("/health")
async def health_check():
    """Simple health check endpoint to confirm the server is up."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/buffer/status")
async def buffer_status():
    """Debug endpoint to check buffer status."""
    buffer_info = {}
    for subscriber_id, messages in manychat_message_buffer.items():
        buffer_info[subscriber_id] = {
            "message_count": len(messages),
            "has_task": subscriber_id in user_buffer_tasks,
            "task_done": user_buffer_tasks.get(subscriber_id, None) and user_buffer_tasks[subscriber_id].done(),
            "is_locked": user_buffer_locks.get(subscriber_id, False),
            # First 3 messages
            "messages": [msg.get("payload", {}).get("last_input_text", "")[:50] + "..." for msg in messages[:3]]
        }

    return {
        "buffer_window_seconds": BUFFER_WINDOW,
        "active_buffers": len(manychat_message_buffer),
        "active_tasks": len(user_buffer_tasks),
        "locked_users": len([k for k, v in user_buffer_locks.items() if v]),
        "buffer_details": buffer_info
    }


@app.post("/webhook/manychat")
async def process_manychat_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives incoming messages from ManyChat, buffers them, and processes them in batches.
    """
    try:
        payload = await request.json()
        logger.info(
            f"Received ManyChat payload: {json.dumps(payload, indent=2)[:500]}...")
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON payload from ManyChat.")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    subscriber_id = payload.get("id") or payload.get(
        "subscriber", {}).get("id")
    if not subscriber_id:
        logger.error("Critical: Subscriber ID missing in ManyChat payload.")
        return PlainTextResponse("Error: Subscriber ID missing", status_code=400)

    # Simplified username extraction
    ig_username = payload.get("ig_username") or payload.get(
        "subscriber", {}).get("name") or f"user_{subscriber_id}"
    if ig_username.startswith('user_') and len(ig_username) > 5:
        logger.warning(
            f"Using placeholder username '{ig_username}' for subscriber {subscriber_id}")

    # Check if user is currently being processed to prevent duplicates
    if user_buffer_locks.get(subscriber_id, False):
        logger.info(
            f"User {subscriber_id} is currently being processed. Skipping duplicate message.")
        return PlainTextResponse("Message received, processing in progress.", status_code=200)

    # Run cleanup to prevent memory leaks
    cleanup_stale_buffers()

    # Append message to buffer
    user_message_created_at_s = payload.get("created_at", time.time())
    manychat_message_buffer[subscriber_id].append({
        "payload": payload,
        "user_msg_created_at_s": user_message_created_at_s
    })
    logger.info(
        f"Appended message to buffer for SID {subscriber_id}. Buffer size: {len(manychat_message_buffer[subscriber_id])}")

    # Cancel any existing timer for this user to restart the buffer window
    if subscriber_id in user_buffer_tasks and not user_buffer_tasks[subscriber_id].done():
        try:
            user_buffer_tasks[subscriber_id].cancel()
            logger.info(
                f"Canceled existing buffer task for SID {subscriber_id} to restart timer.")
        except Exception as e:
            logger.warning(f"Error cancelling task for {subscriber_id}: {e}")

    # Create new asyncio task instead of using background_tasks
    new_task = asyncio.create_task(
        run_core_processing_after_buffer(
            subscriber_id, ig_username, background_tasks)
    )
    user_buffer_tasks[subscriber_id] = new_task
    logger.info(
        f"Scheduled new buffer processing task for SID {subscriber_id}.")

    return PlainTextResponse("Webhook received, processing deferred.", status_code=200)


@app.post("/webhook/wix-onboarding")
async def wix_webhook_endpoint(request: Request, background_tasks: BackgroundTasks):
    """Endpoint to handle Wix form submissions for new client onboarding."""
    return await process_wix_form_submission(request, background_tasks)


# --- Core Processing Logic ---

async def run_core_processing_after_buffer(subscriber_id: str, ig_username: str, bg_tasks: BackgroundTasks):
    """
    Waits for the buffer window to close, then gathers all messages and processes them.
    """
    try:
        # Set processing lock to prevent duplicate processing
        user_buffer_locks[subscriber_id] = True
        logger.info(f"Started buffer processing for SID {subscriber_id}")

        await asyncio.sleep(BUFFER_WINDOW)
    except asyncio.CancelledError:
        logger.info(
            f"Buffer task for SID {subscriber_id} was cancelled by a new message.")
        # Clear the lock if task was cancelled
        user_buffer_locks.pop(subscriber_id, None)
        return
    except Exception as e:
        logger.error(
            f"Error in buffer processing for SID {subscriber_id}: {e}")
        user_buffer_locks.pop(subscriber_id, None)
        return

    logger.info(
        f"Buffer window closed for SID {subscriber_id}. Processing messages.")

    # Clean up task tracking
    user_buffer_tasks.pop(subscriber_id, None)

    # Get buffered messages and clear buffer
    buffered_items = manychat_message_buffer.pop(subscriber_id, [])
    if not buffered_items:
        logger.info(
            f"No messages in buffer for SID {subscriber_id}. Exiting task.")
        user_buffer_locks.pop(subscriber_id, None)
        return

    try:
        message_payloads = [item["payload"] for item in buffered_items]
        batch_start_time_s = min(item["user_msg_created_at_s"]
                                 for item in buffered_items)

        await _handle_buffered_messages(subscriber_id, ig_username, message_payloads, bg_tasks, batch_start_time_s)
    except Exception as e:
        logger.error(
            f"Error processing buffered messages for SID {subscriber_id}: {e}")
    finally:
        # Always clear the processing lock
        user_buffer_locks.pop(subscriber_id, None)
        logger.info(f"Completed buffer processing for SID {subscriber_id}")


async def _handle_buffered_messages(subscriber_id: str, ig_username: str, payloads: List[Dict], bg_tasks: BackgroundTasks, batch_start_time_s: float):
    """
    The main logic hub that processes a user's messages after the buffer wait.
    """
    logger.info(
        f"Handling {len(payloads)} buffered messages for SID: {subscriber_id}")

    # Combine message texts
    combined_text_parts = []
    media_urls_in_batch = []
    for p in payloads:
        text = p.get("last_input_text", "")
        media_url = p.get("message", {}).get("attachments", [{}])[0].get("url")
        if text:
            combined_text_parts.append(text)
        if media_url and media_url not in media_urls_in_batch:
            # Append full URL to text for context and analysis
            combined_text_parts.append(media_url)
            media_urls_in_batch.append(media_url)

    final_combined_message = " ".join(combined_text_parts).strip()
    if not final_combined_message:
        logger.warning(
            f"No text content found for SID {subscriber_id} after combining buffer.")
        return

    logger.info(
        f"Combined message for SID {subscriber_id}: '{final_combined_message[:250]}...'")

    # --- Data Fetching and Analysis ---
    last_payload = payloads[-1]
    first_name = last_payload.get("first_name", "")
    last_name = last_payload.get("last_name", "")

    # Trigger background bio analysis if needed
    bg_tasks.add_task(check_and_trigger_bio_analysis,
                      ig_username, subscriber_id)

    # Get existing user data
    conversation_history, metrics_dict, _ = get_user_data(
        ig_username, subscriber_id)

    # --- RECORD USER MESSAGE IN CONVERSATION HISTORY ---
    # Add the user's message to conversation history before processing
    user_message_timestamp_iso = datetime.fromtimestamp(
        batch_start_time_s).isoformat()
    try:
        from app.dashboard_modules.dashboard_sqlite_utils import add_message_to_history
        add_message_to_history(
            ig_username=ig_username,
            message_type='user',
            message_text=final_combined_message,
            message_timestamp=user_message_timestamp_iso
        )
        logger.info(
            f"📝 Added user message to conversation history for {ig_username}")
    except Exception as e:
        logger.error(
            f"❌ Failed to add user message to conversation history for {ig_username}: {e}")

    # --- Action Detection ---
    # `detect_and_handle_action` will return True if it handled the message (e.g., form check, workout change).
    action_handled = await detect_and_handle_action(ig_username, final_combined_message, subscriber_id, last_payload, batch_start_time_s)

    # --- General Conversational AI Response ---
    if not action_handled:
        logger.info(
            f"No specific action handled for {ig_username}. Proceeding with general AI response.")

        # This processed version is for the AI prompt (e.g., transcribing audio)
        processed_message_for_prompt = process_conversation_for_media(
            final_combined_message)

        prompt, prompt_type = build_member_chat_prompt(
            client_data=metrics_dict,
            current_message=processed_message_for_prompt,
            full_name=f"{first_name} {last_name}".strip() or ig_username
        )

        ai_raw_response = await get_ai_response(prompt)
        ai_filtered_response = await filter_shannon_response(ai_raw_response, processed_message_for_prompt)

        if ai_filtered_response:
            # If auto-mode is ON, schedule the response. Otherwise, queue for manual review.
            user_message_timestamp_iso = datetime.fromtimestamp(
                batch_start_time_s).isoformat()

            # Check auto mode status
            general_auto_active = is_auto_mode_active()
            vegan_auto_active = is_vegan_auto_mode_active()
            is_fresh_vegan = metrics_dict.get('is_fresh_vegan', False)

            should_auto_process = general_auto_active or (
                vegan_auto_active and is_fresh_vegan)

            if should_auto_process:
                logger.info(
                    f"AUTO-MODE ACTIVE: Scheduling response for {ig_username}.")
                review_id = add_response_to_review_queue(
                    user_ig_username=ig_username,
                    user_subscriber_id=subscriber_id,
                    incoming_message_text=final_combined_message,
                    incoming_message_timestamp=user_message_timestamp_iso,
                    generated_prompt_text=prompt,
                    proposed_response_text=ai_filtered_response,
                    status='auto_scheduled'
                )
                if review_id:
                    # Schedule auto-response (this will add to conversation history when sent)
                    schedule_auto_response(review_id)
                    logger.info(
                        f"✅ Auto-scheduled response for {ig_username} (Review ID: {review_id})")
                else:
                    logger.error(
                        f"❌ Failed to auto-schedule response for {ig_username}")
            else:
                logger.info(
                    f"AUTO-MODE OFF: Queuing response for {ig_username} for manual review.")
                review_id = add_response_to_review_queue(
                    user_ig_username=ig_username,
                    user_subscriber_id=subscriber_id,
                    incoming_message_text=final_combined_message,
                    incoming_message_timestamp=user_message_timestamp_iso,
                    generated_prompt_text=prompt,
                    proposed_response_text=ai_filtered_response,
                    prompt_type=prompt_type,
                    status='pending_review'  # Explicitly set status for manual review
                )
                if review_id:
                    logger.info(
                        f"✅ Queued response for manual review (Review ID: {review_id})")
                else:
                    logger.error(
                        f"❌ Failed to queue response for {ig_username}")

            # Record the AI's proposed response in analytics (but NOT in conversation history)
            update_analytics_data(ig_username, final_combined_message, ai_filtered_response, subscriber_id,
                                  first_name, last_name, user_message_timestamp=user_message_timestamp_iso)
        else:
            logger.error(
                f"AI failed to generate a response for {ig_username}.")
            update_analytics_data(ig_username, final_combined_message,
                                  "[AI FAILED TO RESPOND]", subscriber_id, first_name, last_name, user_message_timestamp=user_message_timestamp_iso)
    else:
        logger.info(
            f"Action was handled for {ig_username}; general AI response was skipped.")
        # Analytics are updated inside detect_and_handle_action when it handles the message

# --- Server Startup ---
if __name__ == "__main__":
    logger.info("=== STARTING SHANBOT WEBHOOK SERVER ===")
    # Ensure necessary tables exist on startup
    db_conn = get_util_db_connection()
    if db_conn:
        create_scheduled_responses_table_if_not_exists(db_conn)
        db_conn.close()
    else:
        logger.warning(
            "Could not establish database connection during startup")

    uvicorn.run(
        "main_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[os.path.dirname(__file__)],
        timeout_keep_alive=300
    )
