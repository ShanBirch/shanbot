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

# --- Browser Driver Setup with improved error handling ---
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

try:
    driver = webdriver.Chrome(options=chrome_options)
except Exception as e:
    print(f"Chrome driver initialization error: {e}")
    print("Please make sure ChromeDriver is properly installed and matches your Chrome version.")
    exit(1)

# --- Instagram Credentials ---
USERNAME = "cocos_pt_studio"
PASSWORD = "Shannonb3"

# --- Custom message for cocos_connected ---
CUSTOM_MESSAGE = """Hey Ben Here's your review for the week! :)
Photos: Didn't see any new progress pics this week. No worries, but if you can, snapping some regularly is super helpful to see how far you've come visually!
Weight: Weight's trending down nicely, that's awesome work! You're down 3.5 kg from 87 to 83.5! Keep doing what you're doing!
Food: No nutrition data this week, Ben. Tracking your food intake is the biggest step towards understanding your diet and achieving your goals! Maybe you could track it this week.
Steps: No steps data this week. Remember, physical activity is so important for overall health. Tracking your steps can be a great way to stay motivated!
Sleep: No sleep data this week Ben. Consistently tracking your sleep helps us understand your recovery. Aiming for around 8 hours of sleep each night can significantly impact your progress and well-being! Try and make it a routine, bed at the same time and up at the same time everyday, this will help keep your internal body clock happy!
Workout Summary
Total workouts for week of 24/02/2025-02/03/2025: 7
- Back and Triceps
- Back and Triceps
- Chest and Biceps
- Chest and Biceps
- Core and Arms
- Core and Arms 2
- Core and Arms 2
Total Weight Lifted: 40440.00 kg
Total Reps Done: 1514
Total Sets Done: 152
Total Workload Change comparing previous week to current week:
Workload change vs previous week: 117.19%
Love this see this increase in overall workload! Keep it coming!"""

# --- Default message options for other users ---
DEFAULT_MESSAGE_OPTIONS = [
    "heya hows your week been?",
    "yo yo, hows the week been",
    "Yo! Hows training going this week?",
    "Hey! Hows the meals been this week?",
    "Yo yo hows the nutrition this week?",
    "hey there! how's your training going?",
    "what's up? how's the fitness journey?",
    "hey, how're your meals going lately?",
    "hi! how's your progress this week?",
    "yo, how's the gym life treating you?",
    "hey, seeing any gains this week?",
    "what's good? how's the workout routine?",
    "hi there, how's your fitness routine?",
    "hey! noticing any changes yet?",
    "yo, how's your nutrition going?",
    "hey, how's your energy levels this week?",
    "what's up! how's the training schedule?",
    "hi, how's your eating been?",
    "hey there, getting enough protein?",
    "yo yo, how're your workouts?",
    "hey! how's your recovery been?",
    "hi, how are your sessions feeling?",
    "what's good? how's your eating this week?",
    "hey there, how's the strength training?",
    "yo, noticing any changes yet?",
    "hey, how's your food been this week?",
    "hi! staying hydrated?",
    "what's up? how's your form these days?",
    "hey there, feeling the burn?",
    "yo, how's your week going?",
    "heya, getting enough protein?",
    "hi, how's your sleep quality lately?",
    "hey, hitting those fitness goals?",
    "yo yo, how's your motivation this week?",
    "hey there! seeing any progress?",
    "what's happening? how's your eating?",
    "hi, any new personal records lately?",
    "hey, how're your workouts going?",
    "yo, getting those steps in?",
    "hey there, how's your food this week?",
    "hi! how's your weight?",
    "what's good? how's your endurance lately?",
    "hey, feeling stronger this week?",
    "yo yo, trying any new exercises?",
    "hey there, how's everything going?",
    "hi, how's your weekend nutrition?",
    "hey! how's the gym treating you?",
    "yo, getting enough rest days?",
    "what's up? keeping things flexible?",
    "hey there, staying consistent with workouts?"
]

# --- Function to load usernames from file ---
def load_usernames(file_path):
    if not os.path.exists(file_path):
        # Create the file with sample usernames if it doesn't exist
        with open(file_path, 'w') as f:
            f.write("cocos_connected\n")
            f.write("# Add more usernames below, one per line\n")
            f.write("# Lines starting with # are comments and will be ignored\n")
        print(f"Created username file at {file_path}. Please add usernames and run the script again.")
        return []
    
    with open(file_path, 'r') as f:
        # Filter out empty lines and comments
        usernames = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    return usernames

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
        time.sleep(3)  # Wait for page to load completely

        # --- Login ---
        username_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_field.clear()
        username_field.send_keys(username)
        print("Entered username.")
        
        password_field = driver.find_element(By.NAME, "password")
        password_field.clear()
        password_field.send_keys(password)
        print("Entered password.")
        
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        print("Clicked login button.")

        # Wait for login to complete and handle potential popups
        time.sleep(5)
        
        # Handle "Save Login Info" popup if it appears
        try:
            not_now_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_button.click()
            print("Clicked 'Not Now' on save login info.")
        except Exception:
            print("No 'Save Login Info' popup or already handled.")
        
        # Handle notifications popup if it appears
        try:
            not_now_notif = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_notif.click()
            print("Clicked 'Not Now' on notifications.")
        except Exception:
            print("No notifications popup or already handled.")

        print("Login process completed.")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"Error during login: {e}")
        return False

# --- Function to message a user ---
def message_user(driver, username):
    # Select message based on username
    if username == "cocos_connected":
        message_text = CUSTOM_MESSAGE
        print(f"Using custom message for {username}")
    else:
        # For all other users, use a random message from the default options
        message_text = random.choice(DEFAULT_MESSAGE_OPTIONS)
        print(f"Selected random message for {username}: '{message_text}'")
    
    results_dir = f"results/{username}"
    os.makedirs(results_dir, exist_ok=True)
    
    try:
        # --- Navigate directly to the profile page ---
        try:
            # Direct navigation to profile page
            driver.get(f"https://www.instagram.com/{username}/")
            print(f"Navigating to {username}'s profile page...")
            time.sleep(5)  # Give time for profile page to load
            
            # Take a screenshot to verify we're on the correct page
            driver.save_screenshot(f"{results_dir}/profile_page.png")
            print(f"Profile page screenshot saved for {username}")
        except Exception as e:
            print(f"Error navigating to {username}'s profile: {e}")
            driver.save_screenshot(f"{results_dir}/profile_navigation_error.png")
            return False

        # --- Click "Message" Button ---
        try:
            print("Looking for Message button...")
            message_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[text()='Message']"))
            )
            # Scroll to the element to make sure it's visible
            driver.execute_script("arguments[0].scrollIntoView(true);", message_button)
            time.sleep(1)
            message_button.click()
            print(f"Clicked 'Message' button for {username}.")
            
            # Wait for chat window to load completely
            time.sleep(5)  # Increased wait time
            
            # Take screenshot to see what we're dealing with
            driver.save_screenshot(f"{results_dir}/after_message_button.png")
            
            # Try to handle the notification popup in the message inbox
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
                        time.sleep(1)
                        break
                    except Exception:
                        continue
                
                if not popup_found:
                    print("No notification popup found or couldn't dismiss it automatically.")
            except Exception as e:
                print(f"Error handling notification popup: {e}")
            
        except Exception as e:
            print(f"Error clicking message button for {username}: {e}")
            driver.save_screenshot(f"{results_dir}/message_button_error.png")
            return False

        # --- Type and Send Message using ActionChains ---
        try:
            print(f"Attempting to send message to {username}...")
            
            # No need to split the message - we'll send it all as one
            # Find the message input area
            message_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Message' and @role='textbox' and @contenteditable='true']"))
            )
            
            # Use ActionChains to click and type into the input field
            actions = ActionChains(driver)
            actions.move_to_element(message_input).click().pause(1).send_keys(message_text).perform()
            print(f"Typed full message to {username} using ActionChains.")
            
            # Send the message by pressing Enter
            actions.send_keys(Keys.ENTER).perform()
            print(f"Pressed Enter to send message to {username}.")
            
            # Take a screenshot to verify
            time.sleep(2)
            driver.save_screenshot(f"{results_dir}/message_sent.png")
            print(f"Complete message should be sent to {username}. Screenshot saved.")
            return True
                
        except Exception as e:
            print(f"First approach failed for {username}: {e}")
            print("Trying alternative approach...")
            
            # Second approach: Try to use JavaScript to set the content and trigger events
            try:
                # Find the message input area 
                message_inputs = driver.find_elements(By.XPATH, "//div[@aria-label='Message']")
                
                if message_inputs:
                    message_input = message_inputs[0]
                    print(f"Found message input element: {message_input.get_attribute('class')}")
                    
                    # Send the message as a single block
                    # Use JavaScript to focus and set text
                    driver.execute_script("arguments[0].focus();", message_input)
                    driver.execute_script("arguments[0].click();", message_input)
                    time.sleep(1)
                    
                    # Try to set the text using JavaScript
                    driver.execute_script("arguments[0].textContent = arguments[1];", message_input, message_text)
                    print(f"Set full message text for {username} using JavaScript.")
                    
                    # Try to trigger Enter key via JavaScript
                    driver.execute_script("""
                    var keyEvent = new KeyboardEvent('keydown', {
                        'key': 'Enter',
                        'code': 'Enter',
                        'keyCode': 13,
                        'which': 13,
                        'bubbles': true
                    });
                    arguments[0].dispatchEvent(keyEvent);
                    """, message_input)
                    
                    time.sleep(1)
                    
                    print(f"Triggered Enter key via JavaScript for {username}.")
                    time.sleep(2)
                    
                    # Take a screenshot to verify
                    driver.save_screenshot(f"{results_dir}/message_sent_js.png")
                    print(f"Message should be sent to {username} using JavaScript. Screenshot saved.")
                    return True
                else:
                    print(f"No message input elements found for {username}.")
                    
                    # Third approach: Try to find by class patterns
                    print("Trying to find by class patterns...")
                    
                    # Look for elements with common Instagram message input classes
                    potential_inputs = driver.find_elements(By.XPATH, "//div[@contenteditable='true']")
                    
                    if potential_inputs:
                        print(f"Found {len(potential_inputs)} potential input elements")
                        potential_input = potential_inputs[0]
                        
                        # Send as a single message
                        # Try ActionChains with the potential input
                        actions = ActionChains(driver)
                        actions.move_to_element(potential_input).click().pause(1).send_keys(message_text).perform()
                        print(f"Typed full message to {username} using ActionChains on potential input.")
                        
                        # Send the message by pressing Enter
                        actions.send_keys(Keys.ENTER).perform()
                        time.sleep(1)
                        
                        print(f"Message should be sent to {username}.")
                        
                        # Take a screenshot to verify
                        time.sleep(2)
                        driver.save_screenshot(f"{results_dir}/message_sent_potential.png")
                        return True
                    else:
                        print(f"No potential input elements found for {username}.")
                        driver.save_screenshot(f"{results_dir}/no_inputs_found.png")
                        return False
                
            except Exception as e:
                print(f"Second approach failed for {username}: {e}")
                driver.save_screenshot(f"{results_dir}/second_approach_error.png")
                return False
                
    except Exception as e:
        print(f"Error processing {username}: {e}")
        try:
            driver.save_screenshot(f"{results_dir}/error.png")
        except:
            pass
        return False

# --- Main script execution ---
def main():
    # Create results directory
    os.makedirs("results", exist_ok=True)
    
    # File paths
    usernames_file = "instagram_usernames.txt"
    progress_file = "progress.txt"
    
    # Load usernames and progress
    usernames = load_usernames(usernames_file)
    processed = load_progress(progress_file)
    
    if not usernames:
        print(f"No usernames found in {usernames_file}. Please add usernames and run the script again.")
        driver.quit()
        return
    
    # Filter out already processed usernames
    usernames_to_process = [u for u in usernames if u not in processed]
    
    if not usernames_to_process:
        print("All usernames have already been processed!")
        driver.quit()
        return
    
    print(f"Found {len(usernames_to_process)} usernames to process.")
    
    # Login to Instagram
    if not login_to_instagram(driver, USERNAME, PASSWORD):
        print("Failed to login. Aborting script.")
        driver.quit()
        return
    
    # Process each username
    newly_processed = []
    try:
        for i, username in enumerate(usernames_to_process):
            print(f"\n[{i+1}/{len(usernames_to_process)}] Processing {username}...")
            
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
                wait_time = 30  # 30 seconds between messages
                print(f"Waiting {wait_time} seconds before next user...")
                time.sleep(wait_time)
        
        print("\nScript completed!")
        if newly_processed:
            print(f"Successfully messaged {len(newly_processed)} users: {', '.join(newly_processed)}")
        if len(newly_processed) < len(usernames_to_process):
            print(f"Failed to message {len(usernames_to_process) - len(newly_processed)} users.")
            
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

# Run the script
if __name__ == "__main__":
    main()