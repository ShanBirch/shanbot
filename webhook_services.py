"""
Shanbot Webhook Services
========================
Supporting services for the main webhook including ad response handling, 
Wix onboarding, and other specialized functionality.
"""

import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from webhook_handlers import call_gemini_with_retry, update_analytics_data, get_user_data
from app.dashboard_modules.notifications import add_email_collected_notification
from app.dashboard_modules.dashboard_sqlite_utils import add_paid_challenge_booking, get_db_connection
from app import prompts

logger = logging.getLogger("shanbot_services")

# ============================================================================
# AD RESPONSE HANDLER
# ============================================================================


class AdResponseHandler:
    """Handles Facebook/Instagram ad responses and plant-based challenge leads."""

    @staticmethod
    async def detect_ad_intent(ig_username: str, message_text: str, conversation_history: list) -> tuple[bool, int, int]:
        """Detect if message is responding to a plant-based challenge ad."""
        # Exact trigger matches (100% confidence)
        exact_triggers = [
            "Can you tell me more about your Vegan Weight Loss Challenge",
            "I'm Ready to join the Vegan Weight Loss Challenge",
            "I'm ready for the Vegetarian Weight Loss Challenge!",
            "Can you tell me more about your Vegetarian Weight Loss Challenge"
        ]

        for trigger in exact_triggers:
            if trigger.lower() == message_text.lower().strip():
                challenge_type = "vegan" if "vegan" in trigger.lower() else "vegetarian"
                scenario = 1 if challenge_type == "vegan" else 2
                logger.info(
                    f"[AdIntent] Exact trigger match: {trigger} -> {challenge_type}")
                return True, scenario, 100

        # AI-powered detection for more nuanced cases
        history_context = "\n".join(
            [f"{msg.get('type', 'user')}: {msg.get('text', '')}" for msg in conversation_history[-5:]])

        ad_detection_prompt = f"""
        You are analyzing Instagram DMs to Shannon (fitness coach) to determine if this is someone responding to a Plant-Based Challenge ad.

        CONVERSATION HISTORY:
        {history_context if history_context else "[New conversation]"}

        CURRENT MESSAGE: "{message_text}"

        ANALYSIS CRITERIA:
        🎯 Strong Plant-Based Challenge Ad Indicators:
        - Direct mentions: "vegan challenge", "vegetarian challenge", "plant based challenge"
        - Challenge terms: "28 day challenge", "weight loss challenge", "fitness challenge"
        - Ad context: "saw your ad", "from Facebook", "from Instagram", "interested in your program"
        - Diet + fitness: "vegan" + "weight loss/fitness", "vegetarian" + "program"

        🚫 NOT Plant-Based Ad Response:
        - Generic vegan chat without challenge context
        - Pain/injury focus without plant-based mention
        - General fitness questions without plant-based context

        OUTPUT FORMAT:
        {{
            "is_ad_response": true/false,
            "challenge_type": "vegan/vegetarian/plant_based",
            "confidence": 0-100,
            "reasoning": "Brief explanation"
        }}
        """

        try:
            response = await call_gemini_with_retry("gemini-2.0-flash-thinking-exp-01-21", ad_detection_prompt)
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)

            if json_match:
                result = json.loads(json_match.group())
                is_ad = result.get('is_ad_response', False)
                challenge_type = result.get('challenge_type', 'plant_based')
                confidence = result.get('confidence', 0)

                scenario_map = {'vegan': 1, 'vegetarian': 2, 'plant_based': 3}
                scenario = scenario_map.get(challenge_type, 1)

                logger.info(
                    f"[AdIntent] AI detection: ad={is_ad}, type={challenge_type}, confidence={confidence}%")
                return is_ad, scenario, confidence

        except Exception as e:
            logger.error(f"[AdIntent] Detection error: {e}")

        return False, 1, 0

    @staticmethod
    async def handle_ad_response(ig_username: str, message_text: str, subscriber_id: str,
                                 first_name: str, last_name: str, user_message_timestamp_iso: str) -> bool:
        """Handle ad response using appropriate script."""
        try:
            # Get user data and ad state
            _, metrics, _ = get_user_data(ig_username, subscriber_id)
            is_in_ad_flow = metrics.get('is_in_ad_flow', False)
            current_state = metrics.get('ad_script_state', 'step1')
            scenario = metrics.get('ad_scenario', 1)
            lead_source = metrics.get('lead_source', 'general')

            if not is_in_ad_flow:
                logger.info(f"[AdResponse] User {ig_username} not in ad flow")
                return False

            # Build context
            bio_context = metrics.get(
                'client_analysis', {}).get('profile_bio', '')
            conversation_history = metrics.get('conversation_history', [])
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_conversation = "\n".join(
                [f"{msg.get('type', 'user')}: {msg.get('text', '')}" for msg in conversation_history])
            full_conversation += f"\nUser: {message_text}"

            # Choose appropriate prompt
            if lead_source == 'paid_plant_based_challenge':
                challenge_types = {1: 'vegan',
                                   2: 'vegetarian', 3: 'plant_based'}
                challenge_type = challenge_types.get(scenario, 'plant_based')

                prompt = prompts.PAID_VEGAN_CHALLENGE_PROMPT_TEMPLATE.format(
                    current_melbourne_time_str=current_time,
                    ig_username=ig_username,
                    challenge_type=challenge_type,
                    script_state=current_state,
                    bio=bio_context,
                    full_conversation=full_conversation
                )
            else:
                prompt = prompts.COMBINED_AD_RESPONSE_PROMPT_TEMPLATE.format(
                    current_melbourne_time_str=current_time,
                    ig_username=ig_username,
                    script_state=current_state,
                    ad_scenario=scenario,
                    bio=bio_context,
                    full_conversation=full_conversation
                )

            # Generate response
            from webhook_handlers import get_ai_response
            response = await get_ai_response(prompt)
            if not response:
                logger.error(
                    f"[AdResponse] No response generated for {ig_username}")
                return False

            # Check for email collection
            if lead_source == 'plant_based_challenge':
                await AdResponseHandler._detect_and_store_challenge_email(ig_username, message_text, subscriber_id, scenario)

            # Check for booking confirmation
            if lead_source == 'paid_plant_based_challenge':
                await AdResponseHandler._detect_and_confirm_paid_booking(ig_username, message_text, subscriber_id)

            # Queue response for review
            from app.dashboard_modules.dashboard_sqlite_utils import add_response_to_review_queue
            review_id = add_response_to_review_queue(
                user_ig_username=ig_username,
                user_subscriber_id=subscriber_id,
                incoming_message_text=message_text,
                incoming_message_timestamp=user_message_timestamp_iso,
                generated_prompt_text=prompt,
                proposed_response_text=response,
                prompt_type="plant_based_challenge" if lead_source == 'plant_based_challenge' else "facebook_ad"
            )

            if review_id:
                logger.info(
                    f"[AdResponse] Queued response (ID: {review_id}) for {ig_username}")

                # Update analytics
                update_analytics_data(
                    ig_username, message_text, response, subscriber_id, first_name, last_name)

                # Advance state
                next_state = 'completed' if current_state == 'step3' else f"step{int(current_state[-1]) + 1}"
                update_analytics_data(
                    ig_username, "", "", subscriber_id, first_name, last_name, ad_script_state=next_state)

                if next_state == 'completed':
                    update_analytics_data(
                        ig_username, "", "", subscriber_id, first_name, last_name, is_in_ad_flow=False)

                    # Record paid challenge booking if applicable
                    if lead_source == 'paid_plant_based_challenge':
                        try:
                            add_paid_challenge_booking(ig_username)
                            logger.info(
                                f"[AdResponse] Recorded paid challenge booking for {ig_username}")
                        except Exception as e:
                            logger.error(
                                f"[AdResponse] Booking record failed: {e}")

                return True
            else:
                logger.error(
                    f"[AdResponse] Failed to queue response for {ig_username}")
                return False

        except Exception as e:
            logger.error(f"[AdResponse] Error handling ad response: {e}")
            return False

    @staticmethod
    async def _detect_and_store_challenge_email(ig_username: str, message_text: str, subscriber_id: str, scenario: int):
        """Detect and store email from challenge responses."""
        import re

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message_text)

        if emails:
            email = emails[0]
            challenge_types = {1: 'vegan', 2: 'vegetarian', 3: 'plant_based'}
            challenge_type = challenge_types.get(scenario, 'plant_based')

            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE users 
                    SET challenge_email = ?, challenge_type = ?, challenge_signup_date = ?, ad_script_state = 'step5'
                    WHERE ig_username = ?
                """, (email, challenge_type, datetime.now().isoformat(), ig_username))

                conn.commit()
                conn.close()

                add_email_collected_notification(ig_username, email)
                logger.info(
                    f"[Email] Collected challenge email for {ig_username}: {email}")

            except Exception as e:
                logger.error(f"[Email] Storage failed for {ig_username}: {e}")

    @staticmethod
    async def _detect_and_confirm_paid_booking(ig_username: str, message_text: str, subscriber_id: str):
        """Detect booking confirmation for paid challenges."""
        confirmation_prompt = f"""
        Does this message confirm the user has booked a call/appointment/session?
        Look for: "booked", "done", "all set", "scheduled it", "just booked"
        
        Message: "{message_text}"
        
        Reply with just "YES" or "NO".
        """

        try:
            confirmation = await call_gemini_with_retry("gemini-2.0-flash-thinking-exp-01-21", confirmation_prompt)

            if "YES" in confirmation.upper():
                add_paid_challenge_booking(ig_username)

                from app.dashboard_modules.notifications import add_notification
                add_notification(
                    title="✅ Insight Call Booked!",
                    message=f"@{ig_username} has booked their paid challenge insight call.",
                    notification_type="success",
                    username=ig_username
                )

                logger.info(
                    f"[Booking] Confirmed paid booking for {ig_username}")
                return True

        except Exception as e:
            logger.error(f"[Booking] Detection failed for {ig_username}: {e}")

        return False

# ============================================================================
# WIX ONBOARDING HANDLER
# ============================================================================


class WixOnboardingHandler:
    """Handles Wix form submissions for direct onboarding."""

    @staticmethod
    def map_wix_form_to_client_data(form_data: Dict) -> Optional[Dict]:
        """Map Wix form data to client data structure."""
        try:
            # Handle Wix form structure
            submissions = form_data.get('submissions', [])
            field_map = {}

            for submission in submissions:
                label = submission.get('label', '').lower()
                value = submission.get('value', '')
                field_map[label] = value

            # Extract personal info
            email = field_map.get('email') or form_data.get('email')
            first_name = field_map.get(
                'first name') or field_map.get('firstname')
            last_name = field_map.get('last name') or field_map.get('lastname')
            phone = field_map.get('phone') or field_map.get('phonenumber')

            full_name = f"{first_name or ''} {last_name or ''}".strip(
            ) or 'Unknown'

            # Physical stats
            weight_str = field_map.get('weight', '').replace(
                'kgs', '').replace('kg', '').strip()
            weight = float(weight_str) if weight_str.replace(
                '.', '').isdigit() else 70

            height_str = field_map.get('height', '').replace('cm', '').strip()
            height = float(height_str) if height_str.replace(
                '.', '').isdigit() else 170

            # Calculate age from birthday
            birthday = field_map.get('birthday')
            age = 30  # default
            if birthday:
                try:
                    birth_date = datetime.strptime(birthday, '%Y-%m-%d')
                    today = datetime.now()
                    age = today.year - birth_date.year - \
                        ((today.month, today.day) <
                         (birth_date.month, birth_date.day))
                except:
                    age = 30

            # Fitness and dietary info
            primary_goal = field_map.get('fitness goal') or 'muscle_gain'
            activity_level = field_map.get(
                'activity level') or 'moderately_active'
            gym_access = field_map.get('gym access') or field_map.get(
                'training location') or 'full_gym'
            training_days = field_map.get('training days') or 'monday-friday'
            training_experience = field_map.get(
                'training experience') or 'beginner'

            dietary_type = form_data.get('dietaryType') or 'plant-based'
            dietary_restrictions = form_data.get('dietaryRestrictions') or ''
            disliked_foods = form_data.get('dislikedFoods') or ''

            regular_breakfast = form_data.get('regularBreakfast') or ''
            regular_lunch = form_data.get('regularLunch') or ''
            regular_dinner = form_data.get('regularDinner') or ''

            exercise_dislikes = form_data.get('exerciseDislikes') or ''

            # Build client data structure
            client_data = {
                "personal_info": {
                    "email": {"value": email or "", "confidence": 95},
                    "full_name": {"value": full_name, "confidence": 95},
                    "phone": {"value": phone or "", "confidence": 95},
                    "age": {"value": int(age), "confidence": 90}
                },
                "physical_info": {
                    "weight": {"value": weight, "unit": "kg", "confidence": 95},
                    "height": {"value": height, "unit": "cm", "confidence": 95},
                    "target_weight": {"value": weight + 5 if primary_goal == 'muscle_gain' else weight - 5, "unit": "kg", "confidence": 90},
                    "primary_fitness_goal": {"value": primary_goal, "confidence": 95}
                },
                "training_info": {
                    "activity_level": {"value": activity_level, "confidence": 90},
                    "gym_access": {"value": gym_access, "confidence": 95},
                    "training_days": {"value": training_days, "confidence": 90},
                    "training_experience": {"value": training_experience, "confidence": 85}
                },
                "dietary_info": {
                    "diet_type": {"value": dietary_type, "confidence": 95},
                    "dietary_restrictions": {"value": dietary_restrictions, "confidence": 90},
                    "disliked_foods": {"value": disliked_foods, "confidence": 90},
                    "regular_meals": {
                        "breakfast": {"value": regular_breakfast or "oats with protein", "confidence": 85},
                        "lunch": {"value": regular_lunch or "salad with protein", "confidence": 85},
                        "dinner": {"value": regular_dinner or "plant-based protein with vegetables", "confidence": 85}
                    }
                },
                "exercise_preferences": {
                    "dislikes": {"value": exercise_dislikes, "confidence": 90},
                    "current_routine": {"value": "none", "confidence": 95}
                }
            }

            logger.info(
                f"[WixMapping] Successfully mapped form data for: {full_name}")
            return client_data

        except Exception as e:
            logger.error(f"[WixMapping] Error mapping form data: {e}")
            return None

    @staticmethod
    async def process_wix_onboarding(ig_username: str, subscriber_id: str, client_data: Dict):
        """Process Wix onboarding using existing system."""
        try:
            logger.info(f"[WixOnboarding] Processing for {ig_username}")

            from post_onboarding_handler import PostOnboardingHandler
            import os

            # Get API key
            gemini_api_key = os.getenv(
                "GEMINI_API_KEY") or "AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y"
            handler = PostOnboardingHandler(gemini_api_key)

            # Convert to expected format
            converted_data = WixOnboardingHandler._convert_to_expected_format(
                client_data)
            if not converted_data:
                logger.error(
                    f"[WixOnboarding] Failed to convert data for {ig_username}")
                return False

            # Calculate nutrition
            nutrition_data = handler._calculate_nutrition(converted_data)
            if not nutrition_data:
                logger.error(
                    f"[WixOnboarding] Failed to calculate nutrition for {ig_username}")
                return False

            # Process onboarding
            success_flags = await handler.process_onboarding_with_fixed_data(
                ig_username=ig_username,
                subscriber_id=subscriber_id,
                direct_client_data=converted_data,
                nutrition_targets_override=nutrition_data
            )

            client_added = success_flags.get("client_added_success", False)
            meal_plan_uploaded = success_flags.get(
                "meal_plan_upload_success", False)
            workout_program_built = success_flags.get(
                "workout_program_build_success", False)

            overall_success = client_added and meal_plan_uploaded and workout_program_built

            if overall_success:
                logger.info(f"[WixOnboarding] Success for {ig_username}")

                # Store in database
                try:
                    import sqlite3
                    conn = sqlite3.connect("app/analytics_data_good.sqlite")
                    cursor = conn.cursor()

                    client_full_name = client_data.get('personal_info', {}).get(
                        'full_name', {}).get('value', ig_username)
                    client_first_name = client_data.get('personal_info', {}).get(
                        'first_name', {}).get('value', '')
                    client_last_name = client_data.get('personal_info', {}).get(
                        'last_name', {}).get('value', '')

                    cursor.execute("""
                        INSERT OR REPLACE INTO users 
                        (ig_username, subscriber_id, first_name, last_name, email, source, created_at, client_status)
                        VALUES (?, ?, ?, ?, ?, 'wix_form', ?, 'Trial Client')
                    """, (
                        ig_username, subscriber_id, client_first_name, client_last_name,
                        client_data.get('personal_info', {}).get(
                            'email', {}).get('value', ''),
                        datetime.now().isoformat()
                    ))

                    conn.commit()
                    conn.close()
                    logger.info(
                        f"[WixOnboarding] Stored user record for {ig_username}")

                except Exception as db_error:
                    logger.error(f"[WixOnboarding] Database error: {db_error}")

                # Add dashboard notification
                notification_message = f"New Trial Member - {client_full_name} (IG: @{ig_username}): "
                notification_message += "Client Added to Trainerize. " if client_added else "Client addition FAILED. "
                notification_message += "Meal Plan Added. " if meal_plan_uploaded else "Meal Plan FAILED. "
                notification_message += "Workout Program Added." if workout_program_built else "Workout Program FAILED."

                from webhook_handlers import add_todo_item
                add_todo_item(ig_username, client_full_name,
                              notification_message, "pending")

            else:
                logger.error(f"[WixOnboarding] Failed for {ig_username}")

            return overall_success

        except Exception as e:
            logger.error(f"[WixOnboarding] Processing error: {e}")
            return False

    @staticmethod
    def _convert_to_expected_format(wix_client_data: Dict) -> Dict:
        """Convert Wix data to expected format."""
        try:
            personal_info = wix_client_data.get('personal_info', {})
            physical_info = wix_client_data.get('physical_info', {})
            training_info = wix_client_data.get('training_info', {})
            dietary_info = wix_client_data.get('dietary_info', {})

            # Map activity level to integer
            activity_level_str = training_info.get('activity_level', {}).get(
                'value', 'moderately_active').lower()
            activity_level_map = {
                'sedentary': 1, 'lightly active': 2, 'moderately active': 3,
                'very active': 4, 'extra active': 5
            }
            converted_activity_level = activity_level_map.get(
                activity_level_str, 3)

            # Build converted structure
            converted_data = {
                "personal_info": {
                    "email": {"value": personal_info.get('email', {}).get('value', ''), "confidence": 95},
                    "full_name": {"value": personal_info.get('full_name', {}).get('value', ''), "confidence": 95},
                    "phone": {"value": personal_info.get('phone', {}).get('value', ''), "confidence": 95},
                    "birth_date": {"value": personal_info.get('birth_date', {}).get('value', '1990-06-05'), "confidence": 95},
                    "gender": {"value": personal_info.get('gender', {}).get('value', 'male'), "confidence": 95}
                },
                "physical_info": {
                    "current_weight_kg": {"value": float(physical_info.get('weight', {}).get('value', 70)), "confidence": 95},
                    "height_cm": {"value": float(physical_info.get('height', {}).get('value', 170)), "confidence": 95},
                    "primary_fitness_goal": {"value": physical_info.get('primary_fitness_goal', {}).get('value', 'muscle_gain'), "confidence": 95},
                    "specific_weight_goal_kg": {"value": float(physical_info.get('target_weight', {}).get('value', 75)), "confidence": 90},
                    "activity_level": {"value": converted_activity_level, "confidence": 95}
                },
                "dietary_info": {
                    "diet_type": {"value": dietary_info.get('diet_type', {}).get('value', 'plant-based'), "confidence": 95},
                    "regular_meals": dietary_info.get('regular_meals', {}),
                    "meal_notes": {"value": dietary_info.get('meal_notes', {}).get('value', 'prefers plant-based meals'), "confidence": 95},
                    "other_dietary_restrictions": {"value": dietary_info.get('dietary_restrictions', {}).get('value', ''), "confidence": 95},
                    "disliked_foods": {"value": dietary_info.get('disliked_foods', {}).get('value', ''), "confidence": 95}
                },
                "training_info": {
                    "current_routine": {"value": training_info.get('current_routine', {}).get('value', 'none'), "confidence": 95},
                    "training_location": {"value": training_info.get('gym_access', {}).get('value', 'full_gym'), "confidence": 95},
                    "disliked_exercises": {"value": training_info.get('disliked_exercises', {}).get('value', ''), "confidence": 95},
                    "liked_exercises": {"value": training_info.get('liked_exercises', {}).get('value', ''), "confidence": 95},
                    "training_days": {"value": training_info.get('training_days', {}).get('value', 'monday-friday'), "confidence": 95}
                },
                "general_info": {
                    "location": {"value": personal_info.get('location', {}).get('value', 'Melbourne'), "confidence": 95}
                }
            }

            logger.info(
                f"[WixConversion] Successfully converted data structure")
            return converted_data

        except Exception as e:
            logger.error(f"[WixConversion] Conversion error: {e}")
            return None
