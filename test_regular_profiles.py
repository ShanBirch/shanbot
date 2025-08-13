#!/usr/bin/env python3
"""
Test Smart Lead Finder with Regular Profiles
Test with some regular users who might be potential clients
"""

import time
import random
import base64
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import google.generativeai as genai

# Configure Gemini
GEMINI_API_KEY = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini models for fallback
gemini_models = [
    ('gemini-2.0-flash', genai.GenerativeModel('gemini-2.0-flash')),
    ('gemini-2.0-flash-lite', genai.GenerativeModel('gemini-2.0-flash-lite')),
]

CHROMEDRIVER_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"

# Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option(
    "excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")


def analyze_with_gemini(prompt, image_data=None):
    """Analyze content with Gemini AI."""
    try:
        if image_data:
            contents = [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
            ]
        else:
            contents = prompt

        for model_name, model in gemini_models:
            try:
                response = model.generate_content(contents)
                return response
            except Exception as e:
                print(f"⚠️ {model_name} failed: {e}")
                continue
        return None
    except Exception as e:
        print(f"❌ Gemini analysis failed: {e}")
        return None


def get_screening_prompt(username):
    """Get AI screening prompt - same as improved smart_lead_finder.py"""
    return f"""
    You are an expert Instagram analyst helping a fitness coach find clients. Your task is to analyze the profile of @{username} based on the provided screenshot and determine if they are a potential client.

    Follow these steps and answer the questions in the specified format.

    **IMPORTANT: BE GENEROUS with plant-based identification. Look for:**
    - Any mention of "vegan", "plant-based", "vegetarian"
    - Plant/green emojis (🌱🥗🥕🍃)
    - Healthy eating, smoothies, salads
    - Environmental consciousness
    - Wellness/health content that might indicate plant-based interest

    **Questionnaire (Answer with YES or NO, and provide brief evidence for your choice):**

    1.  **IS_BUSINESS_OR_COACH:** Is this a business, brand, or another coach/trainer?
        - Answer: YES/NO - Evidence: [Provide reason, e.g., "Sells products," "Calls themselves a coach"]

    2.  **IS_PLANT_BASED:** Does this person show ANY interest in plant-based, vegan, or healthy eating?
        - BE GENEROUS: Look for any signs of healthy eating, plant foods, wellness content
        - Answer: YES/NO - Evidence: [Provide reason]

    3.  **APPARENT_GENDER:** What is the apparent gender of the individual?
        - Answer: MALE/FEMALE/UNCLEAR - Evidence: [Briefly state reason]

    4.  **IS_TARGET_FEMALE:** If FEMALE, does she appear to be a middle-aged woman (25+) interested in health/fitness?
        - BE GENEROUS: Any woman who shows wellness/health/fitness interest
        - Answer: YES/NO/NOT_APPLICABLE - Evidence: [Provide reason]

    5.  **IS_TARGET_MALE:** If MALE, does he appear to be someone who could benefit from fitness guidance?
        - BE GENEROUS: Any male who might benefit from fitness coaching
        - Answer: YES/NO/NOT_APPLICABLE - Evidence: [Provide reason]

    6.  **FINAL_VERDICT_POTENTIAL_CLIENT:** Based on the above, is this a potential client?
        - A potential client is an INDIVIDUAL who shows ANY plant-based/health interest and could benefit from coaching
        - Answer: YES/NO - Reason: [Summarize]

    7.  **IS_FAKE_OR_INACTIVE:** Does this look like a bot, fake, or inactive account?
        - Answer: YES/NO - Evidence: [Provide reason]

    **Provide your response in this EXACT format:**
    IS_BUSINESS_OR_COACH: [YES/NO] - Evidence: [reason]
    IS_PLANT_BASED: [YES/NO] - Evidence: [reason]
    APPARENT_GENDER: [MALE/FEMALE/UNCLEAR] - Evidence: [reason]
    IS_TARGET_FEMALE: [YES/NO/NOT_APPLICABLE] - Evidence: [reason]
    IS_TARGET_MALE: [YES/NO/NOT_APPLICABLE] - Evidence: [reason]
    FINAL_VERDICT_POTENTIAL_CLIENT: [YES/NO] - Reason: [reason]
    IS_FAKE_OR_INACTIVE: [YES/NO] - Evidence: [reason]
    """


def test_profile_analysis(username):
    """Test analyzing a single profile."""
    print(f"🧪 TESTING: @{username}")

    driver = None
    try:
        # Setup driver
        service = webdriver.chrome.service.Service(
            executable_path=CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Navigate to profile
        profile_url = f"https://www.instagram.com/{username}/"
        driver.get(profile_url)
        time.sleep(3)

        # Check if profile exists
        if "Sorry, this page isn't available" in driver.page_source:
            print(f"❌ Profile @{username} doesn't exist or is private")
            return

        # Take screenshot
        screenshot_data = driver.get_screenshot_as_base64()

        # Get AI analysis
        prompt = get_screening_prompt(username)
        response = analyze_with_gemini(prompt, screenshot_data)

        if not response:
            print(f"❌ AI analysis failed")
            return

        response_text = response.text
        print(f"✅ AI Analysis Response:")
        print(response_text)

        # Parse response
        def parse_line(key, text):
            match = re.search(
                rf'{key}:\s*(YES|NO|MALE|FEMALE|UNCLEAR|NOT_APPLICABLE)\s*-\s*(?:Evidence|Reason):\s*(.*?)(?=\n[A-Z_]+:|$)',
                text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).upper().strip(), match.group(2).strip()
            return None, "No evidence found"

        is_business_or_coach, _ = parse_line(
            'IS_BUSINESS_OR_COACH', response_text)
        is_plant_based, plant_evidence = parse_line(
            'IS_PLANT_BASED', response_text)
        apparent_gender, _ = parse_line('APPARENT_GENDER', response_text)
        is_target_female, _ = parse_line('IS_TARGET_FEMALE', response_text)
        is_target_male, _ = parse_line('IS_TARGET_MALE', response_text)
        is_potential_client, client_reason = parse_line(
            'FINAL_VERDICT_POTENTIAL_CLIENT', response_text)
        is_fake, _ = parse_line('IS_FAKE_OR_INACTIVE', response_text)

        # Test our criteria logic
        shows_plant_interest = (is_plant_based == 'YES' or
                                'plant' in plant_evidence.lower() or
                                'vegan' in plant_evidence.lower() or
                                'vegetarian' in plant_evidence.lower() or
                                'healthy' in plant_evidence.lower())

        is_potential = (is_business_or_coach != 'YES' and
                        shows_plant_interest and
                        (is_target_female == 'YES' or is_target_male == 'YES') and
                        is_fake != 'YES')

        result = "✅ POTENTIAL CLIENT!" if (
            is_potential_client == 'YES' or is_potential) else "❌ Not a client"
        print(f"\n🎯 FINAL RESULT: {result}")
        print(f"💡 Reason: {client_reason}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    # Test with some regular profiles that might be potential clients
    # These are examples - you can replace with actual usernames
    test_accounts = [
        # Plant-based family account - might have followers who are potential clients
        "earthyandy",
        "fullyrawkristina",  # Raw vegan - followers might be clients
        # Add some regular people usernames here if you know them
    ]

    print(f"🧪 TESTING SMART LEAD FINDER AI WITH MORE GENEROUS CRITERIA")
    print(f"🎯 Goal: See if we can find potential clients with relaxed criteria")
    print(f"\n" + "="*60)

    for username in test_accounts:
        test_profile_analysis(username)
        print("\n" + "="*60 + "\n")
