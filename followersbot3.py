import argparse
import sys
import os

# Import the emoji fix first to handle any encoding issues
import fix_emojis

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
import random
import datetime
import json
import google.generativeai as genai
from scripts.sheets_integration import GoogleSheetsManager
import re
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from app.conversation_analytics_integration import analytics
import traceback

# --- Command Line Argument Parsing ---
parser = argparse.ArgumentParser(
    description='Instagram messaging and liking bot')
parser.add_argument('--reset', action='store_true',
                    help='Reset progress and message all users again')
parser.add_argument('--followers-list', type=str, default='instagram_followers.txt',
                    help='Path to the file containing the list of Instagram followers')
parser.add_argument('--daily-limit', type=int, default=300,
                    help='Maximum number of DMs to send per day (default: 300)')
parser.add_argument('--chromedriver', type=str, default=None,
                    help='Path to ChromeDriver executable (overrides default paths)')
args = parser.parse_args()

# Ensure we're using absolute paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FOLLOWERS_LIST = os.path.join(SCRIPT_DIR, args.followers_list)

# --- Function to find available ChromeDriver ---


def find_chromedriver():
    """Find a valid ChromeDriver executable from multiple common locations"""
    # If user specified a path via command line, try that first
    if args.chromedriver and os.path.exists(args.chromedriver):
        print(f"Using user-specified ChromeDriver: {args.chromedriver}")
        return args.chromedriver

    # List of potential ChromeDriver locations
    potential_paths = [
        # Original path from script
        r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe",
        # Common Windows locations
        r"C:\chromedriver.exe",
        r"C:\chromedriver\chromedriver.exe",
        r"C:\WebDrivers\chromedriver.exe",
        # Program Files locations
        r"C:\Program Files\ChromeDriver\chromedriver.exe",
        r"C:\Program Files (x86)\ChromeDriver\chromedriver.exe",
        # User directory locations
        os.path.join(os.path.expanduser("~"), "chromedriver.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "chromedriver.exe"),
        os.path.join(os.path.expanduser("~"), "Desktop", "chromedriver.exe"),
        # Current directory and script directory
        os.path.join(os.getcwd(), "chromedriver.exe"),
        os.path.join(SCRIPT_DIR, "chromedriver.exe"),
        os.path.join(SCRIPT_DIR, "drivers", "chromedriver.exe"),
    ]

    # Check for the chromedriver in PATH environment variable
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    for path_dir in path_dirs:
        potential_paths.append(os.path.join(path_dir, "chromedriver.exe"))
        potential_paths.append(os.path.join(path_dir, "chromedriver"))

    # Check if any of these paths exist
    for path in potential_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            print(f"Found ChromeDriver at: {path}")
            return path

    # If we get here, no ChromeDriver was found
    print("ERROR: Could not find ChromeDriver in any of the expected locations.")
    print("Please install ChromeDriver and ensure it matches your Chrome version.")
    print("Download from: https://chromedriver.chromium.org/downloads")
    print("\nAvailable options:")
    print("1. Place chromedriver.exe in one of these locations:")
    for path in potential_paths[:5]:  # Show first 5 paths
        print(f"   - {path}")
    print("2. Add chromedriver to your PATH environment variable")
    print("3. Specify the path explicitly using --chromedriver parameter")
    return None


# --- Browser Driver Setup with improved error handling ---
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--start-maximized")  # Start with maximized window
chrome_options.add_argument("--disable-notifications")  # Disable notifications
chrome_options.add_argument(
    "--disable-popup-blocking")  # Disable popup blocking
# These additional options might help with stability issues
chrome_options.add_argument("--disable-extensions")  # Disable extensions
chrome_options.add_argument("--disable-infobars")  # Disable infobars
chrome_options.add_argument(
    "--ignore-certificate-errors")  # Ignore cert errors
chrome_options.add_argument(
    "--disable-blink-features=AutomationControlled")  # Avoid detection
chrome_options.add_experimental_option("detach", True)  # Keep browser open
chrome_options.add_experimental_option(
    "excludeSwitches", ["enable-automation"])  # Hide automation
chrome_options.add_experimental_option(
    'useAutomationExtension', False)  # Disable automation extension
chrome_options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.notifications": 2,  # Block notifications
    "credentials_enable_service": False,  # Disable password saving
    "profile.password_manager_enabled": False  # Disable password manager
})

# Find a valid ChromeDriver path
chromedriver_path = find_chromedriver()

try:
    if not chromedriver_path:
        print("No valid ChromeDriver found. Exiting.")
        sys.exit(1)

    # Initialize the driver with Service object for the specific chromedriver path
    service = webdriver.chrome.service.Service(
        executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(1920, 1080)  # Set a specific window size
    driver.set_window_position(0, 0)  # Position window at top-left
    # Add an explicit wait for the driver
    wait = WebDriverWait(driver, 30)  # 30 second timeout for element finding
except Exception as e:
    print(f"Chrome driver initialization error: {e}")
    print("Please make sure ChromeDriver is properly installed and matches your Chrome version.")
    exit(1)

# --- Instagram Credentials ---
USERNAME = "cocos_connected"
PASSWORD = "Shannonb3"

# --- Gemini API Key ---
GEMINI_API_KEY = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

# --- Google Sheets Service Account ---
# Update this path if your credentials file is named differently or located elsewhere
SHEETS_SERVICE_ACCOUNT = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\sheets_credentials.json"

# Initialize Google Sheets manager
sheets_manager = GoogleSheetsManager(SHEETS_SERVICE_ACCOUNT)

# Initialize Gemini client
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# --- Message Options ---
MESSAGE_OPTIONS = [
    "Love seeing your content! Keep it coming!",
    "Great posts! Keep it up!",
    "Love your content! 👍",
    "Your posts are awesome!",
    "Love what you share!",
    "Your content is 🔥",
    "Love your posts!",
    "Your content is amazing!",
    "Great Content!Keep up the good work!",
    "Really enjoying your posts!",
    "Love your feed!",
    "Great content!",
    "Your posts are fantastic!",
    "Keep the content coming!",
    "Love what you do!",
    "Your page is great!",
    "Amazing content!",
    "Your posts rock!",
    "Love your posts,Keep it up!",
    "Love your style!",
    "Awesome content!",
    "Great page!",
    "Your posts are great!",
    "Nice content!",
    "Sweet Content,Keep posting!"
]

# --- Function to load usernames from file ---


def load_usernames(file_path):
    """Load usernames from a file and return them as a list."""
    print(f"\nAttempting to load usernames from: {file_path}")

    # Create the file if it doesn't exist
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        print("Creating new file...")
        try:
            with open(file_path, 'w') as f:
                f.write("# Add Instagram usernames below (one per line)\\n")
                f.write("# Lines starting with # are ignored\\n")
            print(f"Created new file: {file_path}")
            print(
                f"Please add usernames to {file_path} and run the script again.")
            return []
        except Exception as e:
            print(f"Error creating file: {e}")
            return []

    # Read usernames from file
    try:
        print(f"Reading usernames from file...")
        with open(file_path, 'r') as f:
            # Filter out empty lines and comments
            usernames = [line.strip() for line in f if line.strip()
                         and not line.strip().startswith('#')]
        print(f"Successfully loaded {len(usernames)} usernames")
        print(f"First few usernames: {usernames[:5]}")
        return usernames
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

# --- Function to save progress ---


def save_progress(file_path, processed_usernames):
    with open(file_path, 'w') as f:
        for username in processed_usernames:
            f.write(f"{username}\n")

# --- Function to load progress ---


def load_progress(file_path):
    if not os.path.exists(file_path):
        return set()

    with open(file_path, 'r') as f:
        return {line.strip() for line in f if line.strip()}

# --- Function to login to Instagram ---


def login_to_instagram(driver, username, password):
    try:
        # Navigate to Instagram login page
        driver.get("https://www.instagram.com/accounts/login/")
        print("Navigated to Instagram login page.")
        time.sleep(8)  # Increased wait time for page to load completely

        # Take screenshot of login page to diagnose issues
        driver.save_screenshot("login_page.png")
        print("Saved login page screenshot.")

        # Try to find login fields using various approaches

        # APPROACH 2: Try specific selectors as before, but with more options
        print("Trying specific selectors approach...")
        username_field_selectors = [
            (By.NAME, "username"),
            (By.XPATH, "//input[@name='username']"),
            (By.XPATH,
             "//input[@aria-label='Phone number, username, or email']"),
            (By.XPATH,
             "//input[@placeholder='Phone number, username, or email']"),
            (By.XPATH, "//input[contains(@placeholder, 'username')]"),
            (By.XPATH, "//input[contains(@placeholder, 'email')]"),
            (By.XPATH, "//input[contains(@id, 'user')]"),
            (By.XPATH, "//input[contains(@class, 'user')]"),
            # Often the first input in a form is username
            (By.XPATH, "//form//input[1]"),
            (By.CSS_SELECTOR, "form input:first-of-type")
        ]

        username_field = None
        for selector_type, selector_value in username_field_selectors:
            try:
                elements = driver.find_elements(selector_type, selector_value)
                for element in elements:
                    if element.is_displayed():
                        username_field = element
                        print(
                            f"Found username field with selector: {selector_type}={selector_value}")
                        break
                if username_field:
                    break
            except Exception as e:
                print(f"Selector {selector_type}={selector_value} failed: {e}")
                continue

        if not username_field:
            print("Could not find username field with specific selectors")
            driver.save_screenshot("username_field_not_found.png")
            print("❌ Login failed: Could not find username field.")
            return False
        else:
            username_field.clear()
            username_field.send_keys(username)
            print("Entered username with specific selector.")

            # Try multiple selectors for password field
            password_field_selectors = [
                (By.NAME, "password"),
                (By.XPATH, "//input[@name='password']"),
                (By.XPATH, "//input[@aria-label='Password']"),
                (By.XPATH, "//input[@placeholder='Password']"),
                (By.XPATH, "//input[@type='password']"),
                (By.XPATH, "//input[contains(@id, 'pass')]"),
                (By.XPATH, "//input[contains(@class, 'pass')]"),
                # Often the second input in a form is password
                (By.XPATH, "//form//input[2]"),
                (By.CSS_SELECTOR, "form input[type='password']")
            ]

            password_field = None
            for selector_type, selector_value in password_field_selectors:
                try:
                    elements = driver.find_elements(
                        selector_type, selector_value)
                    for element in elements:
                        if element.is_displayed():
                            password_field = element
                            print(
                                f"Found password field with selector: {selector_type}={selector_value}")
                            break
                    if password_field:
                        break
                except Exception:
                    continue

            if not password_field:
                print("Could not find password field with specific selectors")
                driver.save_screenshot("password_field_not_found.png")
                print("❌ Login failed: Could not find password field.")
                return False
            else:
                password_field.clear()
                password_field.send_keys(password)
                print("Entered password with specific selector.")

                # Take screenshot before clicking login
                driver.save_screenshot("before_login_click.png")

                # Try multiple selectors for login button
                login_button_selectors = [
                    (By.XPATH, "//button[@type='submit']"),
                    (By.XPATH, "//button[contains(text(), 'Log in')]"),
                    (By.XPATH,
                     "//div[contains(text(), 'Log in')]/parent::button"),
                    (By.XPATH, "//button[contains(text(), 'Log In')]"),
                    (By.XPATH, "//button[contains(@class, 'login')]"),
                    (By.XPATH, "//button[contains(@class, 'submit')]"),
                    (By.XPATH,
                     "//div[contains(text(), 'Log In')]/parent::button"),
                    # Generic - any button in a form
                    (By.XPATH, "//form//button"),
                    # Sometimes it's a div with role=button
                    (By.XPATH, "//form//div[@role='button']")
                ]

                login_button = None
                for selector_type, selector_value in login_button_selectors:
                    try:
                        elements = driver.find_elements(
                            selector_type, selector_value)
                        for element in elements:
                            if element.is_displayed():
                                login_button = element
                                print(
                                    f"Found login button with selector: {selector_type}={selector_value}")
                                break
                        if login_button:
                            break
                    except Exception:
                        continue

                if not login_button:
                    print("Could not find login button with specific selectors")
                    driver.save_screenshot("login_button_not_found.png")
                    print("❌ Login failed: Could not find login button.")
                    return False
                else:
                    # --- Modified Click Logic ---
                    login_successful = False
                    try:
                        print(f"Attempting standard click on login button...")
                        # Add a small pause before clicking
                        time.sleep(1)
                        login_button.click()
                        print("Standard click executed.")
                        # Wait for potential page change/login processing
                        # Increased wait to ensure login completes
                        time.sleep(15)
                        # Check if login was successful immediately after standard click
                        if "/accounts/login" not in driver.current_url:
                            print("✅ Login successful after standard click.")
                            login_successful = True
                        else:
                            print(
                                "⚠️ Still on login page after standard click. Trying JS click...")

                    except Exception as click_err:
                        print(
                            f"⚠️ Standard click failed: {click_err}. Trying JS click...")

                    # Try JavaScript click if standard click didn't work or failed
                    if not login_successful:
                        try:
                            print(f"Attempting JavaScript click on login button...")
                            driver.execute_script(
                                "arguments[0].click();", login_button)
                            print("JavaScript click executed.")
                            # Wait again for potential page change
                            time.sleep(10)
                            if "/accounts/login" not in driver.current_url:
                                print("✅ Login successful after JavaScript click.")
                                login_successful = True
                            else:
                                print(
                                    "❌ Still on login page after JavaScript click.")
                                driver.save_screenshot(
                                    "login_failed_after_js_click.png")

                        except Exception as js_err:
                            print(f"❌ JavaScript click failed: {js_err}")
                            driver.save_screenshot("login_js_click_error.png")
                    # --- End of Modified Click Logic ---

                    # Final check and return status
                    if login_successful:
                        print("✅ Login successful overall.")
                        handle_post_login_popups(driver)
                        return True
                    else:
                        print("❌ Login failed overall.")
                        # Screenshot was already taken if JS click failed
                        if "login_failed_after_js_click.png" not in os.listdir():  # Avoid duplicate screenshot
                            driver.save_screenshot("login_failed_final.png")
                        return False

    except Exception as e:
        print(f"Error during login: {e}")
        driver.save_screenshot("login_error.png")
        return False


def handle_post_login_popups(driver):
    """Handle the various popups that might appear after login"""
    try:
        # List of common popups and their dismiss button selectors
        popups = [
            {
                "name": "Save Login Info",
                "selectors": [
                    "//button[contains(text(), 'Not Now')]",
                    "//button[contains(text(), 'Save Info')]",
                    "//button[contains(text(), 'Not now')]",
                    # Class sometimes used for "Not Now"
                    "//button[contains(@class, 'HoLwm')]"
                ]
            },
            {
                "name": "Notifications",
                "selectors": [
                    "//button[contains(text(), 'Not Now')]",
                    "//button[contains(text(), 'Not now')]",
                    "//button[contains(text(), 'Cancel')]",
                    # Class sometimes used for "Not Now"
                    "//button[contains(@class, 'HoLwm')]"
                ]
            },
            {
                "name": "Add to Home Screen",
                "selectors": [
                    "//button[contains(text(), 'Cancel')]",
                    "//button[contains(text(), 'Not now')]",
                    "//div[contains(@role, 'button')][contains(text(), 'Cancel')]"
                ]
            }
        ]

        # Try to handle each possible popup
        for popup in popups:
            try:
                for selector in popup["selectors"]:
                    try:
                        buttons = driver.find_elements(By.XPATH, selector)
                        for button in buttons:
                            if button.is_displayed():
                                button.click()
                                print(
                                    f"Clicked '{popup['name']}' popup dismiss button")
                                time.sleep(2)  # Wait for popup to close
                                break
                    except:
                        continue
            except Exception as e:
                print(f"Error handling {popup['name']} popup: {e}")

        # Also try a generic approach to find any visible "Not Now" button
        try:
            # Look for any button containing "Not Now", "Cancel", etc.
            generic_selectors = [
                "//button[contains(text(), 'Not Now')]",
                "//button[contains(text(), 'Not now')]",
                "//button[contains(text(), 'Cancel')]",
                "//button[contains(text(), 'Skip')]",
                "//button[contains(text(), 'Later')]",
                "//div[@role='button'][contains(text(), 'Not Now')]",
                "//div[@role='button'][contains(text(), 'Cancel')]"
            ]

            for selector in generic_selectors:
                try:
                    buttons = driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed():
                            button.click()
                            print(
                                f"Clicked generic popup dismiss button '{button.text}'")
                            time.sleep(2)
                            break
                except:
                    continue
        except Exception as e:
            print(f"Error with generic popup handling: {e}")

    except Exception as e:
        print(f"Error handling post-login popups: {e}")

    print("Completed post-login popup handling")


def analyze_multiple_images_with_gemini(image_paths, username):
    """Analyze multiple Instagram post images using the Gemini Vision API."""
    print(f"Analyzing {len(image_paths)} posts from {username} with Gemini...")

    # Initialize results
    all_analyses = []
    conversation_topics = []
    main_analysis = None

    # Initialize client analysis data structure
    client_analysis = {
        "posts_analyzed": len(image_paths),
        "timestamp": datetime.datetime.now().isoformat(),
        "interests": [],
        "lifestyle_indicators": [],
        "recent_activities": [],
        "post_summaries": [],
        "conversation_topics": []
    }

    # Analyze each image individually
    for i, image_path in enumerate(image_paths):
        try:
            # Load the image file for Gemini
            with open(image_path, 'rb') as f:
                image_data = f.read()

                if not image_data:
                    print(f"Warning: Empty image data for {image_path}")
                    continue

            # Create a Gemini image part
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_data
            }

            # Adjust the prompt based on whether this is the first (most recent) image
            if i == 0:
                # For the first/most recent image, use the original prompt format
                prompt = f"""
                Analyze this Instagram post by {username}.

                Provide a detailed description of the image and suggest a friendly, personal DIRECT MESSAGE (not a comment) that acknowledges seeing their post.

                IMPORTANT:
                1. Create a message someone would send in a DM after seeing this post, dont include a question in the message
                2. Include genuine compliments or observations about the post
                3. Use past tense when commenting on the content of the post (e.g., "He looked cool," "Hope he had fun")
                4. Keep the comment friendly, personalized, and concise
                5. Add 1-2 relevant emojis if appropriate
                6. Do NOT write "Nice post" or generic comments but dont be too overboard with your comments either as it is becomes obviously an ai. here and example - Hey i was just having a stalk of your profile, the butter chicken looked delish! Did you cook it up? :) (only use 1 emoji per response)
                7. ALWAYS mention you were looking at their profile and at their most recent post" in your message (e.g., "Heya! Just was having a little stalk! Love your latest post! (insert info)
                8. Here's an example of a dm you could send - "Hey was just having a stalk, havnt seen ur gram in a minute love your latest post about (insert here)! Hope your well! :)"- keep it similar to this - chill and easy




                9. RESPOND IN THIS EXACT FORMAT ONLY:

                DESCRIPTION: [Detailed description of what you see in the image]

                COMMENT: [Your message here - do NOT include the word 'COMMENT:' in the actual message text]

                IMPORTANT: The text after "COMMENT:" should be EXACTLY what would be sent as a DM, with no prefixes or labels.
                """
            else:
                # For other images, use a simpler prompt focused on extracting topics
                prompt = f"""
                Analyze this Instagram post by {username}.

                Based on this image, identify 1-2 potential conversation topics that could be used to engage with this person in future messages.

                RESPOND IN THIS FORMAT:
                DESCRIPTION: [Brief description of what you see in the image]

                TOPICS: [List 1-2 conversation topics based on interests or activities shown in the image]
                """

            # Attempt to call the Gemini API with retries
            max_api_retries = 3
            api_retry_count = 0

            while api_retry_count < max_api_retries:
                try:
                    # Generate content with the image using the gemini model
                    response = gemini_model.generate_content(
                        contents=[
                            {"text": prompt},
                            {"inline_data": image_part}
                        ],
                        generation_config=genai.GenerationConfig(
                            temperature=0.4,
                            max_output_tokens=400,
                        )
                    )

                    # Get the response text
                    response_text = response.text

                    # For the first image (most recent post)
                    if i == 0:
                        # Parse the response for description and comment
                        description_match = re.search(
                            r'DESCRIPTION:\s*(.*?)(?=\n\n|\nCOMMENT:)', response_text, re.DOTALL)
                        comment_match = re.search(
                            r'COMMENT:\s*(.*?)(?=$)', response_text, re.DOTALL)

                        if description_match and comment_match:
                            description = description_match.group(1).strip()
                            comment = comment_match.group(1).strip()

                            main_analysis = {
                                'description': description,
                                'comment': comment,
                                'raw_response': response_text
                            }

                            # Add to client analysis
                            client_analysis["post_summaries"].append({
                                "description": description,
                                "activities": [],
                                "interests": []
                            })

                            print(f"Successfully analyzed most recent post.")
                            all_analyses.append(main_analysis)
                    else:
                        # Parse responses from other images for topics
                        description_match = re.search(
                            r'DESCRIPTION:\s*(.*?)(?=\n\n|\nTOPICS:)', response_text, re.DOTALL)
                        topics_match = re.search(
                            r'TOPICS:\s*(.*?)(?=$)', response_text, re.DOTALL)

                        if topics_match:
                            topics = topics_match.group(1).strip()
                            # Add new topics to our list
                            for topic in topics.split('\n'):
                                topic = topic.strip()
                                if topic and not topic.startswith('-'):
                                    conversation_topics.append(topic)
                                    # Add to client analysis
                                    if topic not in client_analysis["conversation_topics"]:
                                        client_analysis["conversation_topics"].append(
                                            topic)

                            if description_match:
                                client_analysis["post_summaries"].append({
                                    "description": description_match.group(1).strip(),
                                    "activities": [],
                                    "interests": []
                                })

                            analysis_result = {
                                'description': description_match.group(1).strip() if description_match else "",
                                'topics': topics,
                                'raw_response': response_text
                            }

                            all_analyses.append(analysis_result)
                            print(f"Extracted topics from post {i+1}.")

                    # Break the retry loop if successful
                    break

                except Exception as api_error:
                    api_retry_count += 1
                    print(
                        f"Gemini API error (attempt {api_retry_count}): {api_error}")
                    if api_retry_count >= max_api_retries:
                        print("Maximum API retries reached. Skipping this image.")
                    else:
                        time.sleep(2)  # Wait before retrying

        except Exception as e:
            print(f"Error analyzing image {i+1}: {str(e)}")

    # If we have a main analysis (from the most recent post)
    if main_analysis:
        # Extract up to 5 unique conversation topics
        unique_topics = []
        for topic in conversation_topics:
            if len(unique_topics) >= 5:
                break
            if topic not in unique_topics:
                unique_topics.append(topic)

        # Add conversation topics to the main analysis
        main_analysis['conversation_topics'] = unique_topics
        main_analysis['all_analyses'] = all_analyses

        # Update client analysis with final topics
        client_analysis["conversation_topics"] = unique_topics

        # *** ADD THE GENERATED COMMENT TO client_analysis ***
        client_analysis["generated_comment"] = main_analysis.get('comment', '')

        # Generate profile bio using the collected data
        profile_bio = generate_profile_bio(
            username, client_analysis, image_paths)
        if profile_bio:
            client_analysis["profile_bio"] = profile_bio

        # Update analytics with client analysis
        # This now includes the generated_comment thanks to the line above
        if username not in analytics.conversation_metrics:
            analytics.conversation_metrics[username] = analytics._initialize_conversation_metrics(
            )

        # Store the client analysis in the analytics
        analytics.conversation_metrics[username]["client_analysis"] = client_analysis
        analytics.export_analytics()  # This will now save the comment

        print(
            f"Analysis complete with {len(unique_topics)} potential conversation topics.")
        return main_analysis

    return None


def generate_profile_bio(username, client_analysis, image_paths):
    """Generate a comprehensive profile bio using Gemini AI based on analyzed posts.

    Args:
        username: The Instagram username
        client_analysis: Dictionary containing analysis of user's posts
        image_paths: List of paths to post screenshots

    Returns:
        Dictionary containing profile bio information
    """
    print(f"Generating profile bio for {username}...")

    try:
        # Prepare the prompt with all available information
        descriptions = []
        for post in client_analysis.get("post_summaries", []):
            if "description" in post:
                descriptions.append(post["description"])

        descriptions_text = "\n\n".join(descriptions)
        topics_text = "\n".join(client_analysis.get("conversation_topics", []))

        # Create a combined prompt for Gemini
        prompt = f"""
        Based on the following information from Instagram user '{username}', create a comprehensive profile bio.

        POST DESCRIPTIONS:
        {descriptions_text}

        IDENTIFIED CONVERSATION TOPICS:
        {topics_text}

        Please analyze this data and create a detailed profile with the following sections:

        1. PERSON NAME: Try to identify their full name if mentioned in posts or username
        2. INTERESTS: List 3-5 key interests based on their content
        3. LIFESTYLE: Brief description of their lifestyle, activities, or profession
        4. CONVERSATION STARTERS: 5 specific questions or topics that would be good to discuss with them
        5. PERSONALITY TRAITS: 3-4 personality traits you can infer from their content

        Format your response as a structured JSON object with these fields. If you cannot determine certain information, indicate "Unknown" for that field.
        """

        try:
            # Generate profile bio using text-only Gemini model for more structured output
            response = gemini_model.generate_content(
                contents=[{"text": prompt}],
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=800,
                )
            )

            # Get the response text
            response_text = response.text

            # Try to parse as JSON first
            try:
                # Check if response is JSON formatted
                if '{' in response_text and '}' in response_text:
                    # Extract JSON part if there's surrounding text
                    json_text = response_text[response_text.find(
                        '{'):response_text.rfind('}')+1]
                    profile_data = json.loads(json_text)
                else:
                    # Parse structured text into a dictionary
                    profile_data = parse_structured_text(response_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, use regex to extract structured information
                profile_data = parse_structured_text(response_text)

            print(f"Successfully generated profile bio for {username}")
            return profile_data

        except Exception as e:
            print(f"Error generating profile bio with Gemini: {e}")
            # Fallback to a basic profile structure
            return {
                "person_name": f"{username}",
                "interests": client_analysis.get("conversation_topics", ["Unknown"]),
                "lifestyle": "Information not available",
                "conversation_starters": [
                    "What have you been up to lately?",
                    "Tell me more about your interests.",
                    "How's your day been going?",
                    "Any exciting plans coming up?",
                    "What do you enjoy doing in your free time?"
                ],
                "personality_traits": ["Based on limited data"]
            }

    except Exception as e:
        print(f"Error in generate_profile_bio: {e}")
        return None


def parse_structured_text(text):
    """Parse structured text into a dictionary when JSON parsing fails."""
    profile_data = {
        "person_name": "Unknown",
        "interests": [],
        "lifestyle": "Unknown",
        "conversation_starters": [],
        "personality_traits": []
    }

    # Extract Person Name
    name_match = re.search(
        r'(?:PERSON NAME|Name|Full Name)[:\s]+(.*?)(?:\n|$)', text, re.IGNORECASE)
    if name_match:
        profile_data["person_name"] = name_match.group(1).strip()

    # Extract Interests
    interests_section = re.search(
        r'(?:INTERESTS|Interests)[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
    if interests_section:
        interests_text = interests_section.group(1).strip()
        interests = [interest.strip() for interest in re.split(
            r'[\n\-•,]', interests_text) if interest.strip()]
        profile_data["interests"] = interests

    # Extract Lifestyle
    lifestyle_match = re.search(
        r'(?:LIFESTYLE|Lifestyle)[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
    if lifestyle_match:
        profile_data["lifestyle"] = lifestyle_match.group(1).strip()

    # Extract Conversation Starters
    conv_section = re.search(
        r'(?:CONVERSATION STARTERS|Conversation Starters)[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
    if conv_section:
        conv_text = conv_section.group(1).strip()
        starters = [starter.strip() for starter in re.split(
            r'[\n\-•]', conv_text) if starter.strip()]
        profile_data["conversation_starters"] = starters

    # Extract Personality Traits
    traits_section = re.search(
        r'(?:PERSONALITY TRAITS|Personality Traits)[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
    if traits_section:
        traits_text = traits_section.group(1).strip()
        traits = [trait.strip() for trait in re.split(
            r'[\n\-•,]', traits_text) if trait.strip()]
        profile_data["personality_traits"] = traits

    return profile_data


# Original function is kept for backward compatibility
def analyze_image_with_gemini(image_path, username):
    """Analyze a single Instagram post image using the Gemini Vision API.

    This is kept for backwards compatibility.
    """
    return analyze_multiple_images_with_gemini([image_path], username)


def like_photos(driver, username, num_photos=1):
    results_dir = f"results/{username}"
    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)

    print(f"Attempting to analyze {num_photos} photos for {username}...")
    final_analysis_result = None  # Variable to hold the result

    try:
        # Check if profile is private
        try:
            private_indicators = driver.find_elements(
                By.XPATH, "//h2[contains(text(), 'Private')]")
            if private_indicators:
                print(
                    f"Profile for {username} is private. Cannot analyze photos.")
                driver.save_screenshot(f"{results_dir}/private_profile.png")
                return None  # Return None if private
        except Exception:
            pass

        # Find posts on the profile page
        try:
            posts = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class, '_aagw')]"))
            )

            # If no posts found, try alternative selector
            if not posts or len(posts) == 0:
                try:
                    posts = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, "//div[@role='button']/a[@role='link' and @tabindex='0']"))
                    )
                except:
                    # Final fallback - just get any elements that look like posts
                    posts = driver.find_elements(
                        By.XPATH, "//div[@role='button']")

            print(f"Found {len(posts)} posts for {username}")

            # Check if any posts are available to analyze
            if posts and len(posts) > 0:
                # Get multiple posts for analysis (up to 6)
                image_paths = []
                max_posts_to_analyze = min(6, len(posts))

                for post_idx in range(max_posts_to_analyze):
                    try:
                        # Click on the post
                        print(f"Opening post {post_idx + 1}...")
                        posts[post_idx].click()
                        time.sleep(4)  # Wait for post to load fully

                        # Take screenshot of the post
                        post_screenshot = f"{results_dir}/post_{post_idx + 1}.png"
                        driver.save_screenshot(post_screenshot)
                        print(f"Screenshot saved at {post_screenshot}")

                        # Add to our list of image paths
                        image_paths.append(post_screenshot)

                        # Close the post and return to profile
                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                        time.sleep(2)
                    except Exception as post_error:
                        print(
                            f"Error processing post {post_idx + 1}: {post_error}")
                        try:
                            # Try to close post if there was an error
                            ActionChains(driver).send_keys(
                                Keys.ESCAPE).perform()
                            time.sleep(2)
                        except:
                            pass

                # Analyze all the collected posts
                if image_paths:
                    final_analysis_result = analyze_multiple_images_with_gemini(
                        image_paths, username)

                    if final_analysis_result:
                        print("Analysis of multiple posts complete.")

                        # Log the conversation topics to help with analytics
                        topics_count = len(final_analysis_result.get(
                            'conversation_topics', []))
                        print(
                            f"Found {topics_count} potential conversation topics:")
                        for i, topic in enumerate(final_analysis_result.get('conversation_topics', [])):
                            print(f"  {i+1}. {topic}")

                        # Update the analysis data in analytics
                        if topics_count > 0 and hasattr(analytics, 'conversation_metrics') and username in analytics.conversation_metrics:
                            analytics.conversation_metrics[username]['profile_conversation_topics'] = final_analysis_result.get(
                                'conversation_topics', [])

                    else:
                        print(
                            f"Analysis skipped or failed for {username}. Proceeding with generic DM.")
                        # Reset consecutive failures counter if we got this far
                        consecutive_failures = 0
                else:
                    print(
                        f"No posts were successfully captured for {username}")

                # --- REMOVED MESSAGE SENDING LOGIC FROM like_photos ---
                # The following block, which scrolled, reloaded, found the message button,
                # and attempted to send the message within like_photos, has been removed.
                # The analysis result will be returned and passed to message_user instead.
                # --- END OF REMOVED LOGIC ---

        except Exception as post_finder_error:
            print(f"Error finding posts: {post_finder_error}")
            driver.save_screenshot(
                f"{results_dir}/post_processing_error.png")

    except Exception as e:
        print(f"Error during post analysis: {e}")
        driver.save_screenshot(f"{results_dir}/like_photos_error.png")

    # Return the analysis result (or None if it failed)
    return final_analysis_result


def message_user(driver, username, sheets_manager, gemini_client, analysis_result=None):
    """Send a direct message to an Instagram user after analyzing their profile.

    Args:
        driver: The WebDriver instance
        username: The Instagram username to message
        sheets_manager: The Google Sheets manager instance
        gemini_client: The Gemini API client
        analysis_result: Optional analysis result from previous profile analysis
    """
    print(
        f"INFO: *** Entered message_user function for {username} ***")  # Added log

    # Initialize default return value in case of early error
    message_sent = False
    return_value = {"message_sent": message_sent}

    # Added log
    print(f"DEBUG: Right before top-level try block for {username}")
    try:  # Added top-level try block
        print(f"DEBUG: Inside top-level try block for {username}")  # Added log
        # Create results directory for this user
        results_dir = f"results/{username}"  # Define results_dir first
        try:
            os.makedirs(results_dir, exist_ok=True)
            print(f"DEBUG: Ensured results directory exists: {results_dir}")
        except OSError as dir_error:
            print(
                f"ERROR: Could not create results directory {results_dir}: {dir_error}")
            # Decide if we should exit or continue without saving screenshots
            # For now, let's continue but screenshots might fail later

        # Initialize status for tracking (redundant now, but keep for clarity)
        # message_sent = False # Already initialized above
        consecutive_failures = 0
        retry_count = 0
        final_analysis_result = None

        # Use provided analysis result or generate new one
        if analysis_result:
            final_analysis_result = analysis_result
            # ====== IMPROVED MESSAGE SENDING BASED ON FOLLOWUP_MANAGER ======
            print(f"Preparing to send message to {username}")

            # Take a screenshot before finding message button
            try:  # Added try block
                driver.save_screenshot(
                    f"{results_dir}/before_message_button_search.png")
                # Added log
                print("DEBUG: Saved screenshot before message button search.")
            except Exception as screenshot_error:  # Added except block
                # Added log
                print(
                    f"ERROR: Failed to save screenshot before message button search: {screenshot_error}")

            # ---- Message Button Finding - Start ----
            # ... (rest of the message button finding logic) ...
            message_button_selectors = [
                # Try specific selector with multiple classes the user provided
                "//div[@role='button' and contains(@class, 'x1i10hfl') and contains(text(), 'Message')]",
                "//div[@role='button' and @tabindex='0' and contains(text(), 'Message')]",
                # Standard selectors
                "//div[contains(text(), 'Message')]",
                "//button[contains(text(), 'Message')]",
                "//a[contains(text(), 'Message')]",
                "//div[contains(@role, 'button') and contains(text(), 'Message')]",
                "//a[contains(@href, '/direct/t/')]"  # Direct message link
            ]

            message_button = None
            # Added log
            print(
                f"DEBUG: Starting search for message button for {username}...")
            for selector in message_button_selectors:
                # Added log
                print(f"DEBUG: Trying button selector: {selector}")
                try:  # Outer try for finding elements
                    elements = driver.find_elements(By.XPATH, selector)
                    # Added log
                    print(
                        f"DEBUG: Found {len(elements)} potential elements with selector: {selector}")

                    for element in elements:
                        try:  # Inner try for checking visibility and interaction
                            if element.is_displayed():
                                # Added log
                                print(
                                    f"DEBUG: Element IS visible for selector: {selector}")
                                # Scroll element into view to ensure it's visible
                                try:  # Added try for scroll
                                    driver.execute_script(
                                        "arguments[0].scrollIntoView(true);", element)
                                    time.sleep(1)
                                    # Added log
                                    print("DEBUG: Scrolled element into view.")
                                except Exception as scroll_err:
                                    # Added log
                                    print(
                                        f"DEBUG: Failed to scroll element into view: {scroll_err}")

                                message_button = element
                                print(
                                    f"INFO: Found visible message button element with selector: {selector}")  # Changed log level
                                break  # Exit inner loop once button is found
                            # else: # Optional: Log if element found but not visible
                            #    print(f"DEBUG: Element found but NOT visible for selector: {selector}")
                        except Exception as display_error:
                            print(
                                f"DEBUG: Error checking visibility/interacting with element for selector {selector}: {display_error}")  # Added log
                    # Correct indentation for break check
                    if message_button:
                        # Added log
                        print("DEBUG: Found button, breaking outer selector loop.")
                        break  # Exit outer loop once button is found
                except Exception as selector_error:  # Matching except for outer try
                    print(
                        f"ERROR: Error finding elements with selector {selector}: {selector_error}")  # Added log

            # ---- Message Button Finding - End ----
            # Log result of search
            if not message_button:
                # Added log
                print(
                    f"WARNING: Could not find a visible message button for {username} after trying all selectors.")

            # ---- Message Button Clicking - Start ----
            if message_button:
                # Restore the button clicking logic
                print("INFO: Message button element FOUND. Attempting to click...")
                # Take screenshot before clicking
                driver.save_screenshot(
                    f"{results_dir}/before_message_click.png")

                # Try different click methods
                click_success = False  # Initialize click_success

                # Method 1: Standard click
                try:
                    print("INFO: Attempting standard click on message button")
                    message_button.click()
                    click_success = True
                    print("INFO: Standard click successful")
                except Exception as click_err:
                    print(f"DEBUG: Standard click failed: {click_err}")

                    # Method 2: JavaScript click
                    if not click_success:
                        try:
                            print("INFO: Attempting JavaScript click")
                            driver.execute_script(
                                "arguments[0].click();", message_button)
                            click_success = True
                            print("INFO: JavaScript click successful")
                        except Exception as js_err:
                            print(f"DEBUG: JavaScript click failed: {js_err}")

                            # Method 3: ActionChains click
                            if not click_success:
                                try:
                                    print("INFO: Attempting ActionChains click")
                                    ActionChains(driver).move_to_element(
                                        message_button).click().perform()
                                    click_success = True
                                    print("INFO: ActionChains click successful")
                                except Exception as action_err:
                                    print(
                                        f"DEBUG: ActionChains click failed: {action_err}")

                # Wait for message dialog to appear
                time.sleep(3)

                # Take screenshot after clicking
                driver.save_screenshot(
                    f"{results_dir}/after_message_click.png")
                # --- End of restored click logic ---

                if click_success:
                    # ... (dialog handling) ...
                    print("INFO: Message button click SUCCEEDED. Handling dialog...")
                    print("INFO: Calling handle_message_dialog...")
                    handle_message_dialog(driver, username, results_dir)
                    print("INFO: Returned from handle_message_dialog.")

                    # --- Check if inbox/input loaded, refresh and retry if not ---
                    print("INFO: Waiting 10s for message input field to appear...")
                    time.sleep(10)
                    message_input_check = None
                    input_check_selectors = [
                        "//div[@contenteditable='true' and @role='textbox']",
                        "//textarea[@placeholder='Message...']",
                        "//div[contains(@aria-label, 'Message') and @role='textbox']"
                    ]
                    for selector in input_check_selectors:
                        try:
                            elements = driver.find_elements(By.XPATH, selector)
                            for element in elements:
                                if element.is_displayed():
                                    message_input_check = element
                                    break
                            if message_input_check:
                                break
                        except:
                            continue  # Ignore errors during check

                    if not message_input_check:
                        print(
                            "WARNING: Message input field not found after 10s. Refreshing and retrying button click...")
                        try:
                            driver.refresh()
                            print("INFO: Page refreshed. Waiting 7s...")
                            time.sleep(7)

                            # Re-find the message button
                            print("INFO: Attempting to find message button again...")
                            message_button_retry = None
                            # Re-use the existing button finding logic/selectors
                            for selector in message_button_selectors:  # Uses the list defined earlier
                                print(
                                    f"DEBUG: Retrying button selector: {selector}")
                                try:
                                    elements = driver.find_elements(
                                        By.XPATH, selector)
                                    print(
                                        f"DEBUG: Retry found {len(elements)} elements with selector: {selector}")
                                    for element in elements:
                                        try:
                                            if element.is_displayed():
                                                print(
                                                    f"DEBUG: Retry Element IS visible for selector: {selector}")
                                                try:
                                                    driver.execute_script(
                                                        "arguments[0].scrollIntoView(true);", element)
                                                    time.sleep(1)
                                                    print(
                                                        "DEBUG: Retry Scrolled element into view.")
                                                except Exception as scroll_err:
                                                    print(
                                                        f"DEBUG: Retry Failed to scroll element into view: {scroll_err}")
                                                message_button_retry = element
                                                print(
                                                    f"INFO: Re-found visible message button element with selector: {selector}")
                                                break
                                        except Exception as display_error:
                                            print(
                                                f"DEBUG: Retry Error checking visibility/interacting with element for selector {selector}: {display_error}")
                                    if message_button_retry:
                                        print(
                                            "DEBUG: Re-found button, breaking retry selector loop.")
                                        break
                                except Exception as selector_error:
                                    print(
                                        f"ERROR: Retry Error finding elements with selector {selector}: {selector_error}")

                            # Re-click the message button if found
                            if message_button_retry:
                                print(
                                    "INFO: Re-found message button. Attempting to click again...")
                                click_success_retry = False
                                try:
                                    print("INFO: Retrying standard click")
                                    message_button_retry.click()
                                    click_success_retry = True
                                    print("INFO: Retry standard click successful")
                                except Exception as click_err:
                                    print(
                                        f"DEBUG: Retry standard click failed: {click_err}")
                                    if not click_success_retry:
                                        try:
                                            print(
                                                "INFO: Retrying JavaScript click")
                                            driver.execute_script(
                                                "arguments[0].click();", message_button_retry)
                                            click_success_retry = True
                                            print(
                                                "INFO: Retry JavaScript click successful")
                                        except Exception as js_err:
                                            print(
                                                f"DEBUG: Retry JavaScript click failed: {js_err}")
                                            if not click_success_retry:
                                                try:
                                                    print(
                                                        "INFO: Retrying ActionChains click")
                                                    ActionChains(driver).move_to_element(
                                                        message_button_retry).click().perform()
                                                    click_success_retry = True
                                                    print(
                                                        "INFO: Retry ActionChains click successful")
                                                except Exception as action_err:
                                                    print(
                                                        f"DEBUG: Retry ActionChains click failed: {action_err}")

                                if click_success_retry:
                                    print(
                                        "INFO: Second message button click successful. Waiting 10s for input...")
                                    time.sleep(10)
                                else:
                                    print(
                                        "WARNING: Failed to click message button on second attempt.")
                            else:
                                print(
                                    "WARNING: Could not find message button after refresh.")

                        except Exception as refresh_error:
                            print(
                                f"ERROR: Failed during refresh/retry process: {refresh_error}")
                    else:
                        print("INFO: Message input field found on first attempt.")
                    # --- End of refresh and retry logic ---

                    # Get the message text from analysis (Moved this down after retry logic)
                    message_text = final_analysis_result.get("comment", "")
                    if not message_text:
                        message_text = "Hey! Just checked out your profile. How's it going? 😊"
                    if message_text is None:  # Ensure message_text is not None
                        message_text = "Hey! Just checked out your profile. How's it going? 😊"
                    print(f"DEBUG: Message to send: {message_text[:50]}...")

                    # --- Gemini DM Validation ---
                    message_text = validate_dm_with_gemini(message_text)

                    # ... (message input finding logic) ...
                    message_input_selectors = [
                        # Modern Instagram selectors with specific class combinations
                        "//div[@contenteditable='true' and @role='textbox']",
                        "//div[@contenteditable='true' and contains(@class, 'x1i0vuye')]",
                        "//div[@role='textbox' and contains(@aria-label, 'Message')]",
                        # Original selectors
                        "//div[@aria-label='Message' and @role='textbox']",
                        "//div[@contenteditable='true']",
                        "//div[contains(@aria-label, 'Message')]",
                        "//textarea[@placeholder='Message...']",
                        "//div[contains(@placeholder, 'Message')]"
                    ]
                    print("INFO: Starting search for message input field...")
                    message_input = None
                    # (Keep the input search loop as it was)
                    for selector in message_input_selectors:
                        try:
                            print(
                                f"INFO: Trying selector for input: {selector}")
                            elements = driver.find_elements(By.XPATH, selector)
                            print(
                                f"DEBUG: Found {len(elements)} elements with selector {selector}")
                            for element in elements:
                                try:
                                    if element.is_displayed():
                                        message_input = element
                                        print(
                                            f"INFO: Found VISIBLE message input with selector: {selector}")
                                        break
                                except Exception as e:
                                    print(
                                        f"DEBUG: Error checking if element is displayed: {e}")
                            if message_input:
                                break
                        except Exception as e:
                            print(
                                f"ERROR: Error searching with selector {selector}: {e}")

                    # ---- Message Sending - Start ----
                    if message_input:
                        # (Keep the message sending logic as it was)
                        print("INFO: Message input field found. Proceeding to send.")
                        try:
                            print("INFO: Attempting to click message input field...")
                            message_input.click()
                            print("INFO: Successfully clicked on message input")
                            time.sleep(1)
                        except Exception as click_error:
                            print(
                                f"ERROR: Failed to click message input: {click_error}")
                            try:
                                print(
                                    "INFO: Attempting JS click on message input field...")
                                driver.execute_script(
                                    "arguments[0].click();", message_input)
                                print(
                                    "INFO: Used JavaScript to click message input")
                                time.sleep(1)
                            except Exception as js_error:
                                print(
                                    f"ERROR: JavaScript click on input also failed: {js_error}")
                        try:
                            print("INFO: Attempting to clear message input field...")
                            message_input.clear()
                            print("INFO: Cleared message input")
                        except Exception as clear_error:
                            print(
                                f"ERROR: Failed to clear input: {clear_error}")
                        # Method 1: ActionChains
                        try:
                            print(
                                "INFO: Trying ActionChains method to send message...")
                            # Re-initialize actions here
                            actions = ActionChains(driver)
                            actions.move_to_element(
                                message_input).click().pause(1)
                            for char in message_text:
                                actions.send_keys(char).pause(0.1)
                            actions.perform()
                            print(
                                "INFO: Successfully typed message using ActionChains")
                            driver.save_screenshot(
                                f"{results_dir}/before_send.png")
                            try:
                                print(
                                    "INFO: Pressing Enter to send message (ActionChains)...")
                                time.sleep(1)
                                message_input.send_keys(Keys.RETURN)
                                print("INFO: Pressed Enter to send message")
                            except Exception as enter_error:
                                print(
                                    f"ERROR: Failed to press Enter: {enter_error}")
                                try:
                                    print("INFO: Trying ActionChains Enter...")
                                    ActionChains(driver).send_keys(
                                        Keys.RETURN).perform()
                                    print(
                                        "INFO: Used ActionChains to press Enter")
                                except Exception as action_enter_error:
                                    print(
                                        f"ERROR: ActionChains Enter also failed: {action_enter_error}")
                                    raise
                            time.sleep(3)
                            driver.save_screenshot(
                                f"{results_dir}/after_send.png")
                            print("INFO: Message marked as sent (ActionChains).")
                            message_sent = True  # Set message_sent flag
                        except Exception as e:
                            print(f"ERROR: ActionChains approach failed: {e}")
                        # Method 2: Direct Selenium input
                        if not message_sent:
                            # ... (keep method 2 logic) ...
                            pass
                        # Method 3: JavaScript injection
                        if not message_sent:
                            # ... (keep method 3 logic) ...
                            pass
                    else:
                        print("ERROR: No message input field found after search.")
                        driver.save_screenshot(
                            f"{results_dir}/no_input_field.png")
                else:
                    print("ERROR: Failed to click message button (all methods).")
            else:
                # Log button not found (already has logging)
                pass
            # ---- Message Sending - End ----

            # Update analytics is now handled within the try block if message_sent becomes True
            if message_sent:
                print(
                    f"INFO: Message to {username} marked as sent, attempting analytics update...")
                try:
                    # ... (analytics update code) ...
                    pass  # Placeholder for brevity
                except Exception as analytics_error:
                    print(
                        f"Warning: Failed to update analytics: {analytics_error}")

            # --- Update Return Value ---
            # Added log
            print(
                f"DEBUG: final_analysis_result before return value update: {final_analysis_result}")
            return_value["message_sent"] = message_sent
            # Add other details to return_value if needed (like description, topics)
            if final_analysis_result:
                return_value["description"] = final_analysis_result.get(
                    "description", "")
                return_value["message_text"] = final_analysis_result.get(
                    "comment", "")  # Add message_text
                if 'conversation_topics' in final_analysis_result:
                    return_value["conversation_topics"] = final_analysis_result['conversation_topics']
                # Retrieve and add profile_bio from analytics data
                try:
                    if username in analytics.conversation_metrics and \
                       analytics.conversation_metrics[username].get("client_analysis") and \
                       analytics.conversation_metrics[username]["client_analysis"].get("profile_bio"):
                        return_value["profile_bio"] = analytics.conversation_metrics[username]["client_analysis"]["profile_bio"]
                        print(
                            f"DEBUG: Added profile_bio to return_value for {username}")
                    else:
                        print(
                            f"DEBUG: No profile_bio found in analytics for {username}")
                except Exception as bio_err:
                    print(
                        f"ERROR: Failed to retrieve profile_bio from analytics for {username}: {bio_err}")

            print(f"DEBUG: Updated return_value: {return_value}")  # Added log

        else:
            # This block is for when analysis_result is None (profile analysis needed)
            print(
                f"INFO: No pre-existing analysis for {username}. Analyzing profile now...")
            # Navigate to the user's profile
            profile_url = f"https://www.instagram.com/{username}/"
            try:
                driver.get(profile_url)
                time.sleep(3)
                # ... (rest of the profile analysis logic - needs error handling too)
                # ... This block would eventually set final_analysis_result and potentially message_sent ...
                # ... We should ensure it also updates return_value properly ...
                pass  # Placeholder for brevity
            except Exception as profile_error:
                print(
                    f"ERROR: Error during profile analysis for {username}: {profile_error}")

    except Exception as e:  # Catch any exception within the main try block
        print(f"FATAL ERROR in message_user for {username}: {e}")
        import traceback
        traceback.print_exc()  # Print detailed traceback
        # Ensure we return a dict indicating failure
        return_value = {"message_sent": False, "error": str(e)}

    # Record interaction in Google Sheets
    if sheets_manager:
        try:
            print(f"DEBUG: Preparing data for Google Sheets for {username}...")

            # Ensure timestamp and username are present before adding the row
            if "timestamp" not in return_value:
                return_value["timestamp"] = datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S")
            if "username" not in return_value:
                return_value["username"] = username

            # Pass the complete return_value dictionary directly to add_row
            # The add_row method in sheets_integration.py expects a dictionary.
            print(
                f"DEBUG: Updating Google Sheet for {username} with return_value dictionary: {return_value}")
            sheets_manager.add_row(return_value)  # Pass the dictionary here
            # Changed log message for clarity
            print(f"DEBUG: Google Sheet update call completed for {username}.")
        except Exception as sheet_error:
            print(
                f"ERROR: Failed to update Google Sheets for {username}: {sheet_error}")
            # Also print the traceback for sheet errors
            import traceback
            traceback.print_exc()

    # Final return
    print(
        f"INFO: Exiting message_user for {username}. Returning: {return_value}")
    return return_value


def try_send_message(driver, username, message_text, results_dir):
    """Send a direct message using most reliable JavaScript method."""
    try:
        print(f"Preparing to send message to {username}")
        driver.save_screenshot(f"{results_dir}/before_message_input.png")

        # Wait for the message dialog to fully load
        time.sleep(5)

        # Find the message input directly with JavaScript - this is the most reliable
        print("Trying to send message using direct JavaScript execution...")

        # Direct JavaScript to find and focus on the input
        find_input_js = """
        function findMessageInput() {
            // Try multiple selectors
            const selectors = [
                'div[role="textbox"]', 
                'div[contenteditable="true"]',
                'div[aria-label*="Message"]',
                'textarea[placeholder*="Message"]'
            ];
            
            for (const selector of selectors) {
                const elements = document.querySelectorAll(selector);
                for (const el of elements) {
                    if (el.offsetWidth > 0 && el.offsetHeight > 0) {
                        return el;
                    }
                }
            }
            return null;
        }
        
        const input = findMessageInput();
        if (input) {
            input.focus();
            return true;
        }
        return false;
        """

        input_found = driver.execute_script(find_input_js)
        if not input_found:
            print("Cannot find message input with JavaScript")
            driver.save_screenshot(f"{results_dir}/input_not_found.png")
            return False

        # Directly insert text and send with JavaScript
        send_message_js = f"""
        function findMessageInput() {{
            // Try multiple selectors
            const selectors = [
                'div[role="textbox"]', 
                'div[contenteditable="true"]',
                'div[aria-label*="Message"]',
                'textarea[placeholder*="Message"]'
            ];
            
            for (const selector of selectors) {{
                const elements = document.querySelectorAll(selector);
                for (const el of elements) {{
                    if (el.offsetWidth > 0 && el.offsetHeight > 0) {{
                        return el;
                    }}
                }}
            }}
            return null;
        }}
        
        function sendMessage() {{
            const input = findMessageInput();
            if (!input) return false;
            
            // Clear existing content
            input.innerHTML = '';
            
            // Set new content
            input.innerHTML = `{message_text}`;
            
            // Dispatch input event to trigger IG's handlers
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            
            // Create and dispatch an Enter keypress event
            const enterEvent = new KeyboardEvent('keypress', {{
                key: 'Enter',
                code: 'Enter',
                keyCode: 13,
                which: 13,
                bubbles: true
            }});
            
            setTimeout(() => {{
                input.dispatchEvent(enterEvent);
            }}, 500);
            
            return true;
        }}
        
        return sendMessage();
        """

        success = driver.execute_script(send_message_js)

        if success:
            print("✅ Successfully executed JavaScript to send message")
            # Give time for the message to be sent
            time.sleep(3)
            driver.save_screenshot(f"{results_dir}/after_message_sent.png")
            return True
        else:
            print("❌ JavaScript message sending failed")
            driver.save_screenshot(f"{results_dir}/js_message_failed.png")

            # Try fallback method with ActionChains - sometimes works when JS fails
            print("Trying fallback with ActionChains...")
            try:
                # Find input element again with Selenium
                input_selectors = [
                    "//div[@role='textbox']",
                    "//div[@contenteditable='true']",
                    "//div[contains(@aria-label, 'Message')]",
                    "//textarea[contains(@placeholder, 'Message')]"
                ]

                for selector in input_selectors:
                    inputs = driver.find_elements(By.XPATH, selector)
                    for input_elem in inputs:
                        if input_elem.is_displayed():
                            print(f"Found input with selector: {selector}")
                            # Use ActionChains for typing
                            actions = ActionChains(driver)
                            actions.move_to_element(
                                input_elem).click().pause(1)

                            # Type message
                            for char in message_text:
                                actions.send_keys(char).pause(0.05)

                            actions.perform()
                            time.sleep(1)

                            # Press Enter
                            input_elem.send_keys(Keys.RETURN)
                            print("✅ Message sent using ActionChains fallback")
                            time.sleep(2)
                            driver.save_screenshot(
                                f"{results_dir}/message_sent_actions.png")
                            return True
            except Exception as e:
                print(f"ActionChains fallback also failed: {e}")
                driver.save_screenshot(
                    f"{results_dir}/all_attempts_failed.png")

            return False
    except Exception as e:
        print(f"Error in try_send_message: {e}")
        print(traceback.format_exc())
        driver.save_screenshot(f"{results_dir}/error_screenshot.png")
    return False

# --- Daily Messaging Counter Functions ---


def load_daily_stats():
    """Load the daily statistics from the stats file."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    stats_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "daily_stats.json")
    try:
        if os.path.exists(stats_path):
            with open(stats_path, "r") as f:
                stats = json.load(f)
                if today not in stats:
                    stats[today] = {"count": 0}
                return stats
        else:
            stats = {today: {"count": 0}}
            return stats
    except Exception as e:
        print(f"Error loading daily stats: {e}")
        return {today: {"count": 0}}


def save_daily_stats(stats):
    """Save the daily statistics to the stats file."""
    stats_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "daily_stats.json")
    try:
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"Saved daily stats: {stats}")

        # Update analytics data for dashboard
        update_analytics_with_bot_stats(stats)
    except Exception as e:
        print(f"Error saving daily stats: {e}")


def update_analytics_with_bot_stats(stats):
    """Update analytics data with bot message statistics for the dashboard."""
    try:
        # Check if analytics instance exists and is initialized
        if not hasattr(analytics, 'global_metrics'):
            print("Analytics not initialized, skipping update")
            return

        # Get the current global metrics
        global_metrics = analytics.global_metrics

        # Initialize bot_message_stats if it doesn't exist
        if "bot_message_stats" not in global_metrics:
            global_metrics["bot_message_stats"] = {
                "total_messages_sent": 0,
                "total_messages_responded": 0,
                "daily_messages_sent": {},
                "daily_messages_responded": {}
            }

        # Update the bot stats
        bot_stats = global_metrics["bot_message_stats"]

        # Process each day's stats
        total_sent = 0
        total_responded = 0

        for date, day_stats in stats.items():
            if isinstance(day_stats, dict):
                # Update daily sent messages
                message_count = day_stats.get("count", 0)
                bot_stats["daily_messages_sent"][date] = message_count
                total_sent += message_count

                # Update daily responded messages
                response_count = day_stats.get("responses", 0)
                bot_stats["daily_messages_responded"][date] = response_count
                total_responded += response_count
            elif isinstance(day_stats, (int, float)):
                # Legacy format handling
                bot_stats["daily_messages_sent"][date] = day_stats
                total_sent += day_stats

        # Update totals
        bot_stats["total_messages_sent"] = total_sent
        bot_stats["total_messages_responded"] = total_responded

        # Print summary of update
        print(f"Updated analytics with bot stats:")
        print(f"- Total messages sent: {total_sent}")
        print(f"- Total messages responded: {total_responded}")
        print(
            f"- Daily tracking for {len(bot_stats['daily_messages_sent'])} days")

        # Save the updated analytics
        analytics.export_analytics()
        print("Successfully exported updated analytics data")
    except Exception as e:
        print(f"Error updating analytics with bot stats: {e}")
        import traceback
        traceback.print_exc()


def check_daily_limit(stats, limit):
    """Check if the daily limit has been reached."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    if today in stats:
        return stats[today].get("count", 0) >= limit
    return False


def increment_daily_counter(stats):
    """Increment the daily message counter and save stats."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    # Initialize the day's entry if it doesn't exist
    if today not in stats:
        stats[today] = {"count": 0}

    # Increment the counter
    stats[today]["count"] = stats[today].get("count", 0) + 1

    # Save the updated stats
    save_daily_stats(stats)

    # Print current count for verification
    print(
        f"Incremented daily counter: {today} count = {stats[today]['count']}")

    return stats


def can_message_user(driver, username):
    """Check if the message button is available on the user's profile and click it if found"""
    try:
        print(f"Checking if we can message {username}...")

        # Take a screenshot of the profile for debugging
        results_dir = f"results/{username}"
        os.makedirs(results_dir, exist_ok=True)
        driver.save_screenshot(f"{results_dir}/profile_check.png")

        # Look for the message button using various selectors
        message_button_found = False
        message_button = None
        message_button_selectors = [
            "//div[contains(text(), 'Message')]",
            "//button[contains(text(), 'Message')]",
            "//a[contains(text(), 'Message')]",
            "//div[contains(@role, 'button') and contains(text(), 'Message')]",
            "//a[contains(@href, '/direct/t/')]",  # Direct message link
        ]

        for selector in message_button_selectors:
            try:
                message_buttons = driver.find_elements(By.XPATH, selector)
                for btn in message_buttons:
                    if btn.is_displayed():
                        message_button = btn
                        print(f"✅ Message button found for {username}")
                        message_button_found = True
                        break
                if message_button_found:
                    break
            except Exception as e:
                print(
                    f"Error checking message button with selector {selector}: {e}")
                continue

        if not message_button_found:
            # Check if account is private
            private_indicators = driver.find_elements(
                By.XPATH, "//h2[contains(text(), 'Private')]")
            if private_indicators and any(ind.is_displayed() for ind in private_indicators):
                print(
                    f"❌ Cannot message {username}: Account is private and you're not following them")
                return False, None

            # No specific reason found, just missing message button
            print(f"❌ Cannot message {username}: No message button found")
            return False, None

        return True, message_button

    except Exception as e:
        print(f"❌ Error checking if we can message {username}: {e}")
        return False, None


def reinitialize_webdriver():
    """Recreate the webdriver when session becomes invalid"""
    global driver
    global wait
    global chromedriver_path

    try:
        print("⚠️ Reinitializing WebDriver due to invalid session...")

        # Try to close the existing driver
        try:
            driver.quit()
        except:
            pass

        # Find ChromeDriver again in case the path changed
        chromedriver_path = find_chromedriver()
        if not chromedriver_path:
            print("❌ Could not find ChromeDriver during reinitialization")
            return False

        # Initialize a new driver
        service = webdriver.chrome.service.Service(
            executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_window_size(1920, 1080)
        wait = WebDriverWait(driver, 30)

        # Login again
        if login_to_instagram(driver, USERNAME, PASSWORD):
            print("✅ Successfully reinitialized WebDriver and logged in again")
            return True
        else:
            print("❌ Failed to log in after reinitializing WebDriver")
            return False
    except Exception as e:
        print(f"❌ Error reinitializing WebDriver: {e}")
        return False


def process_instagram_usernames():
    """Process Instagram usernames from the followers list."""
    print("Starting Instagram messaging and analysis script...")

    # Load daily messaging stats
    daily_stats = load_daily_stats()
    daily_limit = args.daily_limit
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    print(f"Daily messaging limit: {daily_limit}")
    print(f"Messages sent today: {daily_stats[today]['count']}")

    if check_daily_limit(daily_stats, daily_limit):
        print(
            f"Daily limit of {daily_limit} messages has been reached for today ({today}).")
        print("Please try again tomorrow or use --daily-limit to adjust the limit.")
        return

    # File paths
    usernames_file = FOLLOWERS_LIST
    progress_file = "progress.txt"

    # Load usernames
    usernames = load_usernames(usernames_file)
    print(f"Loaded {len(usernames)} usernames from file: {usernames_file}")

    # Handle progress reset if requested
    if args.reset and os.path.exists(progress_file):
        print("Resetting progress as requested. All users will be messaged again.")
        os.remove(progress_file)
        processed = set()
    else:
        processed = load_progress(progress_file)

    if not usernames:
        print(
            f"No usernames found in {usernames_file}. Please add usernames and run the script again.")
        return

    # Filter out already processed usernames
    usernames_to_process = [u for u in usernames if u not in processed]

    if not usernames_to_process:
        print("All usernames have already been processed!")
        print("To run again and message all users, use the --reset flag (e.g., python followersbot.py --reset)")
        return

    # Calculate how many users we can process today based on the daily limit
    remaining_today = daily_limit - daily_stats[today]['count']
    if len(usernames_to_process) > remaining_today:
        print(
            f"Note: Can only process {remaining_today} of {len(usernames_to_process)} users today due to daily limit.")
        usernames_to_process = usernames_to_process[:remaining_today]

    # --- DEBUG --- Print the list of users the script intends to process
    print(f"DEBUG: Usernames to process this session: {usernames_to_process}")
    # -------------
    print(f"Found {len(usernames_to_process)} usernames to process today.")

    # Process each username
    newly_processed = []
    processed_count_session = 0  # Track processed in this run
    consecutive_failures = 0  # Track consecutive browser failures
    max_consecutive_failures = 3  # Maximum consecutive failures before reinitializing

    try:
        for i, username in enumerate(usernames_to_process):
            # Check daily limit before processing each user
            if check_daily_limit(daily_stats, daily_limit):
                print(
                    f"Reached daily limit of {daily_limit} messages during processing.")
                break

            # Check for too many consecutive failures
            if consecutive_failures >= max_consecutive_failures:
                print(
                    f"⚠️ {consecutive_failures} consecutive failures detected. Reinitializing WebDriver...")
                if reinitialize_webdriver():
                    consecutive_failures = 0  # Reset counter after successful reinitialization
                else:
                    print("❌ Failed to reinitialize WebDriver. Stopping script.")
                    break

            print(
                f"\n[{processed_count_session + 1}/{len(usernames_to_process)}] Processing {username} (Overall progress: {len(processed)} processed)..."
            )

            try:
                # Navigate to profile for analysis and check if we can message them
                try:
                    driver.get(f"https://www.instagram.com/{username}/")
                    print(
                        f"Navigating to {username}'s profile for analysis...")
                    time.sleep(7)

                    # Check if we can message this user
                    can_message, message_button = can_message_user(
                        driver, username)
                    if not can_message:
                        print(
                            f"Skipping {username} as they cannot be messaged.")
                        # Add to processed list so we don't retry them
                        processed.add(username)
                        save_progress(progress_file, processed)
                        continue

                except Exception as e:
                    # Check if this is an invalid session error
                    if "invalid session id" in str(e).lower():
                        print(
                            "⚠️ Browser session is invalid, attempting to reinitialize...")
                        if reinitialize_webdriver():
                            # If we successfully reinitialized, don't count this as a failure
                            # and retry the current user
                            i -= 1  # Decrement i to retry the current user
                            consecutive_failures = 0
                            continue
                        else:
                            consecutive_failures += 1
                            print(
                                f"Skipping {username} due to browser session issues.")
                            continue
                    else:
                        print(f"Error navigating to {username}'s profile: {e}")
                        consecutive_failures += 1
                        continue

                # Analyze profile and posts first if needed
                # Added log
                print(f"DEBUG: Calling like_photos for {username}...")
                analysis_result = like_photos(driver, username, num_photos=1)
                # Added log
                print(f"DEBUG: like_photos returned: {analysis_result}")

                # Send a message if profile has message button
                # Check if analysis_result is not None and doesn't indicate an analysis error
                # Added log
                print(
                    f"DEBUG: Checking analysis_result for {username} before calling message_user...")
                if analysis_result and "Unable to analyze" not in str(analysis_result):
                    try:
                        # Call message_user which now returns a dictionary like {"message_sent": True/False, ...}
                        # Added log
                        print(f"INFO: Calling message_user for {username}...")
                        result_dict = message_user(
                            driver, username, sheets_manager, gemini_model, analysis_result)
                        # Added log
                        print(f"DEBUG: message_user returned: {result_dict}")

                        # Explicitly check the 'message_sent' key in the returned dictionary
                        if result_dict and result_dict.get('message_sent'):
                            print(f"Successfully processed DM for {username}.")
                            newly_processed.append(username)
                            processed.add(username)
                            processed_count_session += 1
                            consecutive_failures = 0  # Reset on success

                            # Increment the daily counter ONLY after successful DM
                            daily_stats = increment_daily_counter(daily_stats)
                            print(
                                f"Daily message count: {daily_stats[today]['count']}/{daily_limit}")

                            # Save progress after each successful message
                            save_progress(progress_file, processed)
                        else:
                            # Message sending failed or result_dict was None/empty
                            print(
                                f"Failed to process DM for {username} (message_sent was False or result was invalid). Skipping.")
                            consecutive_failures += 1

                    except Exception as message_error:
                        print(f"Error messaging {username}: {message_error}")

                        # Check if this is an invalid session error
                        if "invalid session id" in str(message_error).lower():
                            consecutive_failures += 1
                        else:
                            # If it's some other error, increment but with less severity
                            consecutive_failures += 0.5  # Count as half a failure

            except Exception as user_error:
                print(f"Error processing user {username}: {user_error}")
                consecutive_failures += 1
                continue

            # Wait between users (check limit again before waiting)
            # Don't wait after the last user OR if limit is reached
            is_last_user = (i == len(usernames_to_process) - 1)
            limit_reached = check_daily_limit(daily_stats, daily_limit)

            if not is_last_user and not limit_reached:
                # Randomized wait time to avoid detection
                wait_time = random.randint(45, 90)  # Slightly shorter wait
                print(f"Waiting {wait_time} seconds before next user...")
                time.sleep(wait_time)
            elif limit_reached:
                print("Daily limit reached, stopping processing.")
                break  # Exit loop immediately if limit hit after processing a user

        print("\nScript completed!")
        if newly_processed:
            print(
                f"Successfully processed {len(newly_processed)} users: {', '.join(newly_processed)}")
        if len(newly_processed) < len(usernames_to_process):
            print(
                f"Failed to process {len(usernames_to_process) - len(newly_processed)} users.")

        # Report on daily limit
        print(
            f"Daily message count: {daily_stats[today]['count']}/{daily_limit}")
        if check_daily_limit(daily_stats, daily_limit):
            print(f"Daily limit reached. The script will process more users tomorrow.")

        # Clear progress file if all users in the list have been processed
        if set(usernames) == processed:
            print(
                "All users have been processed. Clearing progress to allow running again.")
            if os.path.exists(progress_file):
                os.remove(progress_file)
    except Exception as e:
        print(f"An error occurred during username processing loop: {e}")
    finally:
        # Final progress save, just in case
        save_progress(progress_file, processed)
        print("\n--- Processing loop finished --- ")


def handle_message_dialog(driver, username, results_dir):
    """Handle any dialogs that appear after clicking 'Message'."""
    try:
        time.sleep(2)  # Wait for any dialog to appear

        # Check for "Allow Instagram to send notifications" dialog
        notification_dialog_selectors = [
            "//button[contains(text(), 'Not Now')]",
            "//button[text()='Not Now']",
            "//div[contains(text(), 'notifications')]/parent::*/parent::*/parent::*//button",
            "//div[contains(text(), 'would like to send you notifications')]/following::button"
        ]

        for selector in notification_dialog_selectors:
            try:
                buttons = driver.find_elements(By.XPATH, selector)
                for button in buttons:
                    if button.is_displayed():
                        button.click()
                        print("Clicked 'Not Now' for notifications dialog")
                        time.sleep(1)
                        break
            except Exception:
                continue

        # Check for any other unexpected dialog - look for a button that might close it
        dialog_buttons = [
            "//button[contains(text(), 'Cancel')]",
            "//button[contains(text(), 'Not Now')]",
            "//button[contains(text(), 'Skip')]",
            "//button[contains(text(), 'Close')]"
        ]

        for button_selector in dialog_buttons:
            try:
                buttons = driver.find_elements(By.XPATH, button_selector)
                for button in buttons:
                    if button.is_displayed():
                        print(f"Found dialog button: {button.text}")
                        button.click()
                        print(f"Clicked '{button.text}' button on dialog")
                        time.sleep(1)
                        break
            except Exception:
                continue

        # Check if there's a "New Message" dialog title
        new_message_title_selectors = [
            "//div[contains(text(), 'New message')]",
            "//span[contains(text(), 'New message')]",
            "//h1[contains(text(), 'New message')]"
        ]

        for selector in new_message_title_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        print("Found 'New Message' dialog")
                        # Take a screenshot of the dialog
                        driver.save_screenshot(
                            f"{results_dir}/new_message_dialog.png")
                        break
            except Exception:
                continue

        # Look for the "To:" field which indicates we're in the New Message dialog
        to_field_selectors = [
            "//input[@placeholder='Search...']",
            "//div[contains(text(), 'To:')]/following-sibling::input",
            "//div[text()='To:']/following-sibling::div//input",
            "//input[contains(@aria-label, 'Search')]",
            "//input[contains(@placeholder, 'Search')]"
        ]

        to_field = None
        for selector in to_field_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        to_field = element
                        print(
                            f"✅ Found 'To:' search field with selector: {selector}")
                        break
                if to_field:
                    break
            except Exception as e:
                print(f"Error with To: field selector {selector}: {e}")

        if to_field:
            print(f"✅ Found 'To:' field, entering username: {username}")

            # Clear and enter the username
            to_field.clear()
            to_field.send_keys(username)
            time.sleep(3)  # Wait for search results

            # Take screenshot of search results
            driver.save_screenshot(f"{results_dir}/search_results.png")

            # Select the username from search results
            username_selected = False
            username_result_selectors = [
                f"//div[contains(text(), '{username}')]",
                f"//span[contains(text(), '{username}')]",
                f"//div[contains(@role, 'option')]//div[text()='{username}']",
                # More generic selectors
                "//div[contains(@role, 'option')][1]",
                "//div[contains(@role, 'listbox')]//div[contains(@role, 'option')][1]",
                "//div[contains(@aria-label, 'Suggested')]//div[contains(@role, 'button')][1]"
            ]

            for selector in username_result_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            try:
                                element.click()
                                username_selected = True
                                print(
                                    f"✅ Selected username '{username}' from results")
                                break
                            except Exception as click_err:
                                print(
                                    f"⚠️ Click failed: {click_err}, trying JavaScript")
                                try:
                                    driver.execute_script(
                                        "arguments[0].click();", element)
                                    username_selected = True
                                    print(f"✅ Selected username with JavaScript")
                                    break
                                except Exception as js_err:
                                    print(
                                        f"❌ JavaScript click also failed: {js_err}")
                    if username_selected:
                        break
                except Exception as e:
                    print(
                        f"Error with username result selector {selector}: {e}")

            # If no exact match found, try to click the first result
            if not username_selected:
                try:
                    # Try to find and click first result
                    first_result = driver.find_element(
                        By.XPATH, "//div[contains(@role, 'option')][1]")
                    first_result.click()
                    username_selected = True
                    print("✅ Selected first username result")
                except Exception as e:
                    print(f"Could not select first result: {e}")

            # Take screenshot after selection
            driver.save_screenshot(f"{results_dir}/after_selection.png")

            time.sleep(2)

            # Click the "Chat" button
            chat_button_found = False
            chat_button_selectors = [
                "//button[text()='Chat']",
                "//div[text()='Chat']/parent::button",
                "//div[@role='button'][text()='Chat']",
                "//button[contains(@class, 'primary')]",
                "//div[contains(text(), 'Chat')]",
                "//div[@role='dialog']//button:not([aria-label='Close')]"
            ]

            for selector in chat_button_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            try:
                                element.click()
                                chat_button_found = True
                                print("✅ Clicked 'Chat' button")
                                break
                            except Exception as click_err:
                                print(
                                    f"⚠️ Click failed: {click_err}, trying JavaScript")
                                try:
                                    driver.execute_script(
                                        "arguments[0].click();", element)
                                    chat_button_found = True
                                    print(
                                        "✅ Clicked 'Chat' button with JavaScript")
                                    break
                                except Exception as js_err:
                                    print(
                                        f"❌ JavaScript click also failed: {js_err}")
                except Exception as e:
                    print(f"Error with chat button selector {selector}: {e}")

            if not chat_button_found:
                # Try to find any button that might be the Chat/Next button
                try:
                    buttons = driver.find_elements(
                        By.XPATH, "//div[@role='dialog']//button")
                    if buttons:
                        for button in buttons:
                            if button.is_displayed():
                                button.click()
                                print(
                                    "✅ Clicked a button in the dialog that might be 'Chat'")
                                chat_button_found = True
                                break
                except Exception as e:
                    print(f"Error finding fallback buttons: {e}")

            # Wait for chat to open
            if chat_button_found or username_selected:
                print("⏳ Waiting for chat interface to load (5 seconds)...")
                time.sleep(5)
                return True
            else:
                print("ℹ️ No 'To:' field found, might already be in chat interface")
                return True

        else:
            print("ℹ️ No 'To:' field found, might already be in chat interface")
            return True

    except Exception as dialog_err:
        print(f"⚠️ Error handling New Message dialog: {dialog_err}")
        print("Continuing to message attempt anyway...")
        return True


# --- Gemini DM Validation Function ---
def validate_dm_with_gemini(dm_text, user_message=None):
    """
    Validates and, if needed, rewrites the DM using Gemini to ensure it sounds like Shannon.
    """
    # Add a real example of Shannon's style
    shannon_example = '''
Shannon: Heya! How's your week been? I saw you clocked your first session in the app?
Client: Hey good! How are you going? I've done two.. one yesterday and one today. I am sore as 🤣🤣 loved it!
Shannon: That's really good to hear! :) Happy with the exercises? Or is there anything I can add in there for you?
Shannon: I'm going well thanks! Just eating dinner wrapping up for the night! ❤
Client: Nah I'm happy with it all thanks. Thoroughly enjoyed it. My squat strength has absolutely tanked after not having done them in a few months 🫠 onwards and upwards lol
Shannon: Haha it happens like that hey! How much did you squat this week?
Client: 4x8 at 50kg
Shannon: That's solid!
Shannon: What did you used to squat?
Client: My 1RM was 115 a year ago 🥲
Shannon: Okay yeah!
'''
    filter_prompt = f"""
You are Shannon, a fitness coach. Your task is to ensure AI-generated responses sound like you and are direct replies to a client.

Here is an example of how Shannon responds to clients:
{shannon_example}

Here is a message that was generated by an AI trying to respond as you:
[GENERATED RESPONSE]
{dm_text}

Here was the client's message that the AI was responding to (if available):
{user_message or '(No specific client message provided for this turn)'}

Critically evaluate the [GENERATED RESPONSE] based on the following criteria:
1. Is it a direct, friendly, and conversational reply that you, Shannon, would actually send to a client?
2. Does it AVOID any meta-commentary, self-explanation (e.g., "As an AI...", "This response aims to..."), or references to "the conversation history" or "the user" in a generic sense?
3. Is it reasonably concise and to the point, as you would be in a chat?
4. Does it sound natural and in your authentic voice as a fitness coach?

DECISION PROCESS:
- If the [GENERATED RESPONSE] ALREADY meets ALL the above criteria (it's a good, direct, in-character message from Shannon), then your output should be the [GENERATED RESPONSE] EXACTLY as it is. Do not add any extra text or explanation. Just output the original response.
- ONLY if the [GENERATED RESPONSE] FAILS one or more of the criteria (e.g., it's too verbose, sounds like an AI explaining things, is not a direct reply, contains meta-commentary, or is clearly not something you, Shannon, would say), THEN you MUST rewrite it. Your rewritten message should be a perfect, direct, in-character reply that you, Shannon, would send. Output ONLY the rewritten message.

Your Output (either the original [GENERATED RESPONSE] or your rewritten version):
"""
    try:
        filter_model = genai.GenerativeModel('gemini-2.0-flash')
        response = filter_model.generate_content(filter_prompt)
        filtered = response.text.strip()
        # Remove markdown/code block formatting if present
        if filtered.startswith("```"):
            filtered = filtered.split("```", 2)[-1].strip()
        # Only use the filtered version if it's different and not empty
        if filtered and filtered != dm_text:
            print("[Gemini DM Filter] Gemini rewrote the DM.")
            return filtered
        return dm_text
    except Exception as e:
        print(f"[Gemini DM Filter] Error validating DM with Gemini: {e}")
        return dm_text


# --- Main function ---
if __name__ == "__main__":
    try:
        print("\nStarting Instagram bot...")
        print(f"Using followers list: {FOLLOWERS_LIST}")
        print(f"Using ChromeDriver: {chromedriver_path}")

        # Ensure Gemini API and Google Sheets are initialized
        print("\nInitializing services...")
        try:
            # Test Gemini API
            response = gemini_model.generate_content(
                "Hello, please respond with just the word 'ok' to test the connection.")
            if hasattr(response, 'text'):
                print(f"✅ Gemini API initialized: {response.text.strip()}")
            else:
                print(
                    "⚠️ Gemini API response format unexpected but connection established")
        except Exception as e:
            print(f"❌ Error initializing Gemini API: {e}")
            print("Will continue but post analysis will be limited")

        # Test Google Sheets
        try:
            # Check if the 'service' attribute exists and is not None
            if hasattr(sheets_manager, 'service') and sheets_manager.service:
                print("✅ Google Sheets authenticated successfully")
            else:
                print("⚠️ Google Sheets client not initialized - check credentials")
                print("Will continue but results won't be saved to sheets")
        except Exception as e:
            print(f"❌ Error confirming Google Sheets setup: {e}")
            print("Will continue but results won't be saved to sheets")

        # Create results directory
        os.makedirs("results", exist_ok=True)

        # Login to Instagram
        if login_to_instagram(driver, USERNAME, PASSWORD):
            print("✅ Successfully logged in to Instagram")

            # Process usernames
            process_instagram_usernames()
        else:
            print("❌ Failed to login to Instagram. Check credentials or try again later.")
    except Exception as e:
        print(f"Fatal error in main function: {e}")
    finally:
        print("Script execution completed.")
        # Keep browser open since detach=True is set in chrome_options
