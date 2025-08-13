import json
import time
import logging
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
import traceback

# --- Configuration ---
ANALYTICS_FILE = "C:\\Users\\Shannon\\analytics_data.json"
FOLLOW_UP_INTERVAL_SECONDS = 3600  # Check every hour
INSTAGRAM_USERNAME = "cocos_connected"
INSTAGRAM_PASSWORD = "Shannonb3"
MAX_DAILY_MESSAGES = 50  # Rate limiting
MESSAGE_DELAY_SECONDS = 60  # Wait between messages
CHROME_DRIVER_PATH = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"
DEFAULT_TIMEOUT = 10
INSTAGRAM_URL = "https://www.instagram.com"
LOGIN_URL = "https://www.instagram.com/accounts/login/"
TAKE_SCREENSHOTS = False  # Set to False to avoid connection issues with screenshots

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("followup_manager.log"),  # Log to a file
        logging.StreamHandler()  # Also log to console
    ]
)
logger = logging.getLogger("followup_manager")

# Create a global driver variable that can be accessed by imported functions
global_driver = None


def random_delay():
    """Generate a random delay to simulate human interaction."""
    delay = random.uniform(1.0, 3.0)
    time.sleep(delay)


def safe_screenshot(driver, filename):
    """Take a screenshot but don't fail if it doesn't work"""
    if not TAKE_SCREENSHOTS:
        return False

    try:
        return driver.save_screenshot(filename)
    except Exception as e:
        logger.warning(f"Screenshot failed for {filename}: {e}")
        return False


def setup_driver():
    """Set up and return a Chrome WebDriver instance with robust options."""
    try:
        logger.info("Setting up WebDriver with enhanced options...")

        # Create result directory for screenshots if it doesn't exist
        os.makedirs("results", exist_ok=True)

        chrome_options = Options()

        # Performance options
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Window options
        chrome_options.add_argument("--start-maximized")

        # Notification and popup options
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")

        # Browser detection avoidance
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")

        # User agent to appear more like a regular browser
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36")

        # Additional options
        chrome_options.add_argument("--mute-audio")

        # Keep browser open after script ends
        chrome_options.add_experimental_option("detach", True)

        # Hide automation info
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Preferences
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,  # Block notifications
            "credentials_enable_service": False,  # Disable password saving
            "profile.password_manager_enabled": False  # Disable password manager
        })

        # Set the Chrome binary location to use the local Chrome in chrome-win64 folder
        chrome_binary_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chrome-win64\chrome.exe"
        if os.path.exists(chrome_binary_path):
            chrome_options.binary_location = chrome_binary_path
            logger.info(f"Using local Chrome binary at: {chrome_binary_path}")
        else:
            logger.warning(
                f"Local Chrome binary not found at {chrome_binary_path}, using system Chrome instead")

        # Create a new Chrome driver instance
        if os.path.exists(CHROME_DRIVER_PATH):
            service = Service(executable_path=CHROME_DRIVER_PATH)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            logger.warning(
                f"ChromeDriver not found at {CHROME_DRIVER_PATH}, trying without path")
            driver = webdriver.Chrome(options=chrome_options)

        # Set an implicit wait
        driver.implicitly_wait(10)
        logger.info("WebDriver setup complete.")

        # Take a screenshot to verify browser is open
        safe_screenshot(driver, "results/browser_started.png")

        # Set the global driver
        global global_driver
        global_driver = driver

        return driver
    except Exception as e:
        logger.error(f"Error setting up WebDriver: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def login_to_instagram(driver, username, password):
    """Login to Instagram using provided credentials with robust error handling."""
    try:
        # Navigate to Instagram login page
        logger.info(f"Navigating to login page...")
        driver.get(LOGIN_URL)
        time.sleep(5)  # Wait for page to load

        # Take screenshot of login page for debugging
        safe_screenshot(driver, "results/login_page.png")
        logger.info("Attempting login...")

        # Try multiple selectors for username field
        username_field_selectors = [
            (By.NAME, "username"),
            (By.XPATH, "//input[@name='username']"),
            (By.XPATH,
             "//input[@aria-label='Phone number, username, or email']"),
            (By.XPATH,
             "//input[@placeholder='Phone number, username, or email']"),
            (By.XPATH, "//input[contains(@placeholder, 'username')]"),
            (By.XPATH, "//input[contains(@placeholder, 'email')]"),
            # Often the first input in a form is username
            (By.XPATH, "//form//input[1]"),
        ]

        username_field = None
        for selector_type, selector_value in username_field_selectors:
            try:
                elements = driver.find_elements(selector_type, selector_value)
                for element in elements:
                    if element.is_displayed():
                        username_field = element
                        logger.info(
                            f"Found username field with selector: {selector_type}={selector_value}")
                        break
                if username_field:
                    break
            except Exception as e:
                logger.debug(
                    f"Selector {selector_type}={selector_value} failed: {e}")
                continue

        if not username_field:
            logger.error("Could not find username field with any selector")
            safe_screenshot(driver, "results/username_field_not_found.png")
            return False

        # Enter username
        username_field.clear()
        username_field.send_keys(username)
        logger.info(f"Entered username: {username}")
        random_delay()

        # Try multiple selectors for password field
        password_field_selectors = [
            (By.NAME, "password"),
            (By.XPATH, "//input[@name='password']"),
            (By.XPATH, "//input[@aria-label='Password']"),
            (By.XPATH, "//input[@placeholder='Password']"),
            (By.XPATH, "//input[@type='password']"),
            # Often the second input in a form is password
            (By.XPATH, "//form//input[2]"),
        ]

        password_field = None
        for selector_type, selector_value in password_field_selectors:
            try:
                elements = driver.find_elements(selector_type, selector_value)
                for element in elements:
                    if element.is_displayed():
                        password_field = element
                        logger.info(
                            f"Found password field with selector: {selector_type}={selector_value}")
                        break
                if password_field:
                    break
            except Exception:
                continue

        if not password_field:
            logger.error("Could not find password field with any selector")
            safe_screenshot(driver, "results/password_field_not_found.png")
            return False

        # Enter password
        password_field.clear()
        password_field.send_keys(password)
        logger.info("Entered password")
        random_delay()

        # Take screenshot before clicking login
        safe_screenshot(driver, "results/before_login_click.png")

        # Try multiple selectors for login button
        login_button_selectors = [
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Log in')]"),
            (By.XPATH, "//div[contains(text(), 'Log in')]/parent::button"),
            (By.XPATH, "//button[contains(text(), 'Log In')]"),
            (By.XPATH, "//form//button"),  # Generic - any button in a form
        ]

        login_button = None
        for selector_type, selector_value in login_button_selectors:
            try:
                elements = driver.find_elements(selector_type, selector_value)
                for element in elements:
                    if element.is_displayed():
                        login_button = element
                        logger.info(
                            f"Found login button with selector: {selector_type}={selector_value}")
                        break
                if login_button:
                    break
            except Exception:
                continue

        if not login_button:
            logger.error("Could not find login button with any selector")
            safe_screenshot(driver, "results/login_button_not_found.png")
            return False

        # Try multiple login click approaches
        login_successful = False

        # First attempt: standard click
        try:
            logger.info("Attempting standard click on login button...")
            time.sleep(1)
            login_button.click()
            logger.info("Standard click executed.")
            time.sleep(8)  # Wait for potential page change

            if "/accounts/login" not in driver.current_url:
                logger.info("Login successful after standard click.")
                login_successful = True
            else:
                logger.warning(
                    "Still on login page after standard click. Trying JS click...")
                safe_screenshot(driver, "results/login_failed_after_click.png")
        except Exception as click_err:
            logger.warning(
                f"Standard click failed: {click_err}. Trying JS click...")

        # Second attempt: JavaScript click
        if not login_successful:
            try:
                logger.info("Attempting JavaScript click on login button...")
                driver.execute_script("arguments[0].click();", login_button)
                logger.info("JavaScript click executed.")
                time.sleep(8)

                if "/accounts/login" not in driver.current_url:
                    logger.info("Login successful after JavaScript click.")
                    login_successful = True
                else:
                    logger.error("Still on login page after JavaScript click.")
                    safe_screenshot(
                        driver, "results/login_failed_after_js_click.png")
            except Exception as js_err:
                logger.error(f"JavaScript click failed: {js_err}")
                safe_screenshot(driver, "results/login_js_click_error.png")

        # Final check and handle popups if login was successful
        if login_successful:
            logger.info("Login successful overall.")
            handle_post_login_popups(driver)
            return True
        else:
            logger.error("Login failed overall.")
            return False

    except Exception as e:
        logger.error(f"Error during login: {e}")
        logger.error(traceback.format_exc())
        safe_screenshot(driver, "results/login_error.png")
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
                                logger.info(
                                    f"Clicked '{popup['name']}' popup dismiss button")
                                time.sleep(2)  # Wait for popup to close
                                break
                    except:
                        continue
            except Exception as e:
                logger.error(f"Error handling {popup['name']} popup: {e}")

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
                            logger.info(
                                f"Clicked generic popup dismiss button '{button.text}'")
                            time.sleep(2)
                            break
                except:
                    continue
        except Exception as e:
            logger.error(f"Error with generic popup handling: {e}")

        logger.info("Completed post-login popup handling")
        safe_screenshot(driver, "results/after_popup_handling.png")

    except Exception as e:
        logger.error(f"Error handling post-login popups: {e}")
        safe_screenshot(driver, "results/popup_handling_error.png")


def navigate_to_user(driver, username):
    """Navigate to a user's profile page."""
    # Use constants inside the function to ensure they're available when imported
    instagram_url = "https://www.instagram.com"

    try:
        # Enhanced debugging
        logger.info(f"Instagram username received: '{username}'")
        if not username or username.strip() == "":
            logger.error(
                "Empty username provided to navigate_to_user function")
            return False

        logger.info(f"Navigating to user profile: {username}")
        profile_url = f"{instagram_url}/{username}/"
        logger.info(f"Constructed profile URL: {profile_url}")

        # Try to navigate with a timeout
        logger.info(f"Attempting to navigate to URL...")
        try:
            driver.get(profile_url)
            logger.info(f"Driver.get() call completed")
        except Exception as nav_error:
            logger.error(f"Error during navigation: {nav_error}")
            return False

        random_delay()

        # Take screenshot of profile for debugging
        os.makedirs(f"results/{username}", exist_ok=True)
        safe_screenshot(driver, f"results/{username}/profile.png")

        # Log current URL after navigation
        try:
            current_url = driver.current_url
            logger.info(f"Current URL after navigation: {current_url}")

            # Check if we actually reached the profile
            if username.lower() not in current_url.lower():
                logger.warning(
                    f"Username not found in current URL after navigation")
        except Exception as e:
            logger.error(f"Error getting current URL: {e}")

        # Verify we're on the right profile by checking username
        try:
            # Try multiple selectors for username
            username_selectors = [
                "//h2[contains(@class, '_aacl')]",
                "//h1[contains(@class, '_aacl')]",
                "//div[contains(@class, '_aacl')][contains(@class, '_aad6')]",
                "//section//h2"
            ]

            profile_username = None
            for selector in username_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            profile_username = element
                            logger.info(
                                f"Found profile username: {element.text}")
                            break
                    if profile_username:
                        break
                except:
                    continue

            if profile_username:
                logger.info(f"Found profile: {profile_username.text}")
                if username.lower() not in profile_username.text.lower():
                    logger.warning(
                        f"Username mismatch: Expected '{username}', found '{profile_username.text}'")
            else:
                logger.warning(
                    f"Could not verify username for {username}, proceeding anyway")

            # Check if profile is private
            try:
                private_indicators = driver.find_elements(
                    By.XPATH, "//h2[contains(text(), 'Private')]")
                if private_indicators and any(p.is_displayed() for p in private_indicators):
                    logger.warning(
                        f"Profile for {username} appears to be private")
                    safe_screenshot(
                        driver, f"results/{username}/private_profile.png")
            except:
                pass

            return True
        except TimeoutException:
            logger.error(f"Could not verify profile for {username}")
            return False

    except Exception as e:
        logger.error(f"Error navigating to user profile: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def send_message(driver, username, message_text):
    """Send a direct message to the specified user."""
    # Create results directory for this user
    results_dir = f"results/{username}"
    os.makedirs(results_dir, exist_ok=True)

    try:
        logger.info(f"Preparing to send message to {username}")

        # Check if we're on the user's profile page, if not navigate there
        try:
            current_url = driver.current_url
            logger.info(f"Current URL before sending message: {current_url}")

            if not username.lower() in current_url.lower():
                logger.info(
                    f"Not on {username}'s profile, navigating there now")
                if not navigate_to_user(driver, username):
                    logger.error(f"Failed to navigate to {username}'s profile")
                    return {"success": False, "error": "Failed to navigate to user profile"}
                logger.info(f"Successfully navigated to {username}'s profile")
            else:
                logger.info(f"Already on {username}'s profile")
        except Exception as url_check_error:
            logger.error(f"Error checking current URL: {url_check_error}")
            # Try to navigate anyway as a fallback
            if not navigate_to_user(driver, username):
                logger.error(f"Failed to navigate to {username}'s profile")
                return {"success": False, "error": "Failed to navigate to user profile"}

        # Find and click the message button using multiple selectors
        message_button_selectors = [
            "//div[contains(text(), 'Message')]",
            "//button[contains(text(), 'Message')]",
            "//a[contains(text(), 'Message')]",
            "//div[contains(@role, 'button') and contains(text(), 'Message')]",
            "//a[contains(@href, '/direct/t/')]"  # Direct message link
        ]

        message_button = None
        for selector in message_button_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        message_button = element
                        logger.info(
                            f"Found message button with selector: {selector}")
                        break
                if message_button:
                    break
            except Exception:
                continue

        if not message_button:
            logger.error("Message button not found with any selector")
            safe_screenshot(
                driver, f"{results_dir}/message_button_not_found.png")
            return {"success": False, "error": "Message button not found"}

        # Take screenshot before clicking message button
        safe_screenshot(driver, f"{results_dir}/before_message_button.png")

        # Click the message button
        try:
            message_button.click()
            logger.info("Clicked message button")
            random_delay()
        except Exception as click_error:
            logger.warning(
                f"Standard click failed: {click_error}. Trying JavaScript click...")
            try:
                driver.execute_script("arguments[0].click();", message_button)
                logger.info("Clicked message button with JavaScript")
                random_delay()
            except Exception as js_error:
                logger.error(f"JavaScript click also failed: {js_error}")
                return {"success": False, "error": "Could not click message button"}

        # Take screenshot after clicking message button
        safe_screenshot(driver, f"{results_dir}/after_message_button.png")

        # Wait for message input field using multiple selectors
        message_input_selectors = [
            "//div[@role='textbox']",
            "//div[@contenteditable='true']",
            "//div[contains(@aria-label, 'Message')]",
            "//textarea[@placeholder='Message...']",
            "//div[contains(@placeholder, 'Message')]"
        ]

        message_input = None
        for selector in message_input_selectors:
            try:
                elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                for element in elements:
                    if element.is_displayed():
                        message_input = element
                        logger.info(
                            f"Found message input with selector: {selector}")
                        break
                if message_input:
                    break
            except Exception:
                continue

        if not message_input:
            logger.error("Message input field not found with any selector")
            safe_screenshot(
                driver, f"{results_dir}/message_input_not_found.png")
            return {"success": False, "error": "Could not find message input field"}

        # Click to focus the input
        message_input.click()
        time.sleep(1)

        # Try to clear any existing text
        try:
            message_input.clear()
        except Exception:
            pass

        # Take screenshot before typing
        safe_screenshot(driver, f"{results_dir}/before_typing.png")

        # Method 1: Use ActionChains to type character by character
        try:
            actions = ActionChains(driver)
            actions.move_to_element(message_input).click().pause(1)

            # Type character by character with small delays
            for char in message_text:
                actions.send_keys(char).pause(0.1)

            actions.perform()
            logger.info(f"Typed message using ActionChains")

            # Take screenshot after typing
            safe_screenshot(driver, f"{results_dir}/message_typed.png")

            # Wait briefly before sending
            random_delay()

            # Press Enter to send
            message_input.send_keys(Keys.RETURN)
            logger.info(f"Message sent to {username}: {message_text[:30]}...")

            # Wait for send to complete
            time.sleep(2)
            safe_screenshot(driver, f"{results_dir}/message_sent.png")

            return {"success": True}

        except Exception as e:
            logger.warning(
                f"ActionChains typing method failed: {e}. Trying method 2...")

            # Method 2: Try direct send_keys
            try:
                message_input.clear()
                message_input.send_keys(message_text)
                time.sleep(1)
                message_input.send_keys(Keys.ENTER)
                time.sleep(2)

                safe_screenshot(
                    driver, f"{results_dir}/message_sent_direct.png")
                logger.info(f"Message sent using direct send_keys")

                return {"success": True}

            except Exception as e2:
                logger.warning(
                    f"Direct send_keys method failed: {e2}. Trying method 3...")

                # Method 3: JavaScript injection (last resort)
                try:
                    driver.execute_script(
                        "arguments[0].innerHTML = arguments[1]", message_input, message_text)
                    time.sleep(1)
                    message_input.send_keys(Keys.ENTER)
                    time.sleep(2)

                    safe_screenshot(
                        driver, f"{results_dir}/message_sent_js.png")
                    logger.info(f"Message sent using JavaScript")

                    return {"success": True}

                except Exception as e3:
                    logger.error(
                        f"All message sending methods failed. Last error: {e3}")
                    return {"success": False, "error": "All message sending methods failed"}

    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


def send_follow_up_message(driver, username, message):
    """Main function to send a follow-up message to a user."""
    # If driver is None, try to use the global driver
    if driver is None:
        global global_driver
        if global_driver is not None:
            driver = global_driver
        else:
            logger.error(
                "No WebDriver available. Please initialize one first.")
            return {"success": False, "error": "No WebDriver available"}

    try:
        logger.info(f"Starting follow-up message process for {username}")

        # Validate parameters
        if not username or username.strip() == "":
            logger.error("Empty username provided to send_follow_up_message")
            return {"success": False, "error": "Empty username provided"}

        if not message or message.strip() == "":
            logger.warning("Empty message provided to send_follow_up_message")
            # Continue with empty message as it might be intentional

        # Navigate to user profile
        logger.info(f"Calling navigate_to_user for username: {username}")
        nav_result = navigate_to_user(driver, username)
        if not nav_result:
            logger.error(f"Navigation to user profile failed: {username}")
            return {"success": False, "error": f"Could not navigate to {username}'s profile"}
        logger.info(f"Navigation to {username}'s profile succeeded")

        # Send the message
        logger.info(f"Sending message to {username}")
        result = send_message(driver, username, message)

        # Log detailed result
        if result.get("success", False):
            logger.info(f"Successfully sent follow-up message to {username}")
        else:
            error = result.get("error", "Unknown error")
            logger.error(
                f"Failed to send follow-up message to {username}: {error}")

        return result

    except Exception as e:
        logger.error(f"Error in send_follow_up_message: {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


# Function to get the global driver (for external files to use)
def get_driver():
    """Get the global driver instance if available, otherwise set it up."""
    global global_driver
    if global_driver is None:
        global_driver = setup_driver()
    return global_driver


if __name__ == "__main__":
    driver = None
    try:
        logger.info("Starting Instagram followup manager...")

        # Initialize the browser
        driver = setup_driver()
        if not driver:
            logger.error("Failed to initialize WebDriver. Exiting.")
            exit(1)

        # Log in to Instagram
        if login_to_instagram(driver, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD):
            logger.info(
                "✅ Successfully logged in to Instagram. Browser will remain open.")
            logger.info(
                "You can now send messages from the analytics dashboard.")
            logger.info(
                "DO NOT CLOSE THIS WINDOW - it will remain open for messaging.")

            # Keep the browser window open indefinitely (or until manually closed)
            # The detach option should keep it open even when the script ends
            while True:
                # Sleep for 5 minutes and check if still running
                time.sleep(300)
                logger.info("Follow-up manager still running...")

        else:
            logger.error(
                "Failed to log in to Instagram. Check credentials and try again.")
            # Keep the browser open even if login failed
            logger.info("Browser will remain open despite login failure.")
            while True:
                time.sleep(300)
                logger.info(
                    "Follow-up manager still running despite login failure...")
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        # Don't quit the driver on error, keep browser open
        logger.info("Error occurred but browser window will remain open.")
        while True:
            try:
                time.sleep(300)
                logger.info("Follow-up manager still running despite error...")
            except:
                break
