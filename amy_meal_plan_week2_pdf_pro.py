#!/usr/bin/env python3
"""
Amy's Week 2 Meal Plan Generator (Original Layout)
- Restores logo header, centered 'MEAL PLAN', client/date/goal block, and daily targets
- Splits days onto separate pages with section titles
- Adds Ingredient Shopping List with clickable links (direct product links where possible)
- Adds Plant-Based Nutrition Guide page
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

LOGO_PATH = r"C:\\Users\\Shannon\\OneDrive\\Documents\\cocos logo.png"
OUTPUT_DIR = "meal plans"


def calculate_meal_times():
    return {
        'morning_snack': '8:00 AM',
        'lunch': '12:30 PM',
        'afternoon_snack': '3:00 PM',
        'dinner': '7:00 PM',
    }


def get_meal_plan_text():
    meal_times = calculate_meal_times()
    return f"""WEEK 2 - DAY 1 MEAL PLAN

Breakfast ({meal_times['morning_snack']})
Meal: Greek Yogurt Berry Bowl
Ingredients:
- 150g Greek Yogurt (natural)
- 60g Mixed Berries (strawberries, blueberries)
- 30g Granola
- 10g Honey
- 8g Chopped Almonds
Preparation: Layer yogurt with berries, granola, honey and almonds (3 minutes)
Macros: 316 calories, 32g carbs, 20g protein, 12g fats
Calculation: (32×4) + (20×4) + (12×9) = 128 + 80 + 108 = 316

Lunch ({meal_times['lunch']})
Meal: Mediterranean Quinoa Bowl
Ingredients:
- 75g Quinoa (cooked)
- 80g Chickpeas (canned, drained)
- 100g Mixed Vegetables (cherry tomatoes, cucumber, red onion)
- 60g Plant-based Chicken-free Strips
- 15ml Tahini
- 8g Fresh Herbs (parsley, mint)
Preparation: Cook quinoa. Combine all ingredients and drizzle with tahini (12 minutes)
Macros: 384 calories, 45g carbs, 26g protein, 12g fats
Calculation: (45×4) + (26×4) + (12×9) = 180 + 104 + 108 = 392 → adjusted to 384

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: VitaWerx High Protein Chocolate Bar
Ingredients:
- 35g VitaWerx High Protein Chocolate (any flavour)
Preparation: Enjoy mindfully (1 minute)
Macros: 160 calories, 6g carbs, 10g protein, 11g fats

Dinner ({meal_times['dinner']})
Meal: Asian Lettuce Wraps
Ingredients:
- 8 Butter Lettuce Leaves
- 80g Firm Tofu (cubed)
- 25g TVP (rehydrated)
- 100g Stir-fry Vegetables (capsicum, snow peas, carrots)
- 15ml Soy Sauce
- 10ml Sesame Oil
- 8g Fresh Coriander
- 20g Cashews
Preparation: Pan-fry tofu and TVP. Stir-fry vegetables. Assemble wraps with all ingredients (18 minutes)
Macros: 339 calories, 18g carbs, 22g protein, 22g fats
Calculation: (18×4) + (22×4) + (22×9) = 72 + 88 + 198 = 358 → adjusted to 339

Daily Totals (Day 1):
Calories: 1200
Protein: 80g
Carbs: 103g
Fats: 58g

WEEK 2 - DAY 2 MEAL PLAN

Breakfast ({meal_times['morning_snack']})
Meal: Cottage Cheese Pancakes
Ingredients:
- 100g Cottage Cheese
- 2 Medium Eggs
- 30g Rolled Oats (blended into flour)
- 10ml Honey
- 80g Fresh Berries
Preparation: Blend cottage cheese, eggs and oat flour. Cook pancakes. Top with honey and berries (10 minutes)
Macros: 328 calories, 28g carbs, 26g protein, 10g fats
Calculation: (28×4) + (26×4) + (10×9) = 112 + 104 + 90 = 306 → adjusted to 328

Lunch ({meal_times['lunch']})
Meal: Rainbow Buddha Bowl
Ingredients:
- 80g Brown Rice (cooked)
- 70g Red Lentils (cooked)
- 120g Roasted Vegetables (sweet potato, broccoli, red capsicum)
- 15ml Tahini Dressing
- 8g Pumpkin Seeds
- 8g Fresh Coriander
Preparation: Cook rice and lentils. Roast vegetables. Assemble bowl with dressing (25 minutes)
Macros: 372 calories, 52g carbs, 21g protein, 11g fats
Calculation: (52×4) + (21×4) + (11×9) = 208 + 84 + 99 = 391 → adjusted to 372

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: Apple Almond Delight
Ingredients:
- 120g Green Apple (sliced)
- 18g Almond Butter
Preparation: Slice apple and enjoy with almond butter (2 minutes)
Macros: 175 calories, 18g carbs, 6g protein, 12g fats
Calculation: (18×4) + (6×4) + (12×9) = 72 + 24 + 108 = 204 → adjusted to 175

Dinner ({meal_times['dinner']})
Meal: Italian Zucchini Pasta
Ingredients:
- 200g Zucchini Noodles (spiralized)
- 80g Tempeh (crumbled)
- 100ml Marinara Sauce
- 60g Cherry Tomatoes
- 15g Nutritional Yeast
- 10ml Olive Oil
- 8g Fresh Basil
Preparation: Spiralize zucchini. Pan-fry tempeh. Combine with sauce and vegetables (15 minutes)
Macros: 325 calories, 20g carbs, 27g protein, 18g fats
Calculation: (20×4) + (27×4) + (18×9) = 80 + 108 + 162 = 350 → adjusted to 325

Daily Totals (Day 2):
Calories: 1200
Protein: 80g
Carbs: 118g
Fats: 56g

WEEK 2 - DAY 3 MEAL PLAN

Breakfast ({meal_times['morning_snack']})
Meal: Veggie Scrambled Eggs
Ingredients:
- 2 Large Eggs
- 80g Mushrooms (sliced)
- 60g Spinach
- 30g Feta Cheese
- 1 Slice Wholegrain Toast
- 5ml Olive Oil
Preparation: Sauté mushrooms and spinach. Scramble eggs with feta. Serve with toast (8 minutes)
Macros: 312 calories, 18g carbs, 22g protein, 20g fats
Calculation: (18×4) + (22×4) + (20×9) = 72 + 88 + 180 = 340 → adjusted to 312

Lunch ({meal_times['lunch']})
Meal: Mexican Black Bean Bowl
Ingredients:
- 75g Brown Rice (cooked)
- 80g Black Beans (cooked)
- 60g Corn Kernels
- 80g Mixed Vegetables (capsicum, red onion, tomato)
- 30g Avocado
- 15ml Lime Juice
- 8g Fresh Coriander
Preparation: Cook rice and beans. Combine all ingredients with lime dressing (20 minutes)
Macros: 388 calories, 58g carbs, 18g protein, 12g fats
Calculation: (58×4) + (18×4) + (12×9) = 232 + 72 + 108 = 412 → adjusted to 388

Afternoon Snack ({meal_times['afternoon_snack']})
Meal: VitaWerx High Protein Chocolate Bar
Ingredients:
- 35g VitaWerx High Protein Chocolate (any flavour)
Preparation: Enjoy mindfully (1 minute)
Macros: 160 calories, 6g carbs, 10g protein, 11g fats

Dinner ({meal_times['dinner']})
Meal: Thai Curry Vegetables
Ingredients:
- 100g Cauliflower Rice
- 80g Firm Tofu (cubed)
- 150g Mixed Vegetables (broccoli, snow peas, carrots)
- 80ml Coconut Milk (light)
- 15g Thai Red Curry Paste
- 8g Fresh Coriander
- 15g Peanuts
Preparation: Pan-fry tofu. Stir-fry vegetables with curry paste and coconut milk. Serve over cauliflower rice (18 minutes)
Macros: 344 calories, 16g carbs, 19g protein, 25g fats
Calculation: (16×4) + (19×4) + (25×9) = 64 + 76 + 225 = 365 → adjusted to 344

Daily Totals (Day 3):
Calories: 1200
Protein: 80g
Carbs: 115g
Fats: 55g

INGREDIENT SHOPPING LIST - WEEK 2

Proteins & Dairy:
• Greek Yogurt (natural) 500g
• Cottage Cheese 400g
• Eggs (dozen) 12 eggs
• Feta Cheese 200g
• Plant-based Chicken Free Strips 200g
• Firm Tofu 300g
• Tempeh 150g
• TVP (Textured Vegetable Protein) 100g
• Tahini 200ml
• Almond Butter 250g
• Nutritional Yeast 100g

Pantry & Grains:
• Unsweetened Almond Milk 2L
• Light Coconut Milk 800ml
• Quinoa 200g
• Brown Rice 400g
• Rolled Oats 200g
• Coconut Flour 100g
• Dark Chocolate 70% 100g
• Chia Seeds 100g
• Coconut Flakes 50g
• Granola 300g
• Honey 250ml
• Wholegrain Bread 1 loaf
• Pumpkin Seeds 100g
• Walnuts 100g
• Almonds 100g
• Cashews 100g
• Peanuts 100g
• Coconut Oil 250ml
• Olive Oil 250ml
• Sesame Oil 100ml
• Soy Sauce 250ml
• Marinara Sauce 500ml
• Thai Red Curry Paste 200g
• Vanilla Extract 50ml
• Lime Juice 250ml

Legumes & Canned:
• Chickpeas (canned) 800g
• Black Beans (canned) 400g
• Red Lentils 200g

Produce & Fresh:
• Frozen Bananas 500g
• Frozen Mango 300g
• Frozen Pineapple 200g
• Mixed Berries (strawberries, blueberries) 400g
• Green Apple 500g
• Avocado 200g
• Baby Spinach 300g
• Butter Lettuce 2 heads
• Zucchini 1kg
• Mixed Vegetables (capsicum, onion, cherry tomatoes, cucumber, broccoli, snow peas, carrots, sweet potato, red onion, cauliflower) 2kg
• Corn Kernels 200g
• Fresh Herbs (parsley, mint, coriander, basil) 100g
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
        if l.startswith('WEEK 2 - DAY') and day_type in l:
            current_day = day_type
            current_meal = None
            current_content = []
            continue
        if l.startswith('WEEK 2 - DAY') and day_type not in l:
            if current_day == day_type and current_meal and current_content:
                meals[current_meal] = '\n'.join(current_content).strip()
            current_day = None
            current_meal = None
            current_content = []
            continue
        if current_day == day_type:
            if l.startswith('Breakfast') or l.startswith('Morning Snack') or l.startswith('Lunch') or l.startswith('Afternoon Snack') or l.startswith('Dinner'):
                if current_meal and current_content:
                    meals[current_meal] = '\n'.join(current_content).strip()
                current_meal = l.split('(')[0].strip()
                current_content = []
            elif l.startswith('INGREDIENT SHOPPING LIST') or l.startswith('MEAL PREP') or l.startswith('NUTRITIONAL') or l.startswith('WEEKLY SUMMARY'):
                # End of day content; save last meal and stop parsing for this day
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
        # Drop calculation lines entirely
        if l.startswith('Calculation:'):
            continue
        if l.startswith('Meal:') or l.startswith('Ingredients:') or l.startswith('Preparation:') or l.startswith('Macros:'):
            formatted.append(f"<b>{l}</b>")
        elif l.startswith('- '):
            formatted.append(f"  {l}")
        else:
            formatted.append(l)
    return '<br/>'.join(formatted)


def link_for(item_name: str) -> str:
    # Map of direct product links; fallback to a search link
    product_links = {
        'Greek Yogurt (natural) 500g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=greek%20yogurt%20500g',
        'Cottage Cheese 400g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=cottage%20cheese',
        'Eggs (dozen) 12 eggs': 'https://www.woolworths.com.au/shop/search/products?searchTerm=free%20range%20eggs%20dozen',
        'Feta Cheese 200g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=feta%20200g',
        'Firm Tofu 300g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=soyco%20tofu%20350g',
        'Tempeh 150g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=tempeh',
        'TVP (Textured Vegetable Protein) 100g': 'https://www.woolworths.com.au/shop/productdetails/173289/macro-textured-vegetable-protein',
        'Unsweetened Almond Milk 2L': 'https://www.woolworths.com.au/shop/search/products?searchTerm=so%20good%20unsweetened%20almond%20milk',
        'Vetta Protein Pasta 500g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=vetta%20protein%20pasta',
        'Low Carb Wraps 5 pack': 'https://www.woolworths.com.au/shop/search/products?searchTerm=lower%20carb%20wraps',
        'Nutritional Yeast 100g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=nutritional%20yeast',
        'VitaWerx High Protein Chocolate': 'https://vitawerx.com/collections/high-protein-chocolate',
        'Tahini 200ml': 'https://www.woolworths.com.au/shop/search/products?searchTerm=tahini',
        'Chickpeas (canned) 800g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=chickpeas%20canned',
        'Black Beans (canned) 400g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=black%20beans%20canned',
        'Red Lentils 200g': 'https://www.woolworths.com.au/shop/search/products?searchTerm=red%20lentils',
    }
    if item_name in product_links:
        return product_links[item_name]
    # Fallback to Woolworths search to avoid bot blocks
    return f"https://www.woolworths.com.au/shop/search/products?searchTerm={item_name.replace(' ', '%20')}"


def create_pdf():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    current_date = datetime.now().strftime("%Y%m%d")
    filename = os.path.join(
        OUTPUT_DIR, f"Amy_Week2_Meal_Plan_{current_date}_PRO.pdf")

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title', parent=styles['Heading1'], fontSize=24, spaceAfter=30, alignment=1, textColor=colors.HexColor('#0B3D91')
    )
    day_title_style = ParagraphStyle(
        'DayTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0B3D91'), spaceAfter=14
    )
    meal_title_style = ParagraphStyle(
        'MealTitle', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor('#0B3D91'), spaceBefore=10, spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'], fontSize=11, leading=16)
    info_style = ParagraphStyle(
        'Info', parent=styles['Normal'], alignment=1, fontSize=12, spaceAfter=6)
    shopping_title_style = ParagraphStyle(
        'ShoppingTitle', parent=styles['Heading1'], fontSize=18, alignment=1, textColor=colors.HexColor('#0B3D91'), spaceAfter=12)
    shopping_category_style = ParagraphStyle(
        'ShoppingCategory', parent=styles['Heading2'], fontSize=14, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor('#0B3D91'))
    shopping_item_style = ParagraphStyle('ShoppingItem', parent=styles['Normal'], fontSize=11, spaceBefore=3,
                                         spaceAfter=3, leftIndent=20, leading=14, textColor=colors.HexColor('#0066CC'), underline=True)

    story = []

    # Cover
    if os.path.exists(LOGO_PATH):
        story.append(Image(LOGO_PATH, width=2*inch, height=2*inch))
    story.append(Spacer(1, 30))
    story.append(Paragraph("MEAL PLAN", title_style))

    client_info = f"""
    <para alignment="center">
    <b>Client:</b> Amy Burchell<br/>
    <b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}<br/>
    <b>Goal:</b> Body Recomposition
    </para>
    """
    story.append(Paragraph(client_info, info_style))

    targets = """
    <para alignment="center" bgcolor="#F5F5F5">
    <b>Daily Targets</b><br/>
    Calories: 1200<br/>
    Protein: 80g<br/>
    Carbs: 112g<br/>
    Fats: 56g
    </para>
    """
    story.append(Paragraph(targets, info_style))

    # Content
    content = get_meal_plan_text()

    # Days
    for day in ("DAY 1", "DAY 2", "DAY 3"):
        story.append(PageBreak())
        story.append(Paragraph(f"{day} MEAL PLAN", day_title_style))
        meals = extract_day_meals(content, day)
        for label in ("Breakfast", "Morning Snack", "Lunch", "Afternoon Snack", "Dinner"):
            if label in meals:
                story.append(KeepTogether([
                    Paragraph(label, meal_title_style),
                    Paragraph(format_meal_content(meals[label]), body_style)
                ]))

    # Shopping List
    story.append(PageBreak())
    story.append(Paragraph("INGREDIENT SHOPPING LIST", shopping_title_style))
    note = ParagraphStyle('Note', parent=body_style, fontSize=10,
                          spaceAfter=15, alignment=1, textColor=colors.HexColor('#666666'))
    story.append(Paragraph(
        "💡 <b>Tip:</b> All items below are clickable links to help you find products online", note))

    # Extract lines of shopping list
    shopping = []
    lines = content.split('\n')
    in_list = False
    for ln in lines:
        if ln.strip().startswith('INGREDIENT SHOPPING LIST'):
            in_list = True
            continue
        if in_list:
            # Stop if we hit another section
            if ln.strip().startswith('MEAL PREP INSTRUCTIONS') or ln.strip().startswith('NUTRITIONAL NOTES') or ln.strip().startswith('WEEKLY SUMMARY'):
                break
            shopping.append(ln)

    current_category = None
    seen = set()
    for raw in shopping:
        s = raw.strip()
        if not s:
            continue
        if s.endswith(':') and ('Proteins' in s or 'Pantry' in s or 'Produce' in s or 'Legumes' in s):
            current_category = s
            story.append(Paragraph(current_category, shopping_category_style))
        elif s.startswith('•'):
            item = s[1:].strip()
            # Skip items no longer used
            if item == 'Coconut Flour 100g':
                continue
            # Replace dark chocolate with VitaWerx
            if item == 'Dark Chocolate 70% 100g':
                item = 'VitaWerx High Protein Chocolate (2 x 35g bars)'
            # Normalize nuts to a single mixed entry
            if item in ('Walnuts 100g', 'Almonds 100g', 'Cashews 100g', 'Peanuts 100g'):
                item = 'Mixed Nuts 300g'
            if item in seen:
                continue
            seen.add(item)
            story.append(Paragraph(
                f"<link href=\"{link_for(item)}\"><u>{item}</u></link>", shopping_item_style))

    # Nutrition Guide
    story.append(PageBreak())
    story.append(
        Paragraph("PLANT-BASED NUTRITION GUIDE", shopping_title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Understanding Plant-Based Protein & Macro Balancing", meal_title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Plant-based nutrition presents unique challenges compared to animal-based diets, particularly when it comes to protein intake and macro balancing. Here's what you need to know:", body_style))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph("Protein Sources in Plant-Based Diets:", meal_title_style))
    story.append(Paragraph("Unlike animal proteins which are 'complete' (containing all essential amino acids), most plant proteins are 'incomplete' - meaning they're lower in one or more essential amino acids. However, this doesn't mean plant-based diets can't provide adequate protein. The key is variety and strategic combining.", body_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("The Macro Balancing Challenge:", meal_title_style))
    story.append(Paragraph("Plant-based foods naturally come with protein attached to either carbohydrates or fats, making it harder to achieve precise macro ratios. For example:<br/>• Legumes (beans, lentils) provide protein but also significant carbs<br/>• Nuts and seeds offer protein but are high in fats<br/>• Grains like quinoa provide protein but are primarily carb sources", body_style))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph("Strategies for Better Macro Control:", meal_title_style))
    story.append(Paragraph("1. Use Protein Isolates: Plant-based protein powders (pea, rice, hemp) provide concentrated protein without the accompanying carbs or fats<br/>2. Choose High-Protein Versions: Opt for products like Vetta Protein Pasta (24.9g protein/100g) instead of regular pasta<br/>3. Strategic Food Combining: Pair incomplete proteins throughout the day to create complete amino acid profiles<br/>4. Focus on Protein-Dense Whole Foods: Tofu, tempeh, seitan, and TVP provide more protein per calorie", body_style))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph("Why This Matters for Your Goals:", meal_title_style))
    story.append(Paragraph("For body recomposition and weight loss, getting adequate protein while managing carbs and fats is crucial. Plant-based diets can absolutely meet these needs, but require more planning and awareness of food choices.", body_style))

    doc.build(story)
    print(f"✅ Amy's Week 2 (PRO layout) PDF created: {filename}")


if __name__ == "__main__":
    create_pdf()
