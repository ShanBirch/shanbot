"""
Simplified Ad-Only Action Router
===============================
Focuses ONLY on detecting and handling ad responses - no calorie tracking, no other complex flows.
This is for when you just want to run ads and get people to the sign-up link.
"""

from action_handlers.ad_response_handler import AdResponseHandler
from webhook_handlers import get_user_data
from app.db_backend import (
    add_message_to_history as db_add_message_to_history,
    add_response_to_review_queue as db_add_response_to_review_queue,
    set_user_ad_flow as db_set_user_ad_flow,
)
import logging
from typing import Dict, Any

logger = logging.getLogger("shanbot_ads_only")


class AdOnlyRouter:
    """Simplified router that ONLY handles ad responses - nothing else."""

    @staticmethod
    async def route_webhook_message(ig_username: str, message_text: str, subscriber_id: str,
                                    first_name: str, last_name: str, user_message_timestamp_iso: str, fb_ad: bool = False) -> Dict[str, Any]:
        """Route incoming webhook message - ad responses only."""
        try:
            logger.info(
                f"[AdOnly] Processing message from {ig_username}: '{message_text[:50]}...'")

            # Get user data
            _, metrics, _ = get_user_data(ig_username, subscriber_id)

            # Check if user is already in ad flow
            is_in_ad_flow = metrics.get('is_in_ad_flow', False)

            if is_in_ad_flow:
                logger.info(
                    f"[AdOnly] {ig_username} already in ad flow - continuing conversation")

                # Get their scenario and continue the flow
                scenario = metrics.get('ad_scenario', 1)
                success = await AdResponseHandler.handle_ad_response(
                    ig_username, message_text, subscriber_id, first_name, last_name, user_message_timestamp_iso,
                    scenario, metrics, fb_ad
                )
                return {
                    "status": "continued_ad_flow",
                    "success": success
                }

            # Detect if this is a new ad response
            is_ad_response, scenario, ad_confidence = await AdResponseHandler.is_ad_response(
                ig_username, message_text, metrics
            )

            logger.info(
                f"[AdOnly] Ad detection: is_ad={is_ad_response}, confidence={ad_confidence}%")

            if is_ad_response and ad_confidence >= 40:  # Lower threshold for better catch rate
                logger.info(
                    f"[AdOnly] Starting ad flow for {ig_username} (confidence: {ad_confidence}%)")

                success = await AdResponseHandler.handle_ad_response(
                    ig_username, message_text, subscriber_id, first_name, last_name, user_message_timestamp_iso,
                    scenario, metrics, fb_ad
                )
                return {
                    "status": "started_ad_flow",
                    "success": success
                }
            else:
                # Not an ad response - send a simple generic response
                logger.info(
                    f"[AdOnly] Not ad response - sending generic message for {ig_username}")

                success = await AdOnlyRouter._handle_non_ad_message(
                    ig_username, message_text, subscriber_id, first_name, last_name, user_message_timestamp_iso
                )
                return {
                    "status": "generic_response",
                    "success": success
                }

        except Exception as e:
            logger.error(
                f"[AdOnly] Error routing message for {ig_username}: {e}")
            return {
                "status": "error",
                "message": f"Error processing message: {str(e)}"
            }

    @staticmethod
    async def _handle_non_ad_message(ig_username: str, message_text: str, subscriber_id: str,
                                     first_name: str, last_name: str, user_message_timestamp_iso: str) -> bool:
        """Handle messages that aren't ad responses with a simple generic response."""
        try:
            # Persist the incoming user message
            db_add_message_to_history(
                ig_username=ig_username,
                message_type='user',
                message_text=message_text or '',
                message_timestamp=user_message_timestamp_iso
            )

            # Simple generic response - keep it SHORT (Shannon's voice!)
            generic_responses = [
                "Heya! Thanks for reaching out 😊",
                "Hey there! What's up?",
                "Hi! How's things going?",
                "Heya! What can I help with?",
                "Hey! Thanks for the message!"
            ]

            import random
            response = random.choice(generic_responses)

            # Add to review queue for manual approval
            review_id = db_add_response_to_review_queue(
                user_ig_username=ig_username,
                user_subscriber_id=subscriber_id,
                incoming_message_text=message_text,
                incoming_message_timestamp=user_message_timestamp_iso,
                generated_prompt_text="Generic non-ad response",
                proposed_response_text=response,
                prompt_type="generic_response",
                status='pending_review'  # Always manual for non-ad messages
            )

            if review_id:
                logger.info(
                    f"[AdOnly] Queued generic response for {ig_username} (Review ID: {review_id})")
                return True
            else:
                logger.error(
                    f"[AdOnly] Failed to queue generic response for {ig_username}")
                return False

        except Exception as e:
            logger.error(
                f"[AdOnly] Error handling non-ad message for {ig_username}: {e}")
            return False

    @staticmethod
    def force_ad_mode_for_user(ig_username: str, subscriber_id: str, scenario: int = 1) -> bool:
        """Force a user into ad mode - useful for testing or manual override."""
        try:
            ok = db_set_user_ad_flow(
                ig_username=ig_username,
                subscriber_id=subscriber_id,
                scenario=scenario,
                next_state='step1',
                lead_source='manual_ad_mode',
            )
            if ok:
                logger.info(
                    f"[AdOnly] Forced {ig_username} into ad mode (scenario {scenario})")
            else:
                logger.error(
                    f"[AdOnly] Failed to force {ig_username} into ad mode")
            return ok

        except Exception as e:
            logger.error(
                f"[AdOnly] Error forcing ad mode for {ig_username}: {e}")
            return False
