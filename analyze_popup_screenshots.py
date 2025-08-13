import os
import google.generativeai as genai
from datetime import datetime


def analyze_nutrition_popup_with_gemini(screenshot_path, gemini_api_key):
    """Analyze a nutrition popup screenshot with Gemini to extract detailed meal information."""
    if not gemini_api_key:
        print("Gemini API key not configured.")
        return None
    if not screenshot_path or not os.path.exists(screenshot_path):
        print(f"Screenshot not found at {screenshot_path}")
        return None

    print(f"🔍 Analyzing nutrition popup: {screenshot_path}")
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        with open(screenshot_path, 'rb') as image_file:
            image_data = image_file.read()

        image_parts = [{
            "mime_type": "image/png",
            "data": image_data
        }]

        prompt = """Analyze this Trainerize nutrition popup screenshot and extract ALL detailed meal information.

CRITICAL: Look very carefully for meal sections and food items. The format typically shows:

**MEAL SECTIONS** (like "Breakfast", "Lunch", "Dinner", "Snacks"):
- Each meal section shows total calories for that meal
- Under each meal are individual food items with their calories

**FOOD ITEMS** (like):
- "thick bacon - Bacon, 2 slices (90 Cal)"
- "Sourdough - Sourdough, 100 g (222 Cal)" 
- "Caramel Oreo Weetbix, 1 serving (362 Cal)"
- "Beef Oyster Blade - Steak, 300 g (403 Cal)"

**MACRO INFORMATION**:
- Look for Protein, Carbs, Fat values (like "Protein 105g", "Carbs 140g", "Fat 47g")

**TOTAL CALORIES**:
- Look for total daily calories

Please extract and format the information EXACTLY like this:

**DATE:** [Date if visible]

**TOTAL CALORIES:** [Total calories for the day]

**MACROS:**
- Protein: [X]g
- Carbs: [X]g  
- Fat: [X]g

**DETAILED MEALS:**

**BREAKFAST ([X] Cal):**
- [Food item 1 with calories]
- [Food item 2 with calories]
- [etc...]

**LUNCH ([X] Cal):**
- [Food item 1 with calories]
- [Food item 2 with calories]
- [etc...]

**DINNER ([X] Cal):**
- [Food item 1 with calories]
- [Food item 2 with calories]
- [etc...]

**SNACKS ([X] Cal):**
- [Food item 1 with calories]
- [Food item 2 with calories]
- [etc...]

IMPORTANT: 
- Extract EVERY food item you can see, even if the text is small
- Include the exact calorie amounts for each food item
- If you can't see a meal section, write "NOT VISIBLE"
- Be very thorough - this is detailed nutrition tracking data"""

        response = model.generate_content([prompt, image_parts[0]])
        print("✅ Gemini analysis complete.")
        return response.text

    except Exception as e:
        print(f"❌ Error during Gemini analysis: {e}")
        return None


def main():
    """Analyze all nutrition popup screenshots."""
    # Set your Gemini API key here
    gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

    # List of popup screenshots to analyze
    popup_screenshots = [
        "nutrition_popup_2.png",
        "nutrition_popup_3.png",
        "nutrition_popup_4.png",
        "nutrition_popup_5.png"
    ]

    all_analyses = []

    print("🍎 ANALYZING NUTRITION POPUP SCREENSHOTS")
    print("=" * 60)

    for screenshot in popup_screenshots:
        if os.path.exists(screenshot):
            print(f"\n📸 Analyzing {screenshot}...")
            analysis = analyze_nutrition_popup_with_gemini(
                screenshot, gemini_api_key)

            if analysis:
                print(f"✅ Analysis complete for {screenshot}")
                all_analyses.append({
                    'screenshot': screenshot,
                    'analysis': analysis
                })
            else:
                print(f"❌ Analysis failed for {screenshot}")
        else:
            print(f"⚠️ Screenshot not found: {screenshot}")

    # Generate comprehensive report
    if all_analyses:
        print("\n" + "=" * 80)
        print("🍎 COMPREHENSIVE NUTRITION ANALYSIS - ALICE FORSTER")
        print("📅 DETAILED MEAL BREAKDOWN FROM POPUP SCREENSHOTS")
        print("=" * 80)

        report_lines = []
        report_lines.append(
            "🍎 COMPREHENSIVE NUTRITION ANALYSIS - ALICE FORSTER")
        report_lines.append("📅 DETAILED MEAL BREAKDOWN FROM POPUP SCREENSHOTS")
        report_lines.append("=" * 80)

        for i, analysis_data in enumerate(all_analyses, 1):
            screenshot_name = analysis_data['screenshot']
            analysis_text = analysis_data['analysis']

            report_lines.append(
                f"\n📸 POPUP SCREENSHOT #{i}: {screenshot_name}")
            report_lines.append("-" * 60)
            report_lines.append(analysis_text)
            report_lines.append("-" * 60)

            # Also print to console
            print(f"\n📸 POPUP SCREENSHOT #{i}: {screenshot_name}")
            print("-" * 60)
            print(analysis_text)
            print("-" * 60)

        # Save comprehensive report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"Alice_Forster_detailed_nutrition_analysis_{timestamp}.txt"

        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            print(
                f"\n💾 Comprehensive nutrition analysis saved to: {report_filename}")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")

        print("\n✅ All popup screenshots analyzed successfully!")
    else:
        print("\n❌ No popup screenshots could be analyzed.")


if __name__ == "__main__":
    main()
