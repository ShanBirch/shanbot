## Meal Plan Creator – Structure and Build Guide

This guide documents the exact structure, formatting, and steps to build our client meal plans so we can reproduce them every week with consistent quality.

### 1) Cover Page (Page 1)
- **Logo**: Use `cocos logo.png` (2" x 2"). If missing, render title without logo.
- **Centered Title**: “MEAL PLAN” (Heading1, 24pt, color #0B3D91).
- **Client block (centered)**:
  - Client: Full Name
  - Date: DD/MM/YYYY (generation date)
  - Goal: Client’s goal (e.g., Body Recomposition)
- **Daily Targets box (centered, light grey background)**:
  - Calories: NNNN
  - Protein: NN g
  - Carbs: NN g
  - Fats: NN g

Notes:
- Targets are shown on cover only; they are calculated previously per client.
- We do not show any formula calculations in the document.

### 2) Day Sections (Pages 2–4)
Each day starts on a new page with a section header.

- **Header**: “DAY X MEAL PLAN” (Heading1, 16pt, #0B3D91)
- **Meal order**: Breakfast → Morning Snack → Lunch → Afternoon Snack → Dinner
- **Per meal block** (Heading2 for meal name, 13pt, #0B3D91; body 11pt, leading 16):
  - Time in parentheses after meal label if available (e.g., Breakfast (8:00 AM))
  - Meal: <Name>
  - Ingredients: (dash-bulleted list, grams/ml where possible)
  - Preparation: (1–2 lines)
  - Macros: <kcals> calories, <carbs>g carbs, <protein>g protein, <fats>g fats

Rules:
- Do not include macro calculation formulas. Keep the “Macros:” line only.
- Keep ingredient names specific and measurable in g/ml.
- Prefer 8–12 ingredients per day total to keep shopping list manageable.

### 3) Shopping List (Own Page)
Appears after all day sections on a new page. Do not duplicate it at the end of a day page.

- **Title**: “INGREDIENT SHOPPING LIST” (Heading1, 18pt, centered, #0B3D91)
- **Tip line** (centered, grey): “Tip: All items below are clickable links to help you find products online”
- **Categories** (Heading2, 14pt, #0B3D91):
  - Proteins & Dairy (or “Proteins” if vegan)
  - Pantry & Grains
  - Legumes & Canned (optional if relevant)
  - Produce & Fresh
- **Items**: Underlined blue links (#0066CC). Each item links to a product page or a fallback search.

Linking policy:
- Prefer direct product links where we have a stable URL.
- To avoid anti-bot blocks, prefer Woolworths search links: `https://www.woolworths.com.au/shop/search/products?searchTerm=<query>`
- Use brand site when appropriate (e.g., `VitaWerx High Protein Chocolate`).

Content rules:
- Combine individual nuts into one: “Mixed Nuts 300g” (avoid separate 100g walnut/almond/cashew/peanut items).
- Include “VitaWerx High Protein Chocolate (2 x 35g bars)” when used in snacks.
- Only include items used in this week’s recipes. No unreferenced items.
- De-duplicate items across categories.

### 4) Nutrition Guide (Own Page)
Optional education page after the shopping list.

- **Title**: “PLANT-BASED NUTRITION GUIDE” (Heading1, centered, #0B3D91)
- Sections (Heading2 for each):
  - Understanding Plant-Based Protein & Macro Balancing
  - Protein Sources in Plant-Based Diets
  - The Macro Balancing Challenge
  - Strategies for Better Macro Control
  - Why This Matters for Your Goals

### 5) Styling Summary
- Titles: #0B3D91; Links: #0066CC (underlined)
- Fonts: ReportLab defaults (Helvetica family). Body 11pt, leading 16.
- Use KeepTogether for each meal block (heading + content) to avoid awkward page breaks.

### 6) Build Steps (Script Pattern)
Use the pattern implemented in `amy_meal_plan_week2_pdf_pro.py`.

1. Build cover: logo, title, client info, daily targets.
2. Split content into Day 1/2/3 using “WEEK 2 - DAY X MEAL PLAN” markers.
3. Render each day on its own page, meals in fixed order, with KeepTogether.
4. Extract “INGREDIENT SHOPPING LIST” lines; render on its own page with categories and links.
   - Fallback link helper should return Woolworths search URL when no direct product mapping exists.
   - Replace separate nut lines with “Mixed Nuts 300g”.
   - Replace generic dark chocolate with VitaWerx when used as snack.
5. Render optional “PLANT-BASED NUTRITION GUIDE” page.

Key helpers to mirror:
- `extract_day_meals(text, "DAY X")` – finds meals per day and avoids pulling shopping list into day pages.
- `format_meal_content(text)` – bolds section labels, removes any “Calculation:” lines entirely.
- `link_for(item_name)` – product map + Woolworths search fallback.

### 7) QA Checklist (Every Build)
- Cover shows correct client, date, goal, and daily targets.
- No “Calculation:” lines anywhere.
- Day sections start on new pages; meal order is correct; spacing is consistent.
- Shopping list is on its own page only; all links open (no bot-block where possible).
- Nuts consolidated; VitaWerx included when used; no unused items.
- PDFs saved to `meal plans/Client_WeekN_Meal_Plan_YYYYMMDD.pdf`.

### 8) Commands
- Generate a specific plan (example):
  - `python amy_meal_plan_week2_pdf_pro.py`
  - Output: `meal plans/Amy_Week2_Meal_Plan_YYYYMMDD_PRO.pdf`

Use this guide as the source of truth when creating Week 3+ meal plans.


