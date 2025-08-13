#!/usr/bin/env python3
"""
Clean Potential Clients Story Commentor - SIMPLIFIED VERSION
Fixed pause logic that doesn't get stuck.
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

# Import SQLite utilities for conversation tracking
try:
    from app.dashboard_modules.dashboard_sqlite_utils import add_message_to_history
    SQLITE_AVAILABLE = True
    print("✅ SQLite integration available - story interactions will be tracked")
except ImportError as e:
    print(f"⚠️ SQLite integration not available: {e}")
    SQLITE_AVAILABLE = False

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


class PotentialClientBot:
    """Simplified bot for targeting potential clients through stories"""

    def __init__(self):
        self.driver = None
        self.wait = None
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

    def save_story_interaction_to_sqlite(self, username: str, story_description: str, comment_sent: str, interaction_type: str = "story_comment"):
        """Save story interaction to SQLite conversation history"""
        if not SQLITE_AVAILABLE:
            return False

        try:
            # Create a detailed message about the story interaction
            interaction_message = f"Story Interaction: {story_description}\nComment sent: {comment_sent}"

            # Save to SQLite conversation history
            success = add_message_to_history(
                ig_username=username,
                message_type="ai",  # This is Shannon's AI sending the message
                message_text=interaction_message,
                message_timestamp=datetime.now().isoformat()
            )

            if success:
                print(f"✅ Story interaction saved to SQLite for {username}")
                return True
            else:
                print(
                    f"⚠️ Failed to save story interaction to SQLite for {username}")
                return False

        except Exception as e:
            print(f"❌ Error saving story interaction to SQLite: {e}")
            return False

    def save_story_analysis_to_sqlite(self, username: str, story_description: str, ai_comment: str, final_comment: str, action_taken: str):
        """Save detailed story analysis to SQLite for learning and tracking"""
        if not SQLITE_AVAILABLE:
            return False

        try:
            # Create a detailed analysis record
            analysis_data = {
                "story_description": story_description,
                "ai_generated_comment": ai_comment,
                "final_comment_sent": final_comment,
                "action_taken": action_taken,  # "sent", "skipped", or "edited"
                "timestamp": datetime.now().isoformat(),
                "interaction_type": "story_analysis"
            }

            # Save as a structured message for analysis purposes
            analysis_message = f"Story Analysis Data: {json.dumps(analysis_data, indent=2)}"

            success = add_message_to_history(
                ig_username=username,
                message_type="ai_analysis",  # Different type for analysis data
                message_text=analysis_message,
                message_timestamp=datetime.now().isoformat()
            )

            if success:
                print(f"📊 Story analysis data saved to SQLite for {username}")
                return True
            else:
                print(
                    f"⚠️ Failed to save story analysis to SQLite for {username}")
                return False

        except Exception as e:
            print(f"❌ Error saving story analysis to SQLite: {e}")
            return False

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
            time.sleep(5)

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
            time.sleep(2)

            # Find password field
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.send_keys(CONFIG["instagram_password"])
            time.sleep(2)

            # Click login
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
            login_button.click()
            time.sleep(8)

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

    def has_unviewed_recent_story(self, username: str) -> bool:
        """Check if user has UNVIEWED recent stories (RED/colorful rings only)"""
        try:
            print(f"🔍 Looking for RED/colorful story rings for {username}...")

            # Look for story ring with red/colorful gradient (indicates unviewed stories)
            story_ring_selectors = [
                "//header//canvas",  # Story ring canvas
                "//div[@role='button'][.//canvas]",  # Active story indicator
            ]

            for selector in story_ring_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            # Check the parent element for red/colorful gradient styling
                            parent = element.find_element(By.XPATH, "./..")
                            style = parent.get_attribute('style') or ""

                            # Look for RED gradient patterns (Instagram's unviewed story indicator)
                            red_patterns = [
                                'linear-gradient',
                                'conic-gradient',
                                'radial-gradient',
                                # Red color values
                                'rgb(255',  # Bright red
                                'rgb(245',  # Instagram red
                                'rgb(240',
                                '#ff',      # Hex red
                                '#f4',      # Instagram-style red
                                '#e60023',  # Instagram story red
                                '#ff3040',  # Story gradient red
                            ]

                            # Grey patterns (viewed stories) - EXCLUDE these
                            grey_patterns = [
                                'rgb(168',   # Light grey
                                'rgb(219',   # Instagram grey
                                'rgb(142',   # Medium grey
                                '#a8a8a8',   # Hex grey
                                '#dbdbdb',   # Light grey
                                '#8e8e8e',   # Medium grey
                                'rgba(0,0,0,0.1)',  # Transparent grey
                            ]

                            style_lower = style.lower()

                            # First check if it's a viewed (grey) story - SKIP these
                            if any(grey in style_lower for grey in grey_patterns):
                                print(
                                    f"⚠️ Found VIEWED (grey) story ring for {username} - skipping")
                                continue

                            # Check for red/colorful patterns (unviewed stories)
                            if any(red in style_lower for red in red_patterns):
                                print(
                                    f"🔴 Found UNVIEWED (red/colorful) story ring for {username}")
                                return True

                        except Exception as check_error:
                            print(
                                f"⚠️ Error checking style for {username}: {check_error}")
                            continue
                except:
                    continue

            print(f"❌ No RED/colorful story rings found for {username}")
            return False

        except Exception as e:
            print(f"⚠️ Error checking for unviewed recent stories: {e}")
            return False

    def click_user_story(self, username: str) -> bool:
        """Try to click on user's RECENT story (skip highlights)"""
        try:
            print(f"Looking for RECENT stories for {username}...")

            # FIRST: Check if user has unviewed recent stories (red rings)
            if not self.has_unviewed_recent_story(username):
                print(
                    f"❌ No UNVIEWED recent stories found for {username} - skipping")
                return False

            print(
                f"✅ Found unviewed recent story indicators for {username} - proceeding to click")

            # Look for story elements - try multiple approaches
            story_selectors = [
                "//header//canvas",  # Story ring canvas
                # Profile picture container
                "//header//img[contains(@alt, 'profile picture')]/..",
                "//div[@role='button'][.//canvas]",  # Clickable story button
                "//button[.//canvas]",  # Story button with canvas
                # Clickable profile area
                "//header//div[@role='button'][.//img]",
            ]

            story_clicked = False
            for selector in story_selectors:
                if story_clicked:
                    break

                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            print(
                                f"Attempting to click story element for {username}")
                            element.click()
                            time.sleep(3)  # Give more time for page to load

                            # Check what opened
                            current_url = self.driver.current_url
                            if 'stories/' in current_url:
                                print(f"✅ Recent story opened for {username}")
                                story_clicked = True
                                return True
                            elif 'highlights/' in current_url:
                                print(
                                    f"⚠️ Opened highlight instead of recent story for {username}")
                                # Try to go back and try next element
                                self.driver.back()
                                time.sleep(2)
                                continue
                            else:
                                # If URL doesn't contain stories or highlights, check page content
                                page_source = self.driver.page_source.lower()
                                if 'story' in page_source and 'highlight' not in page_source:
                                    print(
                                        f"✅ Story content detected for {username}")
                                    story_clicked = True
                                    return True
                        except Exception as click_error:
                            print(f"⚠️ Click attempt failed: {click_error}")
                            continue
                except:
                    continue

                    # If no recent stories found after all attempts
            if not story_clicked:
                print(
                    f"⚠️ Found unviewed story indicators but couldn't successfully click for {username}")

            print(f"Failed to open unviewed recent story for {username}")
            return False

        except Exception as e:
            logger.error(f"Error clicking story for {username}: {e}")
            return False

    def wait_for_story_to_load(self, timeout=10):
        """Wait for story to fully load before proceeding"""
        try:
            print("⏳ Waiting for story to load...")

            start_time = time.time()
            while time.time() - start_time < timeout:
                # Check for loading indicators
                loading_selectors = [
                    "//div[contains(@class, 'loading')]",
                    "//div[contains(@class, 'spinner')]",
                    "//*[contains(text(), 'Loading')]",
                    "//div[@role='progressbar']"
                ]

                loading_found = False
                for selector in loading_selectors:
                    try:
                        elements = self.driver.find_elements(
                            By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed():
                                loading_found = True
                                break
                        if loading_found:
                            break
                    except:
                        continue

                if not loading_found:
                    # Also check if story content is actually visible
                    story_content_selectors = [
                        "//img[@alt]",  # Story images
                        "//video",     # Story videos
                        # Background images
                        "//div[contains(@style, 'background-image')]"
                    ]

                    content_found = False
                    for selector in story_content_selectors:
                        try:
                            elements = self.driver.find_elements(
                                By.XPATH, selector)
                            if len(elements) > 0:
                                content_found = True
                                break
                        except:
                            continue

                    if content_found:
                        print("✅ Story appears to be loaded")
                        time.sleep(1)  # Extra second for stability
                        return True

                print("   Still loading...")
                time.sleep(0.5)

            print("⚠️ Story loading timeout - proceeding anyway")
            return True

        except Exception as e:
            print(f"⚠️ Error waiting for story load: {e}")
            return True  # Proceed anyway

    def simple_pause_story(self):
        """Simple story pause - wait for load then press space once"""
        try:
            print("⏸️ Pausing story...")

            # First wait for story to fully load
            if not self.wait_for_story_to_load():
                return False

            # Click to focus first
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.click()
                time.sleep(0.2)
            except:
                pass

            # Press space to pause
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.driver).send_keys(Keys.SPACE).perform()
            time.sleep(0.5)

            print("✅ Pause command sent")
            return True

        except Exception as e:
            print(f"❌ Error pausing story: {e}")
            return False

    def has_comment_box(self) -> bool:
        """Check if story has a comment box"""
        try:
            reply_box_selectors = [
                "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl')]",
                "//textarea[@placeholder='Reply...']",
                "//textarea[@placeholder='Send message']",
                "//form//textarea"
            ]

            for selector in reply_box_selectors:
                try:
                    element = WebDriverWait(self.driver, 1).until(
                        EC.presence_of_element_located((By.XPATH, selector)))
                    if element.is_displayed():
                        return True
                except:
                    continue

            return False

        except Exception as e:
            return False

    def is_viewing_highlight(self) -> bool:
        """Enhanced check if we're viewing a highlight vs recent story"""
        try:
            print("🔍 Checking if this is a highlight...")

            # Method 1: Check URL for highlights
            current_url = self.driver.current_url
            if 'highlights/' in current_url:
                print("❌ HIGHLIGHT DETECTED: URL contains 'highlights/'")
                return True

            # Method 2: Look for highlight-specific UI elements
            highlight_indicators = [
                "//div[contains(text(), 'Highlight')]",
                "//div[contains(@aria-label, 'Highlight')]",
                "//div[contains(text(), 'highlight')]",
                # Highlight title bar
                "//header//div[contains(@class, 'highlight')]",
                # Story archive indicators
                "//div[contains(text(), 'Story Archive')]"
            ]

            for selector in highlight_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if len(elements) > 0:
                        print("❌ HIGHLIGHT DETECTED: Found highlight UI element")
                        return True
                except:
                    continue

            # Method 3: Look for old timestamps in visible story content (not page source)
            try:
                # Look for timestamp elements that are actually visible and near story content
                timestamp_selectors = [
                    # Time elements with weeks
                    "//time[contains(text(), 'w')]",
                    # Time elements with years
                    "//time[contains(text(), 'y')]",
                    # Spans with weeks but not "now"
                    "//span[contains(text(), 'w') and not(contains(text(), 'now'))]",
                    # Timestamp divs
                    "//div[contains(@class, 'timestamp')]//text()[contains(., 'w')]",
                ]

                for selector in timestamp_selectors:
                    try:
                        elements = self.driver.find_elements(
                            By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed():
                                text = element.text.strip()
                                # Look for specific old patterns in visible elements
                                import re
                                # 20+ weeks/months/years
                                if re.search(r'\b\d+[2-9]\d*[wmy]\b', text):
                                    print(
                                        f"❌ HIGHLIGHT DETECTED: Found old visible timestamp: {text}")
                                    return True
                    except:
                        continue
            except:
                pass

            # Method 4: Check for highlight ring vs story ring
            try:
                # Story rings are usually colorful gradients, highlight rings are often grey/muted
                canvas_elements = self.driver.find_elements(
                    By.XPATH, "//canvas")
                for canvas in canvas_elements:
                    try:
                        parent = canvas.find_element(By.XPATH, "./..")
                        style = parent.get_attribute('style') or ""
                        # Check if it's a muted/grey ring (highlight) vs colorful (story)
                        if 'rgb(219, 219, 219)' in style or 'rgb(168, 168, 168)' in style:
                            print(
                                "❌ HIGHLIGHT DETECTED: Found grey/muted ring styling")
                            return True
                    except:
                        continue
            except:
                pass

            print("✅ This appears to be a RECENT STORY (not highlight)")
            return False

        except Exception as e:
            print(f"⚠️ Error checking highlight status: {e}")
            return False  # Default to allowing it if we can't determine

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

            prompt = f"""You're Shannon, an authentic Australian vegetarian fitness coach who loves connecting with people. Analyze this Instagram story from {username} and write a super natural, human comment that sounds exactly like Shannon would write.

            CRITICAL: LOOK FOR TIMESTAMPS in the screenshot! 
            - If you see timestamps like "225w", "52w", "1y", etc. this is OLD CONTENT (weeks/years ago)
            - Use PAST TENSE for old content: "loved", "looked", "was", "did"
            - If no timestamp or shows recent (like "2h", "1d"), use present tense
            - Match your language to the age of the content!

            SHANNON'S PERSONALITY:
            - Australian (uses casual Aussie expressions naturally)
            - Vegetarian/plant-based fitness coach
            - Genuine, warm, encouraging but not over-the-top
            - Speaks like a real person, not a bot
            - Uses conversational language
            - Interested in fitness, healthy food, and lifestyle
            - Supportive but not pushy
            
            WRITING STYLE:
            - Keep it SHORT (3-8 words max)
            - Sound completely natural and human
            - Use casual, conversational tone
            - NO emojis (use text emoticons like :) instead)
            - NO excessive exclamation marks
            - NO generic fitness coach language
            - MUST end with a genuine question
            - Write like you're commenting on a friend's story
            - ADJUST TENSE based on timestamp!
            
            BAD EXAMPLES (too bot-like):
            ❌ "Amazing workout! What's your favorite exercise routine?"
            ❌ "Love this! Keep up the great work! 💪"
            ❌ "Incredible transformation! How did you achieve this?"
            
            GOOD EXAMPLES for RECENT content (present tense):
            ✅ "This looks so good! Recipe?"
            ✅ "Love your form! How'd you learn that?"
            ✅ "That trail looks amazing! Where is it?"
            
            GOOD EXAMPLES for OLD content (past tense):
            ✅ "This looked amazing! Where was this?"
            ✅ "Loved this setup! How'd you do it?"
            ✅ "That looked so peaceful! Was it your fave spot?"

            Format:
            DESCRIPTION: [brief description with timestamp if visible]
            COMMENT: [natural, short Shannon-style comment with appropriate tense and question]"""

            # Add robust retry logic
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

                    # Check if response has valid content
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
                        print(f"Waiting before retry {api_retry_count + 1}...")
                        time.sleep(random.uniform(3, 5))

            # Check if all retries failed
            if not api_success:
                print("⚠️ All Gemini API retries failed, using fallback values")
                return self._get_fallback_analysis(username, "API retries exhausted")

            # Parse the response
            lines = response.text.strip().split('\n')
            analysis = {}

            for line in lines:
                if line.startswith('DESCRIPTION:'):
                    analysis['description'] = line.replace(
                        'DESCRIPTION:', '').strip()
                elif line.startswith('COMMENT:'):
                    analysis['comment'] = line.replace('COMMENT:', '').strip()

            # Ensure we have both fields with multiple fallback options
            if 'description' not in analysis or not analysis['description']:
                analysis['description'] = f"Story content from {username}"

            if 'comment' not in analysis or not analysis['comment']:
                # Check if this is likely old content by looking for highlight in URL
                is_highlight = self.is_viewing_highlight()

                if is_highlight:
                    # Past tense fallback comments for highlights/old content
                    fallback_comments = [
                        "This looked great! Where was this?",
                        "So good! How'd you do it?",
                        "Loved this! What inspired you?",
                        "Looked amazing! Any tips?",
                        "That was cool! How long did it take?",
                        "Beautiful! Was this your fave spot?"
                    ]
                else:
                    # Present tense for recent stories
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

        # Check if viewing highlight for appropriate tense
        is_highlight = self.is_viewing_highlight()

        if is_highlight:
            # Past tense for highlights/old content
            fallback_comments = [
                "This looked great! Where was this?",
                "So good! How'd you do it?",
                "Loved this! What inspired you?",
                "Looked amazing! Any tips?",
                "That was cool! How long did it take?",
                "Beautiful! Was this your fave spot?",
                "Nice work! What was your secret?",
                "This was awesome! How'd you start?"
            ]
        else:
            # Present tense for recent stories
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

    def clean_message_for_chrome(self, message: str) -> str:
        """Clean message to remove problematic Unicode characters for ChromeDriver"""
        import re

        # Replace common emojis with text equivalents
        emoji_replacements = {
            '😊': ':)',
            '😁': ':D',
            '😃': ':)',
            '😄': ':D',
            '😆': ':D',
            '😅': ':)',
            '🤣': 'haha',
            '😂': 'haha',
            '😍': '<3',
            '🥰': '<3',
            '😘': ':*',
            '😜': ':P',
            '😉': ';)',
            '👍': 'thumbs up',
            '👏': 'clap',
            '💪': 'strong',
            '🔥': 'fire',
            '❤️': '<3',
            '💕': '<3',
            '💖': '<3',
            '✨': '*sparkle*',
            '🌟': '*star*',
            '🎉': 'party',
            '🙌': 'hands up',
            '💯': '100%',
            '🏋️': 'weights',
            '🥗': 'salad',
            '🌱': 'plant',
            '🌿': 'plants'
        }

        cleaned_message = message
        for emoji, replacement in emoji_replacements.items():
            cleaned_message = cleaned_message.replace(emoji, replacement)

        # Remove any remaining non-BMP characters (emojis we didn't handle)
        cleaned_message = re.sub(r'[^\u0000-\uFFFF]', '', cleaned_message)

        # Clean up extra spaces
        cleaned_message = re.sub(r'\s+', ' ', cleaned_message).strip()

        return cleaned_message

    def send_story_reply(self, message: str) -> bool:
        """Send reply to story with emoji handling"""
        try:
            # Clean the message for ChromeDriver compatibility
            cleaned_message = self.clean_message_for_chrome(message)

            if cleaned_message != message:
                print(f"💬 Original message: {message}")
                print(f"💬 Cleaned message: {cleaned_message}")
            else:
                print(f"💬 Sending story reply: {message}")

            # Find reply box
            reply_selectors = [
                "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl')]",
                "//textarea[@placeholder='Reply...']",
                "//form//textarea"
            ]

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

            # Type message character by character using cleaned message
            reply_box.clear()
            for char in cleaned_message:
                reply_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            time.sleep(0.5)

            # Send with Enter key
            reply_box.send_keys(Keys.ENTER)
            time.sleep(1)

            print(f"✅ Message sent: {cleaned_message}")
            return True

        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            return False

    def is_screenshot_valid(self, filepath: str) -> bool:
        """Check if screenshot is valid and not just a loading screen"""
        try:
            if not os.path.exists(filepath) or os.path.getsize(filepath) < 1000:
                return False

            # Additional check: look for loading indicators in current page
            loading_indicators = [
                "//div[contains(@class, 'loading')]",
                "//div[contains(@class, 'spinner')]",
                "//*[contains(text(), 'Loading')]"
            ]

            for selector in loading_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            print("⚠️ Loading screen detected in screenshot")
                            return False
                except:
                    continue

            return True

        except Exception as e:
            print(f"⚠️ Error validating screenshot: {e}")
            return True  # Assume valid if we can't check

    def take_screenshot(self, filename: str) -> bool:
        """Take a screenshot and ensure it's valid"""
        try:
            os.makedirs("screenshots", exist_ok=True)
            filepath = f"screenshots/{filename}"

            max_attempts = 3  # Increased attempts for loading issues

            for attempt in range(max_attempts):
                try:
                    # Wait a moment for any loading to finish
                    time.sleep(0.5)

                    self.driver.save_screenshot(filepath)

                    # Verify screenshot is valid and not a loading screen
                    if self.is_screenshot_valid(filepath):
                        print(f"📸 Valid screenshot saved: {filepath}")
                        return True
                    else:
                        print(
                            f"⚠️ Screenshot invalid on attempt {attempt + 1} (loading screen or too small)")

                except Exception as e:
                    print(f"❌ Screenshot error on attempt {attempt + 1}: {e}")

                if attempt < max_attempts - 1:
                    print("   Waiting for story to stabilize...")
                    time.sleep(1)  # Longer wait between attempts

            # Final fallback
            try:
                print("⚠️ Attempting final fallback screenshot")
                time.sleep(1)  # One more wait
                self.driver.save_screenshot(filepath)
                if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
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

    def process_story(self, username: str) -> bool:
        """Process a single story (recent stories only, not highlights)"""
        try:
            print(f"\n🎯 Processing story for {username}")

            # Since we already filtered for recent stories in click_user_story(),
            # we can trust that this is a recent story and proceed
            print(f"✅ Processing recent story for {username}")

            # Pause story first
            if not self.simple_pause_story():
                return False

            # Check if there's a comment box (skip ads)
            if not self.has_comment_box():
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

            description = analysis.get('description', 'Story content')
            comment = analysis.get('comment', 'Love this! 🔥')

            # Manual confirmation
            final_comment, should_send, reason = self.manual_confirmation(
                username, description, comment)

            # Determine action taken for analysis tracking
            if not should_send:
                action_taken = "skipped" if reason != "User quit" else "quit"
            elif final_comment != comment:
                action_taken = "edited"
            else:
                action_taken = "sent_as_is"

            # Save analysis data regardless of whether message was sent
            self.save_story_analysis_to_sqlite(
                username=username,
                story_description=description,
                ai_comment=comment,
                final_comment=final_comment,
                action_taken=action_taken
            )

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

                # Save interaction to SQLite conversation history
                self.save_story_interaction_to_sqlite(
                    username=username,
                    story_description=description,
                    comment_sent=final_comment,
                    interaction_type="story_comment"
                )

                print(f"✅ Successfully messaged {username}")
                return True
            else:
                print(f"❌ Failed to send message to {username}")
                return False

        except Exception as e:
            logger.error(f"Error processing story for {username}: {e}")
            return False

    def run_campaign(self):
        """Run the main campaign targeting recent stories only"""
        print("🚀 Starting Potential Clients Story Campaign (Recent Stories Only)")
        print("📝 Note: This campaign targets RECENT STORIES only, not highlight reels")

        # High-value prospects from dashboard (scores 70-95)
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

        print(f"🚀 Total prospects to target: {len(test_usernames)}")
        print(f"📋 First 10: {', '.join(test_usernames[:10])}")

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
