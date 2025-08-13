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
from fitness_wrapped_video import generate_bens_fitness_wrapped

# --- Host the video and get a shareable link ---
def upload_and_get_link(video_path):
    """
    Uploads the video to a file hosting service and returns a shareable link
    
    In a real implementation, you would:
    1. Upload to a service like AWS S3, Google Drive, Dropbox, etc.
    2. Generate a shareable link
    3. Return the link
    
    For this example, we'll just simulate it.
    """
    print(f"Uploading video from {video_path}...")
    # This is a placeholder. In reality, you'd implement the actual upload logic.
    
    # Dummy logic - in reality you'd upload the file and get a real link
    if os.path.exists(video_path):
        video_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
        print(f"Video size: {video_size:.2f} MB")
        
        # Generate a fake link for demo purposes
        # In a real implementation, this would be the actual share link from your upload service
        share_link = f"https://your-video-host.com/fitness-wrapped-{int(time.time())}"
        print(f"Video uploaded. Share link: {share_link}")
        return share_link
    else:
        print(f"Error: Video file not found at {video_path}")
        return None

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
    "what's good? how's the workout routine?"
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
    results_dir = f"results/{username}"
    os.makedirs(results_dir, exist_ok=True)
    
    try:
        # --- For cocos_connected, generate fitness wrapped video ---
        if username == "cocos_connected":
            print("Generating Fitness Wrapped video for Ben...")
            try:
                # Generate the fitness wrapped video
                video_path = generate_bens_fitness_wrapped()
                if video_path and os.path.exists(video_path):
                    # Upload the video and get a shareable link
                    share_link = upload_and_get_link(video_path)
                    if share_link:
                        message_text = f"Hey Ben! I've created your weekly fitness wrapped video! Check it out here: {share_link}"
                        print(f"Will send video link: {share_link}")
                    else:
                        # Fallback message if video upload fails
                        message_text = "Hey Ben! I've prepared your weekly fitness wrapped video but having some technical issues uploading it. I'll get it to you soon!"
                        print("Using fallback message as video upload failed")
                else:
                    # Fallback message if video generation fails
                    message_text = "Hey Ben! I've prepared your weekly review but having some technical issues. I'll get it to you soon!"
                    print("Using fallback message as video generation failed")
            except Exception as e:
                print(f"Error generating fitness wrapped video: {e}")
                message_text = "Hey Ben! I've prepared your weekly review but having some technical issues. I'll get it to you soon!"
        else:
            # For all other users, use a random message from the default options
            message_text = random.choice(DEFAULT_MESSAGE_OPTIONS)
            print(f"Selected random message for {username}: '{message_text}'")
        
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
            time.sleep(5)
            
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
            
            # Find the message input area
            message_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Message' and @role='textbox' and @contenteditable='true']"))
            )
            
            # Use ActionChains to click and type into the input field
            actions = ActionChains(driver)
            actions.move_to_element(message_input).click().pause(1).send_keys(message_text).perform()
            print(f"Typed message to {username} using ActionChains.")
            
            # Send the message by pressing Enter
            actions.send_keys(Keys.ENTER).perform()
            print(f"Pressed Enter to send message to {username}.")
            
            # Take a screenshot to verify
            time.sleep(2)
            driver.save_screenshot(f"{results_dir}/message_sent.png")
            print(f"Message should be sent to {username}. Screenshot saved.")
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
                    
                    # Use JavaScript to focus and set text
                    driver.execute_script("arguments[0].focus();", message_input)
                    driver.execute_script("arguments[0].click();", message_input)
                    time.sleep(1)
                    
                    # Try to set the text using JavaScript
                    driver.execute_script("arguments[0].textContent = arguments[1];", message_input, message_text)
                    print(f"Set message text for {username} using JavaScript.")
                    
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
                        
                        # Try ActionChains again with the potential input
                        actions = ActionChains(driver)
                        actions.move_to_element(potential_input).click().pause(1).send_keys(message_text).perform()
                        print(f"Typed message to {username} using ActionChains on potential input.")
                        
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