import argparse
import sys
import os
import time
import datetime
import json
import random
import pickle
import re
import traceback
import base64
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

# Gemini AI imports
import google.generativeai as genai
import google.api_core.exceptions

# Configure Gemini
GEMINI_API_KEY = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize all three Gemini models for fallback
gemini_models = [
    ('gemini-2.0-flash', genai.GenerativeModel('gemini-2.0-flash')),
    ('gemini-2.0-flash-lite', genai.GenerativeModel('gemini-2.0-flash-lite')),
    ('gemini-2.0-flash-thinking-exp-01-21',
     genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21'))
]

# Script configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMEDRIVER_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"

# SQLite database path
SQLITE_DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

# Instagram credentials for cocos_pt_studio account
USERNAME = "cocos_pt_studio"
PASSWORD = "Shannonb3"

# Target influencers to scrape followers from - HIGHEST PRIORITY
TARGET_INFLUENCERS = [
    'nimai_delgado',       # Vegan bodybuilder - good for male fitness clients
    'plantyou',            # Simple vegan recipes - broad audience
    'pickuplimes',         # Wholesome vegan lifestyle - good for women
    'earthyandy',          # Plant-based family - good for mothers
    'fullyrawkristina',    # Long-time raw vegan influencer
    'the_buddhist_chef',   # Mindful, simple veganism
    'vegan_bodybuilding',  # Community for vegan fitness
    # Shannon's current online clients - GOLD MINE for similar people
    'kristyleecoop',       # Shannon's online client
    'le_greenies',         # Shannon's online client
    'rebeccadangelo01',    # Shannon's online client
]

# Target hashtags for finding potential clients - PLANT-BASED FOCUSED
TARGET_HASHTAGS = [
    "veganrecipes", "plantbasedrecipes", "veganfood", "whatveganseat",
    "vegancommunity", "plantbasedcommunity", "veganlife", "plantbasedlifestyle",
    "veganweightloss", "plantbasedweightloss", "veganfitness", "plantbasedfitness",
    "vegetarianrecipes", "veganuk", "ukvegans"
]

# Local targeting for Bayside Gym - EXPANDED
LOCAL_BUSINESSES = [
    # Local businesses and venues
    'thehamptons.bakery',
    'recoverylab.hampton',
    'regenwellnesscentre',
    'yesfitnessvic',
    'hamptonsttraders',  # Hampton Street Traders Association
    'brightonbaths',
    'sandringhamyachtclub',
    'blackrockfc',
    'baysidecouncil',
    'hamptonpilates',
    'brightongrammar',
    'firbank_grammar',
    'mentonegirlsgrammar',
    'baysideshoppingcentre',
    'cheltenhamracecourse',
    'royalmelbourne_gc',
    'baysideafc',
    # Local gyms and fitness centers
    'anytimefitnessbrighton',
    'f45brighton',
    'baysidecrossfit',
    'plusfitnessmelbourne',
    'goodlifehealthclubs',
    'jettsfitnesshampton',
    'snap_fitness_brighton',
    'curves_brighton',
    'fernwoodfitness',
    'contourshampton',
    # Local health and wellness
    'baysidephysio',
    'hamptonwellnesscentre',
    'baysidechiropractic',
    'brightonbeachphysio',
    'recoverygurumelbourne',
    'baysideosteo',
    'hamptonmassage',
    # Shannon's current gym clients - GOLD MINE for local leads
    'payneinthenix',           # Shannon's gym client
    'simonetindallrealestate',  # Shannon's gym client
    # Local fitness influencers and PTs
    'melbournefitnessmum',
    'baysidebootcamp',
    'beachbodybrighton',
    'melbournept',
    'brightonfitness',
    'hamptonhealthclub',
    'baysidestrength',
    'coastalfitness',
    'southernyogacollective',
    'pilatespointbrighton'
]
LOCAL_HASHTAGS = [
    # Primary location tags
    "hamptonstreet", "baysidemelbourne", "hamptonvic", "brightonvic", "sandringhamvic", "melbournefitness",
    # Extended Bayside suburbs
    "mentone", "cheltenham", "highett", "moorabbin", "bentleigh", "bentleigheast", "carnegie", "ormond",
    "blackrock", "beaumaris", "cheltenhamvic", "parkdale", "mordialloc", "aspendale", "bonbeach",
    # Fitness and lifestyle hashtags with location
    "melbournegym", "melbournept", "melbournestrength", "melbournewellness", "melbournehealthyliving",
    "baysidelife", "baysidegym", "baysidehealth", "baysidewellness", "baysidestrength", "baysidebootcamp",
    "brightonbeach", "brightonbaths", "hamptonbeach", "sandringhambeach", "baysidebeaches",
    "melbournemums", "workingmummelbourne", "melbournemummy", "baysideparents", "schoolmums",
    # Local business and lifestyle
    "hamptonmarket", "brightonmarket", "baysidemarket", "localbusiness", "baysidebusiness",
    "southmelbourne", "portmelbourne", "albertpark", "southyarra", "prahran", "stkildaroad",
    # Fitness specific
    "strengthtrainingmelbourne", "weightlossmelbourne", "personaltrainermelbourne", "gymmelbourne",
    "fitnessmelbourne", "healthcoachmelbourne", "nutritionmelbourne", "wellnessmelbourne",
    "crossfitmelbourne", "pilatesmelbourne", "yogamelbourne", "bootcampmelbourne",
    # Women's fitness
    "mumsworkout", "mumsfitness", "workingmumfitness", "melbournemumlife", "strongmum",
    "fitnessmum", "healthymum", "activemum", "weighttrainingmum", "strengthmum"
]

# New Targeting Methods - Add URLs here
TARGET_POST_URLS = [
    # "https://www.instagram.com/p/C7_..." # Example: A post URL to scrape commenters from
]
TARGET_LOCATION_URLS = [
    # "https://www.instagram.com/explore/locations/212999119/london-united-kingdom/" # Example: A location URL to scrape posters from
]

# New target list for the liker scraping feature
TARGET_POSTS_FOR_LIKERS = [
    # "https://www.instagram.com/p/C8G..." # Add post URLs here to scrape their likers
]

# Criteria for identifying potential clients (less critical with new AI prompt)
CRITERIA_KEYWORDS = {
    'middle_aged_woman': ['mum', 'mom', 'over30', 'over40', 'over50', 'menopause', 'workingmum', 'fitmum'],
    'plant_based': ['vegan', 'plant-based', 'plantbased', 'vegetarian', 'plant powered'],
    'fitness': ['fitness', 'workout', 'exercise', 'gym', 'training', 'strength', 'fit', 'health', 'wellness'],
    'weight_loss': ['weight loss', 'lose weight', 'transformation', 'journey', 'diet', 'slimming']
}

LOCAL_CRITERIA_KEYWORDS = {
    'local': ['bayside', 'hampton', 'brighton', 'sandringham', 'melbourne'],
    'fitness': ['weight training', 'strength training', 'gym', 'fitness', 'workout', 'weights', 'lifting']
}

# Keywords to exclude (coaches/trainers/businesses)
EXCLUDE_KEYWORDS = [
    'coach', 'trainer', 'nutritionist', 'pt', 'personal trainer', 'fitness instructor',
    'wellness coach', 'health coach', 'life coach', 'nutrition coach', 'certified',
    'online coach', 'transformation coach', 'mindset coach', 'business', 'ceo',
    'founder', 'shop', 'sale', 'brand ambassador', 'store', 'official'
]

# Keywords that identify influencers/coaches whose followers we should mine
INFLUENCER_KEYWORDS = [
    'coach', 'trainer', 'nutritionist', 'pt', 'personal trainer', 'fitness instructor',
    'wellness coach', 'health coach', 'transformation coach', 'online coach',
    'certified trainer', 'fitness professional', 'plant based coach', 'vegan coach',
    'programs', 'clients', 'transformations', 'coaching', 'services'
]

# Chrome options
chrome_options = Options()
# Run in headless mode (no browser window)
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-plugins")
# Set window size for headless mode
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
chrome_options.add_experimental_option("detach", True)
chrome_options.add_experimental_option(
    "excludeSwitches", ["enable-automation", "enable-logging"])
chrome_options.add_experimental_option('useAutomationExtension', False)


def save_cookies(driver, username):
    """Save browser cookies to a file"""
    cookies_dir = os.path.join(SCRIPT_DIR, "cookies")
    os.makedirs(cookies_dir, exist_ok=True)
    cookies_file = os.path.join(cookies_dir, f"{username}_cookies.pkl")
    pickle.dump(driver.get_cookies(), open(cookies_file, "wb"))
    print("✅ Cookies saved successfully")


def load_cookies(driver, username):
    """Load saved cookies into browser session"""
    try:
        cookies_file = os.path.join(
            SCRIPT_DIR, "cookies", f"{username}_cookies.pkl")
        if os.path.exists(cookies_file):
            cookies = pickle.load(open(cookies_file, "rb"))
            driver.get("https://www.instagram.com")
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except:
                    continue
            print("✅ Cookies loaded successfully")
            return True
        return False
    except Exception as e:
        print(f"❌ Error loading cookies: {e}")
        return False


def check_login_status(driver):
    """Check if currently logged into Instagram"""
    try:
        # Give page time to load and stabilize
        time.sleep(2)
        current_url = driver.current_url.lower()
        print(f"   - Verifying login status at URL: {current_url}")

        if "login" in current_url or "challenge" in current_url:
            print("   - URL indicates not logged in (contains 'login' or 'challenge').")
            return False

        # Look for elements that only appear when logged in.
        # This is a more robust combination of checks.
        try:
            # Check 1: The user's own profile link in the main nav. Very reliable.
            profile_link_selector = f"a[href*='/{USERNAME}/']"
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, profile_link_selector))
            )
            print("   - Login check PASSED (found profile link).")
            return True
        except TimeoutException:
            print("   - Login check FAILED (did not find profile link).")
            pass  # Continue to the next check

        try:
            # Check 2: The "Home" icon SVG. Good fallback.
            home_icon_selector = "svg[aria-label*='Home']"
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, home_icon_selector))
            )
            print("   - Login check PASSED (found Home icon).")
            return True
        except TimeoutException:
            print("   - Login check FAILED (did not find Home icon).")
            pass

        # If both checks fail, we are not logged in.
        print("   - All login checks failed.")
        return False

    except Exception as e:
        print(f"❌ Error checking login status: {e}")
        return False


def login_to_instagram(driver, username, password):
    """Login to Instagram account with improved error handling and retries."""
    MAX_LOGIN_ATTEMPTS = 3
    for attempt in range(MAX_LOGIN_ATTEMPTS):
        print(
            f"\n=== Starting Instagram Login (Attempt {attempt + 1}/{MAX_LOGIN_ATTEMPTS}) ===")
        try:
            # Go to the login page clean
            driver.delete_all_cookies()
            driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(random.uniform(3, 5))

            # Execute stealth script
            stealth_script = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """
            driver.execute_script(stealth_script)

            # --- Input Credentials ---
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            for char in username:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.2))
            time.sleep(random.uniform(1, 2))

            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_field.clear()
            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.2))
            time.sleep(random.uniform(1, 2))

            # --- Click Login ---
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[type='submit']"))
            )
            login_button.click()
            print("   - Login button clicked. Waiting for page to load...")

            # --- Wait and Verify ---
            # Increased wait time for page transition after login attempt
            time.sleep(20)

            # Check for security challenge / suspicious login page
            page_title = driver.title.lower()
            page_source = driver.page_source.lower()
            if "challenge" in driver.current_url or "suspicious" in page_title or "verify" in page_title:
                print(
                    "   - ⚠️ SECURITY CHALLENGE DETECTED. Manual intervention is likely required.")
                print("   - Taking a screenshot for review: challenge_detected.png")
                driver.save_screenshot("challenge_detected.png")
                # Can't proceed automatically
                return False

            # Use the robust check function
            if check_login_status(driver):
                print("✅ Login successful!")
                save_cookies(driver, USERNAME)
                handle_post_login_popups(driver)
                return True
            else:
                print(
                    f"   - Login verification failed on attempt {attempt + 1}.")
                # Take a screenshot to debug why login might be failing
                screenshot_name = f"login_failed_attempt_{attempt + 1}.png"
                driver.save_screenshot(screenshot_name)
                print(f"   - Screenshot saved: {screenshot_name}")

        except Exception as e:
            print(
                f"❌ An exception occurred during login attempt {attempt + 1}: {e}")
            traceback.print_exc()
            # Take a screenshot on exception as well
            screenshot_name = f"login_exception_attempt_{attempt + 1}.png"
            driver.save_screenshot(screenshot_name)
            print(f"   - Screenshot saved: {screenshot_name}")
            time.sleep(5)  # Wait before next attempt

    print("❌ All login attempts failed.")
    return False


def handle_post_login_popups(driver):
    """Handle any popups that appear after login"""
    try:
        time.sleep(3)

        # Handle "Save Login Info" popup
        try:
            not_now_button = driver.find_element(
                By.XPATH, "//button[contains(text(), 'Not Now')]")
            not_now_button.click()
            time.sleep(2)
        except:
            pass

        # Handle notifications popup
        try:
            not_now_button = driver.find_element(
                By.XPATH, "//button[contains(text(), 'Not Now')]")
            not_now_button.click()
        except:
            pass

    except Exception as e:
        print(f"❌ Error handling popups: {e}")


def analyze_with_gemini(prompt, image_data=None, retry_with_fallback=True):
    """Analyze content with Gemini, falling back to alternate models if needed"""
    try:
        if image_data:
            contents = [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
            ]
        else:
            contents = prompt

        # Try each model in sequence until one works
        last_error = None
        for model_name, model in gemini_models:
            try:
                print(f"🤖 Trying model: {model_name}")
                response = model.generate_content(contents)
                print(f"✅ Successfully used {model_name}")
                return response
            except google.api_core.exceptions.ResourceExhausted as e:
                print(
                    f"⚠️ Rate limit hit for {model_name}, trying next model...")
                last_error = e
                continue
            except Exception as e:
                print(f"❌ Error with {model_name}: {e}")
                last_error = e
                continue

        # If we get here, all models failed
        if last_error:
            print(f"❌ All models failed. Last error: {str(last_error)}")
            raise last_error
        return None

    except Exception as e:
        print(f"❌ Error in Gemini analysis: {e}")
        return None


def get_screening_prompt(username, mode='online'):
    """Returns the appropriate Gemini screening prompt based on the search mode."""
    if mode == 'local':
        return f"""
        You are an expert Instagram analyst helping a local gym owner find new clients in the Bayside, Melbourne area.
        Your task is to analyze the profile of @{username} and determine if they are a potential local client.

        **Questionnaire (Answer with YES or NO, and provide brief evidence for your choice):**

        1.  **IS_LOCAL:** Does this person appear to live in or frequent the Bayside, Melbourne area (e.g., Hampton, Brighton, Sandringham)?
            - Look for: Location tags, mentions of local spots, Melbourne-specific content.
            - Answer: YES/NO - Evidence: [Provide reason, e.g., "Tagged a photo at Hampton Beach"]

        2.  **IS_TARGET_DEMOGRAPHIC:** Is this a middle-aged woman (approx. 35+)?
            - Look for: Mature appearance, mentions of being a mum, content aligning with that age group.
            - Answer: YES/NO - Evidence: [Provide reason, e.g., "Profile picture shows a woman in her 40s"]

        3.  **IS_ACTIVE_OR_HEALTH_CONSCIOUS:** Does she show interest in general fitness, an active lifestyle, health, or wellness?
            - Look for: Posts about exercise (any type), healthy eating, outdoor activities, active hobbies, self-care, healthy habits, or mentions of general fitness/health goals.
            - Answer: YES/NO - Evidence: [Provide reason, e.g., "Posts about daily walks," "Shares healthy recipes," "Mentions trying to eat better," "Photos show her participating in a community run."]

        4.  **IS_BUSINESS_OR_COACH:** Is this a business, brand, or another coach/trainer?
            - Answer: YES/NO - Evidence: [Provide reason, e.g., "This is an individual's personal page"]

        5.  **FINAL VERDICT - POTENTIAL_CLIENT:** Based on the above, is this a potential client?
            - A potential client MUST be a LOCAL, TARGET_DEMOGRAPHIC woman interested in WEIGHT TRAINING and NOT a business/coach.
            - Answer: YES/NO - Reason: [Summarize why they are or are not a potential client]

        6. **IS_FAKE_OR_INACTIVE:** Does this look like a bot, fake, or inactive account?
           - Look for: No profile pic, zero or very few posts, generic bio, high following count with low followers.
           - Answer: YES/NO - Evidence: [Provide reason, e.g., "Account has 0 posts and follows 5000 people"]

        **Provide your response in this EXACT format:**
        IS_LOCAL: [YES/NO] - Evidence: [reason]
        IS_TARGET_DEMOGRAPHIC: [YES/NO] - Evidence: [reason]
        IS_ACTIVE_OR_HEALTH_CONSCIOUS: [YES/NO] - Evidence: [reason]
        IS_BUSINESS_OR_COACH: [YES/NO] - Evidence: [reason]
        POTENTIAL_CLIENT: [YES/NO] - Reason: [reason]
        IS_FAKE_OR_INACTIVE: [YES/NO] - Evidence: [reason]
        """

    # Default to the 'online' prompt
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

    6.  **FINAL VERDICT - POTENTIAL_CLIENT:** Based on the above, is this a potential client?
        - A potential client is an INDIVIDUAL (not a business/coach) who is PLANT-BASED and fits either the TARGET_FEMALE or TARGET_MALE criteria. The account must not appear to be fake or inactive.
        - Answer: YES/NO - Reason: [Summarize why they are or are not a potential client, e.g., "Yes, she is a plant-based woman interested in fitness", "No, this is a business account"]

    7.  **IS_FAKE_OR_INACTIVE:** Does this look like a bot, fake, or inactive account?
        - Look for: No profile pic, zero or very few posts, generic bio, high following count with low followers.
        - Answer: YES/NO - Evidence: [Provide reason, e.g., "Account has 0 posts and follows 5000 people"]

    **Provide your response in this EXACT format:**
    IS_BUSINESS_OR_COACH: [YES/NO] - Evidence: [reason]
    IS_PLANT_BASED: [YES/NO] - Evidence: [reason]
    APPARENT_GENDER: [MALE/FEMALE/UNCLEAR] - Evidence: [reason]
    IS_TARGET_FEMALE: [YES/NO/NOT_APPLICABLE] - Evidence: [reason]
    IS_TARGET_MALE: [YES/NO/NOT_APPLICABLE] - Evidence: [reason]
    POTENTIAL_CLIENT: [YES/NO] - Reason: [reason]
    IS_FAKE_OR_INACTIVE: [YES/NO] - Evidence: [reason]
    """


def analyze_profile_overview(driver, username, mode='online'):
    """Stage 1: Take a screenshot of the profile and ask Gemini specific questions based on search mode."""
    results_dir = f"results/{username}"
    os.makedirs(results_dir, exist_ok=True)

    try:
        print(f"\n🔍 Stage 1: Profile Overview Analysis for {username}")

        # Navigate to profile
        profile_url = f"https://www.instagram.com/{username}/"
        print(f"📱 Navigating to {profile_url}")
        driver.get(profile_url)

        # Human-like delay
        human_delay = random.randint(3, 6)
        print(f"⏳ Human-like delay: {human_delay} seconds")
        time.sleep(human_delay)

        # Check for basic issues first
        try:
            # Rate limiting
            rate_limit_messages = driver.find_elements(
                By.XPATH, "//*[contains(text(), 'Try again later') or contains(text(), 'temporarily blocked') or contains(text(), 'unusual activity')]"
            )
            if rate_limit_messages:
                print(f"⚠️ RATE LIMITING DETECTED for {username}!")
                return None

            # Profile doesn't exist
            error_messages = driver.find_elements(
                By.XPATH, "//h2[contains(text(), 'Sorry, this page')]")
            if error_messages:
                print(f"❌ Profile {username} is not accessible")
                return None

            # Private profile
            private_indicators = driver.find_elements(
                By.XPATH, "//h2[contains(text(), 'Private')]")
            if private_indicators:
                print(f"🔒 Profile {username} is private")
                return None
        except:
            pass

        # Take screenshot of the profile overview
        profile_screenshot = f"{results_dir}/profile_overview.png"
        driver.save_screenshot(profile_screenshot)
        print(f"📸 Profile overview screenshot saved: {profile_screenshot}")

        # Read the screenshot
        with open(profile_screenshot, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # Get the correct prompt for the search mode
        screening_prompt = get_screening_prompt(username, mode)

        print(
            f"🤖 Asking Gemini specific screening questions (Mode: {mode})...")
        response = analyze_with_gemini(screening_prompt, image_data)

        if not response:
            print(f"❌ Failed to get Gemini response for {username}")
            return None

        response_text = response.text
        print(f"✅ Received screening response for {username}")
        print(f"📝 Response preview: {response_text[:200]}...")

        # Parse the responses
        screening_results = {}

        def parse_line(key, text):
            match = re.search(
                rf'{key}:\s*(YES|NO|MALE|FEMALE|UNCLEAR|NOT_APPLICABLE)\s*-\s*(?:Evidence|Reason):\s*(.*?)(?=\n[A-Z_]+:|$)', text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).upper().strip(), match.group(2).strip()
            return None, "No evidence found"

        # Parsing logic for both 'online' and 'local' modes
        if mode == 'online':
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
                'POTENTIAL_CLIENT', response_text)
            is_fake, fake_evidence = parse_line(
                'IS_FAKE_OR_INACTIVE', response_text)

            screening_results['is_business_or_coach'] = is_business_or_coach == 'YES'
            screening_results['business_evidence'] = business_evidence
            screening_results['is_plant_based'] = is_plant_based == 'YES'
            screening_results['plant_evidence'] = plant_evidence
            screening_results['apparent_gender'] = apparent_gender
            screening_results['gender_evidence'] = gender_evidence
            screening_results['is_target_female'] = is_target_female == 'YES'
            screening_results['female_evidence'] = female_evidence
            screening_results['is_target_male'] = is_target_male == 'YES'
            screening_results['male_evidence'] = male_evidence
            screening_results['is_potential_client'] = is_potential_client == 'YES' and is_fake != 'YES'
            screening_results['client_reason'] = client_reason
            screening_results['is_fake_or_inactive'] = is_fake == 'YES'
            screening_results['fake_evidence'] = fake_evidence

        elif mode == 'local':
            is_local, local_evidence = parse_line('IS_LOCAL', response_text)
            is_target_demographic, demo_evidence = parse_line(
                'IS_TARGET_DEMOGRAPHIC', response_text)
            is_interested, interest_evidence = parse_line(
                'IS_INTERESTED_IN_WEIGHT_TRAINING', response_text)
            is_business_or_coach, business_evidence = parse_line(
                'IS_BUSINESS_OR_COACH', response_text)
            is_potential_client, client_reason = parse_line(
                'POTENTIAL_CLIENT', response_text)
            is_fake, fake_evidence = parse_line(
                'IS_FAKE_OR_INACTIVE', response_text)

            screening_results['is_local'] = is_local == 'YES'
            screening_results['local_evidence'] = local_evidence
            screening_results['is_target_demographic'] = is_target_demographic == 'YES'
            screening_results['demo_evidence'] = demo_evidence
            screening_results['is_interested_in_weight_training'] = is_interested == 'YES'
            screening_results['interest_evidence'] = interest_evidence
            screening_results['is_business_or_coach'] = is_business_or_coach == 'YES'
            screening_results['business_evidence'] = business_evidence
            screening_results['is_potential_client'] = is_potential_client == 'YES' and is_fake != 'YES'
            screening_results['client_reason'] = client_reason
            screening_results['is_fake_or_inactive'] = is_fake == 'YES'
            screening_results['fake_evidence'] = fake_evidence

        # Log the results
        print(f"\n📊 SCREENING RESULTS for {username} (Mode: {mode}):")
        if mode == 'online':
            print(
                f"   - Business/Coach: {'❌ YES' if screening_results.get('is_business_or_coach') else '✅ NO'} - {screening_results.get('business_evidence')}")
            print(
                f"   - Plant-Based: {'✅ YES' if screening_results.get('is_plant_based') else '❌ NO'} - {screening_results.get('plant_evidence')}")
            print(
                f"   - Gender: {screening_results.get('apparent_gender')} - {screening_results.get('gender_evidence')}")
            print(
                f"   - Target Female: {'✅ YES' if screening_results.get('is_target_female') else '❌ NO'} - {screening_results.get('female_evidence')}")
            print(
                f"   - Target Male: {'✅ YES' if screening_results.get('is_target_male') else '❌ NO'} - {screening_results.get('male_evidence')}")
            print(
                f"   - 🤖 Fake/Inactive: {'❌ YES' if screening_results.get('is_fake_or_inactive') else '✅ NO'} - {screening_results.get('fake_evidence')}")
            print(
                f"   - 🎯 POTENTIAL CLIENT: {'✅ YES' if screening_results.get('is_potential_client') else '❌ NO'} - {screening_results.get('client_reason')}")
        elif mode == 'local':
            print(
                f"   - Is Local: {'✅ YES' if screening_results.get('is_local') else '❌ NO'} - {screening_results.get('local_evidence')}")
            print(
                f"   - Target Demo: {'✅ YES' if screening_results.get('is_target_demographic') else '❌ NO'} - {screening_results.get('demo_evidence')}")
            print(
                f"   - Weight Training Interest: {'✅ YES' if screening_results.get('is_interested_in_weight_training') else '❌ NO'} - {screening_results.get('interest_evidence')}")
            print(
                f"   - Business/Coach: {'❌ YES' if screening_results.get('is_business_or_coach') else '✅ NO'} - {screening_results.get('business_evidence')}")
            print(
                f"   - 🤖 Fake/Inactive: {'❌ YES' if screening_results.get('is_fake_or_inactive') else '✅ NO'} - {screening_results.get('fake_evidence')}")
            print(
                f"   - 🎯 POTENTIAL CLIENT: {'✅ YES' if screening_results.get('is_potential_client') else '❌ NO'} - {screening_results.get('client_reason')}")

        # Return results for further processing
        return screening_results

    except Exception as e:
        print(f"❌ Error in profile overview analysis for {username}: {e}")
        return None


def analyze_user_profile(driver, username, source_hashtag, source_type='hashtag', mode='online'):
    """
    Analyzes a user's profile using the efficient one-stage AI screening.
    This is the primary analysis function for any discovered user.
    """
    try:
        print(
            f"🕵️ Analyzing profile: @{username} (Source: {source_hashtag}, Mode: {mode})")

        # Perform the AI-driven screening
        screening_results = analyze_profile_overview(driver, username, mode)

        if not screening_results:
            print(
                f"⏭️ Skipping @{username} - profile screening failed or inaccessible.")
            return None, False

        is_potential = screening_results.get('is_potential_client', False)
        is_influencer = is_influencer_profile(screening_results)

        if is_potential:
            print(f"✅ POTENTIAL CLIENT FOUND: {username}")
            print(
                f"   Reason: {screening_results.get('client_reason', 'No reason specified')}")

            # Prepare data for saving
            client_data = {
                'username': username,
                'hashtag_found': source_hashtag,
                'analysis': {
                    'search_mode': mode,
                    'source_type': source_type,
                    'source_influencer': source_hashtag if source_type == 'follower' else None,
                    'screening_results': screening_results,
                    'conversation_topics': [
                        "Topic 1 - Ask about their plant-based journey",
                        "Topic 2 - Discuss their current fitness/health goals",
                        "Topic 3 - Explore challenges they face with their goals",
                        "Topic 4 - Talk about their favorite vegan meals or recipes"
                    ]
                },
                'coaching_score': 100,  # Binary score: 100 for a match, 0 otherwise
                'coaching_reasons': [screening_results.get('client_reason', 'AI screening passed')],
                'timestamp': datetime.datetime.now().isoformat()
            }
            return client_data, is_influencer
        else:
            print(f"❌ Not a potential client: {username}")
            print(
                f"   Reason: {screening_results.get('client_reason', 'AI screening failed')}")
            # Still return if they are an influencer, even if not a direct client
            return None, is_influencer

    except Exception as e:
        print(f"❌ Error analyzing profile @{username}: {e}")
        return None, False


def is_influencer_profile(screening_results):
    """Check if this profile is an influencer/coach based on screening results."""
    if not screening_results:
        return False

    # An influencer is a user who is a coach/business but also plant-based,
    # making their followers valuable targets.
    is_coach = screening_results.get('is_business_or_coach', False)
    is_plant_based = screening_results.get('is_plant_based', False)

    if is_coach and is_plant_based:
        print(
            f"🎯 INFLUENCER DETECTED: A plant-based coach/business. Their followers are valuable.")
        return True
    return False


def get_followers_from_profile(driver, username, max_followers=20, is_vegan_influencer=False):
    """Get followers from an influencer's profile with intelligent scaling"""
    try:
        # Scale up collection for vegan influencers
        if is_vegan_influencer:
            # At least 500 for vegan influencers
            max_followers = max(500, max_followers)
            print(f"🌱 VEGAN INFLUENCER DETECTED: @{username}")
            print(
                f"🚀 SCALING UP: Collecting {max_followers} followers for maximum reach!")
        else:
            print(f"👥 Mining followers from @{username}...")

        # Navigate to profile
        profile_url = f"https://www.instagram.com/{username}/"
        driver.get(profile_url)
        time.sleep(random.randint(3, 5))

        # Click followers link
        try:
            # Multiple selectors for followers link
            followers_selectors = [
                "//a[contains(@href, '/followers/')]",
                "//span[contains(text(), 'followers')]//parent::a",
                "[href*='/followers/']"
            ]

            followers_link = None
            for selector in followers_selectors:
                try:
                    if selector.startswith("//"):
                        followers_link = driver.find_element(
                            By.XPATH, selector)
                    else:
                        followers_link = driver.find_element(
                            By.CSS_SELECTOR, selector)
                    if followers_link:
                        break
                except:
                    continue

            if not followers_link:
                print(f"⚠️ Could not find followers link for @{username}")
                return []

            followers_link.click()
            time.sleep(random.randint(3, 5))

        except Exception as e:
            print(f"⚠️ Failed to click followers for @{username}: {e}")
            return []

        # Collect follower usernames with enhanced scaling
        followers = []
        scroll_attempts = 0
        # Scale scroll attempts for larger collections
        max_scroll_attempts = min(50, max(10, max_followers // 20))

        if is_vegan_influencer:
            print(
                f"⚡ Enhanced collection mode: Will scroll up to {max_scroll_attempts} times")

        while len(followers) < max_followers and scroll_attempts < max_scroll_attempts:
            try:
                # Find follower elements in the modal
                follower_selectors = [
                    "//div[contains(@class, '_aano')]//a[contains(@href, '/')]",
                    "//div[@role='dialog']//a[contains(@href, '/')]",
                    "//span[contains(@class, 'x1lliihq')]//a"
                ]

                found_elements = []
                for selector in follower_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        if elements:
                            found_elements = elements
                            break
                    except:
                        continue

                for element in found_elements:
                    try:
                        href = element.get_attribute('href')
                        if href and '/p/' not in href and '/reel/' not in href and '/tv/' not in href:
                            # Extract username from URL
                            if href.endswith('/'):
                                follower_username = href.split('/')[-2]
                            else:
                                follower_username = href.split('/')[-1]

                            if (follower_username and
                                follower_username not in followers and
                                follower_username != username and
                                    not follower_username.startswith('instagram')):
                                followers.append(follower_username)

                                # Progress reporting - more frequent for large collections
                                progress_interval = 10 if is_vegan_influencer else 5
                                if len(followers) % progress_interval == 0:
                                    progress = (len(followers) /
                                                max_followers) * 100
                                    print(
                                        f"  📊 Collected {len(followers)}/{max_followers} followers ({progress:.1f}%)...")

                        if len(followers) >= max_followers:
                            break

                    except Exception as e:
                        continue

                # Scroll down in the followers modal
                try:
                    # Find the scrollable element (followers modal)
                    scrollable_element = driver.find_element(
                        By.XPATH, "//div[@role='dialog']//div[contains(@style, 'overflow')]")
                    driver.execute_script(
                        "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_element)
                except:
                    # Fallback scroll method
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);")

                time.sleep(random.randint(2, 4))
                scroll_attempts += 1

            except Exception as e:
                print(f"⚠️ Error collecting followers: {e}")
                break

        # Close the followers modal
        try:
            close_button = driver.find_element(
                By.XPATH, "//button[@aria-label='Close']")
            close_button.click()
            time.sleep(2)
        except:
            # Press escape key as fallback
            try:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(2)
            except:
                pass

        print(f"✅ Collected {len(followers)} followers from @{username}")

        # Save follower list for batch processing if it's a large collection
        if len(followers) >= 100:
            save_follower_list_for_batch_processing(
                username, followers, is_vegan_influencer)

        return followers

    except Exception as e:
        print(f"❌ Failed to get followers from @{username}: {e}")
        return []


def save_follower_list_for_batch_processing(influencer_username, followers, is_vegan_influencer=False):
    """Save a large follower list for systematic batch processing"""
    try:
        # Create batch processing directory
        batch_dir = "batch_processing"
        os.makedirs(batch_dir, exist_ok=True)

        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{batch_dir}/{influencer_username}_{len(followers)}_followers_{timestamp}.json"

        batch_data = {
            "influencer_username": influencer_username,
            "is_vegan_influencer": is_vegan_influencer,
            "total_followers": len(followers),
            "followers": followers,
            "created_timestamp": datetime.datetime.now().isoformat(),
            "processed_count": 0,
            "last_processed_index": -1,
            "status": "pending"
        }

        with open(filename, 'w') as f:
            json.dump(batch_data, f, indent=2)

        print(
            f"💾 SAVED FOR BATCH PROCESSING: {len(followers)} followers from @{influencer_username}")
        print(f"   📄 File: {filename}")

        if is_vegan_influencer:
            print(
                f"🌱 VEGAN GOLDMINE: This list will be processed systematically for maximum leads!")

    except Exception as e:
        print(f"⚠️ Failed to save follower list: {e}")


def load_and_process_batch_followers(batch_file, driver, max_to_process=20):
    """Load and process followers from a saved batch file"""
    try:
        with open(batch_file, 'r') as f:
            batch_data = json.load(f)

        influencer = batch_data["influencer_username"]
        followers = batch_data["followers"]
        last_index = batch_data.get("last_processed_index", -1)
        total_followers = len(followers)

        print(f"\n🔄 RESUMING BATCH PROCESSING: @{influencer}")
        print(
            f"   📊 Progress: {last_index + 1}/{total_followers} followers processed")
        print(f"   🎯 Processing next {max_to_process} followers...")

        results = []
        start_index = last_index + 1
        end_index = min(start_index + max_to_process, total_followers)

        for i in range(start_index, end_index):
            follower = followers[i]
            print(f"\n🔍 [{i+1}/{total_followers}] Processing @{follower}...")

            result = analyze_follower_as_prospect(driver, follower, influencer)
            if result:
                results.append(result)
                print(f"✅ LEAD FOUND: @{follower}")

            # Update progress
            batch_data["last_processed_index"] = i
            batch_data["processed_count"] = i + 1

            # Save progress every 5 profiles
            if (i + 1) % 5 == 0:
                with open(batch_file, 'w') as f:
                    json.dump(batch_data, f, indent=2)
                print(f"💾 Progress saved: {i+1}/{total_followers}")

            # Rate limiting delay
            delay = random.randint(8, 15)
            print(f"⏳ Rate limit delay: {delay}s...")
            time.sleep(delay)

        # Mark as complete if finished
        if end_index >= total_followers:
            batch_data["status"] = "completed"
            print(
                f"🎉 BATCH COMPLETED: @{influencer} - All {total_followers} followers processed!")

        # Save final progress
        with open(batch_file, 'w') as f:
            json.dump(batch_data, f, indent=2)

        return results

    except Exception as e:
        print(f"❌ Error processing batch file {batch_file}: {e}")
        return []


def analyze_follower_as_prospect(driver, follower_username, source_influencer):
    """Analyze a follower as a potential prospect using two-stage approach"""
    try:
        print(
            f"🔍 Analyzing follower: @{follower_username} (from @{source_influencer})")

        # STAGE 1: Profile overview screening
        print(f"🔍 Stage 1: Profile screening for @{follower_username}")
        screening_results = analyze_profile_overview(driver, follower_username)

        if not screening_results:
            print(
                f"⏭️ Skipping @{follower_username} - profile screening failed")
            return None

        # Check if they passed the initial screening
        if screening_results.get('is_potential_client', False):
            print(f"✅ POTENTIAL CLIENT FOUND: {follower_username}")
            print(
                f"   Reason: {screening_results.get('client_reason', 'Unknown')}")

            # Prepare data for saving
            return {
                'username': follower_username,
                'analysis': {  # Create a simplified analysis object
                    'source_type': 'follower',
                    'source_influencer': source_influencer,
                    'hashtag_found': f"follower_of_{source_influencer}",
                    'screening_results': screening_results,
                    'conversation_topics': [
                        "Topic 1 - Ask about their plant-based journey",
                        "Topic 2 - Discuss their current fitness/health goals",
                        "Topic 3 - Explore challenges they face with their goals",
                        "Topic 4 - Talk about their favorite vegan meals or recipes"
                    ]
                },
                'score': 100,  # Score is now binary - they are a match or not
                'reasons': [screening_results.get('client_reason', 'Potential client based on AI screening')],
                'screening': screening_results
            }
        else:
            print(f"❌ NOT A POTENTIAL CLIENT: {follower_username}")
            print(
                f"   Reason: {screening_results.get('client_reason', 'Unknown')}")
            return None

    except Exception as e:
        print(f"❌ Error analyzing follower @{follower_username}: {e}")
        return None


def search_hashtag_for_clients(driver, hashtag, max_profiles, processed_usernames, num_clients_goal, current_client_count, mode='online', target_accounts_queue=None, discovered_influencers=None):
    """
    Search a specific hashtag and find potential clients.
    This version is revamped for robustness and better data collection.
    """
    print(f"\n🔍 === Revamped Hashtag Search: #{hashtag} ===")
    potential_clients = []

    try:
        # Navigate to hashtag page
        hashtag_url = f"https://www.instagram.com/explore/tags/{hashtag}/"
        driver.get(hashtag_url)
        time.sleep(random.randint(4, 6))

        # --- Smart Scrolling to gather more posts ---
        post_links = set()
        scroll_attempts = 0
        last_height = driver.execute_script(
            "return document.body.scrollHeight")

        while len(post_links) < 50 and scroll_attempts < 10:
            # Find links in the current view
            links_in_view = driver.find_elements(
                By.CSS_SELECTOR, "a[href*='/p/']")
            for link in links_in_view:
                href = link.get_attribute('href')
                if href:
                    post_links.add(href)

            # Scroll down
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            print(f"  ...scrolling, found {len(post_links)} posts so far...")
            time.sleep(random.uniform(2, 3.5))

            new_height = driver.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                break  # Reached the bottom
            last_height = new_height
            scroll_attempts += 1

        if not post_links:
            print(f"❌ No posts found for #{hashtag} after scrolling.")
            return potential_clients

        unique_post_urls = list(post_links)
        print(
            f"✅ Found {len(unique_post_urls)} unique posts to analyze from #{hashtag}.")

        for i, post_link in enumerate(unique_post_urls[:max_profiles]):
            if len(potential_clients) + current_client_count >= num_clients_goal:
                break

            print(
                f"\n📱 Processing post {i+1}/{min(len(unique_post_urls), max_profiles)} from #{hashtag}")
            try:
                # --- Resilient Username Extraction ---
                username = None
                driver.get(post_link)
                time.sleep(random.randint(4, 7))

                try:
                    # Method 1: Primary selector (fastest)
                    header_link = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//header//a[contains(@href, '/')]"))
                    )
                    href = header_link.get_attribute('href')
                    username = href.rstrip('/').split('/')[-1]
                    print(
                        f"   - Username found with primary selector: @{username}")

                except TimeoutException:
                    # Method 2: Fallback selector (slower but more specific)
                    print("   - Primary selector failed. Trying fallback...")
                    try:
                        user_link = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "span > a[role='link']"))
                        )
                        href = user_link.get_attribute('href')
                        username = href.rstrip('/').split('/')[-1]
                        print(
                            f"   - Username found with fallback selector: @{username}")
                    except TimeoutException:
                        # Method 3: Regex on page source (most resilient)
                        print(
                            "   - Fallback selector failed. Trying page source regex...")
                        page_source = driver.page_source
                        match = re.search(
                            r'"owner":{"username":"([^"]+)"', page_source)
                        if match:
                            username = match.group(1)
                            print(
                                f"   - Username found with page source regex: @{username}")
                        else:
                            print(
                                f"   - All username extraction methods failed for this post.")
                            continue

                if not username or username in processed_usernames:
                    if username:
                        print(f"⏭️ Skipping @{username}, already processed.")
                    continue

                processed_usernames.add(username)

                # Analyze the user's profile
                client_data, is_influencer = analyze_user_profile(
                    driver, username, source_hashtag=hashtag, mode=mode)

                if client_data:
                    potential_clients.append(client_data)
                    save_lead_to_database(client_data)
                    print(
                        f"⭐ Found client #{len(potential_clients) + current_client_count}! Saved @{client_data['username']} to database.")

                if is_influencer and username not in discovered_influencers:
                    print(
                        f"発見 (Discovery) ==> Found new influencer @{username} from hashtag #{hashtag}.")
                    print(f"   - Adding to the front of the follower scraping queue.")
                    # Add to the front of the queue to prioritize them
                    target_accounts_queue.insert(0, username)
                    discovered_influencers.add(username)

                time.sleep(random.randint(8, 15))

            except Exception as e:
                print(f"❌ Error processing post {post_link}: {e}")
                continue

    except Exception as e:
        print(f"❌ Error searching hashtag #{hashtag}: {e}")

    return potential_clients


def create_leads_table():
    """Create the new_leads table if it doesn't exist"""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS new_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashtag_found TEXT,
                coaching_score INTEGER,
                coaching_reasons TEXT,
                posts_analyzed INTEGER,
                interests TEXT,
                lifestyle_indicators TEXT,
                recent_activities TEXT,
                conversation_topics TEXT,
                post_summaries TEXT,
                analysis_data TEXT,
                timestamp TEXT,
                status TEXT DEFAULT 'new',
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Created new_leads table")
        return True

    except Exception as e:
        print(f"❌ Error creating leads table: {e}")
        return False


def save_lead_to_database(client_data):
    """Save a single potential client to the database"""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Extract data
        username = client_data['username']
        hashtag = client_data['hashtag_found']
        score = client_data['coaching_score']
        reasons = json.dumps(client_data['coaching_reasons'])
        analysis = client_data['analysis']

        # Insert or update the lead
        cursor.execute('''
            INSERT OR REPLACE INTO new_leads
            (username, hashtag_found, coaching_score, coaching_reasons,
             posts_analyzed, interests, lifestyle_indicators, recent_activities,
             conversation_topics, post_summaries, analysis_data, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            username,
            hashtag,
            score,
            reasons,
            analysis.get('posts_analyzed', 0),
            json.dumps(analysis.get('interests', [])),
            json.dumps(analysis.get('lifestyle_indicators', [])),
            json.dumps(analysis.get('recent_activities', [])),
            json.dumps(analysis.get('conversation_topics', [])),
            json.dumps(analysis.get('post_summaries', [])),
            json.dumps(analysis),
            client_data['timestamp']
        ))

        conn.commit()
        conn.close()
        print(f"✅ Saved lead {username} to database")
        return True

    except Exception as e:
        print(f"❌ Error saving lead {username}: {e}")
        return False


def save_results(all_potential_clients):
    """Save results to both database and JSON files"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create the leads table
    create_leads_table()

    # Save to database
    print(f"\n💾 Saving {len(all_potential_clients)} leads to database...")
    saved_count = 0
    for client in all_potential_clients:
        if save_lead_to_database(client):
            saved_count += 1

    print(
        f"✅ Saved {saved_count}/{len(all_potential_clients)} leads to database")

    # Also save to JSON file (backup)
    filename = f"potential_clients_{timestamp}.json"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_potential_clients, f, indent=2, ensure_ascii=False)
        print(f"✅ Results saved to {filename}")

        # Also save a summary
        summary_filename = f"client_summary_{timestamp}.txt"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write(f"POTENTIAL CLIENTS FOUND: {len(all_potential_clients)}\n")
            f.write(
                f"Search completed: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            for i, client in enumerate(all_potential_clients, 1):
                f.write(
                    f"{i}. @{client['username']} (Score: {client['coaching_score']}/100)\n")
                f.write(f"   Found via: #{client['hashtag_found']}\n")
                f.write(
                    f"   Reasons: {', '.join(client['coaching_reasons'][:3])}\n")
                f.write(
                    f"   Topics: {len(client['analysis'].get('conversation_topics', []))} conversation starters\n\n")

        print(f"✅ Summary saved to {summary_filename}")

    except Exception as e:
        print(f"❌ Error saving results: {e}")


def process_batch_mode(batch_file, batch_size):
    """Process a saved batch file of followers"""
    driver = None
    try:
        print(f"\n🔄 BATCH PROCESSING MODE")
        print(f"📄 File: {batch_file}")
        print(f"📊 Batch size: {batch_size} followers")

        # Initialize WebDriver
        print(f"\n🚗 Starting ChromeDriver...")
        service = webdriver.chrome.service.Service(
            executable_path=CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Login to Instagram
        if not login_to_instagram(driver, USERNAME, PASSWORD):
            print("❌ Failed to login to Instagram")
            return

        print("✅ Successfully logged into Instagram")

        # Process the batch file
        results = load_and_process_batch_followers(
            batch_file, driver, batch_size)

        print(f"\n🎉 BATCH PROCESSING COMPLETE")
        print(f"✅ Found {len(results)} potential clients in this batch")

        if results:
            save_results(results)

    except Exception as e:
        print(f"❌ Error in batch processing: {e}")
        traceback.print_exc()
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def main():
    """Main function to find potential clients"""
    print("--- SCRIPT START ---")  # Execution trace
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Find potential Instagram clients for fitness coaching.')
    parser.add_argument('--search-mode', type=str, default='online', choices=['online', 'local'],
                        help='The search mode: "online" for vegan clients, "local" for Bayside gym clients.')
    parser.add_argument('--num-clients', type=int, default=100,
                        help='The target number of potential clients to find.')
    parser.add_argument('--max-followers-per-influencer', type=int, default=200,
                        help='Max followers to scrape from each influencer/business profile.')
    parser.add_argument('--batch-file', type=str,
                        help='Process a saved batch file instead of searching hashtags')
    parser.add_argument('--batch-size', type=int, default=20,
                        help='Number of followers to process from batch file')

    args = parser.parse_args()
    print(f"--- ARGS PARSED: {args} ---")  # Execution trace

    print(
        f"🚀 === Instagram PREMIUM Client Finder v2.1 (Mode: {args.search_mode.upper()}) ===")
    print(f"🎯 Target: Find {args.num_clients} potential clients.")

    # DEFAULT STRATEGY: Network exploration first, then traditional methods
    print("🌐 SMART STRATEGY: Network exploration first, then traditional methods!")
    print("🔗 Phase 1: Explore followers of accounts you've already followed")
    print("🎯 Phase 2+: Fall back to influencers, hashtags, and posts as needed")

    if args.search_mode == 'online':
        target_accounts = TARGET_INFLUENCERS
        target_hashtags = TARGET_HASHTAGS
    else:  # local mode
        target_accounts = LOCAL_BUSINESSES
        target_hashtags = LOCAL_HASHTAGS

    if args.batch_file:
        print(f"🔄 BATCH MODE: Processing {args.batch_file}")
        # Note: Batch mode is not the primary focus of this refactor
        process_batch_mode(args.batch_file, args.batch_size)
        return

    print("🔍 DISCOVERY MODE: Searching for new leads...")

    all_potential_clients = []
    processed_usernames = set()
    driver = None  # Initialize driver to None
    discovered_influencers = set()  # Keep track of influencers found on the fly

    # Network-first strategy: Start with empty traditional queues
    # Traditional methods will be activated only as fallbacks
    target_accounts_queue = []  # Will be populated only if network exploration needs help
    target_hashtags_queue = []  # Will be populated only if network exploration needs help
    target_posts_queue = []     # Will be populated only if network exploration needs help
    # Will be populated only if network exploration needs help
    target_locations_queue = []
    # Will be populated only if network exploration needs help
    target_posts_for_likers_queue = []

    # Keep the original lists for fallback activation
    original_target_accounts = list(target_accounts)
    original_target_hashtags = list(target_hashtags)
    original_target_posts = list(TARGET_POST_URLS)
    original_target_locations = list(TARGET_LOCATION_URLS)
    original_target_posts_for_likers = list(TARGET_POSTS_FOR_LIKERS)

    # --- Main Persistent Loop ---
    print("--- ENTERING MAIN LOOP ---")  # Execution trace
    while len(all_potential_clients) < args.num_clients:
        try:
            # Execution trace
            print(
                f"--- LOOP ITERATION: {len(all_potential_clients)}/{args.num_clients} clients found ---")
            # --- Initialize and Login if driver is not active ---
            if not driver or not is_driver_active(driver):
                print("\n🚗 WebDriver is not active. Initializing new session...")
                # Quit previous driver if it exists
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass

                service = webdriver.chrome.service.Service(
                    executable_path=CHROMEDRIVER_PATH)
                driver = webdriver.Chrome(
                    service=service, options=chrome_options)

                # Load previously analyzed usernames from database to avoid duplicates
                try:
                    conn = sqlite3.connect(SQLITE_DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("SELECT username FROM new_leads")
                    existing_usernames = {row[0] for row in cursor.fetchall()}
                    processed_usernames.update(existing_usernames)
                    print(
                        f"📚 Loaded {len(existing_usernames)} previously processed usernames from the database.")
                    conn.close()
                except Exception as e:
                    print(
                        f"⚠️ Could not load existing usernames from database: {e}")

                if not login_to_instagram(driver, USERNAME, PASSWORD):
                    print(
                        "❌ Failed to login to Instagram. Waiting 5 minutes before retrying.")
                    time.sleep(300)
                    continue  # Restart the loop to try again

                print("✅ Successfully logged into Instagram.")

            # --- Phase 0: NETWORK EXPLORATION (Default Primary Strategy) ---
            if len(all_potential_clients) == 0:
                print("\n--- Phase 0: NETWORK EXPLORATION (Primary Strategy) ---")
                print("🌐 Starting with smart network exploration...")
                print("🔗 Leveraging followers of accounts you've already followed")

                priority_network_clients = smart_network_exploration(
                    driver, processed_usernames, args.num_clients,
                    len(all_potential_clients), mode=args.search_mode
                )

                if priority_network_clients:
                    print(
                        f"🎉 NETWORK SUCCESS! Found {len(priority_network_clients)} clients from your network!")

                    # Add to our results
                    for client in priority_network_clients:
                        if client['username'] not in processed_usernames:
                            all_potential_clients.append(client)
                            processed_usernames.add(client['username'])

                    print(
                        f"📊 Network exploration progress: {len(all_potential_clients)}/{args.num_clients} clients")

                    if len(all_potential_clients) >= args.num_clients:
                        print("🏆 Target achieved through network exploration alone!")
                        break
                    else:
                        print(
                            f"📈 Great start! Need {args.num_clients - len(all_potential_clients)} more clients.")
                        print(
                            "🔄 Activating traditional methods to reach full target...")

                        # NOW activate traditional methods as supplementary
                        if not target_accounts_queue:  # Only populate if not already done
                            # Start with top 5 accounts
                            target_accounts_queue.extend(
                                original_target_accounts[:5])
                            # Start with top 3 hashtags
                            target_hashtags_queue.extend(
                                original_target_hashtags[:3])
                            print(
                                f"🎯 Activated {len(target_accounts_queue)} influencer accounts and {len(target_hashtags_queue)} hashtags as supplements")
                else:
                    print("⚠️ Initial network exploration found no new leads.")
                    print(
                        "🔄 Activating traditional influencer and hashtag methods...")

                    # Activate traditional methods as primary fallback
                    target_accounts_queue.extend(original_target_accounts)
                    target_hashtags_queue.extend(original_target_hashtags)
                    target_posts_queue.extend(original_target_posts)
                    target_locations_queue.extend(original_target_locations)
                    target_posts_for_likers_queue.extend(
                        original_target_posts_for_likers)
                    print(
                        f"🎯 Activated ALL traditional methods: {len(target_accounts_queue)} accounts, {len(target_hashtags_queue)} hashtags, {len(target_posts_queue)} posts")

                # Brief pause before continuing to traditional methods
                print("⏳ Brief pause before continuing exploration...")
                time.sleep(random.randint(120, 240))  # 2-4 minute pause

            # --- New Phase 0: MINE POST LIKERS ---
            if target_posts_for_likers_queue:
                print(
                    f"\n--- Phase L: Mining Post Likers from {len(target_posts_for_likers_queue)} Target Posts ---")
                post_to_process = target_posts_for_likers_queue.pop(0)

                print(f"\n✨ Targeting post for likers: {post_to_process}")
                likers = get_users_from_likes(
                    driver, post_to_process, max_users=50)  # Get 50 likers per post

                if likers:
                    print(
                        f"   - Analyzing {len(likers)} likers from the post...")
                    for user_username in likers:
                        if len(all_potential_clients) >= args.num_clients:
                            break
                        if user_username in processed_usernames:
                            continue
                        processed_usernames.add(user_username)

                        client_data, _ = analyze_user_profile(
                            driver, user_username, source_hashtag=f"liker_of_{post_to_process.split('/')[-2]}", source_type='liker', mode=args.search_mode)
                        if client_data:
                            all_potential_clients.append(client_data)
                            save_lead_to_database(client_data)
                            print(
                                f"⭐ Found client #{len(all_potential_clients)}/{args.num_clients}! Saved @{client_data['username']} to database.")

                        time.sleep(random.randint(5, 12))

                if len(all_potential_clients) >= args.num_clients:
                    break

            # --- Phase 1: SCRAPE FOLLOWERS ---
            if target_accounts_queue:
                print(
                    f"\n--- Phase 1: Scraping Followers from {len(target_accounts_queue)} Target Accounts ---")
                account_to_process = target_accounts_queue.pop(0)

                print(f"\n✨ Targeting account: @{account_to_process}")
                followers = get_followers_from_profile(
                    driver, account_to_process, max_followers=args.max_followers_per_influencer)

                if followers:
                    print(
                        f" analyzing {len(followers)} followers of @{account_to_process}...")
                    for follower_username in followers:
                        if len(all_potential_clients) >= args.num_clients:
                            break
                        if follower_username in processed_usernames:
                            continue
                        processed_usernames.add(follower_username)

                        client_data, _ = analyze_user_profile(
                            driver, follower_username, source_hashtag=f"follower_of_{account_to_process}", source_type='follower', mode=args.search_mode)
                        if client_data:
                            all_potential_clients.append(client_data)
                            save_lead_to_database(client_data)
                            print(
                                f"⭐ Found client #{len(all_potential_clients)}/{args.num_clients}! Saved @{client_data['username']} to database.")

                        time.sleep(random.randint(5, 12))

                if len(all_potential_clients) >= args.num_clients:
                    break

            # --- Phase 2: MINE COMMENT SECTIONS ---
            if target_posts_queue:
                print(
                    f"\n--- Phase 2: Mining Comment Sections from {len(target_posts_queue)} Target Posts ---")
                post_to_process = target_posts_queue.pop(0)
                # ... (Implementation similar to follower scraping)
                if len(all_potential_clients) >= args.num_clients:
                    break

            # --- Phase 3: MINE LOCATION PAGES ---
            if args.search_mode == 'local' and target_locations_queue:
                print(
                    f"\n--- Phase 3: Mining Location Pages from {len(target_locations_queue)} Targets ---")
                location_to_process = target_locations_queue.pop(0)
                # ... (Implementation similar to follower scraping)
                if len(all_potential_clients) >= args.num_clients:
                    break

            # --- Phase 4: SEARCH HASHTAGS ---
            if target_hashtags_queue:
                print(
                    f"\n--- Phase 4: Searching Hashtags from a queue of {len(target_hashtags_queue)} ---")
                hashtag_to_process = target_hashtags_queue.pop(0)

                potential_clients_from_hashtag = search_hashtag_for_clients(
                    driver, hashtag_to_process, 20, processed_usernames, args.num_clients, len(all_potential_clients), mode=args.search_mode, target_accounts_queue=target_accounts_queue, discovered_influencers=discovered_influencers)

                for client in potential_clients_from_hashtag:
                    if client['username'] not in processed_usernames:
                        all_potential_clients.append(client)
                        processed_usernames.add(client['username'])

                if len(all_potential_clients) >= args.num_clients:
                    break

            # --- Phase 5: ADVANCED NETWORK EXPLORATION ---
            # Continue network exploration when traditional methods are running low
            if (len(all_potential_clients) >= 10 and len(all_potential_clients) < args.num_clients * 0.8 and
                    not target_accounts_queue and len(target_hashtags_queue) <= 2):

                print(f"\n--- Phase 5: ADVANCED NETWORK EXPLORATION ---")
                print(
                    f"🌱 Current progress: {len(all_potential_clients)}/{args.num_clients} clients")
                print(
                    "🚀 Diving deeper into your network for high-quality leads...")

                # Get a focused network exploration (smaller batch, different angles)
                focused_network_clients = search_followers_of_followed_accounts(
                    driver, processed_usernames, args.num_clients,
                    len(all_potential_clients), mode=args.search_mode
                )

                if focused_network_clients:
                    print(
                        f"🎯 ADVANCED NETWORK SUCCESS! Found {len(focused_network_clients)} additional clients!")

                    # Add to our results
                    for client in focused_network_clients:
                        if client['username'] not in processed_usernames:
                            all_potential_clients.append(client)
                            processed_usernames.add(client['username'])

                    print(
                        f"📈 Updated progress: {len(all_potential_clients)}/{args.num_clients} clients")

                    if len(all_potential_clients) >= args.num_clients:
                        break

                # Brief pause to appear human
                time.sleep(random.randint(120, 180))  # 2-3 minute pause

            # --- Check if all queues are empty ---
            if not target_accounts_queue and not target_posts_queue and not target_locations_queue and not target_hashtags_queue and not target_posts_for_likers_queue:
                print("\n✅ All initial targets have been processed.")

                # --- FINAL PHASE: ULTIMATE NETWORK EXPLORATION ---
                print("🚀 FINAL PHASE: ULTIMATE NETWORK EXPLORATION!")
                print("🌱 Deep dive into your followed accounts network...")

                # Try ultimate network exploration strategy first (most effective)
                network_clients = smart_network_exploration(
                    driver, processed_usernames, args.num_clients,
                    len(all_potential_clients), mode=args.search_mode
                )

                if network_clients:
                    print(
                        f"🎉 ULTIMATE NETWORK SUCCESS! Found {len(network_clients)} additional clients!")

                    # Add network clients to our results
                    for client in network_clients:
                        if client['username'] not in processed_usernames:
                            all_potential_clients.append(client)
                            processed_usernames.add(client['username'])

                    # Continue the loop to check if we've reached our goal
                    if len(all_potential_clients) >= args.num_clients:
                        print(
                            f"🏆 TARGET ACHIEVED! Found {len(all_potential_clients)} total clients!")
                        break

                    # Pause to appear human before continuing
                    print("⏳ Brief pause before continuing exploration...")
                    time.sleep(300)  # 5 minute pause

                    # If we still need more, activate more traditional methods
                    if len(all_potential_clients) < args.num_clients:
                        remaining_accounts = [acc for acc in original_target_accounts if acc not in [
                            q for q in target_accounts_queue]]
                        if remaining_accounts:
                            print(
                                f"🔄 Activating {len(remaining_accounts[:3])} additional influencer accounts...")
                            target_accounts_queue.extend(
                                remaining_accounts[:3])

                        # Add discovered influencers if any
                        if discovered_influencers:
                            print(
                                f"🔄 Adding {len(discovered_influencers)} newly discovered influencers...")
                            target_accounts_queue.extend(
                                list(discovered_influencers)[:5])
                            discovered_influencers.clear()

                    continue  # Continue the main loop with refreshed options

                # --- Last Resort: AI hashtag generation (only if all network exploration fails) ---
                print(
                    "🧠 All network exploration complete. Trying AI hashtag generation as final backup...")

                new_hashtags = generate_new_hashtags(
                    driver, list(original_target_hashtags))  # Use original hashtags
                if new_hashtags:
                    print(
                        f"📱 Generated {len(new_hashtags)} new hashtags as last resort...")
                    target_hashtags_queue.extend(new_hashtags)
                    print("⏳ Brief pause before trying new hashtags...")
                    time.sleep(300)  # 5 minute pause
                else:
                    print("⚠️ All exploration methods exhausted. Concluding search.")
                    print(
                        f"🎯 Final result: {len(all_potential_clients)} potential clients found!")
                    break  # Break the while loop if no new sources can be found

        except WebDriverException as e:
            print(f"💥 WebDriver Exception occurred: {e}")
            print("   - The browser session may have crashed or been disconnected.")
            print("   - The script will attempt to restart the browser and re-login.")
            driver = None  # Reset driver to force re-initialization
            time.sleep(60)  # Wait a minute before restarting
        except Exception as e:
            print(f"❌ A fatal error occurred in the main loop: {e}")
            traceback.print_exc()
            break  # Exit on other fatal errors

    # --- End of Main Loop ---
    print("--- EXITED MAIN LOOP ---")  # Execution trace
    if driver:
        try:
            driver.quit()
            print("\n✅ WebDriver closed.")
        except Exception as e:
            print(f"⚠️ Error closing WebDriver: {e}")

    # Final summary
    print(f"\n🎉 === SEARCH COMPLETE ===")
    print(f"🎯 Total potential clients found: {len(all_potential_clients)}")

    if all_potential_clients:
        # Show top results
        print(f"\n🏆 TOP 5 POTENTIAL CLIENTS:")
        sorted_clients = sorted(all_potential_clients,
                                key=lambda x: x['coaching_score'], reverse=True)

        for i, client in enumerate(sorted_clients[:5], 1):
            print(
                f"{i:2d}. @{client['username']} (Found via: {client['hashtag_found']})")
            print(f"    Reason: {', '.join(client['coaching_reasons'])}")

    else:
        print("❌ No potential clients were found matching the criteria.")

    print("\n✅ Analysis complete!")
    print("--- SCRIPT END ---")  # Execution trace


def is_driver_active(driver):
    """Checks if the WebDriver session is still active."""
    try:
        # A simple command to check session. Accessing title is lightweight.
        _ = driver.title
        return True
    except WebDriverException:
        return False


def get_users_from_comments(driver, post_url):
    """Scrapes all unique usernames from the comment section of a given Instagram post."""
    print(f"\n💬 Mining comment section of: {post_url}")
    usernames = set()
    try:
        driver.get(post_url)
        time.sleep(random.randint(3, 5))

        # Click the "view all comments" button if it exists
        try:
            view_all_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(., 'View all')] | //div[contains(text(), 'View all')]")))
            view_all_button.click()
            time.sleep(2)
        except TimeoutException:
            pass  # Already on the comments page or no button present

        # Scroll down to load more comments
        scroll_attempts = 0
        last_height = driver.execute_script(
            "return document.body.scrollHeight")
        while scroll_attempts < 15:  # Scroll up to 15 times
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1.5, 2.5))
            new_height = driver.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1

        # Scrape usernames from comment links
        commenter_links = driver.find_elements(
            By.XPATH, "//div[contains(@class, 'C4VMK')]//a[@role='link']")
        for link in commenter_links:
            href = link.get_attribute('href')
            if href and 'instagram.com/' in href:
                username = href.split('.com/')[1].split('/')[0]
                if username:
                    usernames.add(username)

        print(f"✅ Found {len(usernames)} unique commenters.")
        return list(usernames)

    except Exception as e:
        print(f"❌ Error scraping comments from {post_url}: {e}")
        return list(usernames)


def get_users_from_location_page(driver, location_url):
    """Scrapes usernames from the 'recent' posts on a location page."""
    print(f"\n📍 Mining location page: {location_url}")
    usernames = set()
    try:
        driver.get(location_url)
        time.sleep(random.randint(4, 6))

        # Scroll down to load more posts
        scroll_attempts = 0
        last_height = driver.execute_script(
            "return document.body.scrollHeight")
        while scroll_attempts < 10:  # Scroll up to 10 times for a good variety
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 3))
            new_height = driver.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1

        # Find all post links on the page
        post_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
        if not post_links:
            print("⚠️ No posts found on this location page.")
            return []

        unique_post_urls = list(dict.fromkeys(
            [link.get_attribute('href') for link in post_links]))
        print(f"Found {len(unique_post_urls)} posts to analyze for usernames.")

        # Visit each post to get the username (more reliable than trying to get it from the grid)
        # Limit to 25 to be efficient
        for i, post_url in enumerate(unique_post_urls[:25]):
            try:
                driver.get(post_url)
                time.sleep(random.randint(2, 4))
                header_link = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//header//a[contains(@href, '/')]"))
                )
                href = header_link.get_attribute('href')
                username = href.rstrip('/').split('/')[-1]
                if username:
                    usernames.add(username)
                    print(
                        f"  [{i+1}/{len(unique_post_urls)}] Found user: @{username}")
            except Exception as e:
                print(f"  Could not get username from post {post_url}: {e}")
                continue

        print(f"✅ Found {len(usernames)} unique users from the location page.")
        return list(usernames)

    except Exception as e:
        print(f"❌ Error scraping location page {location_url}: {e}")
        return list(usernames)


def generate_new_hashtags(driver, existing_hashtags):
    """Uses Gemini to generate new, related hashtags to expand the search."""
    print("\n🧠 AI is generating new hashtags to expand the search...")
    try:
        prompt = f"""
        You are an expert Instagram marketing assistant.
        Based on the following list of hashtags, generate 10 new, related, and popular hashtags that would be used by a similar audience.
        Avoid duplicating any hashtags from the provided list.

        Existing Hashtags: {', '.join(existing_hashtags)}

        Provide ONLY a comma-separated list of the new hashtags, without any additional text or formatting.
        For example: hashtag1,hashtag2,hashtag3
        """

        # Using the text-only model is faster and cheaper for this task
        text_model = genai.GenerativeModel('gemini-1.5-flash')
        response = text_model.generate_content(prompt)

        new_hashtags = [h.strip().replace('#', '')
                        for h in response.text.split(',')]

        # Filter out any duplicates or empty strings
        unique_new = [
            h for h in new_hashtags if h and h not in existing_hashtags]

        if unique_new:
            print(
                f"✨ Generated {len(unique_new)} new hashtags: {', '.join(unique_new)}")
            return unique_new
        else:
            print("⚠️ AI failed to generate unique new hashtags.")
            return []

    except Exception as e:
        print(f"❌ Error generating new hashtags with AI: {e}")
        return []


def get_users_from_likes(driver, post_url, max_users=50):
    """Scrapes users who have liked a given Instagram post."""
    print(f"\n❤️ Mining likers from post: {post_url}")
    usernames = set()
    try:
        driver.get(post_url)
        time.sleep(random.randint(3, 5))

        # Find the link that shows the like count and click it
        try:
            # This selector is more robust, looking for " others" or just " likes"
            likes_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(., ' others') or contains(., ' likes')]"))
            )
            likes_link.click()
            print("   - Likes modal opened.")
            time.sleep(random.randint(2, 4))
        except TimeoutException:
            print("   - Could not find the likes link. It might be a video with views instead, or the post has no likes.")
            return []

        # Now, scrape the users from the modal that opens
        scroll_attempts = 0
        # Simple calculation for scrolls needed
        max_scrolls = (max_users // 10) + 1

        while len(usernames) < max_users and scroll_attempts < max_scrolls:
            try:
                # The likers are in a specific div, let's target that
                likers_modal_selector = "//div[@role='dialog']//a[contains(@href, '/') and not(contains(., 'Follow'))]"
                user_elements = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, likers_modal_selector))
                )

                # Extract usernames from the href attributes
                for element in user_elements:
                    try:
                        href = element.get_attribute('href')
                        if href and '/p/' not in href and '/reel/' not in href:
                            username = href.rstrip('/').split('/')[-1]
                            if username and username != '':
                            usernames.add(username)
                    if len(usernames) >= max_users:
                        break
                    except:
                        continue

                # Scroll within the modal to load more likers
                try:
                scrollable_element = driver.find_element(
                    By.XPATH, "//div[@role='dialog']//div[contains(@style, 'overflow')]")
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_element)
                except:
                    pass

                time.sleep(random.randint(2, 3))
                scroll_attempts += 1

            except TimeoutException:
                print("   - No more likers found or modal closed.")
                break
            except Exception as e:
                print(f"   - Error during likers extraction: {e}")
                break

        # Close the likes modal
        try:
            close_button = driver.find_element(
                By.XPATH, "//button[@aria-label='Close']")
            close_button.click()
            time.sleep(2)
        except:
            try:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(2)
            except:
                pass

        print(f"   ✅ Extracted {len(usernames)} likers from the post.")
        return list(usernames)

    except Exception as e:
        print(f"❌ Error mining post likers: {e}")
        return []


# === NEW: NETWORK EFFECT STRATEGY ===

def get_followed_vegan_accounts(mode='online', min_days_ago=1, max_accounts=50):
    """
    Get list of vegan accounts we've already followed to use as seed accounts for network effect.

    Args:
        mode: 'online' for @cocos_connected, 'local' for @cocos_pt_studio
        min_days_ago: Only get accounts followed at least N days ago (to avoid very recent follows)
        max_accounts: Maximum number of seed accounts to return

    Returns:
        List of tuples: (username, followed_at, follow_back_status)
    """
    try:
        print(
            f"\n🌱 === NETWORK EFFECT: Getting seed accounts for {mode} mode ===")

        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Query processing_queue for accounts we've followed
        cutoff_date = (datetime.datetime.now() -
                       datetime.timedelta(days=min_days_ago)).strftime('%Y-%m-%d')

        cursor.execute("""
            SELECT username, followed_at, follow_back_status, hashtag_found
            FROM processing_queue
            WHERE search_mode = ?
            AND followed_at IS NOT NULL
            AND DATE(followed_at) <= ?
            ORDER BY 
                CASE WHEN follow_back_status = 'yes' THEN 1 ELSE 2 END,
                followed_at DESC
            LIMIT ?
        """, (mode, cutoff_date, max_accounts))

        seed_accounts = cursor.fetchall()
        conn.close()

        # Prioritize accounts that followed back (higher quality network)
        followed_back = [acc for acc in seed_accounts if acc[2] == 'yes']
        others = [acc for acc in seed_accounts if acc[2] != 'yes']

        print(f"📊 Found {len(seed_accounts)} seed accounts:")
        print(f"   ✅ {len(followed_back)} followed back (HIGH PRIORITY)")
        print(f"   ⏳ {len(others)} pending/no follow-back")

        # Return followed-back accounts first, then others
        prioritized_accounts = followed_back + others

        # Show sample of accounts we'll explore
        if prioritized_accounts:
            print(f"\n🎯 Top seed accounts to explore:")
            for i, (username, followed_at, status, hashtag) in enumerate(prioritized_accounts[:10]):
                status_emoji = "✅" if status == 'yes' else "⏳"
                print(f"   {i+1}. {status_emoji} @{username} (via #{hashtag})")

        return prioritized_accounts

    except Exception as e:
        print(f"❌ Error getting followed vegan accounts: {e}")
        return []


def search_followers_of_followed_accounts(driver, processed_usernames, num_clients_goal, current_client_count, mode='online'):
    """
    NETWORK EFFECT STRATEGY: Explore followers of accounts we've already followed.
    This leverages the fact that vegan people tend to follow other vegan people.

    Args:
        driver: Selenium WebDriver instance
        processed_usernames: Set of usernames we've already processed
        num_clients_goal: Target number of clients to find
        current_client_count: How many clients we've found so far
        mode: 'online' or 'local'

    Returns:
        List of potential client data
    """
    print(f"\n🚀 === NETWORK EFFECT LEAD GENERATION ===")
    print(
        f"🎯 Goal: Find {num_clients_goal - current_client_count} more clients through network exploration")

    potential_clients = []

    # Get seed accounts (prioritizing those who followed back)
    seed_accounts = get_followed_vegan_accounts(
        mode=mode, min_days_ago=2, max_accounts=30)

    if not seed_accounts:
        print(
            "❌ No seed accounts found. Run basic lead generation first to build a network.")
        return potential_clients

    # Track which seed accounts we've explored
    explored_seeds = set()

    for seed_username, followed_at, follow_back_status, hashtag in seed_accounts:

        # Stop if we've reached our goal
        if len(potential_clients) + current_client_count >= num_clients_goal:
            print(
                f"🎉 Reached client goal! Found {len(potential_clients)} new clients via network effect.")
            break

        # Skip if we've already explored this seed
        if seed_username in explored_seeds:
            continue

        explored_seeds.add(seed_username)

        print(f"\n🔍 Exploring network of @{seed_username}...")
        print(
            f"   📊 Status: {'✅ Followed back' if follow_back_status == 'yes' else '⏳ Pending'}")
        print(f"   🏷️ Found via: #{hashtag}")

        try:
            # Get followers from this seed account
            # Use more followers for accounts that followed back (higher quality network)
            max_followers = 30 if follow_back_status == 'yes' else 15

            followers = get_followers_from_profile(
                driver,
                seed_username,
                max_followers=max_followers,
                # Treat follow-backs as high quality
                is_vegan_influencer=(follow_back_status == 'yes')
            )

            if not followers:
                print(f"   ⚠️ No followers found for @{seed_username}")
                continue

            print(
                f"   📱 Analyzing {len(followers)} followers for coaching potential...")

            # Analyze each follower as a potential client
            followers_analyzed = 0
            for follower_username in followers:

                # Stop if we've reached our goal
                if len(potential_clients) + current_client_count >= num_clients_goal:
                    break

                # Skip if already processed
                if follower_username in processed_usernames:
                    continue

                processed_usernames.add(follower_username)

                try:
                    # Analyze this follower as a potential client
                    client_data, is_influencer = analyze_user_profile(
                        driver,
                        follower_username,
                        source_hashtag=f"network:{seed_username}",
                        source_type='network_follower',
                        mode=mode
                    )

                    if client_data:
                        potential_clients.append(client_data)
                        save_lead_to_database(client_data)

                        print(
                            f"🌟 NETWORK LEAD #{len(potential_clients)}! @{client_data['username']}")
                        print(f"   🔗 Found via @{seed_username}'s network")
                        print(
                            f"   📊 Score: {client_data['coaching_score']}/100")

                    followers_analyzed += 1

                    # Add delay between follower analyses
                    time.sleep(random.randint(8, 15))

                except Exception as e:
                    print(f"   ⚠️ Error analyzing @{follower_username}: {e}")
                    continue

            print(
                f"   ✅ Analyzed {followers_analyzed}/{len(followers)} followers from @{seed_username}")

            # Add delay between seed account explorations
            time.sleep(random.randint(15, 25))

        except Exception as e:
            print(f"   ❌ Error exploring @{seed_username}: {e}")
            continue

    print(f"\n🎯 NETWORK EFFECT RESULTS:")
    print(f"   🌟 Found {len(potential_clients)} new potential clients")
    print(f"   🔍 Explored {len(explored_seeds)} seed accounts")
    print(
        f"   📈 Total clients found: {len(potential_clients) + current_client_count}/{num_clients_goal}")

    return potential_clients


def get_high_engagement_followers(driver, username, max_followers=50):
    """
    Get followers who are likely to be more engaged (for higher quality network exploration).
    This looks at followers who appear earlier in the list (Instagram shows more engaged followers first).
    """
    try:
        print(f"⚡ Getting high-engagement followers from @{username}...")

        # Get standard followers list but focus on first batch (most engaged)
        followers = get_followers_from_profile(
            driver, username, max_followers=max_followers)

        if not followers:
            return []

        # Instagram tends to show most engaged followers first
        # Take first 70% as "high engagement"
        high_engagement_count = max(10, int(len(followers) * 0.7))
        high_engagement_followers = followers[:high_engagement_count]

        print(
            f"   ⚡ Selected {len(high_engagement_followers)}/{len(followers)} high-engagement followers")

        return high_engagement_followers

    except Exception as e:
        print(f"❌ Error getting high-engagement followers: {e}")
        return []


def smart_network_exploration(driver, processed_usernames, num_clients_goal, current_client_count, mode='online'):
    """
    ENHANCED NETWORK STRATEGY: Intelligently explore the network using multiple approaches.

    1. Start with accounts that followed back (highest quality)
    2. Get their most engaged followers
    3. Use post likes/comments for deeper exploration
    4. Generate new hashtags from successful finds
    """
    print(f"\n🧠 === SMART NETWORK EXPLORATION ===")

    potential_clients = []

    # Phase 1: Core network exploration (followers of followed accounts)
    print(f"\n📊 PHASE 1: Core Network Exploration")
    core_clients = search_followers_of_followed_accounts(
        driver, processed_usernames, num_clients_goal, current_client_count, mode
    )
    potential_clients.extend(core_clients)
    current_client_count += len(core_clients)

    # Stop if we've reached our goal
    if current_client_count >= num_clients_goal:
        return potential_clients

    # Phase 2: Deep engagement exploration (likes/comments from high-quality accounts)
    print(f"\n💎 PHASE 2: Deep Engagement Exploration")
    try:
        # Get our best seed accounts (those who followed back)
        seed_accounts = get_followed_vegan_accounts(
            mode=mode, min_days_ago=1, max_accounts=10)
        # Top 5 who followed back
        high_quality_seeds = [
            acc for acc in seed_accounts if acc[2] == 'yes'][:5]

        for seed_username, _, _, _ in high_quality_seeds:

            if current_client_count >= num_clients_goal:
                break

            print(f"\n🔍 Deep diving into @{seed_username}'s engagement...")

            try:
                # Navigate to their profile to get recent posts
                profile_url = f"https://www.instagram.com/{seed_username}/"
                driver.get(profile_url)
                time.sleep(random.randint(4, 6))

                # Get their recent post links
                post_links = []
                try:
                    post_elements = driver.find_elements(
                        By.CSS_SELECTOR, "a[href*='/p/']")[:3]  # Last 3 posts
                    post_links = [elem.get_attribute(
                        'href') for elem in post_elements if elem.get_attribute('href')]
                except:
                    continue

                # Analyze likers from their recent posts
                for post_link in post_links:
                    if current_client_count >= num_clients_goal:
                        break

                    print(f"   🔍 Mining likers from recent post...")
                    post_likers = get_users_from_likes(
                        driver, post_link, max_users=30)

                    for liker in post_likers[:15]:  # Analyze top 15 likers
                        if current_client_count >= num_clients_goal:
                            break

                        if liker in processed_usernames:
                            continue

                        processed_usernames.add(liker)

                        try:
                            client_data, is_influencer = analyze_user_profile(
                                driver,
                                liker,
                                source_hashtag=f"engagement:{seed_username}",
                                source_type='post_engagement',
                                mode=mode
                            )

                            if client_data:
                                potential_clients.append(client_data)
                                save_lead_to_database(client_data)
                                current_client_count += 1

                                print(
                                    f"💎 ENGAGEMENT LEAD! @{client_data['username']} (Score: {client_data['coaching_score']})")

                            time.sleep(random.randint(10, 18))

                        except Exception as e:
                            print(f"   ⚠️ Error analyzing liker @{liker}: {e}")
                            continue

                    time.sleep(random.randint(8, 12))

            except Exception as e:
                print(
                    f"   ❌ Error in deep engagement exploration for @{seed_username}: {e}")
                continue

    except Exception as e:
        print(f"❌ Error in Phase 2: {e}")

    print(f"\n🎉 SMART NETWORK EXPLORATION COMPLETE!")
    print(f"   📊 Total new clients found: {len(potential_clients)}")
    print(f"   🎯 Overall progress: {current_client_count}/{num_clients_goal}")

    return potential_clients

# === END: NETWORK EFFECT STRATEGY ===


if __name__ == "__main__":
    main()
