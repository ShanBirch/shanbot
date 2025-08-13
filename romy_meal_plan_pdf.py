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

# Romy's data
ROMY_DATA = {
    "personal_info": {
        "full_name": {"value": "Romy Prasad", "confidence": 100},
        "email": {"value": "romikap@gmail.com", "confidence": 100},
        "phone": {"value": "+61 451 953 625", "confidence": 100},
        "birth_date": {"value": "1989-10-24", "confidence": 100},
        "gender": {"value": "Female", "confidence": 100}
    },
    "physical_info": {
        "current_weight": {"value": "58", "confidence": 100},
        "height": {"value": "167", "confidence": 100},
        "primary_fitness_goal": {"value": "Body Recomposition", "confidence": 100},
        "activity_level": {"value": "Moderately active - moderate exercise 6-7 days per week", "confidence": 100}
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
        "training_days": {"value": "Daily", "confidence": 100},
        "workout_time": {"value": "Not specified", "confidence": 50},
        "gym_access": {"value": "At Home Body Weight", "confidence": 100},
        "activities": {"value": "Daily HIIT cycling 30 mins, Tuesdays Zumba 45 mins", "confidence": 100}
    }
}


def calculate_nutrition_for_body_recomposition():
    """Calculate nutrition targets for body recomposition with weight loss (500g/week)"""

    # Romy's stats
    weight_kg = 58
    height_cm = 167
    age = 2025 - 1989  # 36 years old
    gender = "Female"
    activity_level = "Moderately active"

    # Calculate BMR using Mifflin-St Jeor Equation
    if gender == "Male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    # Activity multiplier for "Moderately active"
    activity_multiplier = 1.55

    # Calculate TDEE
    tdee = bmr * activity_multiplier

    # For 500g/week weight loss, create a 500 calorie deficit
    # This allows for fat loss while still providing adequate protein for muscle preservation
    daily_calories = tdee - 500

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
            "deficit": 500,
            "target_weight_loss": "500g/week"
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
    """Get the meal plan text with high-protein vegan meals for body recomposition using cups"""
    meal_times = calculate_meal_times("Not specified")

    return f"""DAY 1 MEAL PLAN

Breakfast ({meal_times['morning_snack']})
Meal: Berry Protein Smoothie Bowl
Ingredients:
- 1/2 cup Frozen Mixed Berries
- 1/2 cup Frozen Banana (sliced)
- 1/4 cup Coles Perform Plant Protein Vanilla
- 3/4 cup Unsweetened Almond Milk
- 1/4 cup Granola
- 2 tbsp Chia Seeds
Preparation: Blend berries, banana, protein powder, and almond milk. Top with granola and chia seeds (5 minutes)
Macros: 420 calories, 45g carbs, 35g protein, 15g fats

Morning Snack ({meal_times['morning_snack']})
Meal: Roasted Chickpea Chips
Ingredients:
- 1/2 cup Brains Chickpea Chips
Preparation: Enjoy as a protein-rich crunchy snack (2 minutes)
Macros: 192 calories, 20g carbs, 7g protein, 9g fats

Lunch ({meal_times['lunch']})
Meal: Spaghetti Bolognese with TVP
Ingredients:
- 1 cup Vetta Protein Pasta (cooked)
- 1/2 cup TVP (Textured Vegetable Protein), dry
- 1 1/2 cups Mixed Vegetables (mushrooms, capsicum, onion)
- 1/2 cup Tomato Passata
- 2 tbsp Nutritional Yeast
- 1 tbsp Olive Oil
- 1/4 cup Fresh Basil (chopped)
- 2 tsp Soy Sauce
Preparation: Cook pasta. Rehydrate TVP with boiling water and soy sauce. Sauté vegetables in olive oil, add TVP and tomato passata. Simmer for 10 minutes. Serve over pasta with nutritional yeast and fresh basil (20 minutes)
Macros: 480 calories, 55g carbs, 35g protein, 18g fats

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: Plant-Based Protein Bar
Ingredients:
- 1 Coles Perform Plant Protein Bar Chocolate Hazelnut
Preparation: Enjoy as a convenient protein boost (1 minute)
Macros: 245 calories, 13g carbs, 11g protein, 12g fats

Dinner ({meal_times['dinner']})
Meal: Vegan Pizza with Roasted Vegetables
Ingredients:
- 1 Cauliflower Pizza Base
- 1/3 cup Vegan Pizza Cheese
- 1 1/4 cups Mixed Roasted Vegetables (capsicum, mushrooms, zucchini)
- 2 tbsp Nutritional Yeast
- 1 tbsp Olive Oil
- 1/4 cup Fresh Basil (chopped)
Preparation: Spread olive oil on pizza base. Top with cheese, roasted vegetables, and nutritional yeast. Bake at 200°C for 12-15 minutes (20 minutes)
Macros: 380 calories, 45g carbs, 22g protein, 16g fats

Daily Totals (Day 1):
Calories: 1717
Protein: 110g
Carbs: 178g
Fats: 70g

DAY 2 MEAL PLAN

Breakfast ({meal_times['morning_snack']})
Meal: Protein Oats with Nuts and Seeds
Ingredients:
- 1/2 cup Rolled Oats
- 1/4 cup Coles Perform Plant Protein Vanilla
- 1/4 cup Mixed Nuts and Seeds
- 3/4 cup Unsweetened Almond Milk
- 1/3 cup Blueberries
Preparation: Cook oats with almond milk and protein powder. Top with nuts, seeds, and blueberries (5 minutes)
Macros: 450 calories, 55g carbs, 32g protein, 18g fats

Morning Snack ({meal_times['morning_snack']})
Meal: Edamame and Fava Protein Mix
Ingredients:
- 1/3 cup Savour Edamame Roasted and Salted
- 1/4 cup Macro Organic Pea & Fava Protein Chunks
Preparation: Mix edamame and protein chunks for a protein-rich snack (2 minutes)
Macros: 220 calories, 8g carbs, 20g protein, 10g fats

Lunch ({meal_times['lunch']})
Meal: Vegan Burger with Sweet Potato Fries
Ingredients:
- 1 Plant-Based Burger Patty
- 1 Whole Grain Burger Bun
- 1/2 cup Mixed Salad Greens
- 1/4 cup Avocado (sliced)
- 1 tbsp Vegan Mayo
- 1 cup Sweet Potato Fries
Preparation: Cook burger patty and sweet potato fries. Assemble burger with greens, avocado, and mayo (15 minutes)
Macros: 520 calories, 65g carbs, 25g protein, 22g fats

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: High Protein Yogurt with Berries
Ingredients:
- 2/3 cup Vitasoy Yogurt
- 1/2 cup Mixed Berries
- 2 tbsp Granola
Preparation: Combine yogurt with berries and granola (3 minutes)
Macros: 280 calories, 35g carbs, 18g protein, 10g fats

Dinner ({meal_times['dinner']})
Meal: Curry Fried Rice with Tofu
Ingredients:
- 1 cup Brown Rice (cooked)
- 1 cup Soyco High Protein Tofu (cubed)
- 1 1/2 cups Mixed Vegetables (capsicum, peas, carrots)
- 2 tbsp Curry Paste
- 1 tbsp Soy Sauce
- 2 tsp Sesame Oil
- 1/4 cup Fresh Coriander (chopped)
Preparation: Cook rice. Stir-fry tofu and vegetables with curry paste and soy sauce. Combine with rice and serve with coriander (20 minutes)
Macros: 420 calories, 55g carbs, 28g protein, 14g fats

Daily Totals (Day 2):
Calories: 1890
Protein: 123g
Carbs: 218g
Fats: 74g

DAY 3 MEAL PLAN

Breakfast ({meal_times['morning_snack']})
Meal: Tofu Scramble with Toast
Ingredients:
- 1 cup Soyco High Protein Tofu (crumbled)
- 2 Slices High Protein Bread
- 1 cup Mixed Vegetables (spinach, capsicum, mushrooms)
- 2 tbsp Nutritional Yeast
- 1 tbsp Olive Oil
- 2 tbsp Mixed Seeds
Preparation: Scramble tofu with vegetables and nutritional yeast. Serve on toasted bread with seeds (10 minutes)
Macros: 380 calories, 35g carbs, 30g protein, 16g fats

Morning Snack ({meal_times['morning_snack']})
Meal: Protein Pudding
Ingredients:
- 1 Fancy Plants High Protein Pud Caramelised Biscuits
Preparation: Enjoy as a protein-rich dessert (1 minute)
Macros: 68 calories, 7g carbs, 10g protein, 2g fats

Lunch ({meal_times['lunch']})
Meal: Burrito Bowl with Quinoa
Ingredients:
- 1/2 cup Quinoa (cooked)
- 1 cup Plant-based Chicken Free Strips
- 1 1/4 cups Mixed Vegetables (capsicum, corn, black beans)
- 2 tbsp Guacamole
- 1 tbsp Vegan Sour Cream
- 1/4 cup Fresh Coriander (chopped)
Preparation: Cook quinoa. Heat chicken strips and vegetables. Assemble bowl with quinoa, chicken, vegetables, guacamole, and sour cream (15 minutes)
Macros: 450 calories, 55g carbs, 32g protein, 18g fats

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: Keep It Cleaner Plant Based Protein Mint Crisp
Ingredients:
- 1 Keep It Cleaner Plant Based Protein Mint Crisp Bar
Preparation: Enjoy as a protein-rich snack (1 minute)
Macros: 243 calories, 10g carbs, 10g protein, 9g fats

Dinner ({meal_times['dinner']})
Meal: Noodle Soup with Tofu and Vegetables
Ingredients:
- 1 cup Rice Noodles
- 1 cup Soyco High Protein Tofu (cubed)
- 1 1/2 cups Mixed Vegetables (bok choy, mushrooms, snow peas)
- 2 tbsp Miso Paste
- 1 tbsp Soy Sauce
- 1 tbsp Fresh Ginger (minced)
- 1/4 cup Spring Onions (chopped)
Preparation: Cook noodles. Simmer miso paste with vegetables and tofu. Add noodles and serve with spring onions (15 minutes)
Macros: 380 calories, 45g carbs, 28g protein, 12g fats

Daily Totals (Day 3):
Calories: 1521
Protein: 110g
Carbs: 152g
Fats: 57g

INGREDIENT SHOPPING LIST

Proteins & Dairy Alternatives:
• Coles Perform Plant Protein Vanilla 455g
• Vitasoy Yogurt 150g
• Soyco High Protein Tofu 350g
• Plant-based Chicken Free Strips 250g
• Vegan Pizza Cheese 200g
• Plant-Based Burger Patty 200g
• Vegan Mayo 375ml
• Vegan Sour Cream 200ml

Pantry & Grains:
• Sanitarium So Good Unsweetened Almond Milk 1L
• Coles Brown Rice 1kg
• Quinoa 500g
• Vetta Protein Pasta 500g
• Rice Noodles 400g
• Coles High Protein Bread 700g
• Whole Grain Burger Buns 6 pack
• Cauliflower Pizza Base 170g
• Kikkoman Soy Sauce 250ml
• Sesame Oil 250ml
• Miso Paste 200g
• Nutritional Yeast 127g
• Granola 300g
• TVP (Textured Vegetable Protein) 200g
• Tomato Passata 700g

Snacks & Protein Products:
• Coles Perform Plant Protein Bar Chocolate Hazelnut 40g
• Brains Chickpea Chips 150g
• Savour Edamame Roasted and Salted Soy Beans 200g
• Macro Organic Pea & Fava Protein Chunks 200g
• Fancy Plants High Protein Pud Caramelised Biscuits 100g
• Keep It Cleaner Plant Based Protein Mint Crisp Bar 40g

Produce & Fresh:
• Frozen Mixed Berries
• Frozen Bananas
• Blueberries (fresh or frozen)
• Mixed Vegetables (capsicum, broccoli, snow peas, mushrooms, zucchini, carrots, peas, corn, black beans, bok choy, spring onions)
• Spinach
• Fresh Coriander
• Fresh Basil
• Fresh Ginger
• Avocado
• Mixed Nuts and Seeds
• Mixed Salad Greens
• Olive Oil"""


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
    """Create PDF for Romy's meal plan - matching original styling"""

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
    """Main function to generate Romy's meal plan PDF"""
    print("=== ROMY PRASAD MEAL PLAN PDF GENERATION ===")
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Calculate nutrition targets
    nutrition_data = calculate_nutrition_for_body_recomposition()
    meal_plan_text = get_meal_plan_text()

    print(f"=== ROMY'S NUTRITION TARGETS ===")
    print(f"Daily Calories: {nutrition_data['daily_calories']}")
    print(f"Protein: {nutrition_data['macros']['protein']}g")
    print(f"Carbs: {nutrition_data['macros']['carbs']}g")
    print(f"Fats: {nutrition_data['macros']['fats']}g")
    print()

    # Create PDF
    pdf_filename = create_meal_plan_pdf(
        meal_plan_text, ROMY_DATA, nutrition_data)

    if pdf_filename:
        print(f"✅ Successfully created PDF: {pdf_filename}")
        print(f"📁 Location: output/meal plans/{pdf_filename}")
        print("\n=== PDF SUMMARY ===")
        print(f"• Professional meal plan PDF for Romy Prasad")
        print(f"• Includes COCOS PT logo and branding")
        print(f"• Blue color scheme matching original design")
        print(f"• High-protein vegan meals for body recomposition")
        print(f"• All ingredients available at Australian stores")
    else:
        print("❌ Failed to create PDF")

if __name__ == "__main__":
    asyncio.run(main())
