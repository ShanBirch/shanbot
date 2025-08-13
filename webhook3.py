
# NOTE: The following analytics helper snippet was left at module top-level, which breaks execution.
# It has been commented out to resolve a syntax error (return outside function).
# If needed, move this logic inside the appropriate handler function.
#
# logger.info(
#     f"Finished _analyze_form_check_video for {ig_username}. AI Response for analytics: {ai_response_for_analytics}")
# # Return these for the main function to log
# return user_message_for_analytics, ai_response_for_analytics


# Global dictionary to track pending form check requests
form_check_pending: Dict[str, bool] = {}

# --- Add post-processing function to filter Gemini responses ---


async def filter_shannon_response(original_response: str, user_message: str = None) -> str:
    """
    Ensures the response is a direct, in-character reply from Shannon. If not, rewrites it as one.
    The filter should be conservative: if the original response is already good, it should be returned unchanged.
    """
    # Example removed for brevity, as it's not directly used by the model, only for human understanding of Shannon's style.

    user_message_block = f"[CLIENT'S MESSAGE (if provided)]\n{user_message}\n" if user_message else "(No specific client message provided for this turn)"

    filter_prompt = f"""
Your task is to ensure an AI-generated response sounds like it's from Shannon, a friendly and knowledgeable fitness coach, and that it's a direct reply to a client. Shannon uses casual Aussie colloquialisms.

Here is the AI-generated response you need to evaluate:
[GENERATED RESPONSE]
{original_response}

Here was the client's message the AI was responding to (if available):
{user_message_block}

**Crucial Evaluation & Decision Process:**

1.  **Is the [GENERATED RESPONSE] ALREADY a direct, conversational message that Shannon would send?**
    *   Does it sound like a human coach chatting on Instagram?
    *   Is it free of any AI self-references (e.g., \"As an AI...\", \"I am a language model...\"), meta-commentary about the conversation (e.g., \"This response aims to...\", \"Based on the conversation history...\"), or explanations of its own thought process?

2.  **DECISION:**
    *   **IF YES** (the [GENERATED RESPONSE] is already a good, direct, in-character message from Shannon, and contains NO AI self-references or meta-commentary as described above):
        **Your output MUST be the [GENERATED RESPONSE] EXACTLY as it is.** Do not add any extra text or explanation. Just output the original response.

    *   **IF NO** (the [GENERATED RESPONSE] contains AI-like meta-commentary, explains itself, refers to itself as an AI, or is otherwise clearly not a direct message Shannon would type):
        **Then you MUST rewrite it.** Your rewritten message should be a perfect, direct, in-character reply that Shannon would send, completely removing any AI-like analysis or self-explanation. Output ONLY the rewritten message.

Your Output (either the original [GENERATED RESPONSE] or your rewritten version):
"""

    # Use the fastest model for filtering
    filtered = await call_gemini_with_retry(GEMINI_MODEL_FLASH, filter_prompt)

    # Clean up any markdown or code block formatting from the filter's output
    if filtered:
        filtered = filtered.strip()
        # Remove potential ```json or ``` markdown blocks if Gemini adds them
        if filtered.startswith("```json"):
            filtered = filtered[len("```json"):].strip()
            if filtered.endswith("```"):
                filtered = filtered[:-len("```")].strip()
        elif filtered.startswith("```"):
            filtered = filtered[len("```"):].strip()
            if filtered.endswith("```"):
                filtered = filtered[:-len("```")].strip()

    # Log if a change was made
    original_check = original_response.strip().lower()
    filtered_check = filtered.strip().lower() if filtered else ""

    if filtered and original_check != filtered_check:
        logger.info(
            f"[FILTER] Gemini response was modified by the filter.\nOriginal: {original_response}\nFiltered: {filtered}")
    elif not filtered:
        logger.warning(
            f"[FILTER] Filter returned an empty response. Falling back to original. Original: {original_response}")
        return original_response  # Fallback to original if filter fails to produce content
    else:
        logger.info(
            "[FILTER] Gemini response passed filter unchanged (or with only minor whitespace/case changes).")

    # Return filtered, or original if filtering resulted in None/empty
    return filtered or original_response


@app.post("/webhook/wix-onboarding")
async def process_wix_form_submission(request: Request, background_tasks: BackgroundTasks):
    """
    Process Wix form submissions from the coaching onboarding form.
    Maps Wix form data to existing client_data structure and triggers meal plan generation.
    """
    try:
        # Get the form data from Wix
        raw_body = await request.body()
        payload_str = raw_body.decode('utf-8')
        logger.info(
            f"[WIX-WEBHOOK] Received raw payload: {payload_str[:500]}...")

        try:
            wix_data = json.loads(payload_str)
            logger.info(
                f"[WIX-WEBHOOK] Parsed Wix form data: {json.dumps(wix_data, indent=2)[:1000]}...")
        except json.JSONDecodeError:
            logger.error("[WIX-WEBHOOK] Failed to parse JSON payload")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        # Extract form fields from Wix data
        # Note: Wix form field structure may vary - we'll need to adjust based on actual payload
        # Handle different Wix webhook structures
        form_data = wix_data.get('data', {}) or wix_data

        # Map Wix form data to our client_data structure
        client_data = _map_wix_form_to_client_data(form_data)

        if not client_data:
            logger.error(
                "[WIX-WEBHOOK] Failed to map Wix form data to client structure")
            return PlainTextResponse("Error: Could not process form data", status_code=400)

        logger.info(
            f"[WIX-WEBHOOK] Successfully mapped Wix data to client structure for: {client_data.get('personal_info', {}).get('full_name', {}).get('value', 'Unknown')}")

        # Generate a fake Instagram username and subscriber_id for the system
        email = client_data['personal_info']['email']['value']
        # Create username from email
        ig_username = f"wix_user_{email.split('@')[0]}"
        subscriber_id = f"wix_{int(time.time())}"  # Timestamp-based ID

        # Process the onboarding in the background using existing system
        background_tasks.add_task(
            _process_wix_onboarding_background,
            ig_username,
            subscriber_id,
            client_data
        )

        logger.info(
            f"[WIX-WEBHOOK] Scheduled background processing for {ig_username}")

        return PlainTextResponse("Form submitted successfully! Your meal plan and workout program are being created.", status_code=200)

    except Exception as e:
        logger.error(
            f"[WIX-WEBHOOK] Error processing Wix form submission: {str(e)}")
        logger.error(
            f"[WIX-WEBHOOK] Exception details: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Error processing form submission: {str(e)}")


def _map_wix_form_to_client_data(form_data: Dict) -> Optional[Dict]:
    """
    Map Wix form fields to the client_data structure expected by the meal plan system.
    This matches the structure used in post_onboarding_handler.py
    """
    try:
        # Extract common field patterns from Wix forms
        # Note: Field names will need to be adjusted based on actual Wix form field names

        # Handle Wix form structure - data is in submissions array
        submissions = form_data.get('submissions', [])

        # Create lookup dictionary from submissions
        field_map = {}
        for submission in submissions:
            label = submission.get('label', '').lower()
            value = submission.get('value', '')
            field_map[label] = value

        # Personal Information - using Wix form labels
        email = field_map.get('email') or form_data.get('email')
        first_name = field_map.get('first name') or field_map.get('firstname')
        last_name = field_map.get('last name') or field_map.get('lastname')
        phone = field_map.get('phone') or field_map.get('phonenumber')

        full_name = f"{first_name or ''} {last_name or ''}".strip()
        if not full_name:
            full_name = 'Unknown'

        # Physical Stats - using Wix form labels
        weight_str = field_map.get('weight', '').replace(
            'kgs', '').replace('kg', '').strip()
        weight = float(weight_str) if weight_str.replace(
            '.', '').isdigit() else 70

        height_str = field_map.get('height', '').replace('cm', '').strip()
        height = float(height_str) if height_str.replace(
            '.', '').isdigit() else 170

        # Calculate age from birthday if available
        birthday = field_map.get('birthday')
        age = 30  # default
        if birthday:
            try:
                from datetime import datetime
                birth_date = datetime.strptime(birthday, '%Y-%m-%d')
                today = datetime.now()
                age = today.year - birth_date.year - \
                    ((today.month, today.day) < (birth_date.month, birth_date.day))
            except:
                age = 30

        # Fitness Information - using Wix form labels
        primary_goal = field_map.get('fitness goal') or 'muscle_gain'
        activity_level = field_map.get('activity level') or 'moderately_active'
        gym_access = field_map.get('gym access') or field_map.get(
            'training location') or 'full_gym'

        # Training Information - using Wix form labels and field names
        training_days = field_map.get('training days') or form_data.get(
            'field:which_days_time_have_you_set_aside_to_train', 'monday-friday')
        training_experience = field_map.get(
            'training experience') or 'beginner'

        # Dietary Information
        dietary_type = form_data.get('dietaryType') or form_data.get(
            'diet_type') or 'plant-based'  # Default to plant-based
        dietary_restrictions = form_data.get('dietaryRestrictions') or form_data.get(
            'restrictions') or form_data.get('allergies')
        disliked_foods = form_data.get('dislikedFoods') or form_data.get(
            'food_dislikes') or form_data.get('dislikes')

        # Meal preferences
        regular_breakfast = form_data.get(
            'regularBreakfast') or form_data.get('breakfast_preferences')
        regular_lunch = form_data.get(
            'regularLunch') or form_data.get('lunch_preferences')
        regular_dinner = form_data.get(
            'regularDinner') or form_data.get('dinner_preferences')

        # Exercise preferences
        exercise_dislikes = form_data.get('exerciseDislikes') or form_data.get(
            'exercise_limitations') or form_data.get('exercises_to_avoid')

        # Build client_data structure matching post_onboarding_handler.py format
        client_data = {
            "personal_info": {
                "email": {"value": email or "", "confidence": 95},
                "full_name": {"value": full_name, "confidence": 95},
                "phone": {"value": phone or "", "confidence": 95},
                "age": {"value": int(age) if age and str(age).isdigit() else 30, "confidence": 90}
            },
            "physical_info": {
                "weight": {"value": weight, "unit": "kg", "confidence": 95},
                "height": {"value": height, "unit": "cm", "confidence": 95},
                "target_weight": {"value": weight + 5 if primary_goal == 'muscle_gain' else weight - 5, "unit": "kg", "confidence": 90},
                "primary_fitness_goal": {"value": primary_goal, "confidence": 95}
            },
            "training_info": {
                "activity_level": {"value": activity_level or "moderately_active", "confidence": 90},
                "gym_access": {"value": gym_access or "full_gym", "confidence": 95},
                "training_days": {"value": training_days or "3-4 days per week", "confidence": 90},
                "training_experience": {"value": training_experience or "beginner", "confidence": 85}
            },
            "dietary_info": {
                "diet_type": {"value": dietary_type, "confidence": 95},
                "dietary_restrictions": {"value": dietary_restrictions or "", "confidence": 90},
                "disliked_foods": {"value": disliked_foods or "", "confidence": 90},
                "regular_meals": {
                    "breakfast": {"value": regular_breakfast or "oats with protein", "confidence": 85},
                    "lunch": {"value": regular_lunch or "salad with protein", "confidence": 85},
                    "dinner": {"value": regular_dinner or "plant-based protein with vegetables", "confidence": 85}
                }
            },
            "exercise_preferences": {
                "dislikes": {"value": exercise_dislikes or "", "confidence": 90},
                "current_routine": {"value": "none", "confidence": 95}
            }
        }

        logger.info(
            f"[WIX-MAPPING] Successfully mapped form data for: {full_name}")
        return client_data

    except Exception as e:
        logger.error(f"[WIX-MAPPING] Error mapping Wix form data: {str(e)}")
        return None


async def _process_wix_onboarding_background(ig_username: str, subscriber_id: str, client_data: Dict):
    """
    Process Wix onboarding data through the existing meal plan system.
    This uses the same pipeline as Instagram DM onboarding but with pre-structured data.
    """
    try:
        logger.info(
            f"[WIX-BG] Starting background processing for {ig_username}")

        # Import the existing post-onboarding handler
        from post_onboarding_handler import PostOnboardingHandler

        # Initialize handler with Gemini API key - try different env var names
        gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv(
            "GOOGLE_AI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y"

        logger.info(f"[WIX-BG] Using API key: {gemini_api_key[:10]}...")

        if not gemini_api_key:
            logger.error("[WIX-BG] GEMINI_API_KEY not found in environment")
            return False

        handler = PostOnboardingHandler(gemini_api_key)

        # Convert Wix data to the format expected by the nutrition calculation
        converted_client_data = _convert_wix_data_to_expected_format(
            client_data)
        if not converted_client_data:
            logger.error(
                f"[WIX-BG] Failed to convert client data format for {ig_username}")
            return False

        # Calculate nutrition data using the handler's method
        nutrition_data = handler._calculate_nutrition(converted_client_data)
        if not nutrition_data:
            logger.error(
                f"[WIX-BG] Failed to calculate nutrition data for {ig_username}")
            return False

        logger.info(f"[WIX-BG] Calculated nutrition: {nutrition_data}")

        # Use the existing method that accepts direct client data with proper nutrition override
        success_flags = await handler.process_onboarding_with_fixed_data(
            ig_username=ig_username,
            subscriber_id=subscriber_id,
            direct_client_data=converted_client_data,
            nutrition_targets_override=nutrition_data
        )

        client_added = success_flags.get("client_added_success", False)
        meal_plan_uploaded = success_flags.get(
            "meal_plan_upload_success", False)
        workout_program_built = success_flags.get(
            "workout_program_build_success", False)

        onboarding_overall_success = client_added and meal_plan_uploaded and workout_program_built

        if onboarding_overall_success:
            logger.info(
                f"[WIX-BG] Successfully processed onboarding for {ig_username}")

            # Store the successful onboarding in our database
            try:
                import sqlite3
                SQLITE_PATH = "app/analytics_data_good.sqlite"
                conn = sqlite3.connect(SQLITE_PATH)
                c = conn.cursor()

                # Use extracted client full name for consistency and better display
                client_full_name = client_data.get('personal_info', {}).get(
                    'full_name', {}).get('value', ig_username)
                client_first_name = client_data.get('personal_info', {}).get(
                    'first_name', {}).get('value', '')
                client_last_name = client_data.get('personal_info', {}).get(
                    'last_name', {}).get('value', '')

                # Insert or update user record
                c.execute("""
                    INSERT OR REPLACE INTO users 
                    (ig_username, subscriber_id, first_name, last_name, email, source, created_at)
                    VALUES (?, ?, ?, ?, ?, 'wix_form', ?)
                """, (
                    ig_username,
                    subscriber_id,
                    client_first_name,
                    client_last_name,
                    client_data.get('personal_info', {}).get(
                        'email', {}).get('value', ''),
                    datetime.now().isoformat()
                ))

                conn.commit()

                # NEW: Update client_status to 'Trial Client' after successful onboarding
                try:
                    c.execute("""
                        UPDATE users
                        SET client_status = ?
                        WHERE ig_username = ? AND subscriber_id = ?
                    """, ('Trial Client', ig_username, subscriber_id))
                    conn.commit()
                    logger.info(
                        f"[WIX-BG] Updated client_status to 'Trial Client' for {ig_username}")
                except Exception as status_update_error:
                    logger.error(
                        f"[WIX-BG] Failed to update client_status for {ig_username}: {status_update_error}")

                conn.close()
                logger.info(
                    f"[WIX-BG] Stored user record in database for {ig_username}")

            except Exception as db_error:
                logger.error(f"[WIX-BG] Database error: {db_error}")
            # --- NEW: Add dashboard notification ---
            notification_message = f"New Trial Member - {client_full_name} (IG: @{ig_username}): "
            if client_added:
                notification_message += "Client Added to Trainerize. "
            else:
                notification_message += "Client addition to Trainerize FAILED. "

            if meal_plan_uploaded:
                notification_message += "Meal Plan Successfully Added. "
            else:
                notification_message += "Meal Plan FAILED to Add. "

            if workout_program_built:
                notification_message += "Workout Program Successfully Added."
            else:
                notification_message += "Workout Program FAILED to Add."

            try:
                add_todo_item(
                    ig_username=ig_username,  # Use ig_username for the todo item
                    client_name=client_full_name,  # Use full name for better display
                    task_description=notification_message,
                    status="pending"  # Always starts as pending for review
                )
                logger.info(
                    f"[WIX-BG] Added dashboard notification for {ig_username}: {notification_message}")
            except Exception as todo_error:
                logger.error(
                    f"[WIX-BG] Failed to add todo item for onboarding status: {todo_error}")

        else:
            logger.error(
                f"[WIX-BG] Failed to process onboarding for {ig_username}")
            client_full_name = client_data.get('personal_info', {}).get(
                'full_name', {}).get('value', ig_username)
            error_notification_message = f"Onboarding FAILED for {client_full_name} (IG: @{ig_username}). Needs manual check. Client Added: {client_added}, Meal Plan: {meal_plan_uploaded}, Workout Program: {workout_program_built}"
            try:
                add_todo_item(
                    ig_username=ig_username,
                    client_name=client_full_name,
                    task_description=error_notification_message,
                    status="pending"
                )
                logger.info(
                    f"[WIX-BG] Added error dashboard notification for {ig_username}: {error_notification_message}")
            except Exception as todo_error:
                logger.error(
                    f"[WIX-BG] Failed to add error todo item: {todo_error}")

        return onboarding_overall_success

    except Exception as e:
        logger.error(f"[WIX-BG] Error in background processing: {str(e)}")
        logger.error(f"[WIX-BG] Exception details: {traceback.format_exc()}")
        # Add a todo item for unexpected errors
        client_full_name = client_data.get('personal_info', {}).get(
            'full_name', {}).get('value', ig_username)
        unexpected_error_message = f"Unexpected error during onboarding for {client_full_name} (IG: @{ig_username}): {str(e)}. Needs manual check."
        try:
            add_todo_item(
                ig_username=ig_username,
                client_name=client_full_name,
                task_description=unexpected_error_message,
                status="pending"
            )
            logger.info(
                f"[WIX-BG] Added unexpected error notification for {ig_username}")
        except Exception as todo_error:
            logger.error(
                f"[WIX-BG] Failed to add unexpected error todo item: {todo_error}")

        return False


def _convert_wix_data_to_expected_format(wix_client_data: Dict) -> Dict:
    """
    Convert Wix form data structure to the format expected by PostOnboardingHandler._calculate_nutrition
    """
    try:
        # Extract values from Wix structure
        personal_info = wix_client_data.get('personal_info', {})
        physical_info = wix_client_data.get('physical_info', {})
        training_info = wix_client_data.get('training_info', {})
        dietary_info = wix_client_data.get('dietary_info', {})

        # Derive a more meaningful ig_username
        first_name_raw = personal_info.get('firstName', {}).get(
            'value', '').lower().replace(' ', '')
        last_name_raw = personal_info.get('lastName', {}).get(
            'value', '').lower().replace(' ', '')
        email_raw = personal_info.get('email', {}).get('value', '').split(
            '@')[0].lower().replace('.', '').replace('+', '')

        # Prioritize firstName_lastName, then email, then a generic fallback
        if first_name_raw and last_name_raw:
            derived_ig_username = f"{first_name_raw}_{last_name_raw}"
        elif email_raw:
            derived_ig_username = email_raw
        else:
            derived_ig_username = "wix_user_unknown"  # Fallback if no name or email

        # Map activity level from Wix string to integer
        activity_level_str = physical_info.get('activity_level', {}).get(
            'value', 'moderately_active').lower()
        activity_level_map = {
            'sedentary': 1,
            'lightly active': 2,
            'moderately active': 3,
            'very active': 4,
            'extra active': 5
        }
        converted_activity_level = activity_level_map.get(
            activity_level_str, 3)  # Default to 3

        # Convert to expected format for _calculate_nutrition
        converted_data = {
            "personal_info": {
                "email": {"value": personal_info.get('email', {}).get('value', ''), "confidence": 95},
                "full_name": {"value": personal_info.get('full_name', {}).get('value', ''), "confidence": 95},
                "phone": {"value": personal_info.get('phone', {}).get('value', ''), "confidence": 95},
                # Use actual birthday if available
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

        # Override ig_username with the derived one
        converted_data['personal_info']['ig_username'] = {
            'value': derived_ig_username, 'confidence': 100}

        logger.info(
            f"[WIX-CONVERSION] Successfully converted data structure for IG: {derived_ig_username}")
        return converted_data

    except Exception as e:
        logger.error(f"[WIX-CONVERSION] Error converting data: {str(e)}")
        return None


if __name__ == "__main__":
    logger.info("\n=== STARTING WEBHOOK SERVER (webhook0605.py) ===")
    uvicorn.run("webhook0605:app",  # Changed to use webhook0605
                host="0.0.0.0",
                port=8000,
                reload=True,
                reload_dirs=["c:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot"],
                timeout_keep_alive=300,
                timeout_graceful_shutdown=300,
                limit_concurrency=100,
                backlog=2048
                )

# ---------------------------------------------------------------------------
# Challenge offer gating helper functions
# ---------------------------------------------------------------------------


def _user_has_agreed_to_challenge(conv_history: list[dict]) -> bool:
    """Return True if user gave an affirmative answer after Shannon's soft intro."""
    intro_idx = -1
    for idx, entry in enumerate(conv_history):
        if entry.get('type') == 'ai':
            txt = entry.get('text', '').lower()
            if any(p in txt for p in [
                'would you be interested',
                'interested in hearing',
                'keen to hear',
                'keen to find out',
                    'would you be keen']):
                intro_idx = idx
    if intro_idx == -1:
        return False
    affirm_words = ['yes', 'yeah', 'yep', 'sure', 'keen', 'interested',
                    'sounds good', 'sounds great', 'ok', 'okay', 'absolutely']
    for entry in conv_history[intro_idx + 1:]:
        if entry.get('type') == 'user':
            txt = entry.get('text', '').lower()
            if any(w in txt for w in affirm_words):
                return True
            if any(w in txt for w in ['no', 'not', 'later', 'maybe']):
                return False
    return False


def enforce_challenge_offer_rules(ai_response: str, conv_history: list[dict]) -> str:
    """Ensure challenge link only sent after affirmative user response; otherwise replace with soft intro."""
    if 'cocospersonaltraining.com' in ai_response.lower():
        if not _user_has_agreed_to_challenge(conv_history):
            # Remove any URLs
            cleaned = _re_chal.sub(r'https?://\S+', '', ai_response).strip()
            soft_intro = "Hey I'm actually about to run a Vegan Fitness Challenge, it's totally free and a bunch of fun, would you be interested in hearing more?"
            if 'would you be interested' in cleaned.lower():
                return cleaned
            return soft_intro
    return ai_response

# ---------------------------------------------------------------------------
# Duplicate-question guard helpers
# ---------------------------------------------------------------------------


def _get_recent_ai_questions(conv_history: list[dict], limit: int = 5) -> list[str]:
    """Return last N Shannon questions (lower-cased, stripped of punctuation)."""
    qs: list[str] = []
    for entry in reversed(conv_history):
        if entry.get('type') == 'ai':
            txt = entry.get('text', '')
            if '?' in txt:
                # take question portion(s)
                for part in txt.split('?'):
                    part = part.strip()
                    if part:
                        qs.append(part.lower())
                if len(qs) >= limit:
                    break
    return qs[:limit]


async def _dedup_and_rewrite_if_needed(new_resp: str, conv_history: list[dict]) -> str:
    """Drop repeated questions; if any removed, ask Gemini to add a fresh one."""
    recent_qs = _get_recent_ai_questions(conv_history)

    # Split into sentence segments preserving punctuation
    segments: list[str] = []
    buff = ''
    for ch in new_resp:
        buff += ch
        if ch in '.!?':
            segments.append(buff)
            buff = ''
    if buff:
        segments.append(buff)

    cleaned_segments: list[str] = []
    duplicate_found = False
    for seg in segments:
        core = seg.strip().rstrip('?').strip().lower()
        if seg.strip().endswith('?') and core in recent_qs:
            duplicate_found = True
            continue  # skip dup question
        cleaned_segments.append(seg)

    cleaned_text = ' '.join(s.strip() for s in cleaned_segments).strip()
    if not duplicate_found:
        return new_resp  # nothing to change

    # We removed a question; ask Gemini to craft a fresh one
    recent_qs_str = '; '.join(recent_qs)
    rewrite_prompt = (
        "You are Shannon speaking casually (max 15 words). "
        "Rewrite the following line so it ends with ONE new open-ended question "
        "that is different from these recent questions: "
        f"{recent_qs_str}.\n\n"
        f"Line to rewrite: \"{cleaned_text}\""
    )

    try:
        alt = await call_gemini_with_retry(GEMINI_MODEL_FLASH, rewrite_prompt)
        if alt and isinstance(alt, str):
            return alt.strip()
    except Exception as e:
        logger.error(f"rewrite duplicate question error: {e}")

    # Fallback: return cleaned_text without duplicate question
    return cleaned_text or new_resp

app.include_router(trainerize_router)


async def handle_ad_response(ig_username: str, message_text: str, subscriber_id: str, first_name: str, last_name: str, user_message_timestamp_iso: str) -> bool:
    try:
        # Get user data including ad states
        _, metrics, _ = get_user_data(ig_username, subscriber_id)
        is_in_ad_flow = metrics.get('is_in_ad_flow', False)
        current_state = metrics.get('ad_script_state', 'step1')
        scenario = metrics.get('ad_scenario', 1)  # Default to 1

        logger.info(
            f"[handle_ad_response] Current state for {ig_username}: is_in_ad_flow={is_in_ad_flow}, ad_script_state={current_state}, scenario={scenario}")

        if not is_in_ad_flow:
            logger.info(
                f"[handle_ad_response] User {ig_username} is not in ad flow (is_in_ad_flow={is_in_ad_flow}), returning False")
            return False

        # Build prompt params
        bio_context = metrics.get('client_analysis', {}).get('profile_bio', '')
        weekly_workout_summary = json.dumps(metrics.get('workout_program', {}))
        meal_plan_summary = json.dumps(metrics.get('meal_plan', {}))
        current_stage = f"Ad Response {current_state}"
        trial_status = "Ad Lead"
        current_time = get_melbourne_time_str()
        full_conversation = format_conversation_history(metrics.get(
            'conversation_history', [])) + f"\nUser: {message_text}"

        # Determine challenge type from scenario
        challenge_types = {1: 'vegan', 2: 'vegetarian', 3: 'plant_based'}
        challenge_type = challenge_types.get(scenario, 'plant_based')

        # Use PAID Plant-Based Challenge prompt for plant_based_challenge leads
        if metrics.get('lead_source') == 'plant_based_challenge':
            prompt = prompts.PAID_VEGAN_CHALLENGE_PROMPT_TEMPLATE.format(
                current_melbourne_time_str=current_time,
                ig_username=ig_username,
                script_state=current_state,
                # Will be updated based on ManyChat button selection
                initial_trigger='direct_comment',
                bio=bio_context,
                full_conversation=full_conversation
            )
        else:
            # Fallback to existing FB ad prompt for facebook_ad leads
            prompt = prompts.COMBINED_AD_RESPONSE_PROMPT_TEMPLATE.format(
                current_melbourne_time_str=current_time,
                ig_username=ig_username,
                ad_script_state=current_state,
                ad_scenario=scenario,
                bio=bio_context,
                full_conversation=full_conversation
            )

        response = await get_ai_response(prompt)
        if not response:
            logger.error(f"Failed to get ad response for {ig_username}")
            return False

        # Check for email collection in Plant-Based Challenge responses
        if metrics.get('lead_source') == 'plant_based_challenge':
            await detect_and_store_challenge_email(ig_username, message_text, subscriber_id, scenario)

        # Check auto mode status to determine how to handle the response
        should_auto_process = False
        try:
            # Import the vegan ad auto mode checker only (explicit control)
            import sys
            import os
            app_dashboard_modules_path = os.path.join(
                os.path.dirname(__file__), 'app', 'dashboard_modules')
            if app_dashboard_modules_path not in sys.path:
                sys.path.insert(0, app_dashboard_modules_path)

            from auto_mode_state import is_vegan_ad_auto_mode_active

            vegan_ad_auto_active = is_vegan_ad_auto_mode_active()

            if vegan_ad_auto_active:
                logger.info(
                    f"🌱 VEGAN AD AUTO MODE ACTIVE - Auto-processing ad response for {ig_username}")
                should_auto_process = True
            else:
                logger.info(
                    f"Vegan Ad auto mode OFF - {ig_username} ad response requires manual review")
                should_auto_process = False

        except ImportError:
            logger.warning(
                "Could not import auto_mode_state, assuming Vegan Ad Auto Mode is OFF for ad response.")
            should_auto_process = False

        # Add to review queue with appropriate status
        review_status = 'auto_scheduled' if should_auto_process else 'pending_review'
        review_id = add_response_to_review_queue(
            user_ig_username=ig_username,
            user_subscriber_id=subscriber_id,
            incoming_message_text=message_text,
            incoming_message_timestamp=user_message_timestamp_iso,
            generated_prompt_text=prompt,
            proposed_response_text=response,
            prompt_type="facebook_ad_response",
            status=review_status
        )

        # If auto mode is active, schedule the response
        if should_auto_process and review_id:
            try:
                # Ensure the scheduled responses table exists
                conn = db_utils.get_db_connection()
                create_scheduled_responses_table_if_not_exists(conn)
                conn.close()

                # Schedule the response with timing delay
                from app.dashboard_modules.response_review import schedule_auto_response
                success_schedule, schedule_message, delay_minutes = schedule_auto_response(
                    # Create a mock review_item for the function
                    {
                        'review_id': review_id,
                        'user_ig_username': ig_username,
                        'user_subscriber_id': subscriber_id,
                        'incoming_message_text': message_text,
                        'incoming_message_timestamp': user_message_timestamp_iso,
                        'proposed_response': response,
                        'status': 'auto_scheduled'
                    },
                    response,
                    user_notes="[AUTO MODE - AD RESPONSE]",
                    manual_context=""
                )

                if success_schedule:
                    logger.info(
                        f"✅ AUTO-SCHEDULED: {ig_username} - Ad response queued for {delay_minutes} minutes")
                else:
                    logger.error(
                        f"❌ Auto-schedule FAILED for ad response {ig_username}: {schedule_message}")
            except Exception as e_auto:
                logger.error(
                    f"❌ Failed to auto-schedule ad response for {ig_username}: {e_auto}", exc_info=True)

        if review_id:
            logger.info(
                f"Successfully added ad response for {ig_username} to review queue (Review ID: {review_id})")

            # Update analytics with the generated response
            update_analytics_data(
                ig_username, message_text, response, subscriber_id, first_name, last_name
            )

            # Advance state
            next_state = 'completed' if current_state == 'step3' else f"step{int(current_state[-1]) + 1}"
            logger.info(
                f"[handle_ad_response] Advancing {ig_username} from {current_state} to {next_state}")

            update_analytics_data(
                ig_username, "", "", subscriber_id, first_name, last_name,
                ad_script_state=next_state
            )
            if next_state == 'completed':
                logger.info(
                    f"[handle_ad_response] Ad flow completed for {ig_username}, setting is_in_ad_flow=False")
                update_analytics_data(
                    ig_username, "", "", subscriber_id, first_name, last_name,
                    is_in_ad_flow=False
                )
                # ONLY FOR PAID CHALLENGE: If lead source is plant_based_challenge and flow is completed,
                # it means they confirmed booking a call. Add them to paid_challenge_bookings.
                if metrics.get('lead_source') == 'plant_based_challenge':
                    try:
                        from app.dashboard_modules.dashboard_sqlite_utils import add_paid_challenge_booking
                        add_paid_challenge_booking(ig_username)
                        logger.info(
                            f"✅ Recorded paid challenge booking confirmation for {ig_username}")
                    except Exception as e_booking:
                        logger.error(
                            f"❌ Failed to record paid challenge booking for {ig_username}: {e_booking}", exc_info=True)
            else:
                logger.info(
                    f"[handle_ad_response] Ad flow continues for {ig_username}, keeping is_in_ad_flow=True")

            return True
        else:
            logger.error(
                f"Failed to add ad response for {ig_username} to review queue")
            return False

    except Exception as e:
        logger.error(f"Error in handle_ad_response: {e}", exc_info=True)
        return False


async def handle_ad_response_with_params(ig_username: str, message_text: str, subscriber_id: str, first_name: str, last_name: str, user_message_timestamp_iso: str, force_ad_flow: bool = False, force_lead_source: str = None, force_scenario: int = None, force_script_state: str = None) -> bool:
    """
    Enhanced version of handle_ad_response that accepts forced parameters to bypass database lookups.
    Used when we know the user should be in ad flow but database might not be updated yet.
    """
    try:
        # Get user data including ad states, but override with forced params if provided
        _, metrics, _ = get_user_data(ig_username, subscriber_id)

        # Use forced parameters if provided, otherwise fall back to database values
        is_in_ad_flow = force_ad_flow if force_ad_flow is not None else metrics.get(
            'is_in_ad_flow', False)
        current_state = force_script_state if force_script_state else metrics.get(
            'ad_script_state', 'step1')
        scenario = force_scenario if force_scenario else metrics.get(
            'ad_scenario', 1)
        lead_source = force_lead_source if force_lead_source else metrics.get(
            'lead_source', 'general')

        logger.info(
            f"[handle_ad_response_with_params] Using parameters for {ig_username}: is_in_ad_flow={is_in_ad_flow}, ad_script_state={current_state}, scenario={scenario}, lead_source={lead_source} (forced: {force_ad_flow})")

        if not is_in_ad_flow:
            logger.info(
                f"[handle_ad_response_with_params] User {ig_username} is not in ad flow (is_in_ad_flow={is_in_ad_flow}), returning False")
            return False

        # Build prompt params
        bio_context = metrics.get('client_analysis', {}).get('profile_bio', '')
        weekly_workout_summary = json.dumps(metrics.get('workout_program', {}))
        meal_plan_summary = json.dumps(metrics.get('meal_plan', {}))
        current_stage = f"Ad Response {current_state}"
        trial_status = "Ad Lead"
        current_time = get_melbourne_time_str()
        full_conversation = format_conversation_history(metrics.get(
            'conversation_history', [])) + f"\nUser: {message_text}"

        # Determine challenge type from scenario
        challenge_types = {1: 'vegan', 2: 'vegetarian', 3: 'plant_based'}
        challenge_type = challenge_types.get(scenario, 'plant_based')

        # Use Plant-Based Challenge prompt for plant_based_challenge leads
        if lead_source == 'paid_plant_based_challenge':
            prompt = prompts.PAID_VEGAN_CHALLENGE_PROMPT_TEMPLATE.format(
                current_melbourne_time_str=current_time,
                ig_username=ig_username,
                challenge_type=challenge_type,
                script_state=current_state,
                bio=bio_context,
                full_conversation=full_conversation
            )
            logger.info(
                f"[handle_ad_response_with_params] Using PAID_VEGAN_CHALLENGE_PROMPT_TEMPLATE for {ig_username} (challenge_type: {challenge_type})")
        else:
            # Fallback to existing FB ad prompt for facebook_ad leads
            prompt = prompts.COMBINED_AD_RESPONSE_PROMPT_TEMPLATE.format(
                current_melbourne_time_str=current_time,
                ig_username=ig_username,
                ad_script_state=current_state,
                ad_scenario=scenario,
                bio=bio_context,
                full_conversation=full_conversation
            )
            logger.info(
                f"[handle_ad_response_with_params] Using COMBINED_AD_RESPONSE_PROMPT_TEMPLATE for {ig_username}")

        response = await get_ai_response(prompt)
        if not response:
            logger.error(f"Failed to get ad response for {ig_username}")
            return False

        # Check for email collection in Plant-Based Challenge responses
        if lead_source == 'plant_based_challenge':
            await detect_and_store_challenge_email(ig_username, message_text, subscriber_id, scenario)

        # Check for booking confirmation in PAID Plant-Based Challenge responses
        if lead_source == 'paid_plant_based_challenge' and metrics.get('paid_challenge_booking_status') != 'booked':
            await detect_and_confirm_paid_booking(ig_username, message_text, subscriber_id)

        # Check auto mode status to determine how to handle the response
        should_auto_process = False
        try:
            # Import the auto mode checkers
            import sys
            import os
            app_dashboard_modules_path = os.path.join(
                os.path.dirname(__file__), 'app', 'dashboard_modules')
            if app_dashboard_modules_path not in sys.path:
                sys.path.insert(0, app_dashboard_modules_path)

            from auto_mode_state import is_auto_mode_active, is_vegan_auto_mode_active

            # Check general auto mode
            general_auto_active = is_auto_mode_active()

            # Check vegan auto mode
            vegan_auto_active = is_vegan_auto_mode_active()

            if general_auto_active:
                logger.info(
                    f"🤖 GENERAL AUTO MODE ACTIVE - Auto-processing plant-based challenge response for {ig_username}")
                should_auto_process = True
            elif vegan_auto_active:
                logger.info(
                    f"🌱 VEGAN AUTO MODE ACTIVE - Auto-processing plant-based challenge response for {ig_username}")
                should_auto_process = True
            else:
                logger.info(
                    f"No auto mode active - {ig_username} plant-based challenge response requires manual review")
                should_auto_process = False

        except ImportError:
            logger.warning(
                "Could not import auto_mode_state, assuming Auto Mode is OFF for plant-based challenge response.")
            should_auto_process = False

        # If auto mode is active, schedule the response
        if should_auto_process and review_id:
            try:
                # Ensure the scheduled responses table exists
                import app.dashboard_modules.dashboard_sqlite_utils as db_utils
                from app.dashboard_modules.dashboard_sqlite_utils import create_scheduled_responses_table_if_not_exists
                conn = db_utils.get_db_connection()
                create_scheduled_responses_table_if_not_exists(conn)
                conn.close()

                # Schedule the response with timing delay
                from app.dashboard_modules.response_review import schedule_auto_response
                success_schedule, schedule_message, delay_minutes = schedule_auto_response(
                    # Create a mock review_item for the function
                    {
                        'review_id': review_id,
                        'user_ig_username': ig_username,
                        'user_subscriber_id': subscriber_id,
                        'incoming_message_text': message_text,
                        'incoming_message_timestamp': user_message_timestamp_iso,
                        'proposed_response': response,
                        'status': 'auto_scheduled'
                    },
                    response,
                    user_notes="[AUTO MODE - PLANT-BASED CHALLENGE RESPONSE]",
                    manual_context=""
                )

                if success_schedule:
                    logger.info(
                        f"✅ AUTO-SCHEDULED: {ig_username} - Plant-based challenge response queued for {delay_minutes} minutes")
                else:
                    logger.error(
                        f"❌ Auto-schedule FAILED for plant-based challenge response {ig_username}: {schedule_message}")
            except Exception as e_auto:
                logger.error(
                    f"❌ Failed to auto-schedule plant-based challenge response for {ig_username}: {e_auto}", exc_info=True)

        # Add to review queue with appropriate status
        review_status = 'auto_scheduled' if should_auto_process else 'pending_review'
        review_id = add_response_to_review_queue(
            user_ig_username=ig_username,
            user_subscriber_id=subscriber_id,
            incoming_message_text=message_text,
            incoming_message_timestamp=user_message_timestamp_iso,
            generated_prompt_text=prompt,
            proposed_response_text=response,
            prompt_type="plant_based_challenge" if lead_source == 'plant_based_challenge' else "facebook_ad",
            status=review_status
        )

        if review_id:
            logger.info(
                f"Successfully added ad response for {ig_username} to review queue (Review ID: {review_id})")

            # Update analytics with the generated response
            update_analytics_data(
                ig_username, message_text, response, subscriber_id, first_name, last_name
            )

            # Advance state
            next_state = 'completed' if current_state == 'step3' else f"step{int(current_state[-1]) + 1}"
            logger.info(
                f"[handle_ad_response_with_params] Advancing {ig_username} from {current_state} to {next_state}")

            update_analytics_data(
                ig_username, "", "", subscriber_id, first_name, last_name,
                ad_script_state=next_state
            )
            if next_state == 'completed':
                logger.info(
                    f"[handle_ad_response_with_params] Ad flow completed for {ig_username}, setting is_in_ad_flow=False")
                update_analytics_data(
                    ig_username, "", "", subscriber_id, first_name, last_name,
                    is_in_ad_flow=False
                )

            return True
        else:
            logger.error(
                f"Failed to add ad response for {ig_username} to review queue")
            return False

    except Exception as e:
        logger.error(
            f"Error in handle_ad_response_with_params: {e}", exc_info=True)
        return False


async def detect_and_store_challenge_email(ig_username: str, message_text: str, subscriber_id: str, current_scenario: int):
    """Detect email in Plant-Based Challenge conversation and store challenge data"""
    import re
    from app.dashboard_modules.notifications import add_email_collected_notification

    # Email pattern detection
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, message_text)

    if emails:
        email = emails[0]  # Take the first email found

        # Determine challenge type from scenario
        challenge_types = {1: 'vegan', 2: 'vegetarian', 3: 'plant_based'}
        challenge_type = challenge_types.get(current_scenario, 'plant_based')

        try:
            import sqlite3
            from datetime import datetime

            conn = sqlite3.connect("app/analytics_data_good.sqlite")
            cursor = conn.cursor()

            # Update user with challenge email and data
            cursor.execute("""
                UPDATE users 
                SET challenge_email = ?, 
                    challenge_type = ?, 
                    challenge_signup_date = ?,
                    ad_script_state = 'step5'
                WHERE ig_username = ?
            """, (email, challenge_type, datetime.now().isoformat(), ig_username))

            conn.commit()
            conn.close()

            # Trigger blue email notification
            add_email_collected_notification(ig_username, email)

            logger.info(
                f"🌱 Challenge email collected for {ig_username}: {email} (Type: {challenge_type})")
            return True

        except Exception as e:
            logger.error(
                f"Error storing challenge email for {ig_username}: {e}")
            return False

        return False


async def detect_and_confirm_paid_booking(ig_username: str, message_text: str, subscriber_id: str):
    """
    Detects if a user's message confirms they have booked a Calendly call
    and updates their status in the database.
    """
    confirmation_prompt = f"""
    Analyze the user's message. Does it confirm they have booked a call, appointment, or session?
    Look for phrases like "booked", "done", "all set", "scheduled it", "just booked".

    User message: "{message_text}"

    If it is a confirmation, respond with "YES". Otherwise, respond with "NO".
    """
    try:
        confirmation = await call_gemini_with_retry(
            model_name="gemini-2.0-flash-thinking-exp-01-21",
            prompt=confirmation_prompt
        )

        if "YES" in confirmation.upper():
            from app.dashboard_modules.dashboard_sqlite_utils import add_paid_challenge_booking
            from app.dashboard_modules.notifications import add_notification

            add_paid_challenge_booking(ig_username)
            add_notification(
                title="✅ Insight Call Booked!",
                message=f"@{ig_username} has booked their paid challenge insight call.",
                notification_type="success",
                username=ig_username
            )
            logger.info(
                f"✅ Confirmed and recorded paid challenge booking for {ig_username}")
            return True

    except Exception as e:
        logger.error(
            f"Error detecting paid booking confirmation for {ig_username}: {e}", exc_info=True)

        return False
