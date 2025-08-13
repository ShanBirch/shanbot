import google.generativeai as genai

# Configure Gemini
gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
genai.configure(api_key=gemini_api_key)


def analyze_popup_screenshot():
    """Analyze the nutrition popup screenshot to see what's visible."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Analyze the popup AFTER clicking MyFitnessPal link
        with open('nutrition_popup_2.png', 'rb') as image_file:
            image_data = image_file.read()

        image_parts = [{
            "mime_type": "image/png",
            "data": image_data
        }]

        prompt = """Analyze this nutrition popup screenshot from Trainerize (after clicking MyFitnessPal link) in detail.

This should show the detailed meal breakdown. Please extract EVERYTHING you can see, especially:

1. **MEAL SECTIONS:**
   - List each meal section you see (Breakfast, Lunch, Dinner, Snacks)
   - For each meal section, what's the calorie total shown?

2. **INDIVIDUAL FOOD ITEMS:**
   - List EVERY food item you can see with exact text
   - Include serving sizes and calorie amounts
   - Format like: "Food Name - Description, serving size (XXX Cal)"
   - Examples might be: "Caramel Oreo Weetbix, 1 serving (362 Cal)"

3. **COMPLETE MEAL BREAKDOWN:**
   - For each meal (Breakfast, Lunch, Dinner, Snacks), list all foods under it
   - Show the structure exactly as it appears

4. **MACRO INFORMATION:**
   - What macro breakdown do you see (Protein, Carbs, Fat)?
   - Any calorie goals or targets?

5. **EXACT TEXT EXTRACTION:**
   - Please be very specific and extract the exact text as it appears
   - Don't summarize - give me the literal text for food items

Be extremely detailed and extract every single food item you can see with exact formatting."""

        response = model.generate_content([prompt, image_parts[0]])

        print("🔍 DETAILED POPUP ANALYSIS (nutrition_popup_2.png):")
        print("=" * 80)
        print(response.text)
        print("=" * 80)

        return response.text

    except Exception as e:
        print(f"❌ Error analyzing popup: {e}")
        return None


if __name__ == "__main__":
    analyze_popup_screenshot()
