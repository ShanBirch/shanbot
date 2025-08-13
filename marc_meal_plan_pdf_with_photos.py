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
MEAL_PHOTOS_DIR = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\meal_photos"

# Marc's data
MARC_DATA = {
    "personal_info": {
        "full_name": {"value": "Marc Potter", "confidence": 100},
        "email": {"value": "aussiepotter1@hotmail.com", "confidence": 100},
        "phone": {"value": "+61 412 682 426", "confidence": 100},
        "birth_date": {"value": "1963-05-29", "confidence": 100},
        "gender": {"value": "Male", "confidence": 100}
    },
    "physical_info": {
        "current_weight": {"value": "85", "confidence": 100},
        "height": {"value": "176", "confidence": 100},
        "primary_fitness_goal": {"value": "Improved Cardiovascular", "confidence": 100},
        "activity_level": {"value": "Sedentary - Little/no exercise - desk job", "confidence": 100}
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
        "workout_time": {"value": "Not specified", "confidence": 50},
        "gym_access": {"value": "At Home With Weights", "confidence": 100},
        "activities": {"value": "Limited walking due to injury. Can't run.", "confidence": 100}
    }
}

# Meal photo mapping
MEAL_PHOTOS = {
    "Wellness Bowl with Curry Roasted Vegetables": "wellness_bowl.jpg",
    "Green Lentil Curry with Rice": "green_lentil_curry.jpg",
    "Mock Chicken Wrap with Red Curry": "chicken_wrap.jpg",
    "Red Lentil Dahl with Rice": "red_lentil_dahl.jpg",
    "Tempeh Stir-Fry with Yellow Curry": "tempeh_stirfry.jpg",
    "Penang Curry with Rice": "penang_curry.jpg"
}


def calculate_nutrition_for_cardiovascular_improvement():
    """Calculate nutrition targets for cardiovascular improvement and weight loss"""

    # Marc's stats
    weight_kg = 85
    height_cm = 176
    age = 2025 - 1963  # 62 years old
    gender = "Male"
    activity_level = "Sedentary"

    # Calculate BMR using Mifflin-St Jeor Equation
    if gender == "Male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    # Activity multiplier for "Sedentary"
    activity_multiplier = 1.2

    # Calculate TDEE
    tdee = bmr * activity_multiplier

    # For cardiovascular improvement and weight loss, create a moderate deficit
    # Target weight: 75kg (10kg loss goal)
    # Create a 500 calorie deficit for steady weight loss
    daily_calories = tdee - 500

    # Macro breakdown for cardiovascular health and weight loss
    # Higher protein to preserve muscle, moderate carbs for energy, lower fat
    protein_percentage = 0.30  # 30% protein
    fat_percentage = 0.20      # 20% fat (lower for heart health)
    carbs_percentage = 0.50    # 50% carbs (higher for energy)

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
            "deficit": 500,
            "target_weight": 75
        }
    }


def calculate_meal_times(workout_time="Not specified"):
    """Calculate meal times based on workout time"""
    if workout_time == "Not specified":
        return {
            "breakfast": "7:00 AM",
            "morning_snack": "10:00 AM",
            "lunch": "12:30 PM",
            "afternoon_snack": "3:30 PM",
            "dinner": "7:00 PM"
        }
    else:
        # Parse workout time and adjust meal times accordingly
        return {
            "breakfast": "7:00 AM",
            "morning_snack": "10:00 AM",
            "lunch": "12:30 PM",
            "afternoon_snack": "3:30 PM",
            "dinner": "7:00 PM"
        }


def get_meal_plan_text():
    """Get the meal plan text with heart-healthy vegan meals for cardiovascular improvement - 2 meals per day using grams"""
    meal_times = calculate_meal_times("Not specified")

    return f"""DAY 1 MEAL PLAN

Lunch ({meal_times['lunch']})
Meal: Wellness Bowl with Curry Roasted Vegetables
Ingredients:
- 1 Low Carb Wrap (Coles 85% Lower Carb High Protein Loaf)
- 200g Mixed Roasted Vegetables (sweet potato, capsicum, cauliflower)
- 15g Tandoori Spice Mix
- 80g Plant-based Chicken Free Strips
- 8g Fresh Coriander
- 20ml Olive Oil
- 40g Mixed Nuts and Seeds
- 30g Nutritional Yeast
Preparation: Roast vegetables with tandoori spices and olive oil. Warm wrap and fill with roasted vegetables, chicken strips, nuts/seeds, nutritional yeast, and fresh coriander (15 minutes)
Macros: 740 calories, 60g carbs, 55g protein, 28g fats

Dinner ({meal_times['dinner']})
Meal: Green Lentil Curry with Rice
Ingredients:
- 150g Brown Rice (cooked)
- 150g Green Lentils (cooked)
- 200g Mixed Vegetables (capsicum, snow peas, mushrooms)
- 20g Green Curry Paste
- 250ml Coconut Milk (light)
- 8g Fresh Coriander
- 20ml Soy Sauce
- 30g Nutritional Yeast
Preparation: Cook rice and lentils. Sauté green curry paste, add coconut milk and vegetables. Simmer for 10 minutes. Add cooked lentils and serve over rice with fresh coriander and nutritional yeast (20 minutes)
Macros: 740 calories, 85g carbs, 38g protein, 24g fats

Daily Totals (Day 1):
Calories: 1480
Protein: 93g
Carbs: 145g
Fats: 52g

DAY 2 MEAL PLAN

Lunch ({meal_times['lunch']})
Meal: Mock Chicken Wrap with Red Curry
Ingredients:
- 1 Low Carb Wrap
- 80g Plant-based Chicken Free Strips
- 20g Red Curry Paste
- 25ml Vegan Mayo
- 150g Mixed Vegetables (capsicum, cucumber, red onion)
- 8g Fresh Coriander
- 30g Mixed Nuts and Seeds
- 25g Nutritional Yeast
Preparation: Warm wrap. Mix chicken strips with red curry paste. Fill wrap with curry chicken, vegetables, vegan mayo, nuts/seeds, nutritional yeast, and fresh coriander (8 minutes)
Macros: 660 calories, 40g carbs, 45g protein, 32g fats

Dinner ({meal_times['dinner']})
Meal: Red Lentil Dahl with Rice
Ingredients:
- 150g Brown Rice (cooked)
- 150g Red Lentils (cooked)
- 200g Mixed Vegetables (capsicum, onion, spinach)
- 20g Red Curry Paste
- 250ml Coconut Milk (light)
- 8g Fresh Coriander
- 20ml Soy Sauce
- 30g Nutritional Yeast
Preparation: Cook rice and lentils. Sauté red curry paste, add coconut milk and vegetables. Simmer for 10 minutes. Add cooked lentils and serve over rice with fresh coriander and nutritional yeast (20 minutes)
Macros: 660 calories, 90g carbs, 38g protein, 26g fats

Daily Totals (Day 2):
Calories: 1320
Protein: 83g
Carbs: 130g
Fats: 58g

DAY 3 MEAL PLAN

Lunch ({meal_times['lunch']})
Meal: Tempeh Stir-Fry with Yellow Curry
Ingredients:
- 150g Tempeh
- 150g Quinoa (cooked)
- 250g Mixed Vegetables (carrots, bell peppers, broccoli)
- 20g Yellow Curry Paste
- 20ml Soy Sauce
- 8g Fresh Coriander
- 30g Mixed Nuts and Seeds
- 25g Nutritional Yeast
Preparation: Stir-fry tempeh and vegetables with yellow curry paste and soy sauce. Serve over quinoa with fresh coriander, nuts/seeds, and nutritional yeast (15 minutes)
Macros: 720 calories, 75g carbs, 45g protein, 28g fats

Dinner ({meal_times['dinner']})
Meal: Penang Curry with Rice
Ingredients:
- 150g Brown Rice (cooked)
- 200g Mixed Vegetables (capsicum, snow peas, mushrooms)
- 20g Penang Curry Paste
- 250ml Coconut Milk (light)
- 80g Plant-based Chicken Free Strips
- 8g Fresh Coriander
- 20ml Soy Sauce
- 30g Nutritional Yeast
Preparation: Cook rice. Sauté penang curry paste, add coconut milk and vegetables. Simmer for 10 minutes. Add chicken strips and serve over rice with fresh coriander and nutritional yeast (20 minutes)
Macros: 720 calories, 80g carbs, 38g protein, 32g fats

Daily Totals (Day 3):
Calories: 1440
Protein: 83g
Carbs: 155g
Fats: 60g

INGREDIENT SHOPPING LIST

Proteins & Dairy Alternatives:
• Coles Perform Plant Protein Vanilla 455g
• Vitasoy Yogurt 150g
• Plant-based Chicken Free Strips 250g
• Soyco High Protein Tofu 350g
• Vegan Bio Cheese 200g
• TVP (Textured Vegetable Protein) 200g
• Tempeh 300g

Pantry & Grains:
• Sanitarium So Good Unsweetened Almond Milk 1L
• Coles 85% Lower Carb High Protein Loaf 700g
• Coles Lower Carb Wraps 5 pack
• Quinoa 500g
• Coles Brown Rice 1kg
• Coles Coconut Milk 400ml
• Coles Penang Curry Paste 200g
• Coles Green Curry Paste 200g
• Coles Red Curry Paste 200g
• Coles Yellow Curry Paste 200g
• Coles Tandoori Spice Mix 100g
• Kikkoman Soy Sauce 250ml
• Vegan Mayo 375ml
• Nutritional Yeast 127g
• Granola 300g
• Red Lentils 500g

Snacks & Protein Products:
• Coles Perform Plant Protein Vanilla 455g
• Mixed Nuts and Seeds 300g
• Chia Seeds 200g

Produce & Fresh:
• Frozen Bananas
• Blueberries (fresh or frozen)
• Strawberries
• Mixed Vegetables (capsicum, onion, zucchini, cauliflower, sweet potato, eggplant, tomato, mushroom, red onion, carrots, broccoli, snow peas)
• Spinach
• Fresh Coriander
• Fresh Basil
• Avocado"""


def extract_day_meals(text, day_type):
    """Extract meals for a specific day"""
    meals = {}
    lines = text.split('\n')
    current_meal = None
    current_content = []

    for line in lines:
        line = line.strip()
        if line.startswith(day_type):
            # Reset for new day
            current_meal = None
            current_content = []
            continue

        if line.startswith('Lunch') or line.startswith('Dinner'):
            # Save previous meal if exists
            if current_meal and current_content:
                meals[current_meal] = '\n'.join(current_content)

            # Start new meal
            current_meal = line.split('(')[0].strip()
            current_content = []
        elif current_meal and line:
            current_content.append(line)
        elif line.startswith('Daily Totals'):
            # Save the last meal
            if current_meal and current_content:
                meals[current_meal] = '\n'.join(current_content)
            break

    return meals


def format_meal_content(content):
    """Format meal content for PDF display"""
    # Convert bullet points to proper formatting
    formatted = content.replace('- ', '• ')
    return formatted


def get_meal_photo_path(meal_name):
    """Get the photo path for a specific meal"""
    photo_filename = MEAL_PHOTOS.get(meal_name, "default_meal.jpg")
    photo_path = os.path.join(MEAL_PHOTOS_DIR, photo_filename)

    # Check if photo exists, otherwise return None
    if os.path.exists(photo_path):
        return photo_path
    else:
        print(f"⚠️  Photo not found: {photo_path}")
        return None


def create_meal_plan_pdf(meal_plan_text, client_data, nutrition_data):
    """Create PDF for Marc's meal plan with photos - matching original styling"""

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
            textColor=colors.HexColor("#0066CC"),
            underline=True
        )

        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=14,
            spaceBefore=10,
            spaceAfter=10,
            alignment=1
        )

        # Cover page with logo
        if os.path.exists(LOGO_PATH):
            logo_img = Image(LOGO_PATH, width=2*inch, height=1.5*inch)
            logo_img.hAlign = 'CENTER'
            story.append(logo_img)
            story.append(Spacer(1, 20))

        story.append(Paragraph("COCOS PT", title_style))
        story.append(Paragraph("MEAL PLAN", title_style))

        # Client info box
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
            "Lunch",
            "Dinner"
        ]

        day1_meals = extract_day_meals(meal_plan_text_only, "DAY 1")
        for meal_type in meal_order:
            if meal_type in day1_meals:
                meal_content = []
                meal_content.append(Paragraph(meal_type, meal_title_style))

                # Add meal photo if available
                meal_text = day1_meals[meal_type]
                meal_name = None
                for line in meal_text.split('\n'):
                    if line.startswith('Meal:'):
                        meal_name = line.replace('Meal:', '').strip()
                        break

                if meal_name:
                    photo_path = get_meal_photo_path(meal_name)
                    if photo_path:
                        try:
                            meal_img = Image(
                                photo_path, width=3*inch, height=2.25*inch)
                            meal_img.hAlign = 'CENTER'
                            meal_content.append(meal_img)
                            meal_content.append(Spacer(1, 10))
                        except Exception as e:
                            print(f"⚠️  Error loading photo {photo_path}: {e}")

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

                # Add meal photo if available
                meal_text = day2_meals[meal_type]
                meal_name = None
                for line in meal_text.split('\n'):
                    if line.startswith('Meal:'):
                        meal_name = line.replace('Meal:', '').strip()
                        break

                if meal_name:
                    photo_path = get_meal_photo_path(meal_name)
                    if photo_path:
                        try:
                            meal_img = Image(
                                photo_path, width=3*inch, height=2.25*inch)
                            meal_img.hAlign = 'CENTER'
                            meal_content.append(meal_img)
                            meal_content.append(Spacer(1, 10))
                        except Exception as e:
                            print(f"⚠️  Error loading photo {photo_path}: {e}")

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

                # Add meal photo if available
                meal_text = day3_meals[meal_type]
                meal_name = None
                for line in meal_text.split('\n'):
                    if line.startswith('Meal:'):
                        meal_name = line.replace('Meal:', '').strip()
                        break

                if meal_name:
                    photo_path = get_meal_photo_path(meal_name)
                    if photo_path:
                        try:
                            meal_img = Image(
                                photo_path, width=3*inch, height=2.25*inch)
                            meal_img.hAlign = 'CENTER'
                            meal_content.append(meal_img)
                            meal_content.append(Spacer(1, 10))
                        except Exception as e:
                            print(f"⚠️  Error loading photo {photo_path}: {e}")

                meal_content.append(
                    Paragraph(format_meal_content(day3_meals[meal_type]), body_style))
                story.append(KeepTogether(meal_content))

        # Add shopping list section
        if shopping_list_content:
            story.append(PageBreak())
            story.append(
                Paragraph("INGREDIENT SHOPPING LIST", shopping_title_style))
            story.append(Spacer(1, 12))

            # Add tip about clickable links
            story.append(Paragraph(
                "💡 Tip: Click on any ingredient to search for it at Coles!", body_style))
            story.append(Spacer(1, 12))

            current_category = None
            for line in shopping_list_content:
                line = line.strip()
                if not line:
                    continue

                # Check if this is a category header
                if line.endswith(':') and not line.startswith('•'):
                    current_category = line
                    story.append(Paragraph(current_category,
                                 shopping_category_style))
                elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    # This is an item
                    item_text = line[1:].strip()
                    if item_text:
                        # Create clickable link
                        formatted_item = f'<u><link href="https://www.coles.com.au/search?q={item_text.replace(" ", "%20")}">{item_text}</link></u>'
                        story.append(
                            Paragraph(formatted_item, shopping_item_style))

            # Add plant-based nutrition guide
            story.append(PageBreak())
            story.append(
                Paragraph("PLANT-BASED NUTRITION GUIDE", shopping_title_style))
            story.append(Spacer(1, 12))

            nutrition_guide = """
            <para>
            <b>Understanding Plant-Based Protein & Macro Balancing</b><br/><br/>
            Plant-based nutrition presents unique challenges compared to animal-based diets, particularly when it comes to protein intake and macro balancing. Here's what you need to know:<br/><br/>
            <b>Protein Sources in Plant-Based Diets:</b><br/>
            Unlike animal proteins which are "complete" (containing all essential amino acids), most plant proteins are "incomplete" - meaning they're lower in one or more essential amino acids. However, this doesn't mean plant-based diets can't provide adequate protein. The key is variety and strategic combining.<br/><br/>
            <b>The Macro Balancing Challenge:</b><br/>
            Plant-based foods naturally come with protein attached to either carbohydrates or fats, making it harder to achieve precise macro ratios. For example:<br/>
            • Legumes (beans, lentils) provide protein but also significant carbs<br/>
            • Nuts and seeds offer protein but are high in fats<br/>
            • Grains like quinoa provide protein but are primarily carb sources<br/><br/>
            <b>Strategies for Better Macro Control:</b><br/>
            1. Use Protein Isolates: Plant-based protein powders (pea, rice, hemp) provide concentrated protein without the accompanying carbs or fats<br/>
            2. Choose High-Protein Versions: Opt for products like Vetta Protein Pasta (24.9g protein/100g) instead of regular pasta<br/>
            3. Strategic Food Combining: Pair incomplete proteins throughout the day to create complete amino acid profiles<br/>
            4. Focus on Protein-Dense Whole Foods: Tofu, tempeh, seitan, and TVP provide more protein per calorie<br/><br/>
            <b>Why This Matters for Your Goals:</b><br/>
            For cardiovascular improvement and weight loss, getting adequate protein while managing carbs and fats is crucial. Plant-based diets can absolutely meet these needs, but require more planning and awareness of food choices.<br/><br/>
            <b>Tips for Success:</b><br/>
            • Track your macros using apps like MyFitnessPal to understand your actual intake<br/>
            • Prioritize protein at each meal to ensure adequate daily intake<br/>
            • Don't be afraid to use protein powders and fortified products to meet your targets<br/>
            • Remember that variety is key - different plant proteins provide different amino acid profiles
            </para>
            """
            story.append(Paragraph(nutrition_guide, body_style))

        # Build PDF
        doc.build(story)
        print(
            f"Created native PDF file: {full_path} (size: {os.path.getsize(full_path)} bytes)")
        print(f"✅ Successfully created PDF: {filename}")
        print(f"📁 Location: output/meal plans/{filename}")
        return filename

    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        return None


async def main():
    """Main function to generate Marc's meal plan PDF"""
    print("=== MARC POTTER MEAL PLAN PDF GENERATION ===")
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Calculate nutrition targets
    nutrition_data = calculate_nutrition_for_cardiovascular_improvement()
    print("=== MARC'S NUTRITION TARGETS ===")
    print(f"Daily Calories: {nutrition_data['daily_calories']}")
    print(f"Protein: {nutrition_data['macros']['protein']}g")
    print(f"Carbs: {nutrition_data['macros']['carbs']}g")
    print(f"Fats: {nutrition_data['macros']['fats']}g")
    print()

    # Get meal plan text
    meal_plan_text = get_meal_plan_text()

    # Create PDF
    filename = create_meal_plan_pdf(meal_plan_text, MARC_DATA, nutrition_data)

    if filename:
        print()
        print("=== PDF SUMMARY ===")
        print("• Professional meal plan PDF for Marc Potter")
        print("• Includes COCOS PT logo and branding")
        print("• Blue color scheme matching original design")
        print("• Heart-healthy vegan meals for cardiovascular improvement")
        print("• All ingredients available at Australian stores")
        print("• Includes meal photos for visual appeal")
    else:
        print("❌ Failed to create PDF")

if __name__ == "__main__":
    asyncio.run(main())
