import argparse
import sys
import os
import fix_emojis
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import datetime
import json
import google.generativeai as genai
import google.api_core.exceptions
from scripts.sheets_integration import GoogleSheetsManager
import re
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import traceback
import random
import pickle
import os.path

# --- NEW: Import SQLite utilities ---
from app.dashboard_modules.dashboard_sqlite_utils import (
    get_db_connection,
    save_metrics_to_sqlite,
    load_conversations_from_sqlite,
    add_message_to_history,
    create_user_table_if_not_exists
)

# --- Global Variables (will be set by argument parsing if run directly) ---
args = None
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FOLLOWERS_LIST = os.path.join(
    SCRIPT_DIR, 'instagram_followers.txt')  # Default value

# --- CHANGED: Use SQLite instead of JSON ---
SQLITE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"
# Keep JSON as backup/legacy (but primary storage is now SQLite)
ANALYTICS_FILE = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"

# --- Browser Setup ---
chrome_options = Options()
# chrome_options.add_argument("--headless")  # COMMENTED OUT - Run in visible mode to see what's happening
# chrome_options.add_argument("--no-startup-window")  # COMMENTED OUT - Allow startup window
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# Disable web security for automation
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-extensions")  # Disable extensions
chrome_options.add_argument("--disable-plugins")  # Disable plugins
# chrome_options.add_argument("--disable-images")  # COMMENTED OUT - Enable images so you can see what's happening
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
# chrome_options.add_argument("--remote-debugging-port=0")  # COMMENTED OUT - Allow debugging
# chrome_options.add_argument("--disable-logging")  # COMMENTED OUT - Enable logging
# chrome_options.add_argument("--log-level=3")  # COMMENTED OUT - Show more logs
# chrome_options.add_argument("--silent")  # COMMENTED OUT - Don't be silent
chrome_options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
# Changed back to True so you can see the browser
chrome_options.add_experimental_option("detach", True)
chrome_options.add_experimental_option(
    "excludeSwitches", ["enable-automation", "enable-logging"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# --- Instagram Credentials ---
USERNAME = "cocos_connected"
PASSWORD = "Shannonb3"

# --- Gemini API Key ---
GEMINI_API_KEY = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

# --- Google Sheets Service Account ---
SHEETS_SERVICE_ACCOUNT = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\sheets_credentials.json"

# Initialize services
sheets_manager = GoogleSheetsManager(SHEETS_SERVICE_ACCOUNT)
genai.configure(api_key=GEMINI_API_KEY)

# Initialize all three Gemini models
gemini_models = [
    ('gemini-2.0-flash', genai.GenerativeModel('gemini-2.0-flash')),
    ('gemini-2.0-flash-lite', genai.GenerativeModel('gemini-2.0-flash-lite')),
    ('gemini-2.0-flash-thinking-exp-01-21',
     genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21'))
]


def find_chromedriver():
    """Find a valid ChromeDriver executable from multiple common locations"""
    if args and args.chromedriver and os.path.exists(args.chromedriver):
        print(f"Using user-specified ChromeDriver: {args.chromedriver}")
        return args.chromedriver

    potential_paths = [
        r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe",
        r"C:\chromedriver.exe",
        r"C:\chromedriver\chromedriver.exe",
        r"C:\WebDrivers\chromedriver.exe",
        r"C:\Program Files\ChromeDriver\chromedriver.exe",
        r"C:\Program Files (x86)\ChromeDriver\chromedriver.exe",
        os.path.join(os.path.expanduser("~"), "chromedriver.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "chromedriver.exe"),
        os.path.join(os.path.expanduser("~"), "Desktop", "chromedriver.exe"),
        os.path.join(os.getcwd(), "chromedriver.exe"),
        os.path.join(SCRIPT_DIR, "chromedriver.exe"),
        os.path.join(SCRIPT_DIR, "drivers", "chromedriver.exe"),
    ]

    for path in potential_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            print(f"Found ChromeDriver at: {path}")
            return path

    print("ERROR: Could not find ChromeDriver in any of the expected locations.")
    return None


def save_cookies(driver, username):
    """Save browser cookies to a file"""
    cookies_dir = os.path.join(SCRIPT_DIR, "cookies")
    os.makedirs(cookies_dir, exist_ok=True)
    cookies_file = os.path.join(cookies_dir, f"{username}_cookies.pkl")
    pickle.dump(driver.get_cookies(), open(cookies_file, "wb"))
    print("Cookies saved successfully")


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
            print("Cookies loaded successfully")
            return True
        return False
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return False


def check_login_status(driver):
    """Check if currently logged into Instagram"""
    try:
        # Multiple checks to verify login status
        current_url = driver.current_url.lower()

        # If we're still on the login page, we're not logged in
        if "login" in current_url or "accounts/login" in current_url:
            print("Still on login page")
            return False

        # Try to find elements that only appear when logged in
        try:
            # Look for profile icon
            profile_icon = driver.find_element(
                By.CSS_SELECTOR, "span[role='link']")
            if profile_icon:
                print("Found profile icon")
                return True
        except:
            pass

        try:
            # Look for search bar
            search_bar = driver.find_element(
                By.CSS_SELECTOR, "input[placeholder*='Search']")
            if search_bar:
                print("Found search bar")
                return True
        except:
            pass

        try:
            # Look for home icon
            home_icon = driver.find_element(
                By.CSS_SELECTOR, "svg[aria-label*='Home']")
            if home_icon:
                print("Found home icon")
                return True
        except:
            pass

        print("No logged-in indicators found")
        return False

    except Exception as e:
        print(f"Error checking login status: {e}")
        return False


def login_to_instagram(driver, username, password):
    """Login to Instagram account with cookie support"""
    try:
        print("\n=== Starting Instagram Login ===")

        # Clear all cookies at start
        driver.delete_all_cookies()
        print("Cleared all cookies to force fresh login")

        # Navigate to login page and wait
        driver.get("https://www.instagram.com/accounts/login/")
        print("Navigating to login page...")
        time.sleep(5)  # Increased wait time

        # Check if we're actually on the login page
        print(f"🔍 Current URL: {driver.current_url}")
        print(f"🔍 Page title: {driver.title}")

        # Execute stealth script
        stealth_script = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """
        driver.execute_script(stealth_script)

        # Wait for login form with multiple selectors
        print("Looking for username field...")
        username_field = None

        # Try multiple selectors for username field
        username_selectors = [
            (By.NAME, "username"),
            (By.CSS_SELECTOR, "input[name='username']"),
            (By.CSS_SELECTOR, "input[aria-label*='username']"),
            (By.CSS_SELECTOR, "input[aria-label*='Username']"),
            (By.CSS_SELECTOR, "input[placeholder*='username']"),
            (By.CSS_SELECTOR, "input[placeholder*='Username']"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.XPATH, "//input[@name='username']"),
            (By.XPATH, "//input[contains(@aria-label, 'username')]"),
            (By.XPATH, "//input[contains(@placeholder, 'username')]")
        ]

        for i, (by_method, selector) in enumerate(username_selectors):
            try:
                print(
                    f"🔍 Trying username selector {i+1}/{len(username_selectors)}: {by_method} = '{selector}'")
                username_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((by_method, selector))
                )
                print(
                    f"✅ Found username field with selector: {by_method} = '{selector}'")
                break
            except Exception as e:
                print(f"❌ Failed selector {i+1}: {str(e)[:100]}")
                continue

        if not username_field:
            print("❌ Could not find username field with any selector!")
            print("🔍 Available input elements on page:")
            try:
                inputs = driver.find_elements(By.TAG_NAME, "input")
                for j, inp in enumerate(inputs[:10]):  # Show first 10 inputs
                    print(f"  Input {j+1}: type='{inp.get_attribute('type')}', name='{inp.get_attribute('name')}', placeholder='{inp.get_attribute('placeholder')}', aria-label='{inp.get_attribute('aria-label')}'")
            except Exception as debug_e:
                print(f"❌ Could not debug input elements: {debug_e}")

            # Take a screenshot for debugging
            try:
                driver.save_screenshot("debug_login_page.png")
                print("📸 Saved screenshot as debug_login_page.png for debugging")
            except:
                pass
            return False

        print("Found username field, entering credentials...")
        # Clear and enter username
        username_field.clear()
        time.sleep(1)
        for char in username:
            username_field.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))

        time.sleep(2)

        # Find password field with multiple selectors
        print("Looking for password field...")
        password_field = None

        password_selectors = [
            (By.NAME, "password"),
            (By.CSS_SELECTOR, "input[name='password']"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[aria-label*='password']"),
            (By.CSS_SELECTOR, "input[aria-label*='Password']"),
            (By.XPATH, "//input[@name='password']"),
            (By.XPATH, "//input[@type='password']"),
            (By.XPATH, "//input[contains(@aria-label, 'password')]")
        ]

        for i, (by_method, selector) in enumerate(password_selectors):
            try:
                print(
                    f"🔍 Trying password selector {i+1}/{len(password_selectors)}: {by_method} = '{selector}'")
                password_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((by_method, selector))
                )
                print(
                    f"✅ Found password field with selector: {by_method} = '{selector}'")
                break
            except Exception as e:
                print(f"❌ Failed selector {i+1}: {str(e)[:100]}")
                continue

        if not password_field:
            print("❌ Could not find password field!")
            return False

        # Clear and enter password
        password_field.clear()
        time.sleep(1)
        for char in password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))

        time.sleep(2)

        # Click login button with multiple selectors
        print("Attempting to click login button...")
        login_button = None

        login_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Log in')]"),
            (By.XPATH, "//button[contains(text(), 'Log In')]"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.CSS_SELECTOR, "button[class*='_acan']"),
            (By.XPATH, "//div[@role='button'][contains(text(), 'Log in')]"),
            # Additional selectors for Instagram's current design
            (By.CSS_SELECTOR, "button"),  # Any button element
            # Any element with button role
            (By.CSS_SELECTOR, "[role='button']"),
            (By.CSS_SELECTOR, "div[role='button']"),  # Div acting as button
            (By.XPATH, "//button"),  # Any button via XPath
            # Any element with button role via XPath
            (By.XPATH, "//*[@role='button']"),
            # Button with 'login' in class
            (By.CSS_SELECTOR, "button[class*='login']"),
            # Common Instagram button class
            (By.CSS_SELECTOR, "button[class*='_aa4b']"),
            # Common Instagram div button class
            (By.CSS_SELECTOR, "div[class*='_aa4b']"),
        ]

        for i, (by_method, selector) in enumerate(login_selectors):
            try:
                print(
                    f"🔍 Trying login button selector {i+1}/{len(login_selectors)}: {by_method} = '{selector}'")
                login_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((by_method, selector))
                )
                print(
                    f"✅ Found login button with selector: {by_method} = '{selector}'")
                break
            except Exception as e:
                print(f"❌ Failed selector {i+1}: {str(e)[:100]}")
                continue

        if not login_button:
            print("❌ Could not find login button with any selector!")
            print("🔍 Available button elements on page:")
            try:
                # Show all button elements
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for j, btn in enumerate(buttons[:10]):  # Show first 10 buttons
                    print(
                        f"  Button {j+1}: type='{btn.get_attribute('type')}', class='{btn.get_attribute('class')}', text='{btn.text[:30]}', role='{btn.get_attribute('role')}'")

                # Show all elements with button role
                role_buttons = driver.find_elements(
                    By.CSS_SELECTOR, "[role='button']")
                print(
                    f"\n🔍 Elements with role='button' ({len(role_buttons)} found):")
                for j, btn in enumerate(role_buttons[:10]):  # Show first 10
                    print(
                        f"  RoleButton {j+1}: tag='{btn.tag_name}', class='{btn.get_attribute('class')}', text='{btn.text[:30]}'")

            except Exception as debug_e:
                print(f"❌ Could not debug button elements: {debug_e}")

            # Take a screenshot for debugging
            try:
                driver.save_screenshot("debug_login_buttons.png")
                print("📸 Saved screenshot as debug_login_buttons.png for debugging")
            except:
                pass

            # Try to find any clickable element near the password field as a last resort
            print("🔍 Attempting to find clickable element near password field...")
            try:
                # Look for clickable elements after the password field
                clickable_elements = driver.find_elements(
                    By.CSS_SELECTOR, "*[role='button'], button, input[type='submit'], [type='submit']")
                if clickable_elements:
                    for j, elem in enumerate(clickable_elements[:5]):
                        try:
                            if elem.is_displayed() and elem.is_enabled():
                                print(
                                    f"  Trying clickable element {j+1}: {elem.tag_name} with text '{elem.text[:30]}' and class '{elem.get_attribute('class')}'")
                                login_button = elem
                                break
                        except:
                            continue
            except Exception as fallback_e:
                print(f"❌ Fallback clickable search failed: {fallback_e}")

            if not login_button:
                return False

        login_button.click()

        # Wait longer for login to complete
        print("Waiting for login to complete...")
        time.sleep(15)

        # Verify login multiple times
        max_attempts = 3
        for attempt in range(max_attempts):
            print(f"🔍 Login verification attempt {attempt + 1}/{max_attempts}")
            if check_login_status(driver):
                print("✅ Login successful!")
                save_cookies(driver, USERNAME)
                handle_post_login_popups(driver)
                return True
            print(
                f"❌ Login verification attempt {attempt + 1}/{max_attempts} failed, waiting...")
            print(f"🔍 Current URL after attempt: {driver.current_url}")
            time.sleep(5)

        print("❌ Login verification failed after all attempts")
        return False

    except Exception as e:
        print(f"❌ Login error: {e}")
        import traceback
        traceback.print_exc()
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
        print(f"Error handling popups: {e}")


def extract_profile_info(driver, username):
    """Extract comprehensive profile information"""
    profile_info = {
        'bio': '',
        'follower_count': '',
        'following_count': '',
        'post_count': '',
        'full_name': '',
        'external_url': '',
        'verified': False
    }

    try:
        print(f"🔍 Extracting profile information for {username}...")

        # Extract bio
        try:
            bio_selectors = [
                "//div[contains(@class, '_aa_c')]//span",
                "//div[@data-testid='user-bio']",
                "//div[contains(@class, '_ac7v')]//span",
                "//article//div[contains(@class, '_a9ze')]//span"
            ]

            for selector in bio_selectors:
                try:
                    bio_element = driver.find_element(By.XPATH, selector)
                    if bio_element and bio_element.text.strip():
                        profile_info['bio'] = bio_element.text.strip()
                        print(f"✅ Found bio: {profile_info['bio'][:100]}...")
                        break
                except:
                    continue
        except Exception as e:
            print(f"Could not extract bio: {e}")

        # Extract follower/following counts
        try:
            stat_selectors = [
                "//div[contains(@class, '_ac2a')]//span[@title]",
                "//div[contains(@class, '_aacl')]//span",
                "//ul[contains(@class, '_a9-_')]//span[@title]"
            ]

            for selector in stat_selectors:
                try:
                    stat_elements = driver.find_elements(By.XPATH, selector)
                    for i, elem in enumerate(stat_elements):
                        text = elem.text.strip() or elem.get_attribute('title') or ''
                        if text and any(char.isdigit() for char in text):
                            if i == 0:  # Usually posts
                                profile_info['post_count'] = text
                            elif i == 1:  # Usually followers
                                profile_info['follower_count'] = text
                            elif i == 2:  # Usually following
                                profile_info['following_count'] = text
                    if profile_info['follower_count']:
                        break
                except:
                    continue

            print(
                f"✅ Stats - Posts: {profile_info['post_count']}, Followers: {profile_info['follower_count']}, Following: {profile_info['following_count']}")
        except Exception as e:
            print(f"Could not extract stats: {e}")

        # Extract full name
        try:
            name_selectors = [
                "//div[contains(@class, '_aacl')]//span[contains(@class, '_aacl')]",
                "//h2[contains(@class, '_aa_c')]",
                "//span[contains(@class, '_aacl') and contains(@class, '_aaco')]"
            ]

            for selector in name_selectors:
                try:
                    name_element = driver.find_element(By.XPATH, selector)
                    if name_element and name_element.text.strip():
                        profile_info['full_name'] = name_element.text.strip()
                        print(
                            f"✅ Found full name: {profile_info['full_name']}")
                        break
                except:
                    continue
        except Exception as e:
            print(f"Could not extract full name: {e}")

        # Check if verified
        try:
            verified_elements = driver.find_elements(
                By.XPATH, "//div[contains(@title, 'Verified')]")
            if verified_elements:
                profile_info['verified'] = True
                print("✅ Profile is verified")
        except:
            pass

    except Exception as e:
        print(f"Error extracting profile info: {e}")

    return profile_info


def analyze_profile(driver, username):
    """Analyze an Instagram profile and its posts"""
    print(f"\n🚀 STARTING ANALYSIS FOR: {username}")
    results_dir = f"results/{username}"
    os.makedirs(results_dir, exist_ok=True)

    try:
        # Navigate to profile
        profile_url = f"https://www.instagram.com/{username}/"
        print(f"📍 Step 1: Navigating to {profile_url}")
        driver.get(profile_url)

        # Add random delay to simulate human behavior (3-8 seconds)
        human_delay = random.randint(3, 8)
        print(f"⏱️ Step 2: Human-like delay: {human_delay} seconds")
        time.sleep(human_delay)

        # Extract comprehensive profile information first
        print(f"🔍 Step 3: Starting profile info extraction...")
        profile_info = extract_profile_info(driver, username)
        print(f"✅ Step 3 Complete: Profile info extracted - {profile_info}")

        # Check for rate limiting or restrictions
        print(f"🛡️ Step 4: Checking for rate limiting...")
        try:
            # Check for "Try again later" message
            rate_limit_messages = driver.find_elements(
                By.XPATH, "//*[contains(text(), 'Try again later') or contains(text(), 'temporarily blocked') or contains(text(), 'unusual activity')]")
            if rate_limit_messages:
                print(f"⚠️ RATE LIMITING DETECTED for {username}!")
                print(
                    "Instagram is asking to try again later. This indicates rate limiting.")
                # Take a screenshot for debugging
                driver.save_screenshot(
                    f"{results_dir}/rate_limit_detected.png")
                # Return None to indicate we should stop/slow down
                return None
        except Exception as e:
            print(f"Error checking rate limits: {e}")

        # Check if profile exists/is accessible
        print(f"🔍 Step 5: Checking if profile exists and is accessible...")
        try:
            error_messages = driver.find_elements(
                By.XPATH, "//h2[contains(text(), 'Sorry, this page')]")
            if error_messages:
                print(
                    f"❌ Profile {username} is not accessible: Page not found or private")
                # ADDED: Update status for not accessible profile
                update_bio_analysis_status_sqlite(
                    username, 'failed_not_accessible')
                return None
        except Exception as e:
            print(f"Error checking profile existence: {e}")

        # Check if profile is private
        print(f"🔒 Step 6: Checking if profile is private...")
        try:
            private_indicators = driver.find_elements(
                By.XPATH, "//h2[contains(text(), 'Private')]")
            if private_indicators:
                print(
                    f"🔒 Profile for {username} is private. Cannot analyze photos.")
                driver.save_screenshot(f"{results_dir}/private_profile.png")
                # ADDED: Update status for private profile
                update_bio_analysis_status_sqlite(
                    username, 'failed_private_profile')
                return None
            else:
                print(f"✅ Profile is public, proceeding with analysis...")
        except Exception as e:
            print(f"Error checking private status: {e}")
            print(f"Assuming profile is public and continuing...")

        # Find and analyze posts
        try:
            # Scroll down to load more posts for comprehensive analysis
            print("📜 Scrolling to load more posts...")
            # Scroll 3 times to load more posts
            for scroll_attempt in range(3):
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.randint(2, 4))
                print(f"Scroll attempt {scroll_attempt + 1}/3 completed")

            # Scroll back to top
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            # Try multiple selectors for posts
            posts = None
            selectors = [
                "//div[contains(@class, '_aagw')]",
                "//div[@role='button']/a[@role='link' and @tabindex='0']",
                "//article//a[contains(@href, '/p/')]",
                "//div[contains(@class, '_aabd')]//a"
            ]

            for selector in selectors:
                try:
                    posts = WebDriverWait(driver, 8).until(  # Reduced timeout
                        EC.presence_of_all_elements_located(
                            (By.XPATH, selector))
                    )
                    if posts:
                        print(
                            f"Found {len(posts)} posts using selector: {selector}")
                        break
                except:
                    continue

            if not posts:
                print(f"Could not find any posts for {username}")
                driver.save_screenshot(f"{results_dir}/no_posts_found.png")
                # ADDED: Update status for no posts
                update_bio_analysis_status_sqlite(username, 'failed_no_posts')
                return None

            print(f"🎯 Found {len(posts)} total posts for {username}")
            print(
                f"📊 Will analyze up to {min(20, len(posts))} posts for comprehensive analysis")

            if posts:
                # Analyze ALL posts for comprehensive profile analysis
                image_paths = []
                post_captions = []
                max_posts_to_analyze = min(
                    20, len(posts))  # Analyze up to 20 posts for comprehensive data

                print(
                    f"🔍 Comprehensive analysis: Processing {max_posts_to_analyze} posts...")

                for post_idx in range(max_posts_to_analyze):
                    try:
                        # Add random delay before each post
                        post_delay = random.randint(2, 5)
                        print(
                            f"📸 Processing post {post_idx + 1}/{max_posts_to_analyze} - Delay: {post_delay}s")
                        time.sleep(post_delay)

                        # Scroll post into view before clicking
                        driver.execute_script(
                            "arguments[0].scrollIntoView(true);", posts[post_idx])
                        time.sleep(1)
                        posts[post_idx].click()

                        # Longer wait for post to load
                        time.sleep(random.randint(4, 7))

                        # Extract caption from the post
                        try:
                            print(
                                f"Extracting caption for post {post_idx + 1}...")

                            # Multiple selectors for captions
                            caption_selectors = [
                                "//div[@data-testid='post-comment-root']//span[contains(@class, '_ap3a')]",
                                "//article//div[contains(@class, '_a9zr')]//span",
                                "//div[@role='button']//span[contains(@dir, 'auto')]",
                                "//article//span[contains(@dir, 'auto') and not(ancestor::time)]",
                                "//div[contains(@class, '_a9zr')]//span[not(ancestor::time)]"
                            ]

                            caption_text = ""
                            for selector in caption_selectors:
                                try:
                                    caption_elements = driver.find_elements(
                                        By.XPATH, selector)
                                    if caption_elements:
                                        # Get the first substantial caption text
                                        for elem in caption_elements:
                                            text = elem.text.strip()
                                            # Ignore very short text
                                            if text and len(text) > 10:
                                                caption_text = text
                                                break
                                        if caption_text:
                                            break
                                except:
                                    continue

                            if caption_text:
                                print(
                                    f"✅ Found caption: {caption_text[:100]}...")
                                post_captions.append(caption_text)
                            else:
                                print("❌ No caption found for this post")
                                post_captions.append("")

                        except Exception as caption_error:
                            print(f"Error extracting caption: {caption_error}")
                            post_captions.append("")

                        # Take screenshot
                        post_screenshot = f"{results_dir}/post_{post_idx + 1}.png"
                        driver.save_screenshot(post_screenshot)
                        image_paths.append(post_screenshot)

                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                        # Randomized escape delay
                        time.sleep(random.randint(2, 4))
                    except Exception as post_error:
                        print(
                            f"Error processing post {post_idx + 1}: {post_error}")
                        try:
                            ActionChains(driver).send_keys(
                                Keys.ESCAPE).perform()
                            time.sleep(2)
                        except:
                            pass

                # Analyze collected posts with captions
                if image_paths:
                    analysis_result = analyze_multiple_images_with_gemini(
                        image_paths, username, post_captions, profile_info)
                    if analysis_result:
                        print("Analysis of multiple posts complete.")

                        # Add coaching potential analysis
                        try:
                            from identify_potential_clients_sqlite import analyze_for_coaching_potential, add_follower_to_database
                            print(
                                f"Running coaching analysis for {username}...")

                            # Run coaching analysis on the profile data
                            coaching_analysis = analyze_for_coaching_potential(
                                analysis_result)
                            if coaching_analysis:
                                print(
                                    f"Coaching analysis complete for {username}")
                                analysis_result['coaching_analysis'] = coaching_analysis

                                # Save to database for prospects tab
                                add_follower_to_database(
                                    username, analysis_result)
                                print(
                                    f"Added {username} to prospects database")
                            else:
                                print(
                                    f"Coaching analysis failed for {username}")
                        except Exception as coaching_error:
                            print(
                                f"Error in coaching analysis for {username}: {coaching_error}")

                        # ADDED: Update status for successful analysis
                        update_bio_analysis_status_sqlite(
                            username, 'completed')
                        return analysis_result
                    else:
                        print(f"Analysis failed for {username}")
                        # ADDED: Update status for AI analysis failure
                        update_bio_analysis_status_sqlite(
                            username, 'failed_ai_analysis')
                        return None
                else:
                    print(
                        f"No posts were successfully captured for {username}")
                    # ADDED: Update status for no posts captured after trying
                    update_bio_analysis_status_sqlite(
                        username, 'failed_no_posts_captured')
                    return None

        except Exception as post_finder_error:
            print(f"Error finding posts: {post_finder_error}")
            driver.save_screenshot(f"{results_dir}/post_processing_error.png")
            # ADDED: Update status for general post processing error
            update_bio_analysis_status_sqlite(
                username, 'failed_post_processing_error')
            return None

    except Exception as e:
        print(f"Error analyzing profile for {username}: {e}")
        driver.save_screenshot(f"{results_dir}/profile_analysis_error.png")
        # ADDED: Update status for general profile analysis error
        update_bio_analysis_status_sqlite(username, 'failed_general_error')
        return None


def initialize_conversation_metrics():
    """Initialize metrics structure for a new conversation"""
    return {
        "messages": [],
        "metrics": {
            "total_messages": 0,
            "user_messages": 0,
            "ai_messages": 0,
            "question_response_rate": 0,
            "conversation_history": []
        },
        "client_analysis": None
    }


def update_analytics_sqlite(username, client_analysis):
    """Update analytics data for a user in SQLite database"""
    try:
        print("\n=== Starting SQLite Analytics Update ===")
        print(f"Attempting to update analytics for {username}")

        # Prepare metrics data for SQLite
        metrics_data = {
            'ig_username': username,
            'client_analysis': client_analysis,
            'timestamp': client_analysis.get('timestamp', datetime.datetime.now().isoformat()),
            'posts_analyzed': client_analysis.get('posts_analyzed', 0),
            'interests': client_analysis.get('interests', []),
            'lifestyle_indicators': client_analysis.get('lifestyle_indicators', []),
            'recent_activities': client_analysis.get('recent_activities', []),
            'post_summaries': client_analysis.get('post_summaries', []),
            'conversation_topics': client_analysis.get('conversation_topics', []),
            'profile_bio': client_analysis.get('profile_bio', {}),
            'analysis_source': 'instagram_follower_analyzer'  # Track the source
        }

        # Save to SQLite
        success = save_metrics_to_sqlite(username, metrics_data)

        if success:
            print("✅ Successfully updated SQLite database")

            # Also add a message to history to track this analysis
            add_message_to_history(
                ig_username=username,
                message_type="instagram_analysis",
                message_text=f"Instagram profile analyzed - {client_analysis.get('posts_analyzed', 0)} posts analyzed",
                message_timestamp=client_analysis.get('timestamp')
            )
            print("✅ Added analysis record to message history")
            return True
        else:
            print("❌ Failed to update SQLite database")
            return False

    except Exception as e:
        print(f"❌ Error in update_analytics_sqlite: {e}")
        print("Full error details:")
        traceback.print_exc()
        return False


def update_bio_analysis_status_sqlite(username: str, status: str, conn=None):
    """
    Updates the bio_analysis_status for a user in the SQLite database.
    Statuses can include 'completed', 'failed_no_posts', 'failed_private_profile', etc.
    """
    should_close_conn = False
    if conn is None:
        conn = get_db_connection()
        should_close_conn = True
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET bio_analysis_status = ?, last_updated = CURRENT_TIMESTAMP
            WHERE ig_username = ?
        """, (status, username))
        conn.commit()
        print(f"✅ Updated bio_analysis_status for {username} to '{status}'")
        return True
    except Exception as e:
        print(f"❌ Error updating bio_analysis_status for {username}: {e}")
        traceback.print_exc()
        return False
    finally:
        if should_close_conn and conn:
            conn.close()


def update_analytics(username, client_analysis):
    """Legacy function - now calls SQLite version and optionally updates JSON as backup"""
    # Primary storage: SQLite
    sqlite_success = update_analytics_sqlite(username, client_analysis)

    # Backup: Also update JSON file (existing functionality)
    json_success = update_analytics_json(username, client_analysis)

    return sqlite_success  # Primary success indicator is SQLite


def update_analytics_json(username, client_analysis):
    """Original JSON update function (now used as backup)"""
    try:
        print("\n=== Starting JSON Analytics Update (Backup) ===")
        print(f"Attempting to update JSON analytics for {username}")

        # Read existing analytics data
        analytics_file_path = ANALYTICS_FILE
        print(f"Reading from: {analytics_file_path}")

        with open(analytics_file_path, 'r', encoding='utf-8') as f:
            analytics_data = json.load(f)
            print("Successfully loaded analytics file")

        # Create path to user's data if it doesn't exist
        if 'conversations' not in analytics_data:
            analytics_data['conversations'] = {}

        if username not in analytics_data['conversations']:
            analytics_data['conversations'][username] = {}

        if 'metrics' not in analytics_data['conversations'][username]:
            analytics_data['conversations'][username]['metrics'] = {}

        metrics = analytics_data['conversations'][username]['metrics']

        if 'client_analysis' not in metrics:
            metrics['client_analysis'] = {}

        target = metrics['client_analysis']

        # Store original state for verification
        original_state = json.dumps(target, sort_keys=True)

        print("\nUpdating JSON fields...")

        # Update core fields
        updates = {
            'posts_analyzed': client_analysis['posts_analyzed'],
            'timestamp': client_analysis['timestamp'],
            'interests': [i.strip('*') for i in client_analysis.get('interests', []) if i and not i.startswith('**')],
            'lifestyle_indicators': [i.strip('*') for i in client_analysis.get('lifestyle_indicators', []) if i and not i.startswith('**')],
            'recent_activities': [a.strip('*') for a in client_analysis.get('recent_activities', []) if a and not a.startswith('**')],
            'post_summaries': [s for s in client_analysis.get('post_summaries', []) if s and not s.startswith('**')],
            'conversation_topics': [t.strip('*') for t in client_analysis.get('conversation_topics', []) if t and not t.startswith('**') and t != "**"]
        }

        # Apply updates and log changes
        for key, value in updates.items():
            if value:  # Only update if we have valid data
                old_value = target.get(key, None)
                target[key] = value
                print(
                    f"Updated {key}: {len(value) if isinstance(value, list) else value}")
                if old_value != value:
                    print(f"Changed from: {old_value}")
                    print(f"Changed to: {value}")

        # Update profile bio
        if 'profile_bio' in client_analysis and isinstance(client_analysis['profile_bio'], dict):
            print("\nUpdating profile bio...")
            target['profile_bio'] = client_analysis['profile_bio']
            print(
                f"Profile bio updated: {json.dumps(client_analysis['profile_bio'], indent=2)}")

        # Verify changes were made
        new_state = json.dumps(target, sort_keys=True)
        if original_state == new_state:
            print("\n⚠️ Warning: No changes detected in the JSON data!")
        else:
            print("\n✅ Changes detected in the JSON data")

        # Write updates to file
        print("\nSaving updates to JSON file...")
        try:
            with open(analytics_file_path, 'w', encoding='utf-8') as f:
                json.dump(analytics_data, f, indent=2, ensure_ascii=False)

            # Verify file was written correctly
            with open(analytics_file_path, 'r', encoding='utf-8') as f:
                verification_data = json.load(f)
                if username in verification_data.get('conversations', {}):
                    print("✅ JSON file write verified successfully")
                else:
                    print("⚠️ Warning: JSON file write verification failed!")
                    return False

            return True
        except Exception as write_error:
            print(f"❌ Error writing to JSON file: {write_error}")
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ Error in update_analytics_json: {e}")
        print("Full error details:")
        traceback.print_exc()
        return False


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
                print(f"Trying model: {model_name}")
                response = model.generate_content(contents)
                print(f"Successfully used {model_name}")
                return response
            except google.api_core.exceptions.ResourceExhausted as e:
                print(f"Rate limit hit for {model_name}, trying next model...")
                last_error = e
                continue
            except Exception as e:
                print(f"Error with {model_name}: {e}")
                last_error = e
                continue

        # If we get here, all models failed
        if last_error:
            print("All models failed. Last error:", str(last_error))
            raise last_error
        return None

    except Exception as e:
        print(f"Error in Gemini analysis: {e}")
        return None


def analyze_multiple_images_with_gemini(image_paths, username, post_captions=None, profile_info=None):
    """Analyze multiple Instagram posts using Gemini Vision API with captions and profile info"""
    print(f"\n=== Starting Comprehensive Analysis for {username} ===")
    print(
        f"Analyzing {len(image_paths)} posts with captions and profile data...")

    try:
        client_analysis = {
            "posts_analyzed": len(image_paths),
            "timestamp": datetime.datetime.now().isoformat(),
            "interests": [],
            "lifestyle_indicators": [],
            "recent_activities": [],
            "post_summaries": [],
            "conversation_topics": [],
            "personality_insights": [],
            "profile_info": profile_info or {},
            "post_captions": post_captions or []
        }

        # Analyze individual posts
        for i, image_path in enumerate(image_paths):
            print(f"\nAnalyzing post {i+1}/{len(image_paths)}...")
            try:
                with open(image_path, 'rb') as f:
                    image_data = f.read()

                # Get the caption for this post if available
                post_caption = post_captions[i] if post_captions and i < len(
                    post_captions) else ""

                prompt = f"""
                Analyze this Instagram post by {username}.
                
                POST CAPTION: "{post_caption}"
                
                Analyze both the IMAGE and the CAPTION to provide comprehensive insights.
                Provide a detailed description and identify potential interests, activities, and conversation topics.
                
                RESPOND IN THIS FORMAT:
                DESCRIPTION: [Brief description combining image content and caption context]
                INTERESTS: [List specific interests or hobbies shown in image AND mentioned in caption]
                ACTIVITIES: [List specific activities being performed or referenced]
                TOPICS: [List 2-3 specific conversation starters based on both visual content and caption]
                PERSONALITY_INSIGHTS: [Brief insights about personality or lifestyle from caption tone/content]
                """

                print(f"Sending post {i+1} to Gemini for analysis...")
                response = analyze_with_gemini(prompt, image_data)

                if response:
                    # Parse the response
                    response_text = response.text
                    print(f"Received response for post {i+1}, parsing...")

                    description = re.search(
                        r'DESCRIPTION:\s*(.*?)(?=\n|$)', response_text, re.DOTALL)
                    interests = re.search(
                        r'INTERESTS:\s*(.*?)(?=\n|$)', response_text, re.DOTALL)
                    activities = re.search(
                        r'ACTIVITIES:\s*(.*?)(?=\n|$)', response_text, re.DOTALL)
                    topics = re.search(
                        r'TOPICS:\s*(.*?)(?=\n|$)', response_text, re.DOTALL)
                    personality = re.search(
                        r'PERSONALITY_INSIGHTS:\s*(.*?)(?=\n|$)', response_text, re.DOTALL)

                    # Add to client analysis
                    if description:
                        desc_text = description.group(1).strip()
                        print(f"Found description: {desc_text[:50]}...")
                        client_analysis["post_summaries"].append(desc_text)
                    if interests:
                        interest_list = [i.strip()
                                         for i in interests.group(1).split(',')]
                        print(f"Found interests: {interest_list}")
                        client_analysis["interests"].extend(interest_list)
                    if activities:
                        activity_list = [a.strip()
                                         for a in activities.group(1).split(',')]
                        print(f"Found activities: {activity_list}")
                        client_analysis["recent_activities"].extend(
                            activity_list)
                    if topics:
                        topic_list = [t.strip()
                                      for t in topics.group(1).split(',')]
                        print(f"Found topics: {topic_list}")
                        client_analysis["conversation_topics"].extend(
                            topic_list)
                    if personality:
                        personality_text = personality.group(1).strip()
                        print(
                            f"Found personality insights: {personality_text[:50]}...")
                        client_analysis["personality_insights"].append(
                            personality_text)

            except Exception as e:
                print(f"❌ Error analyzing image {i+1}: {str(e)}")

        # Generate final conversation topics
        print("\nGenerating enhanced conversation topics with comprehensive data...")
        all_data = {
            'interests': list(set(client_analysis['interests'])),
            'activities': list(set(client_analysis['recent_activities'])),
            'topics': list(set(client_analysis['conversation_topics'])),
            'personality': list(set(client_analysis['personality_insights'])),
            'profile_bio': profile_info.get('bio', '') if profile_info else '',
            'follower_count': profile_info.get('follower_count', '') if profile_info else '',
            'post_count': profile_info.get('post_count', '') if profile_info else ''
        }

        conversation_prompt = f"""
        Based on this COMPREHENSIVE Instagram profile analysis for {username}:

        PROFILE BIO: {all_data['profile_bio']}
        FOLLOWER COUNT: {all_data['follower_count']}
        POST COUNT: {all_data['post_count']}
        
        INTERESTS: {', '.join(all_data['interests'])}
        ACTIVITIES: {', '.join(all_data['activities'])}
        PERSONALITY INSIGHTS: {', '.join(all_data['personality'])}
        EXISTING TOPICS: {', '.join(all_data['topics'])}
        
        POST CAPTIONS ANALYZED: {len(post_captions or [])} captions from recent posts
        VISUAL CONTENT ANALYZED: {len(image_paths)} posts with images

        Generate EXACTLY 4 highly personalized conversation topics/starters that would deeply resonate with this person.
        Use ALL the data above - bio, personality insights, captions, visual content, and activities.
        Each topic should feel like you personally know them from their content.
        
        Format each topic EXACTLY like this example:
        Topic 1 - Discuss their morning workout routine and favorite exercises
        Topic 2 - Explore their experience with plant-based nutrition
        Topic 3 - Talk about their fitness transformation journey
        Topic 4 - Share tips about balancing work and fitness goals

        Make each topic HIGHLY SPECIFIC and personal to their actual content and personality.
        Each topic should start with 'Topic X - ' followed by the actual conversation starter.
        """

        topics_response = analyze_with_gemini(conversation_prompt)

        if topics_response:
            # Parse the topics with their labels and content
            topics = re.findall(
                r'Topic (\d) - (.+?)(?=\n|$)', topics_response.text)
            if topics and len(topics) == 4:
                # Store topics as a list of complete strings
                formatted_topics = [
                    f"Topic {num} - {content.strip()}" for num, content in topics]
                client_analysis["conversation_topics"] = formatted_topics
                print("\nFinal conversation topics:")
                for topic in formatted_topics:
                    print(topic)
            else:
                print("❌ Error: Could not generate exactly 4 conversation topics")
                # Provide fallback topics if needed
                client_analysis["conversation_topics"] = [
                    "Topic 1 - Discuss their fitness journey and current goals",
                    "Topic 2 - Explore their favorite workout routines and exercises",
                    "Topic 3 - Talk about their nutrition preferences and meal planning",
                    "Topic 4 - Share experiences about balancing fitness with daily life"
                ]

        # Generate profile bio
        print("\nGenerating profile bio...")
        profile_bio = generate_profile_bio(
            username, client_analysis, image_paths)
        if profile_bio:
            print("Profile bio generated successfully")
            client_analysis["profile_bio"] = profile_bio
            print("Profile bio content:", json.dumps(profile_bio, indent=2))

        # Update analytics
        print("\nUpdating analytics...")
        if update_analytics(username, client_analysis):
            print("✅ Successfully completed analysis and update")

            # Run coaching potential analysis
            print("\nRunning coaching potential analysis...")
            try:
                from identify_potential_clients import analyze_for_coaching_potential

                # Load the updated user data for coaching analysis
                with open(ANALYTICS_FILE, 'r', encoding='utf-8') as f:
                    analytics_data = json.load(f)

                user_data = analytics_data.get(
                    'conversations', {}).get(username, {})
                if user_data:
                    coaching_analysis = analyze_for_coaching_potential(
                        user_data)

                    if coaching_analysis:
                        # Add coaching analysis back to the data
                        metrics = user_data.get('metrics', {})
                        if 'client_analysis' not in metrics:
                            metrics['client_analysis'] = {}

                        metrics['client_analysis']['coaching_potential'] = coaching_analysis

                        # Save updated data
                        with open(ANALYTICS_FILE, 'w', encoding='utf-8') as f:
                            json.dump(analytics_data, f, indent=2,
                                      ensure_ascii=False)

                        print(
                            f"✅ Coaching analysis complete - Score: {coaching_analysis.get('score', 0)}/100")
                    else:
                        print("❌ Coaching analysis failed")
                else:
                    print("❌ Could not find user data for coaching analysis")

            except ImportError:
                print("⚠️ Coaching analysis module not available")
            except Exception as e:
                print(f"❌ Error in coaching analysis: {e}")
        else:
            print("❌ Failed to update analytics")

        return client_analysis

    except Exception as e:
        print(f"❌ Error in analyze_multiple_images_with_gemini: {e}")
        traceback.print_exc()
        return None


def generate_profile_bio(username, client_analysis, image_paths):
    """Generate a comprehensive profile bio using analyzed data"""
    try:
        descriptions = client_analysis.get("post_summaries", [])
        interests = list(set([i.strip(
            '*') for i in client_analysis.get("interests", []) if i and not i.startswith('**')]))
        activities = list(set([a.strip('*') for a in client_analysis.get(
            "recent_activities", []) if a and not a.startswith('**')]))
        topics = list(set([t.strip('*') for t in client_analysis.get(
            "conversation_topics", []) if t and not t.startswith('**')]))

        prompt = f"""
        Based on the following information from Instagram user '{username}', create a comprehensive profile bio:

        POST DESCRIPTIONS: {' | '.join(descriptions)}
        INTERESTS: {', '.join(interests)}
        ACTIVITIES: {', '.join(activities)}
        TOPICS: {', '.join(topics)}

        Create a structured profile with these exact fields:
        1. PERSON NAME (extract from username if no other info available)
        2. INTERESTS (list the top 3-5 most relevant interests)
        3. LIFESTYLE (write a brief 1-2 sentence description)
        4. PERSONALITY TRAITS (list 3-4 key traits)

        Respond in this exact JSON format:
        {{
            "PERSON NAME": "name",
            "INTERESTS": ["interest1", "interest2", "interest3"],
            "LIFESTYLE": "description",
            "PERSONALITY TRAITS": ["trait1", "trait2", "trait3"]
        }}
        """

        response = analyze_with_gemini(prompt)

        try:
            if response:
                # Clean up response text to ensure valid JSON
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

                # Parse JSON response
                profile_data = json.loads(response_text)

                # Ensure all required fields exist
                required_fields = ["PERSON NAME", "INTERESTS",
                                   "LIFESTYLE", "PERSONALITY TRAITS"]
                for field in required_fields:
                    if field not in profile_data:
                        profile_data[field] = "Unknown" if field == "PERSON NAME" else [
                        ] if field != "LIFESTYLE" else "Unknown lifestyle"

                return profile_data
            else:
                raise Exception("No response from Gemini")

        except json.JSONDecodeError:
            # Fallback to structured text parsing if JSON fails
            return {
                "PERSON NAME": username,
                "INTERESTS": interests[:5],
                "LIFESTYLE": "Fitness enthusiast and personal trainer",
                "PERSONALITY TRAITS": ["Professional", "Motivating", "Knowledgeable"]
            }

    except Exception as e:
        print(f"Error generating profile bio: {e}")
        return {
            "PERSON NAME": username,
            "INTERESTS": [],
            "LIFESTYLE": "Unknown",
            "PERSONALITY TRAITS": []
        }


def get_recently_analyzed_profiles(analytics_file=ANALYTICS_FILE, days_threshold=0):
    """Get list of recently analyzed profiles"""
    try:
        with open(analytics_file, 'r', encoding='utf-8') as f:
            analytics_data = json.load(f)

        recent_profiles = []
        current_time = datetime.datetime.now()

        for username, data in analytics_data.get('conversations', {}).items():
            if 'metrics' in data and 'client_analysis' in data['metrics']:
                timestamp_str = data['metrics']['client_analysis'].get(
                    'timestamp')
                if timestamp_str:
                    try:
                        analyzed_time = datetime.datetime.fromisoformat(
                            timestamp_str)
                        days_diff = (current_time - analyzed_time).days
                        if days_diff < days_threshold:
                            recent_profiles.append(username)
                    except:
                        continue

        return recent_profiles
    except Exception as e:
        print(f"Error getting recently analyzed profiles: {e}")
        return []


def has_complete_instagram_analysis_sqlite(ig_username):
    """Check if a user has complete Instagram analysis data in SQLite"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists and has metrics
        cursor.execute(
            "SELECT metrics_json FROM users WHERE ig_username = ?",
            (ig_username,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result or not result[0]:
            return False

        # Parse the metrics JSON
        try:
            metrics_data = json.loads(result[0])
        except (json.JSONDecodeError, TypeError):
            return False

        # Check for Instagram analysis indicators
        client_analysis = metrics_data.get('client_analysis', {})
        if not client_analysis:
            return False

        # STRICTER CHECK: Verify it has ALL the key fields that indicate a complete Instagram analysis
        required_fields = ['posts_analyzed', 'timestamp',
                           'interests', 'conversation_topics']

        # Check that ALL required fields exist AND have meaningful data
        for field in required_fields:
            if field not in client_analysis:
                return False

            # Additional checks for meaningful data
            if field == 'posts_analyzed':
                if not isinstance(client_analysis[field], int) or client_analysis[field] <= 0:
                    return False
            elif field == 'timestamp':
                if not client_analysis[field] or client_analysis[field] == "":
                    return False
            elif field in ['interests', 'conversation_topics']:
                if not isinstance(client_analysis[field], list) or len(client_analysis[field]) == 0:
                    return False

        # Also verify the analysis source is from Instagram analyzer
        analysis_source = metrics_data.get('analysis_source')
        if analysis_source != 'instagram_follower_analyzer':
            return False

        # Additional check: ensure we have meaningful conversation topics (not just generic ones)
        topics = client_analysis.get('conversation_topics', [])
        if not topics or len(topics) < 2:
            return False

        # Check that topics aren't just generic fallbacks
        generic_topics = [
            "Topic 1 - Discuss their fitness journey and current goals",
            "Topic 2 - Explore their favorite workout routines and exercises",
            "Topic 3 - Talk about their nutrition preferences and meal planning",
            "Topic 4 - Share experiences about balancing fitness with daily life"
        ]

        # If all topics are generic fallbacks, consider analysis incomplete
        if all(topic in generic_topics for topic in topics):
            return False

        return True

    except Exception as e:
        print(f"Error checking Instagram analysis for {ig_username}: {e}")
        return False


def get_analyzed_usernames_from_sqlite():
    """Get set of usernames that have been analyzed from SQLite"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all users with Instagram analysis
        cursor.execute("""
            SELECT ig_username, metrics_json 
            FROM users 
            WHERE metrics_json IS NOT NULL
        """)

        analyzed_usernames = set()
        for row in cursor.fetchall():
            ig_username = row[0]

            if has_complete_instagram_analysis_sqlite(ig_username):
                analyzed_usernames.add(ig_username)

        conn.close()
        print(
            f"Found {len(analyzed_usernames)} usernames with complete Instagram analysis in SQLite")
        return analyzed_usernames

    except Exception as e:
        print(f"Error getting analyzed usernames from SQLite: {e}")
        return set()


def has_complete_instagram_analysis(user_data):
    """Legacy function - check if a user has complete Instagram analysis data from JSON"""
    if not isinstance(user_data, dict):
        return False

    metrics = user_data.get('metrics', {})
    if not isinstance(metrics, dict):
        return False

    # Check for client_analysis which is added by the Instagram analyzer
    client_analysis = metrics.get('client_analysis')
    if not client_analysis:
        return False

    # Verify it has the key fields that indicate a complete analysis
    required_fields = ['posts_analyzed', 'timestamp',
                       'interests', 'conversation_topics']
    if not isinstance(client_analysis, dict):
        return False

    return any(field in client_analysis for field in required_fields)


def process_usernames():
    """Process Instagram usernames from the followers list"""
    print("Starting Instagram profile analysis...")

    # Initialize SQLite database tables
    try:
        conn = get_db_connection()
        create_user_table_if_not_exists(conn)
        conn.close()
        print("✅ SQLite database tables initialized")
    except Exception as e:
        print(f"❌ Error initializing SQLite database: {e}")
        return

    # Create cookies directory if it doesn't exist
    cookies_dir = os.path.join(SCRIPT_DIR, "cookies")
    os.makedirs(cookies_dir, exist_ok=True)

    # Load usernames from file
    initial_usernames_from_file = load_usernames(FOLLOWERS_LIST)
    if not initial_usernames_from_file:
        print(
            f"No usernames found in {FOLLOWERS_LIST} or file does not exist. Exiting.")
        return
    print(
        f"Loaded {len(initial_usernames_from_file)} usernames from {FOLLOWERS_LIST}")

    # --- Get already processed usernames from SQLite ---
    processed_ig_usernames_sqlite = get_analyzed_usernames_from_sqlite()
    print(
        f"Found {len(processed_ig_usernames_sqlite)} usernames with complete Instagram analysis in SQLite")

    # Set all_processed_usernames to only those found in SQLite
    all_processed_usernames = processed_ig_usernames_sqlite
    print(
        f"Total unique processed usernames (SQLite only): {len(all_processed_usernames)}")

    # Filter usernames to process
    usernames_to_consider_processing = []
    for name_from_file in initial_usernames_from_file:
        name_from_file = name_from_file.strip()
        if not name_from_file:
            continue

        if name_from_file.isdigit():
            # Skip numeric IDs for now - this script focuses on actual IG usernames
            print(
                f"Skipping numeric ID {name_from_file} - Instagram analyzer requires actual usernames")
            continue
        else:
            # Check if username is already processed (unless --force is used)
            if args.force:
                print(
                    f"Force mode: Re-analyzing {name_from_file} even if already processed")
                usernames_to_consider_processing.append(name_from_file)
            elif name_from_file not in all_processed_usernames:
                usernames_to_consider_processing.append(name_from_file)
            else:
                print(
                    f"Skipping {name_from_file} - already has complete Instagram analysis (use --force to override)")

    # Final list of usernames to process, ensuring uniqueness and sorted alphabetically
    usernames_to_process = sorted(list(set(usernames_to_consider_processing)))

    print(
        f"After filtering, {len(usernames_to_process)} unique usernames are ready for processing")
    if usernames_to_process:
        print(f"First username to process: {usernames_to_process[0]}")
        print(f"Last username to process: {usernames_to_process[-1]}")

    if not usernames_to_process:
        print("No new usernames to analyze after filtering. Exiting.")
        return

    # --- DRY RUN MODE ---
    if args.dry_run:
        print("\n" + "="*60)
        print("DRY RUN MODE - No actual processing will be performed")
        print("="*60)
        print(
            f"\nUsernames that would be processed ({len(usernames_to_process)} total):")

        # Show first 20 usernames
        for i, username in enumerate(usernames_to_process[:20]):
            print(f"{i+1:3d}. {username}")

        if len(usernames_to_process) > 20:
            print(f"... and {len(usernames_to_process) - 20} more usernames")

        # Show alphabetical range
        print(
            f"\nAlphabetical range: {usernames_to_process[0]} to {usernames_to_process[-1]}")

        # Show progress info if available
        if os.path.exists("analysis_progress.json"):
            try:
                with open("analysis_progress.json", 'r') as f:
                    progress_data = json.load(f)
                    last_batch = progress_data.get('last_completed_batch', 0)
                    processed_count = len(
                        progress_data.get('processed_usernames', []))
                    print(f"\nProgress file shows:")
                    print(f"- Last completed batch: {last_batch}")
                    print(f"- Processed in this session: {processed_count}")
            except:
                print("\nProgress file exists but could not be read")

        print(f"\nEstimated batches: {(len(usernames_to_process) + 49) // 50}")
        print("="*60)
        return

    # Check for progress file
    progress_file = "analysis_progress.json"
    start_batch = 0
    processed_usernames = set()

    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
                start_batch = progress_data.get('last_completed_batch', 0)
                processed_usernames = set(
                    progress_data.get('processed_usernames', []))
                batch_size = progress_data.get('batch_size', 50)
                start_profile = start_batch * batch_size
                print(
                    f"\nResuming from batch {start_batch + 1} (profiles {start_profile + 1}-{min(start_profile + batch_size, len(usernames_to_process))})")
                print(
                    f"Already processed {len(processed_usernames)} usernames in this session")

                # Verify batch size matches
                if batch_size != 50:
                    print(
                        "Warning: Batch size in progress file differs from script's batch size")
        except Exception as e:
            print(
                f"Could not read progress file, starting from beginning: {e}")
            start_batch = 0
            processed_usernames = set()

    # Filter out already processed usernames
    usernames_to_process = [
        u for u in usernames_to_process if u not in processed_usernames]

    if start_batch > 0:
        print(
            f"Skipping first {start_batch} batches ({start_batch * 50} profiles)")
        usernames_to_process = usernames_to_process[start_batch * 50:]

    print(f"\nWill process {len(usernames_to_process)} remaining usernames")

    # Initialize WebDriver
    chromedriver_path = find_chromedriver()
    if not chromedriver_path:
        print("No valid ChromeDriver found. Exiting.")
        return

    try:
        # Process usernames in batches - REDUCED BATCH SIZE FOR SAFETY
        batch_size = 10  # Reduced from 50 to 10 for safety
        for i in range(start_batch * batch_size, len(usernames_to_process), batch_size):
            current_batch = i // batch_size + 1
            total_batches = (len(usernames_to_process) +
                             batch_size - 1) // batch_size
            batch = usernames_to_process[i:i + batch_size]
            print(f"\nProcessing batch {current_batch} of {total_batches}")

            try:
                # Create new browser session for each batch
                service = webdriver.chrome.service.Service(
                    executable_path=chromedriver_path)
                driver = webdriver.Chrome(
                    service=service, options=chrome_options)
                wait = WebDriverWait(driver, 30)

                # Login to Instagram
                login_success = login_to_instagram(driver, USERNAME, PASSWORD)
                print(f"Login attempt result: {login_success}")

                if not login_success:
                    print("Failed to login to Instagram")
                    # For single-user analysis or debug mode, keep browser open for debugging
                    if len(usernames_to_process) <= 1 or (args and args.debug):
                        print("Login failed - keeping browser open for debugging.")
                        print("Please log in manually in the browser window.")
                        print(
                            "Script will continue automatically once you're logged in...")

                        # Instead of waiting for input, check login status periodically
                        max_wait_time = 300  # 5 minutes
                        check_interval = 10  # Check every 10 seconds
                        checks_made = 0
                        max_checks = max_wait_time // check_interval

                        while checks_made < max_checks:
                            time.sleep(check_interval)
                            if check_login_status(driver):
                                print(
                                    "✅ Login detected! Continuing with analysis...")
                                login_success = True
                                break
                            checks_made += 1
                            print(
                                f"Waiting for manual login... ({checks_made}/{max_checks})")

                        if not login_success:
                            print("❌ Timed out waiting for manual login")
                            return
                    else:
                        driver.quit()
                        # Save progress before exiting
                        with open(progress_file, 'w') as f:
                            json.dump({
                                'last_completed_batch': current_batch - 1,
                                'processed_usernames': list(processed_usernames),
                                'batch_size': batch_size
                            }, f)
                        print(f"Saved progress to {progress_file}")
                        return

                # Process each username in the batch with randomized delays
                for idx, username in enumerate(batch):
                    try:
                        print(
                            f"\n🎯 PROCESSING USER {idx + 1}/{len(batch)} in batch {current_batch}: {username}")
                        print(f"📞 About to call analyze_profile function...")

                        # Analyze profile
                        analysis_result = analyze_profile(driver, username)
                        print(
                            f"📞 analyze_profile returned: {analysis_result is not None}")

                        if analysis_result:
                            print(
                                f"Successfully analyzed profile for {username}")
                            processed_usernames.add(username)

                            # Update Google Sheets if available
                            if sheets_manager:
                                try:
                                    sheet_data = {
                                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "username": username,
                                        "analysis_result": analysis_result
                                    }
                                    sheets_manager.add_row(sheet_data)
                                    print(
                                        f"Updated Google Sheets for {username}")
                                except Exception as sheet_error:
                                    print(
                                        f"Error updating Google Sheets: {sheet_error}")
                        else:
                            print(f"Could not analyze profile for {username}")

                        # RANDOMIZED DELAY BETWEEN PROFILES (30-120 seconds)
                        if idx < len(batch) - 1:  # Don't wait after the last profile in batch
                            profile_delay = random.randint(30, 120)
                            print(
                                f"Waiting {profile_delay} seconds before next profile...")
                            time.sleep(profile_delay)

                    except Exception as e:
                        print(f"Error processing {username}: {e}")
                        # Even on error, add a short delay
                        error_delay = random.randint(15, 45)
                        print(f"Error delay: {error_delay} seconds")
                        time.sleep(error_delay)
                        continue

                # Save progress after each batch
                with open(progress_file, 'w') as f:
                    json.dump({
                        'last_completed_batch': current_batch,
                        'processed_usernames': list(processed_usernames),
                        'batch_size': batch_size
                    }, f)
                print(f"Saved progress after batch {current_batch}")

            except Exception as batch_error:
                print(f"Error processing batch: {batch_error}")
                continue
            finally:
                try:
                    # Only quit the driver if we're done with all batches
                    # For single-user analysis or debug mode, keep the browser open for debugging
                    if len(usernames_to_process) <= 1 or (args and args.debug):
                        print(
                            "Single user analysis or debug mode - keeping browser open for debugging")
                        print(f"Browser will stay open. Close manually when done.")
                    else:
                        driver.quit()
                except:
                    pass

            # LONGER RANDOMIZED WAIT BETWEEN BATCHES (5-15 minutes)
            if i + batch_size < len(usernames_to_process):
                batch_delay = random.randint(300, 900)  # 5-15 minutes
                minutes = batch_delay // 60
                seconds = batch_delay % 60
                print(
                    f"\n🕒 BATCH BREAK: Waiting {minutes}m {seconds}s before next batch to avoid rate limiting...")
                print(
                    f"Next batch will start at approximately: {(datetime.datetime.now() + datetime.timedelta(seconds=batch_delay)).strftime('%H:%M:%S')}")
                time.sleep(batch_delay)

    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        print("\nProfile analysis completed!")
        # Save final progress
        with open(progress_file, 'w') as f:
            json.dump({
                'last_completed_batch': (len(usernames_to_process) + batch_size - 1) // batch_size,
                'processed_usernames': list(processed_usernames),
                'batch_size': batch_size
            }, f)
        print(f"Saved final progress to {progress_file}")


def load_usernames(file_path):
    """Load usernames from a file"""
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return []

        with open(file_path, 'r') as f:
            usernames = [line.strip() for line in f if line.strip()
                         and not line.strip().startswith('#')]
        return usernames
    except Exception as e:
        print(f"Error loading usernames: {e}")
        return []


def analyze_single_user_direct(username_to_analyze):
    """
    Direct analysis of a single user - bypasses all filtering logic
    Use this for debugging when normal process_usernames() isn't working
    """
    print(f"\n🎯 DIRECT SINGLE USER ANALYSIS: {username_to_analyze}")
    print("="*60)

    # Initialize SQLite database tables
    try:
        conn = get_db_connection()
        create_user_table_if_not_exists(conn)
        conn.close()
        print("✅ SQLite database tables initialized")
    except Exception as e:
        print(f"❌ Error initializing SQLite database: {e}")
        return False

    # Find ChromeDriver
    chromedriver_path = find_chromedriver()
    if not chromedriver_path:
        print("❌ No valid ChromeDriver found. Exiting.")
        return False

    print(f"✅ Using ChromeDriver: {chromedriver_path}")

    try:
        # Create browser session
        print("🌐 Starting browser session...")
        service = webdriver.chrome.service.Service(
            executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        print("🔐 Attempting Instagram login...")
        login_success = login_to_instagram(driver, USERNAME, PASSWORD)

        if not login_success:
            print("❌ Login failed. Please check credentials.")
            print("🔧 Browser will stay open for manual login debugging...")
            return False

        print("✅ Login successful!")

        # Direct profile analysis
        print(f"🔍 Starting analysis for: {username_to_analyze}")
        analysis_result = analyze_profile(driver, username_to_analyze)

        if analysis_result:
            print(
                f"✅ Analysis completed successfully for {username_to_analyze}")
            print(
                f"📊 Posts analyzed: {analysis_result.get('posts_analyzed', 0)}")
            print(
                f"🏷️ Interests found: {len(analysis_result.get('interests', []))}")
            print(
                f"💬 Conversation topics: {len(analysis_result.get('conversation_topics', []))}")
            return True
        else:
            print(f"❌ Analysis failed for {username_to_analyze}")
            return False

    except Exception as e:
        print(f"❌ Error in direct analysis: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Keep browser open for debugging
        print("🔧 Browser will stay open for debugging. Close manually when done.")


if __name__ == "__main__":
    # --- Command Line Argument Parsing (only when run directly) ---
    parser = argparse.ArgumentParser(description='Instagram profile analyzer')
    parser.add_argument('--followers-list', type=str, default='instagram_followers.txt',
                        help='Path to the file containing the list of Instagram followers')
    parser.add_argument('--chromedriver', type=str, default=None,
                        help='Path to ChromeDriver executable (overrides default paths)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what usernames would be processed without running analysis')
    parser.add_argument('--force', action='store_true',
                        help='Force re-analysis of users even if they already have data')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode - keeps browser open for manual intervention')
    parser.add_argument('--direct-user', type=str, default=None,
                        help='Directly analyze a single user (bypasses all filtering)')
    args = parser.parse_args()

    # Update global variables based on arguments
    FOLLOWERS_LIST = os.path.join(SCRIPT_DIR, args.followers_list)

    # Check for direct user analysis mode
    if args.direct_user:
        print(f"🎯 DIRECT USER MODE: Analyzing {args.direct_user}")
        success = analyze_single_user_direct(args.direct_user)
        if success:
            print(f"✅ Direct analysis completed for {args.direct_user}")
        else:
            print(f"❌ Direct analysis failed for {args.direct_user}")
    else:
        process_usernames()
