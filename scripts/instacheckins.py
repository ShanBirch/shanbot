import argparse
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

# --- Command Line Argument Parsing ---
parser = argparse.ArgumentParser(description='Instagram messaging bot')
parser.add_argument('--reset', action='store_true',
                    help='Reset progress and message all users again')
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
chrome_options.add_experimental_option("detach", True)  # Keep browser open
chrome_options.add_experimental_option(
    "excludeSwitches", ["enable-automation"])  # Hide automation
chrome_options.add_experimental_option(
    'useAutomationExtension', False)  # Disable automation extension

# Set the path to the ChromeDriver executable
chromedriver_path = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"

try:
    # Initialize the driver with Service object for the specific chromedriver path
    service = webdriver.chrome.service.Service(
        executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(1920, 1080)  # Set a specific window size
    driver.set_window_position(0, 0)  # Position window at top-left
except Exception as e:
    print(f"Chrome driver initialization error: {e}")
    print("Please make sure ChromeDriver is properly installed and matches your Chrome version.")
    exit(1)

# --- Instagram Credentials ---
USERNAME = "cocos_connected"
PASSWORD = "Shannonb3"

# --- Message options ---
MESSAGE_OPTIONS = [
    "Heya, hows your week been?",
    "Yo yo! Hows the training been this week",
    "Hey Hey, hows the week been?",
    "Hey, hows your week been?",
    "Good Evening :), hows your week been?",
    "Yo! How's the training been this week?",
    "Hey, hows the training going this week?",
    "Hey, hows the training been this week?",

]

# --- Function to load usernames from file ---


def load_usernames(file_path):
    # Create the file with the specified usernames if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write("kristyleecoop\nShane_Minahan\n")

        print(
            f"Created username file at {file_path} with specified usernames.")

    # Override to only use kristyleecoop and Shane_Minahan for now
    print("NOTE: Script configured to message kristyleecoop and Shane_Minahan as requested")
    return ["kristyleecoop", "Shane_Minahan"]

    # Original code commented out
    # with open(file_path, 'r') as f:
    #     # Filter out empty lines and comments
    #     usernames = [line.strip() for line in f if line.strip()
    #                  and not line.strip().startswith('#')]
    # return usernames

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
        time.sleep(5)  # Increased wait time for page to load completely

        # --- Login ---
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_field.clear()
        username_field.send_keys(username)
        print("Entered username.")

        password_field = driver.find_element(By.NAME, "password")
        password_field.clear()
        password_field.send_keys(password)
        print("Entered password.")

        login_button = driver.find_element(
            By.XPATH, "//button[@type='submit']")
        login_button.click()
        print("Clicked login button.")

        # Wait for login to complete and handle potential popups
        time.sleep(8)  # Increased wait time

        # Handle "Save Login Info" popup if it appears
        try:
            not_now_button = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_button.click()
            print("Clicked 'Not Now' on save login info.")
            time.sleep(2)
        except Exception:
            print("No 'Save Login Info' popup or already handled.")

        # Handle notifications popup if it appears
        try:
            not_now_notif = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_notif.click()
            print("Clicked 'Not Now' on notifications.")
            time.sleep(2)
        except Exception:
            print("No notifications popup or already handled.")

        print("Login process completed.")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"Error during login: {e}")
        driver.save_screenshot("login_error.png")
        return False

# --- Function to message a user ---


def message_user(driver, username):
    # Select a random message
    message_text = random.choice(MESSAGE_OPTIONS)
    print(f"Selected message for {username}: '{message_text}'")

    results_dir = f"results/{username}"
    os.makedirs(results_dir, exist_ok=True)

    try:
        # --- Navigate directly to the profile page ---
        try:
            # Direct navigation to profile page
            driver.get(f"https://www.instagram.com/{username}/")
            print(f"Navigating to {username}'s profile page...")
            time.sleep(7)  # Increased time for profile page to load

            # Take a screenshot to verify we're on the correct page
            driver.save_screenshot(f"{results_dir}/profile_page.png")
            print(f"Profile page screenshot saved for {username}")
        except Exception as e:
            print(f"Error navigating to {username}'s profile: {e}")
            driver.save_screenshot(
                f"{results_dir}/profile_navigation_error.png")
            return False

        # --- Check if profile exists ---
        try:
            # Check for "Sorry, this page isn't available" message
            not_available = driver.find_elements(
                By.XPATH, "//h2[contains(text(), 'Sorry')]")
            if not_available:
                print(f"Profile for {username} does not exist or is private.")
                driver.save_screenshot(
                    f"{results_dir}/profile_not_available.png")
                return False
        except Exception:
            pass

        # --- Click "Message" Button ---
        try:
            print("Looking for Message button...")
            # Try different potential selectors for the Message button
            message_button_selectors = [
                "//div[text()='Message']",
                "//button[contains(text(), 'Message')]",
                "//div[contains(@role, 'button')][contains(text(), 'Message')]"
            ]

            message_button = None
            for selector in message_button_selectors:
                try:
                    message_button = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if message_button:
                        break
                except Exception:
                    continue

            if not message_button:
                print(f"Could not find Message button for {username}")
                driver.save_screenshot(
                    f"{results_dir}/message_button_not_found.png")
                return False

            # Scroll to the element to make sure it's visible
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", message_button)
            time.sleep(2)

            # Try clicking the button
            try:
                message_button.click()
            except Exception:
                # If direct click fails, try JavaScript click
                driver.execute_script("arguments[0].click();", message_button)

            print(f"Clicked 'Message' button for {username}.")

            # Wait for chat window to load completely
            time.sleep(7)  # Increased wait time

            # Take screenshot to see what we're dealing with
            driver.save_screenshot(f"{results_dir}/after_message_button.png")

            # Try to handle notification popups in the message inbox
            handle_popups(driver, results_dir)

        except Exception as e:
            print(f"Error clicking message button for {username}: {e}")
            driver.save_screenshot(f"{results_dir}/message_button_error.png")
            return False

        # --- Type and Send Message ---
        return try_send_message(driver, username, message_text, results_dir)

    except Exception as e:
        print(f"Error processing {username}: {e}")
        try:
            driver.save_screenshot(f"{results_dir}/error.png")
        except:
            pass
        return False

# --- Function to handle popups ---


def handle_popups(driver, results_dir):
    try:
        print("Looking for notification popup in message inbox...")
        # Try different possible text variations for the "Not Now" button
        popup_buttons = [
            "//button[contains(text(), 'Not Now')]",
            "//button[text()='Not Now']",
            "//button[contains(text(), 'Not now')]",
            "//button[contains(text(), 'Skip')]",
            "//button[contains(text(), 'Cancel')]",
            "//button[contains(text(), 'Later')]",
            "//button[contains(@class, 'NotNow')]"
        ]

        popup_found = False
        for button_xpath in popup_buttons:
            try:
                popup_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, button_xpath))
                )
                popup_button.click()
                popup_found = True
                print(f"Clicked popup button with selector: {button_xpath}")
                time.sleep(2)
                break
            except Exception:
                continue

        if not popup_found:
            print("No notification popup found or couldn't dismiss it automatically.")
    except Exception as e:
        print(f"Error handling notification popup: {e}")
        driver.save_screenshot(f"{results_dir}/popup_handling_error.png")

# --- Function to try different methods to send a message ---


def try_send_message(driver, username, message_text, results_dir):
    print(f"Attempting to send message to {username}...")

    # First approach: Try to directly identify the input field
    try:
        # Find the message input area by its specific attributes
        message_input_selectors = [
            "//div[@aria-label='Message' and @role='textbox']",
            "//div[@contenteditable='true']",
            "//div[contains(@aria-label, 'Message')]",
            "//div[contains(@placeholder, 'Message')]"
        ]

        message_input = None
        for selector in message_input_selectors:
            try:
                message_input = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if message_input:
                    break
            except Exception:
                continue

        if not message_input:
            print(f"Could not find message input field for {username}")
            driver.save_screenshot(
                f"{results_dir}/message_input_not_found.png")
            return False

        # Click to focus the input
        message_input.click()
        time.sleep(1)

        # Clear any existing text first
        try:
            message_input.clear()
        except Exception:
            pass

        # Use ActionChains to type into the input field
        actions = ActionChains(driver)
        actions.move_to_element(message_input).click().pause(1)

        # Type character by character with small delays
        for char in message_text:
            actions.send_keys(char).pause(0.1)

        actions.perform()
        print(f"Typed message to {username} using ActionChains.")

        # Take a screenshot before sending
        driver.save_screenshot(f"{results_dir}/before_send.png")

        # Send the message by pressing Enter
        time.sleep(1)
        message_input.send_keys(Keys.ENTER)
        print(f"Pressed Enter to send message to {username}.")

        # Take a screenshot to verify
        time.sleep(3)
        driver.save_screenshot(f"{results_dir}/message_sent.png")
        print(f"Message sent to {username}. Screenshot saved.")
        return True

    except Exception as e:
        print(f"Error sending message to {username}: {e}")

        # Try alternative approaches if the first one fails
        try:
            # JavaScript approach
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
                print(f"Message sent to {username} using JavaScript approach.")
                return True
        except Exception as js_error:
            print(f"JavaScript approach failed: {js_error}")

        driver.save_screenshot(f"{results_dir}/message_send_error.png")
        return False

# --- Main script execution ---


def main():
    print("Starting Instagram messaging script...")
    print("Initializing Chrome browser...")

    # Create results directory
    os.makedirs("results", exist_ok=True)

    # File paths
    usernames_file = "instagram_usernames.txt"
    progress_file = "progress.txt"

    # Load usernames
    usernames = load_usernames(usernames_file)
    print(f"Loaded {len(usernames)} usernames from file")

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
        driver.quit()
        return

    # Filter out already processed usernames
    usernames_to_process = [u for u in usernames if u not in processed]

    if not usernames_to_process:
        print("All usernames have already been processed!")
        print("To run again and message all users, use the --reset flag (e.g., python ic.py --reset)")
        driver.quit()
        return

    print(f"Found {len(usernames_to_process)} usernames to process.")

    # Login to Instagram
    print("Attempting to login to Instagram...")
    if not login_to_instagram(driver, USERNAME, PASSWORD):
        print("Failed to login. Aborting script.")
        driver.quit()
        return

    # Process each username
    newly_processed = []
    try:
        for i, username in enumerate(usernames_to_process):
            print(
                f"\n[{i+1}/{len(usernames_to_process)}] Processing {username}...")

            # Message the user
            success = message_user(driver, username)

            if success:
                print(f"Successfully messaged {username}.")
                newly_processed.append(username)
                processed.add(username)

                # Save progress after each successful message
                save_progress(progress_file, processed)
            else:
                print(f"Failed to message {username}.")

            # Wait between users to avoid rate limiting
            if i < len(usernames_to_process) - 1:  # Don't wait after the last user
                # Randomized wait time to avoid detection
                wait_time = random.randint(40, 70)
                print(f"Waiting {wait_time} seconds before next user...")
                time.sleep(wait_time)

        print("\nScript completed!")
        if newly_processed:
            print(
                f"Successfully messaged {len(newly_processed)} users: {', '.join(newly_processed)}")
        if len(newly_processed) < len(usernames_to_process):
            print(
                f"Failed to message {len(usernames_to_process) - len(newly_processed)} users.")

        # Clear progress file if all users in the list have been processed
        if set(usernames) == processed:
            print(
                "All users have been processed. Clearing progress to allow running again.")
            if os.path.exists(progress_file):
                os.remove(progress_file)

    except Exception as e:
        print(f"An error occurred during script execution: {e}")
    finally:
        # Keep browser open for inspection
        print("\nScript finished. Browser window is still open for observation.")
        print("Press Ctrl+C in the terminal when you're ready to close the browser.")
        try:
            # This will keep the script running until manually interrupted
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("Script terminated by user.")
            driver.quit()


# Run the script immediately
if __name__ == "__main__":
    print("Starting script...")
    main()
