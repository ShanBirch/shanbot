import google.api_core.exceptions
import google.generativeai as genai
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from app.dashboard_modules.dashboard_sqlite_utils import get_db_connection, save_metrics_to_sqlite
import asyncio
import sqlite3
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Set
import os
import sys
import traceback
import random

# Add the project root to sys.path for imports
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import existing modules

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("background_bio_fetcher")

# Configuration
SQLITE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"
GEMINI_API_KEY = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
CHROME_DRIVER_PATH = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"

# Instagram credentials
USERNAME = "cocos_connected"
PASSWORD = "Shannonb3"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Gemini models with fallbacks
GEMINI_MODEL_PRO = "gemini-2.0-flash"
GEMINI_MODEL_FLASH = "gemini-2.0-flash-lite"
GEMINI_MODEL_FLASH_STANDARD = "gemini-2.0-flash-thinking-exp-01-21"


class BackgroundBioFetcher:
    def __init__(self):
        self.running = False
        self.check_interval = 30  # Check for new users every 30 seconds
        self.driver = None
        self.logged_in = False
        self.processed_users = set()
        self.last_db_check = None

    def setup_browser(self):
        """Setup Chrome browser for Instagram scraping with enhanced stealth"""
        try:
            chrome_options = Options()

            # Essential stealth options
            chrome_options.add_argument(
                "--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option(
                "excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option(
                'useAutomationExtension', False)

            # User agent - use a recent, real Chrome user agent
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            # Performance and stability options
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument(
                "--disable-features=VizDisplayCompositor")

            # Memory and cache options
            chrome_options.add_argument("--max_old_space_size=4096")
            chrome_options.add_argument(
                "--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument(
                "--disable-backgrounding-occluded-windows")

            # Language and locale
            chrome_options.add_argument("--lang=en-US")
            chrome_options.add_preference("intl.accept_languages", "en-US,en")

            # Headless mode for background operation (you can comment this out for debugging)
            # chrome_options.add_argument("--headless")  # Uncomment for invisible browser

            # Window size (make it look like a real browser)
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")

            if not os.path.exists(CHROME_DRIVER_PATH):
                logger.error(f"ChromeDriver not found at {CHROME_DRIVER_PATH}")
                return False

            service = webdriver.chrome.service.Service(
                executable_path=CHROME_DRIVER_PATH)
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)

            # Execute stealth scripts to avoid detection
            stealth_script = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            window.chrome = {
                runtime: {}
            };
            
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({ state: 'granted' })
                })
            });
            """

            self.driver.execute_cdp_cmd(
                'Runtime.addBinding', {'name': 'chrome'})
            self.driver.execute_script(stealth_script)

            logger.info(
                "Browser setup successful with enhanced stealth features")
            return True

        except Exception as e:
            logger.error(f"Error setting up browser: {e}")
            return False

    def login_to_instagram(self):
        """Login to Instagram with enhanced handling for 2FA and modern security"""
        try:
            if not self.driver:
                return False

            logger.info("Logging into Instagram...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(5)

            # Handle cookie consent if present
            try:
                cookie_buttons = self.driver.find_elements(By.XPATH,
                                                           "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]")
                if cookie_buttons:
                    cookie_buttons[0].click()
                    time.sleep(2)
            except:
                pass

            # Multiple selectors for username field (Instagram changes these frequently)
            username_selectors = [
                (By.NAME, "username"),
                (By.CSS_SELECTOR, "input[aria-label*='username' i]"),
                (By.CSS_SELECTOR, "input[placeholder*='username' i]"),
                (By.CSS_SELECTOR, "input[autocomplete='username']")
            ]

            username_field = None
            for selector_type, selector in username_selectors:
                try:
                    username_field = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (selector_type, selector))
                    )
                    logger.info(
                        f"Found username field with selector: {selector}")
                    break
                except:
                    continue

            if not username_field:
                logger.error("Could not find username field")
                return False

            # Enter username with human-like typing
            username_field.clear()
            time.sleep(1)
            for char in USERNAME:
                username_field.send_keys(char)
                # Random typing speed
                time.sleep(0.1 + (0.1 * random.random()))

            time.sleep(2)

            # Multiple selectors for password field
            password_selectors = [
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[aria-label*='password' i]"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[autocomplete='current-password']")
            ]

            password_field = None
            for selector_type, selector in password_selectors:
                try:
                    password_field = self.driver.find_element(
                        selector_type, selector)
                    logger.info(
                        f"Found password field with selector: {selector}")
                    break
                except:
                    continue

            if not password_field:
                logger.error("Could not find password field")
                return False

            # Enter password with human-like typing
            password_field.clear()
            time.sleep(1)
            for char in PASSWORD:
                password_field.send_keys(char)
                time.sleep(0.1 + (0.1 * random.random()))

            time.sleep(2)

            # Click login button - multiple selectors
            login_selectors = [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH,
                 "//button[contains(text(), 'Log in') or contains(text(), 'Log In')]"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "div[role='button'][tabindex='0']")
            ]

            login_clicked = False
            for selector_type, selector in login_selectors:
                try:
                    login_button = self.driver.find_element(
                        selector_type, selector)
                    login_button.click()
                    logger.info(
                        f"Clicked login button with selector: {selector}")
                    login_clicked = True
                    break
                except:
                    continue

            if not login_clicked:
                logger.error("Could not find or click login button")
                return False

            # Wait for login to process
            time.sleep(10)

            # Check for various post-login scenarios
            current_url = self.driver.current_url.lower()
            logger.info(f"After login attempt, current URL: {current_url}")

            # Check for 2FA requirement
            if "challenge" in current_url or self._check_for_2fa():
                logger.warning("2FA or additional verification required!")
                logger.warning(
                    "Please complete the verification manually in the browser window.")
                logger.warning(
                    "The system will wait for 60 seconds for you to complete verification...")

                # Wait for manual 2FA completion
                start_time = time.time()
                while time.time() - start_time < 60:  # Wait up to 60 seconds
                    current_url = self.driver.current_url.lower()
                    if "login" not in current_url and "challenge" not in current_url:
                        logger.info(
                            "Manual verification completed successfully!")
                        break
                    time.sleep(2)
                else:
                    logger.error("Manual verification timeout")
                    return False

            # Check if we're successfully logged in
            if self._verify_login_success():
                logger.info("Successfully logged into Instagram")
                self.logged_in = True

                # Handle post-login popups
                self._handle_post_login_popups()
                return True
            else:
                logger.error("Login verification failed")
                self._save_debug_screenshot("login_failed")
                return False

        except Exception as e:
            logger.error(f"Error during Instagram login: {e}")
            self._save_debug_screenshot("login_error")
            return False

    def _check_for_2fa(self) -> bool:
        """Check if 2FA verification is required"""
        try:
            two_fa_indicators = [
                "Enter the 6-digit code",
                "We sent you a code",
                "Enter your phone number",
                "verification code",
                "Please check your email"
            ]

            page_text = self.driver.page_source.lower()
            for indicator in two_fa_indicators:
                if indicator.lower() in page_text:
                    return True

            # Check for specific 2FA elements
            two_fa_selectors = [
                "input[placeholder*='code' i]",
                "input[aria-label*='security code' i]",
                "input[name='verificationCode']"
            ]

            for selector in two_fa_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return True

            return False
        except:
            return False

    def _verify_login_success(self) -> bool:
        """Verify if login was actually successful"""
        try:
            current_url = self.driver.current_url.lower()

            # URL-based checks
            if "login" in current_url:
                return False

            success_indicators = [
                "instagram.com/",
                "instagram.com/accounts/onetap"
            ]

            if any(indicator in current_url for indicator in success_indicators):
                # Additional element-based verification
                success_elements = [
                    (By.CSS_SELECTOR, "svg[aria-label*='Home' i]"),
                    (By.CSS_SELECTOR, "a[href='/']"),
                    (By.CSS_SELECTOR, "[role='navigation']"),
                    (By.CSS_SELECTOR, "input[placeholder*='Search' i]")
                ]

                for selector_type, selector in success_elements:
                    try:
                        elements = self.driver.find_elements(
                            selector_type, selector)
                        if elements:
                            logger.info(
                                f"Login success confirmed by element: {selector}")
                            return True
                    except:
                        continue

            return False
        except:
            return False

    def _handle_post_login_popups(self):
        """Handle popups that appear after successful login"""
        try:
            time.sleep(3)

            popup_dismissers = [
                # Save login info popup
                "//button[contains(text(), 'Not Now') or contains(text(), 'Not now')]",
                # Turn on notifications popup
                "//button[contains(text(), 'Not Now') or contains(text(), 'Not now')]",
                # Various other popups
                "//button[contains(@aria-label, 'Close')]",
                "//button[text()='Save Info' or text()='Save']/following-sibling::button",
            ]

            for xpath in popup_dismissers:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            logger.info(f"Dismissed popup with xpath: {xpath}")
                            time.sleep(2)
                            break
                except:
                    continue

        except Exception as e:
            logger.info(f"No post-login popups to handle: {e}")

    def _save_debug_screenshot(self, prefix: str):
        """Save a screenshot for debugging login issues"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"debug_{prefix}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            logger.info(f"Debug screenshot saved: {filename}")
        except:
            pass

    def get_instagram_bio(self, ig_username: str) -> Optional[Dict[str, Any]]:
        """Fetch bio and basic profile info from Instagram"""
        try:
            if not self.driver or not self.logged_in:
                logger.error("Browser not ready or not logged in")
                return None

            profile_url = f"https://www.instagram.com/{ig_username}/"
            logger.info(f"Fetching bio for {ig_username}")

            self.driver.get(profile_url)
            time.sleep(5)

            bio_data = {
                "ig_username": ig_username,
                "full_name": "",
                "bio_text": "",
                "follower_count": "",
                "following_count": "",
                "post_count": "",
                "is_verified": False,
                "is_private": False,
                "profile_pic_url": "",
                "timestamp": datetime.now().isoformat()
            }

            try:
                # Check if profile is private
                private_indicators = self.driver.find_elements(
                    By.XPATH, "//h2[contains(text(), 'Private')]")
                if private_indicators:
                    bio_data["is_private"] = True
                    logger.info(f"Profile {ig_username} is private")
                    return bio_data
            except:
                pass

            try:
                # Get full name
                full_name_element = self.driver.find_element(
                    By.CSS_SELECTOR, "h1")
                bio_data["full_name"] = full_name_element.text.strip()
            except:
                pass

            try:
                # Get bio text
                bio_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, "h1 + div, h1 + span")
                for element in bio_elements:
                    text = element.text.strip()
                    if text and len(text) > 10:  # Likely bio text
                        bio_data["bio_text"] = text
                        break
            except:
                pass

            try:
                # Get follower/following counts
                count_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, "a[href*='followers'], a[href*='following']")
                for element in count_elements:
                    text = element.text.lower()
                    if "followers" in text:
                        bio_data["follower_count"] = text.replace(
                            "followers", "").strip()
                    elif "following" in text:
                        bio_data["following_count"] = text.replace(
                            "following", "").strip()
            except:
                pass

            try:
                # Check if verified
                verified_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, "svg[aria-label*='Verified']")
                bio_data["is_verified"] = len(verified_elements) > 0
            except:
                pass

            logger.info(f"Successfully fetched bio data for {ig_username}")
            return bio_data

        except Exception as e:
            logger.error(f"Error fetching bio for {ig_username}: {e}")
            return None

    def analyze_bio_with_gemini(self, bio_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze bio data with Gemini to extract conversation topics and insights"""
        try:
            if not bio_data.get("bio_text") and not bio_data.get("full_name"):
                logger.info(
                    f"No bio text or name for {bio_data.get('ig_username')}, skipping Gemini analysis")
                return bio_data

            prompt = f"""
            Analyze this Instagram profile bio and extract useful conversation topics and insights for a fitness coach:

            Username: {bio_data.get('ig_username', '')}
            Full Name: {bio_data.get('full_name', '')}
            Bio Text: {bio_data.get('bio_text', '')}
            Follower Count: {bio_data.get('follower_count', '')}
            Is Private: {bio_data.get('is_private', False)}
            Is Verified: {bio_data.get('is_verified', False)}

            Please provide a JSON response with:
            1. conversation_topics: Array of 3-5 specific conversation starters based on their bio
            2. interests: Array of identified interests/hobbies
            3. personality_traits: Array of 3-4 personality traits you can infer
            4. lifestyle_indicators: Array of lifestyle/life stage indicators
            5. fitness_relevance: How this person might relate to fitness coaching (1-10 scale)
            6. coaching_potential: Brief assessment of their potential as a fitness coaching client
            7. conversation_style: Suggested approach for conversations (casual, professional, motivational, etc.)

            Respond with ONLY a valid JSON object.
            """

            # Try each Gemini model
            models = [
                (GEMINI_MODEL_PRO, genai.GenerativeModel(GEMINI_MODEL_PRO)),
                (GEMINI_MODEL_FLASH, genai.GenerativeModel(GEMINI_MODEL_FLASH)),
                (GEMINI_MODEL_FLASH_STANDARD, genai.GenerativeModel(
                    GEMINI_MODEL_FLASH_STANDARD))
            ]

            for model_name, model in models:
                try:
                    logger.info(f"Trying Gemini model: {model_name}")
                    response = model.generate_content(prompt)

                    if response and response.text:
                        # Clean response
                        cleaned_response = response.text.strip()
                        if cleaned_response.startswith("```json"):
                            cleaned_response = cleaned_response[7:]
                        if cleaned_response.endswith("```"):
                            cleaned_response = cleaned_response[:-3]
                        cleaned_response = cleaned_response.strip()

                        # Parse JSON
                        analysis_data = json.loads(cleaned_response)

                        # Merge with bio_data
                        bio_data.update(analysis_data)
                        logger.info(
                            f"Successfully analyzed bio for {bio_data.get('ig_username')} with {model_name}")
                        return bio_data

                except google.api_core.exceptions.ResourceExhausted:
                    logger.warning(
                        f"Rate limit hit for {model_name}, trying next model...")
                    continue
                except json.JSONDecodeError as je:
                    logger.error(f"JSON parsing error with {model_name}: {je}")
                    continue
                except Exception as e:
                    logger.error(f"Error with {model_name}: {e}")
                    continue

            # If all models fail, return original bio_data
            logger.warning(
                f"All Gemini models failed for {bio_data.get('ig_username')}")
            return bio_data

        except Exception as e:
            logger.error(f"Error in Gemini analysis: {e}")
            return bio_data

    def get_new_users_needing_bios(self) -> Set[str]:
        """Get users who need bio data fetched"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Fixed query - use actual columns that exist in the database
            cursor.execute("""
                SELECT ig_username 
                FROM users 
                WHERE ig_username IS NOT NULL 
                AND ig_username != '' 
                AND ig_username NOT LIKE 'user_%'
                AND (
                    metrics_json IS NULL 
                    OR json_extract(metrics_json, '$.bio_text') IS NULL
                    OR json_extract(metrics_json, '$.bio_text') = ''
                )
                LIMIT 5
            """)

            usernames = {row[0] for row in cursor.fetchall()}
            conn.close()

            logger.info(f"Found {len(usernames)} users needing bio data")
            return usernames

        except Exception as e:
            logger.error(f"Error getting users needing bios: {e}")
            return set()

    def save_bio_to_database(self, bio_data: Dict[str, Any]) -> bool:
        """Save bio data to the database"""
        try:
            ig_username = bio_data.get("ig_username")
            if not ig_username:
                logger.error("No ig_username in bio_data")
                return False

            # Convert bio_data to metrics format
            metrics_data = {
                'bio_data': bio_data,
                'bio_fetch_timestamp': datetime.now().isoformat(),
                'bio_text': bio_data.get('bio_text', ''),
                'full_name': bio_data.get('full_name', ''),
                'conversation_topics': bio_data.get('conversation_topics', []),
                'interests': bio_data.get('interests', []),
                'personality_traits': bio_data.get('personality_traits', []),
                'lifestyle_indicators': bio_data.get('lifestyle_indicators', []),
                'fitness_relevance': bio_data.get('fitness_relevance', 0),
                'coaching_potential': bio_data.get('coaching_potential', ''),
                'conversation_style': bio_data.get('conversation_style', ''),
                'bio_analysis_source': 'background_bio_fetcher'
            }

            success = save_metrics_to_sqlite(ig_username, metrics_data)

            if success:
                logger.info(f"Successfully saved bio data for {ig_username}")
                return True
            else:
                logger.error(f"Failed to save bio data for {ig_username}")
                return False

        except Exception as e:
            logger.error(f"Error saving bio data: {e}")
            return False

    def process_user_bio(self, ig_username: str) -> bool:
        """Process a single user's bio"""
        try:
            logger.info(f"Processing bio for user: {ig_username}")

            # Skip if already processed recently
            if ig_username in self.processed_users:
                return True

            # Fetch bio from Instagram
            bio_data = self.get_instagram_bio(ig_username)
            if not bio_data:
                logger.error(f"Failed to fetch bio for {ig_username}")
                # Mark as processed to avoid retry
                self.processed_users.add(ig_username)
                return False

            # Analyze with Gemini
            analyzed_bio = self.analyze_bio_with_gemini(bio_data)
            if not analyzed_bio:
                logger.error(f"Failed to analyze bio for {ig_username}")
                return False

            # Save to database
            success = self.save_bio_to_database(analyzed_bio)
            if success:
                self.processed_users.add(ig_username)
                logger.info(
                    f"Successfully processed and saved bio for {ig_username}")
                return True
            else:
                logger.error(f"Failed to save bio for {ig_username}")
                return False

        except Exception as e:
            logger.error(f"Error processing bio for {ig_username}: {e}")
            return False

    def run_bio_fetch_cycle(self):
        """Run one cycle of bio fetching"""
        try:
            # Get users needing bios
            users_needing_bios = self.get_new_users_needing_bios()

            if not users_needing_bios:
                logger.info("No users need bio fetching")
                return

            # Setup browser if needed
            if not self.driver or not self.logged_in:
                if not self.setup_browser():
                    logger.error("Failed to setup browser")
                    return

                if not self.login_to_instagram():
                    logger.error("Failed to login to Instagram")
                    return

            # Process each user (limit to 5 per cycle to avoid rate limiting)
            processed_count = 0
            max_per_cycle = 5

            for ig_username in list(users_needing_bios)[:max_per_cycle]:
                try:
                    success = self.process_user_bio(ig_username)
                    processed_count += 1

                    # Add delay between users
                    if processed_count < max_per_cycle:
                        time.sleep(10)  # 10 second delay between users

                except Exception as e:
                    logger.error(f"Error processing {ig_username}: {e}")
                    continue

            logger.info(
                f"Completed bio fetch cycle - processed {processed_count} users")

        except Exception as e:
            logger.error(f"Error in bio fetch cycle: {e}")

    def start(self):
        """Start the background bio fetcher"""
        logger.info("Starting Background Bio Fetcher...")
        self.running = True

        try:
            while self.running:
                try:
                    self.run_bio_fetch_cycle()

                    # Wait before next cycle
                    logger.info(
                        f"Waiting {self.check_interval} seconds until next cycle...")
                    time.sleep(self.check_interval)

                except KeyboardInterrupt:
                    logger.info("Received keyboard interrupt, stopping...")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(30)  # Wait before retrying

        finally:
            self.stop()

    def stop(self):
        """Stop the background bio fetcher"""
        logger.info("Stopping Background Bio Fetcher...")
        self.running = False

        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except:
                pass

        logger.info("Background Bio Fetcher stopped")


def run_bio_fetcher_in_background():
    """Function to run bio fetcher in a separate thread"""
    fetcher = BackgroundBioFetcher()
    fetcher.start()


def start_background_bio_fetcher():
    """Start the bio fetcher in a background thread"""
    logger.info("Starting background bio fetcher thread...")
    thread = threading.Thread(
        target=run_bio_fetcher_in_background, daemon=True)
    thread.start()
    logger.info("Background bio fetcher thread started")
    return thread


if __name__ == "__main__":
    # Run directly for testing
    fetcher = BackgroundBioFetcher()
    try:
        fetcher.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        fetcher.stop()
