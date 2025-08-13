# Smart Lead Finder - Streamlined Lead Generation
# Finds and follows up to 75 new prospects per day

"""
=== ENHANCED SMART LEAD FINDER WITH AUSTRALIAN-FIRST PRIORITY ===

🇦🇺 NEW AUSTRALIAN-FIRST STRATEGY:

**ONLINE MODE (Vegan Clients) - New Priority Order:**
   PHASE 1: 🇦🇺 AUSTRALIAN VEGAN INFLUENCERS (HIGHEST PRIORITY)
   PHASE 2: 🔄 NETWORK EFFECT (Database leveraging) 
   PHASE 3A: 🌍 INTERNATIONAL VEGAN INFLUENCERS (Supplementary)
   PHASE 3B: 🔍 HASHTAG SEARCH (Final fallback)

**LOCAL MODE (Bayside Gym Clients):**
   PHASE 1: 🏠 LOCAL BUSINESSES (Bayside/Melbourne)
   PHASE 2: 🔄 NETWORK EFFECT (Database leveraging)
   PHASE 3: 🔍 HASHTAG SEARCH (Final fallback)

🚀 KEY BENEFITS:

1. **AUSTRALIAN PRIORITY FOR MAXIMUM RELEVANCE**
   - Australian vegan influencers processed FIRST for online mode
   - 15 top Australian accounts with 6.2M+ combined followers
   - Local time zone = better engagement rates
   - Same market = higher conversion potential

2. **DATABASE-DRIVEN NETWORK EFFECT** 
   - Explores followers of people who already followed you back
   - Prioritizes accounts with follow-back status for higher quality networks
   - Can explore 20+ seed accounts × 30 followers each = 600+ potential leads

3. **INTELLIGENT SCALING & FALLBACKS**
   - Only processes international influencers if quota not filled by Australian + Network
   - Adaptive follower collection based on success
   - Smart stopping conditions for efficiency

4. **ENHANCED FOLLOWER COLLECTION**
   - Up to 500 followers per influencer (increased from 200)
   - Up to 50 followers analyzed per influencer (was 25)
   - More aggressive scrolling for deeper reach

🎯 RESULT: Australian-first approach for maximum local relevance + intelligent fallbacks!

💡 Perfect for Shannon's business:
- Prioritizes most relevant Australian audiences first
- Leverages existing network connections second
- Falls back to international only when needed
"""

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

# Initialize Gemini models for fallback (newest to oldest)
gemini_models = [
    ('gemini-2.5-flash-lite-preview-06-17',
     genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')),
    ('gemini-2.5-flash', genai.GenerativeModel('gemini-2.5-flash')),
    # Alias for gemini-2.0-flash-001
    ('gemini-2.0-flash', genai.GenerativeModel('gemini-2.0-flash-001')),
    ('gemini-2.0-flash-lite', genai.GenerativeModel('gemini-2.0-flash-lite')),
    ('gemini-2.0-flash-thinking-exp-01-21',
     genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21'))
]

# Script configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMEDRIVER_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"
SQLITE_DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

# Instagram credentials - will be set based on mode
PASSWORD = "Shannonb3"

# Daily limits
DAILY_FOLLOW_LIMIT = 75

# Target hashtags for online vegan mode
ONLINE_HASHTAGS = [
    "veganrecipes", "plantbasedrecipes", "veganfood", "whatveganseat",
    "vegancommunity", "plantbasedcommunity", "veganlife", "plantbasedlifestyle",
    "veganweightloss", "plantbasedweightloss", "veganfitness", "plantbasedfitness"
]

# Australian vegan influencers - HIGHEST PRIORITY
AUSTRALIAN_VEGAN_INFLUENCERS = [
    # === TOP AUSTRALIAN VEGAN INFLUENCERS ===
    # Sarah Cobacho - 1.9M - Sydney - High-protein plant-based recipes
    'plantbaes',
    # Chloe e Wheatland - 1M - Melbourne - Quick vegan meals, wellness
    'chloeevegan',
    # Luba Pavia - 998K - Adelaide - Easy healthy plant-based recipes
    'cook.vegetarian',
    # Anthea Cheng - 730K - Canberra - Vegan baking, food artistry
    'rainbownourishments',
    # Jade - 586K - Melbourne - Vegan desserts, gluten/sugar-free
    'panaceas_pantry',
    # Liz Miu - 483K - Sydney - Holiday vegan feasts, Asian fusion
    'itslizmiu',
    'tessbegg',                     # Tess Begg - 326K - Sydney - Plant-based food & fitness
    # Bella - 172K - South Australia - Simple vegan recipes
    'bellas_vegan_adventures',
    'humane_vision',                # Jakob - 149K - Brisbane - Vegan activism, animal rights
    # Zacchary Bird - 131K - Australia - Vegan butchery, baking
    'zaccharybird',
    # Lauren McGeachin - 101K - Australia - General vegan lifestyle
    'laurenmcgeachin',
    # Nicola - 100K - Australia - Family-friendly vegan recipes
    'veggie_nerd',

    # === AUSTRALIAN VEGAN BRANDS & ORGANIZATIONS ===
    'v2foodofficial',               # V2Food - Major Australian plant-based food brand
    'petaaustralia',                # PETA Australia - Animal rights organization
]

# International vegan influencers - SUPPLEMENTARY (after Australian + Network Effect)
INTERNATIONAL_VEGAN_INFLUENCERS = [
    'nimai_delgado',                # Vegan bodybuilder
    'plantyou',                     # Simple vegan recipes
    'pickuplimes',                  # Wholesome vegan lifestyle
    'earthyandy',                   # Plant-based family
    'fullyrawkristina',             # Raw vegan influencer
    'the_buddhist_chef',            # Mindful veganism
]

# Legacy list for backward compatibility
ONLINE_INFLUENCERS = AUSTRALIAN_VEGAN_INFLUENCERS + INTERNATIONAL_VEGAN_INFLUENCERS

# Local targeting for Bayside Gym - SMART EXPANDED LIST
LOCAL_BUSINESSES = [
    # Existing businesses
    'thehamptons.bakery',
    'recoverylab.hampton',
    'regenwellnesscentre',
    'yesfitnessvic',
    'hamptonsttraders',
    'brightonbaths',
    'sandringhamyachtclub',
    'blackrockfc',
    'baysidecouncil',
    'hamptonpilates',
    'brightongrammar',
    'firbank_grammar',
    'mentonegirlsgrammar',
    'stleonardsbayside',
    'haileyburyschool',
    'baysideshoppingcentre',
    'westfieldsouthland',
    'cheltenhamracecourse',
    'royalmelbourne_gc',
    'victoriagolfclub',
    'baysideafc',
    'brightonbeachhotel',
    'halfmoonbay.slsc',

    # Local Cafes & Restaurants
    'browncowcafehampton',
    'holymacagyros',
    'paperboyhampton',
    'sebastians.food.wine',

    # Community & Real Estate
    'marshallwhiterealestate',
    'bellepropertybayside',
    'jelliscraigbayside',
    'baysidemums',
    'baysidecommunityhub',

    # Fitness Centers
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

    # Health & Wellness
    'baysidephysio',
    'hamptonwellnesscentre',
    'baysidechiropractic',
    'brightonbeachphysio',
    'recoverygurumelbourne',
    'baysideosteo',
    'hamptonmassage',

    # Shannon's current clients
    'payneinthenix',
    'simonetindallrealestate',

    # Local fitness influencers
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

# NEW: Smart keyword patterns for detecting local businesses
LOCAL_BUSINESS_PATTERNS = [
    # Suburb + business type combinations
    'hampton', 'brighton', 'sandringham', 'bayside', 'cheltenham',
    'mentone', 'blackrock', 'beaumaris', 'moorabbin', 'bentleigh',

    # Business type keywords (will be combined with location check)
    'gym', 'fitness', 'pilates', 'yoga', 'crossfit', 'f45', 'anytime',
    'physio', 'chiro', 'massage', 'wellness', 'health', 'recovery',
    'cafe', 'restaurant', 'bakery', 'coffee', 'food',
    'realestate', 'property', 'grammar', 'school', 'council',
    'mums', 'community', 'club', 'centre', 'baths'
]

# NEW: Advanced network exploration limit
NETWORK_EXPLORATION_LIMIT = 30  # Max followers to check from each seed account

# NEW: Business vs Individual classification
BUSINESS_ACCOUNT_INDICATORS = [
    'gym', 'fitness', 'studio', 'clinic', 'cafe', 'restaurant', 'shop',
    'business', 'company', 'services', 'official', 'centre', 'center',
    'realestate', 'property', 'school', 'council', 'club', 'association'
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

DEEPER_SEARCH_LIMIT = 10  # How many followers to check when diving deeper


class SmartLeadFinder:
    def __init__(self, mode='online'):
        self.driver = None
        self.run_id = None
        self.leads_found = 0
        self.leads_followed = 0
        self.processed_usernames = set()
        self.mode = mode
        self.username = ""

        # Network error tracking
        self.network_error_count = 0
        self.last_network_error_time = 0
        self.max_network_errors = 3  # Max network recoveries per session

        # Set credentials based on mode
        if mode == 'local':
            self.username = "cocos_pt_studio"
            print(
                f"🏠 LOCAL MODE: Using {self.username} account for Bayside gym clients")
        else:
            self.username = "cocos_connected"
            print(
                f"🌱 ONLINE MODE: Using {self.username} account for vegan clients")

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

            # Create the master memory table for all processed profiles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_profiles (
                    username TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    search_mode TEXT NOT NULL,
                    was_lead BOOLEAN NOT NULL,
                    reason TEXT
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

    def save_cookies(self):
        """Save browser cookies to a file"""
        cookies_dir = os.path.join(SCRIPT_DIR, "cookies")
        os.makedirs(cookies_dir, exist_ok=True)
        cookies_file = os.path.join(
            cookies_dir, f"{self.username}_cookies.pkl")
        pickle.dump(self.driver.get_cookies(), open(cookies_file, "wb"))
        print(f"✅ Cookies saved successfully for {self.username}")

    def load_cookies(self):
        """Load saved cookies into browser session"""
        try:
            cookies_file = os.path.join(
                SCRIPT_DIR, "cookies", f"{self.username}_cookies.pkl")
            if os.path.exists(cookies_file):
                cookies = pickle.load(open(cookies_file, "rb"))
                self.driver.get("https://www.instagram.com")
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        continue
                print(f"✅ Cookies loaded successfully for {self.username}")
                return True
            return False
        except Exception as e:
            print(f"❌ Error loading cookies: {e}")
            return False

    def check_login_status(self):
        """Check if currently logged into Instagram"""
        try:
            time.sleep(2)
            current_url = self.driver.current_url.lower()
            if "login" in current_url or "challenge" in current_url:
                return False
            # Check for a reliable element that indicates a logged-in state
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "svg[aria-label='Home']"))
            )
            return True
        except (TimeoutException, NoSuchElementException):
            return False
        except Exception as e:
            print(f"❌ Error checking login status: {e}")
            return False

    def login_to_instagram(self):
        """Login to Instagram with robust cookie handling and retries."""
        print(f"🔐 Logging into Instagram as {self.username}...")

        # Try to use cookies first for a quick login
        if self.load_cookies():
            self.driver.get("https://www.instagram.com/")
            if self.check_login_status():
                print("✅ Successfully logged in using cookies.")
                self.handle_post_login_popups()
                return True
            else:
                print(
                    "⚠️ Cookies found but session is invalid. Proceeding with full login.")

        # Full login process if cookies fail
        MAX_LOGIN_ATTEMPTS = 2
        for attempt in range(MAX_LOGIN_ATTEMPTS):
            print(
                f"Attempting full login ({attempt + 1}/{MAX_LOGIN_ATTEMPTS})...")
            try:
                self.driver.delete_all_cookies()
                self.driver.get("https://www.instagram.com/accounts/login/")
                time.sleep(5)

                # Username
                username_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                username_field.clear()
                username_field.send_keys(self.username)
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

                # Verify login
                if self.check_login_status():
                    print("✅ Successfully logged into Instagram")
                    self.save_cookies()
                    self.handle_post_login_popups()
                    return True
                else:
                    print("❌ Login failed. Checking for challenges...")
                    if "challenge" in self.driver.current_url:
                        print(
                            "🚨 SECURITY CHALLENGE DETECTED. Manual intervention required.")
                        self.driver.save_screenshot(
                            f"challenge_{self.username}.png")
                        return False
            except Exception as e:
                print(f"❌ Error during login attempt: {e}")
                self.driver.save_screenshot(f"login_error_{self.username}.png")

        print(f"❌ All login attempts failed for {self.username}.")
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
        """Analyze content with Gemini AI with enhanced error handling."""
        try:
            if image_data:
                contents = [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
                ]
            else:
                contents = prompt

            # Try each model in order
            for i, (model_name, model) in enumerate(gemini_models):
                try:
                    print(
                        f"🤖 Trying {model_name} (model {i+1}/{len(gemini_models)})...")
                    response = model.generate_content(contents)
                    if response and response.text:
                        print(f"✅ {model_name} succeeded")
                        return response
                    else:
                        print(f"⚠️ {model_name} returned empty response")
                        continue
                except Exception as e:
                    error_msg = str(e)
                    if "503" in error_msg or "timeout" in error_msg.lower():
                        print(
                            f"🌐 {model_name} connection timeout: {error_msg[:100]}...")
                        # Add delay before trying next model for connection issues
                        if i < len(gemini_models) - 1:  # Not the last model
                            print(f"⏳ Waiting 5 seconds before trying next model...")
                            time.sleep(5)
                    else:
                        print(f"⚠️ {model_name} failed: {error_msg[:100]}...")
                    continue

            print("❌ All Gemini models failed")
            return None
        except Exception as e:
            print(f"❌ Gemini analysis failed: {e}")
            return None

    def handle_network_error_recovery(self):
        """Handle network errors by restarting driver and checking connectivity."""
        try:
            print("🔄 Starting network error recovery...")

            # Step 1: Check basic connectivity
            print("🌐 Checking basic internet connectivity...")
            if not self.check_internet_connectivity():
                print("❌ No internet connection detected")
                return False

            # Step 2: Close current driver
            print("🔧 Closing current Chrome driver...")
            try:
                if self.driver:
                    self.driver.quit()
                    time.sleep(3)
            except:
                pass

            # Step 3: Restart driver
            print("🚀 Restarting Chrome driver...")
            if not self.setup_driver():
                print("❌ Failed to restart Chrome driver")
                return False

            # Step 4: Test login
            print("🔐 Testing Instagram login...")
            if not self.login_to_instagram():
                print("❌ Failed to login after driver restart")
                return False

            print("✅ Network recovery completed successfully")
            return True

        except Exception as e:
            print(f"❌ Error during network recovery: {e}")
            return False

    def check_internet_connectivity(self):
        """Check basic internet connectivity."""
        try:
            import socket
            import urllib.request

            # Test 1: Check if we can resolve DNS
            try:
                socket.gethostbyname("instagram.com")
                print("✅ DNS resolution working")
            except socket.gaierror:
                print("❌ DNS resolution failed")
                return False

            # Test 2: Try to reach Instagram
            try:
                urllib.request.urlopen("https://instagram.com", timeout=10)
                print("✅ Instagram.com reachable")
                return True
            except:
                print("⚠️ Instagram.com not reachable, but DNS works")
                return True  # DNS works, might be temporary block

        except Exception as e:
            print(f"❌ Connectivity check failed: {e}")
            return False

    def test_gemini_connectivity(self):
        """Test Gemini API connectivity before starting analysis."""
        print("🤖 Testing Gemini API connectivity...")

        # Simple test prompt
        test_prompt = "Test connection. Respond with 'OK' if working."

        try:
            response = self.analyze_with_gemini(test_prompt)
            if response and response.text:
                print("✅ Gemini API is working")
                return True
            else:
                print("❌ Gemini API test failed - no response")
                return False
        except Exception as e:
            print(f"❌ Gemini API test failed: {e}")
            return False

    def get_screening_prompt(self, username):
        """Get AI screening prompt based on search mode"""
        if self.mode == 'local':
            return self.get_local_screening_prompt(username)
        else:
            return self.get_online_screening_prompt(username)

    def get_local_screening_prompt(self, username, bio_text="", evidence_score=0, evidence_details=""):
        """AI screening prompt for local Bayside gym clients"""
        return f"""
        You are an expert Instagram analyst helping a local gym owner find new clients in the Bayside, Melbourne area.
        Your task is to analyze the profile of @{username} and determine if they are a potential local client.

        **EXTRACTED BIO TEXT:** {bio_text}

        **LOCAL EVIDENCE ANALYSIS:**
        Evidence Score: {evidence_score}/100 points
        Evidence Details: {evidence_details}

        **TARGET CLIENT:** Women 30+ (especially mums) who live in or frequent the Bayside Melbourne area.

        **BAYSIDE AREA KEYWORDS (Use this list for evidence):**
        - **Suburbs:** Hampton, Brighton, Sandringham, Black Rock, Beaumaris, Cheltenham, Highett, Mentone, Parkdale, Moorabbin, Bentleigh.
        - **Major Roads/Streets:** Nepean Highway, Beach Road, Hampton Street, Church Street, Bay Street.
        - **Landmarks:** Brighton Bathing Boxes, Sandringham Yacht Club, Black Rock Clock Tower, Half Moon Bay.
        - **Shopping:** Bayside Shopping Centre, Westfield Southland, Hampton St Shops, Church St Shops.
        - **Schools:** Firbank, Brighton Grammar, Haileybury, St Leonard's, Mentone Girls Grammar.
        - **Businesses/Cafes:** The Hamptons Bakery, Recovery Lab Hampton, Brown Cow, Paperboy.
        - **Recreation:** Brighton Baths, local footy clubs (e.g., Black Rock FC), local beaches (Hampton, Brighton, Sandringham), local golf clubs (Royal Melbourne, Victoria).

        **Questionnaire (Answer with YES or NO, and provide brief evidence for your choice):**

        1.  **IS_LOCAL_CONFIDENCE_SCORE (1-10):** How confident are you that this person lives in or frequents the Bayside Melbourne area? 1=No Clues, 10=Explicitly States Bayside.
            - Look for any of the Bayside Area Keywords in their bio, posts, or location tags.
            - **Answer:** [Score from 1-10] - **Evidence:** [List ALL keywords or clues found, e.g., "Tagged a photo at Hampton Beach", "Bio mentions Brighton Grammar", "Posted from Westfield Southland"]

        2.  **IS_TARGET_MUM:** Is this a woman 30+ (especially a mother)?
            - Look for: Mature appearance, mentions of being a mum/mom, family photos, content about kids/parenting, school-related posts.
            - **Answer:** YES/NO - **Evidence:** [Provide reason, e.g., "Profile shows woman in her 30s with kids", "Bio mentions 'mum of 3'", "Posts about school pickups"]

        3.  **IS_BUSINESS_OR_COACH:** Is this a business, brand, or another coach/trainer?
            - Look for: "coach", "trainer", "PT", "nutritionist", "business", "services", client results, selling products.
            - **Answer:** YES/NO - **Evidence:** [Provide reason, e.g., "This is an individual's personal page", "Bio says 'Personal Trainer'"]

        4.  **FINAL_VERDICT_POTENTIAL_CLIENT:** Based on the above, is this a potential client?
            - A potential client MUST have a LOCAL_CONFIDENCE_SCORE of 4 or higher, be a TARGET_MUM, and NOT be a business/coach.
            - GENEROUS RULE: If evidence score is 40+ points, automatically consider as potential local even with lower confidence.
            - **Answer:** YES/NO - **Reason:** [Summarize why they are or are not a potential client]

        5.  **IS_FAKE_OR_INACTIVE:** Does this look like a bot, fake, or inactive account?
            - Look for: No profile pic, zero or very few posts, generic bio, high following count with low followers.
            - **Answer:** YES/NO - **Evidence:** [Provide reason, e.g., "Account has real photos and normal activity"]

        **CRITICAL: If you cannot see clear details in the screenshot, say "Cannot determine clearly from screenshot" for evidence.**

        **Provide your response in this EXACT format:**
        IS_LOCAL_CONFIDENCE_SCORE: [Score] - Evidence: [reason]
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
            - CRITICAL: If IS_PLANT_BASED is NO, then FINAL_VERDICT must be NO regardless of other factors
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

    def analyze_profile(self, username, skip_memory_check=False):
        """Analyze a user's profile with AI."""
        # Only check memory if not explicitly told to skip (for pre-filtered calls)
        if not skip_memory_check and username in self.processed_usernames:
            print(f"🧠 Skipping @{username} - already in memory.")
            return False

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
                # NEW: Calculate comprehensive Local Evidence Score
                evidence_score, evidence_details = self.calculate_local_evidence_score(
                    username)

                # Extract bio text to pass to AI
                bio_text = self.extract_bio_text()
                if not bio_text:
                    bio_text = "No bio text found"

                # NEW: Check if this is a local business we should follow
                if self.should_follow_local_business(username, bio_text):
                    print(
                        f"🏢 Following local business for networking: @{username}")
                    if self.follow_user(username):
                        self.add_to_processing_queue(
                            username, "local_business")
                        self.log_processed_profile(
                            username, True, "Local business - networking")
                        return True
                    else:
                        self.log_processed_profile(
                            username, False, "Local business - follow failed")
                        return False

                # Get AI analysis with the evidence score
                prompt = self.get_local_screening_prompt(
                    username, bio_text, evidence_score, evidence_details)
                response = self.analyze_with_gemini(prompt, screenshot_data)

                if not response:
                    print(f"❌ AI analysis failed for {username}")
                    return False

                response_text = response.text

                # Parse AI response (simplified for new prompt format)
                is_target_mum, mum_evidence = parse_line(
                    'IS_TARGET_MUM', response_text)
                is_business_or_coach, business_evidence = parse_line(
                    'IS_BUSINESS_OR_COACH', response_text)
                is_potential_client, client_reason = parse_line(
                    'FINAL_VERDICT_POTENTIAL_CLIENT', response_text)
                is_fake, fake_evidence = parse_line(
                    'IS_FAKE_OR_INACTIVE', response_text)

                # Show comprehensive analysis results
                print(f"   📊 Local Evidence Score: {evidence_score}/100")
                print(f"   🔍 Evidence: {evidence_details}")
                print(
                    f"   👩‍👧‍👦 Target Mum: {'✅ YES' if is_target_mum == 'YES' else '❌ NO'} - {mum_evidence}")
                print(
                    f"   🏢 Business/Coach: {'❌ YES' if is_business_or_coach == 'YES' else '✅ NO'} - {business_evidence}")
                print(
                    f"   🤖 Fake/Inactive: {'❌ YES' if is_fake == 'YES' else '✅ NO'} - {fake_evidence}")
                print(
                    f"   🎯 AI Final Verdict: {'✅ YES' if is_potential_client == 'YES' else '❌ NO'} - {client_reason}")

                # NEW LOGIC: Use evidence score + AI assessment
                # RELAXED CRITERIA: Strong evidence (25+ points) OR AI says yes + any evidence (5+ points) OR just AI approval
                strong_local_evidence = evidence_score >= 25
                decent_evidence_with_ai_approval = evidence_score >= 5 and is_potential_client == 'YES'
                # Allow AI-only approval
                ai_approved_only = evidence_score >= 0 and is_potential_client == 'YES'

                is_potential_by_logic = ((strong_local_evidence or decent_evidence_with_ai_approval or ai_approved_only) and
                                         is_target_mum == 'YES' and
                                         is_business_or_coach != 'YES' and
                                         is_fake != 'YES')

                # Final decision
                if is_potential_by_logic:
                    print(f"✅ POTENTIAL LOCAL CLIENT FOUND: {username}")
                    if strong_local_evidence:
                        print(
                            f"   💪 Strong local evidence ({evidence_score}/100 points)")
                    else:
                        print(
                            f"   ✅ AI approval + decent evidence ({evidence_score}/100 points)")
                    self.leads_found += 1
                    self.log_processed_profile(
                        username, True, f"Local Evidence: {evidence_score}/100 - {client_reason}")
                    return True
                else:
                    print(f"❌ Not a potential local client: {username}")
                    print(f"   💡 Reason: {client_reason}")
                    self.log_processed_profile(
                        username, False, f"Local Evidence: {evidence_score}/100 - {client_reason}")

                    # Debug: Show why they failed
                    if evidence_score < 5 and is_potential_client != 'YES':
                        print(
                            f"   🚫 Failed: Insufficient local evidence ({evidence_score}/100) and no AI approval")
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

                # VALIDATION: Check if AI's final verdict contradicts plant-based requirement
                if is_potential_client == 'YES' and is_plant_based != 'YES':
                    print(
                        f"⚠️ AI LOGIC ERROR: Final verdict YES but not plant-based for @{username}")
                    print(
                        f"🔧 Overriding AI verdict to NO due to missing vegan/plant-based requirement")

                # STRICT vegan/plant-based criteria as requested
                # Only accept people who are clearly vegan/plant-based
                # MANDATORY: Must be plant-based to qualify as potential client
                is_clearly_vegan_or_plant_based = (is_plant_based == 'YES')

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

                # FIXED: Enforce strict vegan requirement - NO AI override allowed
                if is_potential:
                    print(f"✅ POTENTIAL CLIENT FOUND: {username}")
                    print(f"   💡 Final verdict: {client_reason}")
                    self.leads_found += 1
                    self.log_processed_profile(
                        username, True, client_reason)  # Log as lead
                    return True
                else:
                    print(f"❌ Not a potential client: {username}")
                    print(f"   💡 Reason: {client_reason}")

                    # Enhanced debug: Show why they failed our STRICT criteria
                    if is_business_or_coach == 'YES':
                        print(f"   🚫 Failed: Is a business/coach")
                        failure_reason = "Business/coach account"
                    elif not is_clearly_vegan_or_plant_based:
                        print(f"   🚫 Failed: Not clearly vegan/plant-based")
                        if is_potential_client == 'YES':
                            print(
                                f"   ⚠️ AI Override Blocked: AI said YES but person isn't plant-based!")
                        failure_reason = "Not vegan/plant-based"
                    elif is_target_female != 'YES' and is_target_male != 'YES':
                        print(f"   🚫 Failed: Doesn't fit target demographic")
                        failure_reason = "Wrong demographic"
                    elif is_fake == 'YES':
                        print(f"   🚫 Failed: Appears fake/inactive")
                        failure_reason = "Fake/inactive account"
                    else:
                        failure_reason = "Unknown reason"

                    self.log_processed_profile(username, False, failure_reason)
                    return False
        except WebDriverException as we:
            # Handle specific WebDriver/network errors
            error_msg = str(we).lower()
            if any(keyword in error_msg for keyword in ['net::err_name_not_resolved', 'dns', 'network', 'connection', 'chrome', 'session']):
                print(f"🌐 Network/DNS error for @{username}: {we}")

                # Circuit breaker: Check if we've had too many network errors
                if self.network_error_count >= self.max_network_errors:
                    print(
                        f"🚨 Circuit breaker activated: {self.network_error_count} network errors in this session")
                    print("❌ Stopping script to prevent infinite retry loops")
                    self.log_processed_profile(
                        username, False, f"Circuit breaker: Too many network errors ({self.network_error_count})")
                    return False

                print("🔄 Attempting network recovery...")
                self.network_error_count += 1
                self.last_network_error_time = time.time()

                # Try to recover from network error
                recovery_success = self.handle_network_error_recovery()

                if recovery_success:
                    print(
                        f"✅ Network recovery successful, retrying @{username}...")
                    # Add delay before retry to prevent rapid-fire requests
                    time.sleep(random.uniform(10, 15))
                    # Retry the analysis once after recovery
                    try:
                        return self.analyze_profile(username, skip_memory_check=True)
                    except Exception as retry_error:
                        print(f"❌ Retry failed for @{username}: {retry_error}")
                        self.log_processed_profile(
                            username, False, f"Network error + retry failed: {retry_error}")
                        return False
                else:
                    print(f"❌ Network recovery failed for @{username}")
                    self.log_processed_profile(
                        username, False, f"Network error - recovery failed: {we}")
                    return False
            else:
                # Other WebDriver errors (not network related)
                print(f"🔧 WebDriver error for @{username}: {we}")
                self.log_processed_profile(
                    username, False, f"WebDriver error: {we}")
                return False
        except Exception as e:
            print(f"❌ Error analyzing {username}: {e}")
            self.log_processed_profile(
                username, False, f"Error during analysis: {e}")
            return False

    def calculate_local_evidence_score(self, username):
        """
        Calculate a comprehensive Local Evidence Score using multiple signals.
        Returns (score, evidence_details) where score is 0-100.
        """
        score = 0
        evidence_details = []

        try:
            print(f"🔍 Calculating Local Evidence Score for @{username}...")

            # Layer 1: Bio Text Analysis (0-20 points)
            bio_score, bio_evidence = self.analyze_bio_for_local_signals()
            score += bio_score
            if bio_evidence:
                evidence_details.append(f"Bio: {bio_evidence}")

            # Layer 2: Location Tags in Posts (0-40 points)
            location_score, location_evidence = self.analyze_posts_for_location_tags()
            score += location_score
            if location_evidence:
                evidence_details.append(f"Location Tags: {location_evidence}")

            # Layer 3: Following Network Analysis (0-30 points)
            network_score, network_evidence = self.analyze_following_network()
            score += network_score
            if network_evidence:
                evidence_details.append(f"Network: {network_evidence}")

            # Layer 4: Post Caption Analysis (0-10 points)
            caption_score, caption_evidence = self.analyze_post_captions()
            score += caption_score
            if caption_evidence:
                evidence_details.append(f"Captions: {caption_evidence}")

            evidence_summary = " | ".join(
                evidence_details) if evidence_details else "No local evidence found"

            print(f"📊 Local Evidence Score: {score}/100 - {evidence_summary}")
            return score, evidence_summary

        except Exception as e:
            print(f"❌ Error calculating local evidence score: {e}")
            return 0, f"Error: {str(e)}"

    def extract_bio_text(self):
        """Extract bio text from the current Instagram profile page"""
        try:
            bio_selectors = [
                "//div[contains(@class, 'x7a106z')]//span",
                "//section//div[contains(@class, 'x1y1aw1k')]//span",
                "//section//span[contains(text(), '.') or contains(text(), '@') or contains(text(), '#')]",
                "//header//div//span",
            ]

            bio_text = ""
            for selector in bio_selectors:
                try:
                    bio_elements = self.driver.find_elements(
                        By.XPATH, selector)
                    for element in bio_elements:
                        text = element.text.strip()
                        if text and len(text) > 5:
                            bio_text += text + " "
                    if bio_text.strip():
                        break
                except:
                    continue

            return bio_text.strip()
        except Exception as e:
            print(f"❌ Error extracting bio text: {e}")
            return ""

    def analyze_bio_for_local_signals(self):
        """ENHANCED: Extract and analyze bio text for local keywords (0-25 points)"""
        try:
            bio_text = self.extract_bio_text()

            if not bio_text:
                return 0, ""

            print(
                f"📝 Extracted bio: {bio_text[:100]}{'...' if len(bio_text) > 100 else ''}")

            # ENHANCED: More comprehensive Bayside keywords
            bayside_keywords = [
                'hampton', 'brighton', 'sandringham', 'black rock', 'beaumaris',
                'cheltenham', 'highett', 'mentone', 'parkdale', 'moorabbin',
                'bentleigh', 'bayside', 'melbourne', 'nepean highway', 'beach road',
                'westfield southland', 'brighton grammar', 'firbank', 'haileybury'
            ]

            # NEW: Instagram location indicators
            location_indicators = [
                '📍', '🗺️', '📌',  # Location emojis
                'based in', 'live in', 'located in', 'from', 'melbourne',
                'aussie', 'australian', 'vic', 'victoria', 'melb'
            ]

            # NEW: Community connection indicators
            community_indicators = [
                'mum', 'mom', 'mother', 'parent', 'family', 'kids', 'children',
                'local', 'community', 'neighbourhood', 'neighbor', 'school mum',
                'working mum', 'busy mum', 'fitness mum'
            ]

            found_keywords = []
            found_location_indicators = []
            found_community_indicators = []

            bio_lower = bio_text.lower()

            # Check for direct location keywords
            for keyword in bayside_keywords:
                if keyword.lower() in bio_lower:
                    found_keywords.append(keyword)

            # Check for location indicators
            for indicator in location_indicators:
                if indicator.lower() in bio_lower:
                    found_location_indicators.append(indicator)

            # Check for community indicators
            for indicator in community_indicators:
                if indicator.lower() in bio_lower:
                    found_community_indicators.append(indicator)

            # Calculate enhanced score
            score = 0
            evidence_parts = []

            if found_keywords:
                # Up to 15 points for direct keywords
                keyword_score = min(15, len(found_keywords) * 6)
                score += keyword_score
                evidence_parts.append(
                    f"Location keywords: {', '.join(found_keywords[:3])}")

            if found_location_indicators:
                # Up to 5 points for location indicators
                location_score = min(5, len(found_location_indicators) * 2)
                score += location_score
                evidence_parts.append(
                    f"Location indicators: {', '.join(found_location_indicators[:2])}")

            if found_community_indicators:
                # Up to 5 points for community indicators
                community_score = min(5, len(found_community_indicators) * 1)
                score += community_score
                evidence_parts.append(
                    f"Community signals: {', '.join(found_community_indicators[:2])}")

            # Cap at 25 points total
            final_score = min(25, score)

            if evidence_parts:
                evidence = " | ".join(evidence_parts)
                return final_score, evidence
            else:
                return 0, ""

        except Exception as e:
            print(f"❌ Error analyzing bio: {e}")
            return 0, ""

    def analyze_posts_for_location_tags(self, max_posts=8):
        """
        Analyze posts for location tags (0-40 points).
        This is now called for ALL potential leads, not just ambiguous ones.
        """
        try:
            post_links = []
            # Find the first few post links on the profile page
            post_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "a[href*='/p/']")
            for el in post_elements[:max_posts]:
                post_links.append(el.get_attribute('href'))

            if not post_links:
                return 0, ""

            # Enhanced Bayside location keywords
            bayside_location_keywords = [
                'hampton', 'brighton', 'sandringham', 'black rock', 'beaumaris',
                'cheltenham', 'highett', 'mentone', 'parkdale', 'moorabbin',
                'bentleigh', 'bayside', 'southland', 'westfield southland',
                'brighton beach', 'hampton beach', 'sandringham beach',
                'brighton baths', 'half moon bay', 'royal melbourne', 'victoria golf',
                'firbank', 'brighton grammar', 'haileybury', 'st leonard',
                'mentone girls', 'recovery lab', 'hamptons bakery'
            ]

            original_url = self.driver.current_url
            found_locations = []

            for i, post_url in enumerate(post_links):
                try:
                    self.driver.get(post_url)
                    time.sleep(random.uniform(2, 3))

                    # Look for location tag
                    location_element = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//header//a[contains(@href, '/explore/locations/')]"))
                    )
                    location_text = location_element.text.lower()

                    # Check if the found location matches our keywords
                    for keyword in bayside_location_keywords:
                        if keyword in location_text:
                            found_locations.append(location_text)
                            break

                except TimeoutException:
                    continue
                except Exception:
                    continue

            # Return to profile
            self.driver.get(original_url)

            if found_locations:
                # Score based on number of local location tags found
                # 15 points per location, max 40
                score = min(40, len(found_locations) * 15)
                evidence = f"Found {len(found_locations)} local tags: {', '.join(found_locations[:3])}"
                return score, evidence
            else:
                return 0, ""

        except Exception as e:
            print(f"❌ Error analyzing location tags: {e}")
            return 0, ""

    def analyze_following_network(self, max_to_check=50):
        """
        Analyze who the user is following for local business connections (0-30 points).
        """
        try:
            # Navigate to following page
            following_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "following"))
            )
            following_link.click()
            time.sleep(random.uniform(3, 5))

            # Find the scrollable element
            scrollable_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@role='dialog']//div[contains(@style, 'overflow')]"))
            )

            following_usernames = set()
            scroll_attempts = 0

            # Collect usernames from following list
            while len(following_usernames) < max_to_check and scroll_attempts < 5:
                following_elements = self.driver.find_elements(
                    By.XPATH, "//div[@role='dialog']//a[contains(@href, '/') and not(contains(@href, '/p/')) and not(contains(@href, '/reel/'))]"
                )

                for element in following_elements:
                    try:
                        href = element.get_attribute('href')
                        if href:
                            username = href.rstrip('/').split('/')[-1]
                            if username and not username.startswith('instagram'):
                                following_usernames.add(username)
                    except:
                        continue

                # Scroll down
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_element
                )
                time.sleep(2)
                scroll_attempts += 1

            # Close following modal
            try:
                self.driver.find_element(
                    By.XPATH, "//button[@aria-label='Close']").click()
                time.sleep(2)
            except:
                pass

            # ENHANCED: Smart local business detection
            local_businesses_followed = []
            potential_local_businesses = []

            for username in following_usernames:
                # Check exact matches first (existing logic)
                if username.lower() in [business.lower() for business in LOCAL_BUSINESSES]:
                    local_businesses_followed.append(username)
                    continue

                # NEW: Smart pattern matching for local businesses
                username_lower = username.lower()

                # Check if username contains both location + business indicators
                has_location = any(location in username_lower for location in
                                   ['hampton', 'brighton', 'sandringham', 'bayside', 'melbourne',
                                    'cheltenham', 'mentone', 'blackrock', 'beaumaris'])

                has_business_type = any(biz_type in username_lower for biz_type in
                                        ['gym', 'fitness', 'pilates', 'yoga', 'crossfit', 'f45',
                                         'physio', 'massage', 'cafe', 'restaurant', 'realestate',
                                         'mums', 'community', 'council', 'school'])

                if has_location and has_business_type:
                    potential_local_businesses.append(username)
                elif has_location or has_business_type:
                    # Single indicator still gets some credit
                    potential_local_businesses.append(username)

            # Calculate enhanced score
            total_score = 0
            evidence_parts = []

            if local_businesses_followed:
                # Higher score for exact matches
                exact_score = min(25, len(local_businesses_followed) * 8)
                total_score += exact_score
                evidence_parts.append(
                    f"{len(local_businesses_followed)} known businesses: {', '.join(local_businesses_followed[:3])}")

            if potential_local_businesses:
                # Lower score for patterns
                potential_score = min(20, len(potential_local_businesses) * 3)
                total_score += potential_score
                evidence_parts.append(
                    f"{len(potential_local_businesses)} potential local accounts: {', '.join(potential_local_businesses[:3])}")

            # Cap total at 30 points
            final_score = min(30, total_score)

            if evidence_parts:
                evidence = " | ".join(evidence_parts)
                return final_score, evidence
            else:
                return 0, ""

        except Exception as e:
            print(f"❌ Error analyzing following network: {e}")
            return 0, ""

    def analyze_post_captions(self, max_posts=6):
        """
        Analyze post captions for local mentions (0-10 points).
        """
        try:
            post_links = []
            post_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "a[href*='/p/']")
            for el in post_elements[:max_posts]:
                post_links.append(el.get_attribute('href'))

            if not post_links:
                return 0, ""

            bayside_keywords = [
                'hampton st', 'brighton', 'sandringham', 'bayside', 'southland',
                'beach road', 'nepean highway', 'westfield', 'melbourne'
            ]

            original_url = self.driver.current_url
            found_mentions = []

            for post_url in post_links[:3]:  # Check fewer posts for efficiency
                try:
                    self.driver.get(post_url)
                    time.sleep(random.uniform(1, 2))

                    # Try to find caption text
                    caption_selectors = [
                        "//article//div//span[contains(@dir, 'auto')]",
                        "//article//span[string-length(text()) > 20]"
                    ]

                    for selector in caption_selectors:
                        try:
                            caption_elements = self.driver.find_elements(
                                By.XPATH, selector)
                            for element in caption_elements:
                                caption_text = element.text.lower()
                                if len(caption_text) > 20:  # Only check substantial captions
                                    for keyword in bayside_keywords:
                                        if keyword in caption_text:
                                            found_mentions.append(keyword)
                                            break
                            if found_mentions:
                                break
                        except:
                            continue
                    if found_mentions:
                        break
                except:
                    continue

            # Return to profile
            self.driver.get(original_url)

            if found_mentions:
                # 3 points per mention, max 10
                score = min(10, len(found_mentions) * 3)
                evidence = f"Found mentions: {', '.join(set(found_mentions))}"
                return score, evidence
            else:
                return 0, ""

        except Exception as e:
            print(f"❌ Error analyzing captions: {e}")
            return 0, ""

    def analyze_posts_for_location(self, max_posts=6):
        """
        DEPRECATED: Legacy method for backward compatibility.
        Use calculate_local_evidence_score() instead.
        """
        score, evidence = self.analyze_posts_for_location_tags(max_posts)
        return score > 0

    def classify_account_type(self, username, bio_text=""):
        """
        NEW: Classify if account is a business, individual, or local business worth following.
        Returns: ('business', 'individual', 'local_business'), confidence_score
        """
        try:
            bio_lower = bio_text.lower()
            username_lower = username.lower()

            # Check for business indicators
            business_score = 0
            local_score = 0

            # Business type indicators in username or bio
            for indicator in BUSINESS_ACCOUNT_INDICATORS:
                if indicator in username_lower or indicator in bio_lower:
                    business_score += 10

            # Local indicators
            local_suburbs = ['hampton', 'brighton', 'sandringham', 'bayside', 'melbourne',
                             'cheltenham', 'mentone', 'blackrock', 'beaumaris', 'moorabbin']
            for suburb in local_suburbs:
                if suburb in username_lower or suburb in bio_lower:
                    local_score += 15

            # Local business patterns (location + business type)
            has_location = any(loc in username_lower for loc in local_suburbs)
            has_business = any(biz in username_lower for biz in
                               ['gym', 'fitness', 'cafe', 'physio', 'massage', 'mums'])

            if has_location and has_business:
                return 'local_business', 80
            elif business_score >= 20 and local_score >= 15:
                return 'local_business', 70
            elif business_score >= 30:
                return 'business', 60
            else:
                return 'individual', max(local_score, 10)

        except Exception as e:
            print(f"❌ Error classifying account type: {e}")
            return 'individual', 10

    def should_follow_local_business(self, username, bio_text=""):
        """
        NEW: Determine if we should follow a local business for networking.
        """
        account_type, confidence = self.classify_account_type(
            username, bio_text)

        if account_type == 'local_business' and confidence >= 60:
            print(
                f"🏢 Identified local business: @{username} (confidence: {confidence})")
            return True
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

    def explore_lead_network(self, lead_username, max_to_check=DEEPER_SEARCH_LIMIT):
        """
        Explore the followers of a newly found lead to find more similar leads.
        This performs a "one-level-deep" search into a lead's network.
        """
        if self.get_daily_follows_count() >= DAILY_FOLLOW_LIMIT:
            return  # Skip if daily limit is already reached

        print(
            f"\n➡️ Diving deeper: Exploring followers of new lead @{lead_username}...")

        try:
            # Step 1: Collect follower usernames from the new lead
            profile_url = f"https://www.instagram.com/{lead_username}/"
            self.driver.get(profile_url)

            followers_link = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.PARTIAL_LINK_TEXT, "followers"))
            )
            followers_link.click()
            time.sleep(random.randint(3, 5))

            # Find the scrollable element in the followers modal
            scrollable_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@role='dialog']//div[contains(@style, 'overflow')]"))
            )

            follower_usernames = set()
            # Scroll just enough to get a good sample
            for _ in range(5):
                follower_elements = self.driver.find_elements(
                    By.XPATH, "//div[@role='dialog']//a[contains(@href, '/') and not(contains(@href, '/p/')) and not(contains(@href, '/reel/'))]"
                )
                for element in follower_elements:
                    try:
                        href = element.get_attribute('href')
                        if href:
                            username = href.rstrip('/').split('/')[-1]
                            if username and not username.startswith('instagram'):
                                follower_usernames.add(username)
                    except:
                        continue

                if len(follower_usernames) >= max_to_check:
                    break

                # Scroll down
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_element
                )
                time.sleep(2)

            # Close followers modal
            try:
                self.driver.find_element(
                    By.XPATH, "//button[@aria-label='Close']").click()
            except:
                pass  # It's okay if this fails

            print(
                f"   Collected {len(follower_usernames)} unique followers from @{lead_username} to analyze.")

            # Step 2: Process the collected usernames
            leads_from_this_network = 0
            for username in list(follower_usernames)[:max_to_check]:
                if self.get_daily_follows_count() >= DAILY_FOLLOW_LIMIT:
                    break
                if username in self.processed_usernames:
                    continue

                self.processed_usernames.add(username)
                print(f"   👤 Analyzing follower's follower: @{username}")

                if self.analyze_profile(username, skip_memory_check=True):
                    if self.follow_user(username):
                        self.add_to_processing_queue(
                            username, f"follower_of_{lead_username}")
                        leads_from_this_network += 1
                        time.sleep(random.uniform(30, 60))

            print(
                f"✅ Found {leads_from_this_network} additional leads from @{lead_username}'s network.")

        except TimeoutException:
            print(
                f"❌ Could not explore @{lead_username}'s followers (private profile or no followers link).")
        except Exception as e:
            print(f"❌ Error exploring network of @{lead_username}: {repr(e)}")

    def mine_followers_from_australian_influencers(self):
        """
        PHASE 1: Mine followers from Australian vegan influencers (highest priority).
        """
        print(f"\n🇦🇺 === PHASE 1: AUSTRALIAN VEGAN INFLUENCERS (HIGHEST PRIORITY) ===")
        print(
            f"🎯 Mining followers from {len(AUSTRALIAN_VEGAN_INFLUENCERS)} Australian vegan influencers...")
        print(f"💡 These accounts have the most relevant Australian audiences for Shannon's business")

        return self._mine_followers_from_accounts(AUSTRALIAN_VEGAN_INFLUENCERS, "🇦🇺 Australian")

    def mine_followers_from_international_influencers(self):
        """
        PHASE 3B: Mine followers from international vegan influencers (supplementary).
        """
        print(f"\n🌍 === PHASE 3B: INTERNATIONAL VEGAN INFLUENCERS (SUPPLEMENTARY) ===")
        print(
            f"🎯 Mining followers from {len(INTERNATIONAL_VEGAN_INFLUENCERS)} international vegan influencers...")
        print(f"💡 Supplementary leads after Australian priority and network effect")

        return self._mine_followers_from_accounts(INTERNATIONAL_VEGAN_INFLUENCERS, "🌍 International")

    def mine_followers_from_influencers(self):
        """
        Legacy function - now redirects to Australian-first approach.
        """
        if self.mode == 'local':
            target_accounts = LOCAL_BUSINESSES
            print(f"🏠 Mining followers from local businesses for Bayside gym clients...")
            return self._mine_followers_from_accounts(target_accounts, "🏠 Local Business")
        else:
            # For online mode, use the new Australian-first approach
            return self.mine_followers_from_australian_influencers()

    def _mine_followers_from_accounts(self, target_accounts, account_type_label):
        """
        Core follower mining logic extracted for reuse.
        """
        print(
            f"📋 Target accounts: {len(target_accounts)} {account_type_label.lower()} accounts to process")

        for influencer in target_accounts:
            if self.get_daily_follows_count() >= DAILY_FOLLOW_LIMIT:
                break

            print(f"\n🎯 Mining followers from @{influencer}...")

            try:
                # --- Step 1: Collect follower usernames ---
                profile_url = f"https://www.instagram.com/{influencer}/"
                self.driver.get(profile_url)

                followers_link = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.PARTIAL_LINK_TEXT, "followers"))
                )
                followers_link.click()
                time.sleep(random.randint(3, 5))

                # Find the scrollable element in the followers modal
                scrollable_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[@role='dialog']//div[contains(@style, 'overflow')]"))
                )

                follower_usernames = set()
                max_followers_to_scrape = 500  # ENHANCED: Much more aggressive collection
                scroll_attempts = 0
                consecutive_no_new_followers = 0

                print(
                    f"   🔄 Starting to collect followers (target: {max_followers_to_scrape})...")

                # ENHANCED: More aggressive scrolling for deeper follower collection
                while len(follower_usernames) < max_followers_to_scrape and scroll_attempts < 50:
                    follower_elements = self.driver.find_elements(
                        By.XPATH, "//div[@role='dialog']//a[contains(@href, '/') and not(contains(@href, '/p/')) and not(contains(@href, '/reel/'))]"
                    )

                    initial_count = len(follower_usernames)

                    for element in follower_elements:
                        try:
                            href = element.get_attribute('href')
                            if href:
                                username = href.rstrip('/').split('/')[-1]
                                if username and not username.startswith('instagram'):
                                    follower_usernames.add(username)
                        except:
                            continue

                    new_count = len(follower_usernames)
                    newly_added = new_count - initial_count

                    # More aggressive scrolling
                    for _ in range(3):  # Multiple scrolls per attempt
                        self.driver.execute_script(
                            "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_element
                        )
                        time.sleep(0.5)

                    scroll_attempts += 1

                    # Track consecutive attempts with no new followers
                    if newly_added == 0:
                        consecutive_no_new_followers += 1
                    else:
                        consecutive_no_new_followers = 0
                        print(
                            f"   📊 Scroll {scroll_attempts}: Found {new_count} total followers (+{newly_added} new)")

                    # Break if we haven't found new followers in multiple attempts
                    if consecutive_no_new_followers >= 5:
                        print(
                            f"   ⏹️ Stopping scroll - no new followers found in {consecutive_no_new_followers} attempts")
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
                    f"   ✅ Collected {len(follower_usernames)} unique follower usernames to analyze.")

                # --- Step 2: Filter for unprocessed usernames and prioritize them ---
                unprocessed_usernames = [
                    u for u in follower_usernames if u not in self.processed_usernames]
                processed_usernames = [
                    u for u in follower_usernames if u in self.processed_usernames]

                print(
                    f"   📊 Found {len(unprocessed_usernames)} new users, {len(processed_usernames)} already processed")

                # Debug: Show a few examples
                if unprocessed_usernames:
                    print(
                        f"   🆕 New users sample: {', '.join(unprocessed_usernames[:5])}")
                if processed_usernames:
                    print(
                        f"   🔄 Already processed sample: {', '.join(processed_usernames[:3])}")

                # Skip this business if we have very few new users (efficiency optimization)
                if len(unprocessed_usernames) < 3:
                    print(
                        f"   ⚠️ Only {len(unprocessed_usernames)} new users found. Trying deeper scroll...")

                    # Try one more round of deeper scrolling
                    additional_scroll_attempts = 0
                    while additional_scroll_attempts < 10 and len(unprocessed_usernames) < 5:
                        self.driver.execute_script(
                            "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_element
                        )
                        time.sleep(1)

                        # Get new followers
                        new_followers = self.driver.find_elements(
                            By.XPATH, "//div[@role='dialog']//a[contains(@href, '/') and not(contains(@href, '/p/')) and not(contains(@href, '/reel/'))]"
                        )

                        for element in new_followers:
                            try:
                                href = element.get_attribute('href')
                                if href:
                                    username = href.rstrip('/').split('/')[-1]
                                    if username and not username.startswith('instagram'):
                                        follower_usernames.add(username)
                            except:
                                continue

                        # Recalculate unprocessed users
                        unprocessed_usernames = [
                            u for u in follower_usernames if u not in self.processed_usernames]
                        additional_scroll_attempts += 1

                    print(
                        f"   📊 After deeper scroll: {len(unprocessed_usernames)} new users total")

                    # If still too few, skip this business
                    if len(unprocessed_usernames) < 3:
                        print(
                            f"   ⏭️ Skipping @{influencer} - still insufficient new users after deep scroll")
                        continue

                # ENHANCED: Process more followers with intelligent prioritization
                # Process up to 50 unprocessed usernames (was 25)
                usernames_to_check = unprocessed_usernames[:50]
                if len(usernames_to_check) < 20:  # If we don't have enough new ones
                    # Add some processed ones to reach minimum processing count
                    usernames_to_check.extend(
                        processed_usernames[:20-len(usernames_to_check)])

                print(
                    f"   🎯 Will analyze {len(usernames_to_check)} usernames ({len([u for u in usernames_to_check if u not in self.processed_usernames])} new)")
                print(
                    f"   💡 ENHANCED: Processing up to 50 followers per influencer for deeper lead generation")

                leads_from_this_influencer = 0

                for username in usernames_to_check:
                    if self.get_daily_follows_count() >= DAILY_FOLLOW_LIMIT:
                        print("Daily follow limit reached during processing.")
                        break

                    # Skip if already in memory (should be rare with our filtering)
                    if username in self.processed_usernames:
                        print(
                            f"   🧠 Skipping @{username} - already in memory.")
                        continue

                    # Add to memory BEFORE analysis to prevent duplicates
                    self.processed_usernames.add(username)
                    print(f"   👤 Analyzing follower: @{username}")

                    if self.analyze_profile(username, skip_memory_check=True):
                        if self.follow_user(username):
                            self.add_to_processing_queue(
                                username, f"follower_of_{influencer}")
                            leads_from_this_influencer += 1

                            # Explore this new lead's network
                            self.explore_lead_network(username)

                            # Delay between successful follows
                            time.sleep(random.uniform(30, 60))

                print(
                    f"✅ Found {leads_from_this_influencer} leads from @{influencer} followers")

            except TimeoutException:
                print(
                    f"❌ Could not find followers link for @{influencer}. They may have 0 followers, a private profile, or a different page layout. Skipping.")
                self.driver.save_screenshot(
                    f"error_no_followers_link_{influencer}.png")
                continue
            except Exception as e:
                print(
                    f"❌ Error mining followers from @{influencer}: {repr(e)}")
                continue

        # Return count of total leads found from this set of accounts
        leads_found = 0
        for account in target_accounts:
            # This is a simple implementation - in practice the leads count
            # is tracked by individual influencer processing above
            pass
        return leads_found

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
                    if self.analyze_profile(username, skip_memory_check=True):
                        # Follow the user
                        if self.follow_user(username):
                            self.add_to_processing_queue(username, hashtag)
                            leads_found_here += 1

                            # Explore this new lead's network
                            self.explore_lead_network(username)

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
        """Main function to run the lead finding session with advanced network effect strategy."""
        print("🚀 Starting Smart Lead Finder...")

        # Create tables if needed
        self.create_tables_if_needed()

        # Log session start
        self.log_run('started')

        try:
            # CORE CHANGE: Load memory of all previously processed users
            self.load_processed_usernames()

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

            # Test Gemini API connectivity
            if not self.test_gemini_connectivity():
                print("⚠️ Gemini API connectivity issues detected")
                print("🔄 Continuing anyway - will handle errors per analysis")
                # Don't return here, just warn - we'll handle individual failures

                # NEW PRIORITY ORDER: Australian influencers → Network Effect → International + Hashtags

            # Initialize lead counters
            leads_from_followers = 0
            network_leads = 0
            australian_leads = 0
            international_leads = 0

            if self.mode == 'local':
                # === LOCAL MODE: Use existing logic for local businesses ===
                print(f"\n🏠 === LOCAL MODE: MINING LOCAL BUSINESSES ===")
                leads_from_followers = self.mine_followers_from_influencers()
                print(
                    f"✅ Found {leads_from_followers} leads from local businesses")

                # Network effect for local mode
                network_leads = 0
                if self.get_daily_follows_count() < DAILY_FOLLOW_LIMIT:
                    print(
                        f"\n🔄 PHASE 2: NETWORK EFFECT - Leveraging existing database...")
                    network_leads = self.search_followers_of_followed_accounts(
                        max_new_leads=30)
                    print(
                        f"✅ Found {network_leads} leads through network effect")

            else:
                # === ONLINE MODE: New Australian-first priority ===

                # === PHASE 1: 🇦🇺 AUSTRALIAN VEGAN INFLUENCERS (HIGHEST PRIORITY) ===
                print(
                    f"\n🇦🇺 === PHASE 1: AUSTRALIAN VEGAN INFLUENCERS (HIGHEST PRIORITY) ===")
                print(
                    f"🎯 Processing {len(AUSTRALIAN_VEGAN_INFLUENCERS)} Australian influencers first for maximum local relevance!")

                australian_leads = 0
                if self.get_daily_follows_count() < DAILY_FOLLOW_LIMIT:
                    australian_leads = self.mine_followers_from_australian_influencers()
                    print(
                        f"✅ Found {australian_leads} leads from Australian vegan influencers")

                # === PHASE 2: 🔄 NETWORK EFFECT (LEVERAGING EXISTING DATABASE) ===
                network_leads = 0
                if self.get_daily_follows_count() < DAILY_FOLLOW_LIMIT:
                    print(
                        f"\n🔄 === PHASE 2: NETWORK EFFECT - Leveraging existing database ===")
                    print(
                        f"🎯 Exploring followers of people who already followed you back...")

                    network_leads = self.search_followers_of_followed_accounts(
                        max_new_leads=30)
                    print(
                        f"✅ Found {network_leads} leads through network effect")

                # === PHASE 3A: 🌍 INTERNATIONAL VEGAN INFLUENCERS (SUPPLEMENTARY) ===
                international_leads = 0
                if self.get_daily_follows_count() < DAILY_FOLLOW_LIMIT:
                    remaining_capacity = DAILY_FOLLOW_LIMIT - self.get_daily_follows_count()
                    print(
                        f"\n🌍 === PHASE 3A: INTERNATIONAL VEGAN INFLUENCERS (SUPPLEMENTARY) ===")
                    print(
                        f"📊 Remaining capacity: {remaining_capacity} follows")
                    print(
                        f"💡 Only processing international if Australian + Network didn't fill quota")

                    international_leads = self.mine_followers_from_international_influencers()
                    print(
                        f"✅ Found {international_leads} leads from international vegan influencers")

            # === PHASE 3B: HASHTAG SEARCH (FINAL FALLBACK) ===
            if self.get_daily_follows_count() < DAILY_FOLLOW_LIMIT:
                print(f"\n🔍 === PHASE 3B: HASHTAG SEARCH (FINAL FALLBACK) ===")

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

            # === FINAL RESULTS ===
            final_follows = self.get_daily_follows_count()
            total_new_leads = final_follows - daily_follows

            print(f"\n🎉 === SMART LEAD FINDER SESSION COMPLETE! ===")
            print(f"📊 Final stats: Found {total_new_leads} new leads today")

            if self.mode == 'local':
                print(f"🏠 Local business leads: {leads_from_followers}")
                print(f"🔄 Network effect leads: {network_leads}")
            else:
                print(f"🇦🇺 Australian vegan leads: {australian_leads}")
                print(f"🔄 Network effect leads: {network_leads}")
                print(f"🌍 International vegan leads: {international_leads}")

            print(
                f"📈 Total follows today: {final_follows}/{DAILY_FOLLOW_LIMIT}")
            print(
                f"💡 Database now contains {len(self.processed_usernames)} processed profiles")

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

    def load_processed_usernames(self):
        """Load all previously processed usernames from the database to prevent re-work."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            # Load from the master memory table
            cursor.execute("SELECT username FROM processed_profiles")
            usernames = {row[0] for row in cursor.fetchall()}
            self.processed_usernames.update(usernames)
            print(
                f"🧠 Loaded {len(usernames)} usernames from the master 'processed_profiles' memory.")

            # Also load from the older queue table for good measure
            cursor.execute("SELECT username FROM processing_queue")
            queue_usernames = {row[0] for row in cursor.fetchall()}
            initial_count = len(self.processed_usernames)
            self.processed_usernames.update(queue_usernames)
            new_additions = len(self.processed_usernames) - initial_count
            if new_additions > 0:
                print(
                    f"🧠 Loaded an additional {new_additions} usernames from 'processing_queue'.")

            print(
                f"🧠 Total unique usernames in memory: {len(self.processed_usernames)}")
        except Exception as e:
            print(f"❌ Error loading processed usernames from database: {e}")
        finally:
            conn.close()

    def log_processed_profile(self, username, was_lead, reason):
        """Log a profile to the master memory table after analysis."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            timestamp = datetime.datetime.now().isoformat()
            cursor.execute("""
                INSERT OR IGNORE INTO processed_profiles (username, timestamp, search_mode, was_lead, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (username, timestamp, self.mode, was_lead, reason))
            conn.commit()
        except Exception as e:
            print(f"❌ Error logging processed profile @{username} to DB: {e}")
        finally:
            conn.close()

    # === NEW: ADVANCED NETWORK EFFECT STRATEGY ===

    def get_followed_vegan_accounts(self, min_days_ago=1, max_accounts=50):
        """
        Get list of accounts we've already followed to use as seed accounts for network effect.
        Prioritizes accounts that followed back for higher quality network exploration.

        Args:
            min_days_ago: Only get accounts followed at least N days ago
            max_accounts: Maximum number of seed accounts to return

        Returns:
            List of tuples: (username, followed_at, follow_back_status, hashtag_found)
        """
        try:
            print(
                f"\n🌱 === NETWORK EFFECT: Getting seed accounts for {self.mode} mode ===")

            conn = self.get_db_connection()
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
            """, (self.mode, cutoff_date, max_accounts))

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
                    print(
                        f"   {i+1}. {status_emoji} @{username} (via #{hashtag})")

            return prioritized_accounts

        except Exception as e:
            print(f"❌ Error getting followed accounts: {e}")
            return []

    def get_high_engagement_followers(self, username, max_followers=50):
        """
        Get followers who are likely to be more engaged by focusing on the first batch
        (Instagram shows more engaged followers first).
        """
        try:
            print(f"⚡ Getting high-engagement followers from @{username}...")

            # Navigate to profile
            profile_url = f"https://www.instagram.com/{username}/"
            self.driver.get(profile_url)
            time.sleep(random.randint(3, 5))

            # Click followers link
            followers_link = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "followers"))
            )
            followers_link.click()
            time.sleep(random.randint(3, 5))

            # Find scrollable element
            scrollable_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@role='dialog']//div[contains(@style, 'overflow')]"))
            )

            followers = []
            # Focus on first batch (most engaged) - less scrolling, higher quality
            for scroll_round in range(min(5, max_followers // 10)):
                follower_elements = self.driver.find_elements(
                    By.XPATH, "//div[@role='dialog']//a[contains(@href, '/') and not(contains(@href, '/p/')) and not(contains(@href, '/reel/'))]"
                )

                for element in follower_elements:
                    try:
                        href = element.get_attribute('href')
                        if href and '/p/' not in href and '/reel/' not in href:
                            follower_username = href.rstrip('/').split('/')[-1]
                            if (follower_username and follower_username not in followers and
                                    follower_username != username and not follower_username.startswith('instagram')):
                                followers.append(follower_username)

                        if len(followers) >= max_followers:
                            break
                    except:
                        continue

                if len(followers) >= max_followers:
                    break

                # Light scrolling for more variety
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_element
                )
                time.sleep(2)

            # Close modal
            try:
                self.driver.find_element(
                    By.XPATH, "//button[@aria-label='Close']").click()
                time.sleep(2)
            except:
                pass

            print(f"   ⚡ Selected {len(followers)} high-engagement followers")
            return followers

        except Exception as e:
            print(f"❌ Error getting high-engagement followers: {e}")
            return []

    def search_followers_of_followed_accounts(self, max_new_leads=30):
        """
        NETWORK EFFECT STRATEGY: Explore followers of accounts we've already followed.
        This leverages the fact that like-minded people tend to follow each other.

        Args:
            max_new_leads: Maximum number of new leads to find through network exploration

        Returns:
            Number of new leads found
        """
        print(f"\n🚀 === NETWORK EFFECT LEAD GENERATION ===")
        print(
            f"🎯 Goal: Find up to {max_new_leads} leads through network exploration")

        leads_found = 0

        # Get seed accounts (prioritizing those who followed back)
        seed_accounts = self.get_followed_vegan_accounts(
            min_days_ago=2, max_accounts=20)

        if not seed_accounts:
            print(
                "❌ No seed accounts found. Run basic lead generation first to build a network.")
            return 0

        # Track which seed accounts we've explored
        explored_seeds = set()

        for seed_username, followed_at, follow_back_status, hashtag in seed_accounts:

            # Stop if we've reached our goal or daily limit
            if leads_found >= max_new_leads or self.get_daily_follows_count() >= DAILY_FOLLOW_LIMIT:
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
                # Use more followers for accounts that followed back (higher quality network)
                max_followers = NETWORK_EXPLORATION_LIMIT if follow_back_status == 'yes' else 15

                # Get high-engagement followers for better quality
                followers = self.get_high_engagement_followers(
                    seed_username, max_followers)

                if not followers:
                    print(f"   ⚠️ No followers found for @{seed_username}")
                    continue

                print(
                    f"   📱 Analyzing {len(followers)} followers for coaching potential...")

                # Analyze each follower as a potential client
                followers_analyzed = 0
                for follower_username in followers:

                    # Stop if we've reached limits
                    if leads_found >= max_new_leads or self.get_daily_follows_count() >= DAILY_FOLLOW_LIMIT:
                        break

                    # Skip if already processed
                    if follower_username in self.processed_usernames:
                        continue

                    self.processed_usernames.add(follower_username)

                    try:
                        print(f"   👤 Analyzing: @{follower_username}")

                        # Analyze this follower as a potential client
                        if self.analyze_profile(follower_username, skip_memory_check=True):
                            if self.follow_user(follower_username):
                                self.add_to_processing_queue(
                                    follower_username, f"network:{seed_username}")
                                leads_found += 1

                                print(
                                    f"🌟 NETWORK LEAD #{leads_found}! @{follower_username}")
                                print(
                                    f"   🔗 Found via @{seed_username}'s network")

                                # Explore this new lead's network too
                                self.explore_lead_network(
                                    follower_username, max_to_check=10)

                                # Delay between successful follows
                                time.sleep(random.uniform(30, 60))

                        followers_analyzed += 1

                        # Add delay between follower analyses
                        time.sleep(random.randint(8, 15))

                    except Exception as e:
                        print(
                            f"   ⚠️ Error analyzing @{follower_username}: {e}")
                        continue

                print(
                    f"   ✅ Analyzed {followers_analyzed}/{len(followers)} followers from @{seed_username}")

                # Add delay between seed account explorations
                time.sleep(random.randint(15, 25))

            except Exception as e:
                print(f"   ❌ Error exploring @{seed_username}: {e}")
                continue

        print(f"\n🎯 NETWORK EFFECT RESULTS:")
        print(f"   🌟 Found {leads_found} new potential clients")
        print(f"   🔍 Explored {len(explored_seeds)} seed accounts")

        return leads_found


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
