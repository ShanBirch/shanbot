from __future__ import annotations

"""Wix onboarding webhook handler extracted from `webhook0605.py` to slim down the main file.
This module provides an `APIRouter` which can be included by the main FastAPI app:

    from wix_onboarding import router as wix_router
    app.include_router(wix_router)

The implementation is a straight lift-and-shift of the previous code so behaviour
remains identical.
"""

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
from typing import Dict, Optional
import json
import logging
import os
import time
import traceback
from datetime import datetime

# External dependency – remains unchanged
from post_onboarding_handler import PostOnboardingHandler

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Helper functions (verbatim from original file, minus docstrings & comments)
# ---------------------------------------------------------------------------


def _map_wix_form_to_client_data(form_data: Dict) -> Optional[Dict]:
    try:
        submissions = form_data.get('submissions', [])
        field_map: Dict[str, str] = {
            (s.get('label', '').lower()): s.get('value', '') for s in submissions
        }
        email = field_map.get('email') or form_data.get('email')
        first_name = field_map.get('first name') or field_map.get('firstname')
        last_name = field_map.get('last name') or field_map.get('lastname')
        phone = field_map.get('phone') or form_data.get('phonenumber')
        full_name = f"{first_name or ''} {last_name or ''}".strip() or 'Unknown'
        weight = float(field_map.get('weight', '').replace(
            'kgs', '').replace('kg', '').strip() or 70)
        height = float(field_map.get(
            'height', '').replace('cm', '').strip() or 170)
        birthday = field_map.get('birthday')
        age = 30
        if birthday:
            try:
                birth_date = datetime.strptime(birthday, '%Y-%m-%d')
                today = datetime.now()
                age = today.year - birth_date.year - \
                    ((today.month, today.day) < (birth_date.month, birth_date.day))
            except Exception:
                pass
        primary_goal = field_map.get('fitness goal') or 'muscle_gain'
        activity_level = field_map.get('activity level') or 'moderately_active'
        gym_access = field_map.get('gym access') or field_map.get(
            'training location') or 'full_gym'
        training_days = field_map.get('training days') or form_data.get(
            'field:which_days_time_have_you_set_aside_to_train', 'monday-friday')
        training_experience = field_map.get(
            'training experience') or 'beginner'
        dietary_type = form_data.get('dietaryType') or form_data.get(
            'diet_type') or 'plant-based'
        dietary_restrictions = form_data.get('dietaryRestrictions') or form_data.get(
            'restrictions') or form_data.get('allergies')
        disliked_foods = form_data.get('dislikedFoods') or form_data.get(
            'food_dislikes') or form_data.get('dislikes')
        regular_breakfast = form_data.get(
            'regularBreakfast') or form_data.get('breakfast_preferences')
        regular_lunch = form_data.get(
            'regularLunch') or form_data.get('lunch_preferences')
        regular_dinner = form_data.get(
            'regularDinner') or form_data.get('dinner_preferences')
        exercise_dislikes = form_data.get('exerciseDislikes') or form_data.get(
            'exercise_limitations') or form_data.get('exercises_to_avoid')

        client_data = {
            "personal_info": {
                "email": {"value": email or "", "confidence": 95},
                "full_name": {"value": full_name, "confidence": 95},
                "phone": {"value": phone or "", "confidence": 95},
                "age": {"value": age, "confidence": 90},
            },
            "physical_info": {
                "weight": {"value": weight, "unit": "kg", "confidence": 95},
                "height": {"value": height, "unit": "cm", "confidence": 95},
                "target_weight": {"value": weight + 5 if primary_goal == 'muscle_gain' else weight - 5, "unit": "kg", "confidence": 90},
                "primary_fitness_goal": {"value": primary_goal, "confidence": 95},
            },
            "training_info": {
                "activity_level": {"value": activity_level, "confidence": 90},
                "gym_access": {"value": gym_access, "confidence": 95},
                "training_days": {"value": training_days, "confidence": 90},
                "training_experience": {"value": training_experience, "confidence": 85},
            },
            "dietary_info": {
                "diet_type": {"value": dietary_type, "confidence": 95},
                "dietary_restrictions": {"value": dietary_restrictions or "", "confidence": 90},
                "disliked_foods": {"value": disliked_foods or "", "confidence": 90},
                "regular_meals": {
                    "breakfast": {"value": regular_breakfast or "oats with protein", "confidence": 85},
                    "lunch": {"value": regular_lunch or "salad with protein", "confidence": 85},
                    "dinner": {"value": regular_dinner or "plant-based protein with vegetables", "confidence": 85},
                },
            },
            "exercise_preferences": {
                "dislikes": {"value": exercise_dislikes or "", "confidence": 90},
                "current_routine": {"value": "none", "confidence": 95},
            },
        }
        return client_data
    except Exception as e:
        logger.error(f"[WIX-MAPPING] Error mapping Wix form data: {e}")
        return None


def _convert_wix_data_to_expected_format(wix_client_data: Dict) -> Dict:
    # Currently just pass-through; kept separate for future transformations
    return wix_client_data


async def _process_wix_onboarding_background(ig_username: str, subscriber_id: str, client_data: Dict):
    try:
        gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv(
            "GOOGLE_AI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            logger.error("[WIX-BG] Gemini API key missing")
            return False
        handler = PostOnboardingHandler(gemini_api_key)
        converted = _convert_wix_data_to_expected_format(client_data)
        nutrition_data = handler._calculate_nutrition(converted)
        await handler.process_onboarding_with_fixed_data(
            ig_username=ig_username,
            subscriber_id=subscriber_id,
            direct_client_data=converted,
            nutrition_targets_override=nutrition_data,
        )
        logger.info(f"[WIX-BG] Finished onboarding for {ig_username}")
        return True
    except Exception as e:
        logger.error(f"[WIX-BG] Error processing onboarding: {e}")
        return False


# ---------------------------------------------------------------------------
# FastAPI endpoint
# ---------------------------------------------------------------------------

@router.post("/webhook/wix-onboarding")
async def process_wix_form_submission(request: Request, background_tasks: BackgroundTasks):
    try:
        payload_str = (await request.body()).decode("utf-8")
        wix_data = json.loads(payload_str)
        form_data = wix_data.get("data", {}) or wix_data
        client_data = _map_wix_form_to_client_data(form_data)
        if not client_data:
            raise HTTPException(status_code=400, detail="Invalid form data")
        email = client_data["personal_info"]["email"]["value"]
        ig_username = f"wix_user_{email.split('@')[0]}"
        subscriber_id = f"wix_{int(time.time())}"
        background_tasks.add_task(
            _process_wix_onboarding_background, ig_username, subscriber_id, client_data)
        return PlainTextResponse("Form submitted successfully! Your meal plan and workout program are being created.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WIX-WEBHOOK] {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="Error processing form submission")
