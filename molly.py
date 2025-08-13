from post_onboarding_handler import PostOnboardingHandler
import getpass
import asyncio
import os
import sys
print("[DEBUG] onboard_molly.py starting...")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
print("[DEBUG] sys.path set, about to import PostOnboardingHandler...")
print("[DEBUG] Successfully imported PostOnboardingHandler!")

# --- Molly's details ---
IG_USERNAME = "mollyforster"  # or any IG username you want to use
SUBSCRIBER_ID = "1438912163"
EMAIL = "molllymay2005@gmail.com"
FULL_NAME = "Molly Forster"
PHONE = "0412345678"
BIRTH_DATE = "2005-01-01"
GENDER = "female"
WEIGHT = 58
HEIGHT = 165
GOAL = "muscle gain"
SPECIFIC_WEIGHT_GOAL = 60
ACTIVITY_LEVEL = 3  # moderately active
LOCATION = "Melbourne"

# --- Dietary info ---
DIET_TYPE = "none"
REGULAR_MEALS = {
    "breakfast": {"value": "eggs, oats, yogurt, avocado", "confidence": 95},
    "lunch": {"value": "chicken, sweet potato, iceberg lettuce", "confidence": 95},
    "dinner": {"value": "fish, pumpkin, avocado", "confidence": 95},
}
MEAL_NOTES = "prefers high protein, likes variety"
OTHER_DIETARY_RESTRICTIONS = "none"
DISLIKED_FOODS = "rice, quinoa"

# --- Training info ---
CURRENT_ROUTINE = "legs 3x, back 2x, push 1x, core on upper days"
TRAINING_LOCATION = "gym"
DISLIKED_EXERCISES = "none"
LIKED_EXERCISES = "hip thrusts, hyper extension, rdls, core"
TRAINING_DAYS = "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday"

# --- Build client_data in expected format ---
client_data = {
    "personal_info": {
        "email": {"value": EMAIL, "confidence": 100},
        "full_name": {"value": FULL_NAME, "confidence": 100},
        "phone": {"value": PHONE, "confidence": 90},
        "birth_date": {"value": BIRTH_DATE, "confidence": 90},
        "gender": {"value": GENDER, "confidence": 100},
        "subscriber_id": {"value": SUBSCRIBER_ID, "confidence": 100},
    },
    "physical_info": {
        "current_weight_kg": {"value": WEIGHT, "confidence": 100},
        "height_cm": {"value": HEIGHT, "confidence": 100},
        "primary_fitness_goal": {"value": GOAL, "confidence": 100},
        "specific_weight_goal_kg": {"value": SPECIFIC_WEIGHT_GOAL, "confidence": 90},
        "activity_level": {"value": ACTIVITY_LEVEL, "confidence": 100},
    },
    "dietary_info": {
        "diet_type": {"value": DIET_TYPE, "confidence": 100},
        "regular_meals": REGULAR_MEALS,
        "meal_notes": {"value": MEAL_NOTES, "confidence": 95},
        "other_dietary_restrictions": {"value": OTHER_DIETARY_RESTRICTIONS, "confidence": 95},
        "disliked_foods": {"value": DISLIKED_FOODS, "confidence": 95},
    },
    "training_info": {
        "current_routine": {"value": CURRENT_ROUTINE, "confidence": 95},
        "training_location": {"value": TRAINING_LOCATION, "confidence": 100},
        "disliked_exercises": {"value": DISLIKED_EXERCISES, "confidence": 95},
        "liked_exercises": {"value": LIKED_EXERCISES, "confidence": 100},
        "training_days": {"value": TRAINING_DAYS, "confidence": 100},
    },
    "general_info": {
        "location": {"value": LOCATION, "confidence": 90},
    },
}

# --- Nutrition override (if you want to force calories/protein) ---
FORCE_CALORIES = 1900
FORCE_PROTEIN = 120


async def main():
    print("=== Onboarding Molly Forster ===")
    gemini_api_key = getpass.getpass("Enter your Gemini API key: ")
    handler = PostOnboardingHandler(gemini_api_key)

    # Optionally override calculated nutrition
    nutrition_data = handler._calculate_nutrition(client_data)
    if nutrition_data:
        nutrition_data["daily_calories"] = FORCE_CALORIES
        nutrition_data["macros"]["protein"] = FORCE_PROTEIN
        print(f"Nutrition targets set: {nutrition_data}")
    else:
        print("Failed to calculate nutrition data. Aborting.")
        return

    # Generate meal plan
    meal_plan = await handler._generate_meal_plan(nutrition_data, client_data)
    if not meal_plan:
        print("Failed to generate meal plan. Aborting.")
        return

    # Generate workout program
    program_request = handler._design_workout_program(client_data)
    if not program_request:
        print("Failed to design workout program. Aborting.")
        return

    # Create PDF
    pdf_path = handler._create_meal_plan_pdf(
        meal_plan['meal_plan_text'], client_data, nutrition_data)
    if not pdf_path:
        print("Failed to create meal plan PDF. Aborting.")
        return

    # Save to analytics (optional, for record-keeping)
    handler.save_workout_program_to_analytics(
        IG_USERNAME, program_request, SUBSCRIBER_ID)
    handler.save_meal_plan_to_analytics(IG_USERNAME, meal_plan, SUBSCRIBER_ID)

    # Launch Playwright onboarding subprocess
    meal_plan_pdf_full_path = handler.PDF_OUTPUT_DIR + "/" + pdf_path
    exit_code = handler._launch_onboarding_subprocess_and_wait(
        client_data, meal_plan_pdf_full_path)
    if exit_code == 0:
        print("Successfully completed onboarding for Molly!")
    else:
        print(f"Onboarding subprocess failed with exit code {exit_code}.")

if __name__ == "__main__":
    asyncio.run(main())
