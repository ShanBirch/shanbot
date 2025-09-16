
from app.db_backend import (
    add_response_to_review_queue,
    add_message_to_history,
    set_user_ad_flow,
)
from app import prompts
from app.general_utils import get_melbourne_time_str, format_conversation_history, clean_and_dedupe_history
from app.ai_handler import get_ai_response
import json
from utilities import process_conversation_for_media
import logging
from typing import Dict, Any

# Import from the main webhook_handlers (not the app one)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger("shanbot_ad_handler")


class AdResponseHandler:
    """Handles responses to Instagram/Facebook ads."""

    @staticmethod
    async def is_ad_response(ig_username: str, message_text: str, metrics: Dict) -> tuple[bool, int, int]:
        """Determine if a message is a response to an ad. Returns (is_ad, scenario, confidence)."""
        logger.info(
            f"[AdResponse] Analyzing message from {ig_username}: '{message_text}' for ad intent")
        # Process media first to extract any textual context before classification/heuristics
        processed_text = message_text
        try:
            processed_text = process_conversation_for_media(message_text)
            if processed_text != message_text:
                logger.info(
                    f"[AdResponse] Media processed for detection. Using processed text: {processed_text[:100]}...")
        except Exception as e:
            logger.warning(
                f"[AdResponse] Media processing failed for detection: {e}")

        text = (processed_text or "").lower()
        scenario = 3  # Default to plant_based
        confidence = 0

        ad_keywords = [
            "challenge", "vegan challenge", "vegetarian challenge",
            "learn more", "get started", "interested", "know more", "more about",
            "ready to", "join", "sign me up", "count me in",
            # Add more common ad response phrases
            "yes", "yeah", "yep", "sure", "ok", "okay", "sounds good",
            "tell me more", "info", "information", "details", "how much",
            "cost", "price", "free", "trial", "help", "lose weight",
            "fitness", "workout", "diet", "healthy", "transformation"
        ]

        # Check for vegan challenge (with typo tolerance)
        if ("vegan" in text and "challeng" in text) or "vegan challenge" in text:
            logger.info(
                f"[AdResponse] Found vegan challenge reference in text")
            scenario = 1
            confidence = 90
        elif ("vegetarian" in text and "challeng" in text) or "vegetarian challenge" in text:
            logger.info(
                f"[AdResponse] Found vegetarian challenge reference in text")
            scenario = 2
            confidence = 90
        # Check for vegan + program/join/weight loss combinations
        elif "vegan" in text and any(program_word in text for program_word in ["program", "join", "weight loss", "weightloss", "fitness", "training"]):
            logger.info(
                f"[AdResponse] Found vegan + program/join/weight loss reference in text")
            scenario = 1
            confidence = 85
        elif "vegetarian" in text and any(program_word in text for program_word in ["program", "join", "weight loss", "weightloss", "fitness", "training"]):
            logger.info(
                f"[AdResponse] Found vegetarian + program/join/weight loss reference in text")
            scenario = 2
            confidence = 85
        elif any(keyword in text for keyword in ad_keywords):
            matched_keywords = [kw for kw in ad_keywords if kw in text]
            logger.info(f"[AdResponse] Found ad keywords: {matched_keywords}")
            scenario = 3
            confidence = 80

        # Check for short first messages (common for ad responses) - be more aggressive
        conv_history_len = len(metrics.get('conversation_history', []))
        if confidence == 0 and conv_history_len <= 2 and len(message_text.split()) < 15:
            logger.info(
                f"[AdResponse] Short early message detected (history: {conv_history_len}, words: {len(message_text.split())})")
            confidence = 55  # Higher confidence for early short messages

        # Even more aggressive - if it's a very first message and not obviously spam
        if conv_history_len == 0 and len(message_text.split()) <= 5:
            # Simple first messages like "Hi", "Hey", "Hello", "Yes" etc
            simple_starters = ["hi", "hey", "hello",
                               "yes", "yeah", "yep", "interested", "info"]
            if any(starter in text for starter in simple_starters):
                confidence = max(confidence, 60)
                logger.info(
                    f"[AdResponse] Simple starter message detected: '{message_text}'")

        # Boost confidence for ANY response if user has no conversation history (likely from ads)
        if conv_history_len == 0 and confidence < 50:
            # Give benefit of doubt to first-time messagers
            confidence = max(confidence, 45)

        # Lightweight Gemini-based classifier to complement heuristics
        try:
            classifier_prompt = (
                "You are a strict classifier. Answer ONLY in JSON.\n\n"
                f"UserMessage: \"{processed_text}\"\n\n"
                "Question: Could this person be inquiring about our Vegan Weight Loss Challenge?\n\n"
                "Return JSON with keys: is_ad_interest (true/false), confidence (0.0-1.0), reasons (array), matched_cues (array).\n"
                "Rules:\n"
                "- Treat vegan/plant-based + interest cues (interested, know more, join, ready, challenge, program) as strong.\n"
                "- Be conservative if it's only diet identity (e.g., pescetarian) with no interest cue.\n"
            )
            cls_raw = await get_ai_response(classifier_prompt)
            cls_data = None
            if cls_raw:
                try:
                    # Extract JSON if model wrapped text
                    start = cls_raw.find('{')
                    end = cls_raw.rfind('}')
                    json_str = cls_raw[start:end+1] if start != - \
                        1 and end != -1 else cls_raw
                    cls_data = json.loads(json_str)
                except Exception:
                    cls_data = None

            if isinstance(cls_data, dict):
                cls_is_ad = bool(cls_data.get('is_ad_interest', False))
                cls_conf = float(cls_data.get('confidence', 0.0))
                matched_cues = [str(c).lower() for c in (cls_data.get(
                    'matched_cues') or []) if isinstance(c, (str, int, float))]

                # Scenario hint from classifier cues if not already set to vegan/vegetarian
                if scenario == 3:
                    if any('vegan' in c for c in matched_cues) or 'vegan' in text:
                        scenario = 1
                    elif any('vegetarian' in c for c in matched_cues) or 'vegetarian' in text:
                        scenario = 2

                # Fuse with heuristics: promote to at least 70% if classifier is confident
                if cls_is_ad and cls_conf >= 0.65:
                    confidence = max(confidence, int(round(cls_conf * 100)))
                    if confidence < 70:
                        confidence = 70
        except Exception as e:
            logger.warning(f"[AdResponse] Classifier step failed: {e}")

        # Small boost if known ad-origin lead
        try:
            lead_source = str(metrics.get('lead_source', '') or '').lower()
            if any(k in lead_source for k in ['facebook_ad', 'paid_plant_based_challenge', 'plant_based_challenge', 'ad']):
                confidence = min(95, confidence + 10)
        except Exception:
            pass

        is_ad = confidence >= 50

        logger.info(
            f"[AdResponse] Final result: is_ad={is_ad}, scenario={scenario}, confidence={confidence}%")

        return is_ad, scenario, confidence

    @staticmethod
    async def handle_ad_response(ig_username: str, message_text: str, subscriber_id: str,
                                 first_name: str, last_name: str, user_message_timestamp_iso: str,
                                 scenario: int, metrics: dict, fb_ad: bool = False) -> bool:
        """Handle ad response by generating a scripted reply."""
        try:
            logger.info(
                f"[AdResponse] Handling ad response for {ig_username} with scenario {scenario}")

            # Prepare data for prompt
            current_time = get_melbourne_time_str()
            bio_context = metrics.get(
                'client_analysis', {}).get('profile_bio', '')

            # Process media URLs in the message before building conversation
            processed_message_text = message_text
            try:
                # Import the media processing function
                processed_message_text = process_conversation_for_media(
                    message_text)
                if processed_message_text != message_text:
                    logger.info(
                        f"[AdResponse] Processed media in message for {ig_username}: {processed_message_text[:100]}...")
            except Exception as e:
                logger.error(
                    f"[AdResponse] Error processing media for {ig_username}: {e}")
                processed_message_text = message_text  # Fallback to original

            # Debug conversation history
            conversation_history_raw = metrics.get('conversation_history', [])
            logger.info(
                f"[AdResponse] Raw conversation history for {ig_username}: {len(conversation_history_raw)} entries")
            logger.info(
                f"[AdResponse] History sample: {conversation_history_raw[-3:] if conversation_history_raw else 'EMPTY'}")

            # Clean and dedupe for clearer prompting
            conversation_history = clean_and_dedupe_history(
                conversation_history_raw, max_items=40)

            full_conversation = format_conversation_history(
                conversation_history) + f"\\nUser: {processed_message_text}"
            logger.info(
                f"[AdResponse] Formatted conversation: {full_conversation[:200]}...")

            script_state = metrics.get('ad_script_state', 'step1')

            challenge_types = {1: 'vegan', 2: 'vegetarian', 3: 'plant_based'}
            challenge_type = challenge_types.get(scenario, 'plant_based')

            # Build prompt using ad response template
            prompt = prompts.COMBINED_AD_RESPONSE_PROMPT_TEMPLATE.format(
                current_melbourne_time_str=current_time,
                ig_username=ig_username,
                script_state=script_state,
                ad_scenario=scenario,
                full_conversation=full_conversation
            )

            # Generate AI response
            ai_response = await get_ai_response(prompt)

            if not ai_response:
                logger.error(
                    f"[AdResponse] Failed to generate AI response for {ig_username}")
                return False

            # ✅ CRITICAL: Tag user as being in ad flow so subsequent messages use this flow
            try:
                current_state = metrics.get('ad_script_state', 'step1')
                next_state = AdResponseHandler._advance_script_state(
                    current_state, message_text)
                ok = set_user_ad_flow(
                    ig_username=ig_username,
                    subscriber_id=subscriber_id,
                    scenario=scenario,
                    next_state=next_state,
                    lead_source='paid_plant_based_challenge',
                )
                if ok:
                    logger.info(
                        f"[AdResponse] Successfully tagged {ig_username} for ad flow (scenario={scenario})")
                else:
                    logger.error(
                        f"[AdResponse] Failed to tag {ig_username} for ad flow via db backend")
            except Exception as e:
                logger.error(
                    f"[AdResponse] Failed to tag {ig_username} for ad flow: {e}")

            # Ensure we have a valid ig_username before queuing
            if not ig_username or ig_username.strip() == '':
                ig_username = f"user_{subscriber_id}"
                logger.warning(
                    f"[AdResponse] Using fallback ig_username '{ig_username}' for ad response")

            # Check auto mode status for ad responses
            should_auto_process = False
            try:
                from app.dashboard_modules.auto_mode_state import is_vegan_ad_auto_mode_active

                # Check if user is a paying client (should always be manual)
                client_status = metrics.get('client_status', 'Not a Client')
                is_paying_client = client_status in [
                    'Trial Member', 'Paying Member', 'Active Client']

                if is_paying_client:
                    logger.info(
                        f"[AdResponse] {ig_username} is a paying client - manual review required")
                    should_auto_process = False
                elif is_vegan_ad_auto_mode_active():
                    logger.info(
                        f"[AdResponse] 🌱 VEGAN AD AUTO MODE ACTIVE - Auto-processing ad response for {ig_username}")
                    should_auto_process = True
                else:
                    logger.info(
                        f"[AdResponse] Vegan ad auto mode OFF - manual review required for {ig_username}")
                    should_auto_process = False

            except ImportError:
                logger.warning(
                    "Could not import auto_mode_state, assuming manual review for ad response")
                should_auto_process = False

            # Persist the incoming USER message immediately
            try:
                add_message_to_history(
                    ig_username=ig_username,
                    message_type='user',
                    message_text=message_text or '',
                    message_timestamp=user_message_timestamp_iso,
                )
            except Exception as persist_e:
                logger.warning(
                    f"[AdResponse] Could not append user message for {ig_username}: {persist_e}")

            # Idempotency: avoid queuing duplicate reviews for the same incoming text
            # within a short window
            review_status = 'auto_scheduled' if should_auto_process else 'pending_review'
            review_id = add_response_to_review_queue(
                user_ig_username=ig_username,
                user_subscriber_id=subscriber_id,
                incoming_message_text=processed_message_text,
                incoming_message_timestamp=user_message_timestamp_iso,
                generated_prompt_text=prompt,
                proposed_response_text=ai_response,
                prompt_type="facebook_ad_response",
                status=review_status
            )

            # If auto mode is active, schedule the response
            if should_auto_process and review_id:
                try:
                    # Create scheduled response entry directly
                    from datetime import datetime, timedelta
                    import random

                    # Calculate delay (30-90 seconds for immediate response)
                    delay_seconds = random.randint(30, 90)
                    scheduled_time = datetime.now() + timedelta(seconds=delay_seconds)

                    # Insert into scheduled_responses table
                    conn = sqlite3.connect(
                        r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite")
                    cursor = conn.cursor()

                    # Ensure table exists
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS scheduled_responses (
                            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            review_id INTEGER,
                            user_ig_username TEXT,
                            user_subscriber_id TEXT,
                            response_text TEXT,
                            incoming_message_text TEXT,
                            incoming_message_timestamp TEXT,
                            user_response_time TEXT,
                            calculated_delay_minutes REAL,
                            scheduled_send_time TEXT,
                            status TEXT DEFAULT 'scheduled',
                            user_notes TEXT,
                            manual_context TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    cursor.execute("""
                        INSERT INTO scheduled_responses (
                            review_id, user_ig_username, user_subscriber_id, response_text,
                            incoming_message_text, incoming_message_timestamp, user_response_time,
                            calculated_delay_minutes, scheduled_send_time, status, user_notes, manual_context
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        review_id,
                        ig_username,
                        subscriber_id,
                        ai_response,
                        processed_message_text,
                        user_message_timestamp_iso,
                        user_message_timestamp_iso,
                        delay_seconds / 60.0,  # Convert to minutes
                        scheduled_time.isoformat(),
                        'scheduled',
                        '[AUTO-SCHEDULED] Vegan Ad Response',
                        ''
                    ))

                    conn.commit()
                    conn.close()

                    logger.info(
                        f"[AdResponse] ✅ Auto-scheduled ad response for {ig_username} (Review ID: {review_id})")
                    logger.info(
                        f"[AdResponse] 📅 Will send at: {scheduled_time.strftime('%H:%M:%S')}")

                except Exception as e:
                    logger.error(
                        f"[AdResponse] Error scheduling auto response: {e}")
            elif review_id:
                logger.info(
                    f"[AdResponse] Queued ad response for manual review (Review ID: {review_id})")
            else:
                logger.error(
                    f"[AdResponse] ❌ Failed to queue ad response for {ig_username}")

            # Do NOT log AI response here to avoid duplicates; it will be logged on send by the auto-sender

            return True
        except Exception as e:
            logger.error(
                f"[AdResponse] Error handling ad response for {ig_username}: {e}", exc_info=True)
            return False

    @staticmethod
    def _advance_script_state(current_state: str, message_text: str) -> str:
        """Advance script state based on user response patterns."""
        try:
            message_lower = message_text.lower()

            # State progression logic for vegan challenge flow
            if current_state == 'step1':
                # After initial interest, move to step2 (goal gathering)
                return 'step2'

            elif current_state == 'step2':
                # After they share goals/struggles, move to step3 (call proposal)
                if len(message_text.split()) > 3:  # Substantial response about goals
                    return 'step3'
                return 'step2'  # Stay in step2 if response too short

            elif current_state == 'step3':
                # After call proposal, check their response
                if any(word in message_lower for word in ['yes', 'sure', 'okay', 'ok', 'sounds good', 'definitely']):
                    return 'step4'  # They agreed to call - send booking link
                elif any(word in message_lower for word in ['no', 'not really', 'cant', 'busy', 'maybe later']):
                    return 'step2'  # They declined call - back to gathering info
                return 'step3'  # Stay in step3 if unclear response

            elif current_state == 'step4':
                # After booking link sent, conversation complete or back to step2 for more info
                if any(word in message_lower for word in ['booked', 'scheduled', 'thanks', 'thank you']):
                    return 'completed'
                return 'step2'  # Continue gathering info if they have questions

            elif current_state == 'completed':
                # Keep them in completed state
                return 'completed'

            else:
                # Default fallback
                return 'step2'

        except Exception as e:
            logger.error(f"Error advancing script state: {e}")
            return current_state  # Stay in current state if error
