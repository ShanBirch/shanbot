from openai import OpenAI
import os
import base64
import time
import logging
import random
import json
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    WebDriverException,
    SessionNotCreatedException,
    InvalidSessionIdException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
import google.generativeai as genai
import re
# Import Google Sheets manager
try:
    from sheets_integration import GoogleSheetsManager
except ImportError:
    print("⚠️ Could not import sheets_integration module. Google Sheets functionality will not be available.")
    # Define a dummy class as fallback

    class GoogleSheetsManager:
        def __init__(self, *args, **kwargs):
            pass

        def update_sheet(self, *args, **kwargs):
            print("⚠️ Google Sheets functionality not available")
            return False


def print_step(message):
    """Print a step with clear formatting"""
    print("\n" + "=" * 50)
    print(message)
    print("=" * 50 + "\n")


def print_substep(message):
    """Print a substep with clear formatting"""
    print("-" * 30)
    print(message)
    print("-" * 30)


def sanitize_message(message):
    """Remove emojis, asterisks, and special characters from the message."""
    # First, remove any asterisks or markdown formatting symbols
    cleaned = message.replace('*', '').replace('_', '').replace('#', '')

    # Then remove emojis and other special characters
    cleaned = "".join(char for char in cleaned if ord(char) < 65536)

    return cleaned.strip()


def encode_image(image_path):
    """Encodes an image file to Base64 format."""
    print_substep(f"Encoding image: {image_path}")
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"❌ Error encoding image: {e}")
        return None


def random_sleep(min_seconds=1, max_seconds=3):
    """Sleep for a random amount of time to appear more human-like"""
    sleep_time = random.uniform(min_seconds, max_seconds)
    sleep(sleep_time)
    return sleep_time


class InstagramBot:
    def __init__(self):
        """Initialize the Instagram bot with configuration."""
        print_step("INITIALIZING BOT CONFIGURATION")

        # Setup logging
        logging.basicConfig(
            filename="instagram_bot_debug.log",
            level=logging.DEBUG,
            format="%(asctime)s:%(levelname)s:%(message)s",
        )

        # Configuration (replace with your credentials)
        self.username = "cocos_connected"
        self.password = "Shannonb3"
        self.gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

        # Using the same ChromeDriver path that's working in other scripts
        self.chromedriver_path = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"

        # Initialize Gemini client
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash')
        logging.info("Gemini API configured.")

        # Initialize Google Sheets manager
        sheets_service_account = "sheets-integration-service-acc@careful-cumulus-453500-k5.iam.gserviceaccount.com"
        self.sheets_manager = GoogleSheetsManager(sheets_service_account)

        # Set to track usernames that have already received DMs in this session
        # ALWAYS start with an empty set to avoid thinking we've commented when we haven't
        self.processed_usernames = set()
        print_step("STARTING WITH FRESH PROCESSED USERNAMES LIST")
        logging.info("Starting fresh with empty processed usernames list")

        # Maximum number of usernames to track before resetting
        self.max_tracked_usernames = 1000

        # Initialize WebDriver
        self.setup_driver()

    def setup_driver(self):
        """Setup and configure the Chrome WebDriver with anti-detection measures."""
        try:
            print_substep("Setting up Chrome WebDriver...")
            # Use the exact same approach as your working scripts
            service = Service(executable_path=self.chromedriver_path)
            chrome_options = Options()

            # Basic settings
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-extensions")

            # Anti-detection measures - hide automation
            chrome_options.add_argument(
                "--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option(
                "excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option(
                "useAutomationExtension", False)

            # Add user agent to prevent bot detection - using a recent, common user agent
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.37 Safari/537.36")

            # Add incognito mode to prevent caching issues
            chrome_options.add_argument("--incognito")

            # Disable image loading to improve performance (optional)
            # chrome_options.add_argument("--blink-settings=imagesEnabled=false")

            # Initialize the driver
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)

            # Execute CDP commands to hide automation even further
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                """
            })

            print("ChromeDriver initialized successfully")
            random_sleep(1, 2)

        except WebDriverException as e:
            print(f"❌ Error initializing ChromeDriver: {e}")
            raise

    def get_first_non_live_story(self, max_retries=3):
        """Find the first non-live story in the tray with retry mechanism."""
        print_step("SCANNING FOR NON-LIVE STORY")

        for retry in range(max_retries):
            try:
                # If this is a retry, refresh the page
                if retry > 0:
                    print(
                        f"Retry attempt {retry + 1}/{max_retries} for finding stories...")
                    self.driver.refresh()
                    random_sleep(4, 6)

                # Multiple selectors for story elements
                story_selectors = [
                    "//div[contains(@class, '_aarf')]/div/div/div/div/div/div/div/div/div",
                    "//div[@role='button'][tabindex='0']//canvas",
                    "//div[@role='button']/div/span//img[contains(@class, 'x') and @draggable='false']/..",
                    "//div[contains(@role, 'button')]//img[contains(@draggable, 'false')]/..",
                    "//div[contains(@class, 'x6s0dn4')]//div[@role='button']",
                    "//div[contains(@role, 'presentation')]//canvas/.."
                ]

                for selector_idx, selector in enumerate(story_selectors):
                    try:
                        print(f"Trying story selector #{selector_idx + 1}...")
                        story_elements = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH, selector))
                        )

                        if len(story_elements) > 0:
                            print(
                                f"Found {len(story_elements)} story elements with selector #{selector_idx + 1}")

                            # Check each story
                            for idx, story in enumerate(story_elements, 1):
                                print(
                                    f"\nChecking story {idx}/{len(story_elements)}")

                                try:
                                    # Updated LIVE indicator selector
                                    live_indicators = story.find_elements(
                                        By.XPATH,
                                        ".//span[text()='LIVE' or contains(@class, 'LiveIndicator')]"
                                    )

                                    if not live_indicators:
                                        print("✅ Found non-live story!")
                                        return story
                                    else:
                                        print("⏭️ Skipping live story...")
                                except Exception as e:
                                    print(f"Error checking story {idx}: {e}")
                                    continue

                            # If we checked all stories but none were suitable, try the next selector
                            continue

                    except Exception as e:
                        print(f"Selector #{selector_idx + 1} failed: {e}")
                        continue

                # If we've tried all selectors and still haven't found a story
                print("❌ No stories found with standard selectors")

                # Direct approach - try clicking the first story element regardless of type
                try:
                    print("Attempting direct approach to find any story...")
                    first_story = None

                    # Try these direct selectors
                    direct_selectors = [
                        "//div[contains(@class, '_aarf')]/div/div/div/div/div[1]",
                        "//section[contains(@class, 'x78zum5')]//div[@role='button'][1]",
                        "//div[contains(@class, 'x1lliihq')]/div[1]",
                        "//div[contains(@class, 'x6s0dn4')]/div[1]//div[@role='button']"
                    ]

                    for direct_selector in direct_selectors:
                        try:
                            first_story = self.driver.find_element(
                                By.XPATH, direct_selector)
                            if first_story:
                                print("✅ Found story with direct selector")
                                return first_story
                        except:
                            continue

                    if not first_story and retry < max_retries - 1:
                        print("No stories found. Retrying...")
                        random_sleep(2, 4)
                        continue

                    return None

                except Exception as e:
                    print(f"Direct approach failed: {e}")
                    if retry < max_retries - 1:
                        continue
                    else:
                        return None

            except Exception as e:
                print(f"Error finding stories: {e}")
                if retry < max_retries - 1:
                    print(
                        f"Retrying story search (attempt {retry + 2}/{max_retries})...")
                    random_sleep(3, 5)
                else:
                    return None

        return None

    def verify_stories_remaining(self):
        """Verify if there are more stories to process."""
        try:
            # Updated selector for story container
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "section._aa64")
                )
            )
            return True
        except:
            try:
                # Alternative selector
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div[role='dialog']")
                    )
                )
                return True
            except:
                return False

    def analyze_image_with_gpt(self, image_path, known_username=None):
        """Analyzes an image using Gemini to extract username, describe the content, and generate a response

        Args:
            image_path: Path to the screenshot image
            known_username: Username if already extracted from HTML (optional)
        """
        print_step("ANALYZING IMAGE WITH GEMINI")
        try:
            # Prepare the image for Gemini
            print_substep("Preparing image for Gemini...")

            # Load the image file for Gemini
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Create a Gemini image part - fixing the format
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_data
            }

            if not image_data:
                return None

            print_substep("Sending request to Gemini...")

            # Adjust the prompt based on whether we already have the username
            if known_username:
                system_prompt = f"""You are analyzing an Instagram story screenshot posted by {known_username}. I need two pieces of information:

                1. DESCRIPTION: Briefly describe what is happening in the MAIN story in the image in 2-3 sentences. Be specific about visible content. NOTE: The screenshot may include other stories in the background or UI elements - focus ONLY on the main central story being viewed.

                2. COMMENT: Create a friendly, casual comment in Shannon's style (Male Australian Personal Trainer) to respond to this story:
                   - Keep it VERY short (5-10 words only)
                   - Use casual Aussie slang
                   - For gym/fitness content ONLY: Use fitness motivation language
                   - For NON-fitness content: Comment specifically about what's in the image without mentioning fitness/gym
                   - DO NOT use any asterisks or special formatting characters
                   - Emojis are allowed and encouraged
                   - ONLY comment on the main story being viewed, not other UI elements or stories visible in the screenshot

                Respond in this EXACT format:
                DESCRIPTION: [brief description of main story content]
                COMMENT: [short friendly comment]
                """
                analysis_instruction = f"Analyze this Instagram story screenshot from {known_username} according to my instructions above, providing DESCRIPTION and COMMENT sections."
            else:
                # Even if we don't have a known username, we'll get it from HTML later, so just ask for description and comment
                system_prompt = """You are analyzing an Instagram story screenshot. I need two pieces of information:

                1. DESCRIPTION: Briefly describe what is happening in the MAIN story in the image in 2-3 sentences. Be specific about visible content. NOTE: The screenshot may include other stories in the background or UI elements - focus ONLY on the main central story being viewed.

                2. COMMENT: Create a friendly, casual comment in Shannon's style (Male Australian Personal Trainer) to respond to this story:
                   - Keep it VERY short (5-10 words only)
                   - Use casual Aussie slang
                   - For gym/fitness content ONLY: Use fitness motivation language
                   - For NON-fitness content: Comment specifically about what's in the image without mentioning fitness/gym
                   - DO NOT use any asterisks or special formatting characters
                   - Emojis are allowed and encouraged
                   - ONLY comment on the main story being viewed, not other UI elements or stories visible in the screenshot

                Respond in this EXACT format:
                DESCRIPTION: [brief description of main story content]
                COMMENT: [short friendly comment]
                """
                analysis_instruction = "Analyze this Instagram story screenshot according to my instructions above, providing DESCRIPTION and COMMENT sections."

            # Combine prompt and image for Gemini - fixing the format
            try:
                # Add retry logic for Gemini API
                max_api_retries = 3
                api_retry_count = 0
                api_success = False

                while api_retry_count < max_api_retries and not api_success:
                    try:
                        print(
                            f"Gemini API attempt {api_retry_count + 1}/{max_api_retries}...")

                        # Increase timeout for Gemini API call
                        response = self.model.generate_content(
                            contents=[
                                {"text": system_prompt},
                                {"text": analysis_instruction},
                                {"inline_data": image_part}
                            ],
                            generation_config=genai.GenerationConfig(
                                max_output_tokens=500,
                                temperature=0.6
                            )
                        )

                        # Check if response has valid content
                        if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                            # Valid response with content
                            analysis = response.text.strip()
                            print("\n--- Gemini Analysis ---")
                            print(analysis)
                            api_success = True
                        else:
                            # Empty response, retry if possible
                            print(
                                f"⚠️ Gemini returned empty response on attempt {api_retry_count + 1}")
                            api_retry_count += 1
                            if api_retry_count < max_api_retries:
                                print(
                                    f"Waiting before retry {api_retry_count + 1}...")
                                random_sleep(3, 5)  # Wait between retries
                            else:
                                print(
                                    "⚠️ All Gemini API retries failed, using fallback values")
                                return {
                                    "username": known_username or "Unknown",
                                    "description": "Image content unavailable",
                                    "comment": "Love it!"
                                }
                    except Exception as retry_error:
                        print(
                            f"⚠️ Gemini API error on attempt {api_retry_count + 1}: {retry_error}")
                        api_retry_count += 1
                        if api_retry_count < max_api_retries:
                            print(
                                f"Waiting before retry {api_retry_count + 1}...")
                            random_sleep(3, 5)  # Wait between retries
                        else:
                            print(
                                "⚠️ All Gemini API retries failed, using fallback values")
                            return {
                                "username": known_username or "Unknown",
                                "description": "Error analyzing image",
                                "comment": "Looking good!"
                            }
            except Exception as api_error:
                print(f"⚠️ Gemini API error: {api_error}")
                return {
                    "username": known_username or "Unknown",
                    "description": "Error analyzing image",
                    "comment": "Looking good!"
                }

            # Parse the response to extract the parts
            try:
                # Initialize variables before parsing to avoid reference errors
                instagram_username = known_username or "Unknown"  # We'll use the one from HTML
                image_description = None
                comment = None

                # Check if response is in JSON format (starts with curly brace or has ```json)
                if '{' in analysis and ('"DESCRIPTION"' in analysis.upper() or '"description"' in analysis or '"COMMENT"' in analysis.upper() or '"comment"' in analysis):
                    print("Detected JSON response, parsing as JSON...")

                    # Extract the JSON part from the response if it's wrapped in code blocks
                    if '```json' in analysis.lower():
                        json_text = analysis.split(
                            '```json')[1].split('```')[0].strip()
                    elif '```' in analysis:
                        json_text = analysis.split(
                            '```')[1].split('```')[0].strip()
                    else:
                        # If not wrapped in code blocks, just use the entire text
                        json_text = analysis

                    # Clean up any non-JSON content
                    start_idx = json_text.find('{')
                    end_idx = json_text.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_text = json_text[start_idx:end_idx]

                    # Parse JSON
                    import json
                    try:
                        json_data = json.loads(json_text)
                        print("Successfully parsed JSON data:", json_data)

                        # Extract data from JSON (handle different possible key formats)
                        # We're not looking for USERNAME anymore since we get it from HTML

                        # Check for DESCRIPTION keys (uppercase or lowercase)
                        for desc_key in ['DESCRIPTION', 'description', 'Description']:
                            if desc_key in json_data:
                                image_description = json_data.get(
                                    desc_key, "Image content unavailable")
                                break

                        # Check for COMMENT keys (uppercase or lowercase)
                        for comment_key in ['COMMENT', 'comment', 'Comment']:
                            if comment_key in json_data:
                                comment = json_data.get(
                                    comment_key, "Love it!")
                                break

                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON: {e}")
                        print(f"Attempted to parse: {json_text}")
                        # Fall back to regular text parsing below
                else:
                    # Traditional line-by-line parsing for non-JSON responses
                    print("Using traditional line-by-line parsing")
                    lines = analysis.split('\n')
                    for i, line in enumerate(lines):
                        line_upper = line.upper()
                        # Don't look for USERNAME anymore
                        if "DESCRIPTION:" in line_upper:
                            # Collect description (might span multiple lines)
                            image_description = line.replace(
                                "DESCRIPTION:", "").replace("Description:", "").strip()
                            j = i + 1
                            while j < len(lines) and not (lines[j].upper().startswith("COMMENT:")):
                                image_description += " " + lines[j].strip()
                                j += 1
                        elif "COMMENT:" in line_upper:
                            comment = line.replace("COMMENT:", "").replace(
                                "Comment:", "").strip()
            except Exception as parse_error:
                print(f"Error parsing Gemini response: {parse_error}")
                # Continue with fallback values below

            # If we couldn't parse properly, provide fallbacks
            if not image_description:
                image_description = "Could not analyze image content"
            if not comment:
                comment = "Love it!"

            print("\n--- Extracted Information ---")
            print(f"Instagram Username: {instagram_username}")
            print(f"Image Description: {image_description}")
            print(f"Original Comment: {comment}")
            print(f"Sanitized Comment: {sanitize_message(comment)}")

            # Return all three components
            return {
                "username": instagram_username,
                "description": image_description,
                "comment": comment
            }

        except Exception as e:
            print(f"❌ Error analyzing image with Gemini: {e}")
            # Return default values in case of error
            return {
                "username": known_username or "Unknown",
                "description": "Error analyzing image",
                "comment": "Love it!"  # Fallback response
            }

    def login(self, max_retries=3):
        """Logs into Instagram with retry mechanism."""
        print_step("LOGGING INTO INSTAGRAM")

        for retry in range(max_retries):
            try:
                print_substep(f"Login attempt {retry + 1}/{max_retries}...")
                print_substep("Opening Instagram...")

                # Clear cookies from previous attempts if retrying
                if retry > 0:
                    self.driver.delete_all_cookies()

                self.driver.get("https://www.instagram.com")
                # Add longer wait to load page completely with random time
                random_sleep(4, 6)

                # First check if we're already logged in (for retry attempts)
                try:
                    # Look for elements that would indicate we're logged in
                    already_logged_in = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//svg[@aria-label='Home']")
                        )
                    )
                    print("✔️ Already logged in!")
                    return True
                except:
                    print("Not logged in yet, proceeding with login...")

                print_substep("Waiting for login form...")
                try:
                    # First attempt with original selector
                    username_input = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.NAME, "username"))
                    )
                except:
                    try:
                        # Alternative approach if the above fails
                        print("Trying alternative login form selector...")
                        username_input = WebDriverWait(self.driver, 20).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "input[aria-label='Phone number, username, or email']"))
                        )
                    except:
                        if retry < max_retries - 1:
                            print("Login form not found. Refreshing and retrying...")
                            random_sleep(2, 4)
                            continue
                        else:
                            raise Exception(
                                "Login form not found after retries")

                # Human-like delay before typing
                random_sleep(0.5, 1.5)

                print_substep("Entering credentials...")
                username_input.clear()
                # Type like a human with random delays
                for char in self.username:
                    username_input.send_keys(char)
                    sleep(random.uniform(0.05, 0.2))

                try:
                    password_input = self.driver.find_element(
                        By.NAME, "password")
                except:
                    # Alternative password field selector
                    password_input = self.driver.find_element(
                        By.CSS_SELECTOR, "input[aria-label='Password']")

                # Human-like delay before typing password
                random_sleep(0.5, 1.5)

                password_input.clear()
                # Type like a human with random delays
                for char in self.password:
                    password_input.send_keys(char)
                    sleep(random.uniform(0.05, 0.2))

                # Pause briefly before clicking login
                random_sleep(0.8, 2)

                print_substep("Clicking login button...")

                # Find login button using multiple selectors
                login_button = None
                selectors = [
                    "//button[@type='submit']",
                    "//div[contains(text(), 'Log in')]/parent::button",
                    "//button[contains(., 'Log in')]"
                ]

                for selector in selectors:
                    try:
                        login_button = self.driver.find_element(
                            By.XPATH, selector)
                        print(
                            f"✔️ Found login button with selector: {selector}")
                        break
                    except:
                        continue

                if not login_button:
                    raise Exception(
                        "Could not find login button with any selector")

                # Add human-like pause before clicking
                random_sleep(0.5, 1.5)
                login_button.click()

                # Longer wait after login with random time
                random_sleep(6, 9)

                # Handle dialogs with updated selectors
                self._handle_dialog("Save Login Info")
                self._handle_dialog("Turn on Notifications")

                # Additional check for successful login with multiple selectors
                login_success = False
                login_indicators = [
                    "//span[contains(text(), 'Search')]",
                    "//svg[@aria-label='Home']",
                    "//a[@href='/explore/']",
                    "//div[@role='button' and @tabindex='0']//img[@data-testid='user-avatar']"
                ]

                for indicator in login_indicators:
                    try:
                        WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located(
                                (By.XPATH, indicator))
                        )
                        login_success = True
                        break
                    except:
                        continue

                if login_success:
                    print("✔️ Successfully logged into Instagram")
                    # Pause to fully load the page
                    random_sleep(3, 5)
                    return True
                else:
                    print("⚠️ Login status uncertain, checking home navigation...")
                    # Try navigating home as a test
                    try:
                        if self.navigate_home():
                            print("✔️ Navigation successful! Login confirmed.")
                            return True
                    except:
                        if retry < max_retries - 1:
                            print("Login likely failed. Retrying...")
                            continue
                        else:
                            print("⚠️ Login uncertain, attempting to continue...")
                            return True  # Try to continue anyway

                    # If we reached here and it's not the last retry, try again
                    if retry < max_retries - 1:
                        print(
                            f"Login attempt {retry + 1} unsuccessful. Retrying...")
                        random_sleep(3, 5)
                        continue
                    else:
                        print("⚠️ Login uncertain, attempting to continue...")
                        return True  # Try to continue anyway

            except (WebDriverException, InvalidSessionIdException) as e:
                if "session deleted" in str(e) or "invalid session id" in str(e):
                    print(f"❌ Browser closed unexpectedly: {e}")
                    if retry < max_retries - 1:
                        print("Reinitializing driver and retrying...")
                        try:
                            self.setup_driver()
                            random_sleep(2, 4)
                            continue
                        except Exception as setup_error:
                            print(
                                f"❌ Failed to reinitialize driver: {setup_error}")
                            raise
                    else:
                        raise
                else:
                    print(f"❌ Login error: {e}")
                    if retry < max_retries - 1:
                        random_sleep(3, 5)
                        continue
                    else:
                        # Take screenshot of login failure for debugging
                        try:
                            self.driver.save_screenshot("login_error.png")
                            print(
                                "Screenshot of login error saved as 'login_error.png'")
                        except:
                            pass
                        raise

        # If we've exhausted all retries
        return False

    def _handle_dialog(self, dialog_type):
        """Handle common Instagram dialogs."""
        try:
            # Try multiple selectors for the "Not Now" button
            selectors = [
                "//button[contains(text(), 'Not Now')]",
                "//button[text()='Not now']",
                "//button[contains(text(), 'Not now')]",
                "//button[contains(@class, '_a9_1')]",
                "//button[contains(@class, 'yWX7d')]",
                "//button[contains(text(), 'Maybe Later')]"
            ]

            for selector in selectors:
                try:
                    not_now_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    # Random pause before clicking
                    random_sleep(0.5, 1.5)
                    not_now_btn.click()
                    print(f"✔️ Dismissed '{dialog_type}' dialog")
                    random_sleep(1, 2)
                    return
                except:
                    continue

            print(f"No '{dialog_type}' dialog found or could not be closed")
        except TimeoutException:
            print(f"No '{dialog_type}' dialog found")

    def navigate_home(self, max_retries=3):
        """Navigates to Instagram home page with retry mechanism."""
        print_step("NAVIGATING TO HOME PAGE")

        for retry in range(max_retries):
            try:
                print_substep(
                    f"Navigation attempt {retry + 1}/{max_retries}...")
                print_substep("Looking for home button...")

                # Multiple selectors for the home button
                home_selectors = [
                    "//a//*[name()='svg' and @aria-label='Home']/ancestor::a",
                    "//a[@href='/']",
                    "//a[contains(@href, '/')]//svg[contains(@aria-label, 'Home')]/..",
                    "//span[text()='Home']/ancestor::a",
                    "//a[contains(@class, 'x1i10hfl') and contains(@href, '/')]",
                    "//nav//a[contains(@role, 'link')]"
                ]

                for selector in home_selectors:
                    try:
                        home_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        # Random pause before clicking
                        random_sleep(0.5, 1.5)
                        home_button.click()
                        print("✔️ Successfully clicked home button")
                        random_sleep(3, 5)
                        return True
                    except:
                        continue

                # If all selectors fail, try navigating directly to homepage
                print(
                    "⚠️ Could not find home button, navigating directly to homepage...")
                self.driver.get("https://www.instagram.com/")
                random_sleep(3, 5)
                print("✔️ Navigated directly to homepage")
                return True

            except Exception as e:
                print(f"❌ Navigation error: {e}")

                # Check if the session is invalid or browser closed
                if "invalid session id" in str(e) or "session deleted" in str(e) or "no such window" in str(e):
                    if retry < max_retries - 1:
                        print("Browser closed unexpectedly. Reinitializing...")
                        try:
                            self.setup_driver()
                            # Try to log in again
                            if self.login():
                                print("✔️ Successfully reinitialized and logged in")
                                continue
                            else:
                                print("❌ Failed to login after reinitialization")
                                return False
                        except Exception as setup_error:
                            print(
                                f"❌ Failed to reinitialize driver: {setup_error}")
                            return False
                    else:
                        return False

                # For other errors, just retry
                if retry < max_retries - 1:
                    print(
                        f"Retrying navigation (attempt {retry + 2}/{max_retries})...")
                    random_sleep(2, 4)
                else:
                    return False

        return False

    def get_total_stories(self):
        """Gets the total number of available stories."""
        try:
            # Try multiple selectors for story elements
            selectors = [
                "//div[@role='presentation']//canvas/ancestor::div[@role='button']",
                "//div[contains(@class, '_aarf')]//div[@role='button']",
                "//div[contains(@class, 'x1qjc9v5') and @role='button']"
            ]

            for selector in selectors:
                try:
                    story_elements = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, selector))
                    )
                    if len(story_elements) > 0:
                        return len(story_elements)
                except:
                    continue

            return 0
        except Exception as e:
            print(f"❌ Error counting stories: {e}")
            return 0

    def is_story_paused(self):
        """Check if the story is currently paused"""
        try:
            # Multiple selectors for pause overlay
            pause_selectors = [
                "//div[contains(@class, 'x1lliihq') and contains(@class, 'x1n2onr6')]",
                "//div[contains(@class, '_ac0k')]//div[contains(@class, 'x1i10hfl')]",
                "//div[@role='dialog']//div[contains(@class, 'x1i10hfl')]"
            ]

            for selector in pause_selectors:
                try:
                    WebDriverWait(self.driver, 1).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    return True  # Overlay is present, story is paused
                except:
                    continue

            return False  # No overlay found, story is likely playing
        except TimeoutException:
            return False  # Overlay is not present, story is playing

    def extract_instagram_username(self):
        """Extracts the Instagram username directly from the HTML element in the story."""
        try:
            last_extracted_username = getattr(
                self, '_last_extracted_username', None)

            # Save and log the current URL for debugging
            current_url = self.driver.current_url
            print(f"Extracting username from story URL: {current_url}")

            # APPROACH 1: Try direct extraction from HTML elements
            selectors = [
                "//div[contains(@class, 'x1i10hfl')]//a[starts-with(@href, '/') and not(contains(@href, 'direct'))]",
                "//header//a[starts-with(@href, '/')]",
                "//div[contains(@class, 'x9f619')]//a",
                "//div[contains(@class, 'x3nfvp2')]//span",
                "//div[contains(@aria-labelledby, 'story')]//a"
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            # Try to get username from href attribute
                            href = element.get_attribute('href')
                            if href and '/' in href:
                                username_candidate = href.strip(
                                    '/').split('/')[-1]
                                # Validate username format (3-30 chars, alphanumeric, dots, underscores)
                                if re.match(r'^[a-zA-Z0-9._]{3,30}$', username_candidate):
                                    print(
                                        f"✅ Extracted username from element href: {username_candidate}")
                                    self._last_extracted_username = username_candidate
                                    return username_candidate

                            # Try to get text directly from element
                            text = element.text.strip()
                            if text and re.match(r'^[a-zA-Z0-9._]{3,30}$', text):
                                print(
                                    f"✅ Extracted username from element text: {text}")
                                self._last_extracted_username = text
                                return text
                        except Exception as element_error:
                            print(
                                f"Error extracting from element: {element_error}")
                            continue
                except Exception as selector_error:
                    print(f"Selector failed: {selector_error}")
                    continue

            # APPROACH 2: Story URL Parsing - Instagram URLs may contain username
            try:
                if 'instagram.com/stories/' in current_url:
                    # Format: https://instagram.com/stories/username/12345678
                    parts = current_url.split('/')
                    if len(parts) > 5:
                        username_idx = parts.index('stories') + 1
                        if username_idx < len(parts):
                            username = parts[username_idx]
                            if re.match(r'^[a-zA-Z0-9._]{3,30}$', username):
                                print(
                                    f"✅ Extracted username from URL: {username}")
                                self._last_extracted_username = username
                                return username
            except Exception as url_error:
                print(f"URL parsing failed: {url_error}")

            # APPROACH 3: Page source regex extraction
            try:
                page_source = self.driver.page_source
                username_patterns = [
                    # Instagram patterns for usernames in the page source
                    r'\"username\":\"([a-zA-Z0-9._]{3,30})\"',
                    r'\"user\":{\"username\":\"([a-zA-Z0-9._]{3,30})\"',
                    r'@([a-zA-Z0-9._]{3,30})',
                    r'([a-zA-Z0-9._]{3,30})\'s story',
                    r'Stories · ([a-zA-Z0-9._]{3,30})',
                    r'instagram.com/([a-zA-Z0-9._]{3,30})(?:/|\")',
                ]

                extracted_usernames = []
                for pattern in username_patterns:
                    matches = re.findall(pattern, page_source)
                    if matches:
                        # Add all valid matches to our list
                        for match in matches:
                            if re.match(r'^[a-zA-Z0-9._]{3,30}$', match):
                                extracted_usernames.append(match)

                if extracted_usernames:
                    # Try to find the most common username in the matches
                    from collections import Counter
                    username_counter = Counter(extracted_usernames)
                    most_common = username_counter.most_common(1)[0][0]

                    print(f"✅ Extracted username using regex: {most_common}")
                    self._last_extracted_username = most_common
                    return most_common
            except Exception as regex_error:
                print(f"Regex extraction failed: {regex_error}")

            # APPROACH 4: Page title extraction
            try:
                page_title = self.driver.title
                if "Instagram" in page_title:
                    # Format might be "Instagram • username's story"
                    if "•" in page_title:
                        parts = page_title.split("•")
                        if len(parts) > 1:
                            title_part = parts[1].strip()
                            if "'s" in title_part:
                                username = title_part.split("'s")[0].strip()
                                if username and re.match(r'^[a-zA-Z0-9._]{3,30}$', username):
                                    print(
                                        f"✅ Extracted username from page title: {username}")
                                    self._last_extracted_username = username
                                    return username
            except Exception as title_error:
                print(f"Title extraction failed: {title_error}")

            # Use the last extracted username as fallback
            if last_extracted_username:
                print(
                    f"⚠️ Using previously extracted username as fallback: {last_extracted_username}")
                return last_extracted_username

            print("❌ Could not extract username with any method")
            return None

        except Exception as e:
            print(f"❌ Error in username extraction: {e}")
            # Use previously extracted username if available
            if last_extracted_username := getattr(self, '_last_extracted_username', None):
                print(
                    f"⚠️ Using previously extracted username after error: {last_extracted_username}")
                return last_extracted_username
            return None

    def find_and_click_next_story(self):
        """Use DOWN arrow key as primary navigation to reliably move to new stories."""
        try:
            print_substep(
                "Navigating to next story primarily using DOWN arrow key...")

            # Keep track of the current URL to verify we're actually moving to a new story
            current_url = self.driver.current_url

            # DOWN arrow key is the most reliable for avoiding loops in Instagram stories
            # It tends to move to different users' stories instead of just different stories from same user
            # Press DOWN arrow twice to ensure moving to a completely different story
            for _ in range(2):
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.ARROW_DOWN).perform()
                random_sleep(1.0, 1.5)  # Short pause between key presses

            # Longer pause after the final arrow key press to let the story load
            random_sleep(1.5, 2.5)

            # Check if URL changed to confirm navigation
            new_url = self.driver.current_url
            if new_url != current_url:
                print(f"✅ Successfully navigated to new story using DOWN arrow keys")
                return True

            # If DOWN arrow didn't work, try RIGHT arrow as fallback
            print("DOWN arrow didn't change story, trying RIGHT arrow twice...")

            # Press RIGHT arrow twice to skip further ahead
            for _ in range(2):
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.ARROW_RIGHT).perform()
                random_sleep(1.0, 1.5)

            # Check URL again
            new_url = self.driver.current_url
            if new_url != current_url:
                print(f"✅ Successfully navigated to new story using RIGHT arrow keys")
                return True

            # If keyboard navigation didn't work, try clicking the right side of the screen
            print("Keyboard navigation failed, trying click navigation...")
            try:
                # Click the far right side of the screen to skip potentially multiple stories
                actions = webdriver.ActionChains(self.driver)
                actions.move_to_element_with_offset(
                    self.driver.find_element(By.TAG_NAME, "body"),
                    # Click further to the right
                    int(self.driver.get_window_size()["width"] * 0.95),
                    int(self.driver.get_window_size()["height"] * 0.5)
                ).click().perform()

                # Try clicking twice to ensure moving past multiple stories
                random_sleep(1.0, 1.5)
                actions.click().perform()

                random_sleep(1.5, 2.5)

                # Check URL one more time
                new_url = self.driver.current_url
                if new_url != current_url:
                    print(
                        f"✅ Successfully navigated to new story by clicking right side")
                    return True
            except Exception as e:
                print(f"Error with click navigation: {e}")

            # If nothing worked, try escaping and restarting
            print("❌ All navigation methods failed, trying to exit story view...")
            try:
                # Press ESC to exit story view
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.ESCAPE).perform()
                random_sleep(2, 3)
                print("Exited story view")
                return False
            except:
                print("Failed to exit story view")

            return False

        except Exception as e:
            print(f"❌ Error in find_and_click_next_story: {e}")
            return False

    def process_single_story(self, story_number, total_stories):
        """Process a single story with the correct navigation sequence."""
        screenshot_path = None
        success = False

        try:
            # First, use the DOWN arrow key ONCE to navigate to next story
            print_substep("Navigating to next story using DOWN arrow key...")
            current_url = self.driver.current_url
            webdriver.ActionChains(self.driver).send_keys(
                Keys.ARROW_DOWN).perform()

            # Wait a short moment for the story to load
            random_sleep(0.8, 1.2)

            # IMMEDIATELY press space bar to pause
            print_substep("Pressing space bar to pause story...")
            webdriver.ActionChains(self.driver).send_keys(Keys.SPACE).perform()
            print("✔️ Story paused")

            # Additional wait to ensure story is fully paused
            random_sleep(0.5, 0.8)

            # Check if navigation worked by comparing URLs
            new_url = self.driver.current_url
            if new_url == current_url:
                print("⚠️ DOWN arrow didn't change story, trying RIGHT arrow...")
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.ARROW_RIGHT).perform()
                random_sleep(0.8, 1.2)
                # Press space bar again after RIGHT arrow
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.SPACE).perform()
                print("✔️ Story paused after RIGHT arrow")
                new_url = self.driver.current_url
                if new_url == current_url:
                    print("❌ Navigation failed completely")
                    return False

            print_step(f"PROCESSING STORY {story_number}/{total_stories}")

            # NOW extract username after navigation and pausing
            print_substep("Checking for username...")
            html_username = self.extract_instagram_username()
            if not html_username:
                print("❌ Could not extract username for this story, skipping...")
                return False

            print(f"Processing story for username: {html_username}")

            # Check if we've already processed this username
            if html_username in self.processed_usernames:
                print(
                    f"⚠️ Already processed {html_username} in this session. Skipping...")
                logging.info(f"Skipping {html_username} - already processed")
                print(
                    f"Current number of tracked usernames: {len(self.processed_usernames)}")
                return False

            # CHECK FOR REPLY BOX before taking screenshot
            print_substep("Checking for reply box...")
            reply_box_found = False
            reply_box = None

            # Try different selectors for reply box
            reply_box_selectors = [
                "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl')]",
                "//textarea[@placeholder='Reply...']",
                "//textarea[@placeholder='Send message']",
                "//textarea[contains(@aria-label, 'Reply')]",
                "//form//textarea",
                "//div[@role='textbox']"
            ]

            for selector in reply_box_selectors:
                try:
                    reply_box = self.driver.find_element(By.XPATH, selector)
                    reply_box_found = True
                    print(f"✔️ Reply box found with selector: {selector}")
                    break
                except:
                    continue

            if not reply_box_found:
                print("❌ No reply box found - skipping to next story")
                return False

            # Now that we have a reply box, take screenshot
            print_substep("Taking screenshot...")
            screenshot_path = f"story_{story_number}_{html_username}.png"
            self.driver.save_screenshot(screenshot_path)
            print("✔️ Screenshot captured")

            # Analyze with Gemini
            print_substep("Analyzing with Gemini...")
            analysis_result = self.analyze_image_with_gpt(
                screenshot_path, html_username)

            if analysis_result:
                print_substep("Processing analysis results...")

                # Extract components
                instagram_username = html_username  # Always use HTML username
                description = analysis_result['description']
                comment = analysis_result['comment']

                # Sanitize the comment for Instagram
                sanitized_comment = sanitize_message(comment)

                print(f"Instagram Username: {instagram_username}")
                print(f"Image Description: {description}")
                print(f"Original Comment: {comment}")
                print(f"Sanitized Comment: {sanitized_comment}")

                # Update Google Sheet with the information before sending comment
                print_substep(
                    "Updating Google Sheet before sending comment...")
                self.sheets_manager.update_sheet(
                    instagram_username, description, sanitized_comment)

                # Now click and focus the reply box
                print_substep("Clicking reply box...")
                try:
                    reply_box.click()
                except:
                    try:
                        self.driver.execute_script(
                            "arguments[0].click();", reply_box)
                    except:
                        print("❌ Failed to click reply box")
                        return False

                print("✔️ Reply box clicked")
                random_sleep(1, 2)

                # Use JavaScript to ensure element focus
                try:
                    self.driver.execute_script(
                        "arguments[0].focus();", reply_box)
                    print("✔️ Focused reply box with JavaScript")
                except Exception as focus_error:
                    print(
                        f"⚠️ Could not focus element with JavaScript: {focus_error}")

                # Type the message
                print_substep("Typing message...")
                try:
                    reply_box.clear()  # Clear any existing text
                except:
                    pass  # Some textareas don't support clear

                # Type like a human with random delays
                for char in sanitized_comment:
                    reply_box.send_keys(char)
                    # Human-like typing speed
                    sleep(random.uniform(0.02, 0.08))

                print("✔️ Message typed")
                random_sleep(0.5, 1)

                # Send the message
                print_substep("Sending message...")
                if self.send_message(reply_box):
                    print("✔️ Message sent successfully")
                    # Add username to processed set after successful message
                    self.processed_usernames.add(html_username)
                    print(f"✔️ Added {html_username} to processed usernames")
                    logging.info(
                        f"Added {html_username} to processed usernames. Total count: {len(self.processed_usernames)}")
                    # Save updated set of processed usernames
                    self.save_processed_usernames()
                    success = True
                    random_sleep(1, 2)
                else:
                    print("❌ Failed to send message")
                    return False

            return success

        except InvalidSessionIdException:
            print("❌ Browser closed unexpectedly during story processing")
            raise

        except Exception as e:
            print(f"❌ Error processing story: {e}")
            return False

        finally:
            if screenshot_path and os.path.exists(screenshot_path):
                try:
                    os.remove(screenshot_path)
                except:
                    pass

        return success

    def send_message(self, reply_box):
        """Attempt to send message using multiple methods."""
        methods = [
            (
                lambda: webdriver.ActionChains(self.driver)
                .send_keys(Keys.ENTER)
                .perform(),
                "Enter key",
            ),
            (lambda: self._click_send_button(), "Send button"),
            (
                lambda: reply_box.send_keys(Keys.ENTER),
                "Enter key directly to element",
            ),
        ]

        for method, name in methods:
            try:
                print_substep(f"Trying {name}...")
                method()
                # Wait to confirm message was sent
                random_sleep(1, 2)
                print(f"✔️ Message sent via {name}")
                return True
            except Exception as e:
                print(f"{name} method failed: {e}")

        return False

    def _click_send_button(self):
        """Helper method to click the send button."""
        # Multiple selectors for send button
        send_button_selectors = [
            "//div[@role='button' and contains(@class, 'x1i10hfl') and contains(@class, 'xjbqb8w') and contains(text(), 'Send')]",
            "//button[contains(text(), 'Send')]",
            "//div[contains(text(), 'Send')]/parent::button",
            "//div[@role='button' and contains(text(), 'Send')]",
            "//button[contains(@type, 'submit')]",
            "//div[contains(@aria-label, 'Send')]",
            "//div[text()='Send' and @role='button']"
        ]

        for selector in send_button_selectors:
            try:
                send_button = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )

                # Try different click methods
                try:
                    send_button.click()
                except:
                    self.driver.execute_script(
                        "arguments[0].click();", send_button)
                return
            except:
                continue

        raise Exception("Could not find send button with any selector")

    def interact_with_stories(self):
        """Interacts with all available Instagram stories with improved error handling."""
        story_count = 0
        successful_comments = 0
        processing = True
        consecutive_failures = 0
        MAX_FAILURES = 5
        last_story_time = time.time()
        max_retries = 3

        # Maximum number of stories to process before restarting completely
        MAX_STORIES_BEFORE_RESTART = 50

        # Track URLs we've already seen to prevent loops
        seen_urls = set()
        # Track usernames we've seen in this session (separate from processed_usernames which tracks those who received DMs)
        seen_usernames = set()

        try:
            # Find first non-live story with retries
            print_step("FINDING FIRST NON-LIVE STORY")
            first_story = self.get_first_non_live_story(
                max_retries=max_retries)

            if not first_story:
                print("❌ No suitable stories found to process")
                # Try refreshing the page and attempt again
                print("Refreshing page and trying again...")
                self.driver.refresh()
                random_sleep(5, 7)
                first_story = self.get_first_non_live_story(
                    max_retries=max_retries)
                if not first_story:
                    print("❌ Still no suitable stories found after refresh")
                    return

            print_step("OPENING FIRST STORY")
            # Add human-like delay before clicking
            random_sleep(1, 2)

            try:
                # Try regular click first
                first_story.click()
            except:
                # If regular click fails, try JavaScript click
                try:
                    self.driver.execute_script(
                        "arguments[0].click();", first_story)
                except Exception as e:
                    print(f"❌ Failed to click on first story: {e}")
                    return

            # Reduced wait time to load story
            random_sleep(0.5, 1)

            # Immediately pause the story
            print_substep("Quickly pausing first story...")
            webdriver.ActionChains(self.driver).send_keys(Keys.SPACE).perform()
            print("✔️ First story paused")
            random_sleep(0.8, 1.5)

            # Add initial URL to seen_urls
            seen_urls.add(self.driver.current_url)

            # Process stories with improved error handling
            while processing:
                current_time = time.time()
                if current_time - last_story_time < 0.5:
                    sleep(0.5 - (current_time - last_story_time))
                last_story_time = current_time

                story_count += 1
                print_step(f"PROCESSING STORY {story_count}")

                # Check if we need to restart after hitting the max stories threshold
                if story_count >= MAX_STORIES_BEFORE_RESTART:
                    print(
                        f"⚠️ Reached maximum stories threshold ({MAX_STORIES_BEFORE_RESTART}), restarting from home feed")
                    # Exit story view
                    try:
                        webdriver.ActionChains(self.driver).send_keys(
                            Keys.ESCAPE).perform()
                        random_sleep(2, 3)
                    except:
                        pass

                    # Navigate home and break out of this loop
                    self.navigate_home()
                    print("Exited stories and returned to home feed for fresh start")
                    break

                # Check if we're in a loop by comparing URL
                current_url = self.driver.current_url
                if current_url in seen_urls and story_count > 1:
                    print(f"⚠️ Detected repeated URL: {current_url}")
                    print(
                        "Attempting to escape potential loop by using enhanced navigation...")

                    # Try DOWN arrow key twice to skip further
                    for _ in range(2):
                        webdriver.ActionChains(self.driver).send_keys(
                            Keys.ARROW_DOWN).perform()
                        random_sleep(1.0, 1.5)

                    # Check if we've moved to a new URL
                    new_url = self.driver.current_url
                    if new_url != current_url:
                        print("✅ Successfully navigated away from repeated story")
                        # Update the current URL after navigation
                        seen_urls.add(new_url)
                        # Pause the story
                        random_sleep(0.5, 1)
                        webdriver.ActionChains(self.driver).send_keys(
                            Keys.SPACE).perform()
                        random_sleep(0.8, 1.5)
                        continue
                    else:
                        # If we can't navigate away, we might be at the end of stories
                        print(
                            "⚠️ Could not navigate away from repeated URL - may be at end of stories")
                        consecutive_failures += 1

                        if consecutive_failures >= 3:
                            print(
                                "⚠️ Multiple failures navigating away from loops - ending story processing")
                            break

                        # Try to exit stories and restart from home
                        try:
                            webdriver.ActionChains(self.driver).send_keys(
                                Keys.ESCAPE).perform()
                            random_sleep(2, 3)
                            self.navigate_home()
                            print("Exited stories and returned to home feed")
                            break
                        except:
                            print("Failed to exit stories mode")
                            break
                else:
                    # Add URL to seen set if it's new
                    seen_urls.add(current_url)

                try:
                    # Extract username before processing to check if already seen
                    html_username = self.extract_instagram_username()
                    if html_username:
                        if html_username in seen_usernames:
                            print(
                                f"⚠️ Already seen a story from {html_username} this session")
                            print("Navigating to next story to avoid duplication...")

                            # Skip ahead using double DOWN arrow to avoid going in circles
                            for _ in range(2):
                                webdriver.ActionChains(self.driver).send_keys(
                                    Keys.ARROW_DOWN).perform()
                                random_sleep(1.0, 1.5)

                            new_url = self.driver.current_url
                            if new_url != current_url:
                                print(
                                    "✅ Successfully navigated to new story after detecting duplicate username")
                                # Pause the new story
                                random_sleep(0.5, 1)
                                webdriver.ActionChains(self.driver).send_keys(
                                    Keys.SPACE).perform()
                                random_sleep(0.8, 1.5)
                                continue
                            else:
                                # If navigation failed, we might be at the end
                                print(
                                    "⚠️ Navigation failed after duplicate - may be at end of stories")
                                consecutive_failures += 1
                                continue
                        else:
                            # Add this username to seen set
                            seen_usernames.add(html_username)

                    # Set total_stories to 0 since we don't know exact count
                    if self.process_single_story(story_count, 0):
                        successful_comments += 1
                        consecutive_failures = 0
                        print("✔️ Story processed successfully")
                    else:
                        consecutive_failures += 1
                        print(
                            f"⚠️ Story processing failed (Failure #{consecutive_failures})")

                    # Add random delay between stories to appear more human-like
                    random_sleep(1, 3)

                except InvalidSessionIdException as e:
                    print(f"❌ Browser closed during story processing: {e}")
                    break

                except Exception as e:
                    consecutive_failures += 1
                    print(f"❌ Error processing story {story_count}: {e}")

                    if consecutive_failures >= MAX_FAILURES:
                        print("❌ Too many consecutive failures - ending processing")
                        processing = False
                    else:
                        print("🔄 Attempting to continue...")
                        random_sleep(2, 4)

                print(
                    f"Progress: {story_count} stories processed, {successful_comments} successful comments")

                # Check if we've processed too many stories with no success
                if story_count > 30 and successful_comments == 0:
                    print(
                        "⚠️ Processed 30+ stories with no successful comments - ending session")
                    break

        except InvalidSessionIdException as e:
            print(f"❌ Browser closed during story interaction: {e}")

        except Exception as e:
            print(f"❌ Error in story interaction: {e}")

        finally:
            print_step("STORY INTERACTION SUMMARY")
            print(
                f"""
Stories Statistics:
Stories processed: {story_count}
Successful comments: {successful_comments}
Success rate: {(successful_comments/story_count)*100 if story_count > 0 else 0:.2f}%
"""
            )

    def cleanup(self):
        """Clean up resources and delete processed usernames file."""
        try:
            # Delete processed usernames file instead of saving it
            filename = "processed_usernames.json"
            if os.path.exists(filename):
                os.remove(filename)
                print_step("DELETED PROCESSED USERNAMES FILE")
                logging.info(
                    "Deleted processed usernames file to reset tracking for next run")

            self.driver.quit()
            print_step("BROWSER CLOSED")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            logging.error(f"Error during cleanup: {e}")

    def load_processed_usernames(self):
        """Load the set of processed usernames from a file if it exists."""
        filename = "processed_usernames.json"
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as file:
                    data = json.load(file)
                    if 'usernames' in data:
                        self.processed_usernames = set(data['usernames'])
                        print(
                            f"✅ Loaded {len(self.processed_usernames)} previously processed usernames")
                        logging.info(
                            f"Loaded {len(self.processed_usernames)} previously processed usernames")
        except Exception as e:
            print(f"⚠️ Error loading processed usernames: {e}")
            logging.error(f"Error loading processed usernames: {e}")
            # If there's an error, start with an empty set
            self.processed_usernames = set()

    def save_processed_usernames(self):
        """Save the set of processed usernames to a file."""
        filename = "processed_usernames.json"

        # Check if we've exceeded the maximum number of tracked usernames
        if len(self.processed_usernames) > self.max_tracked_usernames:
            print(
                f"⚠️ Tracked usernames exceeded limit of {self.max_tracked_usernames}. Clearing list.")
            logging.warning(
                f"Tracked usernames exceeded limit of {self.max_tracked_usernames}. Clearing list.")
            self.processed_usernames = set()
            # Don't save an empty set
            return

        try:
            data = {'usernames': list(self.processed_usernames)}
            with open(filename, 'w') as file:
                json.dump(data, file)
            print(
                f"✅ Saved {len(self.processed_usernames)} processed usernames")
            logging.info(
                f"Saved {len(self.processed_usernames)} processed usernames to {filename}")
        except Exception as e:
            print(f"⚠️ Error saving processed usernames: {e}")
            logging.error(f"Error saving processed usernames: {e}")


def main():
    bot = None
    max_retries = 3

    try:
        print_step("STARTING INSTAGRAM STORY BOT")

        for attempt in range(max_retries):
            try:
                print(
                    f"Attempt {attempt + 1}/{max_retries} to initialize and run bot")
                bot = InstagramBot()

                login_success = bot.login(max_retries=2)
                if not login_success:
                    print("❌ Failed to log in after multiple attempts")
                    if attempt < max_retries - 1:
                        print(
                            f"Retrying entire process (attempt {attempt + 2}/{max_retries})...")
                        if bot:
                            bot.cleanup()
                        bot = None
                        random_sleep(5, 10)
                        continue

                nav_success = bot.navigate_home(max_retries=2)
                if not nav_success:
                    print("❌ Failed to navigate home after multiple attempts")
                    if attempt < max_retries - 1:
                        print(
                            f"Retrying entire process (attempt {attempt + 2}/{max_retries})...")
                        if bot:
                            bot.cleanup()
                        bot = None
                        random_sleep(5, 10)
                        continue

                # If we made it here, we're logged in and at home page
                bot.interact_with_stories()
                print_step("BOT COMPLETED SUCCESSFULLY")
                break  # Exit retry loop if successful

            except InvalidSessionIdException as e:
                print(f"❌ Browser session was closed: {e}")
                if attempt < max_retries - 1:
                    print(
                        f"Retrying entire process (attempt {attempt + 2}/{max_retries})...")
                    if bot:
                        try:
                            bot.cleanup()
                        except:
                            pass
                    bot = None
                    random_sleep(5, 10)
                else:
                    print_step("EXCEEDED MAXIMUM RETRIES")

            except Exception as e:
                print(f"❌ Unexpected error during attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print(
                        f"Retrying entire process (attempt {attempt + 2}/{max_retries})...")
                    if bot:
                        try:
                            bot.cleanup()
                        except:
                            pass
                    bot = None
                    random_sleep(5, 10)
                else:
                    print_step(f"UNEXPECTED ERROR: {e}")

    except KeyboardInterrupt:
        print_step("BOT INTERRUPTED BY USER")
    except Exception as e:
        print_step(f"CRITICAL ERROR: {e}")
    finally:
        if bot:
            try:
                bot.cleanup()
            except Exception as cleanup_error:
                print(f"❌ Error during cleanup: {cleanup_error}")


if __name__ == "__main__":
    main()
