import argparse
import sys
import os
import json
import datetime
import time
import random
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

# --- Command Line Argument Parsing ---
parser = argparse.ArgumentParser(description='Instagram follower profiler')
parser.add_argument('--followers-list', type=str, default='instagram_followers.txt',
                    help='Path to the file containing the list of Instagram followers')
parser.add_argument('--chromedriver', type=str, default=None,
                    help='Path to ChromeDriver executable (overrides default paths)')
args = parser.parse_args()

# Ensure we're using absolute paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FOLLOWERS_LIST = os.path.join(SCRIPT_DIR, args.followers_list)

# --- Instagram Credentials ---
USERNAME = "cocos_connected"
PASSWORD = "Shannonb3"

# --- Gemini API Key ---
GEMINI_API_KEY = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

# Initialize Gemini client
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# --- Browser Setup ---
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_experimental_option("detach", True)
chrome_options.add_experimental_option(
    "excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)


def find_chromedriver():
    """Find a valid ChromeDriver executable from multiple common locations"""
    if args.chromedriver and os.path.exists(args.chromedriver):
        return args.chromedriver

    potential_paths = [
        r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe",
        r"C:\chromedriver.exe",
        r"C:\chromedriver\chromedriver.exe",
        r"C:\WebDrivers\chromedriver.exe",
        r"C:\Program Files\ChromeDriver\chromedriver.exe",
        r"C:\Program Files (x86)\ChromeDriver\chromedriver.exe",
        os.path.join(os.path.expanduser("~"), "chromedriver.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "chromedriver.exe"),
        os.path.join(os.path.expanduser("~"), "Desktop", "chromedriver.exe"),
        os.path.join(os.getcwd(), "chromedriver.exe"),
        os.path.join(SCRIPT_DIR, "chromedriver.exe"),
        os.path.join(SCRIPT_DIR, "drivers", "chromedriver.exe"),
    ]

    for path in potential_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path

    return None


def login_to_instagram(driver, username, password):
    """Login to Instagram account"""
    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(5)

        # Find username and password fields
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = driver.find_element(By.NAME, "password")

        # Enter credentials
        username_field.send_keys(username)
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(5)

        # Handle any post-login popups
        handle_post_login_popups(driver)
        return True
    except Exception as e:
        print(f"Login error: {e}")
        return False


def handle_post_login_popups(driver):
    """Handle various popups that appear after login"""
    try:
        time.sleep(2)
        popup_buttons = [
            "//button[contains(text(), 'Not Now')]",
            "//button[contains(text(), 'Cancel')]",
            "//button[contains(text(), 'Skip')]"
        ]

        for button in popup_buttons:
            try:
                elements = driver.find_elements(By.XPATH, button)
                for element in elements:
                    if element.is_displayed():
                        element.click()
                        time.sleep(1)
            except:
                continue
    except Exception as e:
        print(f"Error handling popups: {e}")


def can_message_user(driver, username):
    """Check if we can message the user"""
    try:
        # Look for message button
        message_button_selectors = [
            "//div[contains(text(), 'Message')]",
            "//button[contains(text(), 'Message')]",
            "//a[contains(text(), 'Message')]",
            "//div[contains(@role, 'button') and contains(text(), 'Message')]"
        ]

        for selector in message_button_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed():
                    return True

        return False
    except Exception as e:
        print(f"Error checking message button: {e}")
        return False


def analyze_profile(driver, username):
    """Analyze a user's profile and posts"""
    try:
        # Create results directory
        results_dir = f"results/{username}"
        os.makedirs(results_dir, exist_ok=True)

        # Get bio text
        bio = ""
        try:
            bio_element = driver.find_element(
                By.XPATH, "//div[contains(@class, '_aa_c')]")
            bio = bio_element.text
        except:
            bio = "No bio available"

        # Find and analyze posts
        posts = driver.find_elements(
            By.XPATH, "//div[contains(@class, '_aagw')]")
        image_paths = []

        # Analyze up to 6 posts
        for i, post in enumerate(posts[:6]):
            try:
                post.click()
                time.sleep(3)

                # Take screenshot
                screenshot_path = f"{results_dir}/post_{i+1}.png"
                driver.save_screenshot(screenshot_path)
                image_paths.append(screenshot_path)

                # Close post
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(2)
            except:
                continue

        # Analyze images with Gemini
        analysis = analyze_content_with_gemini(bio, image_paths, username)
        return analysis

    except Exception as e:
        print(f"Error analyzing profile: {e}")
        return None


def analyze_content_with_gemini(bio, image_paths, username):
    """Analyze user content using Gemini AI"""
    try:
        # Prepare images for analysis
        image_contents = []
        for path in image_paths:
            with open(path, 'rb') as f:
                image_contents.append({
                    "mime_type": "image/jpeg",
                    "data": f.read()
                })

        # Create analysis prompt
        prompt = f"""
        Analyze this Instagram user's profile:

        Bio: {bio}

        Based on their bio and posts, create a detailed profile with:
        1. Brief bio summary
        2. Main interests (3-5)
        3. 4 distinct conversation topics that would engage them
        4. Personality traits/characteristics

        Format the response as JSON with these fields:
        - bio_summary
        - interests (list)
        - conversation_topics (exactly 4)
        - personality_traits (list)
        """

        # Generate content with Gemini
        contents = [{"text": prompt}]
        for img in image_contents:
            contents.append({"inline_data": img})

        response = gemini_model.generate_content(
            contents=contents,
            generation_config=genai.GenerationConfig(
                temperature=0.4,
                max_output_tokens=800,
            )
        )

        # Parse response
        try:
            analysis = json.loads(response.text)
        except:
            # If JSON parsing fails, create structured response
            analysis = {
                "bio_summary": "Could not generate bio summary",
                "interests": ["Unknown"],
                "conversation_topics": [
                    "General interests",
                    "Recent activities",
                    "Professional life",
                    "Hobbies"
                ],
                "personality_traits": ["Unable to determine"]
            }

        return analysis

    except Exception as e:
        print(f"Error in Gemini analysis: {e}")
        return None


def save_profile(username, profile_data):
    """Save user profile to individual files"""
    try:
        # Create followersbio directory if it doesn't exist
        bio_dir = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\followersbio"
        os.makedirs(bio_dir, exist_ok=True)

        # Save individual profile file
        profile_file = os.path.join(bio_dir, f"{username}_profile.txt")
        with open(profile_file, "w", encoding="utf-8") as f:
            f.write(f"INSTAGRAM PROFILE: {username}\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"Bio Summary:\n{profile_data['bio_summary']}\n\n")
            f.write("Interests:\n")
            for interest in profile_data['interests']:
                f.write(f"- {interest}\n")
            f.write("\nConversation Topics:\n")
            for i, topic in enumerate(profile_data['conversation_topics'], 1):
                f.write(f"{i}. {topic}\n")
            f.write("\nPersonality Traits:\n")
            for trait in profile_data['personality_traits']:
                f.write(f"- {trait}\n")
            f.write(
                f"\nAnalyzed on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Also save JSON version for programmatic access
        json_file = os.path.join(bio_dir, f"{username}_profile.json")
        profile_json = {
            "username": username,
            "timestamp": datetime.datetime.now().isoformat(),
            "profile": profile_data
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(profile_json, f, indent=2)

        print(f"Saved profile for {username} in {bio_dir}")

    except Exception as e:
        print(f"Error saving profile for {username}: {e}")


def load_usernames(file_path):
    """Load usernames from file"""
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except Exception as e:
        print(f"Error loading usernames: {e}")
        return []


def main():
    print("Starting Instagram Follower Profiler...")

    # Initialize webdriver
    chromedriver_path = find_chromedriver()
    if not chromedriver_path:
        print("ChromeDriver not found. Please install it.")
        return

    service = webdriver.chrome.service.Service(
        executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Login to Instagram
        if not login_to_instagram(driver, USERNAME, PASSWORD):
            print("Failed to login. Exiting.")
            return

        # Load usernames
        usernames = load_usernames(FOLLOWERS_LIST)
        print(f"Loaded {len(usernames)} usernames")

        # Process each username
        for i, username in enumerate(usernames):
            print(f"\nProcessing {username} ({i+1}/{len(usernames)})")

            try:
                # Navigate to profile
                driver.get(f"https://www.instagram.com/{username}/")
                time.sleep(5)

                # Check if we can message them
                if not can_message_user(driver, username):
                    print(f"Cannot message {username}, skipping...")
                    continue

                # Analyze profile
                profile_data = analyze_profile(driver, username)
                if profile_data:
                    # Save profile data
                    save_profile(username, profile_data)
                    print(
                        f"Successfully analyzed and saved profile for {username}")

                # Random delay between profiles
                delay = random.randint(30, 60)
                print(f"Waiting {delay} seconds before next profile...")
                time.sleep(delay)

            except Exception as e:
                print(f"Error processing {username}: {e}")
                continue

        print("\nProfile analysis complete!")
        print("Results have been saved in followersbio directory")

    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        # Keep browser open since detach=True is set
        print("Script execution completed.")


if __name__ == "__main__":
    main()
