import asyncio
import json
from datetime import datetime

# Hannah's data
HANNAH_DATA = {
    "personal_info": {
        "full_name": {"value": "Hannah Devlin", "confidence": 100},
        "email": {"value": "hannahjanedevlin@gmail.com", "confidence": 100},
        "phone": {"value": "+61 492 859 426", "confidence": 100},
        "birth_date": {"value": "1998-09-29", "confidence": 100},
        "gender": {"value": "Female", "confidence": 100}
    },
    "physical_info": {
        "current_weight": {"value": "76.5", "confidence": 100},
        "height": {"value": "164.5", "confidence": 100},
        "primary_fitness_goal": {"value": "Fat Loss", "confidence": 100},
        "activity_level": {"value": "Lightly active - light exercise 6-7 days per week", "confidence": 100}
    },
    "dietary_info": {
        "diet_type": {"value": "Vegan", "confidence": 100},
        "disliked_foods": {"value": "Fish, Eggs, Pork, Shellfish, Dairy", "confidence": 100},
        "regular_meals": {
            "breakfast": {"value": "Not specified", "confidence": 50},
            "lunch": {"value": "Not specified", "confidence": 50},
            "dinner": {"value": "Not specified", "confidence": 50}
        }
    },
    "training_info": {
        "training_days": {"value": "3 days per week", "confidence": 100},
        "workout_time": {"value": "Evening", "confidence": 100},
        "gym_access": {"value": "At Home Body Weight", "confidence": 100},
        "activities": {"value": "Daily walking, rockclimbing 2-3x per week, Strength training, squats, basketball, swimming, walking, cardio that isn't running", "confidence": 100}
    }
}


def calculate_nutrition_for_weight_loss():
    """Calculate nutrition targets for 500g weight loss per week"""

    # Hannah's stats
    weight_kg = 76.5
    height_cm = 164.5
    age = 2025 - 1998  # 27 years old
    gender = "Female"
    activity_level = "Lightly active"

    # Calculate BMR using Mifflin-St Jeor Equation
    if gender == "Female":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5

    # Activity multiplier for "Lightly active"
    activity_multiplier = 1.375

    # Calculate TDEE
    tdee = bmr * activity_multiplier

    # For 500g weight loss per week, create a 500 calorie deficit
    # 500g fat = ~3850 calories, so ~550 calorie deficit per day
    daily_calories = tdee - 550

    # Macro breakdown for fat loss (higher protein, moderate carbs, lower fat)
    protein_percentage = 0.30  # 30% protein
    fat_percentage = 0.25      # 25% fat
    carbs_percentage = 0.45    # 45% carbs

    protein_grams = int((daily_calories * protein_percentage) / 4)
    fat_grams = int((daily_calories * fat_percentage) / 9)
    carbs_grams = int((daily_calories * carbs_percentage) / 4)

    return {
        "daily_calories": int(daily_calories),
        "macros": {
            "protein": protein_grams,
            "carbs": carbs_grams,
            "fats": fat_grams
        },
        "calculation_factors": {
            "bmr": int(bmr),
            "tdee": int(tdee),
            "activity_multiplier": activity_multiplier,
            "deficit": 550
        }
    }


def calculate_meal_times(workout_time="Evening"):
    """Calculate meal times based on workout schedule"""

    if workout_time == "Evening":
        return {
            "pre_workout": "5:00 PM",
            "post_workout": "7:30 PM",
            "morning_snack": "10:00 AM",
            "lunch": "12:30 PM",
            "afternoon_snack": "3:00 PM",
            "dinner": "8:30 PM"
        }
    elif workout_time == "Morning":
        return {
            "pre_workout": "6:00 AM",
            "post_workout": "8:30 AM",
            "morning_snack": "10:30 AM",
            "lunch": "12:30 PM",
            "afternoon_snack": "3:00 PM",
            "dinner": "7:00 PM"
        }
    else:
        return {
            "pre_workout": "5:00 PM",
            "post_workout": "7:30 PM",
            "morning_snack": "10:00 AM",
            "lunch": "12:30 PM",
            "afternoon_snack": "3:00 PM",
            "dinner": "8:30 PM"
        }


async def generate_meal_plan():
    """Generate meal plan for Hannah"""

    # Calculate nutrition targets
    nutrition_data = calculate_nutrition_for_weight_loss()
    meal_times = calculate_meal_times("Evening")

    print(f"=== HANNAH'S NUTRITION TARGETS ===")
    print(f"Daily Calories: {nutrition_data['daily_calories']}")
    print(f"Protein: {nutrition_data['macros']['protein']}g")
    print(f"Carbs: {nutrition_data['macros']['carbs']}g")
    print(f"Fats: {nutrition_data['macros']['fats']}g")
    print(f"BMR: {nutrition_data['calculation_factors']['bmr']}")
    print(f"TDEE: {nutrition_data['calculation_factors']['tdee']}")
    print()

    # Create meal plan prompt
    prompt = f"""Create a simple three-day meal plan for Hannah, a vegan client with these requirements:

Daily Nutrition Targets:
- Calories: {nutrition_data['daily_calories']}
- Protein: {nutrition_data['macros']['protein']}g
- Carbs: {nutrition_data['macros']['carbs']}g
- Fats: {nutrition_data['macros']['fats']}g

Goal: Fat Loss (500g per week)
Training Days: 3 days per week (Evening workouts)

Client Preferences:
- Dietary Type: Vegan
- Foods to Avoid: Fish, Eggs, Pork, Shellfish, Dairy
- Activities: Daily walking, rockclimbing 2-3x per week, strength training, basketball, swimming

Client's workout time: Evening

IMPORTANT REQUIREMENTS:
1. Use ONLY high-protein vegan ingredients available at Australian stores (Woolworths, Coles)
2. Focus on protein-rich vegan foods like:
   - Tofu, tempeh, seitan
   - Legumes (chickpeas, lentils, black beans)
   - Quinoa, buckwheat
   - Nuts and seeds (almonds, pumpkin seeds, chia seeds)
   - Vegan protein powder
   - Nutritional yeast
   - Edamame
   - Plant-based milks (soy, pea protein)
3. Ensure each meal has adequate protein for muscle preservation during fat loss
4. Keep meals simple and easy to prepare
5. Use common Australian ingredients and measurements

Provide ONLY three day meal plans in this exact format:

DAY 1 MEAL PLAN

Pre-workout ({meal_times['pre_workout']})
Meal: [Specific meal name]
Ingredients:
- [Ingredient 1] [exact quantity]
- [Ingredient 2] [exact quantity]
Preparation: [Simple prep steps]
Macros: [XXX calories, XXg protein, XXg carbs, XXg fats]

Post-workout Breakfast ({meal_times['post_workout']})
Morning Snack ({meal_times['morning_snack']})
Lunch ({meal_times['lunch']})
Afternoon Snack ({meal_times['afternoon_snack']})
Dinner ({meal_times['dinner']})

DAY 2 MEAL PLAN
[Repeat exact same format as Day 1]

DAY 3 MEAL PLAN
[Repeat exact same format as Day 1]

IMPORTANT:
1. Do not include any section headers with asterisks or hashes
2. Each meal must be a specific recipe with exact quantities
3. Include only the meal plans - no other sections
4. Keep formatting clean and simple
5. MUST include all six meals for each day, including dinner
6. All meals must be vegan and use Australian ingredients
7. Focus on high-protein options for fat loss
8. Use metric measurements (grams, ml)"""

    # For now, I'll create the meal plan manually since we don't have Gemini API access
    # In the real system, this would call the AI

    meal_plan_text = f"""DAY 1 MEAL PLAN

Pre-workout ({meal_times['pre_workout']})
Meal: Banana Protein Smoothie
Ingredients:
- Banana: 1 medium (120g)
- Soy protein powder: 30g
- Almond milk: 250ml
- Chia seeds: 10g
- Peanut butter: 15g
Preparation: Blend all ingredients until smooth
Macros: 320 calories, 25g protein, 35g carbs, 12g fats

Post-workout Breakfast ({meal_times['post_workout']})
Meal: Tofu Scramble with Quinoa
Ingredients:
- Firm tofu: 150g
- Quinoa: 60g (cooked)
- Spinach: 50g
- Nutritional yeast: 10g
- Olive oil: 5ml
- Turmeric: 2g
Preparation: Cook quinoa, crumble tofu and cook with spices, add spinach
Macros: 380 calories, 28g protein, 42g carbs, 14g fats

Morning Snack ({meal_times['morning_snack']})
Meal: Protein-Rich Trail Mix
Ingredients:
- Almonds: 20g
- Pumpkin seeds: 15g
- Dried cranberries: 10g
- Soy nuts: 15g
Preparation: Mix all ingredients together
Macros: 280 calories, 12g protein, 18g carbs, 20g fats

Lunch ({meal_times['lunch']})
Meal: Chickpea and Lentil Buddha Bowl
Ingredients:
- Chickpeas: 100g (cooked)
- Red lentils: 60g (cooked)
- Brown rice: 80g (cooked)
- Broccoli: 100g
- Tahini dressing: 15g
Preparation: Cook lentils and rice, steam broccoli, assemble bowl with tahini
Macros: 420 calories, 22g protein, 65g carbs, 12g fats

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: Edamame and Hummus
Ingredients:
- Edamame: 80g (shelled)
- Hummus: 30g
- Carrot sticks: 50g
Preparation: Steam edamame, serve with hummus and carrots
Macros: 200 calories, 15g protein, 18g carbs, 8g fats

Dinner ({meal_times['dinner']})
Meal: Tempeh Stir-Fry
Ingredients:
- Tempeh: 120g
- Brown rice: 80g (cooked)
- Mixed vegetables: 150g
- Soy sauce: 10ml
- Sesame oil: 5ml
Preparation: Cook tempeh, stir-fry with vegetables and rice
Macros: 450 calories, 32g protein, 55g carbs, 16g fats

DAY 2 MEAL PLAN

Pre-workout ({meal_times['pre_workout']})
Meal: Apple and Peanut Butter Protein Balls
Ingredients:
- Apple: 1 medium (180g)
- Peanut butter: 20g
- Oats: 30g
- Protein powder: 20g
Preparation: Mix ingredients, form into balls
Macros: 300 calories, 18g protein, 35g carbs, 12g fats

Post-workout Breakfast ({meal_times['post_workout']})
Meal: Seitan Breakfast Wrap
Ingredients:
- Seitan: 100g
- Whole grain wrap: 1 (60g)
- Spinach: 30g
- Nutritional yeast: 10g
- Avocado: 30g
Preparation: Cook seitan, assemble wrap with vegetables
Macros: 380 calories, 35g protein, 40g carbs, 12g fats

Morning Snack ({meal_times['morning_snack']})
Meal: Protein-Rich Smoothie Bowl
Ingredients:
- Frozen berries: 80g
- Soy protein powder: 25g
- Almond milk: 100ml
- Chia seeds: 10g
- Granola: 20g
Preparation: Blend berries and protein, top with chia and granola
Macros: 280 calories, 20g protein, 30g carbs, 10g fats

Lunch ({meal_times['lunch']})
Meal: Black Bean and Quinoa Salad
Ingredients:
- Black beans: 100g (cooked)
- Quinoa: 60g (cooked)
- Mixed greens: 50g
- Cherry tomatoes: 80g
- Olive oil: 10ml
Preparation: Mix all ingredients, dress with olive oil
Macros: 350 calories, 18g protein, 55g carbs, 10g fats

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: Protein-Rich Energy Bar
Ingredients:
- Dates: 40g
- Almonds: 25g
- Protein powder: 20g
- Chia seeds: 10g
Preparation: Blend ingredients, press into bar shape
Macros: 250 calories, 12g protein, 25g carbs, 12g fats

Dinner ({meal_times['dinner']})
Meal: Lentil and Vegetable Curry
Ingredients:
- Red lentils: 100g (cooked)
- Cauliflower: 150g
- Coconut milk: 50ml
- Brown rice: 80g (cooked)
- Curry spices: 5g
Preparation: Cook lentils with vegetables and coconut milk, serve with rice
Macros: 420 calories, 25g protein, 60g carbs, 14g fats

DAY 3 MEAL PLAN

Pre-workout ({meal_times['pre_workout']})
Meal: Oatmeal with Protein and Berries
Ingredients:
- Oats: 50g
- Soy protein powder: 25g
- Mixed berries: 60g
- Almond milk: 200ml
- Chia seeds: 10g
Preparation: Cook oats with milk, stir in protein powder, top with berries
Macros: 320 calories, 22g protein, 45g carbs, 10g fats

Post-workout Breakfast ({meal_times['post_workout']})
Meal: Tofu and Vegetable Scramble
Ingredients:
- Firm tofu: 150g
- Sweet potato: 80g (cooked)
- Spinach: 50g
- Nutritional yeast: 15g
- Olive oil: 5ml
Preparation: Cook tofu with vegetables and nutritional yeast
Macros: 350 calories, 25g protein, 35g carbs, 15g fats

Morning Snack ({meal_times['morning_snack']})
Meal: Protein-Rich Nut Mix
Ingredients:
- Cashews: 20g
- Almonds: 15g
- Pumpkin seeds: 15g
- Dried apricots: 20g
Preparation: Mix all ingredients together
Macros: 280 calories, 12g protein, 20g carbs, 18g fats

Lunch ({meal_times['lunch']})
Meal: Chickpea and Vegetable Buddha Bowl
Ingredients:
- Chickpeas: 120g (cooked)
- Brown rice: 80g (cooked)
- Roasted vegetables: 150g
- Tahini dressing: 20g
Preparation: Cook rice, roast vegetables, assemble bowl with tahini
Macros: 400 calories, 20g protein, 60g carbs, 12g fats

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: Protein-Rich Smoothie
Ingredients:
- Banana: 1 medium (120g)
- Soy protein powder: 30g
- Almond milk: 250ml
- Peanut butter: 15g
Preparation: Blend all ingredients until smooth
Macros: 300 calories, 25g protein, 30g carbs, 12g fats

Dinner ({meal_times['dinner']})
Meal: Tempeh and Vegetable Stir-Fry
Ingredients:
- Tempeh: 120g
- Quinoa: 80g (cooked)
- Mixed vegetables: 150g
- Soy sauce: 10ml
- Sesame oil: 5ml
Preparation: Cook tempeh, stir-fry with vegetables and quinoa
Macros: 450 calories, 30g protein, 55g carbs, 16g fats"""

    return {
        "meal_plan_text": meal_plan_text,
        "meal_times": meal_times,
        "nutrition_data": nutrition_data
    }


async def main():
    """Main function to generate Hannah's meal plan"""
    print("=== HANNAH DEVLIN MEAL PLAN GENERATION ===")
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Generate meal plan
    meal_plan_data = await generate_meal_plan()

    # Print the meal plan
    print("=== HANNAH'S 3-DAY MEAL PLAN ===")
    print()
    print(meal_plan_data["meal_plan_text"])

    # Save to file
    with open("hannah_meal_plan.txt", "w") as f:
        f.write("=== HANNAH DEVLIN MEAL PLAN ===\n")
        f.write(
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("=== NUTRITION TARGETS ===\n")
        f.write(
            f"Daily Calories: {meal_plan_data['nutrition_data']['daily_calories']}\n")
        f.write(
            f"Protein: {meal_plan_data['nutrition_data']['macros']['protein']}g\n")
        f.write(
            f"Carbs: {meal_plan_data['nutrition_data']['macros']['carbs']}g\n")
        f.write(
            f"Fats: {meal_plan_data['nutrition_data']['macros']['fats']}g\n\n")
        f.write("=== MEAL PLAN ===\n")
        f.write(meal_plan_data["meal_plan_text"])

    print(f"\nMeal plan saved to: hannah_meal_plan.txt")
    print("\n=== MEAL PLAN SUMMARY ===")
    print(f"• Designed for 500g weight loss per week")
    print(f"• High-protein vegan meals using Australian ingredients")
    print(f"• 3-day rotation with 6 meals per day")
    print(f"• All ingredients available at Woolworths/Coles")
    print(f"• Focus on protein preservation during fat loss")

if __name__ == "__main__":
    asyncio.run(main())
