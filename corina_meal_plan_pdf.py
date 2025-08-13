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

# Corina's data
CORINA_DATA = {
    "personal_info": {
        "full_name": {"value": "Corina", "confidence": 100},
        "email": {"value": "corina@example.com", "confidence": 100},
        "phone": {"value": "+61 000 000 000", "confidence": 100},
        "birth_date": {"value": "1985-01-01", "confidence": 100},
        "gender": {"value": "Female", "confidence": 100}
    },
    "physical_info": {
        "current_weight": {"value": "75", "confidence": 100},
        "height": {"value": "165", "confidence": 100},
        "primary_fitness_goal": {"value": "Weight Loss", "confidence": 100},
        "activity_level": {"value": "Slightly Active", "confidence": 100}
    },
    "dietary_info": {
        "diet_type": {"value": "Balanced", "confidence": 100},
        "disliked_foods": {"value": "None specified", "confidence": 100},
        "regular_meals": {
            "breakfast": {"value": "Not specified", "confidence": 50},
            "lunch": {"value": "Not specified", "confidence": 50},
            "dinner": {"value": "Not specified", "confidence": 50}
        }
    },
    "training_info": {
        "training_days": {"value": "3 days per week", "confidence": 100},
        "workout_time": {"value": "Not specified", "confidence": 50},
        "gym_access": {"value": "At Home", "confidence": 100},
        "activities": {"value": "Light exercise and walking", "confidence": 100}
    }
}


def calculate_nutrition_for_weight_loss():
    """Calculate nutrition targets for weight loss (500g per week)"""

    # Corina's stats (estimated)
    weight_kg = 75
    height_cm = 165
    age = 2025 - 1985  # 40 years old
    gender = "Female"
    activity_level = "Slightly Active"

    # Calculate BMR using Mifflin-St Jeor Equation
    if gender == "Female":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5

    # Activity multiplier for "Slightly Active"
    activity_multiplier = 1.375

    # Calculate TDEE
    tdee = bmr * activity_multiplier

    # For weight loss of 500g per week, create a 500 calorie deficit
    daily_calories = tdee - 500

    # Macro breakdown for weight loss
    # Higher protein to preserve muscle, moderate carbs, healthy fats
    protein_percentage = 0.35  # 35% protein
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
            "deficit": 500,
            "target_weight_loss": "500g per week"
        }
    }


def calculate_meal_times(workout_time="Not specified"):
    """Calculate meal times based on workout schedule"""

    if workout_time == "Not specified":
        return {
            "breakfast": "7:30 AM",
            "morning_snack": "10:00 AM",
            "lunch": "12:30 PM",
            "afternoon_snack": "3:00 PM",
            "dinner": "7:00 PM"
        }
    else:
        return {
            "breakfast": "7:30 AM",
            "morning_snack": "10:00 AM",
            "lunch": "12:30 PM",
            "afternoon_snack": "3:00 PM",
            "dinner": "7:00 PM"
        }


def get_meal_plan_text():
    """Get the meal plan text for Corina's weight loss plan"""
    meal_times = calculate_meal_times("Not specified")

    return f"""DAY 1 MEAL PLAN

Breakfast ({meal_times['breakfast']})
Meal: Protein-Rich Oatmeal Bowl
Ingredients:
- 1 small handful rolled oats (or muesli if preferred, check sugar content)
- 1/2 cup plain Greek yogurt (high in protein)
- 1 handful mixed berries (fresh or frozen)
- Water or unsweetened almond milk for cooking
Preparation: Cook oats with water or almond milk until creamy. Top with Greek yogurt and mixed berries (5 minutes)
Macros: 285 calories, 18g protein, 35g carbs, 8g fats

Lunch ({meal_times['lunch']})
Meal: Chicken and Salad
Ingredients:
- 1 palm-sized piece of cooked chicken breast (shredded or diced)
- 2 cups mixed salad greens (spinach, lettuce, rocket)
- 1/2 cup chopped cucumber and cherry tomatoes
- 1-2 tablespoons light vinaigrette dressing or lemon juice and olive oil
- 1 small handful of seeds (pumpkin or sunflower) for healthy fats
Preparation: Combine all ingredients in a bowl. Dress with vinaigrette or lemon juice and olive oil (8 minutes)
Macros: 320 calories, 35g protein, 12g carbs, 15g fats

Dinner ({meal_times['dinner']})
Meal: Salmon and Green Veggies
Ingredients:
- 1 palm-sized fillet of baked or grilled salmon
- 1.5 cups steamed or roasted green vegetables (broccoli, green beans, asparagus)
- Small drizzle of olive oil and a squeeze of lemon juice
Preparation: Bake or grill salmon. Steam or roast green vegetables. Drizzle with olive oil and lemon juice (20 minutes)
Macros: 385 calories, 42g protein, 15g carbs, 18g fats

Daily Totals (Day 1):
Calories: 990
Protein: 95g
Carbs: 62g
Fats: 41g

DAY 2 MEAL PLAN

Breakfast ({meal_times['breakfast']})
Meal: Greek Yogurt and Berries
Ingredients:
- 1/2 cup plain Greek yogurt
- 1 handful mixed berries
- 1 small handful of muesli or oats (check sugar content)
Preparation: Combine Greek yogurt with berries and muesli/oats in a bowl (3 minutes)
Macros: 245 calories, 16g protein, 25g carbs, 8g fats

Lunch ({meal_times['lunch']})
Meal: Asian Inspired Chicken and Veggies
Ingredients:
- 1 palm-sized piece of cooked chicken (stir-fried or baked)
- 1.5 cups mixed stir-fry vegetables (capsicum, snow peas, bok choy, mushrooms)
- 1-2 tablespoons low-sodium soy sauce or tamari, mixed with grated ginger and garlic
- Optional: 1/2 cup cooked brown rice (small portion for carbohydrate)
Preparation: Stir-fry chicken and vegetables with soy sauce, ginger, and garlic. Serve with optional brown rice (15 minutes)
Macros: 365 calories, 38g protein, 25g carbs, 12g fats

Dinner ({meal_times['dinner']})
Meal: Steak and Veggies
Ingredients:
- 1 palm-sized portion of lean steak (sirloin or flank) grilled or pan-fried
- 1.5 cups roasted root vegetables (sweet potato and carrots, cut into small pieces)
- Handful of steamed green beans
- Small drizzle of olive oil
Preparation: Grill or pan-fry steak. Roast root vegetables and steam green beans. Drizzle with olive oil (25 minutes)
Macros: 425 calories, 45g protein, 35g carbs, 15g fats

Daily Totals (Day 2):
Calories: 1035
Protein: 99g
Carbs: 85g
Fats: 35g

DAY 3 MEAL PLAN

Breakfast ({meal_times['breakfast']})
Meal: Oatmeal with Greek Yogurt
Ingredients:
- 1 small handful rolled oats (or muesli) cooked with water or unsweetened almond milk
- 1/2 cup plain Greek yogurt
- 1 handful sliced banana or berries
Preparation: Cook oats with water or almond milk until creamy. Top with Greek yogurt and sliced banana or berries (5 minutes)
Macros: 265 calories, 17g protein, 30g carbs, 8g fats

Lunch ({meal_times['lunch']})
Meal: Tuna Salad (Lightened Up)
Ingredients:
- 1 small can tuna in springwater, drained
- 1 tablespoon light mayonnaise or Greek yogurt
- Chopped celery and onion
- 2 cups mixed green salad or 2-3 lettuce cups
Preparation: Mix tuna with mayonnaise or Greek yogurt and chopped vegetables. Serve with mixed green salad or in lettuce cups (8 minutes)
Macros: 285 calories, 32g protein, 8g carbs, 12g fats

Dinner ({meal_times['dinner']})
Meal: Prawns and Veggie Pad Thai (Lightened Version)
Ingredients:
- 1 handful of cooked prawns
- 2 cups of spiralized zucchini or carrot "noodles" (instead of traditional noodles)
- 1 cup mixed stir-fry vegetables (bean sprouts, capsicum, spring onion)
- 1-2 tablespoons light soy sauce, squeeze of lime juice, pinch of chili flakes (optional)
- Optional: 1 tablespoon crushed peanuts for crunch and healthy fats
Preparation: Stir-fry prawns and vegetables with soy sauce, lime juice, and chili flakes. Serve with spiralized vegetable noodles (15 minutes)
Macros: 345 calories, 38g protein, 25g carbs, 12g fats

Daily Totals (Day 3):
Calories: 895
Protein: 87g
Carbs: 63g
Fats: 32g

INGREDIENT SHOPPING LIST

Proteins & Dairy:
• Woolworths Macro Greek Yogurt Natural 500g
• Coles Chicken Breast Fillets 1kg
• Woolworths Fresh Atlantic Salmon Fillets 400g
• Coles Lean Beef Steak 500g
• Coles Tuna in Springwater 185g
• Coles Cooked Prawns 500g
• Coles Cottage Cheese 250g
• Coles Cheddar Cheese 250g

Pantry & Grains:
• Coles Rolled Oats 900g
• Woolworths Muesli 500g (check sugar content)
• Coles Brown Rice 1kg
• Coles Olive Oil 500ml
• Kikkoman Soy Sauce 250ml
• Coles Light Mayonnaise 375ml
• Coles Mixed Seeds 200g
• Coles Pumpkin Seeds 200g
• Coles Sunflower Seeds 200g
• Coles Mixed Nuts 200g
• Coles Walnuts 200g
• Coles Hummus 250g
• Coles Tzatziki 250g
• Coles Air-Popped Popcorn 100g

Produce & Fresh:
• Mixed Berries (fresh or frozen)
• Bananas
• Mixed Salad Greens
• Cucumber
• Cherry Tomatoes
• Broccoli
• Green Beans
• Asparagus
• Capsicum
• Snow Peas
• Bok Choy
• Mushrooms
• Sweet Potato
• Carrots
• Zucchini
• Bean Sprouts
• Spring Onion
• Celery
• Onion
• Garlic
• Ginger
• Lemon
• Lime
• Baby Carrots
• Grapes
• Apples"""


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
            if line.startswith('Breakfast') or line.startswith('Lunch') or line.startswith('Dinner'):
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
    """Create PDF for Corina's meal plan - matching original styling"""

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
            "Lunch",
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
    """Main function to generate Corina's meal plan PDF"""
    print("=== CORINA MEAL PLAN PDF GENERATION ===")
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Calculate nutrition targets
    nutrition_data = calculate_nutrition_for_weight_loss()
    meal_plan_text = get_meal_plan_text()

    print(f"=== CORINA'S NUTRITION TARGETS ===")
    print(f"Daily Calories: {nutrition_data['daily_calories']}")
    print(f"Protein: {nutrition_data['macros']['protein']}g")
    print(f"Carbs: {nutrition_data['macros']['carbs']}g")
    print(f"Fats: {nutrition_data['macros']['fats']}g")
    print()

    # Create PDF
    pdf_filename = create_meal_plan_pdf(
        meal_plan_text, CORINA_DATA, nutrition_data)

    if pdf_filename:
        print(f"✅ Successfully created PDF: {pdf_filename}")
        print(f"📁 Location: output/meal plans/{pdf_filename}")
        print("\n=== PDF SUMMARY ===")
        print(f"• Professional meal plan PDF for Corina")
        print(f"• Includes COCOS PT logo and branding")
        print(f"• Blue color scheme matching original design")
        print(f"• Weight loss focused meals with portion control")
        print(f"• All ingredients available at Australian stores")
        print(f"• Uses cup and handful measurements for ease")
    else:
        print("❌ Failed to create PDF")

if __name__ == "__main__":
    asyncio.run(main())
