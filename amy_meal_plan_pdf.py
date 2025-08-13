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

# Amy's data
AMY_DATA = {
    "personal_info": {
        "full_name": {"value": "Amy Burchell", "confidence": 100},
        "email": {"value": "amyburchell@icloud.com", "confidence": 100},
        "phone": {"value": "+61 407 686 394", "confidence": 100},
        "birth_date": {"value": "1984-07-11", "confidence": 100},
        "gender": {"value": "Female", "confidence": 100}
    },
    "physical_info": {
        "current_weight": {"value": "45.2", "confidence": 100},
        "height": {"value": "157.5", "confidence": 100},
        "primary_fitness_goal": {"value": "Body Recomposition", "confidence": 100},
        "activity_level": {"value": "Lightly active - light exercise 6-7 days per week", "confidence": 100}
    },
    "dietary_info": {
        "diet_type": {"value": "Vegetarian", "confidence": 100},
        "disliked_foods": {"value": "Pork, Shellfish, Fish", "confidence": 100},
        "regular_meals": {
            "breakfast": {"value": "Not specified", "confidence": 50},
            "lunch": {"value": "Not specified", "confidence": 50},
            "dinner": {"value": "Not specified", "confidence": 50}
        }
    },
    "training_info": {
        "training_days": {"value": "Wed, Thurs, Fri, Sat, Sun", "confidence": 100},
        "workout_time": {"value": "Not specified", "confidence": 50},
        "gym_access": {"value": "At Home With Weights", "confidence": 100},
        "activities": {"value": "Bodyfit twice per week, walking dog most days", "confidence": 100}
    }
}


def calculate_nutrition_for_body_recomposition():
    """Calculate nutrition targets for weight loss with muscle preservation"""

    # Amy's stats
    weight_kg = 45.2
    height_cm = 157.5
    age = 2025 - 1984  # 41 years old
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

    # For healthy weight loss, create a 300 calorie deficit (not 500)
    # This allows for sustainable fat loss while maintaining energy and muscle
    daily_calories = tdee - 300

    # Macro breakdown for weight loss with muscle preservation
    # Higher protein to preserve muscle, moderate carbs for energy, moderate fat
    protein_percentage = 0.35  # 35% protein (higher to preserve muscle)
    fat_percentage = 0.25      # 25% fat
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
            "deficit": 300,
            "target": "Lose fat, preserve muscle, healthy eating rhythm"
        }
    }


def calculate_meal_times(workout_time="Not specified"):
    """Calculate meal times based on workout schedule"""

    if workout_time == "Not specified":
        return {
            "pre_workout": "5:00 PM",
            "post_workout": "7:30 PM",
            "morning_snack": "10:00 AM",
            "lunch": "12:30 PM",
            "afternoon_snack": "3:00 PM",
            "dinner": "8:30 PM"
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


def get_meal_plan_text():
    """Get the meal plan text with high-protein vegetarian meals for weight loss"""
    meal_times = calculate_meal_times("Not specified")

    return f"""DAY 1 MEAL PLAN

Breakfast ({meal_times['morning_snack']})
Meal: Blueberry Peanut Butter Smoothie
Ingredients:
- 60g Frozen Banana
- 60g Blueberries
- 15g Peanut Butter
- 200ml Unsweetened Almond Milk
- 1 Protein Scoop
Preparation: Blend all ingredients until smooth and creamy (3 minutes)
Macros: 320 calories, 35g carbs, 25g protein, 12g fats

Lunch ({meal_times['lunch']})
Meal: Wellness Bowl
Ingredients:
- 1 Low Carb Wrap
- 80g Mixed Vegetables (capsicum, onion, zucchini)
- 40g Plant-based Chicken-free Strips
- 15ml Vegan Mayo
- 10g Fresh Coriander
Preparation: Warm wrap. Cook chicken-free strips and vegetables. Assemble bowl with wrap, vegetables, strips, mayo, and coriander (15 minutes)
Macros: 380 calories, 35g carbs, 25g protein, 12g fats

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: MuscleNation Chocolate
Ingredients:
- 30g MuscleNation Chocolate
Preparation: Enjoy chocolate (1 minute)
Macros: 150 calories, 3g carbs, 2g protein, 10g fats

Dinner ({meal_times['dinner']})
Meal: Vegan Spag Bowl
Ingredients:
- 80g Vetta Protein Pasta
- 25g TVP (microwaved with water)
- 120g Air-fried Vegetables (capsicum, onion, zucchini)
- 80ml Pasta Sauce
- 10g Nutritional Yeast
Preparation: Cook pasta. Rehydrate TVP with water. Air-fry vegetables. Combine with pasta sauce and nutritional yeast (20 minutes)
Macros: 340 calories, 60g carbs, 30g protein, 2g fats

Daily Totals (Day 1):
Calories: 1190
Protein: 82g
Carbs: 133g
Fats: 36g

DAY 2 MEAL PLAN

Breakfast ({meal_times['morning_snack']})
Meal: Vitasoy Yogurt Bowl
Ingredients:
- 120g Vitasoy Yogurt
- 80g Blueberries
- 80g Strawberries
- 20g Granola
Preparation: Combine yogurt with berries and granola (3 minutes)
Macros: 280 calories, 35g carbs, 15g protein, 8g fats

Lunch ({meal_times['lunch']})
Meal: Mock Chicken Wrap
Ingredients:
- 1 Low Carb Wrap
- 40g Plant-based Chicken-free Strips
- 15ml Vegan Mayo
- 80g Mixed Vegetables (capsicum, onion, lettuce)
- 10g Fresh Coriander
Preparation: Warm wrap. Cook chicken-free strips. Assemble wrap with strips, mayo, vegetables, and coriander (10 minutes)
Macros: 320 calories, 25g carbs, 25g protein, 15g fats

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: Fro Pro Vegan Ice Cream
Ingredients:
- 1/2 Tub Fro Pro Vegan Ice Cream
Preparation: Enjoy ice cream (2 minutes)
Macros: 200 calories, 3g carbs, 2g protein, 14g fats

Dinner ({meal_times['dinner']})
Meal: Vegan Pizza
Ingredients:
- 80g Protein Pizza Base
- 40g Plant-based Chicken-free Strips
- 25g Vegan Bio Cheese
- 120g Mixed Vegetables (eggplant, zucchini, tomato, mushroom, capsicum, red onion)
- 40ml Tomato Paste
Preparation: Spread tomato paste on pizza base. Top with chicken-free strips, vegetables, and vegan cheese. Bake until crispy (15 minutes)
Macros: 350 calories, 40g carbs, 22g protein, 15g fats

Daily Totals (Day 2):
Calories: 1150
Protein: 64g
Carbs: 103g
Fats: 52g

DAY 3 MEAL PLAN

Breakfast ({meal_times['morning_snack']})
Meal: Tofu Scramble
Ingredients:
- 120g Soyco High Protein Tofu
- 1 Small Tomato, chopped
- 1/2 Cup Spinach
- ½ Small Onion, chopped
- 1 Slice High Protein Bread
- ¼ Avocado
Preparation: Crumble tofu and scramble with vegetables. Toast bread and serve with avocado (15 minutes)
Macros: 320 calories, 30g carbs, 20g protein, 15g fats

Lunch ({meal_times['lunch']})
Meal: Tempeh Stir-Fry with Quinoa
Ingredients:
- 80g Tempeh
- 80g Quinoa (cooked)
- 150g Mixed Vegetables (carrots, bell peppers, broccoli)
- 12ml Soy Sauce
- 8ml Sesame Oil
Preparation: Cook quinoa. Stir-fry tempeh and vegetables with soy sauce and sesame oil. Serve over quinoa (20 minutes)
Macros: 360 calories, 45g carbs, 25g protein, 10g fats

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: Macro Mike Brownie with Almond Milk
Ingredients:
- 60g Macro Mike Brownie
- 80ml Unsweetened Almond Milk
Preparation: Enjoy brownie with almond milk (2 minutes)
Macros: 200 calories, 20g carbs, 15g protein, 5g fats

Dinner ({meal_times['dinner']})
Meal: Green Goddess Pasta
Ingredients:
- 80g Vetta Protein Pasta
- 120g Air-fried Vegetables (capsicum, onion, zucchini)
- 20ml Green Goddess Dressing
- 10g Fresh Basil
Preparation: Cook pasta. Air-fry vegetables. Toss with green goddess dressing and fresh basil (15 minutes)
Macros: 300 calories, 45g carbs, 20g protein, 5g fats

Daily Totals (Day 3):
Calories: 1180
Protein: 80g
Carbs: 140g
Fats: 35g

INGREDIENT SHOPPING LIST

Proteins & Dairy:
• Coles Perform Plant Protein Vanilla 455g
• Vitasoy Yogurt 150g
• Soyco High Protein Tofu 350g
• Plant-based Chicken-free Strips 250g
• Vegan Bio Cheese 200g
• Tempeh 300g

Pantry & Grains:
• Sanitarium So Good Unsweetened Almond Milk 1L
• Vetta Protein Pasta 500g
• Low Carb Wraps 10 pack
• Quinoa 500g
• High Protein Bread 700g
• Protein Pizza Base 170g
• Kikkoman Soy Sauce 250ml
• Sesame Oil 250ml
• Nutritional Yeast 127g
• Granola 300g
• TVP (Textured Vegetable Protein) 200g
• Pasta Sauce 700ml
• Green Goddess Dressing 250ml

Snacks & Treats:
• Plant-based Protein Bar 40g
• MuscleNation Chocolate 100g
• Fro Pro Vegan Ice Cream 500ml
• Macro Mike Brownie 100g

Produce & Fresh:
• Frozen Bananas
• Blueberries (fresh or frozen)
• Strawberries (fresh or frozen)
• Mixed Vegetables (capsicum, onion, zucchini, carrots, bell peppers, broccoli, eggplant, tomato, mushroom, red onion)
• Spinach
• Avocado
• Fresh Coriander
• Fresh Basil

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
For body recomposition and weight loss, getting adequate protein while managing carbs and fats is crucial. Plant-based diets can absolutely meet these needs, but require more planning and awareness of food choices.

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
                # Reset if we're moving to a different day
                current_day = None
                current_meal = None
                current_content = []
            continue

        # Only process lines if we're in the target day
        if current_day == day_type:
            if line.startswith('Breakfast') or line.startswith('Morning Snack') or line.startswith('Lunch') or line.startswith('Afternoon Snack') or line.startswith('Dinner'):
                # Save previous meal if exists
                if current_meal and current_content:
                    meals[current_meal] = '\n'.join(current_content).strip()
                current_meal = line.split('(')[0].strip()
                current_content = []
            elif current_meal:
                current_content.append(line)

    # Save the last meal of the target day
    if current_day == day_type and current_meal and current_content:
        meals[current_meal] = '\n'.join(current_content).strip()

    return meals


def format_meal_content(content):
    """Format meal content for PDF display"""
    if not content:
        return ""

    # Split content into sections
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
    """Create PDF for Amy's meal plan - matching original styling"""

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
            textColor=colors.HexColor("#0066CC"),
            underline=True
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
        <b>Client:</b> {client_data['personal_info']['full_name']['value']}<br/>
        <b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}<br/>
        <b>Goal:</b> {client_data['physical_info']['primary_fitness_goal']['value']}
        </para>
        """
        story.append(Paragraph(client_info, info_style))

        # Targets box
        targets = f"""
        <para alignment="center" bgcolor="#F5F5F5">
        <b>Daily Targets</b><br/>
        Calories: {nutrition_data['daily_calories']}<br/>
        Protein: {nutrition_data['macros']['protein']}g<br/>
        Carbs: {nutrition_data['macros']['carbs']}g<br/>
        Fats: {nutrition_data['macros']['fats']}g
        </para>
        """
        story.append(Paragraph(targets, info_style))

        # Extract meal plan text without shopping list
        meal_plan_lines = meal_plan_text.split('\n')
        meal_plan_content = []
        shopping_list_content = []
        in_shopping_list = False

        for line in meal_plan_lines:
            if line.strip() == "INGREDIENT SHOPPING LIST":
                in_shopping_list = True
                continue
            if in_shopping_list:
                shopping_list_content.append(line)
            else:
                meal_plan_content.append(line)

        meal_plan_text_only = '\n'.join(meal_plan_content)

        # Day 1 Meal Plan
        story.append(PageBreak())
        story.append(Paragraph("DAY 1 MEAL PLAN", day_title_style))

        # Process meals in specific order
        meal_order = [
            "Breakfast",
            "Morning Snack",
            "Lunch",
            "Afternoon Snack",
            "Dinner"
        ]

        day1_meals = extract_day_meals(meal_plan_text_only, "DAY 1")
        for meal_type in meal_order:
            if meal_type in day1_meals:
                meal_content = []
                meal_content.append(Paragraph(meal_type, meal_title_style))
                meal_content.append(
                    Paragraph(format_meal_content(day1_meals[meal_type]), body_style))
                story.append(KeepTogether(meal_content))

        # Day 2 Meal Plan
        story.append(PageBreak())
        story.append(Paragraph("DAY 2 MEAL PLAN", day_title_style))

        day2_meals = extract_day_meals(meal_plan_text_only, "DAY 2")
        for meal_type in meal_order:
            if meal_type in day2_meals:
                meal_content = []
                meal_content.append(Paragraph(meal_type, meal_title_style))
                meal_content.append(
                    Paragraph(format_meal_content(day2_meals[meal_type]), body_style))
                story.append(KeepTogether(meal_content))

        # Day 3 Meal Plan
        story.append(PageBreak())
        story.append(Paragraph("DAY 3 MEAL PLAN", day_title_style))

        day3_meals = extract_day_meals(meal_plan_text_only, "DAY 3")
        for meal_type in meal_order:
            if meal_type in day3_meals:
                meal_content = []
                meal_content.append(Paragraph(meal_type, meal_title_style))
                meal_content.append(
                    Paragraph(format_meal_content(day3_meals[meal_type]), body_style))
                story.append(KeepTogether(meal_content))

        # Shopping List
        story.append(PageBreak())
        story.append(
            Paragraph("INGREDIENT SHOPPING LIST", shopping_title_style))

        # Add note about clickable links
        note_style = ParagraphStyle(
            'Note',
            parent=body_style,
            fontSize=10,
            spaceAfter=15,
            alignment=1,
            textColor=colors.HexColor("#666666")
        )
        story.append(Paragraph(
            "💡 <b>Tip:</b> All items below are clickable links to help you find products online", note_style))

        # Process shopping list
        shopping_list_text = '\n'.join(shopping_list_content)
        lines = shopping_list_text.split('\n')
        current_category = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.endswith(':') and ('Proteins' in line or 'Pantry' in line or 'Produce' in line):
                current_category = line
                story.append(Paragraph(current_category,
                             shopping_category_style))
            elif line.startswith('•') and current_category:
                # Format as clickable link (in PDF, this will be blue and underlined)
                item_text = line[1:].strip()  # Remove bullet point
                formatted_item = f'<link href="https://www.coles.com.au/search?q={item_text.replace(" ", "%20")}"><u>{item_text}</u></link>'
                story.append(Paragraph(formatted_item, shopping_item_style))
            elif line.startswith('•') and not current_category:
                # Handle items without category
                item_text = line[1:].strip()
                formatted_item = f'<link href="https://www.coles.com.au/search?q={item_text.replace(" ", "%20")}"><u>{item_text}</u></link>'
                story.append(Paragraph(formatted_item, shopping_item_style))

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
        nutrition_text_5 = """For body recomposition and weight loss, getting adequate protein while managing carbs and fats is crucial. Plant-based diets can absolutely meet these needs, but require more planning and awareness of food choices."""
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
        if not os.path.exists(full_path):
            print(f"PDF file was not created at {full_path}")
            return None

        # Log the file size and path
        file_size = os.path.getsize(full_path)
        print(
            f"Created native PDF file: {full_path} (size: {file_size} bytes)")

        return filename

    except Exception as e:
        print(f"Error creating PDF: {e}")
        return None


async def main():
    """Main function to generate Amy's meal plan PDF"""
    print("=== AMY BURCHELL MEAL PLAN PDF GENERATION ===")
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Calculate nutrition targets
    nutrition_data = calculate_nutrition_for_body_recomposition()
    meal_plan_text = get_meal_plan_text()

    print(f"=== AMY'S NUTRITION TARGETS ===")
    print(f"Daily Calories: {nutrition_data['daily_calories']}")
    print(f"Protein: {nutrition_data['macros']['protein']}g")
    print(f"Carbs: {nutrition_data['macros']['carbs']}g")
    print(f"Fats: {nutrition_data['macros']['fats']}g")
    print()

    # Create PDF
    pdf_filename = create_meal_plan_pdf(
        meal_plan_text, AMY_DATA, nutrition_data)

    if pdf_filename:
        print(f"✅ Successfully created PDF: {pdf_filename}")
        print(f"📁 Location: output/meal plans/{pdf_filename}")
        print("\n=== PDF SUMMARY ===")
        print(f"• Professional meal plan PDF for Amy Burchell")
        print(f"• Includes COCOS PT logo and branding")
        print(f"• Blue color scheme matching original design")
        print(f"• High-protein vegetarian meals for body recomposition")
        print(f"• All ingredients available at Australian stores")
    else:
        print("❌ Failed to create PDF")

if __name__ == "__main__":
    asyncio.run(main())
