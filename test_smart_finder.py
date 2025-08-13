#!/usr/bin/env python3
"""
Test Smart Lead Finder AI Analysis
Quick test to see if our AI prompt improvements work
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

    **Step 1: Initial Screening**
    - Is this a business, brand, or sales page? Look for terms like "shop", "official", "services", "sale", "brand".
    - Is this person a coach, trainer, or nutritionist? Look for "coach", "trainer", "PT", "nutritionist", client results.
    - If YES to either, this is NOT a potential client.

    **Step 2: Client Profile Analysis**
    - If the profile is for an individual, proceed with the following questions.

    **Step 3: Fake Account Check**
    - Does this look like a bot, fake, or inactive account? Look for: no profile picture, very few posts, a generic bio with spammy links, or a very high 'following' number with few followers. If so, it is likely NOT a potential client.

    **Questionnaire (Answer with YES or NO, and provide brief evidence for your choice):**

    1.  **IS_BUSINESS_OR_COACH:** Is this a business, brand, or another coach/trainer?
        - Answer: YES/NO - Evidence: [Provide reason, e.g., "Sells products," "Calls themselves a coach"]

    2.  **IS_PLANT_BASED:** Does this person seem to follow a plant-based or vegan lifestyle?
        - Look for: Vegan food, "vegan" in bio, plant-based hashtags or mentions.
        - Answer: YES/NO - Evidence: [Provide reason, e.g., "Bio says 'vegan'", "Photos of plant-based meals"]

    3.  **APPARENT_GENDER:** What is the apparent gender of the individual?
        - Answer: MALE/FEMALE/UNCLEAR - Evidence: [Briefly state reason, e.g., "Profile picture and name"]

    4.  **IS_TARGET_FEMALE:** If FEMALE, does she appear to be a middle-aged woman (approx. 35+) who is interested in fitness or weight loss?
        - Look for: Mature appearance, mentions of family/kids, fitness content (gym, workouts), or weight loss journey.
        - Answer: YES/NO/NOT_APPLICABLE - Evidence: [Provide reason, e.g., "Appears to be in her 40s and posts gym selfies", "Not applicable, gender is male"]

    5.  **IS_TARGET_MALE:** If MALE, does he appear to be overweight or someone who could benefit from weight loss guidance?
        - Look for: A physical appearance that suggests he is carrying extra weight and could be a good candidate for a weight loss program. Be objective and descriptive.
        - Answer: YES/NO/NOT_APPLICABLE - Evidence: [Provide reason, e.g., "Appears overweight in photos", "Not applicable, gender is female"]

    6.  **FINAL_VERDICT_POTENTIAL_CLIENT:** Based on the above, is this a potential client?
        - A potential client is an INDIVIDUAL (not a business/coach) who is PLANT-BASED and fits either the TARGET_FEMALE or TARGET_MALE criteria. The account must not appear to be fake or inactive.
        - Answer: YES/NO - Reason: [Summarize why they are or are not a potential client, e.g., "Yes, she is a plant-based woman interested in fitness", "No, this is a business account"]

    7.  **IS_FAKE_OR_INACTIVE:** Does this look like a bot, fake, or inactive account?
        - Look for: No profile pic, zero or very few posts, generic bio, high following count with low followers.
        - Answer: YES/NO - Evidence: [Provide reason, e.g., "Account has 0 posts and follows 5000 people"]

    **CRITICAL: If you cannot see clear details in the screenshot, say "Cannot determine clearly from screenshot" rather than "No evidence found".**

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
    print(f"🧪 TESTING PROFILE ANALYSIS: @{username}")

    driver = None
    try:
        # Setup driver
        service = webdriver.chrome.service.Service(
            executable_path=CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Navigate to profile (no login needed for public profiles)
        profile_url = f"https://www.instagram.com/{username}/"
        print(f"📱 Navigating to {profile_url}")
        driver.get(profile_url)
        time.sleep(5)

        # Take screenshot
        screenshot_data = driver.get_screenshot_as_base64()
        print(f"📸 Screenshot captured")

        # Get AI analysis
        prompt = get_screening_prompt(username)
        print(f"🤖 Analyzing with AI...")
        response = analyze_with_gemini(prompt, screenshot_data)

        if not response:
            print(f"❌ AI analysis failed")
            return

        response_text = response.text
        print(f"✅ AI Analysis Complete!")
        print(f"\n📋 FULL AI RESPONSE:")
        print(response_text)

        # Parse response
        def parse_line(key, text):
            match = re.search(
                rf'{key}:\s*(YES|NO|MALE|FEMALE|UNCLEAR|NOT_APPLICABLE)\s*-\s*(?:Evidence|Reason):\s*(.*?)(?=\n[A-Z_]+:|$)',
                text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).upper().strip(), match.group(2).strip()
            return None, "No evidence found"

        is_business_or_coach, business_evidence = parse_line(
            'IS_BUSINESS_OR_COACH', response_text)
        is_plant_based, plant_evidence = parse_line(
            'IS_PLANT_BASED', response_text)
        apparent_gender, gender_evidence = parse_line(
            'APPARENT_GENDER', response_text)
        is_target_female, female_evidence = parse_line(
            'IS_TARGET_FEMALE', response_text)
        is_target_male, male_evidence = parse_line(
            'IS_TARGET_MALE', response_text)
        is_potential_client, client_reason = parse_line(
            'FINAL_VERDICT_POTENTIAL_CLIENT', response_text)
        is_fake, fake_evidence = parse_line(
            'IS_FAKE_OR_INACTIVE', response_text)

        print(f"\n📊 PARSED RESULTS:")
        print(
            f"   🏢 Business/Coach: {'❌ YES' if is_business_or_coach == 'YES' else '✅ NO'} - {business_evidence}")
        print(
            f"   🌱 Plant-Based: {'✅ YES' if is_plant_based == 'YES' else '❌ NO'} - {plant_evidence}")
        print(f"   👤 Gender: {apparent_gender} - {gender_evidence}")
        print(
            f"   👩 Target Female: {'✅ YES' if is_target_female == 'YES' else '❌ NO/N/A'} - {female_evidence}")
        print(
            f"   👨 Target Male: {'✅ YES' if is_target_male == 'YES' else '❌ NO/N/A'} - {male_evidence}")
        print(
            f"   🤖 Fake/Inactive: {'❌ YES' if is_fake == 'YES' else '✅ NO'} - {fake_evidence}")
        print(
            f"   🎯 AI Final Verdict: {'✅ YES' if is_potential_client == 'YES' else '❌ NO'} - {client_reason}")

        # Test our criteria logic
        shows_plant_interest = (is_plant_based == 'YES' or
                                'plant' in plant_evidence.lower() or
                                'vegan' in plant_evidence.lower() or
                                'vegetarian' in plant_evidence.lower())

        is_potential = (is_business_or_coach != 'YES' and
                        shows_plant_interest and
                        (is_target_female == 'YES' or is_target_male == 'YES') and
                        is_fake != 'YES')

        print(f"\n🧮 OUR LOGIC RESULT:")
        print(
            f"   🌿 Shows plant interest: {'✅ YES' if shows_plant_interest else '❌ NO'}")
        print(
            f"   🎯 Would we classify as potential client: {'✅ YES' if is_potential else '❌ NO'}")

        if is_potential_client == 'YES' or is_potential:
            print(f"\n🎉 RESULT: POTENTIAL CLIENT FOUND!")
        else:
            print(f"\n❌ RESULT: Not a potential client")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    # Test with some known vegan accounts that should be potential clients
    test_accounts = [
        "nimai_delgado",      # Vegan bodybuilder - should be a male target
        "plantyou",           # Vegan recipe account - might be female target
        "pickuplimes",        # Vegan lifestyle - should be female target
    ]

    for username in test_accounts:
        test_profile_analysis(username)
        print("\n" + "="*80 + "\n")
