from openai import OpenAI
import os
import base64
import time
import logging
import random
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
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re


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
    """Remove emojis and special characters from the message."""
    return "".join(char for char in message if ord(char) < 65536)


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


class InstagramFeedBot:
    def __init__(self):
        """Initialize the Instagram bot for feed commenting."""
        print_step("INITIALIZING BOT CONFIGURATION")

        # Setup logging
        logging.basicConfig(
            filename="instagram_feed_bot_debug.log",
            level=logging.DEBUG,
            format="%(asctime)s:%(levelname)s:%(message)s",
        )

        # Configuration (replace with your credentials)
        self.username = "cocos_pt_studio"
        self.password = "Shannonb3"
        self.gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

        # Using the same ChromeDriver path that's working in other scripts
        self.chromedriver_path = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"

        # Initialize Gemini client
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        logging.info("Gemini API configured.")

        # Setup Google Sheets API
        self.sheets_api = None
        try:
            self.setup_sheets_api()
        except Exception as e:
            logging.error(f"Failed to set up Google Sheets API: {e}")
            print(f"❌ Failed to set up Google Sheets API: {e}")

        # Initialize the webdriver
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Set up the Selenium WebDriver."""
        print_substep("Setting up Chrome WebDriver...")

        try:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--mute-audio")

            # Create Chrome Service
            chrome_service = Service(executable_path=self.chromedriver_path)

            # Initialize the driver
            self.driver = webdriver.Chrome(
                service=chrome_service, options=chrome_options)

            # Set an implicit wait to help with element detection
            self.driver.implicitly_wait(5)
            logging.info("WebDriver initialized successfully.")
            print("✔️ WebDriver initialized successfully")

            return True

        except SessionNotCreatedException as e:
            logging.error(f"Failed to create session: {e}")
            print(f"❌ Chrome session creation failed: {e}")
            if "This version of ChromeDriver only supports Chrome version" in str(e):
                print("⚠️ Error indicates Chrome and ChromeDriver version mismatch.")
                print("Please update ChromeDriver to match your Chrome version.")
            return False

        except Exception as e:
            logging.error(f"Failed to initialize WebDriver: {e}")
            print(f"❌ Failed to initialize WebDriver: {e}")
            return False

    def login(self, max_retries=3):
        """Log into Instagram with retry mechanism."""
        print_step("LOGGING INTO INSTAGRAM")

        for retry in range(max_retries):
            try:
                print_substep(f"Login attempt {retry + 1}/{max_retries}...")
                print_substep("Opening Instagram...")
                self.driver.get("https://www.instagram.com")
                random_sleep(2, 3)

                # Instagram might show various cookie dialogs - try to handle them
                try:
                    cookie_button_selectors = [
                        "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]",
                        "//button[contains(text(), 'Accept All')]",
                        "//button[contains(@class, '_a9--') and contains(@class, '_a9_1')]",
                    ]

                    for selector in cookie_button_selectors:
                        try:
                            cookie_button = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH, selector))
                            )
                            cookie_button.click()
                            print("✔️ Accepted cookies")
                            random_sleep(1, 2)
                            break
                        except:
                            continue
                except:
                    print("No cookie dialog or could not accept")

                # Check if username field is visible
                username_field_selectors = [
                    "//input[@name='username']",
                    "//input[@aria-label='Phone number, username, or email']",
                    "//input[contains(@aria-label, 'username')]",
                ]

                username_field = None
                for selector in username_field_selectors:
                    try:
                        username_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        if username_field:
                            break
                    except:
                        continue

                if not username_field:
                    print("❌ Could not find username field")
                    if retry < max_retries - 1:
                        print("Refreshing page...")
                        self.driver.refresh()
                        random_sleep(2, 3)
                        continue
                    else:
                        return False

                # Clear fields before entering credentials
                username_field.clear()
                random_sleep(0.3, 0.7)
                username_field.send_keys(self.username)
                print("✔️ Username entered")
                random_sleep(0.5, 1)

                password_field_selectors = [
                    "//input[@name='password']",
                    "//input[@aria-label='Password']",
                    "//input[contains(@aria-label, 'password')]",
                ]

                password_field = None
                for selector in password_field_selectors:
                    try:
                        password_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        if password_field:
                            break
                    except:
                        continue

                if not password_field:
                    print("❌ Could not find password field")
                    if retry < max_retries - 1:
                        continue
                    else:
                        return False

                password_field.clear()
                random_sleep(0.3, 0.7)
                password_field.send_keys(self.password)
                print("✔️ Password entered")
                random_sleep(0.5, 1)

                # Login button selection
                login_button_selectors = [
                    "//button[@type='submit']",
                    "//div[text()='Log in']/ancestor::button",
                    "//button[.//div[contains(text(), 'Log')]]",
                ]

                login_button = None
                for selector in login_button_selectors:
                    try:
                        login_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        if login_button:
                            break
                    except:
                        continue

                if not login_button:
                    print("❌ Could not find login button")
                    if retry < max_retries - 1:
                        continue
                    else:
                        return False

                # Random sleep before clicking login to appear more human-like
                random_sleep(0.8, 1.5)
                login_button.click()
                print("✔️ Login button clicked")

                # Wait longer to ensure login process completes
                random_sleep(5, 7)

                # Check for successful login by looking for elements only visible when logged in
                logged_in_selectors = [
                    "//span[text()='Search']/ancestor::a",
                    "//a//*[name()='svg' and @aria-label='Home']/ancestor::a",
                    "//span[contains(text(), 'Profile')]/ancestor::a",
                    "//a[contains(@href, '/direct/inbox/')]",
                ]

                logged_in = False
                for selector in logged_in_selectors:
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located(
                                (By.XPATH, selector))
                        )
                        logged_in = True
                        break
                    except:
                        continue

                if logged_in:
                    print("✔️ Successfully logged into Instagram")

                    # Handle "Save Login Info" dialog
                    try:
                        save_login_selectors = [
                            "//button[text()='Not Now']",
                            "//button[contains(text(), 'Not Now')]",
                            "//button[contains(text(), 'Not now')]",
                        ]

                        for selector in save_login_selectors:
                            try:
                                not_now_button = WebDriverWait(self.driver, 3).until(
                                    EC.element_to_be_clickable(
                                        (By.XPATH, selector))
                                )
                                random_sleep(0.5, 1)
                                not_now_button.click()
                                print("✔️ Clicked 'Not Now' for saving login info")
                                random_sleep(1, 2)
                                break
                            except:
                                continue
                    except:
                        print(
                            "No 'Save Login Info' dialog detected or could not dismiss")

                    # Handle notifications dialog
                    try:
                        notification_selectors = [
                            "//button[text()='Not Now']",
                            "//button[contains(text(), 'Not Now')]",
                            "//button[contains(text(), 'Not now')]",
                        ]

                        for selector in notification_selectors:
                            try:
                                not_now_button = WebDriverWait(self.driver, 3).until(
                                    EC.element_to_be_clickable(
                                        (By.XPATH, selector))
                                )
                                random_sleep(0.5, 1)
                                not_now_button.click()
                                print("✔️ Clicked 'Not Now' for notifications")
                                break
                            except:
                                continue
                    except:
                        print("No notifications dialog detected or could not dismiss")

                    return True
                else:
                    print("❌ Login verification failed")
                    if retry < max_retries - 1:
                        print("Attempting login again...")
                        self.driver.refresh()
                        random_sleep(2, 3)
                        continue
                    else:
                        return False

            except Exception as e:
                print(f"❌ Login error: {e}")
                if retry < max_retries - 1:
                    print("Refreshing page and retrying...")
                    try:
                        self.driver.refresh()
                        random_sleep(2, 3)
                    except:
                        # If refresh fails, try to open Instagram again
                        try:
                            self.driver.get("https://www.instagram.com")
                            random_sleep(2, 3)
                        except:
                            pass
                else:
                    return False

        return False

    def navigate_to_feed(self):
        """Navigate to Instagram's main feed."""
        print_step("NAVIGATING TO FEED")

        try:
            # Try clicking the home button first
            home_selectors = [
                "//a//*[name()='svg' and @aria-label='Home']/ancestor::a",
                "//a[@href='/']",
                "//a[contains(@href, '/')]//svg[contains(@aria-label, 'Home')]/..",
                "//span[text()='Home']/ancestor::a",
            ]

            home_clicked = False
            for selector in home_selectors:
                try:
                    home_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    random_sleep(0.5, 1)
                    home_button.click()
                    print("✔️ Clicked home button")
                    home_clicked = True
                    random_sleep(2, 3)
                    break
                except:
                    continue

            # If clicking home button fails, navigate directly to Instagram
            if not home_clicked:
                print("Direct navigation to Instagram home...")
                self.driver.get("https://www.instagram.com/")
                random_sleep(3, 5)

            # Verify we're on the feed by checking for post elements
            posts_selectors = [
                "//article[contains(@role, 'presentation')]",
                "//div[@role='presentation']//article",
                "//article[contains(@class, 'x1iyjqo2')]"
            ]

            feed_loaded = False
            for selector in posts_selectors:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    feed_loaded = True
                    break
                except:
                    continue

            if feed_loaded:
                print("✔️ Feed loaded successfully")
                return True
            else:
                print("❌ Failed to verify feed is loaded")
                return False

        except Exception as e:
            print(f"❌ Error navigating to feed: {e}")
            return False

    def analyze_post_with_ai(self, image_path, username=None):
        """Generate an encouraging comment based on the post content."""
        print_substep("Analyzing post image with Gemini...")

        try:
            # Encode the image
            base64_image = encode_image(image_path)
            if not base64_image:
                return None, None

            # Create prompt based on whether we know the username
            if username:
                system_prompt = f"""You are analyzing an Instagram post by {username}. Generate a positive, encouraging comment that's:
1. Personalized to what's in the image
2. Supportive and uplifting
3. Natural sounding (like a real comment, not AI-generated)
4. Between 1-3 sentences maximum
5. Includes 1-2 relevant emojis
6. Is not excessively enthusiastic or over the top

IMPORTANT: DO NOT use generic phrases like "Great post!" or "Looking good!". 
The comment should be specific to what you see in the image.
"""
            else:
                system_prompt = """You are analyzing an Instagram post. Generate a positive, encouraging comment that's:
1. Personalized to what's in the image
2. Supportive and uplifting
3. Natural sounding (like a real comment, not AI-generated)
4. Between 1-3 sentences maximum
5. Includes 1-2 relevant emojis
6. Is not excessively enthusiastic or over the top

IMPORTANT: DO NOT use generic phrases like "Great post!" or "Looking good!". 
The comment should be specific to what you see in the image.
"""

            # Create the image part
            image_part = {
                'mime_type': 'image/jpeg',
                'data': base64_image
            }

            # Generate content with Gemini
            response = self.model.generate_content([
                system_prompt,
                image_part,
                "Generate an encouraging comment for this Instagram post:"
            ])

            # Extract the response text
            comment = response.text.strip()

            # Limit length of comment
            if len(comment) > 240:
                comment = comment[:240]

            print(f"✔️ Generated comment: {comment}")

            # Also capture a brief description for logging
            response = self.model.generate_content([
                "Describe this image in a single sentence:",
                image_part
            ])
            description = response.text.strip()
            print(f"✔️ Image description: {description}")

            return comment, description

        except Exception as e:
            print(f"❌ Error analyzing image: {e}")
            return None, None

    def scroll_feed(self, num_posts=10, comments_per_session=5):
        """Scroll through the Instagram feed and comment on posts."""
        print_step("SCROLLING INSTAGRAM FEED")

        posts_processed = 0
        comments_made = 0

        try:
            # Identify posts on the feed
            post_selectors = [
                "//article[contains(@role, 'presentation')]",
                "//div[@role='presentation']//article",
                "//article[contains(@class, 'x1iyjqo2')]"
            ]

            last_height = self.driver.execute_script(
                "return document.body.scrollHeight")

            while posts_processed < num_posts and comments_made < comments_per_session:
                # Find all visible posts
                posts = []
                for selector in post_selectors:
                    try:
                        found_posts = self.driver.find_elements(
                            By.XPATH, selector)
                        if found_posts:
                            posts = found_posts
                            break
                    except:
                        continue

                if not posts:
                    print("❌ No posts found in feed")
                    return posts_processed, comments_made

                # Process visible posts
                for post in posts:
                    # Skip if we've processed enough posts or made enough comments
                    if posts_processed >= num_posts or comments_made >= comments_per_session:
                        break

                    try:
                        # Scroll to post to make it fully visible
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
                        random_sleep(1, 2)

                        # Check if we've already processed this post (simple heuristic)
                        post_id = post.get_attribute("id") or post.get_attribute(
                            "data-id") or str(hash(post.text))

                        posts_processed += 1
                        print_step(
                            f"PROCESSING POST {posts_processed}/{num_posts}")

                        # Try to extract username
                        username = None
                        username_selectors = [
                            ".//a[contains(@href, '/')]",
                            ".//span[contains(@class, 'x1lliihq')]/a",
                            ".//div[contains(@class, 'x1ye3gou')]//a",
                            ".//div[contains(@class, 'x9f619')]//span//a"
                        ]

                        for selector in username_selectors:
                            try:
                                username_elem = post.find_element(
                                    By.XPATH, selector)
                                username = username_elem.text or username_elem.get_attribute(
                                    "href")
                                if username and '/' in username:
                                    username = username.split(
                                        '/')[-2] if username.endswith('/') else username.split('/')[-1]
                                break
                            except:
                                continue

                        if username:
                            print(f"✔️ Post by user: {username}")
                        else:
                            print("⚠️ Could not extract username")

                        # Take screenshot of post for analysis
                        screenshot_path = f"temp_post_{posts_processed}.jpg"
                        try:
                            post.screenshot(screenshot_path)
                            print(f"✔️ Captured screenshot: {screenshot_path}")

                            # Random chance of commenting (70%)
                            if random.random() < 0.7 and comments_made < comments_per_session:
                                # Find comment button
                                comment_button_selectors = [
                                    ".//span[@class='_aamw']/button",
                                    ".//span[contains(@class, 'xp7jhwk')]//div[@role='button']",
                                    ".//div[contains(@aria-label, 'Comment')]",
                                    ".//div[contains(@aria-label, 'Add a comment')]",
                                    ".//div[contains(@class, 'x78zum5') and @role='button']"
                                ]

                                comment_button = None
                                for selector in comment_button_selectors:
                                    try:
                                        comment_button = post.find_element(
                                            By.XPATH, selector)
                                        break
                                    except:
                                        continue

                                if comment_button:
                                    # Click comment button
                                    random_sleep(0.5, 1.5)
                                    try:
                                        comment_button.click()
                                    except:
                                        self.driver.execute_script(
                                            "arguments[0].click();", comment_button)

                                    print("✔️ Clicked comment button")
                                    random_sleep(1, 2)

                                    # Find comment input field
                                    comment_input_selectors = [
                                        "//textarea[@aria-label='Add a comment…']",
                                        "//textarea[@placeholder='Add a comment…']",
                                        "//form//textarea",
                                        "//div[@role='textbox']"
                                    ]

                                    comment_input = None
                                    for selector in comment_input_selectors:
                                        try:
                                            comment_input = WebDriverWait(self.driver, 5).until(
                                                EC.element_to_be_clickable(
                                                    (By.XPATH, selector))
                                            )
                                            break
                                        except:
                                            continue

                                    if comment_input:
                                        # Generate comment using AI
                                        comment_text, description = self.analyze_post_with_ai(
                                            screenshot_path, username)

                                        if comment_text:
                                            # Enter comment text
                                            random_sleep(0.5, 1)
                                            comment_input.click()
                                            random_sleep(0.5, 1)

                                            # Type comment character by character to appear more human-like
                                            for char in comment_text:
                                                comment_input.send_keys(char)
                                                random_sleep(0.01, 0.05)

                                            print(
                                                f"✔️ Entered comment: {comment_text}")
                                            random_sleep(1, 2)

                                            # Post the comment
                                            post_comment_selectors = [
                                                "//button[contains(text(), 'Post')]",
                                                "//button[@type='submit']",
                                                "//div[@role='button' and contains(text(), 'Post')]"
                                            ]

                                            post_button = None
                                            for selector in post_comment_selectors:
                                                try:
                                                    post_button = WebDriverWait(self.driver, 5).until(
                                                        EC.element_to_be_clickable(
                                                            (By.XPATH, selector))
                                                    )
                                                    break
                                                except:
                                                    continue

                                            if post_button:
                                                random_sleep(0.5, 1)
                                                try:
                                                    post_button.click()
                                                except:
                                                    self.driver.execute_script(
                                                        "arguments[0].click();", post_button)

                                                print(
                                                    "✔️ Posted comment successfully")
                                                comments_made += 1

                                                # Record in Google Sheets if setup
                                                if self.sheets_api:
                                                    try:
                                                        self.update_instagram_interaction(
                                                            username,
                                                            description or "Feed post",
                                                            comment_text
                                                        )
                                                        print(
                                                            "✔️ Recorded interaction in Google Sheets")
                                                    except Exception as e:
                                                        print(
                                                            f"⚠️ Failed to record in Google Sheets: {e}")

                                                # Wait a bit longer after commenting to avoid rate limiting
                                                random_sleep(3, 5)
                                            else:
                                                print(
                                                    "❌ Could not find post button")
                                        else:
                                            print(
                                                "❌ Failed to generate comment")
                                    else:
                                        print(
                                            "❌ Could not find comment input field")
                                else:
                                    print("❌ Could not find comment button")

                            # Clean up screenshot
                            try:
                                os.remove(screenshot_path)
                            except:
                                pass
                        except Exception as screenshot_error:
                            print(
                                f"❌ Error taking screenshot: {screenshot_error}")
                            try:
                                if os.path.exists(screenshot_path):
                                    os.remove(screenshot_path)
                            except:
                                pass

                    except Exception as post_error:
                        print(f"❌ Error processing post: {post_error}")

                # Scroll down to load more posts if we need to
                if posts_processed < num_posts and comments_made < comments_per_session:
                    print_substep("Scrolling to load more posts...")
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                    random_sleep(2, 3)

                    # Check if page has new content
                    new_height = self.driver.execute_script(
                        "return document.body.scrollHeight")
                    if new_height == last_height:
                        # Try scrolling a bit more
                        self.driver.execute_script("window.scrollBy(0, 1000);")
                        random_sleep(2, 3)
                        new_height = self.driver.execute_script(
                            "return document.body.scrollHeight")

                        # If still no new content, we've reached the end
                        if new_height == last_height:
                            print("Reached end of feed")
                            break

                    last_height = new_height

            return posts_processed, comments_made

        except Exception as e:
            print(f"❌ Error scrolling feed: {e}")
            return posts_processed, comments_made

    def setup_sheets_api(self):
        """Set up Google Sheets API for tracking interactions."""
        print_substep("Setting up Google Sheets API...")

        try:
            # Path to service account credentials file
            credentials_path = "google-sheet-creds.json"

            # Check if credentials file exists
            if not os.path.exists(credentials_path):
                print("⚠️ Google Sheets credentials file not found")
                return False

            # Set up credentials
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )

            # Build the sheets API client
            self.sheets_api = build("sheets", "v4", credentials=credentials)
            print("✔️ Google Sheets API set up successfully")
            return True

        except Exception as e:
            print(f"❌ Error setting up Google Sheets API: {e}")
            return False

    def update_instagram_interaction(self, instagram_username, description, comment):
        """Record Instagram interaction in Google Sheets."""
        if not self.sheets_api:
            print("⚠️ Google Sheets API not set up")
            return False

        try:
            print(
                f"\nAttempting to update Instagram interaction: {instagram_username}...")

            # Your Google Sheet ID
            spreadsheet_id = "1jZqvq0Xtdsjm3qiCZ1XYqqZm-OsMvSyqb3nYuzoYn4Q"

            # Check if the Instagram user already exists in column P
            result = self.sheets_api.values().get(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!P:P'  # Instagram username column
            ).execute()

            rows = result.get('values', [])
            if not rows:
                print("✗ No data found in the Instagram column")
                return False

            # Check if Instagram username already exists (case insensitive)
            existing_row_index = None
            for i, row in enumerate(rows):
                if row and row[0].strip().lower() == instagram_username.strip().lower():
                    existing_row_index = i
                    print(
                        f"✓ EXISTING USER FOUND: {instagram_username} at row {existing_row_index+1}")
                    break

            if existing_row_index is None:
                # Add new user if not found
                print(f"✓ NEW USER - Adding {instagram_username} as new entry")

                # Get current number of rows to append to the end
                insta_column_data = self.sheets_api.values().get(
                    spreadsheetId=spreadsheet_id,
                    range='Sheet1!P:P'  # Instagram usernames column
                ).execute()

                insta_rows = insta_column_data.get('values', [])
                row_index = len(insta_rows)

                print(f"✓ Will add new Instagram user at row {row_index+1}")

                # Update Instagram username in column P
                self.sheets_api.values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f'Sheet1!P{row_index+1}',
                    valueInputOption='RAW',
                    body={'values': [[instagram_username]]}
                ).execute()

                print(f"✓ Added Instagram username: {instagram_username}")

                # Add conversation history in column R (assuming this is the conversation column)
                conversation_text = f"Instagram Feed Post - {description} - Commented: {comment}"

                self.sheets_api.values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f'Sheet1!R{row_index+1}',
                    valueInputOption='RAW',
                    body={'values': [[conversation_text]]}
                ).execute()

                print(
                    f"✓ Added conversation history for new user {instagram_username}")

            else:
                # Update existing user
                print(f"✓ UPDATING EXISTING USER: {instagram_username}")
                conversation_text = f"Instagram Feed Post - {description} - Commented: {comment}"

                # Get existing conversation text
                existing_convo_result = self.sheets_api.values().get(
                    spreadsheetId=spreadsheet_id,
                    range=f'Sheet1!R{existing_row_index+1}'
                ).execute()

                existing_convo = ""
                if 'values' in existing_convo_result and existing_convo_result['values'][0]:
                    existing_convo = existing_convo_result['values'][0][0]

                # Append new conversation
                if existing_convo:
                    updated_convo = f"{existing_convo}\n\n{conversation_text}"
                else:
                    updated_convo = conversation_text

                # Update the conversation column
                self.sheets_api.values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f'Sheet1!R{existing_row_index+1}',
                    valueInputOption='RAW',
                    body={'values': [[updated_convo]]}
                ).execute()

                print(
                    f"✓ Updated conversation history for existing user {instagram_username}")

            return True

        except Exception as e:
            print(f"✗ Error in update_instagram_interaction: {e}")
            return False

    def cleanup(self):
        """Clean up resources."""
        print_step("CLEANING UP")

        try:
            # Close the browser window
            if self.driver:
                self.driver.quit()
                print("✔️ Browser closed successfully")
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")


def main():
    """Main function to run the Instagram feed commenter bot."""
    print_step("STARTING INSTAGRAM FEED COMMENTER BOT")

    bot = InstagramFeedBot()

    try:
        # Log in to Instagram
        if not bot.login():
            print("❌ Failed to log in to Instagram. Exiting.")
            bot.cleanup()
            return

        # Navigate to feed
        if not bot.navigate_to_feed():
            print("❌ Failed to navigate to feed. Exiting.")
            bot.cleanup()
            return

        # Scroll feed and comment on posts
        # Parameters: number of posts to process, maximum comments per session
        posts_processed, comments_made = bot.scroll_feed(
            num_posts=20, comments_per_session=5)

        print_step("SESSION SUMMARY")
        print(f"""
Feed Interaction Statistics:
Posts processed: {posts_processed}
Comments made: {comments_made}
Success rate: {(comments_made/posts_processed)*100 if posts_processed > 0 else 0:.2f}%
""")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    finally:
        # Always clean up resources
        bot.cleanup()


if __name__ == "__main__":
    main()
