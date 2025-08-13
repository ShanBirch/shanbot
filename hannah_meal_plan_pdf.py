import asyncio
import json
from datetime import datetime
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

# Constants (matching original)
LOGO_PATH = r"C:\Users\Shannon\OneDrive\Documents\cocos logo.png"
PDF_OUTPUT_DIR = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output\meal plans"

# Hannah's data
HANNAH_DATA = {
    "personal_info": {
        "full_name": {"value": "Hannah Devlin", "confidence": 100},
        "email": {"value": "hannahjanedevlin@gmail.com", "confidence": 100},
        "phone": {"value": "+61 492 859 426", "confidence": 100},
        "birthday": {"value": "1998-09-29", "confidence": 100},
        "age": {"value": 26, "confidence": 100},
        "gender": {"value": "Female", "confidence": 100}
    },
    "fitness_goals": {
        "primary_goal": {"value": "Fat Loss", "confidence": 100},
        "specific_goal": {"value": "68kg", "confidence": 100},
        "current_weight": {"value": "76.5kg", "confidence": 100},
        "height": {"value": "164.5cm", "confidence": 100}
    },
    "lifestyle": {
        "activity_level": {"value": "Lightly active - light exercise 6-7 days per week", "confidence": 100},
        "dietary_preferences": {"value": "Vegan", "confidence": 100},
        "meals_per_day": {"value": "3", "confidence": 100},
        "food_exclusions": {"value": ["Fish", "Eggs", "Pork", "Shellfish", "Dairy"], "confidence": 100}
    },
    "preferences": {
        "favorite_meals": {"value": ["Thai curries", "sheppards pie", "pasta", "spring rolls", "pancakes", "salad", "smoothies", "juice", "burgers", "wraps"], "confidence": 100},
        "training_equipment": {"value": "At Home Body Weight", "confidence": 100},
        "training_schedule": {"value": "Daily walking, rockclimbing 2-3x per week", "confidence": 100}
    }
}


def calculate_nutrition_for_fat_loss():
    """Calculate nutrition targets for fat loss"""

    # Hannah's stats
    weight_kg = 76.5
    height_cm = 164.5
    age = 2025 - 1998  # 27 years old
    gender = "Female"
    activity_level = "Lightly active"

    # Calculate BMR using Mifflin-St Jeor Equation
    if gender == "Male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    # Activity multiplier for "Lightly active"
    activity_multiplier = 1.375

    # Calculate TDEE
    tdee = bmr * activity_multiplier

    # For fat loss, create a 400 calorie deficit
    # This allows for sustainable fat loss while maintaining energy
    daily_calories = tdee - 400

    # Macro breakdown for fat loss
    # Higher protein to preserve muscle, moderate carbs for energy, moderate fat
    protein_percentage = 0.30  # 30% protein (high for muscle preservation)
    fat_percentage = 0.30      # 30% fat
    carbs_percentage = 0.40    # 40% carbs

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
            "deficit": 400,
            "target": "Fat loss from 76.5kg to 68kg"
        }
    }


def calculate_meal_times(training_schedule):
    """Calculate meal times based on training schedule"""
    return {
        "breakfast": "7:00 AM",
        "morning_snack": "10:00 AM",
        "lunch": "1:00 PM",
        "afternoon_snack": "4:00 PM",
        "dinner": "7:00 PM"
    }


def get_meal_plan_text():
    """Get the meal plan text with high-protein vegan meals for fat loss"""
    meal_times = calculate_meal_times("Not specified")

    return f"""DAY 1 MEAL PLAN

Breakfast ({meal_times['breakfast']})
Meal: High Protein Vegan Pancakes
Ingredients:
- 40g Rolled Oats
- 1 Protein Scoop (Vanilla)
- 80g Frozen Banana
- 200ml Unsweetened Almond Milk
- 15g Peanut Butter
- 80g Blueberries
Preparation: Blend oats, protein powder, banana, and almond milk into batter. Cook pancakes in non-stick pan. Serve with peanut butter and blueberries (10 minutes)
Macros: 420 calories, 45g carbs, 28g protein, 16g fats

Lunch ({meal_times['lunch']})
Meal: Thai Green Curry with Tofu
Ingredients:
- 120g Soyco High Protein Tofu, cubed
- 80g Brown Rice (cooked)
- 150g Mixed Vegetables (eggplant, capsicum, green beans)
- 100ml Coconut Milk (light)
- 30g Thai Green Curry Paste
- 15g Fresh Basil
- 10ml Soy Sauce
Preparation: Cook rice. Pan-fry tofu until golden. Stir-fry vegetables with curry paste, add coconut milk and tofu. Simmer 10 minutes. Serve over rice with fresh basil (20 minutes)
Macros: 480 calories, 55g carbs, 25g protein, 18g fats

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: Green Smoothie
Ingredients:
- 200ml Unsweetened Almond Milk
- 100g Spinach
- 80g Frozen Banana
- 60g Frozen Mango
- 20g Vanilla Protein Powder
- 15g Almond Butter
Preparation: Blend all ingredients until smooth and creamy (3 minutes)
Macros: 280 calories, 35g carbs, 18g protein, 10g fats

Dinner ({meal_times['dinner']})
Meal: Vegan Burger with Sweet Potato Fries
Ingredients:
- 1 Plant-based Burger Patty
- 1 Whole Grain Burger Bun
- 100g Sweet Potato Fries (air-fried)
- 50g Mixed Salad Greens
- 15g Avocado
- 20ml Vegan Mayo
- 10g Fresh Coriander
Preparation: Air-fry sweet potato fries. Cook burger patty. Assemble burger with greens, avocado, mayo, and coriander (15 minutes)
Macros: 450 calories, 60g carbs, 22g protein, 16g fats

Daily Totals (Day 1):
Calories: 1630
Protein: 93g
Carbs: 195g
Fats: 60g

DAY 2 MEAL PLAN

Breakfast ({meal_times['breakfast']})
Meal: Berry Protein Smoothie Bowl
Ingredients:
- 150g Vitasoy Yogurt
- 100g Mixed Berries (blueberries, strawberries)
- 20g Granola
- 20g Vanilla Protein Powder
- 15g Chia Seeds
- 10g Coconut Flakes
Preparation: Blend yogurt, protein powder, and half the berries. Pour into bowl and top with remaining berries, granola, chia seeds, and coconut (5 minutes)
Macros: 380 calories, 40g carbs, 25g protein, 15g fats

Lunch ({meal_times['lunch']})
Meal: Vegan Spring Rolls with Peanut Sauce
Ingredients:
- 2 Rice Paper Wraps
- 80g Plant-based Chicken-free Strips
- 100g Mixed Vegetables (carrot, cucumber, capsicum, lettuce)
- 50g Rice Noodles (cooked)
- 20g Peanut Butter
- 15ml Soy Sauce
- 10ml Lime Juice
- 15g Fresh Mint
Preparation: Soak rice paper. Cook chicken-free strips and rice noodles. Assemble spring rolls with vegetables, strips, and noodles. Mix peanut butter, soy sauce, and lime for dipping sauce (15 minutes)
Macros: 420 calories, 50g carbs, 25g protein, 14g fats

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: Macro Mike Brownie with Almond Milk
Ingredients:
- 80g Macro Mike Brownie
- 150ml Unsweetened Almond Milk
Preparation: Enjoy brownie with almond milk (2 minutes)
Macros: 250 calories, 25g carbs, 18g protein, 8g fats

Dinner ({meal_times['dinner']})
Meal: Vetta Protein Pasta with TVP Bolognese
Ingredients:
- 100g Vetta Protein Pasta
- 30g TVP (rehydrated)
- 150g Mixed Vegetables (mushrooms, onion, zucchini)
- 100ml Tomato Passata
- 15g Nutritional Yeast
- 15ml Olive Oil
- 15g Fresh Basil
Preparation: Cook pasta. Rehydrate TVP with hot water. Sauté vegetables in olive oil, add TVP and tomato passata. Simmer 10 minutes. Serve over pasta with nutritional yeast and fresh basil (20 minutes)
Macros: 480 calories, 70g carbs, 35g protein, 8g fats

Daily Totals (Day 2):
Calories: 1530
Protein: 103g
Carbs: 185g
Fats: 45g

DAY 3 MEAL PLAN

Breakfast ({meal_times['breakfast']})
Meal: Tofu Scramble Wrap
Ingredients:
- 1 Low Carb Wrap
- 120g Soyco High Protein Tofu, crumbled
- 80g Spinach
- 50g Mushrooms
- 20g Nutritional Yeast
- 15g Avocado
- 10ml Olive Oil
- 5g Turmeric
Preparation: Scramble tofu with turmeric and nutritional yeast. Sauté spinach and mushrooms. Warm wrap and fill with tofu scramble, vegetables, and avocado (12 minutes)
Macros: 360 calories, 25g carbs, 25g protein, 20g fats

Lunch ({meal_times['lunch']})
Meal: Vegan Shepherd's Pie Bowl
Ingredients:
- 80g Mashed Sweet Potato
- 30g TVP (rehydrated)
- 120g Mixed Vegetables (peas, carrots, corn)
- 50ml Vegetable Stock
- 15ml Soy Sauce
- 10ml Olive Oil
- 15g Fresh Parsley
Preparation: Mash sweet potato. Rehydrate TVP with vegetable stock and soy sauce. Sauté vegetables, add TVP mixture. Top with mashed sweet potato and fresh parsley (18 minutes)
Macros: 380 calories, 55g carbs, 20g protein, 8g fats

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: Plant-based Protein Bar
Ingredients:
- 1 Plant-based Protein Bar
Preparation: Enjoy protein bar (1 minute)
Macros: 220 calories, 15g carbs, 15g protein, 10g fats

Dinner ({meal_times['dinner']})
Meal: Asian Salad with Tempeh
Ingredients:
- 100g Tempeh, sliced
- 150g Mixed Asian Greens (bok choy, spinach, lettuce)
- 80g Quinoa (cooked)
- 50g Cucumber, diced
- 30g Edamame
- 20ml Sesame Oil
- 15ml Soy Sauce
- 10ml Rice Vinegar
- 15g Fresh Coriander
Preparation: Cook quinoa and tempeh. Prepare salad with greens, cucumber, and edamame. Mix sesame oil, soy sauce, and rice vinegar for dressing. Serve tempeh over salad with quinoa and fresh coriander (15 minutes)
Macros: 460 calories, 45g carbs, 28g protein, 22g fats

Daily Totals (Day 3):
Calories: 1420
Protein: 88g
Carbs: 140g
Fats: 60g

INGREDIENT SHOPPING LIST

Proteins & Dairy:
• Coles Perform Plant Protein Vanilla 455g
• Vitasoy Yogurt 150g
• Soyco High Protein Tofu 350g
• Plant-based Chicken-free Strips 250g
• Tempeh 300g
• Plant-based Burger Patty 200g

Pantry & Grains:
• Sanitarium So Good Unsweetened Almond Milk 1L
• Vetta Protein Pasta 500g
• Low Carb Wraps 10 pack
• Quinoa 500g
• Brown Rice 1kg
• Rice Noodles 400g
• Whole Grain Burger Buns 6 pack
• Rice Paper Wraps 10 pack
• Rolled Oats 900g
• Kikkoman Soy Sauce 250ml
• Sesame Oil 250ml
• Nutritional Yeast 127g
• Granola 300g
• TVP (Textured Vegetable Protein) 200g
• Tomato Passata 700ml
• Thai Green Curry Paste 200g
• Coconut Milk (light) 400ml
• Vegetable Stock 1L
• Olive Oil 500ml
• Rice Vinegar 250ml

Snacks & Treats:
• Plant-based Protein Bar 40g
• Macro Mike Brownie 100g
• Peanut Butter 380g
• Almond Butter 380g
• Chia Seeds 200g
• Coconut Flakes 200g

Produce & Fresh:
• Frozen Bananas
• Blueberries (fresh or frozen)
• Mixed Berries (fresh or frozen)
• Frozen Mango
• Strawberries (fresh or frozen)
• Mixed Vegetables (eggplant, capsicum, green beans, mushrooms, onion, zucchini, carrots, cucumber, peas, corn)
• Mixed Asian Greens (bok choy, spinach, lettuce)
• Mixed Salad Greens
• Spinach
• Avocado
• Sweet Potato
• Edamame
• Fresh Basil
• Fresh Mint
• Fresh Coriander
• Fresh Parsley

PLANT-BASED NUTRITION GUIDE

Understanding Plant-Based Protein & Macro Balancing

Plant-based nutrition presents unique challenges compared to animal-based diets, particularly when it comes to protein intake and macro balancing. Here's what you need to know:

Protein Sources in Plant-Based Diets:
Unlike animal proteins which are "complete" (containing all essential amino acids), most plant proteins are "incomplete" - meaning they're lower in one or more essential amino acids. However, this doesn't mean plant-based diets can't provide adequate protein. The key is variety and strategic combining.

The Macro Balancing Challenge:
Plant-based foods naturally come with protein attached to either carbohydrates or fats, making it harder to achieve precise macro ratios. For example:
• Legumes (beans, lentils) provide protein but also significant carbs
• Nuts and seeds offer protein but are high in fats
• Grains like quinoa provide protein but are primarily carb sources

Strategies for Better Macro Control:
1. Use Protein Isolates: Plant-based protein powders (pea, rice, hemp) provide concentrated protein without the accompanying carbs or fats
2. Choose High-Protein Versions: Opt for products like Vetta Protein Pasta (24.9g protein/100g) instead of regular pasta
3. Strategic Food Combining: Pair incomplete proteins throughout the day to create complete amino acid profiles
4. Focus on Protein-Dense Whole Foods: Tofu, tempeh, seitan, and TVP provide more protein per calorie

Why This Matters for Your Goals:
For fat loss while preserving muscle, getting adequate protein while managing carbs and fats is crucial. Plant-based diets can absolutely meet these needs, but require more planning and awareness of food choices.

Tips for Success:
• Track your macros using apps like MyFitnessPal to understand your actual intake
• Prioritize protein at each meal to ensure adequate daily intake
• Don't be afraid to use protein powders and fortified products to meet your targets
• Remember that variety is key - different plant proteins provide different amino acid profiles"""


def extract_day_meals(text, day_type):
    """Extract meals for a specific day from the meal plan text"""
    meals = {}
    lines = text.split('\n')
    current_day = None
    current_meal = None
    current_content = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if this is a day header (DAY 1, DAY 2, DAY 3)
        if line.startswith('DAY ') and 'MEAL PLAN' in line:
            # If we were processing the target day, save the last meal
            if current_day == day_type and current_meal and current_content:
                meals[current_meal] = '\n'.join(current_content).strip()

            # Check if this is our target day
            if day_type in line:
                current_day = day_type
                current_meal = None
                current_content = []
            else:
                current_day = None
                current_meal = None
                current_content = []
            continue

        # If we're in the target day, process meal sections
        if current_day == day_type:
            # Check for meal headers
            if any(meal in line for meal in ['Breakfast', 'Lunch', 'Dinner', 'Morning Snack', 'Afternoon Snack']):
                # Save previous meal if it exists
                if current_meal and current_content:
                    meals[current_meal] = '\n'.join(current_content).strip()

                # Start new meal
                current_meal = line
                current_content = []
            elif line.startswith('Daily Totals'):
                # Save last meal and add daily totals
                if current_meal and current_content:
                    meals[current_meal] = '\n'.join(current_content).strip()

                # Add daily totals as a separate meal entry
                daily_totals_content = []
                daily_totals_content.append(line)
                # Continue reading the daily totals lines
                for next_line in lines[lines.index(line) + 1:]:
                    next_line = next_line.strip()
                    if not next_line or next_line.startswith('DAY '):
                        break
                    daily_totals_content.append(next_line)

                meals['Daily Totals'] = '\n'.join(daily_totals_content).strip()
                break
            else:
                # Add content to current meal
                if current_meal:
                    current_content.append(line)

    # Save the last meal if we're still processing the target day
    if current_day == day_type and current_meal and current_content:
        meals[current_meal] = '\n'.join(current_content).strip()

    return meals


def format_meal_content(content):
    """Format meal content for PDF display"""
    lines = content.split('\n')
    formatted_lines = []

    for line in lines:
        line = line.strip()
        if line.startswith('Meal:'):
            formatted_lines.append(f"<b>{line}</b>")
        elif line.startswith('Ingredients:'):
            formatted_lines.append(f"<b>{line}</b>")
        elif line.startswith('- '):
            formatted_lines.append(f"  {line}")
        elif line.startswith('Preparation:'):
            formatted_lines.append(f"<b>{line}</b>")
        elif line.startswith('Macros:'):
            formatted_lines.append(f"<b>{line}</b>")
        else:
            formatted_lines.append(line)

    return '<br/>'.join(formatted_lines)


def create_meal_plan_pdf(meal_plan_text, client_data, nutrition_data):
    """Create PDF for Hannah's meal plan - matching original styling"""

    try:
        # Create filename as 'Full Name Meal Plan.pdf' (no timestamp, spaces allowed)
        full_name = client_data['personal_info']['full_name']['value'].strip()
        filename = f"{full_name} Meal Plan.pdf"
        full_path = os.path.join(PDF_OUTPUT_DIR, filename)
        print(f"[MEAL PLAN PDF] Using filename: {filename}")

        # Ensure output directory exists
        os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

        # Create a canvas directly first to set PDF metadata
        c = canvas.Canvas(full_path, pagesize=A4)
        c.setTitle(
            f"Meal Plan - {client_data['personal_info']['full_name']['value']}")
        c.setAuthor("COCOS PT")
        c.setCreator("COCOS PT Meal Plan Generator")
        c.setProducer("ReportLab PDF Library")
        c.setSubject("Custom Meal Plan")

        # Save the canvas settings
        c.save()

        # Now create the actual document
        doc = SimpleDocTemplate(
            full_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Rest of your existing PDF creation code...
        styles = getSampleStyleSheet()
        story = []

        # Custom styles - matching original
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=30,
            textColor=colors.HexColor("#1A237E"),
            alignment=1,
            fontName='Helvetica-Bold'
        )

        day_title_style = ParagraphStyle(
            'DayTitle',
            parent=styles['Heading2'],
            fontSize=20,
            spaceBefore=20,
            spaceAfter=20,
            textColor=colors.HexColor("#1A237E"),
            fontName='Helvetica-Bold',
            keepWithNext=True
        )

        meal_title_style = ParagraphStyle(
            'MealTitle',
            parent=styles['Heading3'],
            fontSize=16,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor("#2E3B55"),
            fontName='Helvetica-Bold',
            keepWithNext=True
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=12,
            spaceBefore=6,
            spaceAfter=6,
            leading=16
        )

        shopping_title_style = ParagraphStyle(
            'ShoppingTitle',
            parent=styles['Heading2'],
            fontSize=18,
            spaceBefore=30,
            spaceAfter=15,
            textColor=colors.HexColor("#1A237E"),
            fontName='Helvetica-Bold',
            alignment=1
        )

        shopping_category_style = ParagraphStyle(
            'ShoppingCategory',
            parent=styles['Heading3'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor("#2E3B55"),
            fontName='Helvetica-Bold'
        )

        shopping_item_style = ParagraphStyle(
            'ShoppingItem',
            parent=styles['Normal'],
            fontSize=11,
            spaceBefore=3,
            spaceAfter=3,
            leftIndent=20,
            leading=14,
            textColor=colors.HexColor("#0066CC")
        )

        # Cover page
        if os.path.exists(LOGO_PATH):
            story.append(Image(LOGO_PATH, width=2*inch, height=2*inch))
        story.append(Spacer(1, 30))
        story.append(Paragraph("MEAL PLAN", title_style))

        # Client info box
        info_style = ParagraphStyle(
            'Info',
            parent=body_style,
            alignment=1,
            fontSize=14
        )

        client_info = f"""
        <para alignment="center">
        <b>{client_data['personal_info']['full_name']['value']}</b><br/>
        Goal: {client_data['fitness_goals']['primary_goal']['value']}<br/>
        Current Weight: {client_data['fitness_goals']['current_weight']['value']}<br/>
        Target Weight: {client_data['fitness_goals']['specific_goal']['value']}<br/>
        Dietary Preference: {client_data['lifestyle']['dietary_preferences']['value']}
        </para>
        """
        story.append(Paragraph(client_info, info_style))
        story.append(Spacer(1, 20))

        # Nutrition targets
        nutrition_info = f"""
        <para alignment="center">
        <b>Daily Nutrition Targets</b><br/>
        Calories: {nutrition_data['daily_calories']}<br/>
        Protein: {nutrition_data['macros']['protein']}g<br/>
        Carbs: {nutrition_data['macros']['carbs']}g<br/>
        Fats: {nutrition_data['macros']['fats']}g
        </para>
        """
        story.append(Paragraph(nutrition_info, info_style))
        story.append(PageBreak())

        # Process each day
        for day_num in range(1, 4):
            day_name = f"DAY {day_num}"
            story.append(Paragraph(f"{day_name} MEAL PLAN", day_title_style))

            day_meals = extract_day_meals(meal_plan_text, day_name)

            for meal_header, meal_content in day_meals.items():
                if meal_content:
                    if meal_header == 'Daily Totals':
                        # Style daily totals differently
                        story.append(Paragraph(meal_header, day_title_style))
                        story.append(Paragraph(meal_content, body_style))
                        story.append(Spacer(1, 20))
                    else:
                        story.append(Paragraph(meal_header, meal_title_style))
                        formatted_content = format_meal_content(meal_content)
                        story.append(Paragraph(formatted_content, body_style))
                        story.append(Spacer(1, 15))

            if day_num < 3:
                story.append(PageBreak())

        # Shopping List
        story.append(PageBreak())
        story.append(
            Paragraph("INGREDIENT SHOPPING LIST", shopping_title_style))
        story.append(Spacer(1, 20))

        # Add tip about clickable links
        tip_text = "💡 <b>Tip:</b> Click on any ingredient below to search for it on Coles online!"
        story.append(Paragraph(tip_text, body_style))
        story.append(Spacer(1, 15))

        # Extract shopping list from meal plan text
        shopping_lines = meal_plan_text.split("INGREDIENT SHOPPING LIST")[1].split(
            "PLANT-BASED NUTRITION GUIDE")[0].strip().split('\n')

        current_category = None
        for line in shopping_lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a category header (ends with colon)
            if line.endswith(':'):
                current_category = line
                story.append(Paragraph(current_category,
                             shopping_category_style))
            elif line.startswith('•'):
                # Handle items with bullet points
                item_text = line[1:].strip()
                if item_text:
                    # Format as clickable link with proper URL encoding
                    formatted_item = f'<link href="https://www.coles.com.au/search?q={item_text.replace(" ", "%20")}"><u>{item_text}</u></link>'
                    story.append(
                        Paragraph(formatted_item, shopping_item_style))
                    story.append(Spacer(1, 3))

        # Plant-Based Nutrition Guide
        story.append(PageBreak())
        story.append(
            Paragraph("PLANT-BASED NUTRITION GUIDE", shopping_title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "Understanding Plant-Based Protein & Macro Balancing", meal_title_style))
        story.append(Spacer(1, 8))

        nutrition_text_1 = """Plant-based nutrition presents unique challenges compared to animal-based diets, particularly when it comes to protein intake and macro balancing. Here's what you need to know:"""
        story.append(Paragraph(nutrition_text_1, body_style))
        story.append(Spacer(1, 8))

        story.append(
            Paragraph("Protein Sources in Plant-Based Diets:", meal_title_style))
        nutrition_text_2 = """Unlike animal proteins which are "complete" (containing all essential amino acids), most plant proteins are "incomplete" - meaning they're lower in one or more essential amino acids. However, this doesn't mean plant-based diets can't provide adequate protein. The key is variety and strategic combining."""
        story.append(Paragraph(nutrition_text_2, body_style))
        story.append(Spacer(1, 8))

        story.append(
            Paragraph("The Macro Balancing Challenge:", meal_title_style))
        nutrition_text_3 = """Plant-based foods naturally come with protein attached to either carbohydrates or fats, making it harder to achieve precise macro ratios. For example:<br/>
• Legumes (beans, lentils) provide protein but also significant carbs<br/>
• Nuts and seeds offer protein but are high in fats<br/>
• Grains like quinoa provide protein but are primarily carb sources"""
        story.append(Paragraph(nutrition_text_3, body_style))
        story.append(Spacer(1, 8))

        story.append(
            Paragraph("Strategies for Better Macro Control:", meal_title_style))
        nutrition_text_4 = """1. Use Protein Isolates: Plant-based protein powders (pea, rice, hemp) provide concentrated protein without the accompanying carbs or fats<br/>
2. Choose High-Protein Versions: Opt for products like Vetta Protein Pasta (24.9g protein/100g) instead of regular pasta<br/>
3. Strategic Food Combining: Pair incomplete proteins throughout the day to create complete amino acid profiles<br/>
4. Focus on Protein-Dense Whole Foods: Tofu, tempeh, seitan, and TVP provide more protein per calorie"""
        story.append(Paragraph(nutrition_text_4, body_style))
        story.append(Spacer(1, 8))

        story.append(
            Paragraph("Why This Matters for Your Goals:", meal_title_style))
        nutrition_text_5 = """For fat loss while preserving muscle, getting adequate protein while managing carbs and fats is crucial. Plant-based diets can absolutely meet these needs, but require more planning and awareness of food choices."""
        story.append(Paragraph(nutrition_text_5, body_style))
        story.append(Spacer(1, 8))

        story.append(Paragraph("Tips for Success:", meal_title_style))
        nutrition_text_6 = """• Track your macros using apps like MyFitnessPal to understand your actual intake<br/>
• Prioritize protein at each meal to ensure adequate daily intake<br/>
• Don't be afraid to use protein powders and fortified products to meet your targets<br/>
• Remember that variety is key - different plant proteins provide different amino acid profiles"""
        story.append(Paragraph(nutrition_text_6, body_style))

        # Build the PDF with native PDF settings
        doc.build(story)

        # Verify the file exists and is a valid PDF
        if os.path.exists(full_path) and os.path.getsize(full_path) > 1000:
            file_size = os.path.getsize(full_path)
            print(f"an.pdf (size: {file_size} bytes)")
            print(f"✅ Successfully created PDF: {filename}")
            print(
                f"📁 Location: {PDF_OUTPUT_DIR.replace(os.path.expanduser('~'), '~')}/{filename}")
            return True
        else:
            print("❌ PDF file was not created or is too small")
            return False

    except Exception as e:
        print(f"Error creating PDF: {e}")
        return False


async def main():
    """Main function to generate Hannah's meal plan"""
    try:
        print("=== HANNAH DEVLIN MEAL PLAN PDF GENERATION ===")
        print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Calculate nutrition
        nutrition_data = calculate_nutrition_for_fat_loss()
        print("=== HANNAH'S NUTRITION TARGETS ===")
        print(f"Daily Calories: {nutrition_data['daily_calories']}")
        print(f"Protein: {nutrition_data['macros']['protein']}g")
        print(f"Carbs: {nutrition_data['macros']['carbs']}g")
        print(f"Fats: {nutrition_data['macros']['fats']}g")

        # Get meal plan text
        meal_plan_text = get_meal_plan_text()

        # Create PDF
        success = create_meal_plan_pdf(
            meal_plan_text, HANNAH_DATA, nutrition_data)

        if success:
            print()
            print("=== PDF SUMMARY ===")
            print("• Professional meal plan PDF for Hannah Devlin")
            print("• Includes COCOS PT logo and branding")
            print("• Blue color scheme matching original design")
            print("• High-protein vegan meals for fat loss")
            print("• All ingredients available at Australian stores")

    except Exception as e:
        print(f"Error in main function: {e}")


if __name__ == "__main__":
    asyncio.run(main())
