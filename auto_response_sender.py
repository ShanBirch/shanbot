#!/usr/bin/env python3
"""
Auto Response Sender with Pre-Send Message Checking
==================================================

Enhanced to check for new messages just before sending responses.
If new messages are found, reprocesses the entire conversation context.
"""

from webhook_handlers import (
    get_user_data,
    build_member_chat_prompt,
    get_ai_response,
    process_conversation_for_media
)
from app.dashboard_modules.dashboard_sqlite_utils import (
    get_db_connection,
    add_message_to_history,
    update_review_status,
    log_auto_mode_activity,
    update_current_processing,
    clear_current_processing,
    update_auto_mode_heartbeat,
    create_auto_mode_tracking_tables_if_not_exists,
    is_user_in_vegan_flow,
)
import time
import sys
import os
import sqlite3
import logging
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple
import asyncio
import requests
import random

# --- REVISED IMPORTS ---
# Add the project root to the path to allow for absolute imports
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now, import the shared utilities

# Configure simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import ManyChat functionality
try:
    from webhook0605 import update_manychat_fields
    MANYCHAT_AVAILABLE = True
    logger.info("✅ ManyChat integration loaded successfully")
except ImportError:
    try:
        from webhook_handlers import update_manychat_fields
        MANYCHAT_AVAILABLE = True
        logger.info("✅ ManyChat integration loaded successfully (alternative)")
    except ImportError:
        update_manychat_fields = None
        MANYCHAT_AVAILABLE = False
        logger.warning(
            "⚠️ ManyChat integration not available - will simulate sending")

# Import webhook functions for reprocessing

# ManyChat Configuration
MANYCHAT_API_KEY = "996573:5b6dc180662de1be343655db562ee918"


def safe_db_update(sql: str, params: tuple, description: str = "database operation") -> bool:
    """
    Safely execute a database update with retry logic and proper connection management.

    Args:
        sql: SQL statement to execute
        params: Parameters for the SQL statement
        description: Description of the operation for logging

    Returns:
        True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            logger.debug(f"✅ Successful {description}")
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Failed {description}: {e}")
            return False
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"❌ Database connection failed for {description}: {e}")
        return False


def check_for_new_messages_since_scheduled(ig_username: str, scheduled_time: str) -> List[Dict[str, str]]:
    """
    Check for new messages from user since the response was originally scheduled.
    Intelligently avoids duplicates and only returns truly new messages.

    Args:
        ig_username: Instagram username
        scheduled_time: ISO timestamp when response was scheduled

    Returns:
        List of new message dictionaries with 'text' and 'timestamp'
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get existing messages in conversation history after scheduled time
        cursor.execute("""
            SELECT text, timestamp FROM messages 
            WHERE ig_username = ? AND timestamp > ? AND type IN ('user', 'incoming')
            ORDER BY timestamp ASC
        """, (ig_username, scheduled_time))

        existing_messages = set()
        messages_from_history = []

        for row in cursor.fetchall():
            msg_text = row[0] or ''
            msg_timestamp = row[1] or ''
            if msg_text.strip():
                existing_messages.add(msg_text.strip())
                messages_from_history.append({
                    'text': msg_text,
                    'timestamp': msg_timestamp,
                    'source': 'messages_table',
                    'already_in_history': True
                })

        # Check pending_reviews for newer messages not yet in conversation history
        cursor.execute("""
            SELECT incoming_message_text, incoming_message_timestamp 
            FROM pending_reviews 
            WHERE user_ig_username = ? AND incoming_message_timestamp > ?
            AND status != 'discarded'
            ORDER BY incoming_message_timestamp ASC
        """, (ig_username, scheduled_time))

        new_messages_from_reviews = []
        for row in cursor.fetchall():
            msg_text = row[0] or ''
            msg_timestamp = row[1] or ''

            if msg_text.strip() and msg_text.strip() not in existing_messages:
                new_messages_from_reviews.append({
                    'text': msg_text,
                    'timestamp': msg_timestamp,
                    'source': 'pending_reviews',
                    'already_in_history': False
                })
                # Prevent internal duplicates
                existing_messages.add(msg_text.strip())

        # Combine all messages, prioritizing those not yet in history
        all_new_messages = messages_from_history + new_messages_from_reviews

        conn.close()

        if all_new_messages:
            history_count = len(messages_from_history)
            reviews_count = len(new_messages_from_reviews)
            logger.info(
                f"🔍 Found {len(all_new_messages)} messages from {ig_username} since {scheduled_time}")
            logger.info(
                f"   📚 {history_count} already in conversation history")
            logger.info(f"   🆕 {reviews_count} new messages to add to history")

            for i, msg in enumerate(all_new_messages):
                status = "✅ In history" if msg['already_in_history'] else "📝 Need to add"
                logger.info(
                    f"   {i+1}. {status}: '{msg['text'][:50]}...' at {msg['timestamp']}")

        return all_new_messages

    except Exception as e:
        logger.error(
            f"❌ Error checking for new messages for {ig_username}: {e}")
        return []


async def reprocess_with_new_messages(
    original_scheduled_response: Dict,
    new_messages: List[Dict[str, str]]
) -> Optional[str]:
    """
    Reprocess the conversation with new messages included.

    Args:
        original_scheduled_response: The original scheduled response row
        new_messages: List of new message dictionaries

    Returns:
        New AI response text or None if failed
    """
    try:
        ig_username = original_scheduled_response['user_ig_username']
        subscriber_id = original_scheduled_response['user_subscriber_id']
        original_message = original_scheduled_response['incoming_message_text']

        logger.info(
            f"🔄 Reprocessing conversation for {ig_username} with {len(new_messages)} new messages")

        # Get fresh user data and conversation history
        full_conversation_history, metrics_dict, user_id = get_user_data(
            ig_username=ig_username,
            subscriber_id=subscriber_id
        )

        # Combine original message + new messages
        all_user_messages = [original_message]

        # Only add messages that are NOT already in conversation history
        new_messages_only = [
            msg for msg in new_messages
            if msg['text'].strip() and not msg.get('already_in_history', False)
        ]

        for msg in new_messages_only:
            all_user_messages.append(msg['text'])

        combined_message_text = " ".join(all_user_messages).strip()

        # Log what we're actually combining
        if new_messages_only:
            logger.info(f"📝 Original message: '{original_message[:50]}...'")
            logger.info(
                f"📝 Adding {len(new_messages_only)} NEW messages (filtering out {len(new_messages) - len(new_messages_only)} already in history)")
            for i, msg in enumerate(new_messages_only):
                logger.info(f"   {i+1}. '{msg['text'][:50]}...'")
        else:
            logger.info(
                f"📝 No new messages to add - all {len(new_messages)} messages already in conversation history")

        logger.info(
            f"📝 Final combined message for {ig_username}: '{combined_message_text[:100]}...'")

        # Process for media content (same as webhook does)
        processed_message = process_conversation_for_media(
            combined_message_text)

        # Get user details for prompt building - handle metrics_dict as dict or string
        if isinstance(metrics_dict, dict):
            current_stage = metrics_dict.get('journey_stage', {}).get(
                'current_stage', "Topic 1") if isinstance(metrics_dict.get('journey_stage'), dict) else "Topic 1"
            trial_status = metrics_dict.get('trial_status', "Initial Contact")
            first_name = metrics_dict.get('first_name', '')
            last_name = metrics_dict.get('last_name', '')
        else:
            # Fallback if metrics_dict is not a dict
            current_stage = "Topic 1"
            trial_status = "Initial Contact"
            first_name = ''
            last_name = ''

        full_name = f"{first_name} {last_name}".strip() or ig_username

        # Build fresh prompt with updated conversation
        from app.dashboard_modules.dashboard_sqlite_utils import get_good_few_shot_examples, get_vegan_few_shot_examples, is_user_in_vegan_flow

        # Get appropriate few-shot examples (vegan or general)
        few_shot_examples = []
        try:
            if is_user_in_vegan_flow(ig_username):
                few_shot_examples = get_vegan_few_shot_examples(limit=100)
                logger.info(
                    f"📚 Retrieved {len(few_shot_examples)} vegan few-shot examples for reprocessing {ig_username}")
            else:
                few_shot_examples = get_good_few_shot_examples(limit=100)
                logger.info(
                    f"📚 Retrieved {len(few_shot_examples)} general few-shot examples for reprocessing {ig_username}")
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch few-shot examples: {e}")

        # Format conversation history for prompt
        from webhook_handlers import format_conversation_history

        # FIXED: Only add truly NEW messages to history for prompt context, not the combined message
        # The original message is already in the conversation history, so we only need to add new ones
        history_for_prompt = full_conversation_history.copy()

        # Add only the NEW messages (not the original) to avoid duplication
        for msg in new_messages_only:
            history_for_prompt.append({
                "timestamp": msg.get('timestamp', datetime.now().isoformat()),
                "type": "user",
                "text": msg['text']
            })

        # For the current message prompt, use only the NEW messages (not the combined)
        if new_messages_only:
            # If we have new messages, use just the newest one as the "current message"
            current_message_for_prompt = new_messages_only[-1]['text']
            logger.info(
                f"🎯 Using newest message as current prompt context: '{current_message_for_prompt[:50]}...'")
        else:
            # If no new messages, we're just reprocessing the original
            current_message_for_prompt = processed_message
            logger.info(
                f"🎯 No new messages - reprocessing with original: '{current_message_for_prompt[:50]}...'")

        formatted_history = format_conversation_history(history_for_prompt)

        # Build fresh AI prompt
        prompt_str, prompt_type = build_member_chat_prompt(
            client_data=metrics_dict,
            # Use single current message, not combined
            current_message=current_message_for_prompt,
            current_stage=current_stage,
            trial_status=trial_status,
            full_name=full_name,
            full_conversation_string=formatted_history,
            few_shot_examples=few_shot_examples
        )

        # Get fresh AI response
        logger.info(
            f"🤖 Getting fresh AI response for {ig_username} with updated context")
        new_ai_response = await get_ai_response(prompt_str)

        if new_ai_response:
            # Filter the response (same as webhook does)
            from webhook0605 import filter_shannon_response
            filtered_response = await filter_shannon_response(new_ai_response, processed_message)

            logger.info(
                f"✅ Generated fresh response for {ig_username}: '{filtered_response[:100]}...'")
            return filtered_response
        else:
            logger.error(
                f"❌ Failed to generate fresh AI response for {ig_username}")
            return None

    except Exception as e:
        logger.error(
            f"❌ Error reprocessing conversation for {ig_username}: {e}", exc_info=True)
        return None


def split_response_into_messages(text):
    """Split response into multiple messages if too long"""
    max_length = 900
    if len(text) <= max_length:
        return [text]

    # Try to split at sentence boundaries
    sentences = text.split('. ')
    messages = []
    current_message = ""

    for sentence in sentences:
        if len(current_message + sentence + '. ') <= max_length:
            current_message += sentence + '. '
        else:
            if current_message:
                messages.append(current_message.strip())
                current_message = sentence + '. '
            else:
                # Single sentence too long, force split
                messages.append(sentence[:max_length])

    if current_message:
        messages.append(current_message.strip())

    return messages


def send_response_via_manychat(scheduled_response):
    """Send response via ManyChat API with multiple message support"""
    if not MANYCHAT_AVAILABLE:
        logger.info(
            f"📧 SIMULATED ManyChat send to {scheduled_response['user_ig_username']}: {scheduled_response['response_text'][:100]}...")
        return True

    try:
        subscriber_id = scheduled_response['user_subscriber_id']
        response_text = scheduled_response['response_text']

        # Split response into multiple messages if needed
        message_parts = split_response_into_messages(response_text)

        headers = {
            "Authorization": f"Bearer {MANYCHAT_API_KEY}",
            "Content-Type": "application/json"
        }

        # Send each message part
        for i, message_part in enumerate(message_parts):
            field_name = "o1 Response" if i == 0 else f"o1 Response {i + 1}"

            data = {
                "subscriber_id": subscriber_id,
                "fields": [{
                    "field_name": field_name,
                    "field_value": message_part
                }]
            }

            response = requests.post(
                "https://api.manychat.com/fb/subscriber/setCustomFields",
                headers=headers,
                json=data,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(
                    f"✅ Sent message part {i+1}/{len(message_parts)} to {scheduled_response['user_ig_username']}")
                if i < len(message_parts) - 1:
                    time.sleep(1)  # Small delay between parts
            else:
                logger.error(
                    f"❌ Failed to send part {i+1} to {scheduled_response['user_ig_username']}: {response.status_code}")
                return False

        return True

    except Exception as e:
        logger.error(f"❌ Error sending response via ManyChat: {e}")
        return False


async def process_scheduled_responses():
    """
    Enhanced processing with pre-send message checking.
    Checks for new messages before sending and reprocesses if needed.
    """
    try:
        # Determine if Vegan Auto Mode is active (used to disable re-generation in vegan ad mode)
        def is_vegan_auto_mode_enabled() -> bool:
            try:
                vegan_state_file = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\dashboard_modules\vegan_auto_mode.state"
                if os.path.exists(vegan_state_file):
                    with open(vegan_state_file, 'r') as f:
                        return f.read().strip().upper() == 'ON'
                return False
            except Exception:
                return False

        vegan_mode_active = is_vegan_auto_mode_enabled()

        # Get responses ready to send - using shorter connection scope
        ready_responses = []
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM scheduled_responses 
                WHERE status = 'scheduled' 
                AND scheduled_send_time <= ?
                ORDER BY scheduled_send_time ASC
            """, (datetime.now().isoformat(),))

            ready_responses = cursor.fetchall()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Error fetching scheduled responses: {e}")
            return 0

        if not ready_responses:
            return 0

        logger.info(
            f"📤 Processing {len(ready_responses)} scheduled responses...")
        processed_count = 0

        for row in ready_responses:
            processing_start_time = time.time()
            try:
                user_ig = row['user_ig_username']
                subscriber_id = row['user_subscriber_id']
                review_id = row['review_id']
                original_response = row['response_text']
                created_at = row['created_at']

                logger.info(
                    f"📤 Processing response for {user_ig} (Review ID: {review_id}, Scheduled: {row['scheduled_send_time']})")

                # Update current processing status
                update_current_processing(
                    user_ig_username=user_ig,
                    action_type='sending_response',
                    step_number=1,
                    total_steps=5,
                    step_description='Checking for new messages',
                    message_text=original_response[:100]
                )

                # Log activity
                log_auto_mode_activity(
                    user_ig_username=user_ig,
                    action_type='sending',
                    message_preview=original_response[:50],
                    status='processing',
                    auto_mode_type='vegan' if vegan_mode_active else 'general'
                )

                # 🆕 PRE-SEND CHECK: Look for new messages since scheduling
                new_messages = check_for_new_messages_since_scheduled(
                    user_ig, created_at)

                final_response_text = original_response
                response_was_updated = False

                if new_messages:
                    logger.info(
                        f"🔄 Found {len(new_messages)} new messages from {user_ig} - reprocessing conversation")

                    # 🆕 FIRST: Add any new messages to conversation history (only those not already there)
                    messages_added_to_history = 0
                    for msg in new_messages:
                        # Only add messages that aren't already in conversation history
                        if msg['text'].strip() and not msg.get('already_in_history', False):
                            try:
                                # Use the message's original timestamp
                                msg_timestamp = msg['timestamp'] if msg['timestamp'] else datetime.now(
                                ).isoformat()

                                add_message_to_history(
                                    ig_username=user_ig,
                                    message_type='user',
                                    message_text=msg['text'],
                                    message_timestamp=msg_timestamp
                                )
                                messages_added_to_history += 1
                                logger.info(
                                    f"📝 Added new user message to history: '{msg['text'][:50]}...'")
                            except Exception as add_error:
                                logger.warning(
                                    f"⚠️ Failed to add message to history: {add_error}")
                        elif msg.get('already_in_history', False):
                            logger.info(
                                f"⏭️  Skipping message already in history: '{msg['text'][:50]}...'")

                    if messages_added_to_history > 0:
                        logger.info(
                            f"✅ Added {messages_added_to_history} new messages to conversation history")
                    else:
                        logger.info(
                            "📚 All messages were already in conversation history")

                    # 🔒 All Auto Modes: do not regenerate/update the scheduled response text
                    logger.info(
                        "🔒 Auto Mode: skipping re-generation; sending original scheduled response text as-is")

                # Prepare response for sending
                scheduled_response = {
                    'user_ig_username': user_ig,
                    'user_subscriber_id': subscriber_id,
                    'response_text': final_response_text,
                    'original_response': original_response,
                    'was_updated': response_was_updated
                }

                # Send the response (original or updated)
                send_success = send_response_via_manychat(scheduled_response)

                if send_success:
                    # Mark as sent - using safe retry logic
                    sent_sql = """
                        UPDATE scheduled_responses 
                        SET status = 'sent', 
                            sent_at = ?,
                            processed_at = ?
                        WHERE schedule_id = ?
                    """
                    sent_params = (datetime.now().isoformat(
                    ), datetime.now().isoformat(), row['schedule_id'])

                    if not safe_db_update(sent_sql, sent_params, f"marking response as sent for {user_ig}"):
                        logger.error(
                            f"❌ Failed to mark response as sent for {user_ig}")

                    # Add to conversation history
                    try:
                        # Calculate appropriate timestamp for AI response - IMPROVED
                        user_response_time = row['user_response_time'] if 'user_response_time' in row.keys(
                        ) else ''
                        if user_response_time:
                            try:
                                user_msg_timestamp = datetime.fromisoformat(
                                    user_response_time.split('+')[0])

                                # Check for existing AI responses to avoid timestamp collisions
                                conn_check = get_db_connection()
                                cursor_check = conn_check.cursor()
                                cursor_check.execute("""
                                    SELECT timestamp FROM messages 
                                    WHERE ig_username = ? AND type = 'ai' AND timestamp > ?
                                    ORDER BY timestamp DESC LIMIT 1
                                """, (user_ig, user_response_time))

                                last_ai_result = cursor_check.fetchone()
                                conn_check.close()

                                if last_ai_result:
                                    # If there's already an AI response after this user message,
                                    # place this one slightly after the last AI response to avoid duplicates
                                    last_ai_time = datetime.fromisoformat(
                                        last_ai_result[0].split('+')[0])
                                    ai_response_timestamp = (
                                        last_ai_time + timedelta(seconds=random.randint(30, 60))).isoformat()
                                    logger.info(
                                        f"🕐 Adjusted AI timestamp to avoid collision for {user_ig}")
                                else:
                                    # Normal case: respond 30-90 seconds after user message (realistic timing)
                                    delay_seconds = random.randint(30, 90)
                                    ai_response_timestamp = (
                                        user_msg_timestamp + timedelta(seconds=delay_seconds)).isoformat()

                            except (ValueError, AttributeError):
                                ai_response_timestamp = datetime.now().isoformat()
                        else:
                            ai_response_timestamp = datetime.now().isoformat()

                        # Removed explicit add_message_to_history to prevent duplicate AI rows; webhook will handle logging
                    except Exception as history_error:
                        logger.warning(
                            f"⚠️ Failed to add to conversation history for {user_ig}: {history_error}")

                    # Update review status
                    update_review_status(
                        review_id, 'sent', final_response_text)

                    status_msg = "UPDATED & SENT" if response_was_updated else "SENT"
                    logger.info(
                        f"✅ {status_msg}: Response to {user_ig} (Review ID: {review_id})")
                    processed_count += 1

                    # Log successful completion
                    processing_time = int(
                        (time.time() - processing_start_time) * 1000)
                    log_auto_mode_activity(
                        user_ig_username=user_ig,
                        action_type='sent',
                        message_preview=final_response_text[:50],
                        status='success',
                        processing_time_ms=processing_time,
                        auto_mode_type='vegan' if vegan_mode_active else 'general',
                        action_details={
                            'was_updated': response_was_updated,
                            'new_messages_count': len(new_messages) if new_messages else 0
                        }
                    )

                else:
                    # Mark as failed - using safe retry logic
                    failed_sql = """
                        UPDATE scheduled_responses 
                        SET status = 'failed',
                            processed_at = ?
                        WHERE schedule_id = ?
                    """
                    failed_params = (
                        datetime.now().isoformat(), row['schedule_id'])

                    if not safe_db_update(failed_sql, failed_params, f"marking response as failed for {user_ig}"):
                        logger.error(
                            f"❌ Failed to mark response as failed in database for {user_ig}")

                    logger.error(f"❌ Failed to send response to {user_ig}")

                    # Log failure
                    processing_time = int(
                        (time.time() - processing_start_time) * 1000)
                    log_auto_mode_activity(
                        user_ig_username=user_ig,
                        action_type='failed',
                        message_preview=final_response_text[:50],
                        status='failed',
                        processing_time_ms=processing_time,
                        auto_mode_type='general',
                        action_details={'error': 'Failed to send via ManyChat'}
                    )

            except Exception as e:
                logger.error(
                    f"❌ Error processing response for {row['user_ig_username'] if 'user_ig_username' in row.keys() else 'unknown'}: {e}", exc_info=True)
                # Mark as failed - using safe retry logic
                error_sql = """
                    UPDATE scheduled_responses 
                    SET status = 'failed',
                        processed_at = ?
                    WHERE schedule_id = ?
                """
                error_params = (datetime.now().isoformat(), row['schedule_id'])

                username_for_error = row['user_ig_username'] if 'user_ig_username' in row.keys(
                ) else 'unknown'
                if not safe_db_update(error_sql, error_params, f"marking response as failed in exception handler for {username_for_error}"):
                    logger.error(
                        f"❌ Failed to mark response as failed in exception handler for {username_for_error}")

        if processed_count > 0:
            logger.info(
                f"🎉 Successfully processed {processed_count} responses")

        # Clear current processing status
        clear_current_processing()

        return processed_count

    except Exception as e:
        logger.error(
            f"❌ Error in process_scheduled_responses main function: {e}", exc_info=True)
        return 0


def get_stats():
    """Get simple statistics with next send time"""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT status, COUNT(*) as count FROM scheduled_responses GROUP BY status")
        status_counts = {row['status']: row['count']
                         for row in cursor.fetchall()}

        # Get pending count and the time of the soonest-to-be-sent message
        cursor.execute("""
        SELECT COUNT(*) as pending_count, MIN(scheduled_send_time) as next_send_time 
        FROM scheduled_responses 
        WHERE status = 'scheduled' AND scheduled_send_time > ?
        """, (datetime.now().isoformat(),))

        pending_info = cursor.fetchone()

        conn.close()

        return {
            'scheduled': status_counts.get('scheduled', 0),
            'sent': status_counts.get('sent', 0),
            'failed': status_counts.get('failed', 0),
            'pending_count': pending_info['pending_count'] if pending_info else 0,
            'next_send_time': pending_info['next_send_time'] if pending_info else None
        }
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        return {'scheduled': 0, 'sent': 0, 'failed': 0, 'pending_count': 0, 'next_send_time': None}


def check_auto_mode_status() -> bool:
    """Check if Auto Mode is enabled via status file (general or vegan auto mode)"""
    try:
        # Check general auto mode first
        general_auto_active = False

        # Check current directory first, then absolute path for general auto mode
        status_file = "auto_mode_status.json"
        if not os.path.exists(status_file):
            status_file = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\dashboard_modules\auto_mode_status.json"

        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status_data = json.load(f)
            general_auto_active = status_data.get(
                'auto_mode_enabled', status_data.get('active', False))

        # Check vegan auto mode using the new state file
        vegan_auto_active = False
        vegan_state_file = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\dashboard_modules\vegan_auto_mode.state"

        if os.path.exists(vegan_state_file):
            with open(vegan_state_file, 'r') as f:
                vegan_status_text = f.read().strip().upper()
                vegan_auto_active = (vegan_status_text == "ON")

        # Auto sender should run if EITHER mode is active
        any_auto_active = general_auto_active or vegan_auto_active

        if any_auto_active:
            modes = []
            if general_auto_active:
                modes.append("GENERAL")
            if vegan_auto_active:
                modes.append("VEGAN")
            logger.info(
                f"Auto Mode Status: ENABLED ({' + '.join(modes)} mode{'s' if len(modes) > 1 else ''})")
        else:
            logger.info(
                "Auto Mode Status: DISABLED (both general and vegan modes are off)")

        return any_auto_active

    except Exception as e:
        logger.error(f"Error checking auto mode status: {e}")
        return False


async def main():
    """Main worker function"""
    print("=" * 60)
    print("🤖 AUTO RESPONSE SENDER v2.0")
    print("🔄 WITH PRE-SEND MESSAGE CHECKING")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: CONTINUOUS")
    print(
        f"ManyChat Available: {'YES' if MANYCHAT_AVAILABLE else 'NO (simulated)'}")
    print("=" * 60)

    # Ensure auto mode tracking tables exist
    try:
        conn = get_db_connection()
        create_auto_mode_tracking_tables_if_not_exists(conn)
        conn.close()
        logger.info("✅ Auto mode tracking tables ensured")
    except Exception as e:
        logger.error(f"❌ Error creating auto mode tables: {e}")

    # Continuous mode
    logger.info("🔄 Starting continuous mode with pre-send checking...")
    logger.info("💡 Press Ctrl+C to stop")

    try:
        cycle = 0
        check_interval = 60  # 1 minute
        while True:
            cycle += 1
            logger.info(
                f"--- Starting processing cycle #{cycle} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")

            # Update heartbeat
            update_auto_mode_heartbeat(
                status='running',
                cycle_count=cycle,
                performance_stats={'last_cycle': cycle,
                                   'last_run': datetime.now().isoformat()}
            )

            # Check auto mode status each cycle
            if not check_auto_mode_status():
                logger.info("No auto mode active, skipping this cycle")
                update_auto_mode_heartbeat(status='idle', cycle_count=cycle)
                await asyncio.sleep(check_interval)
                continue

            processed = await process_scheduled_responses()

            if processed > 0:
                logger.info(
                    f"✅ Cycle #{cycle}: Processed {processed} responses")
            else:
                logger.info(f"⏳ Cycle #{cycle}: No responses due for sending")

            # Wait before next cycle
            await asyncio.sleep(check_interval)

    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
        update_auto_mode_heartbeat(status='stopped')
        clear_current_processing()
    except Exception as e:
        logger.error(f"💥 Worker error: {e}", exc_info=True)
        update_auto_mode_heartbeat(status='error', error_message=str(e))
        clear_current_processing()


if __name__ == "__main__":
    asyncio.run(main())
