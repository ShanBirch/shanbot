#!/usr/bin/env python3
"""
Linda Hayes – 7-Day Vegan Meal Plan (PRO Layout)
- PRO header with logo, client info, daily targets
- 7-day rotation: repeat lunches Mon–Wed and Thu–Sat, Sunday: no breakfast, early lunch + cheat dinner
- Clickable Woolworths shopping list (bot-safe)
- Iron/B12/Omega-3 emphasis per client notes
"""

import os
from datetime import datetime, date
import argparse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import re

# Removed hardcoded client data and meal rotations
from client_configs import (
    LINDA_CLIENT_DATA,
    LINDA_LUNCHES_MON_WED,
    LINDA_LUNCHES_THU_SAT,
    LINDA_DINNERS_ROT
)
from utils import calculate_age, calculate_targets_by_sex

LOGO_PATH = r"C:\\Users\\Shannon\\OneDrive\\Documents\\cocos logo.png"
OUTPUT_DIR = "meal plans"


def calculate_meal_times():
    return {
        'breakfast': '7:30 AM',
        'lunch': '12:30 PM',
        'snack': '3:00 PM',
        'dinner': '7:00 PM',
    }


def get_meal_plan_text(client_data: dict, week: int = 1):
    name = client_data["name"]
    dob = client_data["dob"]
    sex = client_data["sex"]
    weight_kg = client_data["weight_kg"]
    height_cm = client_data["height_cm"]
    activity_factor = client_data["activity_factor"]
    goal_description = client_data["goal_description"]
    dietary_type = client_data["dietary_type"]

    age = calculate_age(dob)
    target_cal, target_protein, target_carbs, target_fats = calculate_targets_by_sex(
        sex, weight_kg, height_cm, age, activity_factor, 500)

    times = calculate_meal_times()

    wk = int(week)

    # Use client-specific meal rotations
    # This part will need to be made more dynamic if different clients have different meal sets
    # For now, assumes Linda's structure or a similar one for other clients
    lunches_mon_wed = LINDA_LUNCHES_MON_WED  # Placeholder, will be dynamic
    lunches_thu_sat = LINDA_LUNCHES_THU_SAT  # Placeholder, will be dynamic
    dinners_rot = LINDA_DINNERS_ROT  # Placeholder, will be dynamic

    lunch1 = lunches_mon_wed.get(wk, lunches_mon_wed[1])
    lunch2 = lunches_thu_sat.get(wk, lunches_thu_sat[1])
    dinners = dinners_rot.get(wk, dinners_rot[1])

    return f"""WEEK {wk} - DAY 1 MEAL PLAN

Breakfast ({times['breakfast']})
Meal: Protein Oats with Berries, Chia & Hemp
Ingredients:
- 45g Rolled Oats
- 250ml Unsweetened Soy Milk (B12-fortified)
- 15g Chia Seeds
- 10g Hemp Seeds
- 80g Mixed Berries
Preparation: Cook oats with soy milk until creamy. Stir in chia and hemp, top with berries (8 minutes)
Macros: 340 calories, 44g carbs, 18g protein, 11g fats

Lunch ({times['lunch']})
Meal: {lunch1[0]}
Ingredients:
{lunch1[1]}
Preparation: {lunch1[2]}
{lunch1[3]}

Afternoon Snack ({times['snack']})
Meal: Soy Yogurt + Berries + Flax
Ingredients:
- 160g High-Protein Soy Yogurt (fortified)
- 60g Mixed Berries
- 10g Ground Flaxseed (omega-3 ALA)
Preparation: Combine and enjoy (2 minutes)
Macros: 200 calories, 22g carbs, 13g protein, 7g fats

Dinner ({times['dinner']})
Meal: {dinners[0][0]}
Ingredients:
{dinners[0][1]}
Preparation: {dinners[0][2]}
{dinners[0][3]}

Daily Totals (Day 1):
Calories: {target_cal}
Protein: ~{target_protein}g
Carbs: ~{target_carbs}g
Fats: ~{target_fats}g

WEEK {wk} - DAY 2 MEAL PLAN

Breakfast ({times['breakfast']})
Meal: Tofu Scramble on Wholegrain Toast
Ingredients:
- 180g Firm Tofu, crumbled
- 60g Spinach
- 60g Tomato, diced
- 1/4 tsp Turmeric, pinch Black Pepper
- 1 Slice Wholegrain High-Protein Bread
- 5g Nutritional Yeast
Preparation: Scramble tofu with spices and veg (non-stick); serve on toast, sprinkle nutritional yeast (10 minutes)
Macros: 360 calories, 28g carbs, 30g protein, 12g fats

Lunch ({times['lunch']})
Meal: {lunch1[0].replace('(Mon–Wed batch)', '(Leftover batch)')}
Ingredients:
- 1 portion from Mon batch (see Day 1)
Preparation: Reheat gently; add splash of water if needed (5 minutes)
{lunch1[3]}

Afternoon Snack ({times['snack']})
Meal: Apple & Almond Butter + Protein Shake
Ingredients:
- 1 Medium Apple (~180g), sliced
- 12g Almond Butter
- 20g Plant Protein Powder (pea/rice), mixed with cold water
Preparation: Slice apple, spread nut butter; shake protein with water (3 minutes)
Macros: 260 calories, 28g carbs, 22g protein, 10g fats

Dinner ({times['dinner']})
Meal: {dinners[1][0]}
Ingredients:
{dinners[1][1]}
Preparation: {dinners[1][2]}
{dinners[1][3]}

Daily Totals (Day 2):
Calories: {target_cal}
Protein: ~{target_protein}g
Carbs: ~{target_carbs}g
Fats: ~{target_fats}g

WEEK {wk} - DAY 3 MEAL PLAN

Breakfast ({times['breakfast']})
Meal: Protein Oats with Berries, Chia & Hemp
Ingredients: (same as Day 1)
Preparation: (8 minutes)
Macros: 340 calories, 44g carbs, 18g protein, 11g fats

Lunch ({times['lunch']})
Meal: {lunch1[0].replace('(Mon–Wed batch)', '(Leftover batch)')}
Ingredients: (same as Day 1)
Preparation: (5 minutes)
{lunch1[3]}

Afternoon Snack ({times['snack']})
Meal: Soy Yogurt + Berries + Flax
Ingredients: (same as Day 1)
Preparation: (2 minutes)
Macros: 200 calories, 22g carbs, 13g protein, 7g fats

Dinner ({times['dinner']})
Meal: {dinners[2][0]}
Ingredients:
{dinners[2][1]}
Preparation: {dinners[2][2]}
{dinners[2][3]}

Daily Totals (Day 3):
Calories: {target_cal}
Protein: ~{target_protein}g
Carbs: ~{target_carbs}g
Fats: ~{target_fats}g

WEEK {wk} - DAY 4 MEAL PLAN

Breakfast ({times['breakfast']})
Meal: Tofu Scramble on Wholegrain Toast
Ingredients: (same as Day 2)
Preparation: (10 minutes)
Macros: 360 calories, 28g carbs, 30g protein, 12g fats

Lunch ({times['lunch']})
Meal: {lunch2[0]}
Ingredients:
{lunch2[1]}
Preparation: {lunch2[2]}
{lunch2[3]}

Afternoon Snack ({times['snack']})
Meal: Apple & Almond Butter + Protein Shake
Ingredients: (same as Day 2)
Preparation: (3 minutes)
Macros: 260 calories, 28g carbs, 22g protein, 10g fats

Dinner ({times['dinner']})
Meal: Hearty Lentil & Veg Soup with Toast
Ingredients:
- 250g Mixed Soup Veg (celery, carrot, onion, tomato)
- 160g Cooked Red Lentils
- 400ml Veg Stock
- Herbs & Pepper
- 1 Slice Wholegrain Bread (toasted)
Preparation: Simmer veg with stock and lentils 12–15 min; serve with toast (15 minutes)
Macros: 380 calories, 54g carbs, 24g protein, 7g fats

Daily Totals (Day 4):
Calories: {target_cal}
Protein: ~{target_protein}g
Carbs: ~{target_carbs}g
Fats: ~{target_fats}g

WEEK {wk} - DAY 5 MEAL PLAN

Breakfast ({times['breakfast']})
Meal: Protein Oats with Berries, Chia & Hemp
Ingredients: (same as Day 1)
Preparation: (8 minutes)
Macros: 340 calories, 44g carbs, 18g protein, 11g fats

Lunch ({times['lunch']})
Meal: {lunch2[0].replace('(Thu–Sat batch)', '(Leftover batch)')}
Ingredients: (same as Day 4)
Preparation: (5 minutes)
{lunch2[3]}

Afternoon Snack ({times['snack']})
Meal: Soy Yogurt + Berries + Flax
Ingredients: (same as Day 1)
Preparation: (2 minutes)
Macros: 200 calories, 22g carbs, 13g protein, 7g fats

Dinner ({times['dinner']})
Meal: Cauliflower-Base Vegan Pizza (Veg + Vegan Cheese)
Ingredients:
- 1 Cauliflower Pizza Base
- 35g Vegan Pizza Cheese
- 120g Mushrooms, sliced
- 80g Capsicum, sliced
- 2 tbsp Tomato Paste
Preparation: Assemble and bake at 200°C for 10–12 minutes (12 minutes)
Macros: 420 calories, 48g carbs, 17g protein, 16g fats

Daily Totals (Day 5):
Calories: {target_cal}
Protein: ~{target_protein}g
Carbs: ~{target_carbs}g
Fats: ~{target_fats}g

WEEK {wk} - DAY 6 MEAL PLAN

Breakfast ({times['breakfast']})
Meal: Tofu Scramble on Wholegrain Toast
Ingredients: (same as Day 2)
Preparation: (10 minutes)
Macros: 360 calories, 28g carbs, 30g protein, 12g fats

Lunch ({times['lunch']})
Meal: {lunch2[0].replace('(Thu–Sat batch)', '(Leftover batch)')}
Ingredients: (same as Day 4)
Preparation: (5 minutes)
{lunch2[3]}

Afternoon Snack ({times['snack']})
Meal: Apple & Almond Butter + Protein Shake
Ingredients: (same as Day 2)
Preparation: (3 minutes)
Macros: 260 calories, 28g carbs, 22g protein, 10g fats

Dinner ({times['dinner']})
Meal: TVP Tacos (2 shells) with Black Beans & Avocado
Ingredients: (same as Day 2)
Preparation: (12 minutes)
Macros: 410 calories, 44g carbs, 30g protein, 12g fats

Daily Totals (Day 6):
Calories: {target_cal}
Protein: ~{target_protein}g
Carbs: ~{target_carbs}g
Fats: ~{target_fats}g

WEEK {wk} - DAY 7 MEAL PLAN

Breakfast
Meal: —
Ingredients: —
Preparation: Sunday reset – no breakfast today.
Macros: —

Lunch (12:00 PM – early lunch)
Meal: Vegan Protein Pancakes with Berries
Ingredients:
- 60g Rolled Oats (blended into flour)
- 200ml Unsweetened Soy Milk
- 1 tsp Baking Powder
- 1/2 Banana (mashed) or 60g Apple Puree
- 20g Plant Protein Powder (optional)
- 80g Mixed Berries
- 5ml Maple Syrup
Preparation: Blend oats to flour, whisk with soy milk, baking powder and banana. Cook pancakes on a non-stick pan; top with berries and drizzle maple (12 minutes)
Macros: 480 calories, 62g carbs, 22g protein, 12g fats

Dinner (Cheat Meal)
Meal: Flexible Choice within Guidelines
Guidelines:
- Add a protein (tofu/tempeh/beans) and plenty of veg
- Favour baked/grilled over deep-fried
- Pause at comfortable fullness; hydrate well
- Enjoy mindfully – back on plan tomorrow
Macros: Flexible

INGREDIENT SHOPPING LIST – WEEK {wk}

Proteins & Alternatives:
• Firm Tofu 1kg
• Tempeh 300g
• TVP (Textured Vegetable Protein) 300g
• High-Protein Soy Yogurt 4 x 160g
• Plant Protein Powder 500g
• Nutritional Yeast 125g (B12-fortified)

Pantry & Grains:
• Unsweetened Soy Milk 3L (B12-fortified)
• Brown Rice 1kg
• Quinoa 1kg (or Buckwheat 1kg)
• Vetta SMART Protein Pasta 500g
• Cauliflower Pizza Base x2
• Taco Shells (Hard) x1 pack
• Passata 700ml
• Korma Simmer Sauce 375g (low sugar)
• Light Coconut Milk 400ml
• Tahini 385g
• Peanut Butter 375g
• Ground Flaxseed 300g
• Chia Seeds 300g
• Hemp Seeds 200g
• Mixed Nuts 300g
• Olive Oil 250ml
• Soy Sauce 250ml
• Sesame Oil 100ml
• Marinara Sauce 500ml
• Thai Red Curry Paste 200g
• Vanilla Extract 50ml
• Lime Juice 250ml

Legumes & Canned:
• Chickpeas (No Added Salt) 4 x 420g
• Black Beans 2 x 400g
• Red Lentils 500g (dry)

Produce & Fresh/Frozen:
• Mixed Berries 1kg (frozen)
• Apples 1.2kg
• Spinach 600g
• Mushrooms 500g
• Capsicum 4
• Onions 1kg
• Tomatoes 6
• Broccoli 2 heads
• Carrots 1kg
• Lettuce 1
• Lemon/Lime 4
• Sauerkraut 500g (optional)

Supplements (optional):
• Algal Oil (DHA/EPA omega-3)
• B12 Supplement (methylcobalamin or cyanocobalamin)
"""


def extract_day_meals(text: str, day_type: str) -> dict:
    meals = {}
    lines = text.split('\n')
    current_day = None
    current_meal = None
    current_content = []
    for raw in lines:
        l = raw.strip()
        if not l:
            continue
        # Generic week header matcher (works for WEEK 1..6)
        if l.startswith('WEEK ') and ' - DAY ' in l and day_type in l:
            current_day = day_type
            current_meal = None
            current_content = []
            continue
        if l.startswith('WEEK ') and ' - DAY ' in l and day_type not in l:
            if current_day == day_type and current_meal and current_content:
                meals[current_meal] = '\n'.join(current_content).strip()
            current_day = None
            current_meal = None
            current_content = []
            continue
        if current_day == day_type:
            if l.startswith('Breakfast') or l.startswith('Lunch') or l.startswith('Afternoon Snack') or l.startswith('Dinner'):
                if current_meal and current_content:
                    meals[current_meal] = '\n'.join(current_content).strip()
                current_meal = l.split('(')[0].strip()
                current_content = []
            elif l.startswith('INGREDIENT SHOPPING LIST') or l.startswith('NUTRITIONAL'):
                if current_meal and current_content:
                    meals[current_meal] = '\n'.join(current_content).strip()
                break
            elif current_meal:
                current_content.append(l)
    if current_day == day_type and current_meal and current_content:
        meals[current_meal] = '\n'.join(current_content).strip()
    return meals


def format_meal_content(content: str) -> str:
    if not content:
        return ""
    lines = content.split('\n')
    formatted = []
    for l in lines:
        l = l.strip()
        if l.startswith('Calculation:'):
            continue
        # Drop any embedded totals from the source text to avoid duplicates
        if l.startswith('Daily Totals') or l.startswith('Calories:') or l.startswith('Protein:') or l.startswith('Carbs:') or l.startswith('Fats:'):
            continue
        if l.startswith('Meal:') or l.startswith('Ingredients:') or l.startswith('Preparation:') or l.startswith('Macros:') or l.startswith('Guidelines:'):
            formatted.append(f"<b>{l}</b>")
        elif l.startswith('- '):
            formatted.append(f"  {l}")
        else:
            formatted.append(l)
    return '<br/>'.join(formatted)


def link_for(item_name: str) -> str:
    product_links = {
        'Firm Tofu 1kg': 'https://www.woolworths.com.au/shop/search/products?searchTerm=soyco%20firm%20tofu',
        'Tempeh 300g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=tempeh',
        'TVP (Textured Vegetable Protein) 300g': 'https://www.woolworths.com.au/shop/productdetails/173289/macro-textured-vegetable-protein',
        'High-Protein Soy Yogurt 4 x 160g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=soy%20protein%20yogurt',
        'Plant Protein Powder 500g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=plant%20protein%20powder',
        'Nutritional Yeast 125g (B12-fortified)': 'https://www.woolworths.com.au/shop/search/products?searchTerm=nutritional%20yeast',
        'Unsweetened Soy Milk 3L (B12-fortified)': 'https://www.woolworths.com.au/shop/search/products?searchTerm=unsweetened%20soy%20milk',
        'Brown Rice 1kg': 'https://www.woolworths.com.au/shop/search/products?searchTerm=brown%20rice%201kg',
        'Quinoa 1kg (or Buckwheat 1kg)': 'https://www.woolworths.com.au/shop/search/products?searchTerm=quinoa%201kg',
        'Vetta SMART Protein Pasta 500g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=vetta%20protein%20pasta',
        'Cauliflower Pizza Base x2': 'https://www.woolworths.com.au/shop/search/products?searchTerm=cauliflower%20pizza%20base',
        'Taco Shells (Hard) x1 pack': 'https://www.woolworths.com.au/shop/search/products?searchTerm=hard%20taco%20shells',
        'Passata 700ml': 'https://www.woolworths.com.au/shop/search/products?searchTerm=passata',
        'Korma Simmer Sauce 375g (low sugar)': 'https://www.woolworths.com.au/shop/search/products?searchTerm=korma%20simmer%20sauce',
        'Light Coconut Milk 400ml': 'https://www.woolworths.com.au/shop/search/products?searchTerm=light%20coconut%20milk',
        'Tahini 385g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=mayver%27s%20tahini',
        'Peanut Butter 375g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=peanut%20butter',
        'Ground Flaxseed 300g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=ground%20linseed%20flaxseed',
        'Chia Seeds 300g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=chia%20seeds',
        'Hemp Seeds 200g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=hemp%20seeds',
        'Mixed Nuts 300g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=mixed%20nuts%20300g',
        'Olive Oil 250ml': 'https://www.woolworths.com.au/shop/search/products?searchTerm=olive%20oil',
        'Soy Sauce 250ml': 'https://www.woolworths.com.au/shop/search/products?searchTerm=soy%20sauce',
        'Sesame Oil 100ml': 'https://www.woolworths.com.au/shop/search/products?searchTerm=sesame%20oil',
        'Marinara Sauce 500ml': 'https://www.woolworths.com.au/shop/search/products?searchTerm=marinara%20sauce',
        'Thai Red Curry Paste 200g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=thai%20red%20curry%20paste',
        'Vanilla Extract 50ml': 'https://www.woolworths.com.au/shop/search/products?searchTerm=vanilla%20extract',
        'Lime Juice 250ml': 'https://www.woolworths.com.au/shop/search/products?searchTerm=lime%20juice',
    }
    if item_name in product_links:
        return product_links[item_name]
    return f"https://www.woolworths.com.au/shop/search/products?searchTerm={item_name.replace(' ', '%20')}"


def parse_meal_macros(content: str):
    """Extract calories, protein, carbs, fats from a meal content block.
    Returns (calories, protein_g, carbs_g, fats_g). Zeros if not found.
    """
    if not content:
        return 0, 0, 0, 0
    target = None
    for ln in content.split('\n'):
        if ln.strip().lower().startswith('macros:'):
            target = ln.lower()
            break
    if target is None:
        target = content.lower()

    def find_num(pattern: str) -> int:
        m = re.search(pattern, target)
        return int(m.group(1)) if m else 0
    calories = find_num(r"(\d+)\s*calories")
    protein_g = find_num(r"(\d+)\s*g\s*protein")
    carbs_g = find_num(r"(\d+)\s*g\s*carbs")
    fats_g = find_num(r"(\d+)\s*g\s*fats")
    return calories, protein_g, carbs_g, fats_g


def create_pdf(client_data: dict, week: int = 1):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    current_date = datetime.now().strftime("%Y%m%d")

    client_name = client_data["name"].replace(" ", "")
    filename = os.path.join(
        OUTPUT_DIR, f"{client_name}_Week{week}_Meal_Plan_{current_date}_PRO.pdf")

    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=72,
                            leftMargin=72, topMargin=72, bottomMargin=18)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title', parent=styles['Heading1'], fontSize=24, alignment=1, spaceAfter=30, textColor=colors.HexColor('#0B3D91'))
    day_title_style = ParagraphStyle(
        'DayTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0B3D91'), spaceAfter=14)
    meal_title_style = ParagraphStyle('MealTitle', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor(
        '#0B3D91'), spaceBefore=10, spaceAfter=6)
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'], fontSize=11, leading=16)
    info_style = ParagraphStyle(
        'Info', parent=styles['Normal'], alignment=1, fontSize=12, spaceAfter=6)
    shopping_title_style = ParagraphStyle(
        'ShoppingTitle', parent=styles['Heading1'], fontSize=18, alignment=1, textColor=colors.HexColor('#0B3D91'), spaceAfter=12)
    shopping_category_style = ParagraphStyle(
        'ShoppingCategory', parent=styles['Heading2'], fontSize=14, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor('#0B3D91'))
    shopping_item_style = ParagraphStyle('ShoppingItem', parent=styles['Normal'], fontSize=11, leftIndent=20, leading=14, textColor=colors.HexColor(
        '#0066CC'), underline=True, spaceBefore=3, spaceAfter=3)
    note_style = ParagraphStyle('Note', parent=body_style, fontSize=10,
                                alignment=1, textColor=colors.HexColor('#666666'), spaceAfter=15)

    story = []

    # Cover
    if os.path.exists(LOGO_PATH):
        story.append(Image(LOGO_PATH, width=2*inch, height=2*inch))
    story.append(Spacer(1, 30))
    story.append(Paragraph("MEAL PLAN", title_style))

    client_info = f"""
    <para alignment="center">
    <b>Client:</b> {client_data["name"]}<br/>
    <b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}<br/>
    <b>Goal:</b> {client_data["goal_description"]}
    </para>
    """
    story.append(Paragraph(client_info, info_style))

    # Targets
    age = calculate_age(client_data["dob"])
    cal, p, c, f = calculate_targets_by_sex(
        client_data["sex"], client_data["weight_kg"], client_data["height_cm"], age, client_data["activity_factor"], 500)

    targets = f"""
    <para alignment="center" bgcolor="#F5F5F5">
    <b>Daily Targets</b><br/>
    Calories: {cal}<br/>
    Protein: ~{p}g<br/>
    Carbs: ~{c}g<br/>
    Fats: ~{f}g
    </para>
    """
    story.append(Paragraph(targets, info_style))

    # Content
    content = get_meal_plan_text(client_data=client_data, week=week)

    # Days 1–7
    for i in range(1, 8):
        day = f"DAY {i}"
        story.append(PageBreak())
        story.append(
            Paragraph(f"WEEK {wk} - {day} MEAL PLAN", day_title_style))
        meals = extract_day_meals(content, day)
        # Keep order
        day_cals = day_pro = day_carbs = day_fats = 0
        for label in ("Breakfast", "Lunch", "Afternoon Snack", "Dinner"):
            if label in meals:
                # accumulate macros
                cal, pro, carbs, fats = parse_meal_macros(meals[label])
                day_cals += cal
                day_pro += pro
                day_carbs += carbs
                day_fats += fats
                story.append(KeepTogether([
                    Paragraph(label, meal_title_style),
                    Paragraph(format_meal_content(meals[label]), body_style)
                ]))
        # Show recalculated totals for the day
        story.append(Spacer(1, 6))
        totals_str = f"<b>Daily Totals:</b> Calories: {day_cals}  •  Protein: {day_pro}g  •  Carbs: {day_carbs}g  •  Fats: {day_fats}g"
        story.append(Paragraph(totals_str, body_style))

    # Shopping List
    story.append(PageBreak())
    story.append(Paragraph("INGREDIENT SHOPPING LIST", shopping_title_style))
    story.append(Paragraph(
        "💡 <b>Tip:</b> Items below are clickable to help you shop online.", note_style))

    lines = content.split('\n')
    shopping = []
    in_list = False
    for ln in lines:
        t = ln.strip()
        if t.startswith('INGREDIENT SHOPPING LIST'):
            in_list = True
            continue
        if in_list and t.startswith('Supplements'):
            # include supplements too; keep flowing
            shopping.append(ln)
            continue
        if in_list and t == '':
            shopping.append(ln)
            continue
        if in_list and not t:
            shopping.append(ln)
            continue
        if in_list and not t.startswith('•') and not t.endswith(':') and t:
            # reached non-list content; stop (safety)
            break
        if in_list:
            shopping.append(ln)

    current_category = None
    seen = set()
    for raw in shopping:
        s = raw.strip()
        if not s:
            continue
        if s.endswith(':') and ('Proteins' in s or 'Pantry' in s or 'Produce' in s or 'Legumes' in s or 'Supplements' in s):
            current_category = s
            story.append(Paragraph(current_category, shopping_category_style))
            continue
        if s.startswith('•'):
            item = s[1:].strip()
            # Consolidate nuts
            if item in ('Walnuts 300g', 'Almonds 300g'):
                item = 'Mixed Nuts 300g'
            if item in seen:
                continue
            seen.add(item)
            story.append(Paragraph(
                f"<link href=\"{link_for(item)}\"><u>{item}</u></link>", shopping_item_style))

    # Nutrition Guide (expanded – matches PRO quality)
    story.append(PageBreak())
    story.append(
        Paragraph("PLANT-BASED NUTRITION GUIDE", shopping_title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Understanding Plant-Based Protein & Macro Balancing", meal_title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Most plant proteins come bundled with either carbohydrates (legumes, grains) or fats (nuts, seeds). Hitting targets is 100% doable – it just needs smart choices:", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Protein Sources", meal_title_style))
    story.append(Paragraph("Focus on protein-dense options first: tofu, tempeh, seitan, TVP/soy mince, high-protein pasta, and fortified soy yogurt. Use a clean plant protein powder when convenient.", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Macro Control", meal_title_style))
    story.append(Paragraph("• Use protein isolates (powders) for grams without extra carbs/fats.<br/>• Choose high-protein product swaps (e.g., protein pasta vs standard).<br/>• Combine foods across the day to cover amino acids (grains + legumes).", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Iron (non-heme)", meal_title_style))
    story.append(Paragraph("Prioritise chickpeas, lentils, beans, tofu/tempeh, spinach and pumpkin seeds. Add vitamin C at meals (capsicum, lemon, berries) to boost absorption. Avoid tea/coffee 60 minutes around iron-rich meals.", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Vitamin B12", meal_title_style))
    story.append(Paragraph(
        "Use fortified foods (soy milk, nutritional yeast) and a reliable B12 supplement (weekly or daily) to maintain levels.", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Omega-3 Strategy", meal_title_style))
    story.append(Paragraph(
        "Daily ALA from flax, chia and hemp. For direct DHA/EPA, add an algal oil supplement (vegan). This supports brain, mood and endurance.", body_style))

    doc.build(story)
    print(f"✅ {client_data['name']} Week {week} PRO PDF created: {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", type=int, default=1)
    args = parser.parse_args()

    # For testing, you can temporarily use Linda's data
    from client_configs import LINDA_CLIENT_DATA
    create_pdf(client_data=LINDA_CLIENT_DATA, week=args.week)

Macros: 360 calories, 28g carbs, 30g protein, 12g fats


Lunch({times['lunch']})

Meal: {lunch2[0].replace('(Thu–Sat batch)', '(Leftover batch)')}

Ingredients: (same as Day 4)

Preparation: (5 minutes)

{lunch2[3]}


Afternoon Snack({times['snack']})

Meal: Apple & Almond Butter + Protein Shake

Ingredients: (same as Day 2)

Preparation: (3 minutes)

Macros: 260 calories, 28g carbs, 22g protein, 10g fats


Dinner({times['dinner']})

Meal: TVP Tacos(2 shells) with Black Beans & Avocado

Ingredients: (same as Day 2)

Preparation: (12 minutes)

Macros: 410 calories, 44g carbs, 30g protein, 12g fats


Daily Totals(Day 6):

Calories: {target_cal}

Protein: ~{target_protein}g

Carbs: ~{target_carbs}g

Fats: ~{target_fats}g


WEEK 1 - DAY 7 MEAL PLAN


Breakfast

Meal: —

Ingredients: —

Preparation: Sunday reset – no breakfast today.

Macros: —


Lunch(12: 00 PM – early lunch)

Meal: Vegan Protein Pancakes with Berries

Ingredients:

- 60g Rolled Oats(blended into flour)

- 200ml Unsweetened Soy Milk

- 1 tsp Baking Powder

- 1/2 Banana(mashed) or 60g Apple Puree

- 20g Plant Protein Powder(optional)

- 80g Mixed Berries

- 5ml Maple Syrup

Preparation: Blend oats to flour, whisk with soy milk, baking powder and banana. Cook pancakes on a non-stick pan; top with berries and drizzle maple(12 minutes)

Macros: 480 calories, 62g carbs, 22g protein, 12g fats


Dinner(Cheat Meal)

Meal: Flexible Choice within Guidelines

Guidelines:

- Add a protein(tofu/tempeh/beans) and plenty of veg

- Favour baked/grilled over deep-fried

- Pause at comfortable fullness; hydrate well

- Enjoy mindfully – back on plan tomorrow

Macros: Flexible


INGREDIENT SHOPPING LIST – WEEK {wk}


Proteins & Alternatives:

• Firm Tofu 1kg

• Tempeh 300g

• TVP(Textured Vegetable Protein) 300g

• High-Protein Soy Yogurt 4 x 160g

• Plant Protein Powder 500g

• Nutritional Yeast 125g(B12-fortified)


Pantry & Grains:

• Unsweetened Soy Milk 3L(B12-fortified)

• Brown Rice 1kg

• Quinoa 1kg ( or Buckwheat 1kg)

• Vetta SMART Protein Pasta 500g

• Cauliflower Pizza Base x2

• Taco Shells(Hard) x1 pack

• Passata 700ml

• Korma Simmer Sauce 375g(low sugar)

• Light Coconut Milk 400ml

• Tahini 385g

• Peanut Butter 375g

• Ground Flaxseed 300g

• Chia Seeds 300g

• Hemp Seeds 200g

• Mixed Nuts 300g

• Olive Oil 250ml

• Soy Sauce 250ml


Legumes & Canned:

• Chickpeas(No Added Salt) 4 x 420g

• Black Beans 2 x 400g

• Red Lentils 500g(dry)


Produce & Fresh/Frozen:

• Mixed Berries 1kg(frozen)

• Apples 1.2kg

• Spinach 600g

• Mushrooms 500g

• Capsicum 4

• Onions 1kg

• Tomatoes 6

• Broccoli 2 heads

• Carrots 1kg

• Lettuce 1

• Lemon/Lime 4

• Sauerkraut 500g(optional)


Supplements(optional):

• Algal Oil(DHA/EPA omega-3)

• B12 Supplement(methylcobalamin or cyanocobalamin)

"""





def extract_day_meals(text: str, day_type: str) -> dict:

    meals = {}

    lines = text.split('\n')

    current_day = None

    current_meal = None

    current_content = []

    for raw in lines:

        l = raw.strip()

        if not l:

            continue

        # Generic week header matcher (works for WEEK 1..6)

        if l.startswith('WEEK ') and ' - DAY ' in l and day_type in l:

            current_day = day_type

            current_meal = None

            current_content = []

            continue

        if l.startswith('WEEK ') and ' - DAY ' in l and day_type not in l:

            if current_day == day_type and current_meal and current_content:

                meals[current_meal] = '\n'.join(current_content).strip()

            current_day = None

            current_meal = None

            current_content = []

            continue

        if current_day == day_type:

            if l.startswith('Breakfast') or l.startswith('Lunch') or l.startswith('Afternoon Snack') or l.startswith('Dinner'):

                if current_meal and current_content:

                    meals[current_meal] = '\n'.join(current_content).strip()

                current_meal = l.split('(')[0].strip()

                current_content = []

            elif l.startswith('INGREDIENT SHOPPING LIST') or l.startswith('NUTRITIONAL'):

                if current_meal and current_content:

                    meals[current_meal] = '\n'.join(current_content).strip()

                break

            elif current_meal:

                current_content.append(l)

    if current_day == day_type and current_meal and current_content:

        meals[current_meal] = '\n'.join(current_content).strip()

    return meals





def format_meal_content(content: str) -> str:

    if not content:

        return ""

    lines = content.split('\n')

    formatted = []

    for l in lines:

        l = l.strip()

        if l.startswith('Calculation:'):

            continue

        # Drop any embedded totals from the source text to avoid duplicates

        if l.startswith('Daily Totals') or l.startswith('Calories:') or l.startswith('Protein:') or l.startswith('Carbs:') or l.startswith('Fats:'):

            continue

        if l.startswith('Meal:') or l.startswith('Ingredients:') or l.startswith('Preparation:') or l.startswith('Macros:') or l.startswith('Guidelines:'):

            formatted.append(f"<b>{l}</b>")

        elif l.startswith('- '):

            formatted.append(f"  {l}")

        else:

            formatted.append(l)

    return '<br/>'.join(formatted)





def link_for(item_name: str) -> str:

    product_links = {

        'Firm Tofu 1kg': 'https://www.woolworths.com.au/shop/search/products?searchTerm=soyco%20firm%20tofu',

        'Tempeh 300g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=tempeh',

        'TVP (Textured Vegetable Protein) 300g': 'https://www.woolworths.com.au/shop/productdetails/173289/macro-textured-vegetable-protein',

        'High-Protein Soy Yogurt 4 x 160g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=soy%20protein%20yogurt',

        'Plant Protein Powder 500g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=plant%20protein%20powder',

        'Nutritional Yeast 125g (B12-fortified)': 'https://www.woolworths.com.au/shop/search/products?searchTerm=nutritional%20yeast',

        'Unsweetened Soy Milk 3L (B12-fortified)': 'https://www.woolworths.com.au/shop/search/products?searchTerm=unsweetened%20soy%20milk',

        'Brown Rice 1kg': 'https://www.woolworths.com.au/shop/search/products?searchTerm=brown%20rice%201kg',

        'Quinoa 1kg (or Buckwheat 1kg)': 'https://www.woolworths.com.au/shop/search/products?searchTerm=quinoa%201kg',

        'Vetta SMART Protein Pasta 500g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=vetta%20protein%20pasta',

        'Cauliflower Pizza Base x2': 'https://www.woolworths.com.au/shop/search/products?searchTerm=cauliflower%20pizza%20base',

        'Taco Shells (Hard) x1 pack': 'https://www.woolworths.com.au/shop/search/products?searchTerm=hard%20taco%20shells',

        'Passata 700ml': 'https://www.woolworths.com.au/shop/search/products?searchTerm=passata',

        'Korma Simmer Sauce 375g (low sugar)': 'https://www.woolworths.com.au/shop/search/products?searchTerm=korma%20simmer%20sauce',

        'Light Coconut Milk 400ml': 'https://www.woolworths.com.au/shop/search/products?searchTerm=light%20coconut%20milk',

        'Tahini 385g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=mayver%27s%20tahini',

        'Peanut Butter 375g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=peanut%20butter',

        'Ground Flaxseed 300g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=ground%20linseed%20flaxseed',

        'Chia Seeds 300g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=chia%20seeds',

        'Hemp Seeds 200g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=hemp%20seeds',

        'Mixed Nuts 300g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=mixed%20nuts%20300g',

        'Olive Oil 250ml': 'https://www.woolworths.com.au/shop/search/products?searchTerm=olive%20oil',

        'Soy Sauce 250ml': 'https://www.woolworths.com.au/shop/search/products?searchTerm=soy%20sauce',

        'Chickpeas (No Added Salt) 4 x 420g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=chickpeas%20no%20added%20salt',

        'Black Beans 2 x 400g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=black%20beans%20400g',

        'Red Lentils 500g (dry)': 'https://www.woolworths.com.au/shop/search/products?searchTerm=red%20lentils%20dry',

        'Mixed Berries 1kg (frozen)': 'https://www.woolworths.com.au/shop/search/products?searchTerm=mixed%20berries%20frozen',

        'Apples 1.2kg': 'https://www.woolworths.com.au/shop/search/products?searchTerm=gala%20apples',

        'Spinach 600g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=baby%20spinach',

        'Mushrooms 500g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=mushrooms%20500g',

        'Capsicum 4': 'https://www.woolworths.com.au/shop/search/products?searchTerm=capsicum',

        'Onions 1kg': 'https://www.woolworths.com.au/shop/search/products?searchTerm=brown%20onions%201kg',

        'Tomatoes 6': 'https://www.woolworths.com.au/shop/search/products?searchTerm=tomatoes',

        'Broccoli 2 heads': 'https://www.woolworths.com.au/shop/search/products?searchTerm=broccoli',

        'Carrots 1kg': 'https://www.woolworths.com.au/shop/search/products?searchTerm=carrots%201kg',

        'Lettuce 1': 'https://www.woolworths.com.au/shop/search/products?searchTerm=lettuce',

        'Lemon/Lime 4': 'https://www.woolworths.com.au/shop/search/products?searchTerm=lime',

        'Sauerkraut 500g (optional)': 'https://www.woolworths.com.au/shop/search/products?searchTerm=sauerkraut',

        'Algal Oil (DHA/EPA omega-3)': 'https://www.woolworths.com.au/shop/search/products?searchTerm=algal%20oil%20omega%203',

        'B12 Supplement (methylcobalamin or cyanocobalamin)': 'https://www.woolworths.com.au/shop/search/products?searchTerm=vitamin%20b12',

    }

    if item_name in product_links:

        return product_links[item_name]

    return f"https://www.woolworths.com.au/shop/search/products?searchTerm={item_name.replace(' ', '%20')}"





def parse_meal_macros(content: str):

    """Extract calories, protein, carbs, fats from a meal content block.

    Returns(calories, protein_g, carbs_g, fats_g). Zeros if not found.

    """

    if not content:

        return 0, 0, 0, 0

    target = None

    for ln in content.split('\n'):

        if ln.strip().lower().startswith('macros:'):

            target = ln.lower()

            break

    if target is None:

        target = content.lower()



    def find_num(pattern: str) -> int:

        m = re.search(pattern, target)

        return int(m.group(1)) if m else 0

    calories = find_num(r"(\d+)\s*calories")

    protein_g = find_num(r"(\d+)\s*g\s*protein")

    carbs_g = find_num(r"(\d+)\s*g\s*carbs")

    fats_g = find_num(r"(\d+)\s*g\s*fats")

    return calories, protein_g, carbs_g, fats_g





def create_pdf(week: int = 1):

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    current_date = datetime.now().strftime("%Y%m%d")

    filename = os.path.join(

        OUTPUT_DIR, f"Linda_Week{week}_Meal_Plan_{current_date}_PRO.pdf")



    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=72,

                            leftMargin=72, topMargin=72, bottomMargin=18)



    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(

        'Title', parent=styles['Heading1'], fontSize=24, alignment=1, spaceAfter=30, textColor=colors.HexColor('#0B3D91'))

    day_title_style = ParagraphStyle(

        'DayTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0B3D91'), spaceAfter=14)

    meal_title_style = ParagraphStyle('MealTitle', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor(

        '#0B3D91'), spaceBefore=10, spaceAfter=6)

    body_style = ParagraphStyle(

        'Body', parent=styles['Normal'], fontSize=11, leading=16)

    info_style = ParagraphStyle(

        'Info', parent=styles['Normal'], alignment=1, fontSize=12, spaceAfter=6)

    shopping_title_style = ParagraphStyle(

        'ShoppingTitle', parent=styles['Heading1'], fontSize=18, alignment=1, textColor=colors.HexColor('#0B3D91'), spaceAfter=12)

    shopping_category_style = ParagraphStyle(

        'ShoppingCategory', parent=styles['Heading2'], fontSize=14, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor('#0B3D91'))

    shopping_item_style = ParagraphStyle('ShoppingItem', parent=styles['Normal'], fontSize=11, leftIndent=20, leading=14, textColor=colors.HexColor(

        '#0066CC'), underline=True, spaceBefore=3, spaceAfter=3)

    note_style = ParagraphStyle('Note', parent=body_style, fontSize=10,

                                alignment=1, textColor=colors.HexColor('#666666'), spaceAfter=15)



    story = []



    # Cover

    if os.path.exists(LOGO_PATH):

        story.append(Image(LOGO_PATH, width=2*inch, height=2*inch))

    story.append(Spacer(1, 30))

    story.append(Paragraph("MEAL PLAN", title_style))



    client_info = f"""

    <para alignment = "center" >

    <b > Client: < /b > Linda Hayes < br/>

    <b > Date: < /b > {datetime.now().strftime('%d/%m/%Y')} < br/>

    <b > Goal: < /b > Vegan Fat Loss(iron/B12/omega-3 focus)

    </para >

    """

    story.append(Paragraph(client_info, info_style))



    # Targets

    # Recompute to print

    age = calculate_age("2003-09-21")

    cal, p, c, f = calculate_targets_fat_loss_female(

        66.3, 162, age, 1.375, 500)

    targets = f"""

    <para alignment = "center" bgcolor = "#F5F5F5" >

    <b > Daily Targets < /b > <br/>

    Calories: {cal} < br/>

    Protein: ~{p}g < br/>

    Carbs: ~{c}g < br/>

    Fats: ~{f}g

    </para >

    """

    story.append(Paragraph(targets, info_style))



    # Content

    content = get_meal_plan_text(week=week)



    # Days 1–7

    for i in range(1, 8):

        day = f"DAY {i}"

        story.append(PageBreak())

        story.append(Paragraph(f"{day} MEAL PLAN", day_title_style))

        meals = extract_day_meals(content, day)

        # Keep order

        day_cals = day_pro = day_carbs = day_fats = 0

        for label in ("Breakfast", "Lunch", "Afternoon Snack", "Dinner"):

            if label in meals:

                # accumulate macros

                cal, pro, carbs, fats = parse_meal_macros(meals[label])

                day_cals += cal

                day_pro += pro

                day_carbs += carbs

                day_fats += fats

                story.append(KeepTogether([

                    Paragraph(label, meal_title_style),

                    Paragraph(format_meal_content(meals[label]), body_style)

                ]))

        # Show recalculated totals for the day

        story.append(Spacer(1, 6))

        totals_str = f"<b>Daily Totals:</b> Calories: {day_cals}  •  Protein: {day_pro}g  •  Carbs: {day_carbs}g  •  Fats: {day_fats}g"

        story.append(Paragraph(totals_str, body_style))



    # Shopping List

    story.append(PageBreak())

    story.append(Paragraph("INGREDIENT SHOPPING LIST", shopping_title_style))

    story.append(Paragraph(

        "💡 <b>Tip:</b> Items below are clickable to help you shop online.", note_style))



    lines = content.split('\n')

    shopping = []

    in_list = False

    for ln in lines:

        t = ln.strip()

        if t.startswith('INGREDIENT SHOPPING LIST'):

            in_list = True

            continue

        if in_list and t.startswith('Supplements'):

            # include supplements too; keep flowing

            shopping.append(ln)

            continue

        if in_list and t == '':

            shopping.append(ln)

            continue

        if in_list and not t:

            shopping.append(ln)

            continue

        if in_list and not t.startswith('•') and not t.endswith(':') and t:

            # reached non-list content; stop (safety)

            break

        if in_list:

            shopping.append(ln)



    current_category = None

    seen = set()

    for raw in shopping:

        s = raw.strip()

        if not s:

            continue

        if s.endswith(':') and ('Proteins' in s or 'Pantry' in s or 'Produce' in s or 'Legumes' in s or 'Supplements' in s):

            current_category = s

            story.append(Paragraph(current_category, shopping_category_style))

            continue

        if s.startswith('•'):

            item = s[1:].strip()

            # Consolidate nuts

            if item in ('Walnuts 300g', 'Almonds 300g'):

                item = 'Mixed Nuts 300g'

            if item in seen:

                continue

            seen.add(item)

            story.append(Paragraph(

                f"<link href=\"{link_for(item)}\"><u>{item}</u></link>", shopping_item_style))



    # Nutrition Guide (expanded – matches PRO quality)

    story.append(PageBreak())

    story.append(

        Paragraph("PLANT-BASED NUTRITION GUIDE", shopping_title_style))

    story.append(Spacer(1, 12))

    story.append(Paragraph(

        "Understanding Plant-Based Protein & Macro Balancing", meal_title_style))

    story.append(Spacer(1, 6))

    story.append(Paragraph("Most plant proteins come bundled with either carbohydrates (legumes, grains) or fats (nuts, seeds). Hitting targets is 100% doable – it just needs smart choices:", body_style))

    story.append(Spacer(1, 6))

    story.append(Paragraph("Protein Sources", meal_title_style))

    story.append(Paragraph("Focus on protein-dense options first: tofu, tempeh, seitan, TVP/soy mince, high-protein pasta, and fortified soy yogurt. Use a clean plant protein powder when convenient.", body_style))

    story.append(Spacer(1, 6))

    story.append(Paragraph("Macro Control", meal_title_style))

    story.append(Paragraph("• Use protein isolates (powders) for grams without extra carbs/fats.<br/>• Choose high-protein product swaps (e.g., protein pasta vs standard).<br/>• Combine foods across the day to cover amino acids (grains + legumes).", body_style))

    story.append(Spacer(1, 6))

    story.append(Paragraph("Iron (non-heme)", meal_title_style))

    story.append(Paragraph("Prioritise chickpeas, lentils, beans, tofu/tempeh, spinach and pumpkin seeds. Add vitamin C at meals (capsicum, lemon, berries) to boost absorption. Avoid tea/coffee 60 minutes around iron-rich meals.", body_style))

    story.append(Spacer(1, 6))

    story.append(Paragraph("Vitamin B12", meal_title_style))

    story.append(Paragraph(

        "Use fortified foods (soy milk, nutritional yeast) and a reliable B12 supplement (weekly or daily) to maintain levels.", body_style))

    story.append(Spacer(1, 6))

    story.append(Paragraph("Omega-3 Strategy", meal_title_style))

    story.append(Paragraph(

        "Daily ALA from flax, chia and hemp. For direct DHA/EPA, add an algal oil supplement (vegan). This supports brain, mood and endurance.", body_style))



    doc.build(story)

    print(f"✅ Linda Week 1 PRO PDF created: {filename}")





if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--week", type=int, default=1)

    args = parser.parse_args()

    create_pdf(week=args.week)

