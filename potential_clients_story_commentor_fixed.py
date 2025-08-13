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


class PotentialClientBot:
    """Simplified bot for targeting potential clients through stories"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.processed_usernames = set()
        logger.info("PotentialClientBot initialized")

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

            prompt = f"""Analyze this Instagram story from {username}. 

            Provide:
            1. Brief description of what's happening
            2. A friendly, casual comment (5-10 words) suitable for Shannon, an Australian vegetarian fitness coach
            3. MUST end with a question to encourage engagement and conversation
            4. Keep it authentic and relevant to what you see

            Format:
            DESCRIPTION: [brief description]
            COMMENT: [short friendly comment ending with a question]
            
            Examples:
            - "Love this workout! What's your favorite exercise?"
            - "Amazing form! How long have you been training?"
            - "That looks delicious! Do you meal prep often?"
            """

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
            analysis = {}

            for line in lines:
                if line.startswith('DESCRIPTION:'):
                    analysis['description'] = line.replace(
                        'DESCRIPTION:', '').strip()
                elif line.startswith('COMMENT:'):
                    analysis['comment'] = line.replace(
                        'COMMENT:', '').strip()

            # Ensure we have both fields with multiple fallback options
            if 'description' not in analysis or not analysis['description']:
                analysis['description'] = f"Story content from {username}"

            if 'comment' not in analysis or not analysis['comment']:
                # Multiple comment fallbacks like story1.py
                fallback_comments = ["Love this! 🔥",
                                     "Looking good!", "Nice!", "Awesome!"]
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

        # Multiple fallback comment options with questions like story1.py
        fallback_comments = [
            "Love this! What's your favorite workout?",
            "Looking good! How long have you been training?",
            "Nice! What motivates you most?",
            "Awesome! Do you have a training routine?",
            "Love it! What's your fitness goal?",
            "Great shot! How often do you work out?",
            "Amazing! What's your favorite exercise?",
            "So cool! Any fitness tips to share?"
        ]

        return {
            'description': f"Instagram story from {username} (fallback: {reason})",
            'comment': random.choice(fallback_comments)
        }

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
            for char in message:
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
        """Get manual confirmation from user"""
        print("\n" + "=" * 60)
        print("🔍 MESSAGE CONFIRMATION")
        print("=" * 60)
        print(f"👤 Username: {username}")
        print(f"📖 Description: {description}")
        print(f"💬 Proposed Comment: '{comment}'")
        print("=" * 60)

        while True:
            print("\nOptions:")
            print("1. Press ENTER to send as-is")
            print("2. Type 'edit' to modify")
            print("3. Type 'skip' to skip")
            print("4. Type 'quit' to stop")

            choice = input("\n➤ Your choice: ").strip().lower()

            if choice == "" or choice == "1":
                return comment, True, None
            elif choice in ["edit", "e", "2"]:
                new_comment = input("➤ Enter new comment: ").strip()
                if new_comment:
                    return new_comment, True, "User edited message"
            elif choice in ["skip", "s", "3"]:
                return None, False, "User skipped"
            elif choice in ["quit", "q", "4"]:
                return None, False, "User quit"
            else:
                print("❌ Invalid choice. Try again.")

    def pause_story(self) -> bool:
        """Pause the story by pressing space"""
        try:
            print("⏸️ Pausing story...")
            # Try clicking on the story area first to ensure focus
            try:
                story_area = self.driver.find_element(By.TAG_NAME, "body")
                story_area.click()
                time.sleep(0.2)
            except:
                pass

            # Send space key to pause
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.driver).send_keys(Keys.SPACE).perform()
            time.sleep(0.5)

            print("✅ Story paused")
            return True
        except Exception as e:
            print(f"⚠️ Could not pause story: {e}")
            return False

    def process_story(self, username: str) -> bool:
        """Process a single story"""
        try:
            print(f"\n🎯 Processing story for {username}")

            # First, pause the story to get a stable screenshot
            self.pause_story()
            time.sleep(1)  # Give it a moment to fully pause

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

            if not should_send:
                if reason == "User quit":
                    return "QUIT"
                print(f"⏭️ Skipping {username}: {reason}")
                return False

            # Send message
            success = self.send_story_reply(final_comment)
            if success:
                self.processed_usernames.add(username)
                print(f"✅ Successfully messaged {username}")
                return True
            else:
                print(f"❌ Failed to send message to {username}")
                return False

        except Exception as e:
            logger.error(f"Error processing story for {username}: {e}")
            return False

    def run_campaign(self):
        """Run the main campaign"""
        print("🚀 Starting Potential Clients Story Campaign")

        # Get real users from Shannon's analytics with fitness interests
        # These are actual users from your dashboard (excluding the 3 already tested: beelovedkitchen, jeanettespinette, itshannahgray)
        test_usernames = [
            "life_of_a_fitdad", "chean_kbt", "suburbanspartan", "jess_leyshan",
            "jason.layton", "teak__7", "steven.kousis", "brandon.zalcman",
            "mtss_photography", "cocos_pt_studio", "65700214", "599165432",
            "fitnessmodel", "healthcoach", "workoutmotivation", "nutritiontips",
            "strongnotskinny", "veganfitness", "plantbasedlife", "marathontraining"
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
