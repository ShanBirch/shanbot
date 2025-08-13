#!/usr/bin/env python3
"""
Hannah's Week 2 Meal Plan (PRO Layout)
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

from hannah_meal_plan_week2_pdf import get_meal_plan_text as hannah_text

LOGO_PATH = r"C:\\Users\\Shannon\\OneDrive\\Documents\\cocos logo.png"
OUTPUT_DIR = "meal plans"


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
        if l.startswith('Meal:') or l.startswith('Ingredients:') or l.startswith('Preparation:') or l.startswith('Macros:'):
            formatted.append(f"<b>{l}</b>")
        elif l.startswith('- '):
            formatted.append(f"  {l}")
        else:
            formatted.append(l)
    return '<br/>'.join(formatted)


def link_for(item_name: str) -> str:
    return f"https://www.woolworths.com.au/shop/search/products?searchTerm={item_name.replace(' ', '%20')}"


def create_pdf():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    current_date = datetime.now().strftime("%Y%m%d")
    filename = os.path.join(
        OUTPUT_DIR, f"Hannah_Week2_Meal_Plan_{current_date}_PRO.pdf")

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

    story = []
    if os.path.exists(LOGO_PATH):
        story.append(Image(LOGO_PATH, width=2*inch, height=2*inch))
    story.append(Spacer(1, 30))
    story.append(Paragraph("MEAL PLAN", title_style))

    story.append(Paragraph(f"""
    <para alignment="center">
    <b>Client:</b> Hannah<br/>
    <b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}<br/>
    <b>Goal:</b> Plant-Based Performance & Recomp
    </para>
    """, info_style))

    story.append(Paragraph("""
    <para alignment="center" bgcolor="#F5F5F5">
    <b>Daily Targets</b><br/>
    Calories: 1450<br/>
    Protein: 90–95g<br/>
    Carbs: 166–180g<br/>
    Fats: 52–58g
    </para>
    """, info_style))

    content = hannah_text()

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

    story.append(PageBreak())
    story.append(Paragraph("INGREDIENT SHOPPING LIST", shopping_title_style))
    note = ParagraphStyle('Note', parent=body_style, fontSize=10,
                          alignment=1, textColor=colors.HexColor('#666666'), spaceAfter=15)
    story.append(Paragraph(
        "💡 <b>Tip:</b> All items below are clickable links to help you find products online", note))

    lines = content.split('\n')
    shopping = []
    in_list = False
    for ln in lines:
        t = ln.strip()
        if t.startswith('INGREDIENT SHOPPING LIST'):
            in_list = True
            continue
        if in_list and (t.startswith('MEAL PREP') or t.startswith('NUTRITIONAL') or t.startswith('WEEKLY SUMMARY')):
            break
        if in_list:
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
            continue
        if s.startswith('•'):
            item = s[1:].strip()
            if item in ('Walnuts 100g', 'Almonds 100g', 'Cashews 100g', 'Peanuts 100g'):
                item = 'Mixed Nuts 300g'
            if item in seen:
                continue
            seen.add(item)
            story.append(Paragraph(
                f"<link href=\"{link_for(item)}\"><u>{item}</u></link>", shopping_item_style))

    doc.build(story)
    print(f"✅ Hannah Week 2 PRO PDF created: {filename}")


if __name__ == "__main__":
    create_pdf()
