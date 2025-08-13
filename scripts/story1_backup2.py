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
        self.processed_usernames = set()
        # Load previously processed usernames from file if available
        self.load_processed_usernames()
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
            print(f"Comment: {comment}")

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
        """Extracts the Instagram username directly from the HTML element in the story.
        Uses multiple approaches, with prioritization and additional validation."""
        try:
            print_substep("Extracting Instagram username from HTML...")
            timestamp = int(time.time())
            last_extracted_username = getattr(
                self, '_last_extracted_username', None)

            # APPROACH 1: Get username from URL - most reliable method
            try:
                current_url = self.driver.current_url
                print(f"Current URL: {current_url}")

                if "/stories/" in current_url:
                    # URL format: https://www.instagram.com/stories/username/12345678901234567/
                    parts = current_url.split("/stories/")
                    if len(parts) > 1:
                        username_part = parts[1].split("/")[0]
                        if username_part and len(username_part) > 2 and not username_part.isdigit():
                            # Verify that username is different from last one
                            if last_extracted_username != username_part:
                                print(
                                    f"✅ Extracted NEW username from URL: {username_part}")
                                self._last_extracted_username = username_part
                                return username_part
                            else:
                                print(
                                    f"⚠️ Same username as last extraction: {username_part}, trying other methods to confirm")
                                # Continue with other methods rather than returning immediately
            except Exception as url_error:
                print(f"URL extraction failed: {url_error}")

            # Take a screenshot for debugging in case we can't find the username
            debug_ss_path = f"username_debug_{timestamp}.png"
            try:
                self.driver.save_screenshot(debug_ss_path)
                print(f"Debug screenshot saved: {debug_ss_path}")
            except Exception as ss_error:
                print(f"Could not save debug screenshot: {ss_error}")

            # APPROACH 2: Try multiple selectors for the username element, prioritizing more specific ones
            username_selectors = [
                # Direct username indicators - most reliable
                "//div[@role='presentation']//header//a[contains(@role, 'link')]",
                "//div[@role='dialog']//header//a",  # Dialog header username
                "//div[@role='presentation']//h2",  # Username header
                "//header//a[contains(@role, 'link')]",  # Header username link
                # Username buttons
                "//div[@role='button']//span[not(contains(text(), 'Follow'))][string-length(text()) > 2]",

                # Common username classes
                "//div[contains(@class, 'x1qjc9v5')]//a[contains(@role, 'link')]",
                "//span[contains(@class, 'x1lliihq') and contains(@class, 'x193iq5w')]",
                "//span[contains(@class, 'xuxw1ft')]",
                "//div[contains(@class, 'xt0psk2')]/a",
                "//header//div[contains(@class, 'x9f619')]//div[@role='button']",
                "//div[contains(@class, 'x9f619')]//div[contains(@class, 'x1i10hfl')]//span"
            ]

            # Keep track of candidates for validation
            username_candidates = []

            # First pass - collect all potential username candidates
            for selector in username_selectors:
                try:
                    username_elements = self.driver.find_elements(
                        By.XPATH, selector)

                    for element in username_elements:
                        # Get both text and aria-label which sometimes contains the username
                        username_text = element.text.strip()

                        if username_text:
                            # Remove @ if present
                            if username_text.startswith('@'):
                                username_text = username_text[1:]

                            # Basic validation - must be at least 2 chars and not just digits
                            if len(username_text) > 2 and not username_text.isdigit():
                                username_candidates.append(username_text)

                        # Try aria-label as backup
                        aria_label = element.get_attribute("aria-label")
                        if aria_label and "'" in aria_label:
                            username_from_aria = aria_label.split("'")[
                                0].strip()
                            if username_from_aria and len(username_from_aria) > 2:
                                username_candidates.append(username_from_aria)
                except Exception:
                    continue

            # Log all the candidates we found
            if username_candidates:
                print(
                    f"Found {len(username_candidates)} username candidates: {username_candidates}")

                # Validate and filter the candidates
                valid_usernames = []
                for candidate in username_candidates:
                    # Instagram usernames are alphanumeric with _ and . but no spaces
                    if (len(candidate) > 2 and len(candidate) <= 30 and
                        not candidate.isdigit() and
                        not candidate.lower() == "instagram" and
                        " " not in candidate and  # Usernames don't have spaces
                        not candidate.startswith('#') and  # Not a hashtag
                            re.match(r'^[a-zA-Z0-9._]+$', candidate)):  # Valid characters

                        valid_usernames.append(candidate)

                # If we have valid usernames, prioritize different ones from last extraction
                if valid_usernames:
                    print(f"Valid username candidates: {valid_usernames}")

                    # First, check if any username is different from the last extracted one
                    new_usernames = [
                        u for u in valid_usernames if u != last_extracted_username]
                    if new_usernames:
                        selected_username = new_usernames[0]
                        print(f"✅ Selected new username: {selected_username}")
                        self._last_extracted_username = selected_username
                        return selected_username

                    # If all candidates are the same as last username, confirm with URL or another method
                    if last_extracted_username in valid_usernames:
                        print(
                            f"All usernames match last extracted username: {last_extracted_username}")
                        return last_extracted_username

                    # Default to first valid username if we can't determine a new one
                    selected_username = valid_usernames[0]
                    print(
                        f"✅ Selected username from candidates: {selected_username}")
                    self._last_extracted_username = selected_username
                    return selected_username

            # APPROACH 3: Try regex on page source
            try:
                print("Attempting to extract username using regex on page source...")
                page_source = self.driver.page_source

                # Look for patterns like "username":"value" or @username or username's story
                username_patterns = [
                    # JSON pattern for username
                    r'"username":"([a-zA-Z0-9._]{3,30})"',
                    # Another JSON pattern
                    r'"user":{"username":"([a-zA-Z0-9._]{3,30})"',
                    r'@([a-zA-Z0-9._]{3,30})\s',  # @username pattern
                    # username's story pattern
                    r'([a-zA-Z0-9._]{3,30})\'s story',
                    # URL pattern
                    r'instagram.com/stories/([a-zA-Z0-9._]{3,30})/'
                ]

                regex_candidates = []
                for pattern in username_patterns:
                    matches = re.findall(pattern, page_source)
                    regex_candidates.extend(matches)

                if regex_candidates:
                    print(
                        f"Found {len(regex_candidates)} regex candidates: {regex_candidates}")

                    # Filter for valid usernames
                    valid_regex_usernames = []
                    for candidate in regex_candidates:
                        if (candidate and len(candidate) > 2 and not candidate.isdigit() and
                                not candidate.lower() == "instagram" and " " not in candidate):
                            valid_regex_usernames.append(candidate)

                    if valid_regex_usernames:
                        # Prioritize new usernames
                        new_regex_usernames = [
                            u for u in valid_regex_usernames if u != last_extracted_username]
                        if new_regex_usernames:
                            selected_username = new_regex_usernames[0]
                            print(
                                f"✅ Selected new username from regex: {selected_username}")
                            self._last_extracted_username = selected_username
                            return selected_username

                        # Otherwise use first valid
                        selected_username = valid_regex_usernames[0]
                        print(
                            f"✅ Selected username from regex: {selected_username}")
                        self._last_extracted_username = selected_username
                        return selected_username
            except Exception as regex_error:
                print(f"Regex extraction failed: {regex_error}")

            # APPROACH 4: Page title extraction - sometimes contains username
            try:
                page_title = self.driver.title
                if "Instagram" in page_title and "(" in page_title:
                    # Title format sometimes is "Instagram • username's story"
                    title_parts = page_title.split("•")
                    if len(title_parts) > 1:
                        username_part = title_parts[1].strip()
                        if "'s" in username_part:
                            username = username_part.split("'s")[0].strip()
                            if username and len(username) > 2:
                                print(
                                    f"✅ Extracted username from page title: {username}")
                                self._last_extracted_username = username
                                return username
            except Exception as title_error:
                print(f"Title extraction failed: {title_error}")

            # Try using previously extracted username as last resort
            if last_extracted_username:
                print(
                    f"⚠️ Using previously extracted username as fallback: {last_extracted_username}")
                return last_extracted_username

            print("❌ Could not find valid username with any method")
            return None

        except Exception as e:
            print(f"❌ Error extracting username: {e}")
            # Use previously extracted username if available
            if last_extracted_username := getattr(self, '_last_extracted_username', None):
                print(
                    f"⚠️ Using previously extracted username after error: {last_extracted_username}")
                return last_extracted_username
            return None

    def find_and_click_next_story(self):
        """Use mouse-based navigation to find and click on a different story in the story tray."""
        try:
            print_substep("Looking for next available story with mouse...")

            # Try to find story profile images in the story tray
            story_selectors = [
                "//div[@role='dialog']//div[contains(@class, '_abx4')]//div[@role='button']//img",
                "//div[contains(@class, 'xp4054t')]//img[@draggable='false']",
                "//div[contains(@class, 'x6s0dn4')]//span//img",
                "//div[@role='button']//canvas/.."
            ]

            story_elements = []
            for selector in story_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        story_elements = elements
                        print(
                            f"Found {len(elements)} story elements with selector: {selector}")
                        break
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue

            if not story_elements:
                print("❌ Could not find any story elements to click")
                return False

            # Get current story URL to avoid clicking the same one
            current_url = self.driver.current_url

            # Try clicking on each story element until we find one that works
            for i, element in enumerate(story_elements):
                try:
                    # Skip the first element as it might be the current story
                    if i == 0:
                        continue

                    print(
                        f"Attempting to click story element {i+1}/{len(story_elements)}")

                    # Scroll element into view if needed
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", element)
                    random_sleep(0.5, 1)

                    # Try direct click
                    try:
                        element.click()
                    except:
                        # If direct click fails, try JavaScript click
                        self.driver.execute_script(
                            "arguments[0].click();", element)

                    random_sleep(1, 2)

                    # Check if URL changed to confirm navigation
                    new_url = self.driver.current_url
                    if new_url != current_url:
                        print(
                            f"✅ Successfully navigated to new story - URL changed from {current_url} to {new_url}")
                        return True
                    else:
                        print("⚠️ URL didn't change, might not have navigated")
                except Exception as e:
                    print(f"Error clicking story element {i+1}: {e}")
                    continue

            print("❌ Failed to navigate to a new story by clicking story elements")
            return False

        except Exception as e:
            print(f"❌ Error in find_and_click_next_story: {e}")
            return False

    def process_single_story(self, story_number, total_stories):
        """Process a single story with proper pausing and clear step sequence."""
        screenshot_path = None
        MAX_REPLY_BOX_ATTEMPTS = 3
        success = False
        last_username = None  # Keep track of last processed username

        try:
            print_step(f"PROCESSING STORY {story_number}/{total_stories}")

            # Fast pause the new story
            print_substep("Pausing new story...")
            random_sleep(0.1, 0.2)
            webdriver.ActionChains(self.driver).send_keys(
                Keys.SPACE).perform()
            print("✔️ New story paused")
            random_sleep(0.8, 1.5)

            # Clear any previously cached data
            self.driver.execute_cdp_cmd("Network.clearBrowserCache", {})

            # Get new URL after navigation - this ensures we're looking at a new story
            current_url = self.driver.current_url
            print(f"Current story URL: {current_url}")

            # Extract Instagram username directly from HTML
            html_username = self.extract_instagram_username()

            if not html_username:
                print("❌ Could not extract username for this story, skipping...")
                # Navigate to next story
                for key in [Keys.ARROW_RIGHT, Keys.ARROW_DOWN]:
                    try:
                        webdriver.ActionChains(
                            self.driver).send_keys(key).perform()
                        random_sleep(0.5, 1)
                        break
                    except:
                        continue
                return False

            print(f"Processing story for username: {html_username}")

            # Check if we've already sent a DM to this username in this session
            if html_username in self.processed_usernames:
                print(
                    f"⚠️ Already sent a DM to {html_username} in this session. Skipping...")
                logging.info(
                    f"Skipping {html_username} - already processed in this or previous sessions")
                print(
                    f"Current number of tracked usernames: {len(self.processed_usernames)}")

                # Try multiple navigation methods to ensure we move past this story
                print_substep("Attempting to skip to next story...")

                # Method 1: Try mouse-based navigation to find and click the next available story
                if self.find_and_click_next_story():
                    print("✅ Successfully navigated to new story using mouse")
                    # Fast pause the new story
                    random_sleep(0.5, 1)
                    webdriver.ActionChains(self.driver).send_keys(
                        Keys.SPACE).perform()
                    print("✔️ New story paused")
                    random_sleep(0.8, 1.5)
                    return False

                # Method 2: Standard navigation with arrow keys (fallback)
                navigation_success = False
                for key in [Keys.ARROW_RIGHT, Keys.ARROW_DOWN]:
                    try:
                        webdriver.ActionChains(
                            self.driver).send_keys(key).perform()
                        print(f"✔️ Skipped to next story using {key.name}")
                        navigation_success = True
                        break
                    except:
                        continue

                # Method 3: If standard navigation failed, try clicking the right side of the screen
                if not navigation_success:
                    try:
                        print_substep(
                            "Trying to click right side of screen...")
                        actions = webdriver.ActionChains(self.driver)
                        actions.move_to_element_with_offset(
                            self.driver.find_element(By.TAG_NAME, "body"),
                            int(self.driver.get_window_size()["width"] * 0.9),
                            int(self.driver.get_window_size()["height"] * 0.5)
                        )

                        actions.click().perform()
                        print("✔️ Skipped to next story by clicking right side")
                        navigation_success = True
                        random_sleep(1, 2)
                    except Exception as e:
                        print(f"Click navigation failed: {e}")

                # Method 4: If still stuck, try skipping multiple stories at once
                if not navigation_success:
                    try:
                        print_substep(
                            "Trying to skip multiple stories at once...")
                        for _ in range(3):  # Try to skip 3 stories
                            try:
                                webdriver.ActionChains(self.driver).send_keys(
                                    Keys.ARROW_RIGHT).perform()
                                random_sleep(0.5, 1)
                            except:
                                pass
                        print("✔️ Attempted to skip multiple stories")
                        navigation_success = True
                    except:
                        print("❌ Failed to skip multiple stories")

                # Method 5: If all else fails, try to exit stories and start over
                if not navigation_success:
                    try:
                        print_substep(
                            "Exiting story view and returning to feed...")
                        webdriver.ActionChains(self.driver).send_keys(
                            Keys.ESCAPE).perform()
                        random_sleep(2, 3)
                        self.navigate_home()
                        print("✔️ Exited stories and returned to home feed")
                    except Exception as e:
                        print(f"Failed to exit stories: {e}")

                # Fast pause the new story if we successfully navigated
                if navigation_success:
                    try:
                        random_sleep(0.5, 1)
                        webdriver.ActionChains(self.driver).send_keys(
                            Keys.SPACE).perform()
                        print("✔️ New story paused")
                        random_sleep(0.8, 1.5)
                    except Exception as pause_error:
                        print(f"Failed to pause story: {pause_error}")

                return False

            # Check for reply box early to skip processing if not present
            # Multiple selectors for reply box
            reply_box_selectors = [
                "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl')]",
                "//textarea[@placeholder='Reply...']",
                "//textarea[@placeholder='Send message']",
                "//textarea[contains(@aria-label, 'Reply')]",
                "//form//textarea",
                "//div[@role='textbox']"
            ]

            reply_box_found = False
            reply_box = None
            for selector in reply_box_selectors:
                try:
                    reply_box = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    print(f"✔️ Reply box found with selector: {selector}")
                    reply_box_found = True
                    break
                except:
                    continue

            if not reply_box_found:
                print("❌ No reply box detected, skipping to next story.")
                # Try different navigation keys
                for key in [Keys.ARROW_RIGHT, Keys.ARROW_DOWN]:
                    try:
                        webdriver.ActionChains(
                            self.driver).send_keys(key).perform()
                        print(f"✔️ Navigated to next story using {key.name}")
                        random_sleep(0.5, 1)
                        break
                    except:
                        continue

                # Fast pause the new story
                random_sleep(0.1, 0.2)
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.SPACE).perform()
                print("✔️ New story paused")
                random_sleep(0.8, 1.5)
                return False

            # Now that we've confirmed there's a reply box, take the screenshot
            try:
                print_substep("Taking screenshot...")
                screenshot_path = f"story_{story_number}_{html_username}.png"
                self.driver.save_screenshot(screenshot_path)
                print("✔️ Screenshot captured")
            except Exception as e:
                print(f"❌ Error taking screenshot: {e}")
                return False

            print_substep("Analyzing with Gemini...")
            analysis_result = self.analyze_image_with_gpt(
                screenshot_path, html_username)

            if analysis_result:
                print_substep("Processing analysis results...")

                # Extract components, prioritizing HTML username if available
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

                reply_box_found = False
                for attempt in range(MAX_REPLY_BOX_ATTEMPTS):
                    print_substep(
                        f"Finding reply box (Attempt {attempt + 1}/{MAX_REPLY_BOX_ATTEMPTS})..."
                    )

                    try:
                        # Try different selectors for reply box
                        for selector in reply_box_selectors:
                            try:
                                reply_box = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located(
                                        (By.XPATH, selector))
                                )
                                reply_box_found = True
                                print(
                                    f"✔️ Reply box found with selector: {selector}")
                                break
                            except:
                                continue

                        if not reply_box_found:
                            raise Exception(
                                "Reply box not found with any selector")

                        print_substep("Clicking reply box...")
                        # Try different click methods
                        try:
                            reply_box.click()
                        except:
                            try:
                                self.driver.execute_script(
                                    "arguments[0].click();", reply_box)
                            except:
                                print("❌ Failed to click reply box")
                                raise

                        print("✔️ Reply box clicked")
                        # Increase waiting time after clicking reply box
                        random_sleep(2, 3)

                        # Use JavaScript to ensure element focus
                        try:
                            self.driver.execute_script(
                                "arguments[0].focus();", reply_box)
                            print("✔️ Focused reply box with JavaScript")
                        except Exception as focus_error:
                            print(
                                f"⚠️ Could not focus element with JavaScript: {focus_error}")

                        # Add additional wait for element to become fully interactive
                        try:
                            # Wait for element to be interactable (up to 5 seconds)
                            WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH, selector))
                            )
                            print("✔️ Reply box is now interactable")
                        except Exception as wait_error:
                            print(
                                f"⚠️ Wait for interactability timed out: {wait_error}")
                            # Continue anyway - some elements work even when not explicitly "clickable"

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

                        print_substep("Sending message...")
                        if self.send_message(reply_box):
                            print("✔️ Message sent successfully")
                            # Add username to processed set after successful message
                            self.processed_usernames.add(html_username)
                            print(
                                f"✔️ Added {html_username} to processed usernames")
                            logging.info(
                                f"Added {html_username} to processed usernames. Total count: {len(self.processed_usernames)}")
                            # Save updated set of processed usernames
                            self.save_processed_usernames()
                            success = True
                            # Add random delay after successful send
                            random_sleep(1, 2)
                            break
                        else:
                            print("❌ Failed to send message")

                    except Exception as e:
                        print(
                            f"⚠️ Reply box attempt {attempt + 1} failed: {str(e)}")
                        random_sleep(1, 1.5)
                        continue

                if not reply_box_found:
                    print(
                        "❌ No reply box found after all attempts - skipping to next story")

            print_substep("Moving to next story...")
            # Try both navigation methods
            navigation_success = False
            for key in [Keys.ARROW_RIGHT, Keys.ARROW_DOWN]:
                try:
                    webdriver.ActionChains(
                        self.driver).send_keys(key).perform()
                    print(f"✔️ Navigated to next story using {key.name}")
                    navigation_success = True
                    break
                except:
                    continue

            if not navigation_success:
                print("⚠️ Navigation to next story failed with keyboard shortcuts")
                # Try clicking the right side of the screen
                try:
                    actions = webdriver.ActionChains(self.driver)
                    actions.move_to_element_with_offset(self.driver.find_element(By.TAG_NAME, "body"),
                                                        int(self.driver.get_window_size()[
                                                            "width"] * 0.9),
                                                        int(self.driver.get_window_size()["height"] * 0.5))

                    actions.click().perform()
                    print("✔️ Navigated to next story by clicking right side")
                    navigation_success = True
                except:
                    print("⚠️ All navigation methods failed")

            # Wait for navigation to complete before proceeding to next story
            if navigation_success:
                random_sleep(1.5, 2.5)  # Give time for next story to load

            return success

        except InvalidSessionIdException:
            print("❌ Browser closed unexpectedly during story processing")
            raise

        except Exception as e:
            print(f"❌ Error processing story: {e}")
            try:
                # Try navigating with different keys
                for key in [Keys.ARROW_RIGHT, Keys.ARROW_DOWN]:
                    try:
                        webdriver.ActionChains(
                            self.driver).send_keys(key).perform()
                        print(
                            f"➡️ Moved to next story using {key.name} after error")
                        break
                    except:
                        continue

                # Fast pause the new story
                random_sleep(0.1, 0.2)
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.SPACE).perform()
                print("✔️ Next story paused after error")
            except:
                pass

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

            # Process stories with improved error handling
            while processing:
                current_time = time.time()
                if current_time - last_story_time < 0.5:
                    sleep(0.5 - (current_time - last_story_time))
                last_story_time = current_time

                story_count += 1
                print_step(f"PROCESSING STORY {story_count}")

                try:
                    # Set total_stories to 0 since we don't know exact count
                    if self.process_single_story(story_count, 0):
                        successful_comments += 1
                        consecutive_failures = 0
                        print("✔️ Story processed successfully")
                    else:
                        consecutive_failures += 1
                        print(
                            f"⚠️ Story processing failed (Failure #{consecutive_failures})"
                        )

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
                    f"Progress: {story_count} stories processed, {successful_comments} successful comments"
                )

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
