#!/usr/bin/env python3
"""
Simplified Potential Clients Story Commentor - WORKING VERSION
Targets high-potential fitness clients by analyzing their Instagram stories and sending personalized DMs.
"""

import json
import os
import time
import random
import logging
from typing import Dict, List, Optional
from datetime import datetime
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import threading
import uuid
import msvcrt

# Configuration
CONFIG = {
    "instagram_url": "https://www.instagram.com",
    "chromedriver_path": "C:\\SeleniumDrivers\\chromedriver-win64\\chromedriver.exe",
    "analytics_file": "app/analytics_data_good.json",
    "instagram_username": os.getenv('INSTAGRAM_USERNAME', 'cocos_connected'),
    "instagram_password": os.getenv('INSTAGRAM_PASSWORD', 'Shannonb3')
}

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv(
    'GEMINI_API_KEY', 'AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y')
genai.configure(api_key=GEMINI_API_KEY)


def random_sleep(min_seconds=1, max_seconds=3):
    """Sleep for a random amount of time"""
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)
    return sleep_time


class PauseMonitor:
    """
    Simple background monitor that continuously ensures a story stays paused.
    """

    def __init__(self, driver):
        self.driver = driver
        self.monitoring_active = False
        self.monitoring_thread = None
        self.check_interval = 3.0  # Check every 3 seconds
        self.pause_count = 0  # Track how many times we've re-paused

    def start_monitoring(self):
        """Start continuous pause monitoring in a background thread."""
        if self.monitoring_active:
            return
        self.monitoring_active = True
        self.pause_count = 0
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        print("🔄 Pause monitoring started")

    def stop_monitoring(self):
        """Stop pause monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        if self.pause_count > 0:
            print(
                f"🔄 Pause monitoring stopped (re-paused {self.pause_count} times)")
        else:
            print("🔄 Pause monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop that runs in a background thread."""
        while self.monitoring_active:
            try:
                if not self._is_story_paused_quick():
                    self._re_pause_story()
                    self.pause_count += 1
                    print(
                        f"⚠️ Story auto-advanced, re-paused (#{self.pause_count})")
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"⚠️ Pause monitoring error: {e}")
                time.sleep(2)

    def _is_story_paused_quick(self):
        """Quick check if story is paused."""
        try:
            play_indicators = self.driver.find_elements(By.XPATH,
                                                        "//div[contains(@aria-label, 'Play')] | //*[name()='svg' and contains(@aria-label, 'Play')]")
            for indicator in play_indicators:
                if indicator.is_displayed():
                    return True
            return False
        except Exception:
            return False

    def _re_pause_story(self):
        """Re-pause the story."""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.driver).send_keys(Keys.SPACE).perform()
            time.sleep(0.1)
        except Exception as e:
            print(f"⚠️ Failed to re-pause story: {e}")


class PotentialClientBot:
    """Simplified bot for targeting potential clients through stories"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.pause_monitor = None
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.processed_usernames = set()
        self.processed_file = "processed_users.json"
        self.load_processed_users()
        logger.info("PotentialClientBot initialized")

    def load_processed_users(self):
        """Load previously processed users from file"""
        try:
            if os.path.exists(self.processed_file):
                with open(self.processed_file, 'r') as f:
                    data = json.load(f)
                    # Handle both old and new formats
                    if isinstance(data, list):
                        self.processed_usernames = set(data)
                    else:
                        self.processed_usernames = set(
                            data.get('processed_usernames', []))
                    print(
                        f"📋 Loaded {len(self.processed_usernames)} previously processed users")
            else:
                print("📋 No previous processed users file found - starting fresh")
        except Exception as e:
            print(f"⚠️ Could not load processed users: {e}")
            self.processed_usernames = set()

    def save_processed_users(self):
        """Save processed users to file"""
        try:
            data = {
                'processed_usernames': list(self.processed_usernames),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.processed_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(
                f"💾 Saved {len(self.processed_usernames)} processed users to file")
        except Exception as e:
            print(f"⚠️ Could not save processed users: {e}")

    def setup_driver(self):
        """Set up Chrome WebDriver"""
        try:
            print("Setting up Chrome WebDriver...")
            service = Service(executable_path=CONFIG["chromedriver_path"])
            chrome_options = Options()

            # Use unique Chrome profile
            unique_id = str(uuid.uuid4())[:8]
            profile_dir = os.path.join(os.path.expanduser(
                "~"), "OneDrive", "Desktop", "shanbot", f"chrome_profile_{unique_id}")
            os.makedirs(profile_dir, exist_ok=True)
            chrome_options.add_argument(f"--user-data-dir={profile_dir}")

            # Anti-detection measures
            chrome_options.add_argument(
                '--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option(
                "excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option(
                'useAutomationExtension', False)
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")

            # Initialize driver
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            self.pause_monitor = PauseMonitor(self.driver)

            # Anti-detection via CDP
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                """
            })

            print("ChromeDriver initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error setting up WebDriver: {e}")
            return False

    def login_to_instagram(self) -> bool:
        """Enhanced Instagram login"""
        try:
            print("Logging into Instagram...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(3)

            # Try multiple selectors for username field
            username_selectors = [
                (By.NAME, "username"),
                (By.XPATH,
                 "//input[@aria-label='Phone number, username, or email']"),
                (By.XPATH,
                 "//input[@placeholder='Phone number, username, or email']")
            ]

            username_field = None
            for by, selector in username_selectors:
                try:
                    username_field = self.wait.until(
                        EC.presence_of_element_located((by, selector)))
                    break
                except:
                    continue

            if not username_field:
                print("❌ Could not find username field")
                return False

            username_field.send_keys(CONFIG["instagram_username"])
            time.sleep(1)

            # Find password field
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.send_keys(CONFIG["instagram_password"])
            time.sleep(1)

            # Click login
            login_button = self.driver.find_element(
                By.XPATH, "//button[@type='submit']")
            login_button.click()
            time.sleep(5)

            # Check if logged in by looking for home page elements
            try:
                self.wait.until(
                    lambda driver: "login" not in driver.current_url.lower())
                print("✅ Login successful!")
                return True
            except:
                print("❌ Login failed - check credentials")
                return False

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def navigate_to_user_profile(self, username: str) -> bool:
        """Navigate to a user's profile"""
        try:
            profile_url = f"https://www.instagram.com/{username}/"
            print(f"Navigating to: {username}")
            self.driver.get(profile_url)
            time.sleep(3)

            if "Sorry, this page isn't available" in self.driver.page_source:
                print(f"Profile {username} not found")
                return False

            return True

        except Exception as e:
            logger.error(f"Error navigating to profile {username}: {e}")
            return False

    def click_user_story(self, username: str) -> bool:
        """Try to click on user's story or highlight"""
        try:
            print(f"Looking for story/highlight for {username}...")

            # Look for story ring around profile picture
            story_selectors = [
                "//header//canvas",  # Story ring canvas
                # Profile picture container
                "//header//img[contains(@alt, 'profile picture')]/../..",
                "//div[@role='button'][.//canvas]"  # Clickable story button
            ]

            for selector in story_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            element.click()
                            time.sleep(2)

                            # Verify story opened
                            current_url = self.driver.current_url
                            if 'stories/' in current_url or 'highlights/' in current_url:
                                print(
                                    f"✅ Story/highlight opened for {username}")
                                return True
                        except:
                            continue
                except:
                    continue

            print(f"No stories found for {username}")
            return False

        except Exception as e:
            logger.error(f"Error clicking story for {username}: {e}")
            return False

    def analyze_story_with_gemini(self, screenshot_path: str, username: str) -> Optional[Dict]:
        """Analyze story screenshot with Gemini AI"""
        try:
            print("Analyzing story with Gemini...")

            # Check if screenshot exists and has content
            if not os.path.exists(screenshot_path):
                print(f"❌ Screenshot not found: {screenshot_path}")
                return None

            file_size = os.path.getsize(screenshot_path)
            if file_size < 1000:  # Less than 1KB is probably bad
                print(
                    f"❌ Screenshot too small ({file_size} bytes): {screenshot_path}")
                return None

            print(f"📊 Screenshot size: {file_size} bytes")

            with open(screenshot_path, 'rb') as f:
                image_data = f.read()

            image_part = {
                "mime_type": "image/png",
                "data": image_data
            }

            prompt = f"""You're Shannon, an authentic Australian vegetarian fitness coach who loves connecting with people. Analyze this Instagram story from {username} and provide a description, a comment, and two flags (IS_NEGATIVE, IS_REEL).

            SHANNON'S PERSONALITY:
            - Australian (uses casual Aussie expressions naturally)
            - Vegetarian/plant-based fitness coach
            - Genuine, warm, encouraging but not over-the-top
            - Speaks like a real person, not a bot
            - Interested in fitness, healthy food, and lifestyle
            - Supportive but not pushy

            COMMENTING RULES:
            - **IF IS_REEL is True**: The comment should be a single laughing emoji (😂) or a short 1-4 word reaction to text in the reel (e.g., "Haha love it!", "So true!"). DO NOT ask a question.
            - **IF IS_REEL is False**: The comment must be short (3-8 words) and end with a genuine, simple question.
            - Match the energy of the content. Be authentic.
            - Use 0-2 emojis max. No excessive exclamation marks.
            - NO generic fitness coach language.
            
            GOOD EXAMPLES (if IS_REEL is False):
            ✅ "This looks so good! Recipe?"
            ✅ "Love your form! How'd you learn that?"
            ✅ "That trail looks amazing! Where is it?"
            
            BAD EXAMPLES (too bot-like):
            ❌ "Amazing workout! What's your favorite exercise routine?"
            ❌ "Love this! Keep up the great work! 💪"

            Respond in this EXACT format:
            DESCRIPTION: [Brief, specific description of the main story content.]
            IS_NEGATIVE: [True or False, based on whether the story content is related to war, violence, tragedy, or other significantly negative themes.]
            IS_REEL: [True or False, based on whether the content appears to be a reshared video or "Reel" from another creator.]
            COMMENT: [The comment generated based on the rules above.]"""

            # Add robust retry logic like story1.py
            max_api_retries = 3
            api_retry_count = 0
            api_success = False

            while api_retry_count < max_api_retries and not api_success:
                try:
                    print(
                        f"🤖 Gemini API attempt {api_retry_count + 1}/{max_api_retries}...")

                    response = self.model.generate_content(
                        contents=[
                            {"text": prompt},
                            {"inline_data": image_part}
                        ],
                        generation_config={
                            "temperature": 0.7,
                            "max_output_tokens": 500,
                        }
                    )

                    # Check if response has valid content (story1.py method)
                    if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                        # Valid response with content
                        if response.text and response.text.strip():
                            print(
                                f"✅ Gemini response received: {len(response.text)} characters")
                            print(f"📝 Raw response: {response.text[:200]}...")
                            api_success = True
                        else:
                            # Empty response, retry if possible
                            print(
                                f"⚠️ Gemini returned empty response on attempt {api_retry_count + 1}")
                            api_retry_count += 1
                            if api_retry_count < max_api_retries:
                                print(
                                    f"Waiting before retry {api_retry_count + 1}...")
                                # Wait between retries
                                time.sleep(random.uniform(3, 5))
                    else:
                        print(
                            f"⚠️ Gemini returned no candidates on attempt {api_retry_count + 1}")
                        api_retry_count += 1
                        if api_retry_count < max_api_retries:
                            print(
                                f"Waiting before retry {api_retry_count + 1}...")
                            time.sleep(random.uniform(3, 5))

                except Exception as retry_error:
                    print(
                        f"⚠️ Gemini API error on attempt {api_retry_count + 1}: {retry_error}")
                    api_retry_count += 1
                    if api_retry_count < max_api_retries:
                        print(
                            f"Waiting before retry {api_retry_count + 1}...")
                        time.sleep(random.uniform(3, 5))

            # Check if all retries failed
            if not api_success:
                print("⚠️ All Gemini API retries failed, using fallback values")
                return self._get_fallback_analysis(username, "API retries exhausted")

            # Parse the response
            lines = response.text.strip().split('\n')
            analysis = {
                'is_negative': False,
                'is_reel': False
            }

            for line in lines:
                if line.upper().startswith('DESCRIPTION:'):
                    analysis['description'] = line.split(':', 1)[-1].strip()
                elif line.upper().startswith('COMMENT:'):
                    analysis['comment'] = line.split(':', 1)[-1].strip()
                elif line.upper().startswith('IS_NEGATIVE:'):
                    analysis['is_negative'] = 'true' in line.lower()
                elif line.upper().startswith('IS_REEL:'):
                    analysis['is_reel'] = 'true' in line.lower()

            # Ensure we have all fields with multiple fallback options
            if 'description' not in analysis or not analysis['description']:
                analysis['description'] = f"Story content from {username}"

            if 'comment' not in analysis or not analysis['comment']:
                # Natural Shannon-style fallback comments
                fallback_comments = [
                    "This looks great! Where's this?",
                    "So good! How'd you do it?",
                    "Love this! What inspired you?",
                    "Looks amazing! Any tips?",
                    "That's cool! How long did it take?",
                    "Beautiful! Is this your fave spot?"
                ]
                analysis['comment'] = random.choice(fallback_comments)

            print(
                f"✅ Analysis complete - Description: {analysis['description'][:50]}...")
            return analysis

        except Exception as e:
            print(f"❌ Gemini analysis error: {e}")
            logger.error(f"Error analyzing story: {e}")
            return self._get_fallback_analysis(username, str(e))

    def _get_fallback_analysis(self, username: str, reason: str = "Unknown error") -> Dict:
        """Provide fallback analysis when Gemini fails"""
        print(f"🔄 Using fallback analysis: {reason}")

        # Natural Shannon-style fallback comments
        fallback_comments = [
            "This looks great! Where's this?",
            "So good! How'd you do it?",
            "Love this! What inspired you?",
            "Looks amazing! Any tips?",
            "That's cool! How long did it take?",
            "Beautiful! Is this your fave spot?",
            "Nice work! What's your secret?",
            "This is awesome! How'd you start?"
        ]

        return {
            'description': f"Instagram story from {username} (fallback: {reason})",
            'comment': random.choice(fallback_comments)
        }

    def prepare_for_sending(self, message: str) -> str:
        """Prepare message for sending by removing emojis that ChromeDriver can't handle."""
        # Remove emojis and special Unicode characters, keep only BMP characters
        cleaned_chars = []
        for char in message:
            char_code = ord(char)
            # Only keep characters in Basic Multilingual Plane (BMP) - U+0000 to U+FFFF
            if char_code <= 0xFFFF:
                # But also exclude problematic ranges that might cause issues
                if not (0x1F000 <= char_code <= 0x1FFFF):  # Exclude emoji ranges
                    cleaned_chars.append(char)

        cleaned = ''.join(cleaned_chars).strip()

        # If message became empty after removing emojis, provide a fallback
        if not cleaned:
            return "Nice!"

        return cleaned

    def send_story_reply(self, message: str) -> bool:
        """Send reply to story using proven method from story1.py"""
        try:
            print(f"💬 Sending story reply: {message}")

            # Proven selectors from story1.py
            reply_selectors = [
                "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl')]",
                "//textarea[@placeholder='Reply...']",
                "//form//textarea"
            ]

            # Find reply box
            reply_box = None
            for selector in reply_selectors:
                try:
                    reply_box = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    print(f"✅ Found reply box")
                    break
                except:
                    continue

            if not reply_box:
                print("❌ Could not find reply box")
                return False

            # Type message character by character (story1.py method)
            reply_box.clear()
            message_to_send = self.prepare_for_sending(message)
            for char in message_to_send:
                reply_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            time.sleep(0.5)

            # Send with Enter key
            reply_box.send_keys(Keys.ENTER)
            time.sleep(1)

            print(f"✅ Message sent: {message}")
            return True

        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            return False

    def take_screenshot(self, filename: str) -> bool:
        """Take a screenshot with retry logic like story1.py"""
        try:
            os.makedirs("screenshots", exist_ok=True)
            filepath = f"screenshots/{filename}"

            max_attempts = 2  # Reduced attempts to speed up processing

            for attempt in range(max_attempts):
                try:
                    self.driver.save_screenshot(filepath)

                    # Verify screenshot was created and has content
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                        print(f"📸 Screenshot saved: {filepath}")
                        return True
                    else:
                        print(f"❌ Screenshot failed on attempt {attempt + 1}")

                except Exception as e:
                    print(f"❌ Screenshot error on attempt {attempt + 1}: {e}")

                if attempt < max_attempts - 1:
                    time.sleep(0.2)  # Shorter wait between attempts

            # Final fallback - try basic screenshot without verification
            try:
                print("⚠️ Attempting fallback screenshot without verification")
                self.driver.save_screenshot(filepath)
                if os.path.exists(filepath):
                    print(f"✔️ Fallback screenshot captured: {filepath}")
                    return True
            except Exception as fallback_error:
                print(f"❌ Fallback screenshot failed: {fallback_error}")

            return False

        except Exception as e:
            print(f"❌ Screenshot system error: {e}")
            return False

    def manual_confirmation(self, username: str, description: str, comment: str) -> tuple:
        """Manual confirmation with user input"""
        print("\n" + "=" * 60)
        print("🤖 REVIEW MESSAGE BEFORE SENDING")
        print("=" * 60)
        print(f"👤 Username: {username}")
        print(f"📖 Description: {description}")
        print(f"💬 Suggested Comment: '{comment}'")
        print("=" * 60)

        while True:
            choice = input("\n🤔 What would you like to do?\n"
                           "[1] ✅ Send as-is\n"
                           "[2] ✏️ Edit message\n"
                           "[3] ⏭️ Skip this user\n"
                           "[4] 🛑 Quit campaign\n"
                           "Enter choice (1-4): ").strip()

            if choice == '1':
                print(f"✅ Sending message to {username}: '{comment}'")
                return comment, True, "Approved as-is"

            elif choice == '2':
                new_comment = input(
                    f"\n✏️ Edit message for {username}: ").strip()
                if new_comment:
                    print(
                        f"✅ Sending edited message to {username}: '{new_comment}'")
                    return new_comment, True, "Edited by user"
                else:
                    print("❌ Empty message, please try again.")
                    continue

            elif choice == '3':
                print(f"⏭️ Skipping {username}")
                return comment, False, "Skipped by user"

            elif choice == '4':
                print("🛑 Quitting campaign...")
                return comment, False, "User quit"

            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

    def is_story_paused(self):
        """Simple story pause detection - just try a quick check"""
        try:
            # Look for visible play button (indicates paused)
            try:
                play_button = WebDriverWait(self.driver, 0.5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[contains(@aria-label, 'Play')] | //*[name()='svg' and contains(@aria-label, 'Play')]"))
                )
                if play_button.is_displayed():
                    return True
            except:
                pass

            # If no play button found, assume it's playing
            return False

        except Exception as e:
            return False  # Default to not paused

    def robust_pause_story(self):
        """Simple and reliable story pausing"""
        try:
            print("🟡 Attempting to pause story...")

            # Click to ensure focus, then pause
            try:
                # Click on the story area first
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.click()
                time.sleep(0.2)
            except:
                pass

            # Press space to pause (most stories start playing)
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.driver).send_keys(Keys.SPACE).perform()
            time.sleep(0.5)  # Give it time to register

            print("✅ Pause command sent")
            return True

        except Exception as e:
            print(f"❌ Error in robust_pause_story: {e}")
            return False

    def pause_and_check_comment_box(self):
        """Enhanced pause and comment box check with better verification"""
        try:
            # First, try to pause the story robustly
            pause_success = self.robust_pause_story()

            # Short delay to let UI settle
            time.sleep(0.3)

            # Check for comment box
            reply_box_selectors = [
                "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl')]",
                "//textarea[@placeholder='Reply...']",
                "//textarea[@placeholder='Send message']",
                "//form//textarea"
            ]

            comment_box_found = False
            for selector in reply_box_selectors:
                try:
                    element = WebDriverWait(self.driver, 1).until(
                        EC.presence_of_element_located((By.XPATH, selector)))
                    if element.is_displayed():
                        comment_box_found = True
                        break
                except:
                    continue

            if comment_box_found:
                print("✅ Story paused and comment box found")
                return True
            else:
                print("❌ No comment box found (likely an ad or non-commentable story)")
                return False

        except Exception as e:
            print(f"❌ Error in pause_and_check_comment_box: {e}")
            return False

    def ensure_story_stays_paused(self):
        """Ensure story remains paused during processing"""
        try:
            if not self.is_story_paused():
                print("⚠️ Story became unpaused, re-pausing...")
                return self.robust_pause_story()
            else:
                print("✅ Story is still paused")
            return True
        except Exception as e:
            print(f"⚠️ Error ensuring story stays paused: {e}")
            return False

    def keep_story_paused(self):
        """Smart re-pause that checks state first"""
        try:
            # Check if already paused before pressing space (to avoid toggle issue)
            if not self.is_story_paused():
                print("🔄 Story not paused, pausing...")
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.SPACE).perform()
                time.sleep(0.1)  # Minimal wait
            # If already paused, don't press space (would unpause it)
        except Exception as e:
            print(f"⚠️ Keep-pause failed: {e}")

    def has_comment_box(self):
        """Ultra-fast comment box detection"""
        try:
            reply_box_selectors = [
                "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl')]",
                "//textarea[@placeholder='Reply...']",
                "//form//textarea"
            ]

            # Single fast attempt
            for selector in reply_box_selectors:
                try:
                    element = WebDriverWait(self.driver, 0.3).until(
                        EC.presence_of_element_located((By.XPATH, selector)))
                    if element.is_displayed():
                        return True
                except:
                    continue

            return False

        except Exception as e:
            return False

    def process_story(self, username: str) -> bool:
        """Process a single story"""
        self.pause_monitor.start_monitoring()
        try:
            print(f"\n🎯 Processing story for {username}")

            # Use enhanced pause and comment box detection
            if not self.pause_and_check_comment_box():
                print(f"⏭️ Skipping {username} - no comment box available")
                return False

            time.sleep(0.5)  # Brief pause for stability

            # Take screenshot
            screenshot_name = f"story_{username}_{int(time.time())}.png"
            if not self.take_screenshot(screenshot_name):
                return False

            # Analyze with Gemini
            screenshot_path = f"screenshots/{screenshot_name}"
            analysis = self.analyze_story_with_gemini(
                screenshot_path, username)

            if not analysis:
                print("❌ Could not analyze story")
                return False

            # Skip if content is negative
            if analysis.get('is_negative', False):
                print(f"⏭️ Skipping {username} due to negative content.")
                return False

            description = analysis.get('description', 'Story content')
            comment = analysis.get('comment', 'Love this! 🔥')

            # Manual confirmation
            final_comment, should_send, reason = self.manual_confirmation(
                username, description, comment)

            if not should_send:
                if reason == "User quit":
                    return "QUIT"
                print(f"⏭️ Skipping {username}: {reason}")
                # Still track skipped users so we don't retry them
                self.processed_usernames.add(username)
                self.save_processed_users()
                return False

            # Send message
            success = self.send_story_reply(final_comment)
            if success:
                self.processed_usernames.add(username)
                self.save_processed_users()  # Save after each successful message
                print(f"✅ Successfully messaged {username}")
                return True
            else:
                print(f"❌ Failed to send message to {username}")
                return False

        except Exception as e:
            logger.error(f"Error processing story for {username}: {e}")
            return False
        finally:
            self.pause_monitor.stop_monitoring()

    def run_campaign(self):
        """Run the main campaign"""
        print("🚀 Starting Potential Clients Story Campaign")

        # Get high potential clients from Shannon's dashboard with score above 70
        print("📊 Loading high potential clients from dashboard...")
        try:
            from identify_potential_clients import get_high_potential_clients

            # Try score >= 70 first
            high_potential_clients = get_high_potential_clients(min_score=70)

            # If not enough clients, try lower thresholds
            if len(high_potential_clients) < 5:
                print(
                    f"⚠️ Only found {len(high_potential_clients)} clients with score >= 70")
                print("🔄 Trying score >= 60...")
                high_potential_clients = get_high_potential_clients(
                    min_score=60)

            if len(high_potential_clients) < 5:
                print(
                    f"⚠️ Only found {len(high_potential_clients)} clients with score >= 60")
                print("🔄 Trying score >= 50...")
                high_potential_clients = get_high_potential_clients(
                    min_score=50)

                # Always prioritize our comprehensive list of 71 high-potential prospects
            print(
                "🎯 Using comprehensive list of 71 high-value prospects from dashboard...")

            # Continue from kynd.to.all.kinds onwards (skipping already processed users)
            test_usernames = [
                # ALREADY PROCESSED: cocos_pt_studio, liftingwithhayley, beelovedkitchen, veganmuscleorganics, theplantpowercoach, your_vegan_family
                # Score 85/100 - Continue from here
                "kynd.to.all.kinds", "leafcutterlean", "fatvegangetsfit", "dermacura__beauty_and_health",
                "cgordonfit", "ernspiration", "eatonlyplants", "plantbasedrich", "veganos_actualizados",
                "veganbeing", "compassioneat.au", "one.happy.flexitarian",
                # Score 80/100
                "soyhapppy", "fit_force2024", "healthyinternational",
                # Score 78/100 - High Potential
                "vanessa_4.0", "greeniegenie42", "glc_chefathome", "ohmmumma", "leannespeaking",
                "anv7_7", "hippiedepipi_free_spirit", "lucys_healthy_vegan_lifestyle", "marcus.healed",
                # Score 75/100
                "karliekilpatrick", "kayla.ackroyd", "fitnesstrek_", "veg_head_vero", "cookingwithamica",
                "oh_my_yoga", "savvy095", "thewtfvegan", "emsveganjourney", "crazyfitvegan_",
                "veggie_good_apparel", "yogabloomswithcandy", "belicious_foods", "_organic_cookie",
                "veganism_is_magic_", "mockingbirdrawpress", "love_on_yourself_today", "bre.with.nature",
                "vegan_omad_no1", "strength_meals_co", "mrsplantbasedaf", "diary_of_a_phat_vegan",
                "nutrakynd", "challengingmovement",
                # Score 70/100
                "ona.taste_buddies", "silverbacktarzan", "roamingphar", "samrdella", "daancho",
                "7healthydays", "musclemindmentality", "plant.paradigm", "radiantveganvixen",
                "flexfitness_gc", "sellawindi", "tasteamaze", "denverlight9", "recrearte_vegan",
                "veganmanforever", "fitnessaddictcat", "fit_babe_33"
            ]

            # Add any additional clients found in analytics that aren't already in the list
            if high_potential_clients:
                print(
                    f"📊 Also found {len(high_potential_clients)} clients in analytics:")
                for client in high_potential_clients:
                    username = client.get(
                        'ig_username') or client.get('username')
                    score = client.get('score', 0)
                    category = client.get('category', 'Unknown')
                    print(f"  • {username:<20} Score: {score:3d} ({category})")

                    # Add to list if not already there
                    if username and username not in test_usernames:
                        test_usernames.append(username)

            print(f"🚀 Total prospects to target: {len(test_usernames)}")
            print(f"📋 First 10: {', '.join(test_usernames[:10])}")
            if len(test_usernames) > 10:
                print(f"   ... and {len(test_usernames) - 10} more!")

        except ImportError as e:
            print(f"⚠️ Could not import scoring system: {e}")
            print("Using high-value prospects from dashboard...")
            # These are the 71 excellent prospects from Shannon's dashboard (scores 70-95)
            test_usernames = [
                # Score 95/100 - Excellent Prospects
                "cocos_pt_studio", "liftingwithhayley", "beelovedkitchen", "veganmuscleorganics",
                # Score 90/100
                "theplantpowercoach",
                # Score 88/100
                "your_vegan_family",
                # Score 85/100
                "kynd.to.all.kinds", "leafcutterlean", "fatvegangetsfit", "dermacura__beauty_and_health",
                "cgordonfit", "ernspiration", "eatonlyplants", "plantbasedrich", "veganos_actualizados",
                "veganbeing", "compassioneat.au", "one.happy.flexitarian",
                # Score 80/100
                "soyhapppy", "fit_force2024", "healthyinternational",
                # Score 78/100 - High Potential
                "vanessa_4.0", "greeniegenie42", "glc_chefathome", "ohmmumma", "leannespeaking",
                "anv7_7", "hippiedepipi_free_spirit", "lucys_healthy_vegan_lifestyle", "marcus.healed",
                # Score 75/100
                "karliekilpatrick", "kayla.ackroyd", "fitnesstrek_", "veg_head_vero", "cookingwithamica",
                "oh_my_yoga", "savvy095", "thewtfvegan", "emsveganjourney", "crazyfitvegan_",
                "veggie_good_apparel", "yogabloomswithcandy", "belicious_foods", "_organic_cookie",
                "veganism_is_magic_", "mockingbirdrawpress", "love_on_yourself_today", "bre.with.nature",
                "vegan_omad_no1", "strength_meals_co", "mrsplantbasedaf", "diary_of_a_phat_vegan",
                "nutrakynd", "challengingmovement",
                # Score 70/100
                "ona.taste_buddies", "silverbacktarzan", "roamingphar", "samrdella", "daancho",
                "7healthydays", "musclemindmentality", "plant.paradigm", "radiantveganvixen",
                "flexfitness_gc", "sellawindi", "tasteamaze", "denverlight9", "recrearte_vegan",
                "veganmanforever", "fitnessaddictcat", "fit_babe_33"
            ]
        except Exception as e:
            print(f"⚠️ Error loading high potential clients: {e}")
            print("Using high-value prospects from dashboard...")
            # These are the 71 excellent prospects from Shannon's dashboard (scores 70-95)
        test_usernames = [
            # Score 95/100 - Excellent Prospects
            "cocos_pt_studio", "liftingwithhayley", "beelovedkitchen", "veganmuscleorganics",
            # Score 90/100
            "theplantpowercoach",
            # Score 88/100
            "your_vegan_family",
            # Score 85/100
            "kynd.to.all.kinds", "leafcutterlean", "fatvegangetsfit", "dermacura__beauty_and_health",
            "cgordonfit", "ernspiration", "eatonlyplants", "plantbasedrich", "veganos_actualizados",
            "veganbeing", "compassioneat.au", "one.happy.flexitarian",
            # Score 80/100
            "soyhapppy", "fit_force2024", "healthyinternational",
            # Score 78/100 - High Potential
            "vanessa_4.0", "greeniegenie42", "glc_chefathome", "ohmmumma", "leannespeaking",
            "anv7_7", "hippiedepipi_free_spirit", "lucys_healthy_vegan_lifestyle", "marcus.healed",
            # Score 75/100
            "karliekilpatrick", "kayla.ackroyd", "fitnesstrek_", "veg_head_vero", "cookingwithamica",
            "oh_my_yoga", "savvy095", "thewtfvegan", "emsveganjourney", "crazyfitvegan_",
            "veggie_good_apparel", "yogabloomswithcandy", "belicious_foods", "_organic_cookie",
            "veganism_is_magic_", "mockingbirdrawpress", "love_on_yourself_today", "bre.with.nature",
            "vegan_omad_no1", "strength_meals_co", "mrsplantbasedaf", "diary_of_a_phat_vegan",
            "nutrakynd", "challengingmovement",
            # Score 70/100
            "ona.taste_buddies", "silverbacktarzan", "roamingphar", "samrdella", "daancho",
            "7healthydays", "musclemindmentality", "plant.paradigm", "radiantveganvixen",
            "flexfitness_gc", "sellawindi", "tasteamaze", "denverlight9", "recrearte_vegan",
            "veganmanforever", "fitnessaddictcat", "fit_babe_33"
        ]

        try:
            if not self.setup_driver():
                return False

            if not self.login_to_instagram():
                return False

            successful = 0

            for username in test_usernames:
                print(f"\n{'='*50}")
                print(f"Processing user: {username}")
                print(f"{'='*50}")

                if username in self.processed_usernames:
                    print(f"Already processed {username}, skipping...")
                    continue

                # Navigate to profile
                if not self.navigate_to_user_profile(username):
                    continue

                # Try to click story
                if not self.click_user_story(username):
                    print(f"No story available for {username}")
                    continue

                # Check if the story is a highlight and skip if it is
                if 'highlights/' in self.driver.current_url:
                    print(
                        f"⏭️ Skipping {username} because this is a story highlight.")
                    continue

                # Process the story
                result = self.process_story(username)
                if result == "QUIT":
                    print("User requested to quit")
                    break
                elif result:
                    successful += 1

                # Delay between users
                time.sleep(random.uniform(30, 60))

            print(
                f"\n✅ Campaign complete! Successfully processed {successful} users")
            return True

        except Exception as e:
            logger.error(f"Campaign error: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()


def main():
    """Main function"""
    bot = PotentialClientBot()
    bot.run_campaign()


if __name__ == "__main__":
    main()
