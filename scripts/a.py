from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from time import sleep
import random
import logging
import time
import pytesseract
from PIL import Image
import io
import base64
import os
import json

# ----------------------------- Configuration -----------------------------

# Configure logging
logging.basicConfig(
    filename='instagram_bot.log',
    level=logging.DEBUG,  # Set to DEBUG for more detailed logs
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# **INSECURE: Hardcoded credentials (for demonstration purposes only)**
USERNAME = "cocos_pt_studio"
PASSWORD = "Shannonb3"

# **INSECURE: Hardcoded OpenAI API Key removed**

# Path to Tesseract executable
# **INSECURE: Hardcoded path to Tesseract (update if necessary)**
# For Windows users, specify the path where Tesseract is installed
# Example:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Update this path

# Set up ChromeDriver service
service = Service("C:/SeleniumDrivers/chromedriver.exe")  # Ensure this path is correct
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-notifications")  # Disable notifications
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-extensions")
# Uncomment the next line to run Chrome in headless mode (no GUI)
# chrome_options.add_argument("--headless")
driver = webdriver.Chrome(service=service, options=chrome_options)

# ----------------------------- Helper Functions -----------------------------

def close_popups(driver):
    """Closes any unexpected pop-ups that may interfere with interactions."""
    try:
        # Example: Close a generic pop-up with a close button
        close_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(@aria-label, 'Close')]"
            ))
        )
        close_button.click()
        logging.info("Closed a pop-up dialog.")
        sleep(1)
    except TimeoutException:
        # No pop-up found
        logging.debug("No pop-up to close.")
    except Exception as e:
        logging.error(f"Error while closing pop-ups: {e}")

def take_screenshot(driver, name="screenshot"):
    """Takes a screenshot of the current browser window."""
    timestamp = int(time.time())
    filename = f"{name}_{timestamp}.png"
    try:
        driver.save_screenshot(filename)
        logging.info(f"Screenshot saved as {filename}")
        return filename
    except Exception as e:
        logging.error(f"Failed to take screenshot: {e}")
        return None

def load_commented_users(filename='commented_users.json'):
    """Loads the set of commented users from a JSON file."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            return set(data)
    except FileNotFoundError:
        return set()
    except json.JSONDecodeError:
        logging.error("Error decoding JSON from the commented_users file.")
        return set()

def save_commented_users(commented_users, filename='commented_users.json'):
    """Saves the set of commented users to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(list(commented_users), f)
    except Exception as e:
        logging.error(f"Error saving commented users to file: {e}")

# ----------------------------- Image Analysis Functions -----------------------------

def analyze_image(image_path):
    """Extracts text from the image using OCR and returns it."""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        logging.info(f"OCR extracted text: {text.strip()}")
        return text.strip()
    except Exception as e:
        logging.error(f"Error during OCR image analysis: {e}")
        return ""

def generate_casual_question(extracted_text, username):
    """Generates a casual question based on the extracted text."""
    if not extracted_text:
        return "Nice as! Hows things?"
    
    # Simple keyword-based question generation
    keywords = ['birthday', 'vacation', 'food', 'party', 'work', 'friends', 'family', 'travel', 'holiday', 'weekend']

    # Find if any keyword is present in the extracted text
    for word in keywords:
        if word.lower() in extracted_text.lower():
            if word.lower() == 'birthday':
                return f"Happy Birthday, @{username}! How did you celebrate?"
            elif word.lower() in ['vacation', 'travel', 'holiday']:
                return f"Looks like you're on vacation, @{username}! Where are you visiting?"
            elif word.lower() == 'food':
                return f"That looks delicious, @{username}! What's the dish called?"
            elif word.lower() == 'party':
                return f"Looks like you're having a great time at a party, @{username}! Who's joining you?"
            elif word.lower() == 'work':
                return f"Busy day at work, @{username}? How's everything going?"
            elif word.lower() == 'friends':
                return f"Loving time with friends, @{username}! How long have you known them?"
            elif word.lower() == 'family':
                return f"Family time is the best, @{username}! How's everyone doing?"
            elif word.lower() == 'weekend':
                return f"Enjoying your weekend, @{username}? Any special plans?"

    # Default question if no keywords matched
    return "Nice as! Hows things?"

# ----------------------------- Core Functions -----------------------------

def login(driver, username, password):
    """Logs into Instagram using the provided credentials."""
    try:
        driver.get("https://www.instagram.com")
        logging.info("Opening Instagram...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        logging.info("Logging in...")
        sleep(5)  # Wait for login to process

        # Dismiss "Save Your Login Info?" dialog
        try:
            not_now_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(text(), 'Not Now')]"
                ))
            )
            not_now_btn.click()
            logging.info("Dismissed 'Save Your Login Info' dialog.")
            sleep(2)
        except TimeoutException:
            logging.info("'Save Your Login Info' dialog not found. Continuing...")

        # Dismiss "Turn on Notifications?" dialog
        try:
            not_now_btn_2 = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(text(), 'Not Now')]"
                ))
            )
            not_now_btn_2.click()
            logging.info("Dismissed 'Turn on Notifications' dialog.")
            sleep(2)
        except TimeoutException:
            logging.info("'Turn on Notifications' dialog not found. Continuing...")

    except TimeoutException:
        logging.error("Error: Login failed due to timeout.")
        take_screenshot(driver, "login_timeout")
        driver.quit()
        exit("Error: Login failed due to timeout.")
    except Exception as e:
        logging.error(f"Unexpected error during login: {e}")
        take_screenshot(driver, "login_error")
        driver.quit()
        exit(f"Unexpected error during login: {e}")

def navigate_home(driver):
    """Clicks the Home button to load the main feed and ensure stories appear."""
    try:
        home_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//a//*[name()='svg' and @aria-label='Home']/ancestor::a"
            ))
        )
        home_button.click()
        logging.info("Navigated to Home.")
        sleep(5)
    except TimeoutException:
        logging.error("Error: Could not navigate to Home.")
        take_screenshot(driver, "navigate_home_timeout")
        driver.quit()
        exit("Error: Navigation to Home failed.")
    except Exception as e:
        logging.error(f"Unexpected error during navigation to Home: {e}")
        take_screenshot(driver, "navigate_home_error")
        driver.quit()
        exit(f"Unexpected error during navigation to Home: {e}")

def interact_with_stories(driver):
    """Iterates through stories, analyzes content, generates tailored questions, and navigates to the next story."""
    MAX_STORIES = 20  # Limit to prevent excessive interactions
    story_count = 0
    commented_users = load_commented_users()
    MAX_RETRIES = 3  # Number of retries to find the comment box

    try:
        # Open the first story
        first_story = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[@role='presentation']//canvas/ancestor::div[@role='button']"
            ))
        )
        first_story.click()
        logging.info("Opened the first story.")
        sleep(random.uniform(2, 4))

        # Locate the body element to send keyboard inputs
        body = driver.find_element(By.TAG_NAME, 'body')

        while story_count < MAX_STORIES:
            try:
                # Close any unexpected pop-ups
                close_popups(driver)

                # Wait for the story content to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='presentation']"))
                )
                logging.info(f"Interacting with story #{story_count + 1}")

                # Extract the username of the current story's owner
                try:
                    username_element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((
                            By.XPATH, "//header//span[contains(@class, 'x1lliihq') and contains(@class, 'x193iq5w')]"
                        ))
                    )
                    username = username_element.text.strip()
                    logging.info(f"Current story belongs to user: {username}")
                except TimeoutException:
                    logging.warning("Username element not found. Skipping commenting.")
                    username = None
                except Exception as e:
                    logging.error(f"Error extracting username: {e}")
                    username = None

                # If username is found and not already commented on, proceed to comment
                if username and username not in commented_users:
                    # Capture screenshot
                    screenshot_path = take_screenshot(driver, f"story_{story_count + 1}")
                    if not screenshot_path:
                        logging.error("Failed to capture screenshot. Skipping this story.")
                        continue

                    # Analyze the image using OCR
                    extracted_text = analyze_image(screenshot_path)
                    logging.info(f"Extracted Text for story #{story_count + 1}: {extracted_text}")

                    # Generate a tailored, casual question
                    tailored_question = generate_casual_question(extracted_text, username)
                    logging.info(f"Generated question: {tailored_question}")

                    # Attempt to comment on the story
                    for attempt in range(MAX_RETRIES):
                        try:
                            comment_box = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((
                                    By.XPATH,
                                    "//textarea[@autocomplete='off' and starts-with(@placeholder, 'Reply to ')]"
                                ))
                            )
                            comment_box.click()
                            sleep(random.uniform(1, 2))
                            comment_box.clear()  # Clear any existing text
                            comment_box.send_keys(tailored_question)
                            comment_box.send_keys(Keys.ENTER)
                            logging.info(f"Commented on the story by user: {username} with question: '{tailored_question}'")
                            commented_users.add(username)
                            save_commented_users(commented_users)
                            sleep(random.uniform(2, 4))  # Wait after commenting
                            break  # Exit retry loop after successful comment
                        except TimeoutException:
                            logging.warning(f"Attempt {attempt + 1}: Comment box not found.")
                            sleep(1)
                        except Exception as e:
                            logging.error(f"Error while commenting on user {username}: {e}")
                    else:
                        logging.info(f"Comment box not found after {MAX_RETRIES} attempts. Skipping commenting for user: {username}")
                else:
                    if username:
                        logging.info(f"Already commented on user: {username}. Skipping commenting.")

                # Navigate to the next story using ARROW_RIGHT
                body.send_keys(Keys.ARROW_RIGHT)
                logging.info("Navigated to the next story using ARROW_RIGHT.")
                story_count += 1
                sleep(random.uniform(2, 4))  # Wait for the next story to load

            except TimeoutException:
                logging.info("No more stories to view or timed out waiting for the next story.")
                break
            except StaleElementReferenceException:
                logging.warning("StaleElementReferenceException encountered. Retrying...")
                sleep(2)
                continue
            except Exception as e:
                logging.error(f"Unexpected error during story interaction: {e}")
                take_screenshot(driver, "story_interaction_error")
                break

def main():
    try:
        logging.info("Script started.")
        print("Step 1: Logging in...")
        login(driver, USERNAME, PASSWORD)

        print("Step 2: Navigating to Home...")
        navigate_home(driver)

        print("Step 3: Interacting with Stories...")
        interact_with_stories(driver)

        print("Script finished. Press Enter to close the browser...")
        input()
    finally:
        driver.quit()
        logging.info("Browser closed.")

# ----------------------------- Entry Point -----------------------------

if __name__ == "__main__":
    main()
