import argparse
import sys

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

# --- Command Line Argument Parsing ---
parser = argparse.ArgumentParser(
    description='Instagram messaging and liking bot')
parser.add_argument('--reset', action='store_true',
                    help='Reset progress and message all users again')
parser.add_argument('--followers-list', type=str, default='instagram_followers.txt',
                    help='Path to the file containing the list of Instagram followers')
parser.add_argument('--daily-limit', type=int, default=300,
                    help='Maximum number of DMs to send per day (default: 300)')
args = parser.parse_args()

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

# Set the path to the ChromeDriver executable
chromedriver_path = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"

try:
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
    # Create the file if it doesn't exist
    if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
            f.write("# Add Instagram usernames below (one per line)\n")
            f.write("# Lines starting with # are ignored\n")
            print(f"Created new file: {file_path}")
        print(f"Please add usernames to {file_path} and run the script again.")
            return []

    # Read usernames from file
    usernames = []
    try:
        with open(file_path, 'r') as f:
            # Filter out empty lines and comments
            usernames = [line.strip() for line in f if line.strip()
                         and not line.strip().startswith('#')]
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
                        time.sleep(10)
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


def update_analytics_with_client_analysis(username, client_analysis):
    """Update analytics data with client profile analysis"""
    try:
        analytics_file = "analytics_data.json"

        # Load current analytics data
        try:
            with open(analytics_file, 'r') as f:
                analytics_data = json.load(f)
        except FileNotFoundError:
            analytics_data = {"conversations": {}, "global_metrics": {}}

        # Ensure the user exists in conversations
        if username not in analytics_data["conversations"]:
            analytics_data["conversations"][username] = {}

        # Add or update client analysis
        analytics_data["conversations"][username]["client_analysis"] = {
            "timestamp": client_analysis["analysis_timestamp"],
            "posts_analyzed": client_analysis["posts_analyzed"],
            "interests": client_analysis["interests"],
            "lifestyle_indicators": client_analysis["lifestyle_indicators"],
            "recent_activities": client_analysis["recent_activities"],
            "conversation_topics": client_analysis["conversation_topics"],
            "post_summaries": [
                {
                    "description": post.get("description", ""),
                    "activities": post.get("activities", []),
                    "interests": post.get("interests", [])
                }
                for post in client_analysis["post_analyses"]
            ]
        }

        # Save updated analytics data
        with open(analytics_file, 'w') as f:
            json.dump(analytics_data, f, indent=2)

                    print(
            f"Successfully updated analytics with client analysis for {username}")

        except Exception as e:
        print(f"Error updating analytics with client analysis: {e}")


def analyze_multiple_images_with_gemini(image_paths, username):
    """Analyze multiple Instagram post images and update analytics"""
    client_analysis = analyze_posts_with_gemini(
        image_paths, username)  # Rename the original function

    if client_analysis:
        # Update analytics with the analysis results
        update_analytics_with_client_analysis(username, client_analysis)

    return client_analysis


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
        except Exception as post_finder_error:
            print(f"Error finding posts: {post_finder_error}")
            driver.save_screenshot(
                f"{results_dir}/post_processing_error.png")

    except Exception as e:
        print(f"Error during post analysis: {e}")
        driver.save_screenshot(f"{results_dir}/like_photos_error.png")

    # Return the analysis result (or None if it failed)
    return final_analysis_result


def analyze_profile_page(driver, username, results_dir):
    """Analyze the full Instagram profile page for additional context."""
    try:
        # Take full page screenshot
        total_height = driver.execute_script(
            "return document.body.scrollHeight")
        driver.set_window_size(1920, total_height)
        profile_screenshot = f"{results_dir}/full_profile.png"
        driver.save_screenshot(profile_screenshot)

        profile_data = {
            "username": username,
            "analysis_timestamp": datetime.now().isoformat(),
            "profile_info": {
                "display_name": None,
                "bio": None,
                "website": None,
                "post_count": None,
                "follower_count": None,
                "following_count": None,
                "is_private": False,
                "is_verified": False,
                "has_highlights": False
            }
        }

        try:
            # Get display name
            name_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2"))
            )
            profile_data["profile_info"]["display_name"] = name_element.text
        except:
            print("Could not find display name")

        try:
            # Get bio
            bio_element = driver.find_element(By.CSS_SELECTOR, "._aa_c")
            profile_data["profile_info"]["bio"] = bio_element.text
        except:
            print("Could not find bio")

        try:
            # Get website if exists
            website_element = driver.find_element(
                By.CSS_SELECTOR, "a[rel='nofollow noopener noreferrer']")
            profile_data["profile_info"]["website"] = website_element.get_attribute(
                "href")
        except:
            print("Could not find website")

        try:
            # Get follower/following counts
            stats = driver.find_elements(By.CSS_SELECTOR, "span._ac2a")
            if len(stats) >= 3:
                profile_data["profile_info"]["post_count"] = stats[0].text
                profile_data["profile_info"]["follower_count"] = stats[1].text
                profile_data["profile_info"]["following_count"] = stats[2].text
        except:
            print("Could not find follower/following counts")

        # Check if profile is private
        try:
            private_indicator = driver.find_element(
                By.XPATH, "//h2[contains(text(), 'Private')]")
            profile_data["profile_info"]["is_private"] = private_indicator.is_displayed()
        except:
            pass

        # Check if profile is verified
        try:
            verified_badge = driver.find_element(
                By.CSS_SELECTOR, "span[title='Verified']")
            profile_data["profile_info"]["is_verified"] = verified_badge.is_displayed()
        except:
            pass

        # Check for story highlights
        try:
            highlights = driver.find_elements(By.CSS_SELECTOR, "div._aarf")
            profile_data["profile_info"]["has_highlights"] = len(
                highlights) > 0
        except:
            pass

        # Analyze profile with Gemini
        try:
            prompt = f"""
            Analyze this Instagram profile information and provide insights:

            Username: {username}
            Display Name: {profile_data["profile_info"]["display_name"]}
            Bio: {profile_data["profile_info"]["bio"]}
            Website: {profile_data["profile_info"]["website"]}
            Posts: {profile_data["profile_info"]["post_count"]}
            Followers: {profile_data["profile_info"]["follower_count"]}
            Following: {profile_data["profile_info"]["following_count"]}
            Private: {profile_data["profile_info"]["is_private"]}
            Verified: {profile_data["profile_info"]["is_verified"]}
            Has Highlights: {profile_data["profile_info"]["has_highlights"]}

            Provide analysis in the following format:
            PROFILE_TYPE: [Type of account - personal/business/creator etc]
            ENGAGEMENT_LEVEL: [Estimated engagement based on followers/posts]
            INTERESTS: [List potential interests based on bio and profile]
            PERSONALITY: [Personality indicators from bio and style]
            CONVERSATION_STARTERS: [2-3 potential conversation topics]
            """

            response = gemini_model.generate_content(prompt)

            # Parse Gemini response
            response_text = response.text
            sections = {
                "profile_type": re.search(r'PROFILE_TYPE:\s*(.*?)(?=\n[A-Z]+:|$)', response_text, re.DOTALL),
                "engagement_level": re.search(r'ENGAGEMENT_LEVEL:\s*(.*?)(?=\n[A-Z]+:|$)', response_text, re.DOTALL),
                "interests": re.search(r'INTERESTS:\s*(.*?)(?=\n[A-Z]+:|$)', response_text, re.DOTALL),
                "personality": re.search(r'PERSONALITY:\s*(.*?)(?=\n[A-Z]+:|$)', response_text, re.DOTALL),
                "conversation_starters": re.search(r'CONVERSATION_STARTERS:\s*(.*?)(?=$)', response_text, re.DOTALL)
            }

            profile_data["gemini_analysis"] = {}
            for key, match in sections.items():
                if match:
                    content = match.group(1).strip()
                    if key in ["interests", "conversation_starters"]:
                        profile_data["gemini_analysis"][key] = [
                            item.strip() for item in content.split('\n') if item.strip()]
                            else:
                        profile_data["gemini_analysis"][key] = content

    except Exception as e:
            print(f"Error analyzing profile with Gemini: {e}")

        return profile_data

    except Exception as e:
        print(f"Error analyzing profile page: {e}")
        return None


def message_user(driver, username, sheets_manager, gemini_client, analysis_result=None):
    """Send a direct message to an Instagram user after analyzing their profile."""
    results_dir = f"results/{username}"
    os.makedirs(results_dir, exist_ok=True)

    message_sent = False
    consecutive_failures = 0
    retry_count = 0
    final_analysis_result = None

    try:
        # Navigate to profile and analyze
        profile_url = f"https://www.instagram.com/{username}/"
            driver.get(profile_url)
            time.sleep(3)

        # Take screenshot and analyze full profile
        profile_data = analyze_profile_page(driver, username, results_dir)

        # Analyze posts if available (existing functionality)
        posts_analysis = None
        if analysis_result:
            posts_analysis = analysis_result
        else:
            # Look for posts (try for the top posts if available)
            posts = WebDriverWait(driver, 10).find_elements(
                By.XPATH, "//div[@role='button']/a[@role='link' and @tabindex='0']")

            image_paths = []
            max_posts_to_analyze = min(6, len(posts))

            if posts and len(posts) > 0:
                # Get the most recent 6 posts (or fewer if not available)
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
                    posts_analysis = analyze_multiple_images_with_gemini(
                        image_paths, username)

        # Combine analyses
        if posts_analysis and profile_data:
            final_analysis_result = {
                **posts_analysis,
                "profile_analysis": profile_data
            }
        elif profile_data:
            final_analysis_result = {
                "profile_analysis": profile_data,
                "description": f"Profile for {username}",
                "comment": f"Hey! Just checked out your profile. How's it going? 😊"
            }
        elif posts_analysis:
            final_analysis_result = posts_analysis
                    else:
            final_analysis_result = {
                "description": f"Profile for {username}",
                "comment": f"Hey! Just came across your profile. What's been keeping you busy lately? 😊"
            }

        # Update analytics with the combined analysis
        if final_analysis_result:
            update_analytics_with_client_analysis(
                username, final_analysis_result)

        # If we have an analysis result, proceed with sending the message
        if final_analysis_result:
            # Try to click the message button
            try:
                message_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[contains(text(), 'Message')]"))
                )
                    if message_button:
                    # Take screenshot before clicking the message button
                    before_click_screenshot = f"{results_dir}/before_message_button.png"
                    driver.save_screenshot(before_click_screenshot)

                    # Try to click the button
                    message_button.click()
                    time.sleep(3)  # Wait for the message interface to load

                    # Take screenshot after clicking the message button
                    after_click_screenshot = f"{results_dir}/after_message_button.png"
                    driver.save_screenshot(after_click_screenshot)

                    # Extract the comment to send
                    message_text = final_analysis_result.get("comment", "")
                    if not message_text:
                        message_text = "Hey! Just checked out your profile. How's it going? 😊"

                    # Ensure message text is string and handle None
                    if message_text is None:
                        message_text = "Hey! Just checked out your profile. How's it going? 😊"

                    # Send the message using a method with fallback mechanisms
                    handle_message_dialog(driver, username, results_dir)
                    message_sent = try_send_message(
                        driver, username, message_text, results_dir)

            except Exception as e:
                print(f"Error sending message to {username}: {e}")

        # Record the interaction regardless of whether the message was sent
        if sheets_manager and final_analysis_result:
            # Prepare expanded data for Google Sheets
            row_data = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "username": username,
                "message_sent": "Yes" if message_sent else "No",
                "message_text": final_analysis_result.get("comment", ""),
                "description": final_analysis_result.get("description", ""),
                "conversation_topics": ", ".join(final_analysis_result.get("conversation_topics", [])),
                "display_name": profile_data.get("profile_info", {}).get("display_name", "") if profile_data else "",
                "follower_count": profile_data.get("profile_info", {}).get("follower_count", "") if profile_data else "",
                "post_count": profile_data.get("profile_info", {}).get("post_count", "") if profile_data else "",
                "profile_type": profile_data.get("gemini_analysis", {}).get("profile_type", "") if profile_data else "",
                "engagement_level": profile_data.get("gemini_analysis", {}).get("engagement_level", "") if profile_data else "",
                "interests": ", ".join(profile_data.get("gemini_analysis", {}).get("interests", [])) if profile_data and "gemini_analysis" in profile_data else "",
            }
            sheets_manager.add_row(row_data)

        # Remove sensitive information before returning
        if final_analysis_result:
            # Create a clean copy for return
            sanitized_result = {
                "description": final_analysis_result.get("description", ""),
                "message_text": final_analysis_result.get("comment", ""),
                "message_sent": message_sent,
                "profile_analysis": final_analysis_result.get("profile_analysis", {})
            }

            # Add conversation topics if available
            if 'conversation_topics' in final_analysis_result:
                sanitized_result["conversation_topics"] = final_analysis_result['conversation_topics']

            return sanitized_result

        return {"message_sent": message_sent}

    except Exception as e:
        print(f"Error in message_user: {e}")
        return {"message_sent": message_sent}


def try_send_message(driver, username, message_text, results_dir):
    """Try different methods to send a message, from most reliable to least. Based on ic.py approach."""
    print(f"Attempting to send message to {username}...")
    message_sent = False

    # First approach: Use ActionChains to type character-by-character (most human-like)
    try:
        # Find the message input area by its specific attributes
                    message_input_selectors = [
                        "//div[@aria-label='Message' and @role='textbox']",
                        "//div[@contenteditable='true']",
                        "//div[contains(@aria-label, 'Message')]",
                        "//textarea[@placeholder='Message...']",
                        "//div[contains(@placeholder, 'Message')]"
                    ]

                    message_input = None
                    for selector in message_input_selectors:
            try:
                            elements = driver.find_elements(By.XPATH, selector)
                            for element in elements:
                                    if element.is_displayed():
                                        message_input = element
                                        print(
                            f"✅ Found message input with selector: {selector}")
                        break
                            if message_input:
                    break
            except Exception:
                continue

                    if message_input:
            # Click to focus the input
                            message_input.click()
                            time.sleep(1)

            # Clear any existing text first
                        try:
                            message_input.clear()
            except Exception:
                pass

            # Use ActionChains to type into the input field character by character
                            actions = ActionChains(driver)
            actions.move_to_element(message_input).click().pause(1)

            # Type character by character with small delays
                            for char in message_text:
                                actions.send_keys(char).pause(0.1)

                            actions.perform()
            print(
                f"✅ Typed message to {username} using ActionChains (character-by-character).")

            # Take a screenshot before sending
            driver.save_screenshot(f"{results_dir}/before_send.png")

            # Try to send by pressing Enter
                                time.sleep(1)
            message_input.send_keys(Keys.ENTER)
            print(f"✅ Pressed Enter to send message to {username}.")

            # Take a screenshot to verify
                            time.sleep(3)
            driver.save_screenshot(f"{results_dir}/message_sent.png")
            print(f"✅ Message sent to {username}. Screenshot saved.")
                            message_sent = True

            # If we received a reply, update stats
            if "New message from" in driver.page_source:
                got_response = True
                print(f"Detected a response from {username}!")

                # Update response stats
                try:
                    stats = load_daily_stats()
                    today = datetime.datetime.now().strftime("%Y-%m-%d")
                    if today not in stats:
                        stats[today] = {"count": 0}
                    if "responses" not in stats[today]:
                        stats[today]["responses"] = 0
                    stats[today]["responses"] += 1
                    save_daily_stats(stats)

                    # Also track the response in the analytics system
                    try:
                        # Get the message text if possible
                        user_response_text = "Response detected (content unavailable)"
                        response_elements = driver.find_elements(
                            By.XPATH, "//div[contains(@class, 'message-in')]//div[@class='_aa_a']")

                        if response_elements:
                            user_response_text = response_elements[-1].text

                        # Track as user message in analytics
                    analytics.analyze_message(
                        subscriber_id=username,
                            message_text=user_response_text,
                            message_type="user",
                            timestamp=datetime.datetime.now().isoformat(),
                            ig_username=username
                        )
                        print(f"Tracked user response in analytics")

                        # Check for coaching inquiries
                        coaching_phrases = ["coaching", "train me", "personal trainer", "workout plan",
                                            "how much", "cost", "price", "interested in", "sign up"]

                        ai_detection_phrases = ["are you a bot", "is this ai", "automated", "not a real person",
                                                "talking to ai", "chatbot", "is this a person"]

                        # Check for coaching inquiries
                        if any(phrase in user_response_text.lower() for phrase in coaching_phrases):
                            print("Coaching inquiry detected!")
                            analytics.global_metrics["coaching_inquiries"] = analytics.global_metrics.get(
                                "coaching_inquiries", 0) + 1

                        # Check for AI detection
                        if any(phrase in user_response_text.lower() for phrase in ai_detection_phrases):
                            print("AI detection in user message!")
                            analytics.global_metrics["ai_detections"] = analytics.global_metrics.get(
                                "ai_detections", 0) + 1

                    except Exception as e:
                        print(
                            f"Error tracking user response in analytics: {e}")
                except Exception as e:
                    print(f"Error updating response stats: {e}")

            return True
        else:
            print(f"❌ Could not find message input field for {username}")
            driver.save_screenshot(
                f"{results_dir}/message_input_not_found.png")

    except Exception as e:
        print(f"⚠️ ActionChains approach failed: {e}")
        driver.save_screenshot(f"{results_dir}/actionchains_error.png")

    # Second approach: Try direct Selenium input
    try:
        print("Trying direct Selenium input approach...")
        inputs = driver.find_elements(
            By.XPATH, "//div[@contenteditable='true']")
        if inputs:
            input_elem = inputs[0]
            input_elem.clear()
            input_elem.send_keys(message_text)
            time.sleep(1)
            input_elem.send_keys(Keys.ENTER)
            time.sleep(2)
            driver.save_screenshot(f"{results_dir}/message_sent_selenium.png")
            print(f"✅ Message sent to {username} using direct Selenium input.")
            message_sent = True
            return True
    except Exception as selenium_error:
        print(f"⚠️ Direct Selenium approach failed: {selenium_error}")

    # Third approach: JavaScript injection (last resort)
    try:
        print("Trying JavaScript injection approach...")
        potential_inputs = driver.find_elements(
            By.XPATH, "//div[@contenteditable='true']")
        if potential_inputs:
            input_elem = potential_inputs[0]
            # Set text via JavaScript
            driver.execute_script(
                "arguments[0].innerHTML = arguments[1];", input_elem, message_text)
                            time.sleep(1)
            # Trigger Enter key
            input_elem.send_keys(Keys.ENTER)
                            time.sleep(2)
            driver.save_screenshot(f"{results_dir}/message_sent_js.png")
            print(f"✅ Message sent to {username} using JavaScript approach.")
            message_sent = True
                            return True
    except Exception as js_error:
        print(f"⚠️ JavaScript approach failed: {js_error}")

    print(f"❌ All message sending approaches failed for {username}")
    driver.save_screenshot(f"{results_dir}/message_send_all_failed.png")
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

    try:
        print("⚠️ Reinitializing WebDriver due to invalid session...")

        # Try to close the existing driver
        try:
            driver.quit()
        except:
            pass

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
    usernames_file = args.followers_list
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
                analysis_result = like_photos(driver, username, num_photos=1)

                # Send a message if profile has message button
                if "Unable to analyze" not in str(analysis_result):
                    try:
                        success = message_user(
                            driver, username, sheets_manager, gemini_model, analysis_result)

                        if success:
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
                            print(
                                f"Failed to process DM for {username}. Skipping.")
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
                "//div[@role='dialog']//button:not([aria-label='Close'])"
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
                print("❌ Failed to proceed to chat, but will try to continue...")
                return False

        else:
            print("ℹ️ No 'To:' field found, might already be in chat interface")
            return True

    except Exception as dialog_err:
        print(f"⚠️ Error handling New Message dialog: {dialog_err}")
        print("Continuing to message attempt anyway...")
        return True


# --- Main function ---
if __name__ == "__main__":
    try:
        # Ensure Gemini API and Google Sheets are initialized
        print("Initializing services...")
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
