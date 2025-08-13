# Smart Lead Finder - Streamlined Lead Generation
# Finds and follows up to 75 new prospects per day

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

# Initialize Gemini models for fallback
gemini_models = [
    ('gemini-2.0-flash', genai.GenerativeModel('gemini-2.0-flash')),
    ('gemini-2.0-flash-lite', genai.GenerativeModel('gemini-2.0-flash-lite')),
    ('gemini-2.0-flash-thinking-exp-01-21',
     genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21'))
]

# Script configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMEDRIVER_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"
SQLITE_DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

# Instagram credentials - will be set based on mode
USERNAME = ""
PASSWORD = "Shannonb3"

# Daily limits
DAILY_FOLLOW_LIMIT = 75

# Target hashtags for online vegan mode
ONLINE_HASHTAGS = [
    "veganrecipes", "plantbasedrecipes", "veganfood", "whatveganseat",
    "vegancommunity", "plantbasedcommunity", "veganlife", "plantbasedlifestyle",
    "veganweightloss", "plantbasedweightloss", "veganfitness", "plantbasedfitness"
]

# Target influencers for online vegan mode
ONLINE_INFLUENCERS = [
    'nimai_delgado',       # Vegan bodybuilder
    'plantyou',            # Simple vegan recipes
    'pickuplimes',         # Wholesome vegan lifestyle
    'earthyandy',          # Plant-based family
    'fullyrawkristina',    # Raw vegan influencer
    'the_buddhist_chef',   # Mindful veganism
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
    # Women's fitness
    "mumsworkout", "mumsfitness", "workingmumfitness", "melbournemumlife", "strongmum",
    "fitnessmum", "healthymum", "activemum", "weighttrainingmum", "strengthmum"
]

# Chrome options for headless mode (enhanced stability)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Always headless for both modes
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option(
    "excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
# Enhanced stability options
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-features=VizDisplayCompositor")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-plugins")
chrome_options.add_argument("--disable-images")  # Faster loading
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument("--disable-background-timer-throttling")
chrome_options.add_argument("--disable-renderer-backgrounding")
chrome_options.add_argument("--disable-backgrounding-occluded-windows")
chrome_options.add_argument("--enable-unsafe-swiftshader")  # Fix WebGL errors
chrome_options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")


class SmartLeadFinder:
    def __init__(self, mode='online'):
        self.driver = None
        self.run_id = None
        self.leads_found = 0
        self.leads_followed = 0
        self.processed_usernames = set()
        self.mode = mode

        # Set credentials based on mode
        global USERNAME
        if mode == 'local':
            USERNAME = "cocos_pt_studio"
            print(
                f"🏠 LOCAL MODE: Using {USERNAME} account for Bayside gym clients")
        else:
            USERNAME = "cocos_connected"
            print(f"🌱 ONLINE MODE: Using {USERNAME} account for vegan clients")

    def get_db_connection(self):
        """Get database connection."""
        return sqlite3.connect(SQLITE_DB_PATH)

    def create_tables_if_needed(self):
        """Create required tables if they don't exist."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            # Create processing_queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    followed_at TEXT,
                    check_after_date TEXT,
                    hashtag_found TEXT,
                    search_mode TEXT DEFAULT 'online',
                    follow_back_status TEXT DEFAULT 'pending',
                    follow_back_checked_at TEXT,
                    dm_sent_at TEXT,
                    dm_message TEXT,
                    dm_status TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create lead_generation_runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lead_generation_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_type TEXT NOT NULL,
                    run_timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    leads_found INTEGER DEFAULT 0,
                    leads_followed INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """)

            conn.commit()
            print("✅ Database tables ready")
        finally:
            conn.close()

    def log_run(self, status, error_message=None):
        """Log run status to database."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            current_time = datetime.datetime.now().isoformat()

            if status == 'started':
                cursor.execute("""
                    INSERT INTO lead_generation_runs
                    (run_type, run_timestamp, status,
                     leads_found, leads_followed, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ('find_leads', current_time, status, 0, 0, error_message))
                self.run_id = cursor.lastrowid
                print(
                    f"📈 Started new lead finding session (ID: {self.run_id})")
            elif self.run_id:
                cursor.execute("""
                    UPDATE lead_generation_runs
                    SET status = ?, leads_found = ?, leads_followed = ?, error_message = ?
                    WHERE id = ?
                """, (status, self.leads_found, self.leads_followed, error_message, self.run_id))
                print(
                    f"📈 Updated session {self.run_id}: {status} - Found: {self.leads_found}, Followed: {self.leads_followed}")

            conn.commit()
        finally:
            conn.close()

    def get_daily_follows_count(self):
        """Get today's follow count for the current mode/account."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            cursor.execute(
                "SELECT COUNT(*) FROM processing_queue WHERE DATE(followed_at) = ? AND search_mode = ?", (today, self.mode))
            count = cursor.fetchone()[0]
            return count
        finally:
            conn.close()

    def setup_driver(self):
        """Initialize Chrome driver."""
        try:
            service = webdriver.chrome.service.Service(
                executable_path=CHROMEDRIVER_PATH)
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Chrome driver initialized in headless mode")
            return True
        except Exception as e:
            print(f"❌ Failed to setup driver: {e}")
            return False

    def login_to_instagram(self):
        """Login to Instagram."""
        try:
            print("🔐 Logging into Instagram...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(5)

            # Username
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(USERNAME)
            time.sleep(random.uniform(1, 2))

            # Password
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_field.clear()
            password_field.send_keys(PASSWORD)
            time.sleep(random.uniform(1, 2))

            # Login button
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[type='submit']"))
            )
            login_button.click()
            time.sleep(10)

            # Check if login successful
            if "instagram.com/accounts/login" not in self.driver.current_url:
                print("✅ Successfully logged into Instagram")
                self.handle_post_login_popups()
                return True
            else:
                print("❌ Login failed")
                return False

        except Exception as e:
            print(f"❌ Error during login: {e}")
            return False

    def handle_post_login_popups(self):
        """Handle popups after login."""
        try:
            time.sleep(3)
            # Handle "Save Login Info" and notifications popups
            for _ in range(2):
                try:
                    not_now_button = self.driver.find_element(
                        By.XPATH, "//button[contains(text(), 'Not Now')]")
                    not_now_button.click()
                    time.sleep(2)
                except:
                    break
        except Exception as e:
            print(f"Note: No popups to handle: {e}")

    def analyze_with_gemini(self, prompt, image_data=None):
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

    def get_screening_prompt(self, username):
        """Get AI screening prompt based on search mode"""
        if self.mode == 'local':
            return self.get_local_screening_prompt(username)
        else:
            return self.get_online_screening_prompt(username)

    def get_local_screening_prompt(self, username):
        """AI screening prompt for local Bayside gym clients"""
        return f"""
        You are an expert Instagram analyst helping a local gym owner find new clients in the Bayside, Melbourne area.
        Your task is to analyze the profile of @{username} and determine if they are a potential local client.

        **TARGET CLIENT:** Women 30+ (especially mums) who live in or frequent the Bayside Melbourne area.

        **Questionnaire (Answer with YES or NO, and provide brief evidence for your choice):**

        1.  **IS_LOCAL:** Does this person appear to live in or frequent the Bayside, Melbourne area?
            - Look for: Location tags (Hampton, Brighton, Sandringham, Mentone, Cheltenham, Bayside),
              mentions of local spots (Brighton Baths, Hampton Beach, Bayside Shopping Centre),
              Melbourne-specific content, local school tags, local business check-ins
            - Answer: YES/NO - Evidence: [Provide reason, e.g., "Tagged a photo at Hampton Beach", "Bio mentions Brighton", "Posted from Bayside Shopping Centre"]

        2.  **IS_TARGET_MUM:** Is this a woman 30+ (especially a mother)?
            - Look for: Mature appearance, mentions of being a mum/mom, family photos, content about kids/parenting, work-life balance posts
            - Answer: YES/NO - Evidence: [Provide reason, e.g., "Profile shows woman in her 30s with kids", "Bio mentions 'mum of 3'", "Posts about school pickups"]

        3.  **IS_BUSINESS_OR_COACH:** Is this a business, brand, or another coach/trainer?
            - Look for: "coach", "trainer", "PT", "nutritionist", "business", "services", client results, selling products
            - Answer: YES/NO - Evidence: [Provide reason, e.g., "This is an individual's personal page", "Bio says 'Personal Trainer'"]

        4.  **FINAL_VERDICT_POTENTIAL_CLIENT:** Based on the above, is this a potential client?
            - A potential client MUST be: LOCAL to Bayside + TARGET_MUM (30+ woman, preferably mother) + NOT a business/coach
            - Answer: YES/NO - Reason: [Summarize why they are or are not a potential client]

        5.  **IS_FAKE_OR_INACTIVE:** Does this look like a bot, fake, or inactive account?
            - Look for: No profile pic, zero or very few posts, generic bio, high following count with low followers
            - Answer: YES/NO - Evidence: [Provide reason, e.g., "Account has real photos and normal activity"]

        **CRITICAL: If you cannot see clear details in the screenshot, say "Cannot determine clearly from screenshot" rather than "No evidence found".**

        **Provide your response in this EXACT format:**
        IS_LOCAL: [YES/NO] - Evidence: [reason]
        IS_TARGET_MUM: [YES/NO] - Evidence: [reason]
        IS_BUSINESS_OR_COACH: [YES/NO] - Evidence: [reason]
        FINAL_VERDICT_POTENTIAL_CLIENT: [YES/NO] - Reason: [reason]
        IS_FAKE_OR_INACTIVE: [YES/NO] - Evidence: [reason]
        """

    def get_online_screening_prompt(self, username):
        """AI screening prompt for online vegan clients"""
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

        2.  **IS_PLANT_BASED:** Does this person follow a vegan or plant-based lifestyle?
             - Look specifically for: "vegan", "plant-based", "plantbased", vegan food posts, plant emojis (🌱🥕🥗), environmental/animal rights content
             - Answer: YES/NO - Evidence: [Provide reason, e.g., "Bio says vegan", "Posts plant-based meals", "Uses vegan hashtags"]

        3.  **APPARENT_GENDER:** What is the apparent gender of the individual?
            - Answer: MALE/FEMALE/UNCLEAR - Evidence: [Briefly state reason, e.g., "Profile picture and name"]

        4.  **IS_TARGET_FEMALE:** If FEMALE, does she appear to be a woman (25+) who could benefit from fitness coaching?
            - Look for: Mature appearance, mentions of family/kids, fitness content, or appears to be a potential fitness client
            - Answer: YES/NO/NOT_APPLICABLE - Evidence: [Provide reason, e.g., "Appears to be in her 30s", "Posts about family life"]

        5.  **IS_TARGET_MALE:** If MALE, does he appear to be someone who could benefit from fitness or health guidance?
            - BE GENEROUS: Any male who shows health/fitness interest or could benefit from coaching
            - Answer: YES/NO/NOT_APPLICABLE - Evidence: [Provide reason, e.g., "Shows fitness interest", "Could benefit from guidance"]

        6.  **FINAL_VERDICT_POTENTIAL_CLIENT:** Based on the above, is this a potential client?
            - A potential client MUST be: an INDIVIDUAL (not business/coach) who is VEGAN/PLANT-BASED and fits target demographic
            - Answer: YES/NO - Reason: [Summarize why they are or are not a potential client]

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

    def analyze_profile(self, username):
        """Analyze a user's profile with AI."""
        try:
            print(f"🔍 Analyzing @{username}...")

            # Navigate to profile
            profile_url = f"https://www.instagram.com/{username}/"
            self.driver.get(profile_url)
            # Longer wait for better screenshot quality
            time.sleep(random.randint(5, 8))

            # Check for basic issues
            try:
                if self.driver.find_elements(By.XPATH, "//h2[contains(text(), 'Sorry, this page')]"):
                    print(f"❌ Profile {username} not accessible")
                    return False
                if self.driver.find_elements(By.XPATH, "//h2[contains(text(), 'Private')]"):
                    print(f"🔒 Profile {username} is private")
                    return False
            except:
                pass

            # Take screenshot
            screenshot_data = self.driver.get_screenshot_as_base64()

            # Get AI analysis
            prompt = self.get_screening_prompt(username)
            response = self.analyze_with_gemini(prompt, screenshot_data)

            if not response:
                print(f"❌ AI analysis failed for {username}")
                return False

            response_text = response.text

            # Parse response using the same logic as find_potential_clients.py
            def parse_line(key, text):
                match = re.search(
                    rf'{key}:\s*(YES|NO|MALE|FEMALE|UNCLEAR|NOT_APPLICABLE)\s*-\s*(?:Evidence|Reason):\s*(.*?)(?=\n[A-Z_]+:|$)', text, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(1).upper().strip(), match.group(2).strip()
                return None, "No evidence found"

            if self.mode == 'local':
                # Local mode parsing
                is_local, local_evidence = parse_line(
                    'IS_LOCAL', response_text)
                is_target_mum, mum_evidence = parse_line(
                    'IS_TARGET_MUM', response_text)
                is_business_or_coach, business_evidence = parse_line(
                    'IS_BUSINESS_OR_COACH', response_text)
                is_potential_client, client_reason = parse_line(
                    'FINAL_VERDICT_POTENTIAL_CLIENT', response_text)
                is_fake, fake_evidence = parse_line(
                    'IS_FAKE_OR_INACTIVE', response_text)

                # Check for AI analysis issues
                if ("No evidence found" in local_evidence or
                    "No evidence found" in mum_evidence or
                        "Cannot determine clearly" in local_evidence):
                    print(
                        f"⚠️ AI may not be seeing profile clearly for {username}")
                    print(
                        f"🔍 Raw AI response preview: {response_text[:200]}...")

                # Local criteria logic
                is_potential = (is_local == 'YES' and
                                is_target_mum == 'YES' and
                                is_business_or_coach != 'YES' and
                                is_fake != 'YES')

                # Show the AI's reasoning for local mode
                print(
                    f"   🏠 Local: {'✅ YES' if is_local == 'YES' else '❌ NO'} - {local_evidence}")
                print(
                    f"   👩‍👧‍👦 Target Mum: {'✅ YES' if is_target_mum == 'YES' else '❌ NO'} - {mum_evidence}")
                print(
                    f"   🏢 Business/Coach: {'❌ YES' if is_business_or_coach == 'YES' else '✅ NO'} - {business_evidence}")
                print(
                    f"   🤖 Fake/Inactive: {'❌ YES' if is_fake == 'YES' else '✅ NO'} - {fake_evidence}")
                print(
                    f"   🎯 AI Final Verdict: {'✅ YES' if is_potential_client == 'YES' else '❌ NO'} - {client_reason}")

                # Use AI's final verdict if our logic says potential but AI says no
                if is_potential_client == 'YES' or is_potential:
                    print(f"✅ POTENTIAL LOCAL CLIENT FOUND: {username}")
                    print(f"   💡 Final verdict: {client_reason}")
                    self.leads_found += 1
                    return True
                else:
                    print(f"❌ Not a potential local client: {username}")
                    print(f"   💡 Reason: {client_reason}")

                    # Debug: Show why they failed local criteria
                    if is_local != 'YES':
                        print(f"   🚫 Failed: Not local to Bayside area")
                    elif is_target_mum != 'YES':
                        print(f"   🚫 Failed: Not a 30+ woman/mum")
                    elif is_business_or_coach == 'YES':
                        print(f"   🚫 Failed: Is a business/coach")
                    elif is_fake == 'YES':
                        print(f"   🚫 Failed: Appears fake/inactive")

                    return False

            else:
                # Online mode parsing (existing logic)
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

                # Check for AI analysis issues
                if ("No evidence found" in business_evidence or
                    "No evidence found" in plant_evidence or
                        "Cannot determine clearly" in business_evidence):
                    print(
                        f"⚠️ AI may not be seeing profile clearly for {username}")
                    print(
                        f"🔍 Raw AI response preview: {response_text[:200]}...")

                # STRICT vegan/plant-based criteria as requested
                # Only accept people who are clearly vegan/plant-based
                is_clearly_vegan_or_plant_based = (
                    is_plant_based == 'YES' or
                    'plant' in plant_evidence.lower() or
                    'vegan' in plant_evidence.lower() or
                    'plantbased' in plant_evidence.lower() or
                    'plant-based' in plant_evidence.lower()
                )

                is_potential = (is_business_or_coach != 'YES' and
                                is_clearly_vegan_or_plant_based and
                                (is_target_female == 'YES' or is_target_male == 'YES') and
                                is_fake != 'YES')

                # Show the AI's reasoning (updated format)
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

                # Use AI's final verdict if our logic says potential but AI says no
                if is_potential_client == 'YES' or is_potential:
                    print(f"✅ POTENTIAL CLIENT FOUND: {username}")
                    print(f"   💡 Final verdict: {client_reason}")
                    self.leads_found += 1
                    return True
                else:
                    print(f"❌ Not a potential client: {username}")
                    print(f"   💡 Reason: {client_reason}")

                    # Debug: Show why they failed our criteria
                    if is_business_or_coach == 'YES':
                        print(f"   🚫 Failed: Is a business/coach")
                    elif not is_clearly_vegan_or_plant_based:
                        print(f"   🚫 Failed: Not clearly vegan/plant-based")
                    elif is_target_female != 'YES' and is_target_male != 'YES':
                        print(f"   🚫 Failed: Doesn't fit target demographic")
                    elif is_fake == 'YES':
                        print(f"   🚫 Failed: Appears fake/inactive")

                    return False

        except Exception as e:
            print(f"❌ Error analyzing {username}: {e}")
            return False

    def follow_user(self, username):
        """Follow a user on Instagram."""
        try:
            print(f"👥 Following @{username}...")

            # Navigate to profile
            profile_url = f"https://www.instagram.com/{username}/"
            self.driver.get(profile_url)
            time.sleep(random.uniform(3, 6))

            # Find follow button
            follow_selectors = [
                "//button[text()='Follow']",
                "//button[contains(text(), 'Follow')]",
                "//div[text()='Follow']",
                "[aria-label='Follow']"
            ]

            for selector in follow_selectors:
                try:
                    if selector.startswith("//"):
                        follow_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        follow_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable(
                                (By.CSS_SELECTOR, selector))
                        )

                    button_text = follow_button.text.lower()
                    if 'follow' in button_text and 'following' not in button_text and 'requested' not in button_text:
                        follow_button.click()
                        print(f"✅ Successfully followed @{username}")
                        self.leads_followed += 1
                        return True
                    elif 'following' in button_text or 'requested' in button_text:
                        print(f"⚠️ Already following @{username}")
                        return False

                except (TimeoutException, NoSuchElementException):
                    continue

            print(f"⚠️ Could not find follow button for @{username}")
            return False

        except Exception as e:
            print(f"❌ Error following @{username}: {e}")
            return False

    def add_to_processing_queue(self, username, hashtag_found):
        """Add user to processing queue."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            current_time = datetime.datetime.now().isoformat()
            check_after = (datetime.datetime.now() +
                           datetime.timedelta(days=1)).isoformat()

            cursor.execute("""
                INSERT OR IGNORE INTO processing_queue 
                (username, followed_at, check_after_date, hashtag_found, search_mode)
                VALUES (?, ?, ?, ?, ?)
            """, (username, current_time, check_after, hashtag_found, self.mode))

            conn.commit()
            print(
                f"📊 Added @{username} to processing queue ({self.mode} mode)")
        except Exception as e:
            print(f"❌ Error adding to queue: {e}")
        finally:
            conn.close()

    def mine_followers_from_influencers(self):
        """Mine followers from target accounts based on mode."""
        if self.mode == 'local':
            target_accounts = LOCAL_BUSINESSES
            print(f"🏠 Mining followers from local businesses for Bayside gym clients...")
        else:
            target_accounts = ONLINE_INFLUENCERS
            print(f"🌱 Mining followers from vegan influencers for online clients...")

        print(f"📋 Target accounts: {len(target_accounts)} accounts to process")

        total_leads_from_followers = 0

        for influencer in target_accounts:
            if self.get_daily_follows_count() >= DAILY_FOLLOW_LIMIT:
                break

            print(f"\n🎯 Mining followers from @{influencer}...")

            try:
                # Navigate to influencer profile
                profile_url = f"https://www.instagram.com/{influencer}/"
                self.driver.get(profile_url)
                time.sleep(random.randint(3, 5))

                # Click followers link
                followers_link = self.driver.find_element(
                    By.XPATH, "//a[contains(@href, '/followers/')]")
                followers_link.click()
                time.sleep(random.randint(3, 5))

                # Collect followers (limit to 20 per influencer for speed)
                followers_collected = 0
                max_followers_per_influencer = 20

                while (followers_collected < max_followers_per_influencer and
                       self.get_daily_follows_count() < DAILY_FOLLOW_LIMIT):

                    # Find follower elements
                    follower_elements = self.driver.find_elements(
                        By.XPATH, "//div[@role='dialog']//a[contains(@href, '/')]"
                    )

                    for element in follower_elements:
                        try:
                            href = element.get_attribute('href')
                            if href and '/p/' not in href and '/reel/' not in href:
                                follower_username = href.rstrip(
                                    '/').split('/')[-1]

                                if (follower_username and
                                    follower_username not in self.processed_usernames and
                                        not follower_username.startswith('instagram')):

                                    self.processed_usernames.add(
                                        follower_username)
                                    print(
                                        f"   👤 Analyzing follower: @{follower_username}")

                                    # Analyze the follower
                                    if self.analyze_profile(follower_username):
                                        # Follow if they're a potential client
                                        if self.follow_user(follower_username):
                                            self.add_to_processing_queue(
                                                follower_username, f"follower_of_{influencer}")
                                            total_leads_from_followers += 1
                                            followers_collected += 1

                                            # Delay between follows
                                            time.sleep(random.uniform(30, 60))

                                    if self.get_daily_follows_count() >= DAILY_FOLLOW_LIMIT:
                                        break

                        except Exception as e:
                            continue

                    # Scroll to load more followers
                    try:
                        scrollable_element = self.driver.find_element(
                            By.XPATH, "//div[@role='dialog']//div[contains(@style, 'overflow')]"
                        )
                        self.driver.execute_script(
                            "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_element
                        )
                        time.sleep(2)
                    except:
                        break

                # Close followers modal
                try:
                    close_button = self.driver.find_element(
                        By.XPATH, "//button[@aria-label='Close']")
                    close_button.click()
                    time.sleep(2)
                except:
                    pass

                print(
                    f"✅ Found {followers_collected} leads from @{influencer} followers")

            except Exception as e:
                print(f"❌ Error mining followers from @{influencer}: {e}")
                continue

        return total_leads_from_followers

    def search_hashtag_for_leads(self, hashtag, max_to_check=20):
        """Search hashtag for potential leads."""
        print(f"\n🔍 Searching #{hashtag}...")
        leads_found_here = 0

        try:
            # Navigate to hashtag
            hashtag_url = f"https://www.instagram.com/explore/tags/{hashtag}/"
            self.driver.get(hashtag_url)
            time.sleep(random.randint(4, 6))

            # Scroll to gather posts
            post_links = set()
            for _ in range(3):  # Limited scrolling for efficiency
                links = self.driver.find_elements(
                    By.CSS_SELECTOR, "a[href*='/p/']")
                for link in links:
                    href = link.get_attribute('href')
                    if href:
                        post_links.add(href)

                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # Process posts
            for i, post_url in enumerate(list(post_links)[:max_to_check]):
                if self.get_daily_follows_count() >= DAILY_FOLLOW_LIMIT:
                    print(
                        f"⏳ Daily follow limit reached ({DAILY_FOLLOW_LIMIT})")
                    break

                print(
                    f"📱 Processing post {i+1}/{min(len(post_links), max_to_check)}")

                try:
                    # Get username from post with multiple fallback methods
                    username = None

                    # Method 1: Extract from URL (fastest)
                    if '/p/' in post_url:
                        # Navigate to post
                        self.driver.get(post_url)
                        time.sleep(random.randint(3, 5))

                        # Try multiple selectors for username
                        username_selectors = [
                            "//header//a[contains(@href, '/')]",
                            "//div[@role='button']//a[contains(@href, '/')]",
                            "//span//a[contains(@href, '/')]",
                            "//a[contains(@href, '/') and not(contains(@href, '/p/')) and not(contains(@href, '/reel/'))]"
                        ]

                        for selector in username_selectors:
                            try:
                                header_link = WebDriverWait(self.driver, 3).until(
                                    EC.presence_of_element_located(
                                        (By.XPATH, selector))
                                )
                                href = header_link.get_attribute('href')
                                if href and '/p/' not in href and '/reel/' not in href:
                                    username = href.rstrip('/').split('/')[-1]
                                    if username and not username.startswith('instagram'):
                                        break
                            except:
                                continue

                    # Method 2: Extract from page source as fallback
                    if not username:
                        try:
                            page_source = self.driver.page_source
                            import re
                            match = re.search(
                                r'"owner":{"username":"([^"]+)"', page_source)
                            if match:
                                username = match.group(1)
                        except:
                            pass

                    if not username or username in self.processed_usernames:
                        print(
                            f"⏭️ Skipping post - no username found or already processed")
                        continue

                    self.processed_usernames.add(username)
                    print(f"👤 Found user: @{username}")

                    # Analyze profile
                    if self.analyze_profile(username):
                        # Follow the user
                        if self.follow_user(username):
                            self.add_to_processing_queue(username, hashtag)
                            leads_found_here += 1

                            # Delay between follows
                            delay = random.uniform(30, 60)
                            print(
                                f"⏳ Waiting {delay:.1f}s before next action...")
                            time.sleep(delay)

                except WebDriverException as e:
                    print(f"❌ WebDriver error processing post: {e}")
                    # Try to restart driver if session is broken
                    if "invalid session id" in str(e).lower() or "session not created" in str(e).lower():
                        print("🔄 Attempting to restart WebDriver...")
                        try:
                            self.driver.quit()
                        except:
                            pass
                        if not self.setup_driver() or not self.login_to_instagram():
                            print("❌ Failed to restart WebDriver")
                            break
                    continue
                except Exception as e:
                    print(f"❌ Error processing post: {e}")
                    continue

        except Exception as e:
            print(f"❌ Error searching #{hashtag}: {e}")

        print(f"✅ Found {leads_found_here} leads from #{hashtag}")
        return leads_found_here

    def run_lead_finding_session(self):
        """Main function to run the lead finding session."""
        print("🚀 Starting Smart Lead Finder...")

        # Create tables if needed
        self.create_tables_if_needed()

        # Log session start
        self.log_run('started')

        try:
            # Check daily limit
            daily_follows = self.get_daily_follows_count()
            remaining = DAILY_FOLLOW_LIMIT - daily_follows

            if remaining <= 0:
                print(
                    f"⏳ Daily follow limit already reached ({daily_follows}/{DAILY_FOLLOW_LIMIT})")
                self.log_run('completed')
                return

            print(
                f"📊 Daily follows: {daily_follows}/{DAILY_FOLLOW_LIMIT} (can follow {remaining} more)")

            # Setup browser
            if not self.setup_driver():
                self.log_run('failed', 'Failed to setup browser')
                return

            # Login
            if not self.login_to_instagram():
                self.log_run('failed', 'Failed to login to Instagram')
                return

            # Phase 1: Mine followers from vegan influencers (highest success rate)
            print(f"\n🎯 PHASE 1: Mining followers from vegan influencers...")
            leads_from_followers = self.mine_followers_from_influencers()
            print(
                f"✅ Found {leads_from_followers} leads from influencer followers")

            # Phase 2: Search hashtags for leads (if still under daily limit)
            if self.get_daily_follows_count() < DAILY_FOLLOW_LIMIT:
                print(f"\n🔍 PHASE 2: Searching hashtags for leads...")

                # Select hashtags based on mode
                if self.mode == 'local':
                    target_hashtags = LOCAL_HASHTAGS
                    print(f"🏠 Using local Bayside hashtags...")
                else:
                    target_hashtags = ONLINE_HASHTAGS
                    print(f"🌱 Using vegan/plant-based hashtags...")

                for hashtag in target_hashtags:
                if self.get_daily_follows_count() >= DAILY_FOLLOW_LIMIT:
                    break

                self.search_hashtag_for_leads(hashtag, max_to_check=10)

                # Small delay between hashtags
                time.sleep(random.uniform(10, 20))

            print(f"\n🎉 Lead finding session complete!")
            print(
                f"📊 Final stats: Found {self.leads_found} leads, Followed {self.leads_followed} users")

            self.log_run('completed')

        except Exception as e:
            print(f"❌ Critical error: {e}")
            traceback.print_exc()
            self.log_run('failed', str(e))

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print("✅ Browser closed")
                except:
                    pass


if __name__ == "__main__":
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(
        description='Smart Lead Finder - Find Instagram prospects')
    parser.add_argument('--mode', type=str, default='online', choices=['online', 'local'],
                        help='Search mode: "online" for vegan clients, "local" for Bayside gym clients')

    args = parser.parse_args()

    # Create finder with specified mode
    finder = SmartLeadFinder(mode=args.mode)
    finder.run_lead_finding_session()
